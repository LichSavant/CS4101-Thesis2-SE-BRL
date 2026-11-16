"""Shared nested search/calibration/threshold mechanics.

No corpus loader, new partitions, research authorization or default search grid.
Every split reuses supplied development folds. Numerical settings are required
caller inputs, never inferred approvals. Research enters only with a verified
exact-run context; synthetic verification retains its distinct result category.
"""
from dataclasses import dataclass
import math
import warnings

from ml.classifier_adapters import ClassifierSpecification, PreprocessingSpecification, FoldClassifier
from ml.development_experiments import behavioral_columns, development_folds
from ml.development_runner import ScoreBatch, dataset_fingerprint
from ml.evaluation_metrics import binary_metrics, _numbers, _labels
from ml.experiment_inputs import InputContractError
from ml.metadata import fingerprint, freeze_json, json_value

ENGINE_VERSION = "nested-engine-0.2.0"


@dataclass(frozen=True, slots=True)
class Candidate:
    identifier: str
    model: ClassifierSpecification
    preprocessing: PreprocessingSpecification

    def __post_init__(self):
        if (type(self.identifier) is not str or not self.identifier.strip()
                or not isinstance(self.model, ClassifierSpecification)
                or not isinstance(self.preprocessing, PreprocessingSpecification)):
            raise InputContractError("explicit_candidate_required")


@dataclass(frozen=True, slots=True)
class SigmoidSpecification:
    model: ClassifierSpecification
    transform: str
    clip_epsilon: float

    def __post_init__(self):
        if (not isinstance(self.model, ClassifierSpecification) or self.model.family != "logistic_regression"
                or self.transform not in {"identity", "logit_probability"}):
            raise InputContractError("explicit_sigmoid_specification_required")
        _numbers((self.clip_epsilon,))
        if not 0 < self.clip_epsilon < .5:
            raise InputContractError("explicit_probability_clip_required")


@dataclass(frozen=True, slots=True)
class ThresholdSpecification:
    mode: str
    value: float | None

    def __post_init__(self):
        if self.mode == "fixed":
            _numbers((self.value,), probability=True)
        elif self.mode != "training_crossfit_f1" or self.value is not None:
            raise InputContractError("explicit_threshold_policy_required")


@dataclass(frozen=True, slots=True)
class NestedSpecification:
    candidates: tuple[Candidate, ...]
    configurations: tuple[str, ...]
    calibration: SigmoidSpecification
    threshold: ThresholdSpecification
    calibration_edges: tuple
    protocol_reference: str
    omitted_features: tuple[str, ...] = ()

    def __post_init__(self):
        if (type(self.candidates) is not tuple or not self.candidates
                or any(not isinstance(c, Candidate) for c in self.candidates)
                or len({c.identifier for c in self.candidates}) != len(self.candidates)
                or len({(c.model.family, c.model.seed) for c in self.candidates}) != 1):
            raise InputContractError("unique_same_family_seed_candidates_required")
        if (type(self.configurations) is not tuple or not self.configurations
                or any(type(c) is not str for c in self.configurations)
                or len(set(self.configurations)) != len(self.configurations)):
            raise InputContractError("explicit_unique_configurations_required")
        if not isinstance(self.calibration, SigmoidSpecification) or not isinstance(self.threshold, ThresholdSpecification):
            raise InputContractError("explicit_calibration_and_threshold_required")
        if self.calibration.model.seed != self.candidates[0].model.seed:
            raise InputContractError("matched_explicit_seeds_required")
        if (self.calibration.transform == "logit_probability"
                and self.candidates[0].model.family == "linear_svm"):
            raise InputContractError("margin_cannot_use_probability_logit")
        edges = _numbers(self.calibration_edges)
        if (type(self.calibration_edges) is not tuple or len(edges) < 2 or edges[0] != 0 or edges[-1] != 1
                or any(a >= b for a, b in zip(edges, edges[1:]))):
            raise InputContractError("invalid_calibration_edges")
        if type(self.protocol_reference) is not str or not self.protocol_reference.startswith(("synthetic:", "research:")):
            raise InputContractError("explicit_scoped_protocol_reference_required")
        if (type(self.omitted_features) is not tuple or any(type(n) is not str for n in self.omitted_features)
                or len(set(self.omitted_features)) != len(self.omitted_features)):
            raise InputContractError("explicit_unique_omissions_required")


def _transform(scores, specification):
    values = _numbers(scores, probability=specification.transform == "logit_probability")
    if specification.transform == "identity":
        return values
    epsilon = specification.clip_epsilon
    return tuple(math.log(max(epsilon, min(1-epsilon, p)) / (1-max(epsilon, min(1-epsilon, p)))) for p in values)


class FittedSigmoid:
    """Safe JSON state; fitted solely on cross-fitted scores from training IDs."""
    def __init__(self, specification, slope, intercept):
        if not isinstance(specification, SigmoidSpecification):
            raise InputContractError("explicit_sigmoid_specification_required")
        _numbers((slope, intercept))
        self.specification, self.slope, self.intercept = specification, slope, intercept

    @classmethod
    def fit(cls, scores, labels, specification):
        from sklearn.linear_model import LogisticRegression
        from sklearn.exceptions import ConvergenceWarning
        y = _labels(labels, 1)
        values = _transform(scores, specification)
        if len(values) != len(y) or set(y) != {0, 1}:
            raise InputContractError("two_class_aligned_calibration_required")
        model = LogisticRegression(**json_value(specification.model.parameters), random_state=specification.model.seed)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", ConvergenceWarning)
                model.fit([[s] for s in values], y)
        except Exception:
            raise InputContractError("synthetic_sigmoid_fit_failed") from None
        if tuple(int(v) for v in model.classes_) != (0, 1):
            raise InputContractError("calibration_class_orientation_mismatch")
        return cls(specification, float(model.coef_[0, 0]), float(model.intercept_[0]))

    def probabilities(self, scores):
        from scipy.special import expit
        values = tuple(float(expit(self.slope * x + self.intercept)) for x in _transform(scores, self.specification))
        return _numbers(values, probability=True)

    def state(self):
        from importlib.metadata import version
        return {"version": ENGINE_VERSION, "kind": "regularized_logistic_sigmoid",
                "slope": self.slope, "intercept": self.intercept,
                "transform": self.specification.transform, "clip_epsilon": self.specification.clip_epsilon,
                "parameters": json_value(self.specification.model.parameters), "seed": self.specification.model.seed,
                "sklearn_version": version("scikit-learn")}

    @classmethod
    def from_state(cls, state):
        from importlib.metadata import version
        try:
            if (set(state) != {"version", "kind", "slope", "intercept", "transform", "clip_epsilon", "parameters", "seed", "sklearn_version"}
                    or state["version"] != ENGINE_VERSION or state["kind"] != "regularized_logistic_sigmoid"
                    or state["sklearn_version"] != version("scikit-learn")):
                raise InputContractError("calibration_state_version_mismatch")
            spec = SigmoidSpecification(ClassifierSpecification("logistic_regression", state["parameters"], state["seed"]),
                                        state["transform"], state["clip_epsilon"])
            return cls(spec, state["slope"], state["intercept"])
        except (KeyError, TypeError, ValueError):
            raise InputContractError("invalid_calibration_state") from None


def choose_training_f1_threshold(labels, probabilities):
    """Maximize F1 on TRAINING cross-fits; equal F1 -> smallest observed p.

    This exact policy is an explicit versioned engineering option, not approval.
    """
    y = _labels(labels, 1)
    p = _numbers(probabilities, len(y), probability=True)
    if set(y) != {0, 1}:
        raise InputContractError("two_class_threshold_population_required")
    return max(sorted(set(p)), key=lambda t: (binary_metrics(y, p, positive_label=1, threshold=t)["f1"], -t))


class _Worker:
    def __init__(self, dataset, specification, config, names, factory, execution_context=None):
        self.dataset, self.specification, self.config, self.names, self.factory = dataset, specification, config, names, factory
        self.traces, self.fit_count, self.calibration_count = [], 0, 0
        self.execution_context = execution_context
        self._population_cache = {}

    def population_evidence(self, rows, name):
        ids = tuple(r.observation_id for r in rows)
        if self.execution_context is None:
            return {name: list(ids)}
        # Research traces do not repeat enormous ID lists for every grid point.
        # Actual IDs/folds remain in the immutable D9 input and OOF artifact.
        key = tuple(sorted({r.fold for r in rows}))
        if key not in self._population_cache:
            self._population_cache[key] = (len(ids), fingerprint(sorted(ids)))
        count, digest = self._population_cache[key]
        return {name+"_count": count, name+"_set_sha256": digest}

    def x(self, rows):
        all_names = tuple(c.name for c in self.dataset.specification.conventional)
        if self.config == "E2":
            all_names = behavioral_columns()
        elif self.config == "E3":
            all_names += behavioral_columns()
        positions = tuple(all_names.index(n) for n in self.names)
        result = []
        for row in rows:
            values = row.behavioral if self.config == "E2" else row.conventional
            if self.config == "E3":
                values += row.behavioral
            result.append(tuple(values[i] for i in positions))
        return tuple(result)

    def fit(self, rows, candidate):
        if self.execution_context is not None:
            self.execution_context.before_fit("base", len(rows))
        if set(r.target for r in rows) != {0, 1}:
            raise InputContractError("two_class_training_subset_required")
        pipeline = self.factory(self.dataset.specification, candidate.model, candidate.preprocessing, self.config)
        if not isinstance(pipeline, FoldClassifier) or pipeline.pipeline is not None:
            raise InputContractError("fresh_genuine_classifier_required")
        pipeline.fit(self.x(rows), tuple(r.target for r in rows), feature_names=self.names, seed=candidate.model.seed)
        self.fit_count += 1
        return pipeline

    def score(self, pipeline, rows):
        ids = tuple(r.observation_id for r in rows)
        batch = pipeline.score(self.x(rows), observation_ids=ids)
        if not isinstance(batch, ScoreBatch) or set(batch.observation_ids) != set(ids):
            raise InputContractError("prediction_population_mismatch")
        index = dict(zip(batch.observation_ids, batch.scores))
        return tuple(index[i] for i in ids)

    def split(self, rows):
        folds = sorted({r.fold for r in rows})
        if len(folds) < 2:
            raise InputContractError("at_least_two_supplied_inner_folds_required")
        for fold in folds:
            train, valid = tuple(r for r in rows if r.fold != fold), tuple(r for r in rows if r.fold == fold)
            if set(r.target for r in valid) != {0, 1}:
                raise InputContractError("two_class_validation_subset_required")
            yield train, valid

    def tune(self, rows):
        searches = []
        for candidate in self.specification.candidates:
            y, scores, folds = [], [], []
            for train, valid in self.split(rows):
                pipeline = self.fit(train, candidate)
                scores.extend(self.score(pipeline, valid))
                y.extend(r.target for r in valid)
                folds.append({**self.population_evidence(train, "train_ids"), **self.population_evidence(valid, "validation_ids"),
                              "pipeline": pipeline.audit_record()})
            ap = binary_metrics(y, scores, positive_label=1, threshold=0.)["average_precision"]
            searches.append({"candidate": candidate.identifier, "average_precision": ap, "folds": folds})
        # Candidate tuple order is a predeclared tie rule, never data-dependent.
        winner = max(range(len(searches)), key=lambda i: searches[i]["average_precision"])
        self.traces.append({"stage": "inner_search", **self.population_evidence(rows, "population_ids"),
                            "candidates": searches, "selected": searches[winner]["candidate"]})
        return self.specification.candidates[winner]

    def calibrated(self, rows):
        selected = self.tune(rows)
        base = self.fit(rows, selected)
        y, scores, ids = [], [], []
        # Re-tune inside each calibration split: a calibration row is absent
        # from both its base predictor fit AND that predictor's parameter search.
        for train, valid in self.split(rows):
            inner_selected = self.tune(train)
            pipeline = self.fit(train, inner_selected)
            scores.extend(self.score(pipeline, valid))
            y.extend(r.target for r in valid)
            ids.extend(r.observation_id for r in valid)
        if self.execution_context is not None:
            self.execution_context.before_fit("calibration", len(y))
        sigmoid = FittedSigmoid.fit(scores, y, self.specification.calibration)
        self.calibration_count += 1
        self.traces.append({"stage": "calibration", **self.population_evidence(rows, "training_ids"), "state": sigmoid.state()})
        return base, sigmoid, selected.identifier

    def threshold(self, rows):
        policy = self.specification.threshold
        if policy.mode == "fixed":
            return policy.value
        y, probabilities, ids = [], [], []
        # Full calibrated pipelines exclude each threshold-held-out fold.
        for train, valid in self.split(rows):
            base, sigmoid, _ = self.calibrated(train)
            probabilities.extend(sigmoid.probabilities(self.score(base, valid)))
            y.extend(r.target for r in valid)
            ids.extend(r.observation_id for r in valid)
        threshold = choose_training_f1_threshold(y, probabilities)
        self.traces.append({"stage": "threshold", **self.population_evidence(rows, "training_ids"), "value": threshold,
                            "policy": "training_crossfit_f1_tie_smallest_observed_probability"})
        return threshold


def run_synthetic_nested_cv(dataset, specification, *, classifier_type=FoldClassifier):
    """Five supplied outer folds; all learned choices inside outer training.

    classifier_type is a trusted test seam restricted to genuine FoldClassifier
    instances. This function does not authenticate arbitrary callers/data as
    synthetic and is not a security sandbox. No research launcher is exposed.
    """
    if not isinstance(specification, NestedSpecification) or not specification.protocol_reference.startswith("synthetic:"):
        raise InputContractError("synthetic_protocol_required")
    return _run_nested_cv(dataset, specification, classifier_type=classifier_type)


def run_research_nested_cv(dataset, specification, *, execution_context):
    """Exact accepted development run; no alternate estimator callback seam."""
    from ml.preflight import require_research_fitting
    require_research_fitting(execution_context)
    execution_context.bind(dataset, specification)
    return _run_nested_cv(dataset, specification, classifier_type=FoldClassifier, execution_context=execution_context)


def _run_nested_cv(dataset, specification, *, classifier_type, execution_context=None):
    input_hash = dataset_fingerprint(dataset)  # full D9/group contract before fit
    if not isinstance(specification, NestedSpecification) or not callable(classifier_type):
        raise InputContractError("nested_specification_required")
    plans = {c: development_folds(dataset, c) for c in specification.configurations}
    for config, folds in plans.items():
        names = folds[0].feature_names
        if not set(specification.omitted_features) <= set(names) or set(names) <= set(specification.omitted_features):
            raise InputContractError("invalid_ablation_features")
        # Validate EVERY inner class boundary before the first dependency/fit.
        for plan in folds:
            train = tuple(r for r in dataset.observations if r.fold != plan.validation_fold)
            if any(set(r.target for r in train if r.fold == f) != {0, 1} for f in {r.fold for r in train}):
                raise InputContractError("two_class_inner_fold_required")
            if set(r.target for r in dataset.observations if r.fold == plan.validation_fold) != {0, 1}:
                raise InputContractError("two_class_outer_fold_required")
    oof, reports, pooled, traces, decision_records, fitted = [], [], {}, [], [], []
    base_fits = calibration_fits = 0
    for config, folds in plans.items():
        for plan in folds:
            names = tuple(n for n in plan.feature_names if n not in specification.omitted_features)
            worker = _Worker(dataset, specification, config, names, classifier_type, execution_context)
            train = tuple(r for r in dataset.observations if r.fold != plan.validation_fold)
            valid = tuple(r for r in dataset.observations if r.fold == plan.validation_fold)
            base, sigmoid, selected = worker.calibrated(train)
            threshold = worker.threshold(train)
            raw = worker.score(base, valid)
            probabilities = sigmoid.probabilities(raw)
            metrics = binary_metrics(tuple(r.target for r in valid), probabilities, positive_label=1, threshold=threshold,
                                     probabilities=probabilities, calibration_edges=specification.calibration_edges)
            metrics["probability_provenance"] = "training_nested_crossfit_sigmoid"
            reports.append({"configuration": config, "fold": plan.validation_fold, "feature_names": names,
                            "selected_candidate": selected, "metrics": metrics, "calibration": sigmoid.state(),
                            "pipeline": base.audit_record(), "threshold": threshold})
            traces.append({"configuration": config, "outer_fold": plan.validation_fold,
                           **worker.population_evidence(train, "outer_train_ids"),
                           **worker.population_evidence(valid, "outer_validation_ids"), "events": worker.traces})
            for row, probability in zip(valid, probabilities):
                oof.append({"configuration": config, "observation_id": row.observation_id, "group_id": row.group_id,
                            "fold": row.fold, "target": row.target, "score": probability, "probability": probability})
                decision_records.append({"configuration": config, "observation_id": row.observation_id,
                                         "decision": int(probability >= threshold)})
            fitted.append((config, plan.validation_fold, base, sigmoid, threshold))
            base_fits += worker.fit_count
            calibration_fits += worker.calibration_count
        rows = [r for r in oof if r["configuration"] == config]
        decisions = [r["decision"] for r in decision_records if r["configuration"] == config]
        metrics = binary_metrics(tuple(r["target"] for r in rows), tuple(r["score"] for r in rows), positive_label=1,
                                 threshold=.5, probabilities=tuple(r["probability"] for r in rows),
                                 calibration_edges=specification.calibration_edges)
        threshold_metrics = binary_metrics(tuple(r["target"] for r in rows), decisions, positive_label=1, threshold=.5)
        for key in ("confusion_matrix", "precision", "recall", "f1", "specificity", "balanced_accuracy", "mcc"):
            metrics[key] = threshold_metrics[key]
        metrics.update(threshold=None, threshold_scale="fold_specific_training_policy", probability_provenance="training_nested_crossfit_sigmoid")
        pooled[config] = metrics
    request = {"family": specification.candidates[0].model.family, "seed": specification.candidates[0].model.seed,
               "configurations": specification.configurations, "protocol_reference": specification.protocol_reference,
               "candidates": [{"id": c.identifier, "parameters": c.model.parameters, "preprocessing": {
                   "numeric_missing": c.preprocessing.numeric_missing, "numeric_scaling": c.preprocessing.numeric_scaling,
                   "text_parameters": c.preprocessing.text_parameters}} for c in specification.candidates],
               "calibration": {"parameters": specification.calibration.model.parameters, "transform": specification.calibration.transform,
                               "clip_epsilon": specification.calibration.clip_epsilon},
               "threshold": {"mode": specification.threshold.mode, "value": specification.threshold.value},
               "calibration_edges": specification.calibration_edges, "omitted_features": specification.omitted_features,
               "search_statistic": "pooled_inner_raw_average_precision", "search_tie_rule": "declared_candidate_order",
               "outer_ranking_statistic": "pooled_nested_sigmoid_average_precision"}
    result = json_value(freeze_json({"result_category": "SYNTHETIC RESULT" if execution_context is None else "RESEARCH RESULT",
        "research_execution": "BLOCKED" if execution_context is None else "AUTHORIZED DEVELOPMENT ONLY",
        "engine_version": ENGINE_VERSION, "dataset": dataset.specification.dataset, "input_fingerprint": input_hash,
        "request": request, "request_fingerprint": fingerprint(request), "base_fits": base_fits,
        "calibration_fits": calibration_fits, "selection_performed": False, "candidate_search_performed": True,
        "oof_predictions": oof, "fold_reports": reports, "pooled_metrics": pooled,
        "decision_records": decision_records, "traces": traces}))
    if execution_context is not None:
        execution_context.check_budget()
        result["authorization_sha256"] = execution_context.authorization_sha256
        result["execution_scope"] = execution_context._state.get("boundary")
        result["accepted_specification_fingerprint"] = execution_context.specification_fingerprint
        result["exposure_disposition"] = execution_context.exposure_disposition
        result["final_evaluation_authorized"] = False
    return result, tuple(fitted)
