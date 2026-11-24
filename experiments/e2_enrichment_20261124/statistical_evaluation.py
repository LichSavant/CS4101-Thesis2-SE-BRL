
import numpy as np
import pandas as pd

from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    confusion_matrix,
    matthews_corrcoef
)

def validate_predictions(frame):
    required = {
        "observation_id", "group_id", "fold",
        "target", "score", "prediction"
    }

    if not required.issubset(frame.columns):
        raise ValueError("Missing prediction columns")

    if not frame["observation_id"].is_unique:
        raise ValueError("Duplicate observations")

    if frame["group_id"].isna().any():
        raise ValueError("Missing groups")

    if set(frame["target"]) != {0, 1}:
        raise ValueError("Both classes required")

    if not set(frame["prediction"]).issubset({0, 1}):
        raise ValueError("Invalid predictions")

    if not np.isfinite(frame["score"]).all():
        raise ValueError("Invalid scores")

    if frame.groupby("group_id")["fold"].nunique().max() != 1:
        raise ValueError("Group crosses folds")

def pooled_metrics(frame, comparable_scores=False):
    validate_predictions(frame)

    y = frame["target"]
    pred = frame["prediction"]

    tn, fp, fn, tp = confusion_matrix(
        y, pred, labels=[0, 1]
    ).ravel()

    return {
        "n": len(frame),
        "ap": (
            float(average_precision_score(y, frame["score"]))
            if comparable_scores else None
        ),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "precision": float(precision_score(
            y, pred, zero_division=0
        )),
        "recall": float(recall_score(
            y, pred, zero_division=0
        )),
        "mcc": float(matthews_corrcoef(y, pred)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp)
    }

def paired_bootstrap(
    baseline, candidate, repeats=2000,
    seed=42, comparable_scores=False
):
    validate_predictions(baseline)
    validate_predictions(candidate)

    a = baseline.sort_values("observation_id").reset_index(drop=True)
    b = candidate.sort_values("observation_id").reset_index(drop=True)

    keys = ["observation_id", "group_id", "fold", "target"]

    if not a[keys].equals(b[keys]):
        raise ValueError("Unmatched experimental populations")

    groups = list(a.groupby("group_id").indices.values())
    rng = np.random.default_rng(seed)

    differences = {"f1": []}

    if comparable_scores:
        differences["ap"] = []

    for _ in range(repeats):
        sample = rng.integers(0, len(groups), len(groups))
        idx = np.concatenate([groups[i] for i in sample])

        y = a["target"].to_numpy()[idx]

        if len(np.unique(y)) != 2:
            continue

        pa = a["prediction"].to_numpy()[idx]
        pb = b["prediction"].to_numpy()[idx]

        differences["f1"].append(
            f1_score(y, pb, zero_division=0)
            - f1_score(y, pa, zero_division=0)
        )

        if comparable_scores:
            sa = a["score"].to_numpy()[idx]
            sb = b["score"].to_numpy()[idx]

            differences["ap"].append(
                average_precision_score(y, sb)
                - average_precision_score(y, sa)
            )

    results = {}

    for metric, values in differences.items():
        if not values:
            raise ValueError("No valid bootstrap samples")

        results[metric] = {
            "mean_difference": float(np.mean(values)),
            "ci95_lower": float(np.percentile(values, 2.5)),
            "ci95_upper": float(np.percentile(values, 97.5)),
            "valid_replicates": len(values),
            "requested_replicates": repeats
        }

    return results
