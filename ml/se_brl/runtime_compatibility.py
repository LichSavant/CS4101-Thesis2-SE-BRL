"""Source-bound runtime declarations, not cross-repository approval.

No corpus is opened, no other checkout is executed, and no feature vector or
research permission is emitted. Matching version strings alone are insufficient.
"""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import re

from ml.metadata import canonical_json, fingerprint
from ml.research_policy import load_policy
from .codebook import load_codebook
from .representation_contract import contract
from .review_adapter import FIELD_KEYS, REQUEST_KEYS
from .semantic_review import POLICY_ID, REVIEW_VERSION, ROW_KEYS, TOP_KEYS, preprocessing_contract
from .semantic_candidates import semantic_configuration


DECLARATION_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = (
    "ml/preprocessing.py", "ml/datasets.py", "ml/metadata.py", "ml/research_policy.py", "ml/research-inputs.v1.json",
    "ml/behavioral_validation.py", "ml/annotation_validation.py",
    "ml/se_brl/context.py", "ml/se_brl/extraction.py", "ml/se_brl/detectors.py", "ml/se_brl/rules.py",
    "ml/se_brl/semantic_review.py", "ml/se_brl/review_adapter.py", "ml/se_brl/semantic_candidates.py",
    "ml/se_brl/codebook.py", "ml/se_brl/representation_contract.py", "ml/se_brl/runtime_compatibility.py",
)
OUTER_FIELDS = {"declaration_version", "base_commit", "source_state", "contracts", "research_release"}


def _source_fingerprints():
    # Only explicit implementation/configuration files; never inspect a corpus.
    return {name: hashlib.sha256((ROOT / name).read_text(encoding="utf-8").encode()).hexdigest() for name in SOURCE_FILES}


def runtime_declaration(*, base_commit: str | None = None, source_state: str = "working_tree") -> dict:
    if base_commit is not None and (type(base_commit) is not str or not re.fullmatch(r"[0-9a-f]{40}", base_commit)):
        raise ValueError("full_base_commit_required")
    if type(source_state) is not str or source_state not in {"working_tree", "committed"} or (source_state == "committed" and base_commit is None):
        raise ValueError("explicit_source_state_required")
    cb = load_codebook()
    model, _ = semantic_configuration()
    admission = load_policy()
    for key in ("approved_training_datasets", "approved_annotation_sources", "accepted_experiments"):
        if admission.get(key) != []:
            raise ValueError("runtime_declaration_requires_closed_research_admission")
    representation = contract()
    from ml.behavioral_validation import VALIDATION_VERSION, REFERENCE_SCHEMA_VERSION
    parents = {i["id"]: d["id"] for d in cb["dimensions"] for i in d["indicators"]}
    policy = {"policy_version": REVIEW_VERSION, "policy_id": POLICY_ID,
              "labels": "deterministic_observations_preserved", "neural_authority": "review_only",
              "source_custody": "caller_declaration_not_authenticated", "confidence": "uncalibrated"}
    return {"declaration_version": DECLARATION_VERSION, "base_commit": base_commit, "source_state": source_state,
            "contracts": {
                "codebook": {"schema_version": cb["schema_version"], "version": cb["codebook_version"], "semantic_sha256": fingerprint(cb)},
                "preprocessing": preprocessing_contract(),
                "admission": {"policy_version": admission["policy_version"], "configuration_sha256": fingerprint(admission),
                              "approved_training_datasets": [], "approved_annotation_sources": [], "accepted_experiments": []},
                "normalization": {"model_text": "HTML_unescape_then_NFKC_then_casefold_then_whitespace_collapse", "source_evidence": "unchanged_original_fields",
                                  "locators": "half_open_python_unicode_characters", "unknown": None,
                                  "known_empty_text": "", "known_empty_links": []},
                "taxonomy": {"indicator_order": list(parents), "parents": parents,
                             "dimension_order": list(cb["vector_ordering"]["dimension_order"]),
                             "modality_support": {m["id"]: dict(m["support_by_dimension"]) for m in cb["modalities"]}},
                "input": {"schema_version": REVIEW_VERSION, "required_fields": sorted(REQUEST_KEYS),
                          "modality_fields": {key: sorted(values) for key, values in FIELD_KEYS.items()},
                          "content_language": "explicit_english_only", "body_consent": "explicit_plus_study_purpose", "links": "opt_in"},
                "output": {"schema_version": REVIEW_VERSION, "envelope_fields": sorted(TOP_KEYS), "indicator_fields": sorted(ROW_KEYS),
                           "deterministic_states": ["supported", "absent", "unavailable", None],
                           "candidate_states": ["abstained", "unavailable"], "availability_mask": "four_strict_binary_values"},
                "representation": {key: representation[key] for key in ("representation_types", "learned_feature_order",
                                        "historical_binary_feature_order", "historical_dimension_aliases", "historical_indicator_aliases",
                                        "learned_values", "accepted_behavioral_features")},
                "semantic_model": {key: model[key] for key in ("model", "tokenizer", "revision", "hypotheses_sha256",
                                        "max_tokens", "oversized_evidence_policy", "confidence_calibrated")},
                "reference_validation": {"packet_schema_version": REFERENCE_SCHEMA_VERSION, "evaluation_plan_version": VALIDATION_VERSION,
                                         "independence_authenticated": False, "research_execution_authorized": False},
                "policy": policy, "source_files_utf8_lf_sha256": _source_fingerprints()},
            "research_release": {"approved_for_E2_E3": False, "approved_for_sealed_test": False,
                                 "publishable_as_validated_results": False}}


def parse_runtime_declaration(payload: str) -> dict:
    if type(payload) is not str:
        raise ValueError("bounded_runtime_json_required")
    try:
        if len(payload.encode("utf-8")) > 1_000_000:
            raise ValueError("runtime_declaration_too_large")
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate_runtime_key")
                result[key] = value
            return result
        def reject_constant(value):
            raise ValueError("nonfinite_runtime_value")
        document = json.loads(payload, object_pairs_hook=unique, parse_constant=reject_constant)
        if not isinstance(document, dict):
            raise ValueError("runtime_mapping_required")
        canonical_json(document)  # finite JSON and bounded metadata nesting
    except (UnicodeError, RecursionError):
        raise ValueError("invalid_runtime_json") from None
    return document


def compare_runtime_declaration(expected: Mapping, supplied: Mapping | None) -> dict:
    """Compare source/semantic claims; never authenticate a remote checkout."""
    pending = {"status": "PENDING_COUNTERPART_DECLARATION", "declaration_compatible": None,
               "counterpart_commit": None, "mismatches": [], "checkout_independently_verified": False,
               "integration_accepted": False, "research_release": False}
    if not isinstance(expected, Mapping) or set(expected) != OUTER_FIELDS:
        raise ValueError("expected_runtime_declaration_required")
    closed = {"approved_for_E2_E3": False, "approved_for_sealed_test": False, "publishable_as_validated_results": False}
    if (not isinstance(expected["contracts"], Mapping) or expected["declaration_version"] != DECLARATION_VERSION
            or canonical_json(expected["research_release"]) != canonical_json(closed)):
        raise ValueError("closed_expected_runtime_contract_required")
    if supplied is None:
        return pending
    errors = []
    if not isinstance(supplied, Mapping) or set(supplied) != OUTER_FIELDS:
        return {**pending, "status": "INVALID_DECLARATION", "declaration_compatible": False,
                "mismatches": ["runtime_envelope_fields"]}
    commit = supplied["base_commit"]
    if type(commit) is not str or not re.fullmatch(r"[0-9a-f]{40}", commit):
        errors.append("full_counterpart_commit_required")
        commit = None
    if supplied["source_state"] != "committed":
        errors.append("counterpart_committed_source_required")
    if supplied["declaration_version"] != expected["declaration_version"]:
        errors.append("declaration_version")
    try:
        if canonical_json(supplied["research_release"]) != canonical_json(expected["research_release"]):
            errors.append("closed_research_release_required")
        values = supplied["contracts"]
        if not isinstance(values, Mapping) or set(values) != set(expected["contracts"]):
            errors.append("runtime_contract_fields")
        else:
            for key, value in expected["contracts"].items():
                if canonical_json(values[key]) != canonical_json(value):
                    errors.append("contract:" + key)
    except (TypeError, ValueError, RecursionError):
        errors.append("malformed_runtime_contract")
    return {**pending, "status": "DECLARATION_MATCH_INTEGRATION_PENDING" if not errors else "INCOMPATIBLE",
            "declaration_compatible": not errors, "counterpart_commit": commit, "mismatches": errors}
