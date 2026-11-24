
import json
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import (
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    balanced_accuracy_score,
    matthews_corrcoef,
    precision_recall_curve
)
from xgboost import XGBClassifier

SEED = 42

def require_authorization(workspace):
    path = Path(workspace) / (
        "docs/research/2026-11-17_scientific_validation/"
        "research-gate.json"
    )

    gate = json.loads(path.read_text(encoding="utf-8"))

    if not (
        gate.get("status") == "PASS"
        and gate.get("research_fitting_enabled") is True
        and gate.get("scientific_authorization_verified") is True
        and len(gate.get("checks", [])) == 10
        and all(
            c.get("status") == "PASS"
            for c in gate["checks"]
        )
    ):
        raise PermissionError("Scientific admission gate closed")

    return gate

def make_classifier(family, params):
    params = dict(params)

    if family == "logistic_regression":
        estimator = LogisticRegression(
            random_state=SEED,
            **params
        )

    elif family == "linear_svm":
        estimator = LinearSVC(
            random_state=SEED,
            **params
        )

    elif family == "random_forest":
        estimator = RandomForestClassifier(
            random_state=SEED,
            **params
        )

    elif family == "xgboost":
        estimator = XGBClassifier(
            random_state=SEED,
            **params
        )

    else:
        raise ValueError("Unapproved classifier family")

    steps = [
        ("imputer", SimpleImputer(
            strategy="constant",
            fill_value=-1,
            keep_empty_features=True
        ))
    ]

    if family in {"logistic_regression", "linear_svm"}:
        steps.append(("scaler", StandardScaler()))

    steps.append(("classifier", estimator))

    return Pipeline(steps)

def ranking_scores(model, X):
    if hasattr(model, "predict_proba"):
        assert list(model.classes_) == [0, 1]
        return model.predict_proba(X)[:, 1]

    assert list(model.classes_) == [0, 1]
    return model.decision_function(X)

def select_threshold(y, scores):
    p, r, thresholds = precision_recall_curve(y, scores)

    values = np.divide(
        2 * p[:-1] * r[:-1],
        p[:-1] + r[:-1],
        out=np.zeros_like(p[:-1]),
        where=(p[:-1] + r[:-1]) > 0
    )

    return float(thresholds[np.argmax(values)])

def metrics(y, scores, threshold):
    pred = (scores >= threshold).astype(int)

    return {
        "ap": float(average_precision_score(y, scores)),
        "precision": float(precision_score(
            y, pred, zero_division=0
        )),
        "recall": float(recall_score(
            y, pred, zero_division=0
        )),
        "f1": float(f1_score(
            y, pred, zero_division=0
        )),
        "roc_auc": float(roc_auc_score(y, scores)),
        "balanced_accuracy": float(
            balanced_accuracy_score(y, pred)
        ),
        "mcc": float(matthews_corrcoef(y, pred))
    }

def validate_development(frame, features, approved_features):
    required = {
        "observation_id", "group_id",
        "partition", "cv_fold", "target"
    }

    assert required.issubset(frame.columns)
    assert frame["observation_id"].is_unique
    assert frame["partition"].eq("development").all()
    assert set(frame["target"]) == {0, 1}
    assert set(frame["cv_fold"]) == {1, 2, 3, 4, 5}
    assert frame["group_id"].notna().all()
    assert frame.groupby("group_id")["cv_fold"].nunique().max() == 1

    assert list(features) == list(approved_features)
    assert len(features) == len(set(features))
    assert not required.intersection(features)

    forbidden = {
        "source_dataset", "source_position",
        "source_row_id", "source_label",
        "legacy_rank", "subject", "body",
        "sender", "receiver", "model_text"
    }

    assert not forbidden.intersection(features)
    assert set(features).issubset(frame.columns)

    X = frame[list(features)].apply(
        pd.to_numeric, errors="raise"
    )

    assert not np.isinf(X.to_numpy(dtype=float)).any()

    return X

def inner_predictions(X, y, groups, family, params, splits):
    scores = np.full(len(y), np.nan)

    cv = StratifiedGroupKFold(
        n_splits=splits,
        shuffle=True,
        random_state=SEED
    )

    for tr, va in cv.split(X, y, groups):
        assert not set(groups[tr]).intersection(groups[va])
        assert set(y[tr]) == {0, 1}
        assert set(y[va]) == {0, 1}

        model = make_classifier(family, params)
        model.fit(X.iloc[tr], y[tr])
        scores[va] = ranking_scores(model, X.iloc[va])

    assert np.isfinite(scores).all()

    return scores

def nested_development(
    frame, features, approved_features,
    family, parameter_grid, inner_splits,
    workspace
):
    require_authorization(workspace)

    X = validate_development(
        frame, features, approved_features
    )

    y = frame["target"].to_numpy(dtype=int)
    groups = frame["group_id"].to_numpy()
    folds = frame["cv_fold"].to_numpy(dtype=int)

    results = []
    predictions = []

    for fold in range(1, 6):
        tr = np.flatnonzero(folds != fold)
        va = np.flatnonzero(folds == fold)

        assert not set(groups[tr]).intersection(groups[va])

        assert set(y[tr]) == {0, 1}
        assert set(y[va]) == {0, 1}

        candidates = []

        for params in parameter_grid:
            scores = inner_predictions(
                X.iloc[tr], y[tr], groups[tr],
                family, params, inner_splits
            )

            ap = average_precision_score(y[tr], scores)

            candidates.append((ap, params, scores))

        _, best_params, inner_scores = max(
            candidates, key=lambda item: item[0]
        )

        threshold = select_threshold(y[tr], inner_scores)

        model = make_classifier(family, best_params)
        model.fit(X.iloc[tr], y[tr])

        scores = ranking_scores(model, X.iloc[va])

        result = metrics(y[va], scores, threshold)
        result.update({
            "fold": fold,
            "family": family,
            "parameters": best_params,
            "threshold": threshold
        })

        results.append(result)

        for idx, score in zip(va, scores):
            predictions.append({
                "observation_id": frame.iloc[idx]["observation_id"],
                "group_id": groups[idx],
                "fold": fold,
                "target": int(y[idx]),
                "score": float(score),
                "prediction": int(score >= threshold)
            })

    assert len(predictions) == len(frame)

    return results, predictions
