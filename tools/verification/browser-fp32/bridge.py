"""Experimental Pyodide bridge for the existing Python rules, never production.

The collector discovers requests using valid neutral placeholders only. Those
temporary reports are discarded. All final reports use actual model scores.
"""
from copy import deepcopy
import json

from ml.datasets import DatasetRecord
from ml.preprocessing import TextEvidence
from ml.se_brl.detectors import DetectorContext, IdentityReference, AuthorityReview
from ml.se_brl.semantic_candidates import SemanticInferenceUnavailable, semantic_configuration
from ml.se_brl.semantic_review import review_record, validate_review, predictor_values, ReviewContractError


def reconstruct(case):
    data = dict(case["record"])
    data["fields_available"] = tuple(data["fields_available"])
    record = DatasetRecord(**data)
    ctx = case["context"]
    if ctx is None:
        return record, None
    identities = tuple(IdentityReference(**{**r, "claim": TextEvidence(**r["claim"]),
                        "authorized_domains": tuple(r["authorized_domains"])}) for r in ctx["identities"])
    reviews = tuple(AuthorityReview(**{**r, "role": TextEvidence(**r["role"]),
                     "directive": TextEvidence(**r["directive"])}) for r in ctx["authority_reviews"])
    return record, DetectorContext(identities, reviews)


def key(text, indicator):
    return json.dumps([text, indicator], ensure_ascii=False, separators=(",", ":"))


def normalize(report):
    data = deepcopy(report)
    for row in data["indicators"]:
        for candidate in row["semantic_candidates"]:
            candidate["scores"] = "compared_separately"
    return data


def discover(payload):
    requests = {}
    class Collector:
        def score(self, text, indicator):
            requests.setdefault(key(text, indicator), {"text": text, "indicator": indicator})
            return [{"entailment": 0.0, "neutral": 1.0, "contradiction": 0.0}] * 3
    for case in payload["cases"]:
        record, context = reconstruct(case)
        review_record(record, scorer=Collector(), detector_context=context)
    for text in (payload["boundary_text"], payload["boundary_text"] + "synthetic "):
        requests.setdefault(key(text, "urgency"), {"text": text, "indicator": "urgency"})
    return list(requests.values())


def run_suite(payload, scored):
    lookup = {key(r["text"], r["indicator"]): r for r in scored}
    class Scorer:
        def __init__(self):
            self.calls = 0
        def score(self, text, indicator):
            self.calls += 1
            result = lookup[key(text, indicator)]
            if result["oversized"]:
                raise SemanticInferenceUnavailable("Evidence exceeds token limit; abstain without truncation")
            return deepcopy(result["scores"])
    scorer = Scorer()
    cases = []
    for case in payload["cases"]:
        record, context = reconstruct(case)
        baseline = review_record(record, detector_context=context).to_dict()
        report = review_record(record, scorer=scorer, detector_context=context).to_dict()
        validate_review(report, record, detector_context=context)
        for old, row in zip(baseline["indicators"], report["indicators"], strict=True):
            assert old["deterministic_state"] == row["deterministic_state"]
            assert old["evidence"] == row["evidence"]
            assert row["candidate_state"] in {"abstained", "unavailable"}
            assert not row["failure_codes"]
        assert report["availability_mask"] == baseline["availability_mask"]
        assert report["learned_values"] == [None] * 4
        assert not any(report["research_release"].values()) and report["semantic_changes_labels"] is False
        cases.append({"name": case["name"], "outcome": normalize(report)})
    scores = scorer.score(payload["boundary_text"], "urgency")
    cases.append({"name": "exact_512_tokens", "outcome": {"scored": True,
        "maxima": [[k for k, v in r.items() if v == max(r.values())] for r in scores]}})
    try:
        scorer.score(payload["boundary_text"] + "synthetic ", "urgency")
    except SemanticInferenceUnavailable:
        cases.append({"name": "513_tokens_abstain", "outcome": {"abstained_without_truncation": True}})
    else:
        raise AssertionError("Oversized input executed")
    record, context = reconstruct(payload["budget_case"])
    replay = Scorer()
    budget_report = review_record(record, scorer=replay, detector_context=context).to_dict()
    assert replay.calls == 512
    assert any("semantic_budget_exhausted" in row["failure_codes"] for row in budget_report["indicators"])
    cases.append({"name": "64_unit_512_call_budget_replay", "outcome": normalize(budget_report)})
    record, context = reconstruct(payload["cases"][0])
    valid = review_record(record, scorer=scorer, detector_context=context).to_dict()
    rejected = 0
    for value in (True, -1):
        invalid = deepcopy(valid)
        invalid["indicators"][0]["semantic_candidates"][0]["evidence"]["start"] = value
        try:
            validate_review(invalid, record, detector_context=context)
        except ValueError:
            rejected += 1
    promoted = deepcopy(valid)
    promoted["indicators"][0]["candidate_state"] = "supported"
    try:
        validate_review(promoted, record, detector_context=context)
    except ValueError:
        rejected += 1
    assert rejected == 3
    class Bad:
        def score(self, *args):
            return [{"entailment": float("nan"), "neutral": 0, "contradiction": 0}] * 3
    bad = review_record(record, scorer=Bad(), detector_context=context).to_dict()
    assert all(not row["semantic_candidates"] for row in bad["indicators"])
    blocked = False
    try:
        predictor_values(valid)
    except ReviewContractError:
        blocked = True
    assert blocked
    cases.append({"name": "malformed_inputs_and_export_gate", "outcome": {
        "invalid_spans_and_promotion_rejected": rejected, "nan_scores_rejected": True, "predictor_export_blocked": True}})
    assert len(cases) == 24
    return {"cases": cases, "research_gates_closed": True, "deterministic_labels_and_evidence_unchanged": True}
