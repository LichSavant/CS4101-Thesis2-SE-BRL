import math

import pytest

from ml.features import (
    ConventionalFeatureBuilder, FeatureConfiguration, FeatureUnavailableError,
    SplitManifest, TfidfExtractor, structural_features,
)
from ml.models import CandidateAlgorithm, ModelUnavailableError, prepare_training_input
from ml.pipeline import ComponentExecutionError, PretrainingPipeline
from ml.preprocessing import ArtifactParserError, preprocess
from ml.se_brl import serialize_result_envelope


def prepared(subject):
    return preprocess({"kind": "email", "subject": subject})


@pytest.mark.parametrize("analyzer,ngrams", [("word", (1, 1)), ("char", (3, 3))])
def test_tfidf_fit_transform_training_only(analyzer, ngrams):
    extractor = TfidfExtractor(analyzer, ngrams)
    manifest = SplitManifest("fixture-split", ("a", "b"), ("v",), ("t",))
    with pytest.raises(FeatureUnavailableError):
        extractor.transform(prepared("alpha"))
    with pytest.raises(ValueError, match="training"):
        extractor.fit({"a": prepared("alpha"), "v": prepared("leaked")}, manifest)
    extractor.fit({"a": prepared("alpha beta"), "b": prepared("alpha")}, manifest)
    before = (extractor.vocabulary, dict(extractor.idf))
    output = extractor.transform(prepared("unseen ΩΩΩ"))
    assert (extractor.vocabulary, dict(extractor.idf)) == before
    assert all(value == 0 for value in output.values.values())
    with pytest.raises(ValueError, match="fresh"):
        extractor.fit({"a": prepared("a"), "b": prepared("b")}, manifest)


def test_tfidf_smoothed_idf_and_normalization():
    extractor = TfidfExtractor()
    extractor.fit({"a": prepared("alpha beta"), "b": prepared("alpha")}, SplitManifest("fixture", ("a", "b")))
    assert extractor.idf["alpha"] == 1
    assert extractor.idf["beta"] == pytest.approx(math.log(3 / 2) + 1)
    weights = extractor.transform(prepared("alpha beta")).require_numeric()
    assert sum(v * v for v in weights.values()) == pytest.approx(1)
    with pytest.raises(TypeError):
        extractor.idf["alpha"] = 2


def test_empty_vocabulary_is_not_fake_data():
    extractor = TfidfExtractor()
    extractor.fit({"a": prepared("")}, SplitManifest("empty-fixture", ("a",)))
    assert dict(extractor.transform(prepared("new")).require_numeric()) == {}


def test_split_overlap_rejected():
    with pytest.raises(ValueError):
        SplitManifest("invalid", ("a",), ("a",))


def test_structural_and_url_features_are_counts_not_risk():
    artifact = preprocess({"kind": "webpage", "html": '<form><input type="password"><input type="email"></form>', "page_url": "http://127.0.0.1/a?x=2"})
    values = structural_features(artifact).values
    assert values["conventional:form_count"] == 1
    assert values["conventional:input_count"] == 2
    assert values["conventional:password_input_count"] == 1
    assert values["conventional:url_ip_host_count"] == 1
    assert values["conventional:url_http_count"] == 1
    assert not any("risk" in name or "probability" in name for name in values)
    assert structural_features(preprocess({"kind": "email", "link_extraction_authorized": False})).values["conventional:links_authorized"] == 0


def test_email_metadata_features():
    values = structural_features(preprocess({"kind": "email", "subject": "Hello", "sender": "A <a@example.test>", "reply_to": "b@other.test"})).values
    assert values["conventional:sender_reply_domain_differ"] == 1
    assert values["conventional:body_supplied"] == 0


def test_pipeline_prepares_all_configs_and_never_fits_or_predicts():
    result = PretrainingPipeline().run({"kind": "email", "subject": "Act now!"})
    assert result.envelope.overall_status == "not_evaluated"
    assert len(result.features) == 3
    e1, e2, e3 = result.features
    assert e1.block.missing_components == ("word_tfidf_not_fitted", "char_tfidf_not_fitted")
    assert len(e2.block.values) == 8
    assert all(e2.block.values[f"se_brl:z{i}"] is None for i in range(1, 5))
    assert dict(e3.block.values) == dict(e1.block.values) | dict(e2.block.values)
    for config in FeatureConfiguration:
        with pytest.raises(FeatureUnavailableError):
            result.model_input(config)
    wire = serialize_result_envelope(result.envelope)
    assert "Act now" not in repr(wire)
    assert "probability" not in wire and "classification" not in wire


def test_fitted_e1_reaches_missing_model_boundary_e2_e3_stay_blocked():
    conventional = ConventionalFeatureBuilder()
    conventional.fit({"fixture": prepared("Hello")}, SplitManifest("fixture", ("fixture",)))
    pipeline = PretrainingPipeline(conventional)
    result = pipeline.run({"kind": "email", "subject": "Hello"})
    features = result.model_input(FeatureConfiguration.E1)
    assert features.block.require_numeric()
    with pytest.raises(ModelUnavailableError):
        pipeline.model.predict(features)
    for config in (FeatureConfiguration.E2, FeatureConfiguration.E3):
        with pytest.raises(FeatureUnavailableError):
            result.model_input(config)
    assert {candidate.value for candidate in CandidateAlgorithm} == {"logistic_regression", "linear_svm", "random_forest", "xgboost"}


def test_standalone_url_keeps_technical_features_behavior_unavailable():
    result = PretrainingPipeline(ConventionalFeatureBuilder(include_tfidf=False)).run({"kind": "url", "url": "https://act-now.test/claim-prize"})
    assert result.representation.slots == (None, None, None, None, 0, 0, 0, 0)
    assert result.model_input(FeatureConfiguration.E1).block.values["conventional:url_count"] == 1
    assert not any(i.evidence for i in result.representation.extraction.indicators)


@pytest.mark.parametrize("raw,reason", [
    ({"kind": "video"}, "unsupported_modality"),
    ({"kind": "email", "subject": 123}, "invalid_schema"),
    ({"kind": "email", "body": "unauthorized"}, "invalid_schema"),
    ({"kind": "webpage"}, "missing_required_evidence"),
])
def test_safe_review_paths(raw, reason):
    result = PretrainingPipeline().run(raw)
    assert result.envelope.overall_status == "review_required"
    assert result.envelope.reason_codes == (reason,)
    with pytest.raises(ValueError):
        result.model_input(FeatureConfiguration.E1)


def test_operational_failures_sanitized_programming_errors_surface(monkeypatch):
    pipeline = PretrainingPipeline()
    def fail(_):
        raise ComponentExecutionError("private internal detail")
    monkeypatch.setattr(pipeline.conventional, "transform", fail)
    result = pipeline.run({"kind": "email", "subject": "Hello"})
    assert result.envelope.overall_status == "failed"
    assert result.features == () and result.artifact is None
    assert "private" not in repr(result)
    def bug(_):
        raise RuntimeError("programming defect")
    monkeypatch.setattr(pipeline.conventional, "transform", bug)
    with pytest.raises(RuntimeError, match="programming defect"):
        pipeline.run({"kind": "email", "subject": "Hello"})


def test_parser_failure_is_review_required(monkeypatch):
    def fail(_):
        raise ArtifactParserError("private detail")
    monkeypatch.setattr("ml.pipeline.preprocess", fail)
    result = PretrainingPipeline().run({"kind": "webpage", "html": "bad"})
    assert result.envelope.reason_codes == ("parser_failure",)
    assert "private" not in repr(result)


def test_training_boundary_validates_splits_labels_and_feature_readiness():
    pipeline = PretrainingPipeline(ConventionalFeatureBuilder(include_tfidf=False))
    bundles = pipeline.run({"kind": "email", "subject": "Hello"}).features
    manifest = SplitManifest("synthetic", ("train",), (), ("test",))
    data = prepare_training_input({"train": bundles[0]}, {"train": "synthetic-label"}, manifest)
    assert data.record_ids == ("train",) and len(data.rows[0]) == len(data.feature_names)
    with pytest.raises(ValueError):
        prepare_training_input({"test": bundles[0]}, {"test": "synthetic-label"}, manifest)
    with pytest.raises(ValueError):
        prepare_training_input({"train": bundles[0]}, {}, manifest)
    with pytest.raises(FeatureUnavailableError):
        prepare_training_input({"train": bundles[1]}, {"train": "synthetic-label"}, manifest)
