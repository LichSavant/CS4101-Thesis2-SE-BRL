"""Independent annotation preparation and checks. No generated reference labels."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from datetime import date
import hashlib
import json

from ml.research_policy import ResearchPolicyError, load_policy, reject_excluded
from ml.se_brl.codebook import load_codebook


STATES = {"supported", "absent", "unavailable"}


def indicator_ids() -> tuple[str, ...]:
    return tuple(item["id"] for dim in load_codebook()["dimensions"] for item in dim["indicators"])


def validate_span(span: Mapping, fields: Mapping[str, str]) -> None:
    if not isinstance(span, Mapping) or not isinstance(fields, Mapping):
        raise ValueError("Evidence span and original fields must be mappings")
    field, start, end = span.get("field"), span.get("start"), span.get("end")
    if type(field) is not str:
        raise ValueError("Evidence span requires a named original field")
    original = fields.get(field)
    if (not isinstance(original, str) or type(start) is not int or type(end) is not int
            or not 0 <= start < end <= len(original) or original[start:end] != span.get("text")):
        raise ValueError("Evidence span must match the named original field")


def _label_values(row: Mapping, *, candidates: bool = False) -> Mapping:
    if not isinstance(row, Mapping):
        raise ValueError("Annotation row must be a mapping")
    reject_excluded((row.get("record_id"), row.get("source_dataset"), row.get("source_provenance", {})))
    values = row.get("indicators", {})
    if not isinstance(values, Mapping) or set(values) - set(indicator_ids()):
        raise ValueError("Unknown annotation indicator")
    allowed = STATES | ({"abstained"} if candidates else set())
    if any(value is not None and (type(value) is not str or value not in allowed) for value in values.values()):
        raise ValueError("Malformed label; missing is None and is never a negative")
    return values


def _opportunity(modality: str, fields: Mapping[str, str]) -> tuple[bool, bool]:
    if not isinstance(fields, Mapping) or any(type(value) is not str for value in fields.values()):
        raise ValueError("Original fields must contain text values")
    field_sets = {
        "content_bearing_email": {"subject", "body", "sender", "reply_to"},
        "content_bearing_webpage": {"title", "visible_text", "html", "page_url"},
        "standalone_url": {"url"}, "engineered_technical_record": set(),
    }
    if modality not in field_sets or set(fields) - field_sets[modality]:
        raise ValueError("Evidence fields contradict the canonical modality")
    if modality == "content_bearing_email":
        return (any(fields.get(key, "").strip() for key in ("subject", "body")),
                any(fields.get(key, "").strip() for key in ("sender", "reply_to")))
    if modality == "content_bearing_webpage":
        from ml.preprocessing import preprocess
        artifact = preprocess({"kind": "webpage", **fields})
        return artifact.required_content_available, artifact.conditional_evidence_available
    return False, False


def validate_judgment(item: Mapping, fields: Mapping[str, str]) -> None:
    """Partial/missing labels are valid; human provenance is mandatory for claims."""
    values = _label_values(item)
    if item.get("codebook_version") != load_codebook()["codebook_version"]:
        raise ValueError("Incompatible annotation codebook")
    for key in ("record_id", "annotator_id", "role", "qualifications", "review_date", "protocol_version"):
        if type(item.get(key)) is not str or not item[key].strip():
            raise ValueError(f"Missing annotation provenance: {key}")
    date.fromisoformat(item["review_date"])
    reject_excluded(item.get("source_provenance", {}))
    if type(item.get("model_output_visible")) is not bool:
        raise ValueError("Blinding visibility must be explicit")
    if item.get("independent") is not True or item["model_output_visible"] or item["role"] != "independent_human":
        raise ValueError("Independent reference requires blinded independent-human provenance")
    evidence = item.get("evidence", {})
    if not isinstance(evidence, Mapping) or set(evidence) - set(indicator_ids()):
        raise ValueError("Unknown evidence indicator")
    codebook = load_codebook()
    modality = next((entry for entry in codebook["modalities"] if entry["id"] == item.get("modality")), None)
    if modality is None:
        raise ValueError("Annotation requires a canonical modality")
    content_available, conditional_available = _opportunity(modality["id"], fields)
    parents = {entry["id"]: dim["id"] for dim in codebook["dimensions"] for entry in dim["indicators"]}
    for indicator in indicator_ids():
        value = values.get(indicator)
        spans = evidence.get(indicator, [])
        if not isinstance(spans, list):
            raise ValueError("Evidence must be a list")
        for span in spans:
            validate_span(span, fields)
        if value == "supported" and not spans:
            raise ValueError("Supported reference requires grounded evidence")
        support = modality["support_by_dimension"][parents[indicator]]
        if value in {"supported", "absent"} and (support == "U" or not content_available or (support == "A*" and not conditional_available)):
            raise ValueError("Judgment unavailable for this modality/evidence opportunity")
        if value in {"supported", "absent"} and indicator in {"impersonation", "brand_exploitation"}:
            references_by_indicator = item.get("identity_reference_ids", {})
            references = references_by_indicator.get(indicator) if isinstance(references_by_indicator, Mapping) else None
            if not isinstance(references, list) or not references or any(not isinstance(ref, str) or not ref.strip() for ref in references):
                raise ValueError("Identity judgment requires independent evidence references")
        if value in (None, "unavailable") and spans:
            raise ValueError("Missing/unavailable judgments cannot assert evidence")


def coverage(rows: list[Mapping]) -> dict:
    """Describe completeness only. Does not establish independence or accuracy."""
    values = [_label_values(row, candidates=True) for row in rows]
    identities = [(row.get("record_id"), row.get("annotator_id")) for row in rows]
    if any(type(key) is not str or not key.strip() for key, _ in identities) or len(identities) != len(set(identities)):
        raise ValueError("Coverage requires unique record/annotator response identities")
    result = {}
    for indicator in indicator_ids():
        counts = Counter(value.get(indicator) if value.get(indicator) is not None else "missing" for value in values)
        result[indicator] = {state: counts[state] for state in ("supported", "absent", "unavailable", "abstained", "missing")}
    return {"items": len(rows), "indicators": result, "independence_established": False}


def pairwise_agreement(left: list[Mapping], right: list[Mapping]) -> dict:
    """Three-category descriptive agreement; missing/abstained pairs excluded.

    This arithmetic does not authenticate annotators or adjudicate disagreements.
    Unavailable is an explicit third category, never converted into absent.
    """
    def indexed(rows):
        result = {}
        for row in rows:
            _label_values(row, candidates=True)
            key = row.get("record_id")
            if type(key) is not str or not key:
                raise ValueError("Agreement requires explicit record IDs")
            if key in result:
                raise ValueError("Duplicate annotation record ID")
            result[key] = row
        return result
    a, b = indexed(left), indexed(right)
    for key in set(a) & set(b):
        for field in ("text_hash", "modality", "codebook_version"):
            if field in a[key] and field in b[key] and a[key][field] != b[key][field]:
                raise ValueError("Agreement records refer to incompatible artifacts or contracts")
    per_indicator = {}
    for indicator in indicator_ids():
        pairs = [(a[key].get("indicators", {}).get(indicator), b[key].get("indicators", {}).get(indicator)) for key in sorted(set(a) & set(b))]
        valid = [(x, y) for x, y in pairs if x in STATES and y in STATES]
        n = len(valid)
        observed = sum(x == y for x, y in valid) / n if n else None
        expected = sum(sum(x == s for x, _ in valid) * sum(y == s for _, y in valid) for s in STATES) / (n * n) if n else None
        kappa = (observed - expected) / (1 - expected) if expected is not None and expected < 1 else None
        per_indicator[indicator] = {"comparable": n, "excluded_missing_or_abstained": len(pairs) - n,
                                    "observed_agreement": observed, "cohens_kappa": kappa,
                                    "degenerate_or_no_pairs": kappa is None}
    return {"category_policy": "supported/absent/unavailable; missing and abstention excluded",
            "unmatched_record_count": len(set(a) ^ set(b)), "indicators": per_indicator,
            "independence_established": False}


def blinded_packet(records: list[Mapping]) -> dict:
    """Prepare only explicitly approved development sources, stripping all labels."""
    approved = set(load_policy()["approved_annotation_sources"])
    packet, custody, ids = [], [], set()
    for record in records:
        if not isinstance(record, Mapping) or not isinstance(record.get("provenance"), Mapping) or not record["provenance"]:
            raise ValueError("Blinded packet requires explicit source provenance")
        reject_excluded((record.get("provenance", {}), record.get("source_dataset", ""), record.get("record_id"), record.get("group_id")))
        if record.get("source_dataset") not in approved:
            raise ResearchPolicyError("Annotation source is not approved; no replacement corpus is selected")
        if record.get("partition") != "development":
            raise ResearchPolicyError("Blinded packet cannot expose calibration or holdout artifacts")
        key, group = record.get("record_id"), record.get("group_id")
        if not isinstance(key, str) or not key or key in ids or not isinstance(group, str) or not group:
            raise ValueError("Unique record and group identities are required")
        ids.add(key)
        fields = record.get("fields")
        if not isinstance(fields, Mapping) or not fields or any(type(v) is not str for v in fields.values()):
            raise ValueError("Original evidence fields required")
        permitted_fields = {"subject", "body", "sender", "reply_to", "title", "visible_text", "html", "page_url", "url"}
        if set(fields) - permitted_fields:
            raise ValueError("Annotation packet contains non-evidence fields")
        if record.get("modality") not in {entry["id"] for entry in load_codebook()["modalities"]}:
            raise ValueError("Packet requires canonical modality")
        _opportunity(record["modality"], fields)
        text_hash = hashlib.sha256(json.dumps(dict(fields), sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        annotation_id = f"annotation_{len(packet) + 1:06d}"
        blind_group = hashlib.sha256((record["source_dataset"] + "\0" + group).encode()).hexdigest()
        custody.append({"annotation_id": annotation_id, "source_record_id": key, "source_dataset": record["source_dataset"],
                        "source_group_id": group, "original_fields_sha256": text_hash,
                        "provenance": dict(record.get("provenance", {}))})
        packet.append({"record_id": annotation_id, "group_id": blind_group, "modality": record["modality"],
                       "fields": dict(fields), "text_hash": text_hash,
                       "indicators": {i: None for i in indicator_ids()}, "evidence": {},
                       "uncertainty": {}, "annotation_notes": ""})
    return {"schema_version": "1.0.0", "codebook_version": load_codebook()["codebook_version"],
            "judgments_generated": 0, "items": packet, "researcher_only_custody_manifest": custody,
            "delivery_policy": "Deliver items only to annotators; retain custody manifest separately"}


def validate_packet_response(packet_item: Mapping, response: Mapping) -> None:
    """Bind a human-completed response to the unchanged blinded artifact."""
    if not isinstance(packet_item, Mapping) or not isinstance(response, Mapping):
        raise ValueError("Packet item and response must be mappings")
    fields = packet_item.get("fields")
    if not isinstance(fields, Mapping):
        raise ValueError("Packet original fields missing")
    digest = hashlib.sha256(json.dumps(dict(fields), sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if packet_item.get("text_hash") != digest or response.get("text_hash") != digest:
        raise ValueError("Response must identify the unchanged blinded artifact")
    if response.get("record_id") != packet_item.get("record_id") or response.get("modality") != packet_item.get("modality"):
        raise ValueError("Response does not belong to this packet item")
    validate_judgment(response, fields)


def validate_adjudication(item: Mapping, reference_rows: list[Mapping], fields: Mapping[str, str]) -> None:
    """Require separately recorded human resolution; never choose a label by vote."""
    required = ("record_id", "indicator_id", "adjudicator_id", "review_date", "reason", "reference_annotator_ids")
    if any(not item.get(key) for key in required) or item["indicator_id"] not in indicator_ids():
        raise ValueError("Incomplete adjudication provenance")
    if any(type(item[key]) is not str or not item[key].strip() for key in required[:-1]):
        raise ValueError("Adjudication provenance must be explicit text")
    refs = item["reference_annotator_ids"]
    if not isinstance(refs, list) or any(type(ref) is not str or not ref for ref in refs) or len(set(refs)) < 2 or len(refs) != len(set(refs)) or item["adjudicator_id"] in refs:
        raise ValueError("Adjudication requires distinct reference annotators and adjudicator")
    available = {}
    for row in reference_rows:
        if row.get("record_id") == item["record_id"] and row.get("annotator_id") in refs:
            validate_judgment(row, fields)
            if row["annotator_id"] in available:
                raise ValueError("Duplicate reference annotator")
            if row["indicators"].get(item["indicator_id"]) not in STATES:
                raise ValueError("Adjudication references an unjudged indicator")
            available[row["annotator_id"]] = row
    if set(refs) != set(available):
        raise ValueError("Adjudication references unavailable judgments")
    if type(item.get("value")) is not str or item["value"] not in STATES:
        raise ValueError("Adjudication cannot fabricate a missing decision")
    if len({row["modality"] for row in available.values()}) != 1:
        raise ValueError("Adjudication reference modalities differ")
    judgment = {"record_id": item["record_id"], "annotator_id": item["adjudicator_id"],
                "role": item.get("role"), "qualifications": item.get("adjudicator_qualifications"),
                "review_date": item["review_date"], "protocol_version": item.get("protocol_version"),
                "codebook_version": load_codebook()["codebook_version"], "modality": next(iter(available.values()))["modality"],
                "independent": item.get("independent"), "model_output_visible": item.get("model_output_visible"),
                "source_provenance": item.get("source_provenance", {}),
                "indicators": {item["indicator_id"]: item["value"]},
                "evidence": {item["indicator_id"]: item.get("evidence", [])},
                "identity_reference_ids": item.get("identity_reference_ids", {})}
    validate_judgment(judgment, fields)


def acceptance_gate() -> dict:
    return {"independent_validation_complete": False, "scientific_policy_approved": False,
            "dataset_roles_approved": False, "Dhanwil_interface_confirmed": False,
            "approved_for_E2_E3": False, "approved_for_sealed_test": False,
            "publishable_as_validated_results": False}
