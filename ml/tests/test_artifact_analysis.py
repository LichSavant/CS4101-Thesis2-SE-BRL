"""Synthetic submission boundary; no research records, database or network."""
from dataclasses import replace
import hashlib
import json

import pytest

from ml.artifact_analysis import ArtifactAnalyzer, write_bundle, load_bundle
from ml.decision import RiskPolicy, decide, validate_decision
from ml.experiment_inputs import InputContractError
from ml.synthetic_system import fixture_bundle, fixture_artifact


@pytest.fixture(scope="module")
def bundle():
    return fixture_bundle()


@pytest.mark.parametrize("family", ("logistic_regression", "linear_svm", "random_forest", "xgboost"))
def test_genuine_classifier_evidence_calibration_attribution_decision(family):
    b = fixture_bundle(family=family)
    raw = fixture_artifact("Email", 55, 1)
    result = ArtifactAnalyzer({"content_bearing_email": b}).analyze(raw, language="en")
    assert result["status"] == "complete", result
    assert result["research_validated"] is False
    assert result["result_category"] == "synthetic_model_generated"
    assert 0 <= result["calibrated_probability"] <= 1
    attribution = result["attribution"]
    assert attribution["channel"] == "model_attribution_not_artifact_evidence"
    assert sum(f["contribution"] for f in attribution["features"]) + attribution["omitted_contribution"] + attribution["base_value"] == pytest.approx(attribution["explained_output"], abs=2e-5)
    assert len(result["behavioral_evidence"]) == 12
    assert result["decision"]["severity"] == 3
    for indicator in result["behavioral_evidence"]:
        for evidence in indicator["evidence"]:
            for locator in evidence["locators"]:
                assert raw[locator["field"]][locator["start"]:locator["end"]]
    serialized = json.dumps(result)
    assert raw["subject"] not in serialized
    assert "Fixture item 55" not in serialized
    assert "mean_tree_path" in attribution["method"] if family == "random_forest" else True


def test_web_routing_and_no_active_markup(bundle):
    b = fixture_bundle("Web")
    analyzer = ArtifactAnalyzer({"content_bearing_webpage": b})
    assert analyzer.analyze(fixture_artifact("Web", 5, 1), language="en")["status"] == "complete"
    result = analyzer.analyze({"kind": "webpage", "html": '<script>fetch("https://forbidden.test")</script><p>Act now. Submit your password.</p>'}, language="en")
    # HTML supplies conditional evidence, but no independently audited trust
    # references exist. The incomplete E3 input must remain blocked.
    assert result["status"] == "review_required", result
    assert "behavioral_evaluation_incomplete" in result["decision"]["reasons"]
    assert "<script>" not in json.dumps(result)
    assert "fetch(" not in json.dumps(result)
    assert result["decision"]["severity"] == 2
    with pytest.raises(InputContractError, match="routing"):
        ArtifactAnalyzer({"content_bearing_email": b})


@pytest.mark.parametrize("raw,language,reason", [
    ({"kind": "email", "subject": "Synthetic notice"}, "unknown", "unsupported_or_unknown_language"),
    ({"kind": "email", "subject": "Synthetic notice"}, "fr", "unsupported_or_unknown_language"),
    ({"kind": "email"}, "en", "missing_required_content"),
    ({"kind": "email", "subject": "S"*200001}, "en", "component_failure"),
    ({"kind": "email", "subject": "Notice", "body": "SENSITIVE"}, "en", "component_failure"),
    ({"kind": "email", "subject": "Notice", "sender": "sender@example.test"}, "en", "behavioral_evaluation_incomplete"),
    ({"kind": "url", "url": "https://example.test/"}, "en", "source_specific_technical_features_required"),
])
def test_failure_cannot_reuse_a_prior_complete_prediction(bundle, raw, language, reason):
    analyzer = ArtifactAnalyzer({"content_bearing_email": bundle})
    assert analyzer.analyze(fixture_artifact("Email", 1, 0), language="en")["status"] == "complete"
    result = analyzer.analyze(raw, language=language)
    assert result["status"] == "review_required"
    assert result["classification"] is result["calibrated_probability"] is result["attribution"] is None
    assert reason in result["decision"]["reasons"]
    assert result["decision"]["tier"] == "review_required"
    assert "SENSITIVE" not in json.dumps(result)


def test_missing_bundle_timeout_and_attribution_outage(bundle, monkeypatch):
    import ml.artifact_analysis as module
    raw = fixture_artifact("Email", 1, 0)
    assert "compatible_bundle_unavailable" in ArtifactAnalyzer().analyze(raw, language="en")["decision"]["reasons"]
    ticks = iter(range(100))
    analyzer = ArtifactAnalyzer({"content_bearing_email": bundle}, timeout_seconds=.1, clock=lambda: next(ticks))
    assert "analysis_timeout" in analyzer.analyze(raw, language="en")["decision"]["reasons"]
    def fail(*args, **kwargs):
        raise RuntimeError("secret source text MUST NOT LEAK")
    monkeypatch.setattr(module, "explain", fail)
    result = ArtifactAnalyzer({"content_bearing_email": bundle}).analyze(raw, language="en")
    assert result["status"] == "review_required" and "MUST NOT LEAK" not in json.dumps(result)


def test_srs_risk_precedence_and_severity_boundary():
    policy = RiskPolicy(.3, .8, .5, "synthetic:test", "synthetic_fixture")
    def tier(p, severity=0, families=(), coverage=1., reasons=()):
        return decide(p, severity=severity, families=families, coverage=coverage, reasons=reasons, policy=policy)["tier"]
    assert tier(.99, 3, reasons=("evidence_conflict",)) == "review_required"
    assert tier(.99, 3, coverage=.1) == "review_required"
    assert tier(.8, 2) == "high"
    assert tier(.8, 0, ("behavioral_language", "form_structure")) == "high"
    assert tier(.99) == "elevated"  # high p alone is not sufficient
    assert tier(.1, 2, ("form_structure",)) == "elevated"
    assert tier(.1, 2) == "review_required"  # severe request cannot be informational
    assert tier(.1) == "informational"
    for p in (float("nan"), float("inf"), None, True):
        assert tier(p) == "review_required"


def test_bundle_roundtrip_tamper_versions_and_exclusive_creation(bundle, tmp_path):
    directory = tmp_path / "bundle"
    digest = write_bundle(directory, bundle, code_reference="synthetic:test-source-hash")
    restored = load_bundle(directory, expected_manifest_sha256=digest, max_bytes=20_000_000)
    raw = fixture_artifact("Email", 9, 1)
    expected = ArtifactAnalyzer({"content_bearing_email": bundle}).analyze(raw, language="en")
    actual = ArtifactAnalyzer({"content_bearing_email": restored}).analyze(raw, language="en")
    assert actual["calibrated_probability"] == pytest.approx(expected["calibrated_probability"])
    with pytest.raises(InputContractError, match="unused"):
        write_bundle(directory, bundle, code_reference="synthetic:test")
    with pytest.raises(InputContractError, match="digest"):
        load_bundle(directory, expected_manifest_sha256="0"*64, max_bytes=20_000_000)
    (directory / "calibrator.json").write_text("{}")
    with pytest.raises(InputContractError, match="digest"):
        load_bundle(directory, expected_manifest_sha256=digest, max_bytes=20_000_000)


def test_partial_output_and_research_scope_cannot_be_promoted(bundle):
    with pytest.raises(InputContractError):
        replace(bundle, scope="frozen_research")
    result = ArtifactAnalyzer().analyze(fixture_artifact("Email", 1, 0), language="en")
    result["calibrated_probability"] = .01
    with pytest.raises(InputContractError, match="partial"):
        validate_decision(result)


@pytest.mark.parametrize("dataset",("UCI","PhiUSIIL"))
def test_technical_route_never_invokes_content_rules_and_preserves_native_values(dataset,monkeypatch,tmp_path):
    from ml.se_brl.extraction import RuleEngine
    b=fixture_bundle(dataset)
    def forbidden(*args,**kwargs):
        pytest.fail("Technical U1 invoked a content rule")
    monkeypatch.setattr(RuleEngine,"extract",forbidden)
    raw=fixture_artifact(dataset,1,1)
    if dataset=="UCI":raw["features"]["URL_Length"]=0
    result=ArtifactAnalyzer({dataset:b}).analyze(raw,language="unknown")
    assert result["status"]=="complete",result
    assert all(i["state"]=="unavailable" and not i["evidence"] for i in result["behavioral_evidence"])
    assert result["decision"]["severity"]==0 and result["decision"]["corroborating_families"]==[]
    assert {f["finding"]:f["value"] for f in result["technical_findings"]}==raw["features"]
    directory=tmp_path/"model";digest=write_bundle(directory,b,code_reference="synthetic:technical-roundtrip")
    restored=load_bundle(directory,expected_manifest_sha256=digest,max_bytes=20000000)
    assert ArtifactAnalyzer({dataset:restored}).analyze(raw,language="unknown")["calibrated_probability"]==pytest.approx(result["calibrated_probability"])
    for features in ({**raw["features"],"target":1},{},{**raw["features"],next(iter(raw["features"])):None}):
        invalid=ArtifactAnalyzer({dataset:b}).analyze({**raw,"features":features},language="unknown")
        assert invalid["status"]=="review_required" and invalid["calibrated_probability"] is None


def test_bare_url_cannot_be_substituted_for_UCI_or_language_evidence(bundle):
    result=ArtifactAnalyzer({"content_bearing_email":bundle}).analyze({"kind":"url","url":"https://example.test/act-now"},language="unknown")
    assert result["status"]=="review_required"
    assert len(result["behavioral_evidence"])==12
    assert all(i["state"]=="unavailable" for i in result["behavioral_evidence"])
    assert "source_specific_technical_features_required" in result["decision"]["reasons"]
