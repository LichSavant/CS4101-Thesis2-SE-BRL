"""Create explicitly synthetic analytical bundles for offline system validation.

No corpus paths, training-selection claims or research-promotion option exists.
The small fixture dictionary is intentionally not a complete research baseline.
"""
import argparse
import hashlib
import json
from pathlib import Path

from ml.artifact_analysis import AnalyticalBundle, ArtifactAnalyzer, write_bundle, load_bundle
from ml.classifier_adapters import FoldClassifier, ClassifierSpecification, PreprocessingSpecification
from ml.decision import RiskPolicy
from ml.development_experiments import DevelopmentSpecification, FeatureColumn, behavioral_columns
from ml.experiment_engine import FittedSigmoid, SigmoidSpecification
from ml.genuine_classifier_smoke import synthetic_parameters
from ml.observed_features import observed_conventional
from ml.preprocessing import preprocess
from ml.se_brl.extraction import RuleEngine
from ml.se_brl.representation import BrlRepresentation


def fixture_artifact(dataset, index, target):
    if dataset == "UCI":
        return {"kind":"technical","dataset":"UCI","features":{"URL_Length":-1 if target else 1,"Redirect":target}}
    if dataset == "PhiUSIIL":
        return {"kind":"technical","dataset":"PhiUSIIL","features":{"URLLength":70 if target else 20,"IsDomainIP":target}}
    text = (("Act now. Submit your password. Pay this invoice. " if target else
             "Synthetic weekly meeting notes and project schedule. ") + f"Fixture item {index}.")
    return {"kind": "email", "subject": text} if dataset == "Email" else {"kind": "webpage", "visible_text": text}


def fixture_bundle(dataset="Email", family="logistic_regression"):
    if dataset not in {"Email", "Web", "UCI", "PhiUSIIL"}:
        raise ValueError("Synthetic supported fixture branch required")
    content = dataset in {"Email","Web"}
    columns = ((FeatureColumn("model_text", "text"), FeatureColumn("conventional:text_char_count", "numeric"),
                FeatureColumn("conventional:text_word_count", "numeric")) if content else
               tuple(FeatureColumn(n,"numeric") for n in fixture_artifact(dataset,0,0)["features"]))
    dictionary = DevelopmentSpecification(dataset, columns,
        "synthetic:system-integration-fixture", "synthetic:text-fixture-not-full-research-E1")
    text = dict(lowercase=True, ngram_range=(1, 1), min_df=1, max_df=1., max_features=100,
        sublinear_tf=False, norm="l2", strip_accents=None, analyzer="word", token_pattern=r"(?u)\b\w\w+\b", stop_words=None)
    model = FoldClassifier(dictionary, ClassifierSpecification(family, synthetic_parameters(family), 17),
        PreprocessingSpecification("reject", "standard", text if content else None), "E3" if content else "U1")
    def row(index, target):
        if not content:
            return tuple(fixture_artifact(dataset,index,target)["features"][n] for n in model.expected)
        artifact = preprocess(fixture_artifact(dataset, index, target))
        conventional = observed_conventional(artifact)
        behavioral = BrlRepresentation(RuleEngine().extract(artifact)).deterministic_slots
        values = dict(conventional.values) | dict(zip(behavioral_columns(), behavioral, strict=True))
        return tuple(values[n] for n in model.expected)
    labels = tuple(i % 2 for i in range(20))
    rows = tuple(row(i, y) for i, y in enumerate(labels))
    model.fit(rows, labels, feature_names=model.expected, seed=17)
    calibration_labels = tuple(i % 2 for i in range(10))
    scores = model.score(tuple(row(i+100, y) for i, y in enumerate(calibration_labels)),
        observation_ids=tuple(f"synthetic-calibration-{i}" for i in range(10)))
    spec = SigmoidSpecification(ClassifierSpecification("logistic_regression", synthetic_parameters("logistic_regression"), 17),
        "identity" if family == "linear_svm" else "logit_probability", 1e-6)
    calibrator = FittedSigmoid.fit(scores.scores, calibration_labels, spec)
    return AnalyticalBundle(model, calibrator, RiskPolicy(.35, .8, .5,
        "synthetic:fixture-thresholds-not-research-freeze", "synthetic_fixture"), .5,
        f"synthetic-{dataset.lower()}-{family}-1", "synthetic_fixture",
        {"URL_Length":(-1,0,1),"Redirect":(0,1)} if dataset == "UCI" else None)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    directory = Path(args.output)
    if directory.exists() or not directory.parent.is_dir():
        parser.error("Unused fixture root with an existing parent required")
    # Validate both in memory before any output is created.
    bundles = {dataset: fixture_bundle(dataset) for dataset in ("Email", "Web", "UCI", "PhiUSIIL")}
    directory.mkdir()
    receipts = {}
    reference = "synthetic_system.py SHA256 " + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for dataset, bundle in bundles.items():
        digest = write_bundle(directory / dataset.lower(), bundle, code_reference=reference)
        restored = load_bundle(directory / dataset.lower(), expected_manifest_sha256=digest, max_bytes=20_000_000)
        result = ArtifactAnalyzer({{"Email": "content_bearing_email", "Web": "content_bearing_webpage", "UCI":"UCI", "PhiUSIIL":"PhiUSIIL"}[dataset]: restored}).analyze(
            fixture_artifact(dataset, 500, 1), language="en")
        if result["status"] != "complete":
            raise RuntimeError("Synthetic roundtrip failed; no completed receipt written")
        receipts[dataset] = {"manifest_sha256": digest, "roundtrip_status": result["status"]}
    receipt = {"category": "SYNTHETIC RESULT", "research_models_fitted": 0,
               "fixture_base_classifier_fits": len(bundles), "fixture_calibrator_fits": len(bundles), "bundles": receipts}
    with (directory / "fixture_receipt.json").open("x", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)
    print(json.dumps(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
