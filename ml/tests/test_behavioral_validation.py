"""All declared-human responses here are synthetic software fixtures."""

from dataclasses import FrozenInstanceError
import hashlib
import json

import pytest

from ml.behavioral_validation import (EvaluationManifest, evaluate_independent_references, import_adjudications,
    import_human_responses, plan_validation, reference_coverage, synthetic_pair_statistics, verify_evaluation_manifest, wilson_interval)
from ml.research_policy import ResearchPolicyError


def packet(key="synthetic:1", group="synthetic:group"):
    fields = {"subject": "Act now."}
    digest = hashlib.sha256(json.dumps(fields, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {"record_id": key, "group_id": group, "modality": "content_bearing_email", "fields": fields, "text_hash": digest}


def response(p, annotator="synthetic-human-a"):
    return {"record_id": p["record_id"], "text_hash": p["text_hash"], "annotator_id": annotator,
            "role": "independent_human", "qualifications": "synthetic fixture only, not a real person",
            "review_date": "2026-11-15", "protocol_version": "synthetic-v1", "codebook_version": "0.1.0",
            "modality": p["modality"], "independent": True, "model_output_visible": False,
            "indicators": {"urgency": "supported"},
            "evidence": {"urgency": [{"field": "subject", "start": 0, "end": 7, "text": "Act now"}]}}


def test_reference_import_is_bound_immutable_and_does_not_authenticate_humans():
    p = packet();row = response(p);batch = import_human_responses([p], json.dumps([row]))
    assert batch.human_independence_authenticated is False
    with pytest.raises(TypeError):batch.responses[0]["indicators"]["urgency"] = "absent"
    row["indicators"]["urgency"] = "absent"
    assert batch.responses[0]["indicators"]["urgency"] == "supported"
    assert "Act now" not in repr(batch)


@pytest.mark.parametrize("key,value", [("independent", False), ("model_output_visible", True),
    ("role", "AI_assisted"), ("text_hash", "0" * 64), ("codebook_version", "other"),
    ("record_id", "other"), ("indicators", {"urgency": 1})])
def test_invalid_reference_declarations_are_rejected(key, value):
    p=packet();row=response(p);row[key]=value
    with pytest.raises(ValueError):import_human_responses([p], json.dumps([row]))


def test_duplicate_json_duplicate_responses_and_orphan_spans_rejected():
    p=packet();row=response(p)
    with pytest.raises(ValueError, match="duplicate"):import_human_responses([p], '[{"record_id":"a","record_id":"b"}]')
    with pytest.raises(ValueError, match="duplicate"):import_human_responses([p], json.dumps([row,row]))
    row["evidence"]["urgency"][0]["start"]=True
    with pytest.raises(ValueError):import_human_responses([p],json.dumps([row]))


def test_unanswered_packets_and_missing_indicator_cells_are_counted_explicitly():
    p=packet();q=packet("synthetic:2", "synthetic:group2")
    batch=import_human_responses([p,q],json.dumps([response(p)]))
    result=reference_coverage(batch,expected_annotator_ids=("synthetic-human-a","synthetic-human-b"))
    assert result["expected_responses"]==4 and result["received_responses"]==1 and result["unanswered_responses"]==3
    assert result["indicators"]["urgency"]["supported"]==1 and result["indicators"]["urgency"]["missing"]==3
    assert result["indicators"]["scarcity"]["missing"]==4
    row=response(p);row["AI_generated"]=True
    with pytest.raises(ValueError,match="unknown_reference"):import_human_responses([p],json.dumps([row]))


def test_plan_binds_model_policy_references_and_supplied_groups():
    p=packet();batch=import_human_responses([p],json.dumps([response(p)]))
    manifest=plan_validation(batch,{p["record_id"]:"development"},protocol_version="synthetic-v1")
    d=manifest.to_dict()
    assert d["reference_set_sha256"]==batch.sha256 and d["policy_version"]=="1.0.0"
    assert len(d["semantic_model"]["revision"])==40
    assert not d["research_execution_authorized"] and not d["human_independence_authenticated"]
    verify_evaluation_manifest(manifest,batch,{p["record_id"]:"development"},protocol_version="synthetic-v1")
    with pytest.raises(ValueError,match="bind_current"):
        verify_evaluation_manifest(manifest,batch,{p["record_id"]:"calibration"},protocol_version="synthetic-v1")
    with pytest.raises(FrozenInstanceError):manifest.sha256="other"
    with pytest.raises(ValueError):EvaluationManifest(manifest.canonical_document,"0"*64)
    with pytest.raises(ValueError):plan_validation(batch,{p["record_id"]:"test"},protocol_version="synthetic-v1")
    with pytest.raises(ValueError):plan_validation(batch,{p["record_id"]:"development"},protocol_version="other")
    q=packet("synthetic:2");batch=import_human_responses([p,q],json.dumps([response(p),response(q)]))
    with pytest.raises(ValueError,match="group_crosses"):
        plan_validation(batch,{p["record_id"]:"development",q["record_id"]:"calibration"},protocol_version="synthetic-v1")


def test_adjudication_is_separate_bound_and_cannot_replace_responses():
    p=packet();a=response(p);b=response(p,"synthetic-human-b");b.update(indicators={"urgency":"absent"},evidence={})
    batch=import_human_responses([p],json.dumps([a,b]));original=batch.sha256
    row={"record_id":p["record_id"],"indicator_id":"urgency","text_hash":p["text_hash"],
         "adjudicator_id":"synthetic-human-c","review_date":"2026-11-15","reason":"synthetic fixture only",
         "reference_annotator_ids":[a["annotator_id"],b["annotator_id"]],"value":"supported",
         "role":"independent_human","adjudicator_qualifications":"synthetic fixture only",
         "protocol_version":"synthetic-v1","independent":True,"model_output_visible":False,
         "evidence":a["evidence"]["urgency"]}
    result=import_adjudications(batch,json.dumps([row]));assert result[0]["value"]=="supported"
    planned=plan_validation(batch,{p["record_id"]:"development"},protocol_version="synthetic-v1",adjudications=result)
    assert len(planned.to_dict()["adjudication_hashes"])==1
    assert batch.sha256==original and batch.responses[1]["indicators"]["urgency"]=="absent"
    row["text_hash"]="0"*64
    with pytest.raises(ValueError,match="binding"):import_adjudications(batch,json.dumps([row]))


def test_synthetic_metrics_keep_abstention_unavailable_and_missing_separate():
    pairs=[({"urgency":r},{"urgency":p}) for r,p in [
        ("supported","supported"),("absent","supported"),("supported","absent"),("absent","absent"),
        ("supported","abstained"),("supported","unavailable"),("supported",None),("unavailable","supported"),(None,"supported")]]
    result=synthetic_pair_statistics(pairs);r=result["indicators"]["urgency"]
    assert [r[k] for k in ("tp","fp","fn","tn")]==[1,1,1,1]
    assert r["eligible_references"]==7 and r["decided"]==4 and r["coverage"]==4/7
    assert r["precision"]==r["recall_among_decided"]==r["f1_among_decided"]==0.5
    assert [r[k] for k in ("prediction_abstained","prediction_unavailable","prediction_missing","reference_unavailable","reference_missing")]==[1]*5
    assert result["verification_kind"]=="synthetic_arithmetic_only" and not result["independent_validation"]
    assert r["f1_interval"] is None
    assert synthetic_pair_statistics([])["indicators"]["urgency"]["precision"] is None


@pytest.mark.parametrize("successes,trials", [(True,1),(1,True),(-1,2),(3,2),(0,-1)])
def test_invalid_interval_counts_fail(successes,trials):
    with pytest.raises(ValueError):wilson_interval(successes,trials)


def test_wilson_extremes_and_closed_real_research_entrypoint():
    assert wilson_interval(0,0) is None
    low,high=wilson_interval(5,10)
    assert low==pytest.approx(0.236593,abs=1e-6) and high==pytest.approx(0.763407,abs=1e-6)
    assert wilson_interval(0,10)[1]>0 and wilson_interval(10,10)[0]<1
    class Trap:
        def __iter__(self):raise AssertionError("No data should be read")
    with pytest.raises(ResearchPolicyError,match="blocked"):evaluate_independent_references(Trap())
