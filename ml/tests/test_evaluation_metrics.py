"""Analytic metric fixtures; all values are synthetic, never thesis performance."""
import math
import pytest
from ml.evaluation_metrics import binary_metrics, paired_group_bootstrap
from ml.experiment_inputs import InputContractError


def evaluate(y=(0, 1, 0, 1), scores=(.1, .4, .35, .8), **kwargs):
    return binary_metrics(y, scores, positive_label=1, threshold=.5, **kwargs)


def test_confusion_pr_roc_brier_and_reliability_against_hand_calculation():
    r = evaluate(probabilities=(.1, .4, .35, .8), calibration_edges=(0, .5, 1))
    assert r["confusion_matrix"] == [[2, 0], [1, 1]]
    assert r["precision"] == 1 and r["recall"] == .5
    assert r["f1"] == pytest.approx(2 / 3)
    assert r["balanced_accuracy"] == .75
    assert r["mcc"] == pytest.approx(1 / math.sqrt(3))
    assert r["average_precision"] == r["roc_auc"] == 1
    assert r["brier_score"] == pytest.approx(.133125)
    assert r["ece"] == pytest.approx(.0875)
    assert [b["count"] for b in r["reliability_bins"]] == [3, 1]
    assert r["probability_provenance"] == "caller_supplied_not_authenticated"


def test_noninterpolated_average_precision_known_rational_and_score_direction():
    r = evaluate((1, 0, 1), (.9, .8, .1))
    assert r["average_precision"] == pytest.approx(5 / 6)
    assert r["roc_auc"] == .5
    oriented = evaluate((0, 1), (.1, .9))
    reversed_result = evaluate((0, 1), (-.1, -.9))
    assert oriented["average_precision"] == 1
    assert reversed_result["average_precision"] == .5
    assert reversed_result["roc_auc"] == 0


def test_ties_are_grouped_and_order_invariant():
    r = evaluate(scores=(0, 0, 0, 0))
    assert r["average_precision"] == r["roc_auc"] == .5
    assert len(r["precision_recall_curve"]) == 1
    assert evaluate((1, 0, 1, 0), (0, 0, 0, 0))["average_precision"] == r["average_precision"]


@pytest.mark.parametrize("labels", [(0, 0), (1, 1)])
def test_one_class_undefined_statistics_are_explicit(labels):
    r = evaluate(labels, (.1, .2))
    assert r["roc_auc"] is None and r["balanced_accuracy"] is None and r["mcc"] is None
    assert r["precision"] is None
    assert r["average_precision"] == (None if labels[0] == 0 else 1)
    assert r["f1"] == (None if labels[0] == 0 else 0)


def test_probability_endpoints_empty_bins_and_edges_have_fixed_membership():
    r = evaluate((0, 1), (0, 1), probabilities=(0, 1), calibration_edges=(0, .25, .5, .75, 1))
    assert r["brier_score"] == r["ece"] == 0
    assert [b["count"] for b in r["reliability_bins"]] == [1, 0, 0, 1]
    assert r["reliability_bins"][1]["mean_probability"] is None


def test_raw_margins_remain_separate_from_probability_metrics():
    r = evaluate(scores=(-3, 2, -2, 4))
    assert r["brier_score"] is None and r["reliability_bins"] is None
    with pytest.raises(InputContractError, match="probabilities_outside"):
        evaluate(probabilities=(-3, 2, -2, 4), calibration_edges=(0, 1))


@pytest.mark.parametrize("labels,scores", [((), ()), (None, (1,)), ((True, 0), (1, 0)),
    ((2, 0), (1, 0)), ((0, 1), None), ((0, 1), (0,)), ((0, 1), (True, 1)),
    ((0, 1), (float("nan"), 1)), ((0, 1), (0, float("inf")))])
def test_invalid_labels_or_scores_fail(labels, scores):
    with pytest.raises(InputContractError):
        evaluate(labels, scores)


@pytest.mark.parametrize("positive", [0, True, None, "1"])
def test_positive_class_must_be_explicit_integer_one(positive):
    with pytest.raises(InputContractError):
        binary_metrics((0, 1), (0, 1), positive_label=positive, threshold=.5)


@pytest.mark.parametrize("edges", [None, (), (0,), (0, .5), (-1, 1), (0, 1, 1), (0, float("nan"), 1)])
def test_invalid_calibration_edges_fail(edges):
    with pytest.raises(InputContractError):
        evaluate(probabilities=(.1, .4, .35, .8), calibration_edges=edges)


def test_paired_bootstrap_uses_groups_with_identical_resampled_indices():
    result = paired_group_bootstrap((0, 1, 0, 1), (.8, .2, .3, .9), (.8, .2, .3, .9),
        ("a", "a", "b", "b"), positive_label=1, resamples=30, confidence=.95, seed=7)
    assert result["interval"] == [0, 0]
    assert result["resamples_valid"] == 30 and result["resamples_undefined"] == 0
    assert not result["selection_performed"]
    assert result == paired_group_bootstrap((0, 1, 0, 1), (.8, .2, .3, .9), (.8, .2, .3, .9),
        ("a", "a", "b", "b"), positive_label=1, resamples=30, confidence=.95, seed=7)


def test_undefined_bootstrap_draws_are_reported_not_replaced():
    result = paired_group_bootstrap((0, 1), (.1, .9), (.9, .1), ("a", "b"),
        positive_label=1, resamples=100, confidence=.95, seed=42)
    assert 0 < result["resamples_undefined"] < 100
    assert result["resamples_valid"] + result["resamples_undefined"] == 100
    assert result["interval"] == [.5, .5]  # AP 1 minus reversed-order AP .5.


@pytest.mark.parametrize("change", [{"resamples": 0}, {"resamples": True}, {"confidence": 1},
    {"confidence": float("nan")}, {"seed": True}])
def test_invalid_bootstrap_configuration_is_rejected(change):
    settings = dict(positive_label=1, resamples=20, confidence=.95, seed=3)
    settings.update(change)
    with pytest.raises(InputContractError):
        paired_group_bootstrap((0, 1), (.1, .9), (.2, .8), ("a", "b"), **settings)


def test_bootstrap_replicates_whole_unequal_clusters_identically_for_both_candidates(monkeypatch):
    import ml.evaluation_metrics as metrics
    class FixedRandom:
        def __init__(self, seed): pass
        def choice(self, names): return "b"
    original = metrics._ranking
    observed = []
    def ranking(y, scores):
        observed.append((y, scores))
        return original(y, scores)
    monkeypatch.setattr(metrics.random, "Random", FixedRandom)
    monkeypatch.setattr(metrics, "_ranking", ranking)
    paired_group_bootstrap((0, 1, 0, 1, 1), (0, 1, .2, .3, .4), (1, 0, .8, .7, .6),
        ("a", "a", "b", "b", "b"), positive_label=1, resamples=1, confidence=.95, seed=7)
    assert observed == [((0, 1, 1, 0, 1, 1), (.2, .3, .4, .2, .3, .4)),
                        ((0, 1, 1, 0, 1, 1), (.8, .7, .6, .8, .7, .6))]

