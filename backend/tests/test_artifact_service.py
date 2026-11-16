"""Isolated artifact API tests; never import main or its persistent repository."""
import asyncio
import json
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.app.artifact_service import ArtifactAnalysisService, ArtifactBodyLimit, artifact_router
from ml.artifact_analysis import ArtifactAnalyzer
from ml.synthetic_system import fixture_bundle, fixture_artifact


def settings(**changes):
    values = dict(artifact_email_bundle=None, artifact_email_bundle_sha256=None,
                  artifact_web_bundle=None, artifact_web_bundle_sha256=None,
                  artifact_bundle_max_bytes=20_000_000, artifact_timeout_seconds=2.,
                  artifact_metadata_retention_enabled=False, database_url="sqlite:///:memory:")
    return SimpleNamespace(**dict(values, **changes))


def client(service, limit=1_000_000):
    app = FastAPI()
    app.include_router(artifact_router(service))
    app.add_middleware(ArtifactBodyLimit, max_bytes=limit)
    return TestClient(app, headers={"content-type":"application/json"})


def submission(**changes):
    values = dict(schema_version="artifact-decision-1.0", artifact=fixture_artifact("Email", 9, 1),
                  language="en", submission_authorized=True, retain_metadata=False)
    return dict(values, **changes)


@pytest.fixture(scope="module")
def bundle():
    return fixture_bundle()


def test_post_runs_complete_flow_without_persistence(bundle, monkeypatch):
    service = ArtifactAnalysisService(settings())
    monkeypatch.setattr(service, "_analyzer", lambda *_: ArtifactAnalyzer({"content_bearing_email": bundle}))
    response = client(service).post("/api/v1/artifact-analysis", json=submission())
    assert response.status_code == 200
    assert response.json()["status"] == "complete"
    assert response.json()["research_validated"] is False
    assert service._memory is None


def test_invalid_consent_schema_payload_and_errors_do_not_echo_content():
    service = ArtifactAnalysisService(settings())
    api = client(service)
    for body, code in ((submission(submission_authorized=False), 403),
                       (submission(submission_authorized="true"), 422),
                       (submission(schema_version="bad"), 422),
                       (submission(extra="SENSITIVE SECRET"), 422),
                       (submission(retain_metadata=True), 403)):
        response = api.post("/api/v1/artifact-analysis", json=body)
        assert response.status_code == code
        assert "SENSITIVE" not in response.text
    response = api.post("/api/v1/artifact-analysis", content=b'{"secret":"SENSITIVE",broken')
    assert response.status_code == 422 and "SENSITIVE" not in response.text
    response = client(service, limit=100).post("/api/v1/artifact-analysis", json=submission())
    assert response.status_code == 413
    assert service._memory is None


def test_missing_tampered_bundle_and_outage_are_not_legitimate(monkeypatch):
    service = ArtifactAnalysisService(settings())
    response = client(service).post("/api/v1/artifact-analysis", json=submission())
    assert response.status_code == 200 and response.json()["status"] == "review_required"
    def unavailable(*_):
        raise ValueError("PRIVATE PATH or SECRET")
    monkeypatch.setattr(service, "_analyzer", unavailable)
    response = client(service).post("/api/v1/artifact-analysis", json=submission())
    assert response.status_code == 503
    assert "PRIVATE" not in response.text and "SECRET" not in response.text


def test_opt_in_metadata_contains_no_text_probability_or_explanation(bundle, monkeypatch):
    service = ArtifactAnalysisService(settings(artifact_metadata_retention_enabled=True))
    monkeypatch.setattr(service, "_analyzer", lambda *_: ArtifactAnalyzer({"content_bearing_email": bundle}))
    response = client(service).post("/api/v1/artifact-analysis", json=submission(retain_metadata=True))
    assert response.status_code == 200
    record = service._memory.execute("SELECT metadata_json FROM artifact_analysis_metadata").fetchone()[0]
    metadata = json.loads(record)
    assert set(metadata) == {"schema_version", "run_id", "artifact_sha256", "modality", "status", "result_category", "versions"}
    assert "Fixture" not in record and "subject" not in record and "password" not in record
    service._memory.close()


def test_timeout_returns_no_partial_result_or_metadata(bundle, monkeypatch):
    import time
    service = ArtifactAnalysisService(settings(artifact_timeout_seconds=.01, artifact_metadata_retention_enabled=True))
    def slow(*_):
        time.sleep(.04)
        return ArtifactAnalyzer({"content_bearing_email": bundle})
    monkeypatch.setattr(service, "_analyzer", slow)
    response = client(service).post("/api/v1/artifact-analysis", json=submission(retain_metadata=True))
    assert response.status_code == 504
    assert "probability" not in response.text
    assert service._memory is None


@pytest.mark.parametrize("kind", ["webpage", "url", "technical", None])
def test_phase1_rejects_non_email_before_analysis(kind, monkeypatch):
    service = ArtifactAnalysisService(settings())
    monkeypatch.setattr(service, "_analyzer", lambda *_: pytest.fail("Non-email analysis must not run"))
    response = client(service).post("/api/v1/artifact-analysis", json=submission(artifact={"kind": kind}))
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "phase1_email_only"
    assert service._memory is None
