"""Versioned, no-fit interface comparison. Compatibility never grants release."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import re

from ml.research_policy import ResearchPolicyError, reject_excluded
from ml.se_brl.codebook import load_codebook
from ml.se_brl.representation_contract import contract
from ml.se_brl.semantic_candidates import semantic_configuration


INTERFACE_VERSION = "1.0.0"
DATA_FIELDS = {"integrity_artifacts", "partition_fingerprints", "group_fingerprints"}


def integration_interface(preflight: Mapping) -> dict:
    """Derive inspection-only compatibility requirements from a successful preflight."""
    if not isinstance(preflight, Mapping) or preflight.get("integrity_checks_pass") is not True or preflight.get("failures"):
        raise ValueError("Cannot prepare a handoff from failed local-integrity checks")
    codebook, representation = load_codebook(), contract()
    artifacts, seen = [], set()
    for item in preflight.get("checked_artifacts", []):
        if (not isinstance(item, Mapping) or type(item.get("path")) is not str or not item["path"]
                or Path(item["path"]).is_absolute() or ".." in Path(item["path"]).parts
                or item["path"] in seen or type(item.get("sha256")) is not str
                or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) or type(item.get("role")) is not str):
            raise ValueError("Malformed or duplicate handoff artifact")
        seen.add(item["path"])
        reject_excluded((item["path"], item["sha256"]))
        if item.get("accepted_for_research") is not False:
            raise ResearchPolicyError("Inspection custody is not dataset approval")
        artifacts.append({key: item[key] for key in ("path", "sha256", "role", "accepted_for_research")})
    datasets = preflight.get("datasets", {})
    if not artifacts or set(datasets) != {"email", "phiusiil", "iscx", "uci"} or any(
            entry.get("supplied_group_integrity") is not True or entry.get("feature_metadata_matches") is not True
            or entry.get("partition_manifest_matches") is not True for entry in datasets.values()):
        raise ValueError("Handoff requires consistent source/feature/partition metadata")
    for entry in datasets.values():
        for key in ("partition_metadata_sha256", "group_membership_sha256"):
            if type(entry.get(key)) is not str or not re.fullmatch(r"[0-9a-f]{64}", entry[key]):
                raise ValueError("Malformed handoff group/partition fingerprint")
    model, _ = semantic_configuration()
    return {
        "interface_schema_version": INTERFACE_VERSION,
        "canonical_schema_version": codebook["schema_version"], "codebook_version": codebook["codebook_version"],
        "representation_contract_version": representation["contract_version"],
        "indicator_order": representation["indicator_order"], "dimension_order": representation["dimension_order"],
        "feature_orders": {"learned": representation["learned_feature_order"], "historical_rule_binary": representation["historical_binary_feature_order"]},
        "representation_types": representation["representation_types"],
        "feature_definitions": {"rule_binary": representation["rule_binary"], "availability": representation["availability"],
                                "learned": "z1-z4 remain None until an accepted estimator exists"},
        "semantic_model_contract": {key: model[key] for key in ("model", "tokenizer", "revision", "hypotheses_sha256", "max_tokens", "oversized_evidence_policy", "confidence_calibrated")},
        "state_semantics": {"supported": "qualifying assessable evidence; accepted decisions require independent validation",
                            "absent": "assessable behavior not observed; not inferred from missingness",
                            "unavailable": "required evidence opportunity missing", "abstained": "decision withheld",
                            "missing": None, "learned_z_values": [None] * 4, "nli_confidence_calibrated": False},
        "modality_support": {item["id"]: dict(item["support_by_dimension"]) for item in codebook["modalities"]},
        "historical_dataset_identifiers": sorted(datasets),
        "historical_source_identifiers": ["CEAS-08", "Enron", "Nazario", "SpamAssassin", "PhiUSIIL", "UCI Phishing Websites", "ISCX-URL2016 Phishing"],
        "approved_active_dataset_ids": [], "accepted_behavioral_features": [],
        "integrity_artifacts": sorted(artifacts, key=lambda item: item["path"]),
        "partition_fingerprints": {key: datasets[key]["partition_metadata_sha256"] for key in sorted(datasets)},
        "group_fingerprints": {key: datasets[key]["group_membership_sha256"] for key in sorted(datasets)},
        "excluded_dataset_identifiers": list(preflight["excluded_datasets"]),
        "excluded_source_policy": "reject aliases, nested provenance, excluded fingerprints and unregistered/changed inputs; no fallback",
        "historical_result_limits": ["email_source_class_confounded", "holdouts_already_evaluated", "local_integrity_not_upstream_custody_or_scientific_acceptance"],
        "research_release": {"approved_for_E2_E3": False, "approved_for_sealed_test": False, "publishable_as_validated_results": False},
    }


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def compare_interface(expected: Mapping, supplied: Mapping | None) -> dict:
    """Compare declarations, not an unseen checkout. Never invent a commit."""
    pending = {"actual_interface_supplied": False, "schema_compatible": None, "data_compatible": None,
               "declaration_compatible": None, "authoritative_commit": None,
               "checkout_independently_verified": False, "research_release_approved": False,
               "status": "PENDING_DHANWIL_INTERFACE", "mismatches": []}
    if supplied is None:
        return pending
    errors = []
    if not isinstance(supplied, Mapping):
        return {**pending, "actual_interface_supplied": True, "status": "INCOMPATIBLE", "mismatches": ["interface_must_be_mapping"]}
    missing = set(expected) - set(supplied)
    extra = set(supplied) - set(expected) - {"authoritative_commit"}
    errors.extend(f"missing:{key}" for key in sorted(missing))
    errors.extend(f"unexpected:{key}" for key in sorted(extra))
    commit = supplied.get("authoritative_commit")
    if type(commit) is not str or not re.fullmatch(r"[0-9a-f]{40}", commit):
        errors.append("authoritative_commit_required_as_full_hex")
        commit = None
    try:
        # Exclusion declarations themselves intentionally name excluded sources;
        # only the fields claiming active/historical inputs are accepted inputs.
        reject_excluded([supplied.get(key) for key in (
            "approved_active_dataset_ids", "accepted_behavioral_features", "historical_dataset_identifiers",
            "historical_source_identifiers", "integrity_artifacts", "partition_fingerprints", "group_fingerprints")])
    except ResearchPolicyError:
        errors.append("excluded_source_or_fingerprint_in_interface_inputs")
    for key in sorted(set(expected) & set(supplied)):
        try:
            if _canonical(expected[key]) != _canonical(supplied[key]):
                errors.append(f"different:{key}")
        except (TypeError, ValueError):
            errors.append(f"malformed:{key}")
    data_errors = [error for error in errors if any(error.endswith(":" + field) for field in DATA_FIELDS)]
    general_errors = [error for error in errors if error not in data_errors]
    return {**pending, "actual_interface_supplied": True, "authoritative_commit": commit,
            "schema_compatible": not general_errors, "data_compatible": not data_errors and not any("excluded_" in error for error in errors),
            "declaration_compatible": not errors, "status": "DECLARATION_MATCH_RESEARCH_BLOCKED" if not errors else "INCOMPATIBLE",
            "mismatches": errors}


def load_interface(path: Path) -> Mapping:
    """Read bounded JSON only; reject duplicate keys and non-finite constants."""
    with Path(path).open("rb") as stream:
        payload = stream.read(1_000_001)
    if len(payload) > 1_000_000:
        raise ValueError("Interface document exceeds size limit")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate interface key")
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError("Non-finite JSON value")
    document = json.loads(payload, object_pairs_hook=unique, parse_constant=invalid_constant)
    if not isinstance(document, dict):
        raise ValueError("Interface JSON must be an object")
    return document
