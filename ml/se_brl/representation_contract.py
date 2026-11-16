"""Versioned handoff semantics; rule bits and NLI scores are never learned z."""

from enum import StrEnum

from ml.research_policy import ResearchPolicyError, require_stage_authorization
from .codebook import load_codebook


CONTRACT_VERSION = "1.0.0"


class RepresentationKind(StrEnum):
    RULE_BINARY = "rule_derived_binary_v1"
    SEMANTIC_CANDIDATE = "semantic_candidate_v1"
    VALIDATED_DECISION = "validated_behavioral_decision_v1"
    LEARNED = "learned_dimension_values_v1"


def contract() -> dict:
    codebook = load_codebook()
    return {
        "contract_version": CONTRACT_VERSION,
        "codebook_version": codebook["codebook_version"],
        "source_schema_version": codebook["schema_version"],
        "dimension_order": list(codebook["vector_ordering"]["dimension_order"]),
        "indicator_order": [item["id"] for dim in codebook["dimensions"] for item in dim["indicators"]],
        "learned_feature_order": list(codebook["vector_ordering"]["future_structure"]),
        "historical_binary_feature_order": [f"{dim}_{suffix}" for suffix in ("supported", "available")
            for dim in ("pressure_threat", "lure_attention", "trust_identity", "requested_action_consequence")],
        "historical_dimension_aliases": {
            "pressure_threat": "pressure_threat_cues", "lure_attention": "lure_attention_cues",
            "trust_identity": "trust_identity_manipulation", "requested_action_consequence": "requested_action_consequence"},
        "historical_indicator_aliases": {"credential_sensitive_request": "credential_sensitive_data_request"},
        "historical_adapter_policy": "explicit schema mapping only; never rewrite protected files or reinterpret bits as z",
        "representation_types": [kind.value for kind in RepresentationKind],
        "rule_binary": "0/1 observations, never calibrated confidence or learned z",
        "semantic_candidate": "uncalibrated NLI evidence for review, never accepted judgment",
        "validated_decision": "requires independent references and an approved decision policy",
        "availability": "evidence opportunity; unavailable is not an ordinary negative",
        "abstention": "decision withheld despite possible evidence; not absent or unavailable",
        "uncertainty": "record separately; never impute a missing label or value",
        "learned_values": [None, None, None, None],
        "accepted_behavioral_features": [],
        "approved_for_E2_E3": False,
    }


def validate_values(kind: RepresentationKind | str, values: tuple) -> None:
    kind = RepresentationKind(kind)
    if kind == RepresentationKind.RULE_BINARY:
        if len(values) != 8 or any(type(v) is not int or v not in (0, 1) for v in values):
            raise ResearchPolicyError("Rule representation requires four bits and four availability bits")
        if any(v > a for v, a in zip(values[:4], values[4:])):
            raise ResearchPolicyError("Unavailable dimensions cannot assert rule support")
    elif kind == RepresentationKind.LEARNED:
        if len(values) != 8 or values[:4] != (None,) * 4:
            raise ResearchPolicyError("No accepted estimator provides learned z values")
        if any(type(v) is not int or v not in (0, 1) for v in values[4:]):
            raise ResearchPolicyError("Availability requires strict binary values")
    else:
        raise ResearchPolicyError("Candidate/validated decisions are evidence records, not numeric z vectors")


def require_experiment_ready(configuration: str, kind: RepresentationKind | str) -> None:
    RepresentationKind(kind)
    if configuration not in {"E1", "E2", "E3"}:
        raise ResearchPolicyError("Unknown experiment configuration")
    require_stage_authorization("training")
