from dataclasses import replace
import json

import pytest

from ml.feature_schema import FeatureSchema
from ml.feature_storage import CombinedFeatureValues, SparseFeatureValues
from ml.features import ConventionalFeatureBuilder, FeatureBlock, FeatureConfiguration, FeatureUnavailableError, SplitManifest, TfidfExtractor
from ml.models import prepare_training_input
from ml.pipeline import PretrainingPipeline
from ml.preprocessing import PREPROCESSING_VERSION, preprocess
from ml.readiness import pipeline_readiness
from ml.tests.test_dataset_boundaries import record
from ml.datasets import PhishingLabel, SourcePhishingLabel


def test_feature_schema_is_reproducible_and_round_trips():
    raw = {"kind": "email", "subject": "Hello"}
    first = PretrainingPipeline().run(raw)
    second = PretrainingPipeline().run(raw)
    for left, right in zip(first.features, second.features):
        assert left.schema.configuration_id == right.schema.configuration_id
        assert FeatureSchema.from_json(left.schema.to_json()) == left.schema
        assert left.schema.preprocessing_version == PREPROCESSING_VERSION
        assert left.schema.codebook_version == "0.1.0"
        assert left.schema.ruleset_version == "0.2.0"
    assert len({b.schema.configuration_id for b in first.features}) == 3
    assert "Hello" not in first.features[0].schema.to_json()
    with pytest.raises(ValueError):
        FeatureSchema.from_json(first.features[0].schema.to_json().replace('"schema_version":"0.1.0"', '"schema_version":"99"'))


def test_fitted_tfidf_signature_is_deterministic_and_changes_with_training_input():
    split = SplitManifest("fixture", ("a",))
    instances = [TfidfExtractor() for _ in range(3)]
    for extractor, text in zip(instances, ("hello", "hello", "other")):
        extractor.fit({"a": preprocess({"kind": "email", "subject": text})}, split)
    assert instances[0].describe_configuration() == instances[1].describe_configuration()
    assert instances[0].fitted_state_id != instances[2].fitted_state_id
    with pytest.raises(AttributeError):
        instances[0].vocabulary = ("tampered",)
    instances[0].ngram_range = (1, 2)
    with pytest.raises(ValueError, match="changed"):
        instances[0].transform(preprocess({"kind": "email", "subject": "hello"}))


def test_training_rejects_same_columns_with_different_feature_configuration():
    bundle = PretrainingPipeline(ConventionalFeatureBuilder(include_tfidf=False)).run({"kind": "email", "subject": "Hello"}).features[0]
    different = replace(bundle, schema=replace(bundle.schema, ruleset_version="future"))
    with pytest.raises(ValueError, match="schemas"):
        prepare_training_input({"a": bundle, "b": different}, {"a": "fixture", "b": "fixture"}, SplitManifest("fixture", ("a", "b")))


def test_sparse_mapping_survives_e1_and_e3_and_never_imputes_unknown_z():
    values = SparseFeatureValues(("a", "b", "c"), {"b": 2.0})
    assert dict(values) == {"a": 0.0, "b": 2.0, "c": 0.0}
    class SparseExtractor:
        def transform(self, artifact):
            return FeatureBlock(values, configuration_json='{"backend":"fixture-sparse"}', preprocessing_version=artifact.preprocessing_version)
    result = PretrainingPipeline(SparseExtractor()).run({"kind": "email", "subject": "Hello"})
    assert result.features[0].block.values is values
    assert result.features[0].block.require_numeric() is values
    assert isinstance(result.features[2].block.values, CombinedFeatureValues)
    assert result.features[2].block.values["a"] == 0.0
    assert result.features[2].block.values["se_brl:z1"] is None
    with pytest.raises(FeatureUnavailableError):
        result.features[2].block.require_numeric()
    with pytest.raises(AttributeError):
        values._values = {}
    with pytest.raises(ValueError):
        CombinedFeatureValues((values, {"a": 3}))
    with pytest.raises(ValueError):
        SparseFeatureValues(("a",), {"not-in-schema": 2})
    with pytest.raises(FeatureUnavailableError):
        FeatureBlock(SparseFeatureValues(("a",), {"a": None})).require_numeric()


def test_readiness_never_promotes_research_stages():
    report = pipeline_readiness().to_dict()
    stages = {s["stage"]: s for s in report["stages"]}
    assert stages["preprocessing"]["status"] == "ready"
    assert stages["candidate_rule_extraction"]["status"] == "partial"
    assert stages["behavioral_model"]["status"] == "not_trained"
    assert stages["behavioral_ground_truth"]["dependencies"] == ["dataset_dependent", "ground_truth_dependent"]
    assert stages["E1"]["status"] == "structurally_ready"
    assert stages["E2"]["status"] == stages["E3"]["status"] == "blocked_by_z_values"
    assert stages["decision_rules"]["status"] == "not_frozen"
    assert json.loads(json.dumps(report)) == report
    pipeline = PretrainingPipeline(ConventionalFeatureBuilder(include_tfidf=False))
    good = pipeline.run({"kind": "email", "subject": "Hello"})
    statuses = {s.stage: s.status.value for s in pipeline.readiness(good).stages}
    assert statuses["E1"] == "ready" and statuses["classifier"] == "not_trained"
    bad = pipeline.run({"kind": "email", "subject": 2})
    assert {s.stage: s.status.value for s in pipeline.readiness(bad).stages}["E1"] == "unavailable"


def test_dataset_pipeline_retains_provenance_and_preprocesses_once(monkeypatch):
    import ml.pipeline as module
    original = module.preprocess
    calls = []
    def observed(raw):
        calls.append(raw)
        return original(raw)
    monkeypatch.setattr(module, "preprocess", observed)
    source = record()
    result = PretrainingPipeline().run_record(source)
    assert len(calls) == 1
    assert result.record is source
    assert result.analysis.envelope.overall_status == "not_evaluated"
    with pytest.raises(ValueError, match="availability"):
        PretrainingPipeline().run_record(record(content_available=False))


def test_source_phishing_label_never_enters_features_or_behavioral_evidence():
    pipeline = PretrainingPipeline()
    source = record()
    labeled = replace(source, phishing_label=SourcePhishingLabel(PhishingLabel.PHISHING, "fixture-source"))
    first = pipeline.run_record(source).analysis
    second = pipeline.run_record(labeled).analysis
    assert first.features == second.features
    assert first.representation == second.representation
