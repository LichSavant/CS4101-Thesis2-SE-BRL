"""Explicit synthetic demonstration; no corpus input or research estimator.

Run with -B and an unused --directory whose parent exists. The artificial signal
equals a constructed target solely to exercise plumbing. Its metrics must never
be reported as empirical thesis performance.
"""
import argparse
import hashlib
import json
from pathlib import Path

from ml.development_experiments import (
    DevelopmentSpecification, FeatureColumn, behavioral_columns, build_development_dataset,
)
from ml.development_runner import (
    CVSpecification, ScoreBatch, run_synthetic_cv, dimension_ablations,
    compare_synthetic_results, write_synthetic_bundle, verify_synthetic_bundle,
)
from ml.inference_benchmark import benchmark_synthetic_inference


def fixture(branch="Email"):
    spec = DevelopmentSpecification(branch, (FeatureColumn("fixture_signal", "numeric"),
        FeatureColumn("fixture_row_index", "numeric")), "synthetic-only", "synthetic-only")
    rows, vectors = [], []
    for fold in range(1, 6):
        for target in (0, 1):
            pos = len(rows)
            source = ("Nazario" if target else "Enron") if branch == "Email" else "UCI Phishing Websites"
            row = dict(observation_id=f"synthetic-{pos}", target=target, source_dataset=source, source_row_id=pos,
                group_id=f"synthetic-supplied-pair-{fold}", partition="development", cv_fold=fold,
                fixture_signal=target, fixture_row_index=pos)
            row["label" if branch == "Email" else "Result"] = target if branch == "Email" else (1 if target == 0 else -1)
            if branch == "Email":
                row.update(subject="synthetic fixture", body="synthetic fixture", language="en")
            vector = {key: row[key] for key in ("observation_id", "target", "group_id", "partition", "cv_fold")}
            vector.update({c: 0 for c in behavioral_columns()})
            if branch == "Email":
                vector.update({c: 1 for c in behavioral_columns()[4:]})
                vector[behavioral_columns()[0]] = target
            rows.append(row);vectors.append(vector)
    return build_development_dataset(rows, vectors, specification=spec)


class SyntheticScoringStub:
    """No optimization; fit only accepts the training portion delivered to it."""
    def fit(self, rows, labels, *, feature_names, seed):
        if len(rows) != len(labels):
            raise ValueError("synthetic training width mismatch")
    def score(self, rows, *, observation_ids):
        values = tuple(.2 + .6 * row[0] for row in rows)
        return ScoreBatch(observation_ids, values, "probability", 1, values)


def demonstrate(directory, *, code_reference):
    dataset = fixture()
    def request(configurations, omitted=()):
        return CVSpecification("logistic_regression", configurations, 7, .5, {"stub_only": True},
            "synthetic:no-optimization-scoring-stub", "synthetic fixed comparable scale",
            (0, .5, 1), omitted)
    factory = lambda *args: SyntheticScoringStub()
    result = run_synthetic_cv(dataset, request(("E1", "E2", "E3")), factory=factory)
    ablations = {}
    for name, columns in dimension_ablations(dataset).items():
        variant = run_synthetic_cv(dataset, request(("E3",), columns), factory=factory)
        ablations[name] = compare_synthetic_results(result, variant,
            left_configuration="E3", right_configuration="E3")
    technical = run_synthetic_cv(fixture("UCI"), request(("U1",)), factory=factory)
    result["dimension_ablation_smoke"] = ablations
    result["technical_u1_smoke"] = {"result_category": "SYNTHETIC RESULT",
        "observations": len(technical["oof_predictions"]), "configurations": list(technical["pooled_metrics"]),
        "input_fingerprint": technical["input_fingerprint"]}
    result["efficiency_smoke"] = benchmark_synthetic_inference(lambda rows: tuple(.5 for _ in rows),
        ((1., 0.),), warmup=1, repetitions=5, batch_size=1,
        thread_reference="synthetic single-process callback; external threads not controlled")
    root = Path(__file__).resolve().parent
    hashes = {str(p.relative_to(root.parent)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (root / "synthetic_demo.py", root / "development_runner.py", root / "evaluation_metrics.py",
                  root / "inference_benchmark.py", root / "development_experiments.py",
                  root / "notebook_contracts.py", root / "se_brl/codebook.v0.1.0.json")}
    manifest = write_synthetic_bundle(directory, result, code_reference=code_reference, code_hashes=hashes)
    verify_synthetic_bundle(directory)
    return {"result_category": "SYNTHETIC RESULT", "manifest": str(manifest),
            "oof_rows": len(result["oof_predictions"]), "dimension_ablation_checks": len(ablations),
            "technical_u1_observations": 10, "actual_research_models_fitted": 0,
            "synthetic_stub_fit_calls": 40, "research_execution": "BLOCKED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--code-reference", required=True)
    args = parser.parse_args()
    print(json.dumps(demonstrate(args.directory, code_reference=args.code_reference), indent=2))


if __name__ == "__main__":
    main()

