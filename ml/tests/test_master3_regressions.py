"""Software contract fixtures only; no study annotation or research execution."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json

import pytest

from ml.behavioral_validation import EvaluationManifest, import_adjudications, import_human_responses, plan_validation
from ml.metadata import canonical_json
from ml.se_brl.semantic_review import review_record, validate_review
from ml.tests.test_behavioral_validation import packet, response
from ml.tests.test_semantic_review import Scorer, source


def declared_fixture():
    p=packet();a=response(p);b=response(p,"synthetic-human-b")
    batch=import_human_responses([p],json.dumps([a,b]))
    decision={"record_id":p["record_id"],"indicator_id":"urgency","text_hash":p["text_hash"],
              "adjudicator_id":"synthetic-human-c","review_date":"2026-11-15","reason":"software fixture, no actual judgment",
              "reference_annotator_ids":[a["annotator_id"],b["annotator_id"]],"value":"supported",
              "role":"independent_human","adjudicator_qualifications":"software fixture only",
              "protocol_version":"synthetic-v1","independent":True,"model_output_visible":False,
              "evidence":a["evidence"]["urgency"]}
    return p,batch,decision


@pytest.mark.parametrize("key,value",[("AI_generated",True),("codebook_version","999"),("modality","standalone_url")])
def test_adjudication_cannot_smuggle_ignored_authority_or_version_claims(key,value):
    _,batch,row=declared_fixture();row[key]=value
    with pytest.raises(ValueError):import_adjudications(batch,json.dumps([row]))


@pytest.mark.parametrize("hint",["target","AI_rationale","model_scores"])
def test_blinded_packet_cannot_carry_hidden_predictor_or_label_hints(hint):
    p=packet();row=response(p);p[hint]="not permitted"
    with pytest.raises(ValueError):import_human_responses([p],json.dumps([row]))


@pytest.mark.parametrize("field",["abstention_policy","interval_policy"])
def test_evaluation_manifest_rejects_unapproved_policy_text_even_with_matching_hash(field):
    p,batch,_=declared_fixture()
    manifest=plan_validation(batch,{p["record_id"]:"development"},protocol_version="synthetic-v1")
    document=manifest.to_dict();document[field]="unapproved alternative"
    payload=canonical_json(document)
    with pytest.raises(ValueError):EvaluationManifest(payload,hashlib.sha256(payload.encode()).hexdigest())


def test_review_cannot_claim_context_blocking_when_context_is_eligible():
    record,context=source("Act now.")
    report=review_record(record,detector_context=context).to_dict()
    report["indicators"][0]["semantic_status"]="context_blocked"
    with pytest.raises(ValueError):validate_review(report,record,detector_context=context)


def test_review_cannot_invent_semantic_disagreement_without_scores():
    record,context=source("Act now.")
    report=review_record(record,detector_context=context).to_dict()
    report["indicators"][0].update(needs_review=True,review_reasons=["semantic_rule_disagreement"])
    with pytest.raises(ValueError):validate_review(report,record,detector_context=context)


def test_double_negated_isolation_is_reviewed_without_scoring_the_reversed_directive():
    record,context=source("Do not avoid contacting your bank.")
    scorer=Scorer();report=review_record(record,scorer=scorer,detector_context=context).to_dict()
    row=next(r for r in report["indicators"] if r["indicator_id"]=="confidentiality_isolation")
    assert all("avoid contacting" not in c["evidence"]["text"] for c in row["semantic_candidates"])
    assert row["needs_review"]


@pytest.mark.parametrize("field,value",[("indicators",{"urgency":"supported"}),("evidence",{"urgency":[]}),
    ("uncertainty",{"urgency":"prior"}),("annotation_notes","previous model conclusion"),
    ("modality",[]),("text_hash","0"*64)])
def test_blank_instrument_and_artifact_binding_are_checked_for_every_packet(field,value):
    p=packet();row=response(p);p[field]=value
    with pytest.raises(ValueError):import_human_responses([p],json.dumps([row]))


@pytest.mark.parametrize("error",[ImportError("private path"),OSError("private library path"),RuntimeError("private native library detail")])
def test_optional_dependency_import_failures_are_sanitized(monkeypatch,error):
    import builtins
    from ml.se_brl.semantic_candidates import PinnedLocalNliScorer,SemanticInferenceUnavailable
    original=builtins.__import__
    def importing(name,*args,**kwargs):
        if name=="transformers":raise error
        return original(name,*args,**kwargs)
    monkeypatch.setattr(builtins,"__import__",importing)
    with pytest.raises(SemanticInferenceUnavailable,match="dependencies") as caught:PinnedLocalNliScorer()
    assert "private" not in str(caught.value)


def test_excluded_path_is_rejected_before_resolving_or_reading_any_file(monkeypatch):
    from pathlib import Path
    from ml.research_policy import ResearchPolicyError,verify_artifact
    def trap(*args,**kwargs):raise AssertionError("Excluded metadata must fail before filesystem resolution")
    monkeypatch.setattr(Path,"resolve",trap)
    with pytest.raises(ResearchPolicyError):verify_artifact(Path('/synthetic/SpaFish/input.csv'),Path('/synthetic'))


@pytest.mark.parametrize("refs",[None,True,{},[False]])
def test_adjudication_reference_shape_failure_is_stable(refs):
    _,batch,row=declared_fixture();row["reference_annotator_ids"]=refs
    with pytest.raises(ValueError):import_adjudications(batch,json.dumps([row]))


def test_unavailable_modality_cannot_claim_a_model_failure():
    from ml.datasets import DatasetRecord
    record=DatasetRecord("synthetic:url","synthetic","standalone_url",{"kind":"url","url":"https://example.test/"},("url",),False,{"source":"synthetic"})
    report=review_record(record).to_dict();row=report["indicators"][0]
    row.update(failure_codes=["semantic_failed"],needs_review=True,review_reasons=["semantic_failure"])
    with pytest.raises(ValueError):validate_review(report,record)


@pytest.mark.parametrize("module,function,args",[
    ("V13D_run_regression","run",()),("V13F_ablation_audit","load_cases",(None,"v10")),
    ("V13F_ablation_audit","main",()),("V14_annotation_integrity","inspect",()),("V14_dataset_lineage","audit",())])
def test_legacy_corpus_entrypoints_stop_at_admission_before_reading_any_input(monkeypatch,tmp_path,module,function,args):
    import importlib
    from pathlib import Path
    from ml.research_policy import ResearchPolicyError
    monkeypatch.syspath_prepend(str(Path(__file__).parents[2]/"experiments/vera_validation"))
    loaded=importlib.import_module(module)
    if function=="main":
        import sys
        monkeypatch.setattr(sys,"argv",["guard","--dataset","v10","--output",str(tmp_path/"not-written.json")])
    with pytest.raises(ResearchPolicyError,match="blocked"):getattr(loaded,function)(*args)


@pytest.mark.parametrize("field,value",[("start",False),("quoted",0)])
def test_canonical_identity_evidence_rejects_boolean_offsets_and_nonboolean_quote_flags(field,value):
    from ml.se_brl.detectors import DetectorContext
    from ml.se_brl.semantic_candidates import generate_candidates
    record,context=source("Click here.")
    ref=context.identities[0]
    malformed=replace(ref,claim=replace(ref.claim,**{field:value}))
    with pytest.raises(ValueError,match="span"):
        generate_candidates(record,Scorer(),DetectorContext((malformed,)))


@pytest.mark.parametrize("module,function",[("V13D_hybrid_extractor","extract"),("V13E_review_policy","assess")])
def test_legacy_review_ties_require_review_without_changing_labels(monkeypatch,module,function):
    import importlib
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).parents[2]/"experiments/vera_validation"))
    loaded=importlib.import_module(module)
    class Tied:
        def score(self,*args):return [{"entailment":.5,"neutral":.5,"contradiction":0.0}]*3
    result=getattr(loaded,function)("Please submit before midnight.",semantic=Tied())
    row=result["indicators"]["urgency"]
    assert row["state"]=="supported" and row["needs_review"] is True


@pytest.mark.parametrize("module,function",[("V13D_hybrid_extractor","extract"),("V13E_review_policy","assess"),
    ("V15_autonomous_inference","decision_labels"),("V13F_ablation_audit","candidate_top_labels")])
def test_legacy_score_consumers_reject_booleans_instead_of_treating_them_as_certainty(monkeypatch,module,function):
    import importlib
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).parents[2]/"experiments/vera_validation"))
    loaded=importlib.import_module(module)
    scores=[{"entailment":True,"neutral":0,"contradiction":0}]*3
    class Invalid:
        def score(self,*args):return scores
    with pytest.raises(ValueError):
        if function in {"decision_labels","candidate_top_labels"}:getattr(loaded,function)(scores)
        else:getattr(loaded,function)("Please submit before midnight.",semantic=Invalid())


def test_experimental_autonomous_voting_cannot_turn_a_tie_into_support(monkeypatch):
    import importlib
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).parents[2]/"experiments/vera_validation"))
    decide=importlib.import_module("V15_autonomous_inference").decision_labels
    with pytest.raises(ValueError,match="tied"):
        decide([{"entailment":.5,"neutral":.5,"contradiction":0.0}]*3)


def test_evaluation_plan_detects_controller_source_drift_under_unchanged_versions(monkeypatch):
    from pathlib import Path
    from ml.behavioral_validation import verify_evaluation_manifest
    p,batch,_=declared_fixture();assignments={p["record_id"]:"development"}
    manifest=plan_validation(batch,assignments,protocol_version="synthetic-v1")
    target=Path(__file__).parents[1]/"se_brl/semantic_review.py"
    original=Path.read_text
    def changed_source(path,*args,**kwargs):
        value=original(path,*args,**kwargs)
        return value+'\n# simulated source drift without modifying any file\n' if path==target else value
    monkeypatch.setattr(Path,"read_text",changed_source)
    with pytest.raises(ValueError):verify_evaluation_manifest(manifest,batch,assignments,protocol_version="synthetic-v1")


def test_reference_packet_v1_stays_supported_but_unbound_old_plans_are_not_silently_upgraded():
    p=packet();p["schema_version"]="1.0.0";row=response(p)
    batch=import_human_responses([p],json.dumps([row]))
    plan=plan_validation(batch,{p["record_id"]:"development"},protocol_version="synthetic-v1")
    assert plan.to_dict()["schema_version"]=="1.1.0"
    old=plan.to_dict();old["schema_version"]="1.0.0";old.pop("review_runtime_sha256")
    serialized=canonical_json(old)
    with pytest.raises(ValueError):EvaluationManifest(serialized,hashlib.sha256(serialized.encode()).hexdigest())
