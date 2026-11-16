"""Versioned artifact DecisionObject and SRS 4.6 precedence; no user scoring.

Numerical settings are supplied by a compatible bundle, never defaults inferred
from results. Synthetic policy settings do not become approved research rules.
"""
from dataclasses import dataclass
import math
import re

from ml.experiment_inputs import InputContractError

SCHEMA_VERSION = "artifact-decision-1.0"
POLICY_VERSION = "srs-4.6-precedence-1.0"
FAMILIES = frozenset({"behavioral_language", "identity_authentication", "url_destination",
                      "form_structure", "brand_domain_relation"})
RESPONSES = {
    "review_required": ("Analysis is incomplete or incompatible. Verify independently before acting.",
                        "Do not submit credentials or payments based on this result."),
    "high": ("Do not submit credentials or payments through this artifact.",
             "Verify using an independently known contact or service address."),
    "elevated": ("Pause before following requests or links.",
                 "Verify the request through an independently known channel."),
    "informational": ("No higher tier was established by this analysis; this does not certify safety.",
                      "Continue ordinary verification before sharing sensitive information."),
}


@dataclass(frozen=True, slots=True)
class RiskPolicy:
    low: float
    high: float
    minimum_coverage: float
    reference: str
    scope: str

    def __post_init__(self):
        if (any(type(v) not in (int, float) or not math.isfinite(v) for v in (self.low, self.high, self.minimum_coverage))
                or not 0 <= self.low < self.high <= 1 or not 0 <= self.minimum_coverage <= 1
                or type(self.reference) is not str or not self.reference.strip()
                or self.scope not in {"synthetic_fixture", "frozen_research"}):
            raise InputContractError("explicit_risk_policy_required")


def decide(probability, *, severity, families, coverage, policy, reasons=()):
    if (not isinstance(policy, RiskPolicy) or type(severity) is not int or severity not in range(4)
            or type(families) is not tuple or len(set(families)) != len(families)
            or not set(families) <= FAMILIES or type(coverage) not in (int, float)
            or not math.isfinite(coverage) or not 0 <= coverage <= 1
            or type(reasons) is not tuple or any(type(r) is not str or not re.fullmatch(r"[a-z0-9_]+", r) for r in reasons)):
        raise InputContractError("risk_input_invalid")
    invalid_probability = type(probability) not in (float, int) or not math.isfinite(probability) or not 0 <= probability <= 1
    blockers = tuple(dict.fromkeys(reasons + (("probability_unavailable",) if invalid_probability else ())
                                   + (("insufficient_coverage",) if coverage < policy.minimum_coverage else ())))
    technical = set(families) - {"behavioral_language"}
    if blockers:
        tier = "review_required"
    elif probability >= policy.high and (severity >= 2 or len(families) >= 2):
        tier = "high"
    elif probability >= policy.low or (severity >= 2 and technical):
        tier = "elevated"
    elif severity < 2:
        tier = "informational"
    else:
        tier, blockers = "review_required", ("severe_request_without_corroboration",)
    return {"tier": tier, "reasons": list(blockers), "severity": severity,
            "corroborating_families": list(families), "coverage": coverage,
            "policy_version": POLICY_VERSION, "policy_reference": policy.reference,
            "policy_scope": policy.scope, "actions": list(RESPONSES[tier])}


def validate_decision(value):
    """Assembler invariants, also applied before returning any API result."""
    required = {"schema_version", "run_id", "artifact_sha256", "modality", "status", "result_category",
                "research_validated", "classification", "calibrated_probability", "technical_findings",
                "behavioral_evidence", "attribution", "decision", "limitations", "versions", "timing_ms"}
    if type(value) is not dict or set(value) != required or value["schema_version"] != SCHEMA_VERSION:
        raise InputContractError("decision_schema_invalid")
    if (not re.fullmatch(r"[a-f0-9]{64}", value["artifact_sha256"])
            or not re.fullmatch(r"[a-f0-9]{32}", value["run_id"])
            or value["status"] not in {"complete", "review_required"}
            or value["decision"]["tier"] not in RESPONSES or type(value["research_validated"]) is not bool):
        raise InputContractError("decision_identity_or_state_invalid")
    p = value["calibrated_probability"]
    if value["status"] == "review_required":
        if (p is not None or value["classification"] is not None or value["attribution"] is not None
                or value["decision"]["tier"] != "review_required"):
            raise InputContractError("partial_definitive_decision_rejected")
    elif (type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1
          or value["classification"] not in {"phishing", "legitimate"} or value["attribution"] is None
          or value["decision"]["tier"] == "review_required"):
        raise InputContractError("decision_critical_component_missing")
    for indicator in value["behavioral_evidence"]:
        if (indicator["state"] not in {"supported", "absent", "unavailable", "not_evaluated"}
                or (indicator["state"] == "supported") != bool(indicator["evidence"])):
            raise InputContractError("unsupported_evidence_claim_rejected")
    return value
