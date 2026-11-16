"""Complete nested synthetic bundles include digest-bound models and calibration."""
from pathlib import Path

import pytest

from ml.development_experiments import development_folds
from ml.experiment_artifacts import write_nested_bundle, load_nested_bundle
from ml.experiment_engine import run_synthetic_nested_cv
from ml.experiment_inputs import InputContractError
from ml.synthetic_demo import fixture
from ml.tests.test_classifier_adapters import genuine
from ml.tests.test_experiment_engine import spec


@genuine
def test_complete_bundle_roundtrip_and_preservation(tmp_path):
    dataset = fixture()
    result, fitted = run_synthetic_nested_cv(dataset, spec())
    directory = tmp_path / "run"
    digest = write_nested_bundle(directory, result, fitted, code_reference="synthetic:test", code_hashes={"fixture": "a" * 64})
    manifest, restored = load_nested_bundle(directory, expected_manifest_sha256=digest, max_bytes=20_000_000)
    assert manifest["research_execution"] == "BLOCKED" and len(restored) == 5
    for (_, _, a, cal_a, threshold_a), (_, _, b, cal_b, threshold_b), fold in zip(fitted, restored, development_folds(dataset, "E3")):
        scores_a = a.score(fold.x_validation, observation_ids=fold.validation_ids).scores
        scores_b = b.score(fold.x_validation, observation_ids=fold.validation_ids).scores
        assert cal_a.probabilities(scores_a) == cal_b.probabilities(scores_b)
        assert threshold_a == threshold_b
    before = {p.relative_to(directory): p.read_bytes() for p in directory.rglob("*") if p.is_file()}
    with pytest.raises(InputContractError):
        write_nested_bundle(directory, result, fitted, code_reference="synthetic:test", code_hashes={"fixture": "a" * 64})
    assert before == {p.relative_to(directory): p.read_bytes() for p in directory.rglob("*") if p.is_file()}
    (directory / "results/oof_predictions.csv").write_bytes(b"tamper")
    with pytest.raises(InputContractError, match="payload_mismatch"):
        load_nested_bundle(directory, expected_manifest_sha256=digest, max_bytes=20_000_000)


@genuine
def test_bundle_failure_no_completion_or_partial_leaf(tmp_path, monkeypatch):
    result, fitted = run_synthetic_nested_cv(fixture(), spec())
    with pytest.raises(InputContractError, match="coverage"):
        write_nested_bundle(tmp_path / "missing", result, fitted[:-1], code_reference="synthetic:test", code_hashes={"fixture": "a" * 64})
    assert list(tmp_path.iterdir()) == []
    original = Path.open
    directory = tmp_path / "failed"
    def denied(path, *args, **kwargs):
        if path == directory / "run_manifest.json" and args and args[0] == "xb":
            raise OSError("synthetic injected failure")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(InputContractError, match="nested_bundle_write_failed"):
        write_nested_bundle(directory, result, fitted, code_reference="synthetic:test", code_hashes={"fixture": "a" * 64})
    assert list(tmp_path.iterdir()) == []
