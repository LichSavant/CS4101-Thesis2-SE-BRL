"""Overflow is invalid numeric input, not a corpus exclusion or raw exception."""
import pytest
from ml.development_experiments import build_development_dataset
from ml.experiment_inputs import InputContractError
from ml.tests.test_development_experiments import fixture_rows, spec
from ml.tests.test_uci_preparation import synthetic, invoke
from ml.evaluation_metrics import binary_metrics


def test_d9_huge_integer_uses_existing_numeric_contract_error():
    rows, vectors = fixture_rows()
    rows[0]["length"] = 10 ** 1000
    with pytest.raises(InputContractError, match="^invalid_numeric_predictor$"):
        build_development_dataset(rows, vectors, specification=spec())


def test_uci_huge_integer_fails_before_outputs(tmp_path):
    rows, assignments, ids, specification = synthetic()
    rows[0]["URL_Length"] = 10 ** 1000
    with pytest.raises(InputContractError, match="^invalid_numeric_predictor$"):
        invoke(tmp_path, rows, assignments, ids, specification)
    assert list(tmp_path.iterdir()) == []


def test_metric_huge_score_has_sanitized_contract_failure():
    with pytest.raises(InputContractError, match="^finite_aligned_scores_required$"):
        binary_metrics((0, 1), (0, 10 ** 1000), positive_label=1, threshold=.5)

