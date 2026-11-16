"""Genuine fold-local classifiers for the D9 synthetic development runner.

No corpus loader, search, implicit calibration, serialization, or research
authorization lives here. Dependencies are lazy and never replaced by stubs.
Caller-supplied settings are explicit execution settings, not protocol approval.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import import_module, metadata
import math
import warnings

from ml.development_experiments import DevelopmentSpecification, behavioral_columns
from ml.development_runner import ScoreBatch
from ml.experiment_inputs import InputContractError
from ml.metadata import fingerprint, freeze_json, json_value

ADAPTER_VERSION = "genuine-fold-classifiers-0.1.0"
PARAMETERS = {
    "logistic_regression": frozenset(("C", "penalty", "solver", "max_iter", "class_weight", "tol", "fit_intercept")),
    "linear_svm": frozenset(("C", "penalty", "loss", "dual", "max_iter", "class_weight", "tol", "fit_intercept")),
    "random_forest": frozenset(("n_estimators", "max_depth", "min_samples_leaf", "max_features", "class_weight", "criterion", "bootstrap", "n_jobs")),
    "xgboost": frozenset(("n_estimators", "max_depth", "learning_rate", "subsample", "colsample_bytree", "min_child_weight", "reg_lambda", "scale_pos_weight", "n_jobs", "tree_method", "objective", "eval_metric", "device", "booster")),
}
TEXT_PARAMETERS = frozenset(("lowercase", "ngram_range", "min_df", "max_df", "max_features", "sublinear_tf", "norm", "strip_accents", "analyzer", "token_pattern", "stop_words"))


class ClassifierDependencyError(InputContractError):
    """The requested genuine algorithm cannot run in this environment."""


def _positive(value, *, integer=False, zero=False):
    try:
        valid = (type(value) in ((int,) if integer else (int, float))
                 and math.isfinite(value) and value >= 0 and (zero or value != 0))
    except OverflowError:
        valid = False
    if not valid:
        raise InputContractError("invalid_explicit_classifier_parameter")


@dataclass(frozen=True, slots=True)
class ClassifierSpecification:
    family: str
    parameters: Mapping
    seed: int

    def __post_init__(self):
        if type(self.family) is not str or self.family not in PARAMETERS:
            raise InputContractError("unsupported_classifier_family")
        if type(self.seed) is not int or not 0 <= self.seed <= 2**32 - 1:
            raise InputContractError("explicit_uint32_seed_required")
        if not isinstance(self.parameters, Mapping) or set(self.parameters) != PARAMETERS[self.family]:
            raise InputContractError("exact_explicit_classifier_parameters_required")
        p = json_value(freeze_json(self.parameters))
        if any(v is not None and type(v) not in (str, int, float, bool) for v in p.values()):
            raise InputContractError("scalar_classifier_parameters_required")
        for name in ("C", "tol", "learning_rate", "reg_lambda", "min_child_weight"):
            if name in p:
                _positive(p[name], zero=name in {"reg_lambda", "min_child_weight"})
        for name in ("max_iter", "n_estimators", "min_samples_leaf", "n_jobs"):
            if name in p:
                _positive(p[name], integer=True)
        if "max_depth" in p and p["max_depth"] is not None:
            _positive(p["max_depth"], integer=True)
        if self.family in {"logistic_regression", "linear_svm"}:
            if p["penalty"] != "l2" or p["class_weight"] not in (None, "balanced") or type(p["fit_intercept"]) is not bool:
                raise InputContractError("unsupported_linear_classifier_setting")
            if self.family == "logistic_regression" and p["solver"] not in {"liblinear", "lbfgs", "saga"}:
                raise InputContractError("unsupported_logistic_solver")
            if self.family == "linear_svm" and (p["loss"] != "squared_hinge" or type(p["dual"]) is not bool):
                raise InputContractError("explicit_linear_svm_solver_required")
        if self.family == "random_forest":
            if (p["max_features"] not in ("sqrt", .5) or p["class_weight"] not in (None, "balanced", "balanced_subsample")
                    or p["criterion"] not in {"gini", "entropy", "log_loss"} or type(p["bootstrap"]) is not bool):
                raise InputContractError("unsupported_forest_setting")
        if self.family == "xgboost":
            if p["max_depth"] is None:
                raise InputContractError("explicit_xgboost_depth_required")
            for name in ("subsample", "colsample_bytree"):
                _positive(p[name])
                if p[name] > 1:
                    raise InputContractError("invalid_sampling_fraction")
            if p["scale_pos_weight"] != "fold_ratio":
                _positive(p["scale_pos_weight"])
            if (p["objective"] != "binary:logistic" or p["booster"] != "gbtree"
                    or p["tree_method"] != "hist" or p["device"] != "cpu" or p["eval_metric"] != "logloss"):
                raise InputContractError("explicit_cpu_binary_xgboost_required")
        object.__setattr__(self, "parameters", freeze_json(p))


@dataclass(frozen=True, slots=True)
class PreprocessingSpecification:
    numeric_missing: str
    numeric_scaling: str
    text_parameters: Mapping | None

    def __post_init__(self):
        if self.numeric_missing not in {"reject", "median"} or self.numeric_scaling not in {"none", "standard"}:
            raise InputContractError("explicit_preprocessing_policy_required")
        if self.text_parameters is not None:
            if not isinstance(self.text_parameters, Mapping) or set(self.text_parameters) != TEXT_PARAMETERS:
                raise InputContractError("exact_explicit_tfidf_parameters_required")
            p = json_value(freeze_json(self.text_parameters))
            if (type(p["ngram_range"]) is not list or len(p["ngram_range"]) != 2
                    or any(type(n) is not int or n < 1 for n in p["ngram_range"])
                    or p["ngram_range"][0] > p["ngram_range"][1]
                    or p["analyzer"] != "word" or p["norm"] not in (None, "l1", "l2")
                    or p["strip_accents"] not in (None, "ascii", "unicode")
                    or any(type(p[k]) is not bool for k in ("lowercase", "sublinear_tf"))
                    or p["stop_words"] not in (None, "english") or type(p["token_pattern"]) is not str):
                raise InputContractError("invalid_explicit_tfidf_parameters")
            for key in ("min_df", "max_df"):
                _positive(p[key])
                if type(p[key]) is float and p[key] > 1:
                    raise InputContractError("invalid_tfidf_document_frequency")
            if p["max_features"] is not None:
                _positive(p["max_features"], integer=True)
            object.__setattr__(self, "text_parameters", freeze_json(p))


def require_dependencies(family):
    """Read-only check. Never installs a package or changes environments."""
    if family not in PARAMETERS:
        raise InputContractError("unsupported_classifier_family")
    names = ("numpy", "scipy", "sklearn") + (("xgboost",) if family == "xgboost" else ())
    for name in names:
        try:
            import_module(name)
        except (ImportError, OSError):
            raise ClassifierDependencyError(f"genuine_classifier_dependency_unavailable:{name}") from None


class FoldClassifier:
    """Single-use pipeline; only the runner supplies development fold matrices.

    Matrices contain predictors only; no IDs, groups, partitions or validation
    labels are estimator inputs. This is an interface boundary, not a sandbox.
    Raw predict_proba output is explicitly uncalibrated; LinearSVC stays a margin.
    """
    def __init__(self, dictionary, model, preprocessing, configuration):
        if (not isinstance(dictionary, DevelopmentSpecification) or not isinstance(model, ClassifierSpecification)
                or not isinstance(preprocessing, PreprocessingSpecification)):
            raise InputContractError("typed_classifier_specifications_required")
        allowed = ("E1", "E2", "E3") if dictionary.dataset in {"Email", "Web"} else ("U1",)
        if configuration not in allowed:
            raise InputContractError("configuration_branch_mismatch")
        self.dictionary, self.model, self.preprocessing, self.configuration = dictionary, model, preprocessing, configuration
        conventional = tuple(c.name for c in dictionary.conventional)
        self.expected = conventional if configuration in {"E1", "U1"} else behavioral_columns() if configuration == "E2" else conventional + behavioral_columns()
        self.kinds = {c.name: c.kind for c in dictionary.conventional}
        self.kinds.update({c: "numeric" for c in behavioral_columns()})
        self.pipeline = None
        self._attempted = False
        self._record = None

    def _matrix(self, rows):
        if type(rows) is not tuple or not rows:
            raise InputContractError("nonempty_immutable_predictor_rows_required")
        clean = []
        for row in rows:
            if type(row) is not tuple or len(row) != len(self.feature_names):
                raise InputContractError("predictor_schema_width_mismatch")
            values = []
            for name, value in zip(self.feature_names, row):
                if self.kinds[name] == "text":
                    if type(value) is not str or not value.strip():
                        raise InputContractError("missing_or_invalid_text_predictor")
                elif value is None:
                    if name in behavioral_columns() or self.preprocessing.numeric_missing == "reject":
                        raise InputContractError("missing_numeric_predictor")
                    value = float("nan")
                else:
                    if type(value) not in (int, float):
                        raise InputContractError("invalid_numeric_predictor")
                    _positive(abs(value), zero=True)
                    if name in behavioral_columns() and value not in (0, 1):
                        raise InputContractError("binary_behavioral_value_required")
                values.append(value)
            clean.append(values)
        return import_module("numpy").asarray(clean, dtype=object)

    def fit(self, rows, labels, *, feature_names, seed):
        if self._attempted:
            raise InputContractError("single_use_fold_classifier_required")
        if seed != self.model.seed or type(seed) is not int:
            raise InputContractError("classifier_seed_mismatch")
        if (type(feature_names) is not tuple or not feature_names or any(type(n) is not str for n in feature_names)
                or len(set(feature_names)) != len(feature_names)
                or tuple(n for n in self.expected if n in feature_names) != feature_names):
            raise InputContractError("ordered_dictionary_predictors_required")
        if (type(rows) is not tuple or not rows or type(labels) is not tuple or len(labels) != len(rows)
                or any(type(y) is not int or y not in (0, 1) for y in labels) or set(labels) != {0, 1}):
            raise InputContractError("both_binary_training_classes_required")
        self.feature_names = feature_names
        require_dependencies(self.model.family)
        x = self._matrix(rows)
        self._attempted = True
        from sklearn.compose import ColumnTransformer
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.exceptions import ConvergenceWarning
        transforms = []
        numeric = [i for i, n in enumerate(feature_names) if self.kinds[n] == "numeric"]
        if numeric:
            if any(all(row[i] is None for row in rows) for i in numeric):
                raise InputContractError("training_numeric_column_entirely_missing")
            steps = []
            if self.preprocessing.numeric_missing == "median":
                steps.append(("impute", SimpleImputer(strategy="median", keep_empty_features=True)))
            if self.preprocessing.numeric_scaling == "standard":
                steps.append(("scale", StandardScaler(with_mean=False)))
            transforms.append(("numeric", Pipeline(steps) if steps else "passthrough", numeric))
        for i, name in enumerate(feature_names):
            if self.kinds[name] == "text":
                if self.preprocessing.text_parameters is None:
                    raise InputContractError("text_preprocessing_specification_required")
                p = json_value(self.preprocessing.text_parameters)
                p["ngram_range"] = tuple(p["ngram_range"])
                transforms.append((f"text_{i}", TfidfVectorizer(**p), i))
        params = json_value(self.model.parameters)
        params["random_state"] = seed
        if self.model.family == "logistic_regression":
            from sklearn.linear_model import LogisticRegression
            estimator = LogisticRegression(**params)
        elif self.model.family == "linear_svm":
            from sklearn.svm import LinearSVC
            estimator = LinearSVC(**params)
        elif self.model.family == "random_forest":
            from sklearn.ensemble import RandomForestClassifier
            estimator = RandomForestClassifier(**params)
        else:
            from xgboost import XGBClassifier
            if params["scale_pos_weight"] == "fold_ratio":
                params["scale_pos_weight"] = labels.count(0) / labels.count(1)
            estimator = XGBClassifier(**params)
        pipeline = Pipeline((("preprocess", ColumnTransformer(transforms, remainder="drop", sparse_threshold=1., n_jobs=1)),
                             ("classifier", estimator)))
        # A nonconverged fit cannot silently become a successful candidate run.
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            pipeline.fit(x, labels)
        if tuple(int(v) for v in estimator.classes_) != (0, 1):
            raise InputContractError("positive_class_orientation_mismatch")
        resolved = estimator.get_params(deep=False)
        # XGB's default missing=nan is configuration, never a serialized JSON NaN.
        resolved = {k: "NaN sentinel" if type(v) is float and math.isnan(v) else v for k, v in resolved.items()}
        self._record = json_value(freeze_json({"adapter_version": ADAPTER_VERSION,
            "estimator": f"{type(estimator).__module__}.{type(estimator).__name__}",
            "family": self.model.family, "parameters": self.model.parameters, "resolved_estimator_parameters": resolved,
            "preprocessing": {"numeric_missing": self.preprocessing.numeric_missing,
                "numeric_scaling": self.preprocessing.numeric_scaling, "text_parameters": self.preprocessing.text_parameters},
            "feature_names": feature_names, "dictionary_reference": self.dictionary.feature_dictionary_reference,
            "protocol_reference": self.dictionary.protocol_reference, "training_rows": len(rows),
            "training_matrix_hash": fingerprint({"x": rows, "y": labels}),
            "positive_label": 1, "calibration": "none; raw estimator output", "seed": seed,
            "versions": {n: metadata.version(n) for n in ("numpy", "scipy", "scikit-learn") + (("xgboost",) if self.model.family == "xgboost" else ())}}))
        self.pipeline = pipeline
        return self

    def score(self, rows, *, observation_ids):
        if self.pipeline is None:
            raise InputContractError("fitted_fold_classifier_required")
        if (type(rows) is not tuple or not rows or type(observation_ids) is not tuple or len(observation_ids) != len(rows)
                or any(type(i) is not str or not i.strip() for i in observation_ids)
                or len(set(observation_ids)) != len(observation_ids)):
            raise InputContractError("exact_unique_prediction_ids_required")
        x = self._matrix(rows)
        if self.model.family == "linear_svm":
            values = tuple(float(v) for v in self.pipeline.decision_function(x))
            return ScoreBatch(observation_ids, values, "margin", 1)
        values = tuple(float(v) for v in self.pipeline.predict_proba(x)[:, 1])
        return ScoreBatch(observation_ids, values, "probability", 1, values)

    def audit_record(self):
        if self._record is None:
            raise InputContractError("fitted_fold_classifier_required")
        return json_value(freeze_json(self._record))


def classifier_factory(dictionary, model, preprocessing):
    """Bind exact settings; reject runner requests that disagree before fitting."""
    # Validate now even if a caller supplies no folds, without importing libraries.
    if not isinstance(dictionary, DevelopmentSpecification):
        raise InputContractError("typed_classifier_specifications_required")
    FoldClassifier(dictionary, model, preprocessing, "E1" if dictionary.dataset in {"Email", "Web"} else "U1")
    def factory(family, configuration, fold, seed, parameters):
        if (family != model.family or seed != model.seed or freeze_json(parameters) != model.parameters
                or type(fold) is not int or fold not in range(1, 6)):
            raise InputContractError("runner_classifier_specification_mismatch")
        return FoldClassifier(dictionary, model, preprocessing, configuration)
    return factory
