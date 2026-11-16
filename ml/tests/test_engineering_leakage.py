"""Synthetic no-fit regression for dictionary and matrix field enforcement."""
import pytest

from ml.development_experiments import FeatureColumn
from ml.experiment_inputs import BOOKKEEPING, InputContractError, select_predictors


@pytest.mark.parametrize("name", ["FILENAME", "filename", "FileName", *sorted(BOOKKEEPING)])
def test_dictionary_and_selection_reject_same_metadata(name):
    for operation in (lambda: FeatureColumn(name, "numeric"),
                      lambda: select_predictors({name: 1}, (name,))):
        with pytest.raises(InputContractError, match="bookkeeping_predictor_forbidden"):
            operation()


@pytest.mark.parametrize("name", ["URL_Length", "Domain", "TLD", "model_text", "conventional:text_char_count"])
def test_valid_fields_retain_exact_case_and_values(name):
    assert FeatureColumn(name, "numeric").name == name
    assert dict(select_predictors({name: 17, "FILENAME": "private.htm"}, (name,))) == {name: 17}
    with pytest.raises(InputContractError, match="missing_predictor_field"):
        select_predictors({name: 17}, (name.upper()+"_missing",))


def test_forbidden_selection_is_rejected_even_when_value_missing():
    with pytest.raises(InputContractError, match="bookkeeping_predictor_forbidden"):
        select_predictors({}, ("FILENAME",))
