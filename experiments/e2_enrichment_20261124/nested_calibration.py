
import numpy as np

from sklearn.metrics import (
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    matthews_corrcoef,
    brier_score_loss,
    confusion_matrix,
    precision_recall_curve,
    balanced_accuracy_score
)

from sklearn.linear_model import LogisticRegression


def raw_scores(estimator, X):
    if hasattr(estimator, "decision_function"):
        return np.asarray(
            estimator.decision_function(X)
        ).reshape(-1)

    if hasattr(estimator, "predict_proba"):
        p = np.asarray(
            estimator.predict_proba(X)[:, 1]
        )
        p = np.clip(p, 1e-7, 1 - 1e-7)
        return np.log(p / (1 - p))

    raise TypeError("Estimator has no ranking score")


def fit_sigmoid_calibrator(scores, targets):
    scores = np.asarray(scores, dtype=float)
    targets = np.asarray(targets, dtype=int)

    if len(scores) != len(targets):
        raise ValueError("Calibration alignment mismatch")

    if not np.isfinite(scores).all():
        raise ValueError("Invalid calibration scores")

    if set(np.unique(targets)) != {0, 1}:
        raise ValueError("Calibration requires both classes")

    calibrator = LogisticRegression(
        C=1.0,
        solver="lbfgs",
        max_iter=2000,
        random_state=42
    )

    calibrator.fit(
        scores.reshape(-1, 1),
        targets
    )

    return calibrator


def calibrated_probabilities(calibrator, scores):
    scores = np.asarray(scores, dtype=float)

    if not np.isfinite(scores).all():
        raise ValueError("Invalid inference scores")

    return calibrator.predict_proba(
        scores.reshape(-1, 1)
    )[:, 1]


def select_f1_threshold(targets, probabilities):
    targets = np.asarray(targets, dtype=int)
    probabilities = np.asarray(probabilities, dtype=float)

    if len(targets) != len(probabilities):
        raise ValueError("Threshold alignment mismatch")

    if set(np.unique(targets)) != {0, 1}:
        raise ValueError("Threshold selection requires both classes")

    if not np.isfinite(probabilities).all():
        raise ValueError("Invalid probabilities")

    if np.any(probabilities < 0) or np.any(probabilities > 1):
        raise ValueError("Probability outside valid range")

    precision, recall, thresholds = precision_recall_curve(
        targets,
        probabilities
    )

    p = precision[:-1]
    r = recall[:-1]

    scores = np.divide(
        2 * p * r,
        p + r,
        out=np.zeros_like(p),
        where=(p + r) > 0
    )

    best = np.flatnonzero(
        np.isclose(
            scores,
            scores.max(),
            rtol=0,
            atol=1e-12
        )
    )

    selected = best[np.argmax(thresholds[best])]

    return {
        "threshold": float(thresholds[selected]),
        "inner_f1": float(scores[selected]),
        "tie_policy": "highest_threshold"
    }


def evaluate_outer_fold(targets, probabilities, threshold):
    targets = np.asarray(targets, dtype=int)
    probabilities = np.asarray(probabilities, dtype=float)

    if len(targets) != len(probabilities):
        raise ValueError("Evaluation alignment mismatch")

    if set(np.unique(targets)) != {0, 1}:
        raise ValueError("Evaluation requires both classes")

    if not np.isfinite(probabilities).all():
        raise ValueError("Invalid probabilities")

    if np.any(probabilities < 0) or np.any(probabilities > 1):
        raise ValueError("Probability outside valid range")

    if not 0 <= threshold <= 1:
        raise ValueError("Invalid threshold")

    predicted = (
        probabilities >= threshold
    ).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        targets,
        predicted,
        labels=[0, 1]
    ).ravel()

    return {
        "average_precision": float(
            average_precision_score(targets, probabilities)
        ),
        "precision": float(
            precision_score(targets, predicted, zero_division=0)
        ),
        "recall": float(
            recall_score(targets, predicted, zero_division=0)
        ),
        "f1": float(
            f1_score(targets, predicted, zero_division=0)
        ),
        "roc_auc": float(
            roc_auc_score(targets, probabilities)
        ),
        "mcc": float(
            matthews_corrcoef(targets, predicted)
        ),
        "balanced_accuracy": float(
            balanced_accuracy_score(targets, predicted)
        ),
        "brier": float(
            brier_score_loss(targets, probabilities)
        ),
        "threshold": float(threshold),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp)
    }


def fold_local_positive_weight(targets):
    targets = np.asarray(targets, dtype=int)

    if set(np.unique(targets)) != {0, 1}:
        raise ValueError("Training requires both classes")

    positives = np.sum(targets == 1)
    negatives = np.sum(targets == 0)

    return float(negatives / positives)
