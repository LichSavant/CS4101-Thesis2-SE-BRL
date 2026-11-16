"""Pure generated evidence fixtures for the hierarchy; no research selection."""
from copy import deepcopy
from dataclasses import replace

import pytest

from ml.model_selection import SelectionPolicy, select_synthetic_family
from ml.evaluation_metrics import binary_metrics
from ml.experiment_inputs import InputContractError


def policy(**changes):
    values = dict(families=("logistic_regression", "random_forest"), configuration="E3", delta_pr=.01, resamples=40, confidence=.95, seed=17,
        hard_limits=dict(minimum_recall=None, minimum_precision=None, maximum_p95_ms=None, maximum_memory_bytes=None),
        memory_evidence="measured_required",
        calibration_order=("brier_score", "ece"), efficiency_order=("p95_batch_ms", "throughput_artifacts_per_second",
        "measured_memory_bytes_max", "serialized_model_bytes"), protocol_reference="synthetic:selection-fixture")
    values.update(changes)
    return SelectionPolicy(**values)


def evidence(family, *, quality="good", speed=2., simplicity=1):
    y = (0, 1) * 5
    p = {"good": (.1, .9) * 5, "weak": (.9, .1) * 5, "uncalibrated": (.45, .55) * 5}[quality]
    rows = [dict(configuration="E3", observation_id=f"synthetic-{i}", group_id=f"pair-{i//2}", fold=i//2+1,
                 target=target, score=score, probability=score) for i, (target, score) in enumerate(zip(y, p))]
    return dict(result=dict(result_category="SYNTHETIC RESULT", research_execution="BLOCKED", input_fingerprint="synthetic:shared",
        request=dict(family=family, protocol_reference="synthetic:fixture", calibration_edges=(0., .5, 1.),
            outer_ranking_statistic="pooled_nested_sigmoid_average_precision", threshold=dict(mode="fixed", value=.5)),
        oof_predictions=rows, pooled_metrics={"E3": binary_metrics(y, p, positive_label=1, threshold=.5,
            probabilities=p, calibration_edges=(0., .5, 1.))}),
        benchmark=dict(result_category="SYNTHETIC RESULT", comparison_fingerprint="synthetic:timing-scope",
            p95_batch_ms=speed, throughput_artifacts_per_second=100./speed,
            measured_memory_bytes_max=1000, serialized_model_bytes=500), simplicity_rank=simplicity)


def test_fast_materially_weaker_model_cannot_win():
    candidates = {"logistic_regression": evidence("logistic_regression"),
                  "random_forest": evidence("random_forest", quality="weak", speed=.01)}
    selected = select_synthetic_family(candidates, policy())
    assert selected["selected"] == "logistic_regression"
    assert selected["comparisons"]["random_forest"]["disposition"] == "materially_weaker"


def test_calibration_precedes_efficiency_and_final_lr_preference_is_last():
    candidates = {"logistic_regression": evidence("logistic_regression", quality="uncalibrated", speed=.01),
                  "random_forest": evidence("random_forest")}
    assert select_synthetic_family(candidates, policy())["selected"] == "random_forest"
    candidates["logistic_regression"] = evidence("logistic_regression")
    outcome = select_synthetic_family(candidates, policy())
    assert outcome["selected"] == "logistic_regression"
    assert outcome["tie_stages"][-1]["criterion"] == "final_logistic_regression_preference"
    candidates["random_forest"] = evidence("random_forest", speed=.01)
    assert select_synthetic_family(candidates, policy())["selected"] == "random_forest"


def test_real_limit_is_enforced_and_unknown_disposition_rejected():
    candidates = {"logistic_regression": evidence("logistic_regression")}
    hard = dict(policy().hard_limits, maximum_p95_ms=1.)
    outcome = select_synthetic_family(candidates, policy(families=("logistic_regression",), hard_limits=hard))
    assert outcome["status"] == "no_eligible_candidate" and outcome["selected"] is None
    for limits in ({}, dict(hard, maximum_memory_bytes="unknown")):
        with pytest.raises(InputContractError):
            policy(hard_limits=limits)
    with pytest.raises(InputContractError):
        policy(delta_pr=None)


def test_mismatched_population_or_benchmark_and_missing_measurement_fail_closed():
    a, b = evidence("logistic_regression"), evidence("random_forest")
    for change in ("fold", "benchmark", "memory", "target"):
        broken = deepcopy(b)
        if change == "fold": broken["result"]["oof_predictions"][0]["fold"] = 2
        if change == "benchmark": broken["benchmark"]["comparison_fingerprint"] = "different"
        if change == "memory": broken["benchmark"]["measured_memory_bytes_max"] = None
        if change == "target": broken["result"]["oof_predictions"][0]["target"] = 1
        with pytest.raises(InputContractError):
            select_synthetic_family({"logistic_regression": a, "random_forest": broken}, policy())


def test_inconclusive_equivalence_and_non_lr_final_tie_do_not_choose_arbitrarily():
    a, b = evidence("logistic_regression"), evidence("random_forest")
    # Same ranking except one discordant positive: paired interval is broad.
    b["result"]["oof_predictions"][1]["score"] = .05
    b["result"]["oof_predictions"][1]["probability"] = .05
    rows = b["result"]["oof_predictions"]
    b["result"]["pooled_metrics"]["E3"] = binary_metrics(tuple(r["target"] for r in rows), tuple(r["score"] for r in rows),
        positive_label=1, threshold=.5, probabilities=tuple(r["probability"] for r in rows), calibration_edges=(0., .5, 1.))
    assert select_synthetic_family({"logistic_regression": a, "random_forest": b}, policy())["status"] == "inconclusive_uncertainty"
    outcome = select_synthetic_family({"linear_svm": evidence("linear_svm"), "random_forest": evidence("random_forest")},
                                      policy(families=("linear_svm", "random_forest")))
    assert outcome["status"] == "unresolved_final_tie" and outcome["selected"] is None


def test_missing_family_folds_group_crossings_and_forged_summary_are_rejected():
    a, b = evidence("logistic_regression"), evidence("random_forest")
    with pytest.raises(InputContractError):
        select_synthetic_family({"logistic_regression": a}, policy())
    for field in ("summary", "operating", "folds", "groups"):
        broken = deepcopy(b)
        if field == "summary": broken["result"]["pooled_metrics"]["E3"]["average_precision"] = .5
        if field == "operating": broken["result"]["pooled_metrics"]["E3"]["recall"] = .1
        if field == "folds": broken["result"]["oof_predictions"] = broken["result"]["oof_predictions"][:-2]
        if field == "groups": broken["result"]["oof_predictions"][2]["group_id"] = "pair-0"
        with pytest.raises(InputContractError):
            select_synthetic_family({"logistic_regression": a, "random_forest": broken}, policy())


def test_unavailable_memory_needs_explicit_policy_and_never_bypasses_a_hard_limit():
    candidates = {"logistic_regression": evidence("logistic_regression"), "random_forest": evidence("random_forest")}
    candidates["random_forest"]["benchmark"]["measured_memory_bytes_max"] = None
    with pytest.raises(InputContractError, match="memory_measurement"):
        select_synthetic_family(candidates, policy())
    choice = select_synthetic_family(candidates, policy(memory_evidence="unavailable_allowed_without_limit"))
    assert choice["selected"] == "logistic_regression"
    assert any(s["criterion"] == "measured_memory_bytes_max" and "disposition" in s for s in choice["tie_stages"])
    with pytest.raises(InputContractError, match="memory_measurement"):
        select_synthetic_family(candidates, policy(memory_evidence="unavailable_allowed_without_limit",
            hard_limits=dict(policy().hard_limits, maximum_memory_bytes=2000)))
    assert candidates["random_forest"]["benchmark"]["measured_memory_bytes_max"] is None
