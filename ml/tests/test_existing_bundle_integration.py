"""Opt-in NO-FIT integration using existing independently pinned synthetic state.

Set SEBRL_READBACK_ROOT and SEBRL_READBACK_RECEIPT_SHA256 explicitly. No fallback
to training fixtures or searching other directories exists. All estimator and
calibrator fitting methods are forbidden for this entire module.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.app.artifact_service import ArtifactAnalysisService, ArtifactBodyLimit, artifact_router
from ml.artifact_analysis import ArtifactAnalyzer, load_bundle
from ml.classifier_adapters import FoldClassifier
from ml.experiment_engine import FittedSigmoid
from ml.experiment_inputs import InputContractError
from ml.inference_benchmark import benchmark_synthetic_inference
from ml.synthetic_system import fixture_artifact


@pytest.fixture(scope="module", autouse=True)
def no_fit():
    if not os.environ.get("SEBRL_READBACK_ROOT") or not os.environ.get("SEBRL_READBACK_RECEIPT_SHA256"):
        pytest.skip("explicit existing synthetic readback bundle and digest required; no training fallback")
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import LinearSVC
    from sklearn.ensemble import RandomForestClassifier
    from xgboost import XGBClassifier
    patch=pytest.MonkeyPatch()
    def forbidden(*args,**kwargs):
        raise AssertionError("Fitting is forbidden during existing-state verification")
    for cls in (FoldClassifier,LogisticRegression,LinearSVC,RandomForestClassifier,XGBClassifier):
        patch.setattr(cls,"fit",forbidden)
    patch.setattr(FittedSigmoid,"fit",classmethod(forbidden))
    yield
    patch.undo()


@pytest.fixture(scope="module")
def existing(no_fit):
    root=Path(os.environ["SEBRL_READBACK_ROOT"])
    raw=(root/"fixture_receipt.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest()==os.environ["SEBRL_READBACK_RECEIPT_SHA256"]
    receipt=json.loads(raw)
    assert receipt["category"]=="SYNTHETIC RESULT" and receipt["new_model_fits"]==receipt["new_calibrator_fits"]==0
    bundles={dataset:load_bundle(root/dataset.lower(),expected_manifest_sha256=e["manifest_sha256"],max_bytes=20000000)
             for dataset,e in receipt["bundles"].items()}
    return root,receipt,bundles


def settings(root, receipt):
    result=SimpleNamespace(artifact_bundle_max_bytes=20000000,artifact_timeout_seconds=10.,
        artifact_metadata_retention_enabled=False,database_url="sqlite:///:memory:")
    for dataset,stem in (("Email","email"),("Web","web"),("UCI","uci"),("PhiUSIIL","phiusiil")):
        setattr(result,"artifact_"+stem+"_bundle",str(root/dataset.lower()))
        setattr(result,"artifact_"+stem+"_bundle_sha256",receipt["bundles"][dataset]["manifest_sha256"])
    return result


def api(service,limit=1000000):
    app=FastAPI();app.include_router(artifact_router(service));app.add_middleware(ArtifactBodyLimit,max_bytes=limit)
    return TestClient(app)


def submission(raw,**changes):
    return dict(dict(schema_version="artifact-decision-1.0",artifact=raw,language="en",submission_authorized=True,retain_metadata=False),**changes)


@pytest.mark.parametrize("dataset",("Email","Web","UCI","PhiUSIIL"))
def test_existing_state_full_API_and_separate_evidence_attribution(existing,dataset):
    root,receipt,_=existing
    service=ArtifactAnalysisService(settings(root,receipt))
    response=api(service).post("/api/v1/artifact-analysis",json=submission(fixture_artifact(dataset,900,1)))
    assert response.status_code==200,response.text
    result=response.json()
    assert result["status"]=="complete" and result["research_validated"] is False
    assert result["result_category"]=="synthetic_model_generated"
    assert result["attribution"]["channel"]=="model_attribution_not_artifact_evidence"
    assert len(result["behavioral_evidence"])==12 and service._memory is None
    if dataset in {"UCI","PhiUSIIL"}:
        assert all(i["state"]=="unavailable" for i in result["behavioral_evidence"])
        assert result["decision"]["severity"]==0


def test_UCI_loads_only_its_own_bundle(existing,monkeypatch):
    import backend.app.artifact_service as module
    root,receipt,_=existing
    config=settings(root,receipt)
    config.artifact_email_bundle=config.artifact_web_bundle=config.artifact_phiusiil_bundle="MUST_NOT_OPEN"
    calls=[]
    original=module.load_bundle
    def guarded(path,**kwargs):
        assert Path(path)==root/"uci"
        calls.append(path);return original(path,**kwargs)
    monkeypatch.setattr(module,"load_bundle",guarded)
    response=api(ArtifactAnalysisService(config)).post("/api/v1/artifact-analysis",json=submission(fixture_artifact("UCI",1,0),language="unknown"))
    assert response.status_code==200 and response.json()["status"]=="complete" and len(calls)==1


def test_failure_consent_limits_logs_and_no_stale_prediction(existing,caplog):
    root,receipt,_=existing
    service=ArtifactAnalysisService(settings(root,receipt));client=api(service)
    good=submission(fixture_artifact("Email",1,1))
    assert client.post("/api/v1/artifact-analysis",json=good).json()["status"]=="complete"
    unknown=client.post("/api/v1/artifact-analysis",json=submission({"kind":"email","subject":"PRIVATE_SENTINEL"},language="unknown")).json()
    assert unknown["status"]=="review_required"
    assert unknown["classification"] is unknown["calibrated_probability"] is unknown["attribution"] is None
    assert "PRIVATE_SENTINEL" not in json.dumps(unknown) and "PRIVATE_SENTINEL" not in caplog.text
    assert client.post("/api/v1/artifact-analysis",json=dict(good,submission_authorized=False)).status_code==403
    invalid=client.post("/api/v1/artifact-analysis",content=b'PRIVATE_SENTINEL',headers={"content-type":"application/json"})
    assert invalid.status_code==422 and "PRIVATE_SENTINEL" not in invalid.text
    assert set(invalid.json()["detail"])=={"code","stage","state","limitation","next_step"}
    assert client.post("/api/v1/artifact-analysis",content="{}",headers={"content-type":"text/plain"}).status_code==415
    assert api(service,limit=100).post("/api/v1/artifact-analysis",json=good).status_code==413


def test_existing_pipeline_model_only_timing_without_any_fitting(existing):
    _,_,bundles=existing
    classifier=bundles["UCI"].classifier
    rows=((-1,1),)
    ready=classifier.pipeline.named_steps["preprocess"].transform(classifier._matrix(rows))
    estimator=classifier.pipeline.named_steps["classifier"]
    def predict(_):return tuple(float(v) for v in estimator.predict_proba(ready)[:,1])
    result=benchmark_synthetic_inference(predict,((0.,),),warmup=1,repetitions=3,batch_size=1,thread_reference="synthetic existing-state verification only")
    assert result["result_category"]=="SYNTHETIC RESULT" and result["p95_batch_ms"]>0
    assert result["measured_memory_bytes_max"] is None


def test_tampered_component_rejected_even_with_new_manifest_digest(existing,tmp_path):
    root,receipt,_=existing
    destination=tmp_path/"tampered"
    shutil.copytree(root/"email",destination)
    manifest=json.loads((destination/"manifest.json").read_bytes())
    manifest["components"]["extractor_sha256"]="0"*64
    (destination/"manifest.json").write_text(json.dumps(manifest))
    digest=hashlib.sha256((destination/"manifest.json").read_bytes()).hexdigest()
    with pytest.raises(InputContractError,match="version"):
        load_bundle(destination,expected_manifest_sha256=digest,max_bytes=20000000)


def test_opt_in_retains_metadata_only(existing):
    root,receipt,_=existing
    config=settings(root,receipt);config.artifact_metadata_retention_enabled=True
    service=ArtifactAnalysisService(config)
    response=api(service).post("/api/v1/artifact-analysis",json=submission(fixture_artifact("Email",1,1),retain_metadata=True))
    assert response.status_code==200
    raw=service._memory.execute("SELECT metadata_json FROM artifact_analysis_metadata").fetchone()[0]
    assert set(json.loads(raw))=={"schema_version","run_id","artifact_sha256","modality","status","result_category","versions"}
    assert "subject" not in raw and "password" not in raw
    assert "attribution" not in json.loads(raw)  # component version is allowed metadata; the explanation is not
    service._memory.close()
