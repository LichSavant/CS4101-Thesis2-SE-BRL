"""Nested genuine synthetic pipeline boundaries and reproducibility."""
from dataclasses import replace
import json

import pytest

from ml.experiment_engine import (Candidate, SigmoidSpecification, ThresholdSpecification,
    NestedSpecification, FittedSigmoid, choose_training_f1_threshold, run_synthetic_nested_cv)
from ml.development_runner import write_synthetic_bundle, verify_synthetic_bundle
from ml.experiment_inputs import InputContractError
from ml.synthetic_demo import fixture
from ml.tests.test_classifier_adapters import genuine, model, preprocessing, FAMILIES


def spec(family="logistic_regression", configs=("E3",), threshold="fixed", two=False):
    candidates = (Candidate("first", model(family), preprocessing()),)
    if two:
        candidates += (Candidate("second", model(family, C=.1), preprocessing()),)
    return NestedSpecification(candidates, configs, SigmoidSpecification(model(), "identity", 1e-6),
        ThresholdSpecification(threshold, .5 if threshold == "fixed" else None), (0., .5, 1.), "synthetic:nested-test")


@genuine
@pytest.mark.parametrize("family", FAMILIES)
def test_all_genuine_families_nested_oof_and_safe_sigmoid_state(family):
    result, pipelines = run_synthetic_nested_cv(fixture(), spec(family))
    assert len(pipelines) == 5 and len(result["oof_predictions"]) == 10
    assert result["base_fits"] == 105 and result["calibration_fits"] == 5
    assert result["research_execution"] == "BLOCKED"
    assert all(0 <= r["probability"] <= 1 for r in result["oof_predictions"])
    for trace in result["traces"]:
        outer_valid = set(trace["outer_validation_ids"])
        outer_train = set(trace["outer_train_ids"])
        assert not outer_valid & outer_train
        for event in trace["events"]:
            if event["stage"] == "inner_search":
                assert set(event["population_ids"]) <= outer_train
                for candidate in event["candidates"]:
                    for fold in candidate["folds"]:
                        assert not set(fold["train_ids"]) & set(fold["validation_ids"])
                        assert set(fold["train_ids"] + fold["validation_ids"]) <= outer_train
            else:
                assert set(event["training_ids"]) <= outer_train
    for _, _, _, sigmoid, _ in pipelines:
        restored = FittedSigmoid.from_state(json.loads(json.dumps(sigmoid.state())))
        assert restored.probabilities((0., .1, .9, 1.)) == sigmoid.probabilities((0., .1, .9, 1.))


@genuine
def test_outer_validation_labels_cannot_change_that_folds_search_calibration_threshold_or_scores():
    dataset = fixture()
    request = spec(threshold="training_crossfit_f1", two=True)
    before, _ = run_synthetic_nested_cv(dataset, request)
    changed = replace(dataset, observations=tuple(replace(r, target=1-r.target) if r.fold == 1 else r
                                                  for r in dataset.observations))
    after, _ = run_synthetic_nested_cv(changed, request)
    a, b = before["fold_reports"][0], after["fold_reports"][0]
    assert a["selected_candidate"] == b["selected_candidate"]
    assert a["pipeline"] == b["pipeline"]
    assert a["calibration"] == b["calibration"]
    assert a["threshold"] == b["threshold"]
    assert before["traces"][0] == after["traces"][0]
    assert [r["score"] for r in before["oof_predictions"] if r["fold"] == 1] == [
        r["score"] for r in after["oof_predictions"] if r["fold"] == 1]
    assert before["base_fits"] == 625 and before["calibration_fits"] == 25


@genuine
def test_matched_views_u1_and_bundle(tmp_path):
    result, _ = run_synthetic_nested_cv(fixture(), spec(configs=("E1", "E2", "E3")))
    controls = [{(r["observation_id"], r["group_id"], r["fold"], r["target"])
                 for r in result["oof_predictions"] if r["configuration"] == c} for c in ("E1", "E2", "E3")]
    assert controls[0] == controls[1] == controls[2]
    directory = tmp_path / "run"
    write_synthetic_bundle(directory, result, code_reference="synthetic:test", code_hashes={"fixture": "a" * 64})
    assert verify_synthetic_bundle(directory)["result_category"] == "SYNTHETIC RESULT"
    with pytest.raises(InputContractError):
        write_synthetic_bundle(directory, result, code_reference="synthetic:test", code_hashes={"fixture": "a" * 64})
    u1, _ = run_synthetic_nested_cv(fixture("UCI"), spec(configs=("U1",)))
    assert {r["configuration"] for r in u1["oof_predictions"]} == {"U1"}


@genuine
def test_search_tie_order_declared_and_fresh_preprocessing():
    request = spec()
    first = request.candidates[0]
    request = replace(request, candidates=(first, replace(first, identifier="identical-second")))
    result, fitted = run_synthetic_nested_cv(fixture(), request)
    assert {r["selected_candidate"] for r in result["fold_reports"]} == {"first"}
    assert len({id(p.pipeline.named_steps["preprocess"]) for _, _, p, _, _ in fitted}) == 5


def test_invalid_metadata_and_policies_fail_before_fit():
    def forbidden(*args):
        pytest.fail("fit must not be reached")
    dataset = fixture()
    for bad in (replace(dataset, observations=dataset.observations + dataset.observations[:1]),
                replace(dataset, observations=tuple(replace(r, fold=0) if i == 0 else r for i, r in enumerate(dataset.observations))),
                replace(dataset, observations=tuple(replace(r, target=0) if r.fold == 1 else r for r in dataset.observations))):
        with pytest.raises(InputContractError):
            run_synthetic_nested_cv(bad, spec(), classifier_type=forbidden)
    for change in (dict(configurations=("test",)), dict(omitted_features=("source_dataset",))):
        with pytest.raises(InputContractError):
            run_synthetic_nested_cv(dataset, replace(spec(), **change), classifier_type=forbidden)
    for change in (dict(protocol_reference="Approved"), dict(calibration_edges=(0., 1., .5)), dict(candidates=())):
        with pytest.raises(InputContractError):
            replace(spec(), **change)
    for mode, value in (("fixed", None), ("test_f1", None), ("training_crossfit_f1", .5), ("fixed", True)):
        with pytest.raises(InputContractError):
            ThresholdSpecification(mode, value)
    with pytest.raises(InputContractError):
        replace(spec("linear_svm"), calibration=SigmoidSpecification(model(), "logit_probability", 1e-6))


def test_threshold_ties_and_invalid_calibration_state():
    assert choose_training_f1_threshold((0, 1, 0, 1), (.1, .8, .3, .9)) == .8
    assert choose_training_f1_threshold((0, 1), (.5, .5)) == .5
    for y, p in (((0, 0), (.2, .3)), ((0, 1), (.1,)), ((0, 1), (-1., 1.))):
        with pytest.raises(InputContractError):
            choose_training_f1_threshold(y, p)
    with pytest.raises(InputContractError):
        FittedSigmoid.from_state({})


@genuine
def test_candidate_failure_aborts_without_a_result_or_output(tmp_path):
    from ml.classifier_adapters import FoldClassifier
    class Failing(FoldClassifier):
        def fit(self, *args, **kwargs):
            raise InputContractError("synthetic_candidate_failure")
    with pytest.raises(InputContractError, match="candidate_failure"):
        run_synthetic_nested_cv(fixture(), spec(), classifier_type=Failing)
    assert list(tmp_path.iterdir()) == []
