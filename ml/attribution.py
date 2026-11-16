"""Local model influence, separate from observed artifact evidence.

Linear models explain positive-class margin; forests explain positive-class
probability using additive tree-path changes (not SHAP); XGBoost uses native
TreeSHAP margin contributions. Every full explanation must close numerically.
"""
import math

from ml.classifier_adapters import FoldClassifier
from ml.experiment_inputs import InputContractError

VERSION = "local-attribution-0.1.0"


def explain(classifier, row, *, max_features=30):
    if (not isinstance(classifier, FoldClassifier) or classifier.pipeline is None
            or type(max_features) is not int or not 1 <= max_features <= 100):
        raise InputContractError("attribution_configuration_invalid")
    import numpy as np
    x = classifier._matrix((row,))
    transform = classifier.pipeline.named_steps["preprocess"]
    estimator = classifier.pipeline.named_steps["classifier"]
    z = transform.transform(x)
    names = tuple(str(n) for n in transform.get_feature_names_out())
    values = np.asarray(z.toarray() if hasattr(z, "toarray") else z, dtype=float)[0]
    family = classifier.model.family
    if family in {"logistic_regression", "linear_svm"}:
        contributions = values * estimator.coef_[0]
        base = float(estimator.intercept_[0])
        output = float(estimator.decision_function(z)[0])
        method, space = "linear_feature_times_coefficient", "positive_class_margin"
    elif family == "random_forest":
        contributions = np.zeros(len(values))
        base = 0.
        for tree in estimator.estimators_:
            t = tree.tree_
            def positive(node):
                counts = t.value[node][0]
                return float(counts[1] / counts.sum())
            node = 0
            base += positive(node)
            while t.children_left[node] != t.children_right[node]:
                feature = t.feature[node]
                child = t.children_left[node] if values[feature] <= t.threshold[node] else t.children_right[node]
                contributions[feature] += positive(child) - positive(node)
                node = child
        base /= len(estimator.estimators_)
        contributions /= len(estimator.estimators_)
        output = float(estimator.predict_proba(z)[0, 1])
        method, space = "mean_tree_path_probability_change_not_SHAP", "uncalibrated_positive_class_probability"
    elif family == "xgboost":
        from xgboost import DMatrix
        matrix = DMatrix(z)
        booster = estimator.get_booster()
        result = booster.predict(matrix, pred_contribs=True)[0]
        contributions, base = result[:-1], float(result[-1])
        output = float(booster.predict(matrix, output_margin=True)[0])
        method, space = "native_TreeSHAP", "positive_class_margin"
    else:
        raise InputContractError("attribution_family_unsupported")
    if (len(names) != len(values) or len(contributions) != len(names)
            or not all(math.isfinite(float(v)) for v in (*values, *contributions, base, output))
            or not math.isclose(float(sum(contributions)) + base, output, abs_tol=2e-5, rel_tol=2e-5)):
        raise InputContractError("attribution_closure_failed")
    # Do not reveal unrelated zero-valued vocabulary entries from training.
    observed = (i for i in range(len(names)) if values[i] != 0 or contributions[i] != 0)
    indices = sorted(observed, key=lambda i: (-abs(float(contributions[i])), names[i]))[:max_features]
    return {"version": VERSION, "channel": "model_attribution_not_artifact_evidence",
            "method": method, "space": space, "base_value": base, "explained_output": output,
            "features": [{"feature": names[i], "value": float(values[i]),
                          "contribution": float(contributions[i])} for i in indices],
            "omitted_feature_count": len(names)-len(indices),
            "omitted_contribution": float(sum(contributions[i] for i in range(len(names)) if i not in indices)),
            "calibration_note": "Explains the base classifier; not the subsequent sigmoid probability or causal evidence."}
