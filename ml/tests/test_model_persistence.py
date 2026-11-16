"""Safe persistence of genuine SYNTHETIC estimators; no research inputs."""
import hashlib
import io
import json
from pathlib import Path
import zipfile
from dataclasses import replace

import pytest

from ml.classifier_adapters import FoldClassifier
from ml.development_experiments import development_folds, FeatureColumn
from ml.experiment_inputs import InputContractError
from ml.metadata import canonical_json
from ml.model_persistence import save_fold_artifact, load_fold_artifact, _safe_skops_load
from ml.synthetic_demo import fixture
from ml.tests.test_classifier_adapters import genuine, model, preprocessing, text_parameters, FAMILIES


def fitted(family):
    ds = fixture()
    fold = development_folds(ds, "E3")[0]
    classifier = FoldClassifier(ds.specification, model(family), preprocessing(), "E3")
    classifier.fit(fold.x_train, fold.y_train, feature_names=fold.feature_names, seed=17)
    return classifier, fold


@genuine
@pytest.mark.parametrize("family", FAMILIES)
def test_roundtrip_prediction_identity_and_exclusive_creation(tmp_path, family):
    classifier, fold = fitted(family)
    directory = tmp_path / "model"
    digest = save_fold_artifact(directory, classifier, code_reference="synthetic:test")
    loaded = load_fold_artifact(directory, expected_manifest_sha256=digest, max_bytes=10_000_000)
    assert loaded.score(fold.x_validation, observation_ids=fold.validation_ids) == classifier.score(
        fold.x_validation, observation_ids=fold.validation_ids)
    assert loaded.audit_record() == classifier.audit_record()
    before = {p.name: p.read_bytes() for p in directory.iterdir()}
    with pytest.raises(InputContractError, match="unused_model_directory"):
        save_fold_artifact(directory, classifier, code_reference="synthetic:test")
    assert before == {p.name: p.read_bytes() for p in directory.iterdir()}


@genuine
def test_digests_resources_and_fixed_file_set_before_deserialization(tmp_path, monkeypatch):
    classifier, _ = fitted("logistic_regression")
    directory = tmp_path / "model"
    digest = save_fold_artifact(directory, classifier, code_reference="synthetic:test")
    import ml.model_persistence as persistence
    monkeypatch.setattr(persistence, "_safe_skops_load", lambda *a: pytest.fail("must reject before deserializing"))
    for supplied, cap in ((None, 10_000_000), ("0" * 64, 10_000_000), (digest, 1), (digest, True)):
        with pytest.raises(InputContractError):
            load_fold_artifact(directory, expected_manifest_sha256=supplied, max_bytes=cap)
    (directory / "extra").write_bytes(b"unexpected")
    with pytest.raises(InputContractError, match="files_mismatch"):
        load_fold_artifact(directory, expected_manifest_sha256=digest, max_bytes=10_000_000)
    (directory / "extra").unlink()
    with (directory / "pipeline.skops").open("ab") as stream:
        stream.write(b"tampered")
    with pytest.raises(InputContractError, match="payload_digest"):
        load_fold_artifact(directory, expected_manifest_sha256=digest, max_bytes=10_000_000)


@genuine
def test_version_and_duplicate_manifest_rejected(tmp_path):
    classifier, _ = fitted("logistic_regression")
    directory = tmp_path / "model"
    save_fold_artifact(directory, classifier, code_reference="synthetic:test")
    path = directory / "manifest.json"
    content = json.loads(path.read_bytes())
    content["versions"]["skops"] = "unsupported"
    body = canonical_json(content).encode()
    path.write_bytes(body)
    with pytest.raises(InputContractError, match="version_or_scope"):
        load_fold_artifact(directory, expected_manifest_sha256=hashlib.sha256(body).hexdigest(), max_bytes=10_000_000)
    body = b'{"family":"logistic_regression","family":"xgboost"}'
    path.write_bytes(body)
    with pytest.raises(InputContractError):
        load_fold_artifact(directory, expected_manifest_sha256=hashlib.sha256(body).hexdigest(), max_bytes=10_000_000)


def test_archive_limits_and_unknown_types_never_auto_trusted():
    class Scanner:
        def get_untrusted_types(self, **kwargs):
            return ["unreviewed.CustomType"]
        def loads(self, *args, **kwargs):
            pytest.fail("must never deserialize untrusted types")
    def archive(name, data=b"fixture"):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as file:
            file.writestr(name, data)
        return stream.getvalue()
    for payload, limit, error in ((archive("../escape"), 1000, "path_rejected"),
            (archive("large", b"x" * 2000), 1000, "resource_limit"),
            (archive("schema.json"), 1000, "untrusted_model_types"),
            (b"invalid", 1000, "archive_invalid")):
        with pytest.raises(InputContractError, match=error):
            _safe_skops_load(Scanner(), payload, limit)


@genuine
def test_failed_write_rolls_back_owned_leaf(tmp_path, monkeypatch):
    classifier, _ = fitted("logistic_regression")
    original = Path.open
    def denied(path, *args, **kwargs):
        if path.name == "manifest.json" and args and args[0] == "xb":
            raise OSError("fixture denied")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(InputContractError, match="write_failed"):
        save_fold_artifact(tmp_path / "model", classifier, code_reference="synthetic:test")
    assert list(tmp_path.iterdir()) == []


@genuine
def test_learned_vocabulary_idf_median_and_scaler_survive_reload(tmp_path):
    ds = fixture()
    ds = replace(ds, specification=replace(ds.specification, conventional=(FeatureColumn("model_text", "text"),
        FeatureColumn("observed_length", "numeric"))), observations=tuple(replace(r, conventional=(
            f"synthetic token{r.fold} {'request' if r.target else 'notice'}", None if r.fold == 2 else r.fold)) for r in ds.observations))
    fold = development_folds(ds, "E1")[0]
    classifier = FoldClassifier(ds.specification, model(), preprocessing(numeric_missing="median", numeric_scaling="standard",
        text_parameters=text_parameters()), "E1")
    classifier.fit(fold.x_train, fold.y_train, feature_names=fold.feature_names, seed=17)
    digest = save_fold_artifact(tmp_path / "text", classifier, code_reference="synthetic:text-state")
    restored = load_fold_artifact(tmp_path / "text", expected_manifest_sha256=digest, max_bytes=10_000_000)
    assert restored.score(fold.x_validation, observation_ids=fold.validation_ids) == classifier.score(
        fold.x_validation, observation_ids=fold.validation_ids)
    before, after = classifier.pipeline.named_steps["preprocess"], restored.pipeline.named_steps["preprocess"]
    for name in before.named_transformers_:
        a, b = before.named_transformers_[name], after.named_transformers_[name]
        if hasattr(a, "vocabulary_"):
            assert a.vocabulary_ == b.vocabulary_ and (a.idf_ == b.idf_).all()
            assert "token1" not in a.vocabulary_
