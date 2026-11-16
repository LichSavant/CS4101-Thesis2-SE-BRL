"""Contract tests and genuine synthetic fits; never opens research inputs."""
from dataclasses import replace
from importlib.util import find_spec
import json

import pytest

from ml.classifier_adapters import (
    ClassifierSpecification, PreprocessingSpecification, FoldClassifier,
    classifier_factory, ClassifierDependencyError, require_dependencies,
)
from ml.development_experiments import DevelopmentSpecification, FeatureColumn
from ml.development_runner import CVSpecification, run_synthetic_cv, write_synthetic_bundle, verify_synthetic_bundle
from ml.experiment_inputs import InputContractError
from ml.synthetic_demo import fixture
from ml.genuine_classifier_smoke import synthetic_parameters


def settings(family):
    """Tiny fixture budgets are NOT proposed or approved research search settings."""
    return synthetic_parameters(family)


def preprocessing(**changes):
    values = dict(numeric_missing="reject", numeric_scaling="none", text_parameters=None)
    values.update(changes)
    return PreprocessingSpecification(**values)


def text_parameters():
    return dict(lowercase=True, ngram_range=(1, 1), min_df=1, max_df=1., max_features=100,
                sublinear_tf=False, norm="l2", strip_accents=None, analyzer="word",
                token_pattern=r"(?u)\b\w\w+\b", stop_words=None)


def model(family="logistic_regression", **changes):
    return ClassifierSpecification(family, dict(settings(family), **changes), 17)


FAMILIES = ("logistic_regression", "linear_svm", "random_forest", "xgboost")
SCIENCE = all(find_spec(n) is not None for n in ("numpy", "scipy", "sklearn", "xgboost"))
genuine = pytest.mark.skipif(not SCIENCE, reason="genuine classifier dependencies absent; no substitute fit")


@pytest.mark.parametrize("family", FAMILIES)
def test_explicit_parameters_are_immutable_and_exact(family):
    p = settings(family)
    spec = ClassifierSpecification(family, p, 17)
    p[next(iter(p))] = "changed"
    assert dict(spec.parameters) == settings(family)
    with pytest.raises(TypeError):
        spec.parameters["extra"] = True
    for broken in ({}, dict(settings(family), early_stopping_rounds=1), None):
        with pytest.raises(InputContractError):
            ClassifierSpecification(family, broken, 17)


@pytest.mark.parametrize("change", [{"seed": True}, {"seed": -1}, {"seed": 2**32}, {"family": "transformer"}])
def test_invalid_family_seed(change):
    with pytest.raises(InputContractError):
        replace(model(), **change)


@pytest.mark.parametrize("change", [{"C": 0}, {"C": True}, {"C": float("inf")}, {"C": 10**1000},
    {"max_iter": 0}, {"max_iter": 2.5}, {"penalty": "l1"}, {"solver": "unknown"},
    {"class_weight": {0: 1}}, {"fit_intercept": 1}])
def test_invalid_linear_parameters(change):
    with pytest.raises((InputContractError, ValueError)):
        model(**change)


@pytest.mark.parametrize("family,change", [
    ("linear_svm", {"dual": "auto"}), ("linear_svm", {"loss": "hinge"}),
    ("random_forest", {"n_jobs": -1}), ("random_forest", {"bootstrap": 1}),
    ("random_forest", {"max_features": "target"}), ("xgboost", {"subsample": 2}),
    ("xgboost", {"scale_pos_weight": 0}), ("xgboost", {"device": "cuda"}),
    ("xgboost", {"objective": "multi:softprob"}), ("xgboost", {"booster": "gblinear"}),
])
def test_invalid_other_classifier_parameters(family, change):
    with pytest.raises(InputContractError):
        model(family, **change)


@pytest.mark.parametrize("changes", [dict(numeric_missing="zero"), dict(numeric_scaling="fit_on_all"),
    dict(text_parameters={}), dict(text_parameters=dict(text_parameters(), min_df=True)),
    dict(text_parameters=dict(text_parameters(), ngram_range=(2, 1)))])
def test_explicit_preprocessing_contract(changes):
    with pytest.raises(InputContractError):
        preprocessing(**changes)


def test_runner_binding_and_branches_fail_before_import_or_fit():
    ds = fixture()
    factory = classifier_factory(ds.specification, model(), preprocessing())
    for args in (("linear_svm", "E1", 1, 17, settings("logistic_regression")),
                 ("logistic_regression", "E1", 1, 18, settings("logistic_regression")),
                 ("logistic_regression", "E1", 0, 17, settings("logistic_regression")),
                 ("logistic_regression", "E1", 1, 17, {})):
        with pytest.raises(InputContractError, match="runner_classifier_specification_mismatch"):
            factory(*args)
    with pytest.raises(InputContractError):
        FoldClassifier(fixture("UCI").specification, model(), preprocessing(), "E2")
    with pytest.raises(InputContractError):
        classifier_factory(None, model(), preprocessing())


def test_dependency_absence_fails_explicitly_without_substitution(monkeypatch):
    import ml.classifier_adapters as adapters
    def unavailable(name):
        raise ImportError("sensitive machine information")
    monkeypatch.setattr(adapters, "import_module", unavailable)
    with pytest.raises(ClassifierDependencyError, match="unavailable:numpy") as caught:
        require_dependencies("logistic_regression")
    assert "sensitive" not in str(caught.value)


@pytest.mark.parametrize("names", [("target",), ("source_dataset",), ("unknown",),
    ("fixture_row_index", "fixture_signal"), ("fixture_signal", "fixture_signal"), ()])
def test_invalid_predictor_schema_rejected_before_dependency_access(names, monkeypatch):
    import ml.classifier_adapters as adapters
    monkeypatch.setattr(adapters, "require_dependencies", lambda *a: pytest.fail("invalid schema reached dependency access"))
    pipe = FoldClassifier(fixture().specification, model(), preprocessing(), "E1")
    with pytest.raises(InputContractError, match="ordered_dictionary_predictors_required"):
        pipe.fit(((0., 1.), (1., 2.)), (0, 1), feature_names=names, seed=17)


@genuine
@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("branch", ["Email", "UCI"])
def test_genuine_matched_cv_all_families_and_technical_boundary(family, branch, tmp_path):
    ds = fixture(branch)
    configs = ds.configurations
    m = model(family)
    request = CVSpecification(family, configs, 17, 0. if family == "linear_svm" else .5, m.parameters,
        "synthetic:genuine-classifier-adapters", "synthetic uncalibrated pooled scale; not selection evidence", (0., .5, 1.))
    produced = []
    real_factory = classifier_factory(ds.specification, m, preprocessing())
    def factory(*args):
        pipe = real_factory(*args)
        produced.append(pipe)
        return pipe
    result = run_synthetic_cv(ds, request, factory=factory)
    assert len(produced) == 5 * len(configs)
    assert len(result["pipeline_records"]) == len(produced)
    assert len({id(p.pipeline) for p in produced}) == len(produced)
    assert result["calibration_fits"] == 0 and result["research_execution"] == "BLOCKED"
    for record, pipe in zip(result["pipeline_records"], produced):
        meta = record["pipeline"]
        assert meta["training_rows"] == 8
        assert meta["seed"] == meta["resolved_estimator_parameters"]["random_state"] == 17
        assert "target" not in meta["feature_names"]
        assert meta["versions"]["scikit-learn"] == "1.6.1"
        assert type(pipe.pipeline.named_steps["classifier"]).__name__ == {
            "logistic_regression": "LogisticRegression", "linear_svm": "LinearSVC",
            "random_forest": "RandomForestClassifier", "xgboost": "XGBClassifier"}[family]
        if family == "xgboost":
            assert meta["resolved_estimator_parameters"]["scale_pos_weight"] == 1.
        if branch == "UCI":
            assert not any(n.endswith(("_supported", "_available")) for n in meta["feature_names"])
    for config in configs:
        rows = [r for r in result["oof_predictions"] if r["configuration"] == config]
        assert {(r["observation_id"], r["group_id"], r["fold"]) for r in rows} == {
            (r.observation_id, r.group_id, r.fold) for r in ds.observations}
        assert all((r["probability"] is None) == (family == "linear_svm") for r in rows)
    repeated = run_synthetic_cv(ds, request, factory=real_factory)
    assert repeated == result
    path = tmp_path / "unused-bundle"
    write_synthetic_bundle(path, result, code_reference="synthetic-test", code_hashes={"test": "0" * 64})
    verify_synthetic_bundle(path)
    manifest = json.loads((path / "manifest.json").read_text())
    assert manifest["pipeline_records"] == result["pipeline_records"]
    with pytest.raises(InputContractError, match="already_exists"):
        write_synthetic_bundle(path, result, code_reference="synthetic-test", code_hashes={"test": "0" * 64})


@genuine
@pytest.mark.parametrize("family", FAMILIES)
def test_fold_local_text_imputation_scaling_and_no_validation_learning(family):
    dictionary = DevelopmentSpecification("Email", (FeatureColumn("body_text", "text"), FeatureColumn("measurement", "numeric")),
                                          "synthetic-only", "synthetic-only")
    pipe = FoldClassifier(dictionary, model(family), preprocessing(numeric_missing="median", numeric_scaling="standard",
                        text_parameters=text_parameters()), "E1")
    training = (("ordinary alpha", -1), ("ordinary beta", 0), ("urgent alpha", None), ("urgent gamma", 2))
    pipe.fit(training, (0, 0, 1, 1), feature_names=("body_text", "measurement"), seed=17)
    transform = pipe.pipeline.named_steps["preprocess"]
    vocabulary = dict(transform.named_transformers_["text_0"].vocabulary_)
    statistics = transform.named_transformers_["numeric"].named_steps["impute"].statistics_.copy()
    before = pipe.audit_record()
    result = pipe.score((("unseenword onlyvalidation", 100000), ("alpha ordinary", None)), observation_ids=("v2", "v1"))
    assert result.observation_ids == ("v2", "v1")
    assert transform.named_transformers_["text_0"].vocabulary_ == vocabulary
    assert "onlyvalidation" not in vocabulary
    assert list(statistics) == [0]
    assert list(transform.named_transformers_["numeric"].named_steps["impute"].statistics_) == [0]
    assert pipe.audit_record() == before
    assert training[0][1] == -1 and training[1][1] == 0
    with pytest.raises(InputContractError, match="single_use"):
        pipe.fit(training, (0, 0, 1, 1), feature_names=("body_text", "measurement"), seed=17)


@genuine
def test_native_codes_pass_through_and_positive_orientation():
    pipe = FoldClassifier(fixture("UCI").specification, model(), preprocessing(), "U1")
    rows = ((-1, 0), (-1, 1), (1, 0), (1, 1))
    pipe.fit(rows, (0, 0, 1, 1), feature_names=("fixture_signal", "fixture_row_index"), seed=17)
    import numpy as np
    assert np.array_equal(pipe.pipeline.named_steps["preprocess"].transform(np.array(rows, dtype=object)), rows)
    result = pipe.score(((-1, 0), (1, 0)), observation_ids=("negative", "positive"))
    assert result.scores[1] > result.scores[0]
    assert result.scores == result.probabilities


@genuine
@pytest.mark.parametrize("rows", [((None, 0), (None, 1)), ((True, 0), (1, 1)), ((float("nan"), 0), (1, 1))])
def test_missing_nonfinite_or_boolean_numeric_fails(rows):
    pipe = FoldClassifier(fixture().specification, model(), preprocessing(numeric_missing="median"), "E1")
    with pytest.raises(InputContractError):
        pipe.fit(rows, (0, 1), feature_names=("fixture_signal", "fixture_row_index"), seed=17)


@genuine
def test_xgboost_weight_uses_supplied_training_labels_only():
    pipe = FoldClassifier(fixture().specification, model("xgboost"), preprocessing(), "E1")
    pipe.fit(((0, 1), (0, 2), (0, 3), (1, 4)), (0, 0, 0, 1),
             feature_names=("fixture_signal", "fixture_row_index"), seed=17)
    assert pipe.audit_record()["resolved_estimator_parameters"]["scale_pos_weight"] == 3.
    pipe.score(((100, 100),), observation_ids=("validation",))
    assert pipe.audit_record()["resolved_estimator_parameters"]["scale_pos_weight"] == 3.


@genuine
def test_missing_text_and_prediction_identity_fail_without_refit():
    d = DevelopmentSpecification("Email", (FeatureColumn("body_text", "text"),), "synthetic-only", "synthetic-only")
    p = FoldClassifier(d, model(), preprocessing(text_parameters=text_parameters()), "E1")
    with pytest.raises(InputContractError, match="missing_or_invalid_text_predictor"):
        p.fit(((None,), ("valid",)), (0, 1), feature_names=("body_text",), seed=17)
    p.fit((("normal alpha",), ("urgent beta",)), (0, 1), feature_names=("body_text",), seed=17)
    with pytest.raises(InputContractError, match="exact_unique_prediction_ids"):
        p.score((("urgent beta",), ("normal alpha",)), observation_ids=("repeat", "repeat"))


@genuine
def test_convergence_warning_is_not_reported_as_success(monkeypatch):
    from sklearn.linear_model import LogisticRegression
    from sklearn.exceptions import ConvergenceWarning
    import warnings
    def nonconverged(*args, **kwargs):
        warnings.warn("fixture-only nonconvergence", ConvergenceWarning)
    monkeypatch.setattr(LogisticRegression, "fit", nonconverged)
    p = FoldClassifier(fixture().specification, model(), preprocessing(), "E1")
    with pytest.raises(ConvergenceWarning):
        p.fit(((0, 0), (1, 1)), (0, 1), feature_names=("fixture_signal", "fixture_row_index"), seed=17)
    with pytest.raises(InputContractError, match="fitted_fold_classifier_required"):
        p.score(((0, 0),), observation_ids=("validation",))
