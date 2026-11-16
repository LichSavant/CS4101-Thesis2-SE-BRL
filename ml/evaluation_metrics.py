"""Binary evaluation primitives, not a fitted model or scientific protocol freeze.

Positive label is explicitly 1; larger scores mean phishing. Undefined statistics
are None. PR-AUC is non-interpolated average precision with ties grouped; it is
not trapezoidal area under the PR curve. Calibration edges and thresholds are
caller-supplied. No threshold selection or calibration fitting occurs.
"""
from collections import defaultdict
import math
import random

from ml.experiment_inputs import InputContractError


def _numbers(values, count=None, *, probability=False):
    try:
        values = tuple(values)
    except TypeError:
        raise InputContractError("finite_aligned_scores_required") from None
    try:
        valid = bool(values) and (count is None or len(values) == count) and all(
            type(v) in (int, float) and math.isfinite(v) for v in values)
    except OverflowError:
        valid = False
    if not valid:
        raise InputContractError("finite_aligned_scores_required")
    if probability and any(not 0 <= v <= 1 for v in values):
        raise InputContractError("probabilities_outside_unit_interval")
    return values


def _labels(values, positive_label):
    try:
        labels = tuple(values)
    except TypeError:
        raise InputContractError("binary_integer_labels_required") from None
    if type(positive_label) is not int or positive_label != 1:
        raise InputContractError("explicit_positive_label_one_required")
    if not labels or any(type(v) is not int or v not in (0, 1) for v in labels):
        raise InputContractError("binary_integer_labels_required")
    return labels


def _ranking(labels, scores):
    groups = defaultdict(lambda: [0, 0])
    for y, s in zip(labels, scores):
        groups[s][y] += 1
    positive, negative = sum(labels), len(labels) - sum(labels)
    tp = fp = 0
    ap = 0.0
    curve = []
    for score in sorted(groups, reverse=True):
        neg, pos = groups[score]
        tp += pos
        fp += neg
        precision = tp / (tp + fp)
        recall = tp / positive if positive else None
        if positive:
            ap += pos / positive * precision
        curve.append({"threshold": score, "precision": precision, "recall": recall})
    below_negative = 0
    concordant = 0.0
    for score in sorted(groups):
        neg, pos = groups[score]
        concordant += pos * (below_negative + neg / 2)
        below_negative += neg
    return (ap if positive else None,
            concordant / (positive * negative) if positive and negative else None,
            curve)


def binary_metrics(labels, scores, *, positive_label, threshold,
                   probabilities=None, calibration_edges=None):
    """Threshold applies to scores in their supplied units; higher means phishing.

    probabilities, when supplied, are assessed only for calibration statistics;
    their calibrated provenance is NOT inferred. Empty reliability bins remain
    explicit. Bins are [left,right), with 1 included in the last bin.
    """
    labels = _labels(labels, positive_label)
    scores = _numbers(scores, len(labels))
    _numbers((threshold,))
    tp = sum(y == 1 and s >= threshold for y, s in zip(labels, scores))
    fp = sum(y == 0 and s >= threshold for y, s in zip(labels, scores))
    fn = sum(labels) - tp
    tn = len(labels) - sum(labels) - fp
    ratio = lambda n, d: n / d if d else None
    precision, recall = ratio(tp, tp + fp), ratio(tp, tp + fn)
    specificity = ratio(tn, tn + fp)
    ap, roc, curve = _ranking(labels, scores)
    denominator = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    result = {
        "positive_label": 1, "score_orientation": "higher_is_phishing",
        "threshold": threshold, "threshold_scale": "supplied_scores",
        "observations": len(labels), "confusion_matrix": [[tn, fp], [fn, tp]],
        "precision": precision, "recall": recall, "f1": ratio(2 * tp, 2 * tp + fp + fn),
        "specificity": specificity,
        "balanced_accuracy": (recall + specificity) / 2 if recall is not None and specificity is not None else None,
        "mcc": (tp * tn - fp * fn) / math.sqrt(denominator) if denominator else None,
        "average_precision": ap, "pr_auc_definition": "non_interpolated_average_precision",
        "roc_auc": roc, "precision_recall_curve": curve,
        "brier_score": None, "ece": None, "reliability_bins": None,
        "probability_provenance": "not_supplied",
    }
    if probabilities is None:
        if calibration_edges is not None:
            raise InputContractError("calibration_edges_without_probabilities")
        return result
    probabilities = _numbers(probabilities, len(labels), probability=True)
    if calibration_edges is None:
        raise InputContractError("explicit_calibration_edges_required")
    edges = _numbers(calibration_edges)
    if len(edges) < 2 or edges[0] != 0 or edges[-1] != 1 or any(a >= b for a, b in zip(edges, edges[1:])):
        raise InputContractError("invalid_calibration_edges")
    bins = []
    ece = 0.0
    for i, (lo, hi) in enumerate(zip(edges, edges[1:])):
        indices = [j for j, p in enumerate(probabilities) if lo <= p < hi or (i == len(edges) - 2 and p == 1)]
        mean_probability = sum(probabilities[j] for j in indices) / len(indices) if indices else None
        positive_rate = sum(labels[j] for j in indices) / len(indices) if indices else None
        if indices:
            ece += len(indices) / len(labels) * abs(mean_probability - positive_rate)
        bins.append({"left": lo, "right": hi, "count": len(indices),
                     "mean_probability": mean_probability, "positive_rate": positive_rate})
    result.update(brier_score=sum((p - y) ** 2 for p, y in zip(probabilities, labels)) / len(labels),
                  ece=ece, reliability_bins=bins, probability_provenance="caller_supplied_not_authenticated")
    return result


def _quantile(values, probability):
    values = sorted(values)
    position = (len(values) - 1) * probability
    lo, hi = math.floor(position), math.ceil(position)
    return values[lo] + (values[hi] - values[lo]) * (position - lo)


def paired_group_bootstrap(labels, left_scores, right_scores, group_ids, *,
                           positive_label, resamples, confidence, seed):
    """Paired cluster bootstrap of AP(left)-AP(right), never model selection.

    Resample whole groups with replacement, applying identical multiplicities to
    both candidates. One-class draws are undefined and counted, not silently
    replaced. Caller freezes settings/estimand; tests may use smaller synthetic
    settings than the proposal's 2,000 / 95% research procedure.
    """
    labels = _labels(labels, positive_label)
    left, right = _numbers(left_scores, len(labels)), _numbers(right_scores, len(labels))
    groups = tuple(group_ids)
    if (len(groups) != len(labels)
            or any(type(g) is not str or not g.strip() for g in groups)):
        raise InputContractError("aligned_group_ids_required")
    if (type(resamples) is not int or resamples < 1 or type(seed) is not int
            or type(confidence) not in (int, float) or not 0 < confidence < 1):
        raise InputContractError("explicit_bootstrap_settings_required")
    indexed = defaultdict(list)
    for i, group in enumerate(groups):
        indexed[group].append(i)
    names = sorted(indexed)
    rng = random.Random(seed)
    differences = []
    for _ in range(resamples):
        positions = [i for _ in names for i in indexed[rng.choice(names)]]
        y = tuple(labels[i] for i in positions)
        if set(y) != {0, 1}:
            continue
        a = _ranking(y, tuple(left[i] for i in positions))[0]
        b = _ranking(y, tuple(right[i] for i in positions))[0]
        differences.append(a - b)
    tail = (1 - confidence) / 2
    return {"statistic": "average_precision_left_minus_right", "sampling_unit": "supplied_group",
            "resamples_requested": resamples, "resamples_valid": len(differences),
            "resamples_undefined": resamples - len(differences), "confidence": confidence, "seed": seed,
            "interval_method": "percentile_linear_interpolation",
            "interval": [_quantile(differences, tail), _quantile(differences, 1 - tail)] if len(differences) >= 2 else None,
            "selection_performed": False}

