"""Legacy resource/identity guards; only synthetic injected scorers are used."""
import importlib
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

HERE = Path(__file__).resolve().parents[2] / "experiments/vera_validation"


@pytest.fixture
def legacy(monkeypatch):
    monkeypatch.syspath_prepend(str(HERE))
    return lambda name: importlib.import_module(name)


@pytest.mark.parametrize("name,function", [
    ("V15_autonomous_inference","infer"),("V16_constraint_governed_controller","infer"),
    ("V17_semantic_controller","infer"),("V21_semantic_candidates","generate_candidates")])
def test_missing_scorer_abstains_without_initializing_any_model(legacy,monkeypatch,name,function):
    module=legacy(name)
    def trap(*args,**kwargs):raise AssertionError("Implicit model initialization is prohibited")
    monkeypatch.setattr(module,"SemanticNLI",trap)
    result=getattr(module,function)("Submit your password before midnight.")
    assert all(row["state"] in {"abstained","unavailable"} for row in result["indicators"].values())
    assert all(not row.get("semantic_inference_executed",False) for row in result["indicators"].values())


@pytest.mark.parametrize("name,function", [("V15_autonomous_inference","infer"),("V21_semantic_candidates","generate_candidates")])
def test_bare_verified_flags_cannot_authorize_legacy_identity_inference(legacy,name,function):
    class Fake:
        def score(self,text,indicator):
            assert indicator not in {"impersonation","brand_exploitation"}
            return [{"entailment":.9,"neutral":.05,"contradiction":.05}]*3
    result=getattr(legacy(name),function)("We are Contoso.",semantic=Fake(),identity_evidence={"verified":True})
    assert all(result["indicators"][i]["state"]=="unavailable" for i in ("impersonation","brand_exploitation"))


def test_legacy_explicit_loader_delegates_to_pinned_local_only_wrapper(legacy,monkeypatch):
    import ml.se_brl.semantic_candidates as canonical
    module=legacy("V13D_hybrid_extractor")
    calls=[]
    class Fake:
        torch=model=tokenizer=indices=None
        def __init__(self):calls.append("explicit-construction")
        def score(self,text,indicator):return [{"entailment":.9,"neutral":.05,"contradiction":.05}]*3
    monkeypatch.setattr(canonical,"PinnedLocalNliScorer",Fake)
    model=module.SemanticNLI()
    assert calls==["explicit-construction"] and len(model.score("synthetic","urgency"))==3


def test_v14_review_only_invariants_with_fake_scores_not_a_real_model_run(legacy):
    deterministic=legacy("V13D_hybrid_extractor").rules_only
    reviewed=legacy("V13E_review_policy").assess
    class Fake:
        def score(self,text,indicator):return [{"entailment":.9,"neutral":.05,"contradiction":.05}]*3
    for text,modality in [("Your account will be suspended unless you verify it before midnight.","content_bearing_email"),
                          ("This security lesson says never send your password to anyone.","content_bearing_email"),
                          ("https://example.invalid/", "standalone_url")]:
        baseline=deterministic(text,modality=modality)
        result=reviewed(text,modality=modality,semantic=Fake())
        assert not result["semantic_changes_final_labels"]
        assert {i:r["state"] for i,r in result["indicators"].items()}=={i:r["state"] for i,r in baseline.items()}


@pytest.mark.parametrize("exists",[False,True])
def test_legacy_configuration_failure_is_sanitized_before_model_initialization(legacy,monkeypatch,tmp_path,exists):
    import ml.se_brl.semantic_candidates as canonical
    from ml.se_brl.semantic_candidates import SemanticInferenceUnavailable
    module=legacy("V13D_hybrid_extractor")
    path=tmp_path/"private-source-configuration.json"
    if exists:path.write_text('{}')
    def trap():raise AssertionError("No model initialization permitted")
    monkeypatch.setattr(canonical,"PinnedLocalNliScorer",trap)
    with pytest.raises(SemanticInferenceUnavailable) as error:module.SemanticNLI(config=path)
    assert "private-source" not in str(error.value)
