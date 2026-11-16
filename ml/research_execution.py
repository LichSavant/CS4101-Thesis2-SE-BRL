"""Verify or execute one explicitly authorized immutable development run.

Default verifies only. --execute additionally requires the independent acceptance
digest and all fixed, consistent evidence files. No source discovery, partition
allocation, calibration/test payload loading, final selection or final freeze.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from ml.development_experiments import _within
from ml.evaluation_metrics import binary_metrics, paired_group_bootstrap
from ml.experiment_artifacts import write_nested_bundle, load_nested_bundle
from ml.experiment_engine import run_research_nested_cv
from ml.experiment_inputs import InputContractError
from ml.metadata import fingerprint
from ml.research_protocol import verify_accepted_run, fit_estimate


def benchmark_outer_models(fitted, dataset, context):
    from ml.inference_benchmark import benchmark_research_model
    from ml.model_persistence import serialized_fold_bytes
    configuration = "E3" if dataset.specification.dataset in {"Email", "Web"} else "U1"
    benchmark_folds = []
    for config, fold, classifier, _, _ in fitted:
        if config != configuration:
            continue
        # Prespecified validation-fold smallest ID: label-independent and
        # reproducible. Predictors are prepared outside the model-only timer.
        observation = min((r for r in dataset.observations if r.fold == fold), key=lambda r:r.observation_id)
        raw = observation.conventional + (observation.behavioral if config == "E3" else ())
        from ml.development_experiments import behavioral_columns
        names = tuple(c.name for c in dataset.specification.conventional) + (behavioral_columns() if config == "E3" else ())
        lookup = dict(zip(names, raw))
        values = tuple(lookup[n] for n in classifier.feature_names)
        benchmark_folds.append(benchmark_research_model(classifier, (values,), execution_context=context,
            settings=context.selection_record["benchmark"], serialized_model_bytes=serialized_fold_bytes(classifier)))
    if len(benchmark_folds) != 5:
        raise InputContractError("five_selected_outer_models_required_for_benchmark")
    result = dict(benchmark_folds[0])
    result.update(p95_batch_ms=max(b["p95_batch_ms"] for b in benchmark_folds),
        p50_batch_ms=max(b["p50_batch_ms"] for b in benchmark_folds),
        throughput_artifacts_per_second=min(b["throughput_artifacts_per_second"] for b in benchmark_folds),
        serialized_model_bytes=max(b["serialized_model_bytes"] for b in benchmark_folds),
        measured_memory_bytes_max=(max(b["measured_memory_bytes_max"] for b in benchmark_folds)
            if all(b["measured_memory_bytes_max"] is not None for b in benchmark_folds) else None),
        aggregation="max latency/encoded size/process working set, min throughput across outer selected models",
        fold_benchmarks=benchmark_folds)
    result["p95_model_ms_per_artifact"] = result["p95_batch_ms"]
    result["p50_model_ms_per_artifact"] = result["p50_batch_ms"]
    result.pop("timed_batch_seconds")  # individual timing arrays remain per fold
    return result


def source_diagnostics(dataset, context):
    contingency = {}
    for row in dataset.observations:
        source = context.sources_by_id[row.observation_id]
        counts = contingency.setdefault(source, {"0": 0, "1": 0})
        counts[str(row.target)] += 1
    return {"source_class_counts": contingency,
            "single_target_sources": sorted(s for s, counts in contingency.items() if 0 in counts.values()),
            "source_independent_performance_established": False,
            "note": "Source contingency is descriptive. A fitted source-only/normalized-format comparison must be separately present in the accepted execution settings."}


def research_summaries(result, context):
    """Recompute source slices with the actual fold-specific decisions."""
    decision = {(r["configuration"], r["observation_id"]): r["decision"] for r in result["decision_records"]}
    by_source = {}
    for configuration in result["request"]["configurations"]:
        by_source[configuration] = {}
        for source in sorted(set(context.sources_by_id.values())):
            rows = [r for r in result["oof_predictions"] if r["configuration"] == configuration
                    and context.sources_by_id[r["observation_id"]] == source]
            y = tuple(r["target"] for r in rows)
            p = tuple(r["score"] for r in rows)
            metrics = binary_metrics(y, p, positive_label=1, threshold=.5, probabilities=p,
                                     calibration_edges=result["request"]["calibration_edges"])
            operating = binary_metrics(y, tuple(decision[(configuration, r["observation_id"])] for r in rows), positive_label=1, threshold=.5)
            for key in ("confusion_matrix", "precision", "recall", "f1", "balanced_accuracy", "mcc"):
                metrics[key] = operating[key]
            metrics["threshold"] = "fold_specific_training_policy"
            by_source[configuration][source] = metrics
    summary = {"source_stratified_metrics": by_source, "source_independent_performance_established": False,
               "final_evaluation_performed": False}
    if result["request"]["family"] == "logistic_regression" and {"E1", "E3"} <= set(result["request"]["configurations"]):
        e1 = {r["observation_id"]: r for r in result["oof_predictions"] if r["configuration"] == "E1"}
        e3 = {r["observation_id"]: r for r in result["oof_predictions"] if r["configuration"] == "E3"}
        ids = sorted(e1)
        summary["confirmatory_representation_contrast"] = paired_group_bootstrap(
            tuple(e1[i]["target"] for i in ids), tuple(e3[i]["score"] for i in ids), tuple(e1[i]["score"] for i in ids),
            tuple(e1[i]["group_id"] for i in ids), positive_label=1, resamples=2000, confidence=.95,
            seed=result["request"]["seed"])
        summary["confirmatory_claim_limitation"] = context.exposure_disposition
    return summary


def launch(checkout, input_run_id, *, expected_authorization_sha256, execute=False, purpose="fit"):
    if purpose not in {"fit", "ablation"}:
        raise InputContractError("explicit_launcher_scope_required")
    context, dataset, specification = verify_accepted_run(checkout, input_run_id,
        expected_authorization_sha256=expected_authorization_sha256, purpose=purpose)
    from ml.run_preflight import verified_run_report
    dry_run = verified_run_report(checkout, context, dataset, specification)
    summary = {"status": "accepted_inputs_verified", "fitting_performed": False,
        "branch": context.branch, "input_fingerprint": context.input_fingerprint,
        "authorization_sha256": context.authorization_sha256, "fit_estimate": fit_estimate(specification),
        "output_run_id": context.output_run_id, "final_evaluation_authorized": False,
        "source_diagnostics": source_diagnostics(dataset, context), "dry_run": dry_run}
    if not execute:
        return summary
    # Same nested engine as synthetic verification. No research-to-synthetic
    # relabeling and no alternate training pipeline hidden in this launcher.
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        result, fitted = run_research_nested_cv(dataset, specification, execution_context=context)
    result["source_diagnostics"] = summary["source_diagnostics"]
    result["research_summaries"] = research_summaries(result, context)
    result["implementation_benchmark"] = benchmark_outer_models(fitted, dataset, context)
    context.check_budget()
    output = _within(Path(checkout).resolve(), "experiments/runs/"+context.output_run_id)
    digest = write_nested_bundle(output, result, fitted,
        code_reference="accepted-code-map:"+fingerprint(context.code_sha256), code_hashes=context.code_sha256,
        execution_context=context)
    load_nested_bundle(output, expected_manifest_sha256=digest, max_bytes=500_000_000, execution_context=context)
    return dict(summary, status="authorized_development_run_completed", fitting_performed=True,
                run_manifest_sha256=digest, base_fits=result["base_fits"], calibration_fits=result["calibration_fits"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--input-run-id", required=True)
    parser.add_argument("--authorization-sha256", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--purpose", choices=("fit", "ablation"), default="fit")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.execute and not args.worker:
            # The public CLI bounds the whole worker, including a native fit
            # that cannot be interrupted by between-fit checks. No shell, no
            # job/partition retries, no forceful repository operations.
            context, _, _ = verify_accepted_run(args.root, args.input_run_id,
                expected_authorization_sha256=args.authorization_sha256, purpose=args.purpose)
            command = [sys.executable, "-B", "-m", "ml.research_execution", "--root", str(Path(args.root).resolve()),
                "--input-run-id", args.input_run_id, "--authorization-sha256", args.authorization_sha256, "--purpose", args.purpose, "--execute", "--worker"]
            try:
                process = subprocess.run(command, cwd=Path(__file__).resolve().parents[1], capture_output=True,
                    text=True, timeout=context.budget["max_seconds"],
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except subprocess.TimeoutExpired:
                print(json.dumps({"status":"FAILED", "code":"research_worker_wall_time_exceeded", "fitting_performed":None,
                    "completed_result_verified":False, "note":"Worker terminated; do not treat partial files as a completed experiment."}))
                return 2
            if process.returncode != 0:
                print(json.dumps({"status":"FAILED", "code":"research_worker_failed", "fitting_performed":None,
                    "completed_result_verified":False}))
                return 2
            try:
                result = json.loads(process.stdout)
                if result["status"] != "authorized_development_run_completed":
                    raise ValueError
            except (ValueError, KeyError, TypeError):
                raise InputContractError("research_worker_completion_invalid") from None
            print(json.dumps(result))
            return 0
        result = launch(args.root, args.input_run_id, expected_authorization_sha256=args.authorization_sha256, execute=args.execute, purpose=args.purpose)
    except InputContractError as error:
        print(json.dumps({"status": "BLOCKED_OR_FAILED", "code": str(error), "fitting_performed": None,
                          "note": "Failure is not permission to substitute inputs, shrink the grid or use historical test outcomes."}))
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
