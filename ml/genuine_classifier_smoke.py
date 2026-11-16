"""Real CPU estimators on generated fixtures only; NOT research experiments.

Requires the separately approved scientific dependencies. No dataset path,
research-loader, calibration fitting, search, or candidate selection option exists.
Each family bundle has the existing three fixed synthetic artifact names.
"""
import argparse
import hashlib
import json
from pathlib import Path

from ml.classifier_adapters import ClassifierSpecification, PreprocessingSpecification, classifier_factory, require_dependencies
from ml.development_experiments import CLASSIFIER_FAMILIES
from ml.development_runner import (
    CVSpecification, run_synthetic_cv, dimension_ablations, compare_synthetic_results,
    slice_synthetic_metrics, write_synthetic_bundle, verify_synthetic_bundle,
)
from ml.evaluation_metrics import paired_group_bootstrap
from ml.experiment_inputs import InputContractError
from ml.inference_benchmark import benchmark_synthetic_inference
from ml.synthetic_demo import fixture


def synthetic_parameters(family):
    """Fixture execution values, never a proposed or accepted research search."""
    common = dict(C=1., penalty="l2", max_iter=2000, class_weight=None, tol=1e-4, fit_intercept=True)
    if family == "logistic_regression":
        return dict(common, solver="liblinear")
    if family == "linear_svm":
        return dict(common, loss="squared_hinge", dual=False)
    if family == "random_forest":
        return dict(n_estimators=8, max_depth=3, min_samples_leaf=1, max_features="sqrt",
                    class_weight="balanced", criterion="gini", bootstrap=True, n_jobs=1)
    if family == "xgboost":
        return dict(n_estimators=8, max_depth=3, learning_rate=.1, subsample=1., colsample_bytree=1.,
                    min_child_weight=1., reg_lambda=1., scale_pos_weight="fold_ratio", n_jobs=1,
                    tree_method="hist", objective="binary:logistic", eval_metric="logloss", device="cpu", booster="gbtree")
    raise InputContractError("unsupported_classifier_family")


def demonstrate(directory, *, code_reference):
    directory = Path(directory)
    if directory.exists() or not directory.parent.is_dir():
        raise InputContractError("unused_synthetic_directory_and_existing_parent_required")
    for family in CLASSIFIER_FAMILIES:
        require_dependencies(family)
    from threadpoolctl import threadpool_limits
    import numpy as np
    dataset = fixture()
    prepared = []
    fit_count = 0
    hashes = {f"ml/{name}": hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
              for name in ("genuine_classifier_smoke.py", "classifier_adapters.py", "development_runner.py",
                           "development_experiments.py", "evaluation_metrics.py", "inference_benchmark.py", "synthetic_demo.py",
                           "notebook_contracts.py", "metadata.py", "experiment_inputs.py", "requirements-classifiers-synthetic.txt")}
    hashes["ml/se_brl/codebook.v0.1.0.json"] = hashlib.sha256(Path(__file__).with_name("se_brl").joinpath("codebook.v0.1.0.json").read_bytes()).hexdigest()
    with threadpool_limits(limits=1):
        for family in CLASSIFIER_FAMILIES:
            model = ClassifierSpecification(family, synthetic_parameters(family), 17)
            preprocessing = PreprocessingSpecification("reject", "none", None)
            factory = classifier_factory(dataset.specification, model, preprocessing)
            pipelines = []
            def recording_factory(*args):
                pipeline = factory(*args)
                pipelines.append(pipeline)
                return pipeline
            def request(configurations, omitted=()):
                return CVSpecification(family, configurations, 17, 0. if family == "linear_svm" else .5,
                    model.parameters, "synthetic:genuine-fold-classifiers-0.1.0",
                    "synthetic raw pooled scores; no calibrated comparability or selection claim", (0., .5, 1.), omitted)
            result = run_synthetic_cv(dataset, request(dataset.configurations), factory=recording_factory)
            fit_count += len(pipelines)
            benchmark_pipeline = pipelines[-1]
            result["dimension_ablation_smoke"] = {}
            for dimension, omitted in dimension_ablations(dataset).items():
                variant = run_synthetic_cv(dataset, request(("E3",), omitted), factory=factory)
                fit_count += 5
                result["dimension_ablation_smoke"][dimension] = compare_synthetic_results(
                    result, variant, left_configuration="E3", right_configuration="E3")
            omitted = ("fixture_row_index",)
            variant = run_synthetic_cv(dataset, request(("E3",), omitted), factory=factory)
            fit_count += 5
            result["feature_family_ablation_smoke"] = compare_synthetic_results(
                result, variant, left_configuration="E3", right_configuration="E3")
            technical = fixture("UCI")
            u1 = run_synthetic_cv(technical, request(("U1",)),
                factory=classifier_factory(technical.specification, model, preprocessing))
            fit_count += 5
            result["technical_u1_smoke"] = {"result_category": "SYNTHETIC RESULT", "research_execution": "BLOCKED",
                "oof_rows": len(u1["oof_predictions"]), "input_fingerprint": u1["input_fingerprint"],
                "fold_reports": u1["fold_reports"], "pipeline_records": u1["pipeline_records"]}
            e1 = {r["observation_id"]: r for r in result["oof_predictions"] if r["configuration"] == "E1"}
            e3 = {r["observation_id"]: r for r in result["oof_predictions"] if r["configuration"] == "E3"}
            ids = tuple(e1)
            result["paired_bootstrap_smoke"] = paired_group_bootstrap(
                tuple(e1[i]["target"] for i in ids), tuple(e3[i]["score"] for i in ids),
                tuple(e1[i]["score"] for i in ids), tuple(e1[i]["group_id"] for i in ids),
                positive_label=1, resamples=25, confidence=.95, seed=17)
            result["source_slice_smoke"] = slice_synthetic_metrics(result, "E3",
                slices_by_id={r.observation_id: f"artificial-source-{r.target}" for r in dataset.observations})
            # Prepare the numeric model matrix before timing; this fixture has no
            # sparse/text conversion or corpus parsing in its timed boundary.
            row = dataset.observations[0]
            x = np.asarray((row.conventional + row.behavioral,), dtype=object)
            ready = benchmark_pipeline.pipeline.named_steps["preprocess"].transform(x)
            values = tuple(tuple(float(v) for v in r) for r in ready)
            estimator = benchmark_pipeline.pipeline.named_steps["classifier"]
            def predict(rows):
                return tuple(float(v) for v in (estimator.decision_function(rows) if family == "linear_svm"
                                                else estimator.predict_proba(rows)[:, 1]))
            result["efficiency_smoke"] = benchmark_synthetic_inference(predict, values, warmup=1,
                repetitions=5, batch_size=1, thread_reference="synthetic CPU; threadpoolctl limits=1; RF/XGB n_jobs=1")
            result["genuine_estimators"] = True
            result["research_models_fitted"] = 0
            prepared.append((family, result))
    # No files are written unless every requested fixture computation succeeds.
    directory.mkdir()
    summaries = []
    for family, result in prepared:
        path = directory / family
        write_synthetic_bundle(path, result, code_reference=code_reference, code_hashes=hashes)
        verify_synthetic_bundle(path)
        summaries.append({"family": family, "bundle": family,
            "manifest_sha256": hashlib.sha256((path / "manifest.json").read_bytes()).hexdigest(),
            "email_oof_rows": len(result["oof_predictions"]), "score_kind": result["score_kind"]})
    summary = {"result_category": "SYNTHETIC RESULT", "genuine_estimator_fit_calls": fit_count,
        "research_models_fitted": 0, "calibration_fits": 0, "selection_performed": False,
        "research_execution": "BLOCKED", "bundles": summaries,
        "incomplete_export_rule": "Each bundle validates independently; no summary.json means the multi-family export is incomplete."}
    with (directory / "summary.json").open("x", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, allow_nan=False)
        f.write("\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--code-reference", required=True)
    args = parser.parse_args()
    print(json.dumps(demonstrate(args.directory, code_reference=args.code_reference), indent=2))


if __name__ == "__main__":
    main()
