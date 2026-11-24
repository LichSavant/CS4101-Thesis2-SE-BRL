
import numpy as np
import pandas as pd

from sklearn.model_selection import (
    StratifiedGroupKFold,
    ParameterGrid
)

from sklearn.metrics import average_precision_score

from development_harness import make_classifier

from nested_calibration import (
    raw_scores,
    fit_sigmoid_calibrator,
    calibrated_probabilities,
    select_f1_threshold,
    evaluate_outer_fold,
    fold_local_positive_weight
)


def checked_splits(X, y, groups, seed, n_splits=3):
    cv = StratifiedGroupKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=seed
    )

    splits = list(cv.split(X, y, groups))

    for train, valid in splits:
        if set(groups[train]) & set(groups[valid]):
            raise ValueError("Inner group leakage")

        if set(y[train]) != {0, 1}:
            raise ValueError("Training class missing")

        if set(y[valid]) != {0, 1}:
            raise ValueError("Validation class missing")

    return splits


def train_model(family, params, X, y):
    params = dict(params)

    if family == "xgboost":
        params["scale_pos_weight"] = (
            fold_local_positive_weight(y)
        )

    model = make_classifier(family, params)
    model.fit(X, y)

    return model


def tune_model(family, grid, X, y, groups, seed):
    splits = checked_splits(X, y, groups, seed)

    best_params = None
    best_ap = -np.inf
    history = []

    for params in ParameterGrid(grid):
        scores = []

        for train, valid in splits:
            model = train_model(
                family, params, X[train], y[train]
            )

            ranking = raw_scores(model, X[valid])

            if not np.isfinite(ranking).all():
                raise ValueError("Invalid ranking scores")

            scores.append(
                average_precision_score(
                    y[valid], ranking
                )
            )

        mean_ap = float(np.mean(scores))

        history.append({
            "parameters": dict(params),
            "mean_inner_ap": mean_ap,
            "inner_fold_ap": [
                float(value) for value in scores
            ]
        })

        if mean_ap > best_ap:
            best_ap = mean_ap
            best_params = dict(params)

    if best_params is None:
        raise RuntimeError("No valid configuration")

    return best_params, history


def nested_calibration_scores(
    family, grid, X, y, groups, seed
):
    scores = np.full(len(y), np.nan)

    for train, valid in checked_splits(
        X, y, groups, seed
    ):
        params, _ = tune_model(
            family,
            grid,
            X[train],
            y[train],
            groups[train],
            seed
        )

        model = train_model(
            family, params, X[train], y[train]
        )

        scores[valid] = raw_scores(
            model, X[valid]
        )

    if not np.isfinite(scores).all():
        raise ValueError("Incomplete calibration scores")

    return scores


def evaluate_configuration(
    frame,
    features,
    family,
    grid,
    authorization_verified=False,
    seed=42
):
    if authorization_verified is not True:
        raise PermissionError(
            "Verified research-fit authorization required"
        )

    if not frame["partition"].eq("development").all():
        raise ValueError("Non-development record detected")

    if not frame["observation_id"].is_unique:
        raise ValueError("Duplicate observations")

    if len(features) != len(set(features)):
        raise ValueError("Duplicate predictors")

    if not set(features).issubset(frame.columns):
        raise ValueError("Missing predictors")

    forbidden = {
        "observation_id", "source_dataset",
        "target", "group_id", "partition",
        "cv_fold", "source_row_position",
        "source_native_label"
    }

    if forbidden.intersection(features):
        raise ValueError("Forbidden predictor")

    if frame.groupby("group_id")["cv_fold"].nunique().max() != 1:
        raise ValueError("Outer group leakage")

    if set(frame["cv_fold"]) != {1, 2, 3, 4, 5}:
        raise ValueError("Unexpected outer folds")

    X = frame[features].to_numpy(dtype=float)
    y = frame["target"].to_numpy(dtype=int)
    groups = frame["group_id"].to_numpy()
    folds = frame["cv_fold"].to_numpy()

    if np.isinf(X).any():
        raise ValueError("Infinite feature value")

    results = []
    predictions = []
    search_history = []

    for fold in [1, 2, 3, 4, 5]:
        train = np.flatnonzero(folds != fold)
        test = np.flatnonzero(folds == fold)

        if set(groups[train]) & set(groups[test]):
            raise ValueError("Outer leakage detected")

        if set(y[train]) != {0, 1} or set(y[test]) != {0, 1}:
            raise ValueError("Outer class missing")

        params, history = tune_model(
            family,
            grid,
            X[train],
            y[train],
            groups[train],
            seed
        )

        calibration_scores = nested_calibration_scores(
            family,
            grid,
            X[train],
            y[train],
            groups[train],
            seed
        )

        calibrator = fit_sigmoid_calibrator(
            calibration_scores,
            y[train]
        )

        inner_probabilities = calibrated_probabilities(
            calibrator,
            calibration_scores
        )

        threshold = select_f1_threshold(
            y[train],
            inner_probabilities
        )["threshold"]

        model = train_model(
            family,
            params,
            X[train],
            y[train]
        )

        probabilities = calibrated_probabilities(
            calibrator,
            raw_scores(model, X[test])
        )

        metrics = evaluate_outer_fold(
            y[test],
            probabilities,
            threshold
        )

        results.append({
            "fold": fold,
            "classifier": family,
            "parameters": params,
            **metrics
        })

        search_history.append({
            "outer_fold": fold,
            "history": history
        })

        for index, probability in zip(test, probabilities):
            predictions.append({
                "observation_id": frame.iloc[index]["observation_id"],
                "group_id": groups[index],
                "cv_fold": fold,
                "target": int(y[index]),
                "probability": float(probability),
                "prediction": int(probability >= threshold)
            })

        print(
            family,
            "| Fold", fold,
            "| AP:", round(metrics["average_precision"], 4),
            "| F1:", round(metrics["f1"], 4),
            flush=True
        )

    prediction_frame = pd.DataFrame(predictions)

    if len(prediction_frame) != len(frame):
        raise ValueError("Incomplete outer predictions")

    if not prediction_frame["observation_id"].is_unique:
        raise ValueError("Duplicate outer predictions")

    if set(prediction_frame["observation_id"]) != set(frame["observation_id"]):
        raise ValueError("Prediction identity mismatch")

    return {
        "fold_metrics": results,
        "predictions": prediction_frame,
        "search_history": search_history,
        "mean_fold_ap": float(np.mean([
            item["average_precision"] for item in results
        ])),
        "mean_fold_f1": float(np.mean([
            item["f1"] for item in results
        ]))
    }
