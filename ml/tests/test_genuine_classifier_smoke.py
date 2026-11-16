"""Fixture-only complete adapter path and independent metric checks."""
from importlib.util import find_spec
import json
import random

import pytest

from ml.classifier_adapters import ClassifierDependencyError
from ml.development_runner import verify_synthetic_bundle
from ml.evaluation_metrics import binary_metrics
from ml.experiment_inputs import InputContractError
from ml.genuine_classifier_smoke import demonstrate

SCIENCE = all(find_spec(n) is not None for n in ("numpy", "scipy", "sklearn", "xgboost"))
genuine = pytest.mark.skipif(not SCIENCE, reason="genuine classifier dependencies absent; no substitute run")


def test_existing_output_rejected_without_computation(tmp_path, monkeypatch):
    import ml.genuine_classifier_smoke as smoke
    monkeypatch.setattr(smoke, "require_dependencies", lambda *a: pytest.fail("existing output reached computation"))
    marker = tmp_path / "user-work.txt"
    marker.write_text("preserve")
    with pytest.raises(InputContractError):
        demonstrate(tmp_path, code_reference="synthetic-only")
    assert marker.read_text() == "preserve"
    assert list(tmp_path.iterdir()) == [marker]


def test_missing_dependency_creates_no_files(tmp_path, monkeypatch):
    import ml.genuine_classifier_smoke as smoke
    def unavailable(*args):
        raise ClassifierDependencyError("fixture missing dependency")
    monkeypatch.setattr(smoke, "require_dependencies", unavailable)
    with pytest.raises(ClassifierDependencyError):
        demonstrate(tmp_path / "unused", code_reference="synthetic-only")
    assert list(tmp_path.iterdir()) == []


@genuine
def test_genuine_demo_all_families_ablations_and_replay(tmp_path):
    root = tmp_path / "synthetic-genuine"
    result = demonstrate(root, code_reference="synthetic-test")
    assert result["genuine_estimator_fit_calls"] == 180
    assert result["research_models_fitted"] == result["calibration_fits"] == 0
    assert not result["selection_performed"]
    assert json.loads((root / "summary.json").read_text()) == result
    assert len(result["bundles"]) == 4
    for item in result["bundles"]:
        manifest = verify_synthetic_bundle(root / item["bundle"])
        assert item["email_oof_rows"] == 30
        assert len(manifest["dimension_ablation_smoke"]) == 4
        assert manifest["technical_u1_smoke"]["oof_rows"] == 10
        assert manifest["efficiency_smoke"]["measured_memory_bytes_max"] is None
        assert manifest["efficiency_smoke"]["serialized_model_bytes"] is None
        assert manifest["paired_bootstrap_smoke"]["resamples_requested"] == 25
        assert manifest["source_slice_smoke"]["source_independence_established"] is False
        assert all(s["roc_auc"] is None for s in manifest["source_slice_smoke"]["slices"].values())


@genuine
@pytest.mark.parametrize("seed", range(5))
def test_metrics_match_independent_sklearn_on_tied_synthetic_scores(seed):
    from sklearn.metrics import (average_precision_score, roc_auc_score, brier_score_loss,
        confusion_matrix, precision_score, recall_score, f1_score, balanced_accuracy_score, matthews_corrcoef)
    rng = random.Random(seed)
    y = (0, 1) * 20
    p = tuple(rng.choice((0., .2, .5, .8, 1.)) for _ in y)
    predictions = tuple(int(v >= .5) for v in p)
    actual = binary_metrics(y, p, positive_label=1, threshold=.5, probabilities=p, calibration_edges=(0., .5, 1.))
    assert actual["average_precision"] == pytest.approx(average_precision_score(y, p))
    assert actual["roc_auc"] == pytest.approx(roc_auc_score(y, p))
    assert actual["brier_score"] == pytest.approx(brier_score_loss(y, p))
    assert actual["confusion_matrix"] == confusion_matrix(y, predictions).tolist()
    for key, fn in (("precision", precision_score), ("recall", recall_score), ("f1", f1_score),
                    ("balanced_accuracy", balanced_accuracy_score), ("mcc", matthews_corrcoef)):
        assert actual[key] == pytest.approx(fn(y, predictions))
