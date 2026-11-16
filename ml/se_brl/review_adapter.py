"""Proposed evidence-only adapter; no endpoint, predictor export or corpus loader.

Dhanwil's EmailEvidenceInput has subject/body/sender/links wrappers, without
observation identity or collection consent. Those must be supplied separately.
This adapter never reads a source target, group, fold, partition or raw provenance.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
import re

from ml.datasets import DatasetRecord
from ml.metadata import require_text
from ml.research_policy import reject_excluded
from .codebook import load_codebook
from .semantic_review import REVIEW_VERSION, ReviewContractError, preprocessing_contract, review_record, validate_review


REQUEST_KEYS = {"schema_version", "codebook_version", "artifact_id", "source_id", "source_reference",
                "modality", "language", "fields", "body_collection_authorized",
                "link_extraction_authorized", "study_purpose"}
KINDS = {"content_bearing_email": "email", "content_bearing_webpage": "webpage",
         "standalone_url": "url", "engineered_technical_record": "technical"}
FIELD_KEYS = {"content_bearing_email": {"subject", "body", "sender", "reply_to", "headers", "urls"},
              "content_bearing_webpage": {"html", "visible_text", "title", "page_url", "urls"},
              "standalone_url": {"url", "urls"}, "engineered_technical_record": set()}


def record_from_request(request: Mapping) -> DatasetRecord:
    if not isinstance(request, Mapping) or set(request) != REQUEST_KEYS:
        raise ReviewContractError("evidence_request_schema_mismatch")
    if request["schema_version"] != REVIEW_VERSION or request["codebook_version"] != load_codebook()["codebook_version"]:
        raise ReviewContractError("incompatible_evidence_request_version")
    for key in ("artifact_id", "source_id", "source_reference"):
        value = request[key]
        require_text(value)
        if len(value) > 1024 or any(ord(c) < 32 for c in value):
            raise ReviewContractError("bounded_opaque_identifier_required")
        reject_excluded(value)
    modality = request["modality"]
    if type(modality) is not str or modality not in KINDS:
        raise ReviewContractError("canonical_modality_required")
    language = request["language"]
    if type(language) is not str or not re.fullmatch(r"[a-z]{2,3}(?:-[a-z0-9]{2,8})*", language):
        raise ReviewContractError("explicit_language_required")
    if modality in {"content_bearing_email", "content_bearing_webpage"} and language.split("-")[0] != "en":
        raise ReviewContractError("unsupported_or_unknown_language")
    values = request["fields"]
    if not isinstance(values, Mapping) or set(values) - FIELD_KEYS[modality] or len(values) > 8:
        raise ReviewContractError("evidence_only_fields_required")
    for flag in ("body_collection_authorized", "link_extraction_authorized"):
        if type(request[flag]) is not bool:
            raise ReviewContractError("explicit_boolean_consent_required")
    if type(request["study_purpose"]) is not str or len(request["study_purpose"]) > 2000:
        raise ReviewContractError("bounded_study_purpose_required")
    raw = {"kind": KINDS[modality], **dict(values), "link_extraction_authorized": request["link_extraction_authorized"]}
    if modality == "content_bearing_email":
        raw.update(body_collection_authorized=request["body_collection_authorized"], study_purpose=request["study_purpose"])
    elif request["body_collection_authorized"]:
        raise ReviewContractError("email_body_consent_not_applicable")
    # Header and URL types and all original-field limits are checked by preprocess.
    record = DatasetRecord(request["artifact_id"], request["source_id"], modality, raw, tuple(values), None,
                           {"reference": request["source_reference"], "language_declared": language})
    from ml.datasets import prepare_record
    prepare_record(record)
    return record


def analyze_evidence(request: Mapping, *, scorer=None, detector_context=None) -> dict:
    record = record_from_request(request)
    report = review_record(record, scorer=scorer, detector_context=detector_context).to_dict()
    validate_review(report, record, detector_context=detector_context)
    return report


def email_request_from_view(view, *, artifact_id: str, source_id: str, source_reference: str,
                            language: str, body_collection_authorized: bool = False,
                            link_extraction_authorized: bool = False, study_purpose: str = "") -> dict:
    """Shape bridge for the published evidence-only dataclass, not an observation.

    None is omitted (unavailable); explicit empty strings/tuples remain known
    empty. Collection consent cannot be inferred from the presence of content.
    """
    if not is_dataclass(view) or isinstance(view, type) or {f.name for f in fields(view)} != {"subject", "body", "sender", "links"}:
        raise ReviewContractError("evidence_only_view_required")
    supplied = {}
    for source, dest in (("subject", "subject"), ("body", "body"), ("sender", "sender"), ("links", "urls")):
        wrapper = getattr(view, source)
        if not is_dataclass(wrapper) or isinstance(wrapper, type) or {f.name for f in fields(wrapper)} != {"value"}:
            raise ReviewContractError("typed_availability_wrapper_required")
        value = wrapper.value
        if value is not None:
            if source == "links":
                if type(value) is not tuple:
                    raise ReviewContractError("supplied_link_tuple_required")
                supplied[dest] = list(value)
            else:
                if type(value) is not str:
                    raise ReviewContractError("original_text_required")
                supplied[dest] = value
    request = {"schema_version": REVIEW_VERSION, "codebook_version": load_codebook()["codebook_version"],
               "artifact_id": artifact_id, "source_id": source_id, "source_reference": source_reference,
               "modality": "content_bearing_email", "language": language, "fields": supplied,
               "body_collection_authorized": body_collection_authorized,
               "link_extraction_authorized": link_extraction_authorized, "study_purpose": study_purpose}
    record_from_request(request)
    return request


def interface_specification() -> dict:
    cb = load_codebook()
    return {"schema_version": REVIEW_VERSION, "status": "proposed_engineering_adapter_not_research_approval",
            "request_fields": sorted(REQUEST_KEYS), "codebook_version": cb["codebook_version"],
            "preprocessing_contract": preprocessing_contract(),
            "indicator_order": [i["id"] for d in cb["dimensions"] for i in d["indicators"]],
            "dimension_order": list(cb["vector_ordering"]["dimension_order"]),
            "state_policy": "deterministic observations preserved; NLI candidates abstained or unavailable",
            "offset_units": "half-open Python Unicode character indices in the named original field",
            "predictor_export": "blocked; output is evidence/review bookkeeping, not an E2/E3 feature vector",
            "forbidden_predictor_inputs": ["target", "source_label", "native_label", "partition", "cv_fold", "group_id", "provenance"],
            "collection_policy": "explicit body authorization plus study purpose; extracted links opt-in",
            "external_commit_verified": "6a41d94d4e4f88c77c08bf7ea20a6ca59d192136",
            "external_checkout_execution_verified": False, "scientific_release": False}
