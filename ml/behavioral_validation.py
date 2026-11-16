"""Human-reference import and evaluation planning; no scientific approval.

No files, datasets, models, or existing annotations are loaded or modified.
Human identity/blinding declarations are validated structurally, not authenticated.
The research evaluation entry point stays closed. Pure arithmetic is testable on
synthetic pairs and must never be represented as independent behavioral evidence.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import math
from statistics import NormalDist

from ml.annotation_validation import _opportunity, coverage, indicator_ids, validate_packet_response, validate_adjudication
from ml.metadata import canonical_json, fingerprint, freeze_json, json_value, require_text
from ml.preprocessing import MAX_FIELD_CHARS
from ml.research_policy import reject_excluded, require_stage_authorization
from ml.se_brl.codebook import load_codebook
from ml.se_brl.rules import RULESET_VERSION
from ml.se_brl.semantic_review import POLICY_ID, REVIEW_VERSION, preprocessing_contract
from ml.se_brl.semantic_candidates import semantic_configuration


VALIDATION_VERSION = "1.1.0"
REFERENCE_SCHEMA_VERSION = "1.0.0"
STATES = {"supported", "absent", "unavailable"}
RESPONSE_FIELDS = {"record_id", "text_hash", "annotator_id", "role", "qualifications", "review_date",
                   "protocol_version", "codebook_version", "modality", "independent", "model_output_visible",
                   "indicators", "evidence", "identity_reference_ids", "source_provenance", "uncertainty", "annotation_notes"}
PACKET_FIELDS = {"record_id", "group_id", "modality", "fields", "text_hash", "indicators", "evidence",
                 "uncertainty", "annotation_notes", "codebook_version", "schema_version"}
ADJUDICATION_FIELDS = {"record_id", "indicator_id", "text_hash", "adjudicator_id", "review_date", "reason",
                       "reference_annotator_ids", "value", "role", "adjudicator_qualifications", "protocol_version",
                       "independent", "model_output_visible", "evidence", "identity_reference_ids", "source_provenance",
                       "codebook_version", "modality"}
ABSTENTION_POLICY = "explicit selective metrics; never impute abstentions as ordinary negatives"
INTERVAL_POLICY = "Wilson iid binomial diagnostics only; clustered study intervals require approved policy"


def _review_runtime_binding() -> str:
    # Version strings alone do not identify executable policy/context behavior.
    from ml.se_brl.runtime_compatibility import runtime_declaration
    return fingerprint(runtime_declaration()["contracts"])


def _validate_blinded_packet(packet: Mapping) -> None:
    """Check an unchanged blank instrument; never construct reference judgments."""
    required = {"record_id", "group_id", "modality", "fields", "text_hash"}
    if not isinstance(packet, Mapping) or set(packet) - PACKET_FIELDS or not required <= set(packet):
        raise ValueError("blinded_packet_schema_mismatch")
    for key in ("record_id", "group_id"):
        require_text(packet[key])
        if len(packet[key]) > 1024 or any(ord(c) < 32 for c in packet[key]):
            raise ValueError("bounded_blinded_identifier_required")
        reject_excluded(packet[key])
    fields = packet["fields"]
    if (type(packet["modality"]) is not str or not isinstance(fields, Mapping)
            or any(type(v) is not str or len(v) > MAX_FIELD_CHARS for v in fields.values())):
        raise ValueError("bounded_original_packet_fields_required")
    _opportunity(packet["modality"], fields)
    digest = hashlib.sha256(json.dumps(json_value(fields), sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if packet["text_hash"] != digest:
        raise ValueError("blinded_packet_artifact_binding_mismatch")
    if packet.get("codebook_version", load_codebook()["codebook_version"]) != load_codebook()["codebook_version"]:
        raise ValueError("blinded_packet_codebook_mismatch")
    if packet.get("schema_version", REFERENCE_SCHEMA_VERSION) != REFERENCE_SCHEMA_VERSION:
        raise ValueError("blinded_packet_schema_version_mismatch")
    cells = packet.get("indicators", {})
    if not isinstance(cells, Mapping) or set(cells) - set(indicator_ids()) or any(v is not None for v in cells.values()):
        raise ValueError("blinded_packet_cannot_contain_reference_labels")
    for key in ("evidence", "uncertainty"):
        value = packet.get(key, {})
        if not isinstance(value, Mapping) or value:
            raise ValueError("blinded_packet_cannot_contain_prior_judgments")
    if packet.get("annotation_notes", "") != "":
        raise ValueError("blinded_packet_cannot_contain_review_hints")


def _json_document(payload: str):
    if type(payload) is not str:
        raise ValueError("bounded_utf8_reference_json_required")
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate_reference_json_key")
            value[key] = item
        return value
    def invalid(value):
        raise ValueError("nonfinite_reference_json")
    try:
        if len(payload.encode("utf-8")) > 1_000_000:
            raise ValueError("bounded_utf8_reference_json_required")
        return json.loads(payload, object_pairs_hook=unique, parse_constant=invalid)
    except (UnicodeError, RecursionError, json.JSONDecodeError):
        raise ValueError("invalid_reference_json") from None


@dataclass(frozen=True, slots=True)
class ReferenceBatch:
    packets: tuple[Mapping, ...] = field(repr=False)
    responses: tuple[Mapping, ...] = field(repr=False)
    sha256: str
    human_independence_authenticated: bool = False

    def __post_init__(self):
        if self.human_independence_authenticated is not False:
            raise ValueError("software_cannot_authenticate_independent_humans")
        if (not isinstance(self.packets, (list, tuple)) or not isinstance(self.responses, (list, tuple))
                or len(self.packets) > 10_000 or len(self.responses) > 10_000
                or any(not isinstance(p, Mapping) for p in self.packets) or any(not isinstance(r, Mapping) for r in self.responses)):
            raise ValueError("reference_packet_and_response_mappings_required")
        packets = tuple(freeze_json(p) for p in self.packets)
        responses = tuple(freeze_json(r) for r in self.responses)
        for packet in packets:
            _validate_blinded_packet(packet)
        # Freeze only after validators have seen ordinary JSON lists.
        by_id = {p["record_id"]: p for p in packets}
        if len(by_id) != len(packets) or not responses:
            raise ValueError("unique_packets_and_nonempty_responses_required")
        for p in packets:
            require_text(p.get("record_id"))
            require_text(p.get("group_id"))
            reject_excluded((p["record_id"], p["group_id"]))
        keys = set()
        for row in responses:
            if set(row) - RESPONSE_FIELDS:
                raise ValueError("unknown_reference_fields_or_independence_claims")
            require_text(row.get("record_id"))
            require_text(row.get("annotator_id"))
            key = (row.get("record_id"), row.get("annotator_id"))
            if key in keys or key[0] not in by_id:
                raise ValueError("duplicate_or_unbound_reference_response")
            keys.add(key)
            validate_packet_response(json_value(by_id[key[0]]), json_value(row))
        if self.sha256 != fingerprint({"packets": packets, "responses": responses}):
            raise ValueError("reference_batch_fingerprint_mismatch")
        object.__setattr__(self, "packets", packets)
        object.__setattr__(self, "responses", responses)


def import_human_responses(packet_items: Sequence[Mapping], payload: str) -> ReferenceBatch:
    """Validate declared human responses; no label filling, voting or approval."""
    rows = _json_document(payload)
    if not isinstance(rows, list) or not rows or len(rows) > 10_000:
        raise ValueError("nonempty_reference_response_list_required")
    if not isinstance(packet_items, (list, tuple)) or len(packet_items) > 10_000:
        raise ValueError("bounded_packet_sequence_required")
    if any(not isinstance(p, Mapping) for p in packet_items):
        raise ValueError("reference_packet_mappings_required")
    packets = tuple(dict(p) for p in packet_items)
    for p in packets:
        require_text(p.get("record_id"))
        require_text(p.get("group_id"))
        reject_excluded((p["record_id"], p["group_id"]))
    return ReferenceBatch(packets, tuple(rows), fingerprint({"packets": packets, "responses": rows}))


def reference_coverage(batch: ReferenceBatch, *, expected_annotator_ids: tuple[str, ...]) -> dict:
    """Count unanswered responses and partial cells without fabricating judgments."""
    if (not isinstance(batch, ReferenceBatch) or type(expected_annotator_ids) is not tuple
            or not expected_annotator_ids or any(type(a) is not str or not a.strip() for a in expected_annotator_ids)
            or len(set(expected_annotator_ids)) != len(expected_annotator_ids)):
        raise ValueError("explicit_distinct_expected_annotators_required")
    if any(r["annotator_id"] not in expected_annotator_ids for r in batch.responses):
        raise ValueError("unexpected_reference_annotator")
    result = coverage(json_value(batch.responses))
    expected = len(batch.packets) * len(expected_annotator_ids)
    unanswered = expected - len(batch.responses)
    for row in result["indicators"].values():
        row["missing"] += unanswered
    return {**result, "expected_responses": expected, "received_responses": len(batch.responses),
            "unanswered_responses": unanswered, "independence_authenticated": False}


def import_adjudications(batch: ReferenceBatch, payload: str) -> tuple[Mapping, ...]:
    """Bind separately recorded adjudications; preserve all original responses."""
    if not isinstance(batch, ReferenceBatch):
        raise ValueError("validated_reference_batch_required")
    rows = _json_document(payload)
    if not isinstance(rows, list) or len(rows) > 10_000:
        raise ValueError("bounded_adjudication_list_required")
    packets = {p["record_id"]: p for p in batch.packets}
    seen = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("adjudication_mapping_required")
        if set(row) - ADJUDICATION_FIELDS:
            raise ValueError("unknown_adjudication_fields_or_authority_claims")
        require_text(row.get("record_id"))
        require_text(row.get("indicator_id"))
        key = (row.get("record_id"), row.get("indicator_id"))
        if key in seen or key[0] not in packets:
            raise ValueError("duplicate_or_unbound_adjudication")
        seen.add(key)
        packet = packets[key[0]]
        refs = row.get("reference_annotator_ids")
        if not isinstance(refs, list) or any(type(value) is not str for value in refs):
            raise ValueError("explicit_adjudication_reference_ids_required")
        if row.get("text_hash") != packet["text_hash"]:
            raise ValueError("adjudication_artifact_binding_required")
        if row.get("codebook_version", load_codebook()["codebook_version"]) != load_codebook()["codebook_version"]:
            raise ValueError("adjudication_codebook_mismatch")
        if row.get("modality", packet["modality"]) != packet["modality"]:
            raise ValueError("adjudication_modality_mismatch")
        if any(r["protocol_version"] != row.get("protocol_version") for r in batch.responses
               if r["record_id"] == key[0] and r["annotator_id"] in refs):
            raise ValueError("adjudication_reference_protocol_mismatch")
        validate_adjudication(row, json_value(batch.responses), json_value(packet["fields"]))
    return tuple(freeze_json(row) for row in rows)


@dataclass(frozen=True, slots=True)
class EvaluationManifest:
    """Immutable plan, not authorization to execute or an authenticity signature."""
    canonical_document: str
    sha256: str

    def __post_init__(self):
        document = _json_document(self.canonical_document)
        required = {"schema_version", "codebook_version", "indicator_order", "reference_set_sha256",
                    "protocol_version", "policy_id", "policy_version", "ruleset_version", "semantic_model",
                    "assignments", "group_assignments_sha256", "artifact_bindings", "reference_response_hashes", "adjudication_hashes",
                    "human_independence_authenticated", "research_execution_authorized", "abstention_policy", "interval_policy", "preprocessing_contract", "review_runtime_sha256"}
        model, _ = semantic_configuration()
        if (canonical_json(document) != self.canonical_document
                or hashlib.sha256(self.canonical_document.encode()).hexdigest() != self.sha256
                or not isinstance(document, dict) or set(document) != required
                or document.get("schema_version") != VALIDATION_VERSION
                or document.get("codebook_version") != load_codebook()["codebook_version"]
                or document.get("indicator_order") != list(indicator_ids())
                or document.get("policy_id") != POLICY_ID or document.get("policy_version") != REVIEW_VERSION
                or document.get("ruleset_version") != RULESET_VERSION
                or document.get("preprocessing_contract") != preprocessing_contract()
                or document.get("review_runtime_sha256") != _review_runtime_binding()
                or document.get("semantic_model") != {k: model[k] for k in ("model", "tokenizer", "revision", "hypotheses_sha256")}
                or document.get("human_independence_authenticated") is not False
                or document.get("abstention_policy") != ABSTENTION_POLICY
                or document.get("interval_policy") != INTERVAL_POLICY
                or document.get("research_execution_authorized") is not False):
            raise ValueError("invalid_immutable_evaluation_manifest")
        require_text(document["protocol_version"])
        def sha(value):
            return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
        if (not sha(document["reference_set_sha256"]) or not sha(document["group_assignments_sha256"])
                or not isinstance(document["assignments"], dict) or not document["assignments"]
                or not isinstance(document["artifact_bindings"], dict)
                or set(document["assignments"]) != set(document["artifact_bindings"])
                or any(type(value) is not str or value not in {"development", "calibration"} for value in document["assignments"].values())
                or not all(sha(v) for v in document["artifact_bindings"].values())
                or not isinstance(document["reference_response_hashes"], list) or not document["reference_response_hashes"]
                or not all(sha(v) for v in document["reference_response_hashes"])
                or not isinstance(document["adjudication_hashes"], list)
                or not all(sha(v) for v in document["adjudication_hashes"])):
            raise ValueError("invalid_evaluation_bindings")

    def to_dict(self):
        return json.loads(self.canonical_document)


def plan_validation(batch: ReferenceBatch, assignments: Mapping[str, str], *, protocol_version: str,
                    adjudications: tuple[Mapping, ...] = ()) -> EvaluationManifest:
    """Check supplied group separation; never generate splits or access holdouts."""
    if not isinstance(batch, ReferenceBatch) or not isinstance(assignments, Mapping):
        raise ValueError("validated_references_and_explicit_assignments_required")
    require_text(protocol_version)
    ids = {p["record_id"] for p in batch.packets}
    if set(assignments) != ids or not ids:
        raise ValueError("assignments_must_cover_exact_packet_ids")
    groups = {}
    for p in batch.packets:
        group, partition = p["group_id"], assignments[p["record_id"]]
        # A future sealed-test protocol needs separate reviewed implementation.
        if partition not in {"development", "calibration"}:
            raise ValueError("sealed_test_or_unknown_partition_not_authorized")
        if groups.setdefault(group, partition) != partition:
            raise ValueError("reference_group_crosses_partitions")
    if any(row["protocol_version"] != protocol_version for row in batch.responses):
        raise ValueError("reference_protocol_version_mismatch")
    # Revalidate even previously imported decisions against this exact batch.
    bound_adjudications = import_adjudications(batch, json.dumps(json_value(adjudications)))
    if any(row["protocol_version"] != protocol_version for row in bound_adjudications):
        raise ValueError("adjudication_protocol_version_mismatch")
    model, _ = semantic_configuration()
    document = {"schema_version": VALIDATION_VERSION, "codebook_version": load_codebook()["codebook_version"],
                "indicator_order": list(indicator_ids()), "reference_set_sha256": batch.sha256,
                "protocol_version": protocol_version, "policy_id": POLICY_ID, "policy_version": REVIEW_VERSION,
                "ruleset_version": RULESET_VERSION,
                "preprocessing_contract": preprocessing_contract(),
                "review_runtime_sha256": _review_runtime_binding(),
                "semantic_model": {k: model[k] for k in ("model", "tokenizer", "revision", "hypotheses_sha256")},
                "assignments": dict(assignments), "group_assignments_sha256": fingerprint(groups),
                "artifact_bindings": {p["record_id"]: p["text_hash"] for p in batch.packets},
                "reference_response_hashes": sorted(fingerprint(r) for r in batch.responses),
                "adjudication_hashes": sorted(fingerprint(r) for r in bound_adjudications),
                "human_independence_authenticated": False, "research_execution_authorized": False,
                "abstention_policy": ABSTENTION_POLICY,
                "interval_policy": INTERVAL_POLICY}
    serialized = canonical_json(document)
    return EvaluationManifest(serialized, hashlib.sha256(serialized.encode()).hexdigest())


def verify_evaluation_manifest(manifest: EvaluationManifest, batch: ReferenceBatch, assignments: Mapping[str, str], *,
                               protocol_version: str, adjudications: tuple[Mapping, ...] = ()) -> None:
    """Bind a stored plan back to exact references, assignments and current code."""
    if not isinstance(manifest, EvaluationManifest):
        raise ValueError("typed_evaluation_manifest_required")
    expected = plan_validation(batch, assignments, protocol_version=protocol_version, adjudications=adjudications)
    if manifest.sha256 != expected.sha256 or manifest.canonical_document != expected.canonical_document:
        raise ValueError("evaluation_manifest_does_not_bind_current_inputs")


def wilson_interval(successes: int, trials: int, *, confidence: float = 0.95) -> tuple[float, float] | None:
    """Pure binomial arithmetic; not a campaign/group-aware study interval."""
    if (type(successes) is not int or type(trials) is not int or not 0 <= successes <= trials
            or type(confidence) not in (float, int) or not math.isfinite(confidence) or not 0 < confidence < 1):
        raise ValueError("valid_binomial_counts_and_confidence_required")
    if not trials:
        return None
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    proportion, scale = successes / trials, 1 + z * z / trials
    center = (proportion + z * z / (2 * trials)) / scale
    radius = z * math.sqrt(proportion * (1 - proportion) / trials + z * z / (4 * trials * trials)) / scale
    return max(0.0, center - radius), min(1.0, center + radius)


def synthetic_pair_statistics(pairs: Sequence[tuple[Mapping, Mapping]]) -> dict:
    """Explicit synthetic arithmetic harness, never independent study evaluation.

    Each pair is (reference indicator map, prediction indicator map). Real-study
    execution must use the separately gated entry point below after approval.
    """
    if not isinstance(pairs, (list, tuple)) or len(pairs) > 10_000:
        raise ValueError("bounded_synthetic_pairs_required")
    ids = indicator_ids()
    for pair in pairs:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("reference_prediction_pair_required")
        for index, values in enumerate(pair):
            allowed = STATES | ({"abstained"} if index else set())
            if (not isinstance(values, Mapping) or set(values) - set(ids)
                    or any(v is not None and (type(v) is not str or v not in allowed) for v in values.values())):
                raise ValueError("canonical_explicit_reference_prediction_states_required")
    result = {}
    for indicator in ids:
        counts = Counter()
        for reference, prediction in pairs:
            ref, pred = reference.get(indicator), prediction.get(indicator)
            if ref is None:
                counts["reference_missing"] += 1
            elif ref == "unavailable":
                counts["reference_unavailable"] += 1
            elif pred not in {"supported", "absent"}:
                counts[{None: "prediction_missing", "abstained": "prediction_abstained", "unavailable": "prediction_unavailable"}[pred]] += 1
            else:
                counts[{("supported", "supported"): "tp", ("absent", "supported"): "fp",
                        ("supported", "absent"): "fn", ("absent", "absent"): "tn"}[(ref, pred)]] += 1
        for key in ("tp", "fp", "fn", "tn", "reference_missing", "reference_unavailable",
                    "prediction_missing", "prediction_abstained", "prediction_unavailable"):
            counts[key] += 0
        tp, fp, fn, tn = (counts[k] for k in ("tp", "fp", "fn", "tn"))
        eligible = len(pairs) - counts["reference_missing"] - counts["reference_unavailable"]
        decided = tp + fp + fn + tn
        result[indicator] = {**dict(counts), "eligible_references": eligible, "decided": decided,
                             "coverage": decided / eligible if eligible else None,
                             "precision": tp / (tp + fp) if tp + fp else None,
                             "recall_among_decided": tp / (tp + fn) if tp + fn else None,
                             "f1_among_decided": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
                             "precision_interval_iid": wilson_interval(tp, tp + fp),
                             "recall_interval_iid_among_decided": wilson_interval(tp, tp + fn),
                             "coverage_interval_iid": wilson_interval(decided, eligible),
                             "f1_interval": None}
    return {"verification_kind": "synthetic_arithmetic_only", "independent_validation": False,
            "interval_limitations": "iid binomial diagnostics; not group-aware uncertainty; no F1 interval asserted",
            "indicators": result}


def evaluate_independent_references(*args, **kwargs):
    """Fail before reading predictions/references until a reviewed protocol exists."""
    require_stage_authorization("validation")
