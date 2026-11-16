"""Candidate schema validation is not a scientific approval."""
from copy import deepcopy
from dataclasses import replace

import pytest

from ml.development_experiments import FeatureColumn
from ml.feature_freeze import load_candidate, validate_candidate, validate_candidate_dataset
from ml.experiment_inputs import InputContractError
from ml.synthetic_demo import fixture


def test_machine_candidate_is_pending_and_exactly_canonical():
    candidate = load_candidate()
    assert len(candidate["indicators"]) == 12
    assert len(candidate["E3"]) == 11
    assert validate_candidate(candidate)["scientifically_approved"] is False


@pytest.mark.parametrize("broken", ("approval", "codebook", "label", "order", "indicator", "mask", "extra", "missing_decisions"))
def test_candidate_rejects_schema_drift_and_approval_claims(broken):
    c = deepcopy(load_candidate())
    if broken == "approval": c["status"] = "Approved"
    if broken == "codebook": c["codebook_sha256"] = "0" * 64
    if broken == "label": c["E1"][0]["name"] = "target"
    if broken == "order": c["E3"].reverse()
    if broken == "indicator": c["indicators"][0]["id"] = "invented"
    if broken == "mask": c["E2"][0]["missing"] = "zero"
    if broken == "extra": c["unexpected"] = True
    if broken == "missing_decisions": c["pending"] = []
    with pytest.raises(InputContractError):
        validate_candidate(c)


def candidate_fixture():
    c = load_candidate()
    dataset = fixture()
    specification = replace(dataset.specification, conventional=tuple(FeatureColumn(x["name"], x["kind"]) for x in c["E1"]))
    rows = []
    for i, row in enumerate(dataset.observations):
        text = f"synthetic unique message {i}"
        rows.append(replace(row, conventional=(text, len(text), len(text.split()))))
    return replace(dataset, specification=specification, observations=tuple(rows)), c


def test_candidate_values_and_matched_metadata():
    dataset, c = candidate_fixture()
    assert validate_candidate_dataset(dataset, c)["matched_configurations"] == ["E1", "E2", "E3"]
    row = dataset.observations[0]
    for values in (("", 0, 0), (row.conventional[0], 1, 1), (None, 0, 0), (row.conventional[0], True, 4)):
        changed = replace(dataset, observations=(replace(row, conventional=values),) + dataset.observations[1:])
        with pytest.raises(InputContractError):
            validate_candidate_dataset(changed, c)
    with pytest.raises(InputContractError):
        validate_candidate_dataset(fixture(), c)
