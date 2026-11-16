"""Bounded semantic review of authoritative deterministic observations.

This is an offline engineering interface, not a validated decision policy. No
model is constructed implicitly. Neural scores can request review, never replace
rule labels, fill learned slots, authorize research, or authenticate identity.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re

from ml.annotation_validation import validate_span
from ml.datasets import DatasetRecord, prepare_record
from ml.metadata import fingerprint, freeze_json, json_value
from ml.preprocessing import TextEvidence
from ml.research_policy import reject_excluded
from .codebook import load_codebook
from .context import ContextIndex, NEGATION
from .detectors import DetectorContext
from .extraction import RuleEngine
from .semantic_candidates import LABELS, SemanticInferenceUnavailable, semantic_configuration, validate_scores


REVIEW_VERSION = "1.0.0"
POLICY_ID = "deterministic_labels_semantic_review_v1"
MAX_UNITS = 64
MAX_CALLS = 512
IDENTITY = frozenset({"impersonation", "brand_exploitation"})
META = re.compile(r"\b(?:hypothetical|suppose|imagine|educational|security lesson|for instance|as an example)\b", re.I)
UNITS = re.compile(r"[^.!?;\n]+[.!?;]?", re.UNICODE)
ROW_KEYS = {"indicator_id", "dimension_id", "deterministic_state", "evaluation_status", "evidence",
            "candidate_state", "semantic_status", "semantic_candidates", "failure_codes",
            "needs_review", "review_reasons", "constraints"}
TOP_KEYS = {"schema_version", "policy_id", "policy_version", "codebook_version", "artifact_id",
            "source_id", "modality", "artifact_sha256", "ruleset_version", "semantic_contract",
            "dimension_order", "availability_mask", "indicators", "semantic_changes_labels",
            "learned_values", "research_release", "provenance_metadata", "preprocessing_contract"}
FAILURES = {"semantic_unavailable", "semantic_failed", "semantic_budget_exhausted"}
REASONS = {"deterministic_not_evaluated", "context_requires_review", "hypothesis_disagreement",
           "semantic_rule_disagreement", "semantic_candidate_without_rule_support", "semantic_failure"}


class ReviewContractError(ValueError):
    """Stable error with no artifact text, credentials, or provider diagnostics."""


@dataclass(frozen=True, slots=True)
class ReviewReport:
    document: Mapping

    def __post_init__(self):
        object.__setattr__(self, "document", freeze_json(self.document))

    def to_dict(self) -> dict:
        return json_value(self.document)


def _span(span: TextEvidence, record: DatasetRecord) -> dict:
    value = {"field": span.field, "start": span.start, "end": span.end,
             "text": span.text, "location": span.location}
    validate_span(value, record.artifact_input)
    if type(span.location) is not str or not span.location:
        raise ReviewContractError("invalid_evidence_location")
    return value


def _symbolic(record, context):
    if not isinstance(record, DatasetRecord) or not isinstance(context, DetectorContext):
        raise ReviewContractError("canonical_record_and_typed_context_required")
    reject_excluded((record.source_dataset, record.record_id, record.provenance, record.source_metadata))
    artifact = prepare_record(record).artifact
    result = RuleEngine().extract(artifact, context)
    evidence = {}
    for row in result.indicators:
        evidence[row.indicator_id] = [
            {"span": _span(hit.span, record), "supporting_spans": [_span(s, record) for s in hit.supporting_spans],
             "rule_id": hit.rule_id, "reference_id": hit.reference_id, "provenance": "rule-based"}
            for hit in row.evidence]
        if row.evidence_state == "supported" and not evidence[row.indicator_id]:
            raise ReviewContractError("unsupported_deterministic_assertion")
    return artifact, result, evidence


def _units(artifact):
    """Original-field units; no normalized-text offsets or silent source truncation."""
    for segment in artifact.segments:
        for match in UNITS.finditer(segment.text):
            text = match.group().strip()
            if not text:
                continue
            start = match.start() + len(match.group()) - len(match.group().lstrip())
            yield segment, start, start + len(text)


def _context_allowed(segment, start, end, indicator, guards):
    # The negative directive "do not consult your bank" is potentially isolating;
    # ordinary prohibitions are not positive evidence for other indicators.
    double_negation = indicator == "confidentiality_isolation" and len(NEGATION.findall(segment.text[start:end])) > 1
    return not (double_negation or META.search(segment.text) or "?" in segment.text or guards.suppressed(
        segment, start, end, allow_negative_instruction=indicator == "confidentiality_isolation"))


def _semantic_contract():
    spec, _ = semantic_configuration()
    return {**{k: spec[k] for k in ("model", "tokenizer", "revision", "hypotheses_sha256", "max_tokens",
                                    "oversized_evidence_policy", "confidence_calibrated")},
            "scorer_provenance": "explicit_injection_not_independently_authenticated"}


def _provenance(record, context):
    return {"source_provenance_sha256": fingerprint(record.provenance),
            "detector_reference_ids": sorted({r.reference_id for r in (*context.identities, *context.authority_reviews)}),
            "independent_identity_truth_authenticated": False, "source_custody_authenticated": False}


def preprocessing_contract():
    # Upstream implementations currently share a version string but differ in
    # malformed-HTML handling. Pin source too; normalize only checkout newlines.
    from ml import preprocessing
    payload = Path(preprocessing.__file__).read_text(encoding="utf-8").encode("utf-8")
    return {"version": preprocessing.PREPROCESSING_VERSION,
            "source_utf8_lf_sha256": hashlib.sha256(payload).hexdigest()}


def review_record(record: DatasetRecord, *, scorer=None, detector_context: DetectorContext | None = None) -> ReviewReport:
    """Preserve RuleEngine labels; optional NLI diagnostics remain abstained.

    Scorers are trusted, explicit dependencies. Arbitrary external callbacks are
    not sandboxed. Corpus admission and scientific release remain separately shut.
    """
    if scorer is not None and not callable(getattr(scorer, "score", None)):
        raise ReviewContractError("explicit_scorer_interface_required")
    context = detector_context if detector_context is not None else DetectorContext()
    artifact, base, evidence = _symbolic(record, context)
    cb = load_codebook()
    guards = ContextIndex(artifact)
    reports = {r.indicator_id: r for r in base.detector_reports}
    all_units = []
    overflow = False
    for unit in _units(artifact):
        if len(all_units) == MAX_UNITS:
            overflow = True
            break
        all_units.append(unit)
    available = dict(zip(cb["vector_ordering"]["dimension_order"], base.assessment.availability_mask, strict=True))
    calls = 0
    rows = []
    for original in base.indicators:
        indicator = original.indicator_id
        identity_ok = indicator not in IDENTITY or (
            reports[indicator].evaluated and any(r.indicator_id == indicator and r.delegation_audited for r in context.identities))
        eligible = bool(available[original.dimension_id]) and identity_ok
        reasons = set()
        failures = set()
        candidates = []
        eligible_units = [(s, start, end) for s, start, end in all_units
                          if _context_allowed(s, start, end, indicator, guards)]
        blocked = len(eligible_units) != len(all_units)
        if original.evaluation_status == "not_evaluated":
            reasons.add("deterministic_not_evaluated")
        if scorer is not None and eligible:
            if overflow:
                failures.add("semantic_budget_exhausted")
            for segment, start, end in eligible_units:
                span = _span(TextEvidence(segment.field, segment.start + start, segment.start + end,
                                          segment.text[start:end], segment.location), record)
                if calls >= MAX_CALLS:
                    failures.add("semantic_budget_exhausted")
                    break
                calls += 1
                try:
                    scores = validate_scores(scorer.score(span["text"], indicator))
                except SemanticInferenceUnavailable:
                    failures.add("semantic_unavailable")
                    continue
                except Exception:
                    # Failures never expose provider exceptions or invent negatives.
                    failures.add("semantic_failed")
                    continue
                tops = [max(LABELS, key=lambda label: score[label]) for score in scores]
                # Ties are uncertainty, not a hidden entailment threshold.
                tied = any(sum(value == max(score.values()) for value in score.values()) > 1 for score in scores)
                if tied or len(set(tops)) > 1:
                    reasons.add("hypothesis_disagreement")
                elif tops[0] == "entailment" and original.evidence_state != "supported":
                    reasons.add("semantic_candidate_without_rule_support")
                elif tops[0] != "entailment" and original.evidence_state == "supported":
                    reasons.add("semantic_rule_disagreement")
                candidates.append({"evidence": span, "scores": scores, "decision": "candidate_only",
                                   "confidence_calibrated": False})
        if blocked:
            reasons.add("context_requires_review")
        if failures:
            reasons.add("semantic_failure")
        status = ("unavailable" if not eligible else "not_requested" if scorer is None else
                  "partial" if candidates and failures else "scored" if candidates else
                  "failed" if failures else "context_blocked")
        rows.append({"indicator_id": indicator, "dimension_id": original.dimension_id,
                     "deterministic_state": original.evidence_state, "evaluation_status": original.evaluation_status,
                     "evidence": evidence[indicator], "candidate_state": "abstained" if eligible else "unavailable",
                     "semantic_status": status, "semantic_candidates": candidates, "failure_codes": sorted(failures),
                     "needs_review": bool(reasons), "review_reasons": sorted(reasons),
                     "constraints": {"modality_before": bool(available[original.dimension_id]),
                                     "identity_before": identity_ok, "context_before": not blocked,
                                     "spans_before_and_after": True, "scores_after": True,
                                     "label_preservation_after": True}})
    payload = {"schema_version": REVIEW_VERSION, "policy_id": POLICY_ID, "policy_version": REVIEW_VERSION,
               "codebook_version": cb["codebook_version"], "artifact_id": record.record_id, "source_id": record.source_dataset,
               "modality": record.modality, "artifact_sha256": fingerprint(record.artifact_input),
               "ruleset_version": base.ruleset_version, "semantic_contract": _semantic_contract(),
               "provenance_metadata": _provenance(record, context),
               "preprocessing_contract": preprocessing_contract(),
               "dimension_order": list(available), "availability_mask": list(available.values()), "indicators": rows,
               "semantic_changes_labels": False, "learned_values": [None] * 4,
               "research_release": {"approved_for_E2_E3": False, "approved_for_sealed_test": False,
                                    "publishable_as_validated_results": False}}
    validate_review(payload, record, detector_context=context)
    return ReviewReport(payload)


def validate_review(payload: Mapping, record: DatasetRecord, *, detector_context: DetectorContext | None = None) -> None:
    """Validate a proposed callback result without model inference or data access.

    Symbolic evidence is recomputed against the supplied original artifact.
    Unknown fields, numeric promotions, corrupted spans and policy overrides fail.
    """
    if not isinstance(payload, Mapping) or set(payload) != TOP_KEYS:
        raise ReviewContractError("review_schema_mismatch")
    context = detector_context if detector_context is not None else DetectorContext()
    artifact, base, evidence = _symbolic(record, context)
    cb = load_codebook()
    expected = {"schema_version": REVIEW_VERSION, "policy_id": POLICY_ID, "policy_version": REVIEW_VERSION,
                "codebook_version": cb["codebook_version"], "artifact_id": record.record_id, "source_id": record.source_dataset,
                "modality": record.modality, "artifact_sha256": fingerprint(record.artifact_input),
                "ruleset_version": base.ruleset_version, "semantic_contract": _semantic_contract(),
                "provenance_metadata": _provenance(record, context),
                "preprocessing_contract": preprocessing_contract(),
                "dimension_order": cb["vector_ordering"]["dimension_order"],
                "availability_mask": list(base.assessment.availability_mask), "semantic_changes_labels": False,
                "learned_values": [None] * 4,
                "research_release": {"approved_for_E2_E3": False, "approved_for_sealed_test": False,
                                     "publishable_as_validated_results": False}}
    from ml.metadata import canonical_json
    if any(canonical_json(payload[k]) != canonical_json(v) for k, v in expected.items()):
        raise ReviewContractError("review_identity_policy_or_version_mismatch")
    rows = payload["indicators"]
    if not isinstance(rows, (list, tuple)) or len(rows) != len(base.indicators):
        raise ReviewContractError("canonical_indicator_coverage_required")
    guards = ContextIndex(artifact)
    units = []
    for unit in _units(artifact):
        if len(units) == MAX_UNITS:
            break
        units.append(unit)
    units_by_key = {(s.field, s.location, s.start + start, s.start + end): (s, start, end)
                    for s, start, end in units}
    detectors = {r.indicator_id: r for r in base.detector_reports}
    availability = dict(zip(expected["dimension_order"], expected["availability_mask"], strict=True))
    total_candidates = 0
    for row, original in zip(rows, base.indicators, strict=True):
        if not isinstance(row, Mapping) or set(row) != ROW_KEYS:
            raise ReviewContractError("indicator_schema_mismatch")
        for key, value in {"indicator_id": original.indicator_id, "dimension_id": original.dimension_id,
                           "deterministic_state": original.evidence_state, "evaluation_status": original.evaluation_status,
                           "evidence": evidence[original.indicator_id]}.items():
            if canonical_json(row[key]) != canonical_json(value):
                raise ReviewContractError("deterministic_labels_or_evidence_changed")
        if type(row["candidate_state"]) is not str or row["candidate_state"] not in {"abstained", "unavailable"}:
            raise ReviewContractError("unapproved_candidate_promotion")
        identity_ok = original.indicator_id not in IDENTITY or (
            detectors[original.indicator_id].evaluated and any(
                r.indicator_id == original.indicator_id and r.delegation_audited for r in context.identities))
        eligible = bool(availability[original.dimension_id]) and identity_ok
        blocked = any(not _context_allowed(s, start, end, original.indicator_id, guards) for s, start, end in units)
        constraints = {"modality_before": bool(availability[original.dimension_id]), "identity_before": identity_ok,
                       "context_before": not blocked, "spans_before_and_after": True,
                       "scores_after": True, "label_preservation_after": True}
        if (row["candidate_state"] != ("abstained" if eligible else "unavailable")
                or canonical_json(row["constraints"]) != canonical_json(constraints)):
            raise ReviewContractError("constraint_or_availability_mismatch")
        if type(row["semantic_status"]) is not str or row["semantic_status"] not in {"scored", "partial", "failed", "unavailable", "not_requested", "context_blocked"}:
            raise ReviewContractError("unknown_semantic_status")
        if (type(row["needs_review"]) is not bool or not isinstance(row["review_reasons"], (list, tuple))
                or any(type(v) is not str or v not in REASONS for v in row["review_reasons"])
                or row["needs_review"] != bool(row["review_reasons"])
                or not isinstance(row["failure_codes"], (list, tuple))
                or any(type(v) is not str or v not in FAILURES for v in row["failure_codes"])):
            raise ReviewContractError("invalid_review_or_failure_state")
        if not isinstance(row["semantic_candidates"], (list, tuple)) or len(row["semantic_candidates"]) > MAX_UNITS:
            raise ReviewContractError("invalid_candidate_collection")
        if (len(set(row["review_reasons"])) != len(row["review_reasons"])
                or len(set(row["failure_codes"])) != len(row["failure_codes"])
                or bool(row["failure_codes"]) != ("semantic_failure" in row["review_reasons"])
                or (blocked and "context_requires_review" not in row["review_reasons"])
                or (original.evaluation_status == "not_evaluated" and "deterministic_not_evaluated" not in row["review_reasons"])):
            raise ReviewContractError("inconsistent_review_flags")
        n = len(row["semantic_candidates"])
        allowed_status = ({"unavailable"} if not eligible else {"partial"} if n and row["failure_codes"] else
                          {"scored"} if n else {"failed"} if row["failure_codes"] else {"not_requested", "context_blocked"})
        if row["semantic_status"] not in allowed_status:
            raise ReviewContractError("inconsistent_semantic_status")
        if row["semantic_status"] == "context_blocked" and not blocked:
            raise ReviewContractError("context_blocking_not_supported_by_evidence")
        if not eligible and row["failure_codes"]:
            raise ReviewContractError("unavailable_indicator_cannot_claim_inference_failure")
        required_reasons = set()
        if original.evaluation_status == "not_evaluated":
            required_reasons.add("deterministic_not_evaluated")
        if blocked:
            required_reasons.add("context_requires_review")
        if row["failure_codes"]:
            required_reasons.add("semantic_failure")
        total_candidates += n
        if total_candidates > MAX_CALLS:
            raise ReviewContractError("semantic_budget_exceeded")
        seen_spans = set()
        for candidate in row["semantic_candidates"]:
            if not isinstance(candidate, Mapping) or set(candidate) != {"evidence", "scores", "decision", "confidence_calibrated"}:
                raise ReviewContractError("candidate_schema_mismatch")
            span = candidate["evidence"]
            validate_span(span, record.artifact_input)
            if set(span) != {"field", "start", "end", "text", "location"} or type(span["location"]) is not str:
                raise ReviewContractError("invalid_candidate_locator")
            key = (span["field"], span["location"], span["start"], span["end"])
            unit = units_by_key.get(key)
            if key in seen_spans or unit is None or not _context_allowed(*unit, original.indicator_id, guards):
                raise ReviewContractError("candidate_context_ineligible")
            seen_spans.add(key)
            scores = validate_scores(json_value(candidate["scores"]))
            if any(set(item) != set(LABELS) for item in candidate["scores"]):
                raise ReviewContractError("evidence_only_semantic_scores_required")
            tops = [max(LABELS, key=lambda label: score[label]) for score in scores]
            tied = any(sum(v == max(score.values()) for v in score.values()) > 1 for score in scores)
            required_reason = ("hypothesis_disagreement" if tied or len(set(tops)) > 1 else
                               "semantic_candidate_without_rule_support" if tops[0] == "entailment" and original.evidence_state != "supported" else
                               "semantic_rule_disagreement" if tops[0] != "entailment" and original.evidence_state == "supported" else None)
            if required_reason and required_reason not in row["review_reasons"]:
                raise ReviewContractError("semantic_review_signal_removed")
            if required_reason:
                required_reasons.add(required_reason)
            if candidate["decision"] != "candidate_only" or candidate["confidence_calibrated"] is not False:
                raise ReviewContractError("unapproved_score_interpretation")
        if row["candidate_state"] == "unavailable" and row["semantic_candidates"]:
            raise ReviewContractError("unavailable_indicator_was_scored")
        if set(row["review_reasons"]) != required_reasons:
            raise ReviewContractError("review_signal_not_supported_by_evidence")


def predictor_values(*args, **kwargs):
    """Review documents are not a feature vector. Explicit research decision needed."""
    raise ReviewContractError("review_candidates_are_not_approved_predictors")
