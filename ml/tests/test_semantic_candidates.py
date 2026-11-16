from dataclasses import replace

import pytest

from ml.datasets import DatasetRecord
from ml.preprocessing import TextEvidence
from ml.se_brl.detectors import DetectorContext, IdentityReference
from ml.se_brl.semantic_candidates import generate_candidates, SemanticInferenceUnavailable, validate_scores


class FakeScorer:
    def __init__(self):
        self.calls = []

    def score(self, text, indicator):
        self.calls.append((text, indicator))
        return [{"entailment": 0.9, "neutral": 0.05, "contradiction": 0.05}] * 3


def record(subject="Hello", **extra):
    fields = {"kind": "email", "subject": subject, "sender": "sender@example.test", **extra}
    return DatasetRecord("fixture:semantic", "synthetic-fixture", "content_bearing_email", fields,
                         tuple(key for key in fields if key not in {"kind", "body_collection_authorized", "study_purpose"}),
                         bool(subject), {"source": "synthetic-unit-test"})


@pytest.mark.parametrize("text", [
    "Submit the report before midnight.", "Never send your password.",
    'The lesson quotes "send your password".', "Send the report; your password remains private.",
    "A routine meeting occurs tomorrow.", "No payment is requested.",
    "Please transfer money.", "The article describes scarcity and reward.",
])
def test_all_twelve_remain_candidates_with_grounded_fields(text):
    scorer = FakeScorer()
    report = generate_candidates(record(text), scorer)
    assert report["indicator_count"] == 12
    assert report["approved_for_E2_E3"] is False
    assert report["learned_values"] == [None] * 4
    assert len(scorer.calls) == 10
    for item in report["indicators"].values():
        assert item["state"] in {"abstained", "unavailable"}
        for candidate in item["candidates"]:
            span = candidate["evidence"]
            assert span["field"] == "subject"
            assert text[span["start"]:span["end"]] == span["text"]
            assert not candidate["confidence_calibrated"]


def test_technical_and_url_sources_never_run_semantic_scorer():
    scorer = FakeScorer()
    for kind, modality, fields in [("url", "standalone_url", {"url": "https://example.test"}), ("technical", "engineered_technical_record", {})]:
        source = DatasetRecord("fixture:technical", "fixture", modality, {"kind": kind, **fields}, tuple(fields), False, {"source": "fixture"})
        report = generate_candidates(source, scorer)
        assert all(item["state"] == "unavailable" for item in report["indicators"].values())
    assert scorer.calls == []


def test_conditional_trust_modality_and_independent_identity_guards():
    source = record("We are Contoso")
    no_sender = replace(source, artifact_input={"kind": "email", "subject": "We are Contoso"}, fields_available=("subject",))
    report = generate_candidates(no_sender, FakeScorer())
    for indicator in ("authority", "impersonation", "brand_exploitation", "confidentiality_isolation"):
        assert report["indicators"][indicator]["state"] == "unavailable"
    reference = IdentityReference("impersonation", "Contoso", TextEvidence("subject", 0, 14, "We are Contoso", "subject"), ("official.example",), "fixture-audit", True)
    report = generate_candidates(source, FakeScorer(), DetectorContext((reference,), ()))
    assert report["indicators"]["impersonation"]["candidates"]
    assert report["indicators"]["impersonation"]["state"] == "abstained"
    assert report["indicators"]["brand_exploitation"]["state"] == "unavailable"


def test_bad_identity_field_offset_is_rejected():
    reference = IdentityReference("impersonation", "Contoso", TextEvidence("subject", 1, 15, "We are Contoso", "subject"), ("official.example",), "fixture-audit", True)
    with pytest.raises(ValueError, match="span"):
        generate_candidates(record("We are Contoso"), FakeScorer(), DetectorContext((reference,), ()))


def test_missing_model_or_oversized_evidence_abstains():
    class Unavailable:
        def score(self, text, indicator):
            raise SemanticInferenceUnavailable("fixture token limit")
    report = generate_candidates(record(), Unavailable())
    assert all(not item["semantic_inference_executed"] for item in report["indicators"].values())
    assert not report["behavioral_accuracy_validated"]


def test_semantic_changes_are_preserved_without_promoting_candidate_decisions():
    class Opposite:
        def score(self, text, indicator):
            return [{"entailment": 0.05, "neutral": 0.05, "contradiction": 0.9}] * 3
    first = generate_candidates(record("Submit the report."), FakeScorer())
    second = generate_candidates(record("Submit the report."), Opposite())
    left, right = first["indicators"]["urgency"], second["indicators"]["urgency"]
    assert left["candidates"][0]["scores"] != right["candidates"][0]["scores"]
    assert left["state"] == right["state"] == "abstained"
    assert not first["approved_for_E2_E3"] and not second["approved_for_E2_E3"]


def test_model_loading_contract_is_pinned_local_only_and_has_no_silent_truncation():
    import ast
    import json
    from pathlib import Path
    from ml.se_brl.semantic_candidates import LOCK, HYPOTHESES
    from ml.research_policy import fingerprint
    spec = json.loads(LOCK.read_text())
    assert len(spec["revision"]) == 40 and spec["hypotheses_sha256"] == fingerprint(HYPOTHESES)
    tree = ast.parse(Path(__file__).parents[1].joinpath("se_brl/semantic_candidates.py").read_text())
    loaders = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "from_pretrained"]
    assert len(loaders) == 2
    assert all(any(keyword.arg == "local_files_only" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True for keyword in call.keywords) for call in loaders)
    assert spec["oversized_evidence_policy"] == "abstain_without_truncation"


def test_oversized_pair_abstains_before_any_model_forward_call():
    from ml.se_brl.semantic_candidates import PinnedLocalNliScorer
    scorer = PinnedLocalNliScorer.__new__(PinnedLocalNliScorer)
    scorer.spec = {"max_tokens": 512}
    scorer.hypotheses = {"urgency": ["fixture"] * 3}
    class Tokens:
        shape = (3, 513)
    def tokenize(*args, **kwargs):
        assert kwargs["truncation"] is False
        return {"input_ids": Tokens()}
    scorer.tokenizer = tokenize
    with pytest.raises(SemanticInferenceUnavailable, match="token limit"):
        scorer.score("synthetic oversized fixture", "urgency")


@pytest.mark.parametrize("scores", [[], [{}] * 3, [{"entailment": float("nan"), "neutral": 0, "contradiction": 0}] * 3,
    [{"entailment": True, "neutral": 0, "contradiction": 0}] * 3,
    [{"entailment": 0.9, "neutral": 0.9, "contradiction": 0.9}] * 3])
def test_malformed_semantic_scores_fail_closed(scores):
    with pytest.raises(ValueError):
        validate_scores(scores)


# Synthetic transport/contract cases, not real-model semantic accuracy labels.
INDICATOR_EXAMPLES = {
    "urgency": ("Submit the report before midnight.", "No action or deadline is required."),
    "fear_threat": ("Unless you verify, your account will be suspended.", "The history lesson describes an old penalty."),
    "scarcity": ("Only two seats remain, so register now.", "Ordinary stock information is available."),
    "curiosity": ("Open this link to discover the hidden message.", "All meeting information is included here."),
    "reward_lure": ("Claim your prize by completing this form.", "The payroll statement records ordinary compensation."),
    "authority": ("As your manager, I require you to submit the report.", "The manager is mentioned in a history article."),
    "impersonation": ("This is an official notice from Contoso.", "The source is not independently confirmed."),
    "brand_exploitation": ("Use the Contoso portal to claim your benefit.", "A textbook mentions the brand Contoso."),
    "confidentiality_isolation": ("Keep this private and avoid consulting your bank.", "A routine privacy statement follows."),
    "call_to_action": ("Please open the portal.", "The portal was opened last year."),
    "credential_sensitive_data_request": ("Please provide your password.", "Never share your password."),
    "financial_action_request": ("Transfer the payment to this account.", "The statement records a completed payment."),
}


def grounded_source(text, modality="content_bearing_email", *, identity=True):
    from ml.preprocessing import preprocess
    full_text = "We are Contoso. " + text
    if modality == "content_bearing_email":
        fields = {"kind": "email", "subject": full_text, "sender": "sender@example.test"}
        evidence_field = "subject"
    else:
        fields = {"kind": "webpage", "html": "<p>" + full_text + "</p>", "page_url": "https://sender.example.test/"}
        evidence_field = "html"
    source = DatasetRecord("fixture:all-indicators", "synthetic-fixture", modality, fields,
                           tuple(key for key in fields if key != "kind"), True, {"source": "synthetic-only"})
    artifact = preprocess(fields)
    segment = next(span for span in artifact.segments if span.field == evidence_field)
    claim = TextEvidence(evidence_field, segment.start, segment.start + 14, "We are Contoso", segment.location)
    refs = tuple(IdentityReference(indicator, "Contoso", claim, ("official.example",), "synthetic-reference", True)
                 for indicator in ("impersonation", "brand_exploitation")) if identity else ()
    return source, DetectorContext(refs, ())


@pytest.mark.parametrize("indicator", INDICATOR_EXAMPLES)
@pytest.mark.parametrize("modality", ["content_bearing_email", "content_bearing_webpage"])
@pytest.mark.parametrize("case", ["positive", "negative", "negated", "counterfactual"])
def test_each_indicator_grounding_semantics_and_abstention(indicator, modality, case):
    from ml.se_brl.codebook import load_codebook
    positive, negative = INDICATOR_EXAMPLES[indicator]
    text = positive if case == "positive" else negative if case in {"negative", "counterfactual"} else "Do not act on this instruction: " + positive
    source, context = grounded_source(text, modality)
    class Scorer(FakeScorer):
        def score(self, evidence, target):
            self.calls.append((evidence, target))
            return [{"entailment": 0.9 if case == "positive" else 0.05,
                     "neutral": 0.05, "contradiction": 0.05 if case == "positive" else 0.9}] * 3
    scorer = Scorer()
    report = generate_candidates(source, scorer, context)
    parents = {item["id"]: dim["id"] for dim in load_codebook()["dimensions"] for item in dim["indicators"]}
    target = report["indicators"][indicator]
    assert list(report["indicators"]) == list(parents)
    assert target["dimension"] == parents[indicator]
    assert target["state"] == "abstained" and target["semantic_inference_executed"]
    assert report["dimension_availability"][parents[indicator]] == 1
    assert target["candidates"]
    for candidate in target["candidates"]:
        span = candidate["evidence"]
        assert source.artifact_input[span["field"]][span["start"]:span["end"]] == span["text"]
        assert len(candidate["scores"]) == 3
        assert candidate["scores"][0]["entailment"] == (0.9 if case == "positive" else 0.05)
        if case == "negated":
            assert candidate["requires_context_review"]
    assert report["learned_values"] == [None] * 4
    assert not report["approved_for_E2_E3"]


@pytest.mark.parametrize("indicator", INDICATOR_EXAMPLES)
@pytest.mark.parametrize("kind,modality,fields", [("url", "standalone_url", {"url": "https://example.test/"}),
    ("technical", "engineered_technical_record", {}), ("email", "content_bearing_email", {"subject": ""})])
def test_each_indicator_missing_or_unsupported_evidence_does_not_score(indicator, kind, modality, fields):
    source = DatasetRecord("fixture:missing", "fixture", modality, {"kind": kind, **fields}, tuple(fields), False, {"source": "fixture"})
    scorer = FakeScorer()
    item = generate_candidates(source, scorer)["indicators"][indicator]
    assert item["state"] == "unavailable" and not item["candidates"]
    assert not item["semantic_inference_executed"] and not scorer.calls


@pytest.mark.parametrize("indicator", INDICATOR_EXAMPLES)
@pytest.mark.parametrize("malformed", [None, [], [{"entailment": 1.0}] * 3,
    [{"entailment": False, "neutral": 1.0, "contradiction": 0.0}] * 3])
def test_each_indicator_rejects_malformed_scorer_records(indicator, malformed):
    source, context = grounded_source(INDICATOR_EXAMPLES[indicator][0])
    class BadScorer(FakeScorer):
        def score(self, text, target):
            return malformed if target == indicator else super().score(text, target)
    with pytest.raises(ValueError):
        generate_candidates(source, BadScorer(), context)


@pytest.mark.parametrize("indicator", ["impersonation", "brand_exploitation"])
def test_each_identity_indicator_requires_typed_references_and_origin_evidence(indicator):
    source, _ = grounded_source("Review this notice.", identity=False)
    assert generate_candidates(source, FakeScorer())["indicators"][indicator]["state"] == "unavailable"
    with pytest.raises(TypeError, match="typed"):
        generate_candidates(source, FakeScorer(), {"verified": True})
    source, context = grounded_source("Review this notice.", "content_bearing_webpage")
    no_url = replace(source, artifact_input={key: value for key, value in source.artifact_input.items() if key != "page_url"},
                     fields_available=("html",))
    assert generate_candidates(no_url, FakeScorer(), context)["indicators"][indicator]["state"] == "unavailable"


@pytest.mark.parametrize("change", [{"model": "other"}, {"tokenizer": "other"}, {"revision": "0" * 40},
    {"local_files_only": False}, {"max_tokens": True}, {"max_tokens": 513}, {"confidence_calibrated": True}])
def test_model_lock_tampering_fails_before_dependency_import(tmp_path, monkeypatch, change):
    import json
    import ml.se_brl.semantic_candidates as module
    spec = json.loads(module.LOCK.read_text())
    file = tmp_path / "lock.json"
    file.write_text(json.dumps({**spec, **change}))
    monkeypatch.setattr(module, "LOCK", file)
    with pytest.raises(SemanticInferenceUnavailable, match="configuration mismatch"):
        module.semantic_configuration()


@pytest.mark.parametrize("failure", [None, OSError("synthetic cache missing")])
def test_pinned_loader_contract_uses_fake_dependencies_only(monkeypatch, failure):
    import sys
    from types import SimpleNamespace
    import ml.se_brl.semantic_candidates as module
    calls = []
    class Model:
        config = SimpleNamespace(id2label={0: "entailment", 1: "neutral", 2: "contradiction"})
        def to(self, device):
            assert device == "cpu"
            return self
        def eval(self):
            return self
    def loader(name, **kwargs):
        calls.append((name, kwargs))
        assert kwargs == {"revision": module.MODEL_REVISION, "local_files_only": True}
        if failure:
            raise failure
        return Model()
    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=loader), AutoModelForSequenceClassification=SimpleNamespace(from_pretrained=loader)))
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace())
    if failure:
        with pytest.raises(SemanticInferenceUnavailable, match="local model"):
            module.PinnedLocalNliScorer()
    else:
        module.PinnedLocalNliScorer()
        assert len(calls) == 2 and all(name == module.MODEL_ID for name, _ in calls)


def test_missing_optional_dependencies_are_a_safe_unavailable_condition(monkeypatch):
    import sys
    from ml.se_brl.semantic_candidates import PinnedLocalNliScorer
    monkeypatch.setitem(sys.modules, "transformers", None)
    with pytest.raises(SemanticInferenceUnavailable, match="dependencies"):
        PinnedLocalNliScorer()


def test_candidate_order_and_outputs_are_deterministic_and_no_scorer_is_implicit():
    source, context = grounded_source("Please submit the report.")
    assert generate_candidates(source, FakeScorer(), context) == generate_candidates(source, FakeScorer(), context)
    with pytest.raises(TypeError, match="explicit scorer"):
        generate_candidates(source, None)
