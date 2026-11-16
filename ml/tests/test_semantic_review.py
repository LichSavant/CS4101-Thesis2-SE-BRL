"""Synthetic engineering cases, not human references or model accuracy."""

from copy import deepcopy
from dataclasses import replace

import pytest

from ml.datasets import DatasetRecord, prepare_record
from ml.preprocessing import TextEvidence
from ml.se_brl.context import ContextIndex
from ml.se_brl.detectors import AuthorityReview, ConservativeTrustDetector, DetectorContext, IdentityReference
from ml.se_brl.extraction import RuleEngine
from ml.se_brl.semantic_candidates import SemanticInferenceUnavailable
from ml.se_brl.semantic_review import ReviewContractError, predictor_values, review_record, validate_review


EXAMPLES = {
    "urgency": "Act now.", "fear_threat": "Your account will be suspended.",
    "scarcity": "Claim your reward before it expires.", "curiosity": "Click here to discover who sent this.",
    "reward_lure": "Claim your prize.", "authority": "As your manager, submit your report.",
    "impersonation": "Use our portal.", "brand_exploitation": "Use our portal.",
    "confidentiality_isolation": "Do not contact your bank.", "call_to_action": "Click here.",
    "credential_sensitive_data_request": "Submit your password.", "financial_action_request": "Transfer your money.",
}


class Scorer:
    def __init__(self, top="entailment"):
        self.top, self.calls = top, []

    def score(self, text, indicator):
        self.calls.append((text, indicator))
        return [{key: 0.9 if key == self.top else 0.05 for key in ("entailment", "neutral", "contradiction")}] * 3


def source(text="Hello.", modality="content_bearing_email", *, authorized=False):
    text = "We are Contoso. " + text
    if modality == "content_bearing_email":
        values = {"kind": "email", "subject": text, "sender": "sender@official.example" if authorized else "sender@other.example"}
        field = "subject"
    else:
        values = {"kind": "webpage", "html": "<p>" + text + "</p>",
                  "page_url": "https://official.example/" if authorized else "https://other.example/"}
        field = "html"
    record = DatasetRecord("synthetic:review", "synthetic-engineering", modality, values,
                           tuple(k for k in values if k != "kind"), True, {"reference": "synthetic-only"})
    artifact = prepare_record(record).artifact
    segment = next(s for s in artifact.segments if s.field == field)
    claim = TextEvidence(field, segment.start, segment.start + 14, "We are Contoso", segment.location)
    identities = tuple(IdentityReference(i, "Contoso", claim, ("official.example",), "synthetic-identity-audit", True)
                       for i in ("impersonation", "brand_exploitation"))
    observed = ConservativeTrustDetector().detect(artifact, DetectorContext(), ContextIndex(artifact))[0].observations
    reviews = tuple(AuthorityReview(o.spans[0], o.spans[1], "authorized" if authorized else "contradicted",
                                   "synthetic-authority-audit") for o in observed)
    return record, DetectorContext(identities, reviews)


@pytest.mark.parametrize("indicator", EXAMPLES)
@pytest.mark.parametrize("modality", ["content_bearing_email", "content_bearing_webpage"])
@pytest.mark.parametrize("top", ["entailment", "neutral", "contradiction"])
def test_each_indicator_executes_grounded_functionality_without_neural_override(indicator, modality, top):
    record, context = source(EXAMPLES[indicator], modality)
    scorer = Scorer(top)
    report = review_record(record, scorer=scorer, detector_context=context).to_dict()
    original = RuleEngine().extract(prepare_record(record).artifact, context)
    assert [r["deterministic_state"] for r in report["indicators"]] == [r.evidence_state for r in original.indicators]
    row = next(r for r in report["indicators"] if r["indicator_id"] == indicator)
    assert row["deterministic_state"] == "supported"
    assert row["semantic_candidates"] and row["candidate_state"] == "abstained"
    assert row["needs_review"] is (top != "entailment")
    assert all(not v for v in report["research_release"].values())
    assert report["learned_values"] == [None] * 4 and report["semantic_changes_labels"] is False
    validate_review(report, record, detector_context=context)


@pytest.mark.parametrize("indicator", EXAMPLES)
def test_each_indicator_has_an_assessable_negative_or_explicit_unavailable(indicator):
    text = EXAMPLES["authority"] if indicator == "authority" else "The meeting is at noon."
    record, context = source(text, authorized=True)
    report = review_record(record, scorer=Scorer(), detector_context=context).to_dict()
    row = next(r for r in report["indicators"] if r["indicator_id"] == indicator)
    assert row["deterministic_state"] == "absent"
    assert row["candidate_state"] == "abstained"
    assert "semantic_candidate_without_rule_support" in row["review_reasons"]


@pytest.mark.parametrize("text", ['The article quotes "Submit your password".',
    "Security training: Submit your password.", "Hypothetical: Submit your password.",
    "Imagine you are told to submit your password.", "A warning says submit your password.",
    "Could you submit your password?", "Never submit your password."])
def test_contexts_cannot_create_neural_support(text):
    record, context = source(text)
    scorer = Scorer()
    report = review_record(record, scorer=scorer, detector_context=context).to_dict()
    row = next(r for r in report["indicators"] if r["indicator_id"] == "credential_sensitive_data_request")
    assert not any(i == "credential_sensitive_data_request" and "submit your password" in unit.lower()
                   for unit, i in scorer.calls)
    assert all("submit your password" not in c["evidence"]["text"].lower() for c in row["semantic_candidates"])
    assert row["needs_review"]
    # Even previously over-broad deterministic matches are retained for review,
    # never reinterpreted as validated context-aware final decisions.
    baseline = RuleEngine().extract(prepare_record(record).artifact, context)
    assert row["deterministic_state"] == next(r.evidence_state for r in baseline.indicators if r.indicator_id == row["indicator_id"])


def test_implied_behavior_is_offered_without_a_lexical_rule_trigger():
    record, context = source("The window closes at midnight; your place will then be reassigned.")
    scorer = Scorer()
    row = next(r for r in review_record(record, scorer=scorer, detector_context=context).to_dict()["indicators"] if r["indicator_id"] == "urgency")
    assert row["deterministic_state"] == "absent" and row["semantic_candidates"]
    assert row["candidate_state"] == "abstained" and row["needs_review"]


@pytest.mark.parametrize("indicator", EXAMPLES)
@pytest.mark.parametrize("template", ['The poster says "{}"', "Security training: {}", "Hypothetical: {}", "It is not true: {}"])
def test_every_indicator_excludes_contextual_counterexamples_before_semantic_scoring(indicator, template):
    text = template.format(EXAMPLES[indicator])
    record, context = source(text)
    report = review_record(record, scorer=Scorer(), detector_context=context).to_dict()
    row = next(r for r in report["indicators"] if r["indicator_id"] == indicator)
    assert all(EXAMPLES[indicator].rstrip(".") not in c["evidence"]["text"] for c in row["semantic_candidates"])
    assert row["needs_review"] and row["candidate_state"] in {"abstained", "unavailable"}


def test_unicode_offsets_and_malformed_nested_output_are_rejected():
    record, context = source("🧪 Submit your password.")
    report = review_record(record, scorer=Scorer(), detector_context=context).to_dict()
    row = next(r for r in report["indicators"] if r["indicator_id"] == "credential_sensitive_data_request")
    for candidate in row["semantic_candidates"]:
        span=candidate["evidence"]
        assert record.artifact_input[span["field"]][span["start"]:span["end"]] == span["text"]
    for key,value in [("candidate_state",[]),("semantic_status",{}),("review_reasons",[{}]),("failure_codes",[False])]:
        changed=deepcopy(report);changed["indicators"][0][key]=value
        with pytest.raises(ValueError):validate_review(changed,record,detector_context=context)


@pytest.mark.parametrize("kind,modality,fields", [("url", "standalone_url", {"url": "https://example.test/"}),
    ("technical", "engineered_technical_record", {})])
def test_noncontent_modalities_do_not_call_the_scorer(kind, modality, fields):
    record = DatasetRecord("synthetic:technical", "synthetic", modality, {"kind": kind, **fields}, tuple(fields), False, {"reference": "synthetic"})
    scorer = Scorer()
    report = review_record(record, scorer=scorer).to_dict()
    assert not scorer.calls
    assert all(r["candidate_state"] == r["deterministic_state"] == "unavailable" for r in report["indicators"])


def test_identity_needs_typed_audited_artifact_linked_references():
    record, context = source("Click here.")
    for supplied in (DetectorContext(), DetectorContext(tuple(replace(r, delegation_audited=False) for r in context.identities))):
        report = review_record(record, scorer=Scorer(), detector_context=supplied).to_dict()
        assert all(r["candidate_state"] == "unavailable" and not r["semantic_candidates"] for r in report["indicators"] if r["indicator_id"] in {"impersonation", "brand_exploitation"})
    with pytest.raises(ReviewContractError):
        review_record(record, scorer=Scorer(), detector_context={"verified": True})
    broken = replace(context.identities[0], claim=replace(context.identities[0].claim, start=1))
    with pytest.raises(ValueError, match="span"):
        review_record(record, scorer=Scorer(), detector_context=DetectorContext((broken,)))


@pytest.mark.parametrize("failure", [RuntimeError("private-provider-detail"), SemanticInferenceUnavailable("private-model-path"),
                                      ValueError("private-input-detail")])
def test_provider_failure_is_sanitized_and_never_becomes_absence(failure):
    class Broken:
        def score(self, *args):
            raise failure
    record, context = source("Act now.")
    report = review_record(record, scorer=Broken(), detector_context=context).to_dict()
    row = report["indicators"][0]
    assert row["deterministic_state"] == "supported" and row["candidate_state"] == "abstained"
    assert row["failure_codes"] and row["needs_review"]
    assert "private-" not in str(report)


@pytest.mark.parametrize("scores", [[], [{}] * 3, [{"entailment": True, "neutral": 0, "contradiction": 0}] * 3,
    [{"entailment": float("nan"), "neutral": 0, "contradiction": 0}] * 3])
def test_malformed_scores_fail_closed(scores):
    class Bad:
        def score(self, *args):return scores
    record, context = source()
    report = review_record(record, scorer=Bad(), detector_context=context).to_dict()
    assert all(not r["semantic_candidates"] for r in report["indicators"])
    assert "semantic_failed" in report["indicators"][0]["failure_codes"]


@pytest.mark.parametrize("field,value", [("deterministic_state", "absent"), ("candidate_state", "supported"),
    ("needs_review", 1), ("semantic_status", "validated")])
def test_output_schema_rejects_policy_and_type_changes(field, value):
    record, context = source("Act now.")
    report = review_record(record, scorer=Scorer(), detector_context=context).to_dict()
    report["indicators"][0][field] = value
    with pytest.raises((ValueError, ReviewContractError)):
        validate_review(report, record, detector_context=context)


def test_offsets_context_and_availability_cannot_be_forged():
    record, context = source("Act now.")
    report = review_record(record, scorer=Scorer(), detector_context=context).to_dict()
    for mutation in (lambda r: r["indicators"][0]["semantic_candidates"][0]["evidence"].update(start=True),
                     lambda r: r["indicators"][0]["semantic_candidates"][0]["evidence"].update(location="other"),
                     lambda r: r["indicators"][0]["constraints"].update(identity_before=False),
                     lambda r: r["preprocessing_contract"].update(source_utf8_lf_sha256="0"*64),
                     lambda r: r.update(availability_mask=[True] * 4),
                     lambda r: r.update(target=1)):
        changed = deepcopy(report);mutation(changed)
        with pytest.raises(ValueError):validate_review(changed, record, detector_context=context)


def test_ties_partial_failure_and_budget_are_explicit(monkeypatch):
    from ml.se_brl import semantic_review as module
    record, context = source("Act now. Submit your password. Click here.")
    monkeypatch.setattr(module, "MAX_UNITS", 2);monkeypatch.setattr(module, "MAX_CALLS", 3)
    scorer = Scorer()
    report = review_record(record, scorer=scorer, detector_context=context).to_dict()
    assert len(scorer.calls) == 3
    assert all("semantic_budget_exhausted" in r["failure_codes"] for r in report["indicators"])
    class Tied:
        def score(self, *args):return [{"entailment": 0.5, "neutral": 0.5, "contradiction": 0.0}] * 3
    report = review_record(record, scorer=Tied(), detector_context=context).to_dict()
    assert "hypothesis_disagreement" in report["indicators"][0]["review_reasons"]


def test_report_is_immutable_and_cannot_export_predictors():
    record, context = source()
    report = review_record(record, detector_context=context)
    with pytest.raises(TypeError):report.document["policy_id"] = "override"
    copied = report.to_dict();copied["research_release"]["approved_for_E2_E3"] = True
    assert not report.to_dict()["research_release"]["approved_for_E2_E3"]
    with pytest.raises(ReviewContractError):predictor_values(report)
