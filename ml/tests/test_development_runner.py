"""Synthetic runner callback isolation, matching and immutable bundle checks."""
from dataclasses import replace
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from ml.development_experiments import (
    CLASSIFIER_FAMILIES, DevelopmentSpecification, FeatureColumn, behavioral_columns,
    build_development_dataset,
)
from ml.development_runner import (
    CVSpecification, ScoreBatch, run_synthetic_cv, dimension_ablations,
    compare_synthetic_results, slice_synthetic_metrics, write_synthetic_bundle, verify_synthetic_bundle,
)
from ml.experiment_inputs import InputContractError


def synthetic_dataset(branch="Email"):
    """Artificial target-correlated signal; never represents thesis performance."""
    spec = DevelopmentSpecification(branch, (FeatureColumn("signal", "numeric"), FeatureColumn("record_code", "numeric")),
                                    "synthetic-protocol", "synthetic-dictionary")
    records, vectors = [], []
    for fold in range(1, 6):
        for target in (0, 1):
            pos = len(records)
            source = ("Nazario" if target else "Enron") if branch == "Email" else (
                "PhiUSIIL" if branch == "PhiUSIIL" else "UCI Phishing Websites")
            native = target if branch == "Email" else (1 - target if branch == "PhiUSIIL" else (1 if target == 0 else -1))
            row = dict(observation_id=f"synthetic-{pos}", source_dataset=source, source_row_id=pos,
                target=target, group_id=f"supplied-pair-{fold}", partition="development", cv_fold=fold,
                signal=target, record_code=pos)
            row["Result" if branch == "UCI" else "label"] = native
            if branch == "Email": row.update(subject="synthetic", body="synthetic", language="en")
            vector = {k: row[k] for k in ("observation_id", "target", "group_id", "partition", "cv_fold")}
            vector.update({c: 0 for c in behavioral_columns()})
            if branch == "Email":
                vector.update({c: 1 for c in behavioral_columns()[4:]})
                vector[behavioral_columns()[0]] = target
            records.append(row);vectors.append(vector)
    return build_development_dataset(records, vectors, specification=spec)


def request(**changes):
    base = CVSpecification("logistic_regression", ("E1", "E2", "E3"), 7, .5, {"stub": True},
                           "synthetic:deterministic_recording_stub", "synthetic fixed comparable scale",
                           (0, .5, 1))
    return replace(base, **changes)


class RecordingPipeline:
    def __init__(self, log, config, fold):
        self.log, self.config, self.fold = log, config, fold
    def fit(self, x, y, *, feature_names, seed):
        self.log.append(("fit", self.config, self.fold, x, y, feature_names, seed))
    def score(self, x, *, observation_ids):
        self.log.append(("score", self.config, self.fold, x, observation_ids))
        # Reordered returned IDs exercise identity-based join, not positional zip.
        scores = tuple(.2 + .6 * row[0] for row in x)
        return ScoreBatch(tuple(reversed(observation_ids)), tuple(reversed(scores)), "probability", 1,
                          tuple(reversed(scores)))


def factory_for(log):
    return lambda family, config, fold, seed, parameters: RecordingPipeline(log, config, fold)


def test_matched_folds_fresh_callbacks_and_oof_identity_without_validation_labels():
    dataset = synthetic_dataset()
    before = deepcopy(dataset.observations)
    log = []
    result = run_synthetic_cv(dataset, request(), factory=factory_for(log))
    assert dataset.observations == before
    assert result["result_category"] == "SYNTHETIC RESULT" and result["research_execution"] == "BLOCKED"
    assert result["calibration_fits"] == 0 and not result["selection_performed"]
    assert len(result["fold_reports"]) == 15 and len(result["oof_predictions"]) == 30
    for config in ("E1", "E2", "E3"):
        predictions = [r for r in result["oof_predictions"] if r["configuration"] == config]
        assert {(r["observation_id"], r["fold"], r["group_id"]) for r in predictions} == {
            (r.observation_id, r.fold, r.group_id) for r in dataset.observations}
        assert all(r["score"] == pytest.approx(.2 + .6 * r["target"]) for r in predictions)
        for fold in range(1, 6):
            fit = next(r for r in log if r[:3] == ("fit", config, fold))
            scored = next(r for r in log if r[:3] == ("score", config, fold))
            assert len(fit[3]) == 8 and len(fit[4]) == 8 and len(scored[3]) == 2
            assert set(scored[4]) == {r.observation_id for r in dataset.observations if r.fold == fold}
            assert not {"target", "group_id", "cv_fold", "source_dataset"} & set(fit[5])
            if config != "E2":
                assert {row[1] for row in fit[3]}.isdisjoint({row[1] for row in scored[3]})
    assert result["pooled_metrics"]["E3"]["average_precision"] == 1


@pytest.mark.parametrize("family", CLASSIFIER_FAMILIES)
def test_all_family_slots_work_with_explicit_synthetic_stub_only(family):
    result = run_synthetic_cv(synthetic_dataset(), request(family=family), factory=factory_for([]))
    assert result["request"]["family"] == family
    assert result["request"]["implementation_reference"].startswith("synthetic:")


@pytest.mark.parametrize("branch", ["UCI", "PhiUSIIL"])
def test_technical_branches_run_only_u1_and_no_behavioral_ablations(branch):
    ds = synthetic_dataset(branch)
    r = run_synthetic_cv(ds, request(configurations=("U1",)), factory=factory_for([]))
    assert set(r["pooled_metrics"]) == {"U1"}
    assert all(f["feature_names"] == ["signal", "record_code"] for f in r["fold_reports"])
    with pytest.raises(InputContractError):
        dimension_ablations(ds)
    with pytest.raises(InputContractError):
        run_synthetic_cv(ds, request(), factory=lambda *args: pytest.fail("invalid config reached factory"))


@pytest.mark.parametrize("change", [
    {"family": "transformer"}, {"configurations": ()}, {"configurations": ("E1", "E1")},
    {"seed": True}, {"threshold": float("nan")}, {"parameters": None},
    {"implementation_reference": "sklearn real model"}, {"score_comparability_reference": ""},
    {"omitted_features": ("signal", "signal")}, {"calibration_edges": (0, 1, 1)},
])
def test_invalid_specifications_fail(change):
    with pytest.raises((InputContractError, ValueError)):
        request(**change)


def test_invalid_omissions_and_fold_metadata_fail_before_callbacks():
    ds = synthetic_dataset()
    called = lambda *args: pytest.fail("invalid input reached factory")
    for omitted in (("unapproved_field",), ("signal", "record_code")):
        with pytest.raises(InputContractError):
            run_synthetic_cv(ds, request(configurations=("E1",), omitted_features=omitted), factory=called)
    for bad in (replace(ds.observations[0], fold=6), replace(ds.observations[0], target=True),
                replace(ds.observations[0], conventional=(0,)), replace(ds.observations[0], behavioral=(0,) * 7)):
        with pytest.raises(InputContractError):
            run_synthetic_cv(replace(ds, observations=(bad, *ds.observations[1:])), request(), factory=called)


def test_pipeline_reuse_is_rejected():
    pipeline = RecordingPipeline([], "E1", 1)
    with pytest.raises(InputContractError, match="fresh_fold_pipeline_required"):
        run_synthetic_cv(synthetic_dataset(), request(), factory=lambda *args: pipeline)


@pytest.mark.parametrize("difference", ["implementation", "preprocessing", "partial_record"])
def test_representation_comparison_holds_recorded_pipeline_policy_fixed(difference):
    left = run_synthetic_cv(synthetic_dataset(), request(), factory=factory_for([]))
    left["pipeline_records"] = [{"configuration": config, "fold": fold,
        "pipeline": {"preprocessing": {"numeric_scaling": "none"}}}
        for config in ("E1", "E2", "E3") for fold in range(1, 6)]
    right = deepcopy(left)
    if difference == "implementation":
        right["request"]["implementation_reference"] = "synthetic:different-implementation"
    elif difference == "preprocessing":
        for record in right["pipeline_records"]:
            record["pipeline"]["preprocessing"]["numeric_scaling"] = "standard"
    else:
        right["pipeline_records"] = []
    with pytest.raises(InputContractError):
        compare_synthetic_results(left, right, left_configuration="E1", right_configuration="E3")


def test_callback_errors_are_sanitized_and_no_partial_result_returned():
    def broken(*args):
        raise RuntimeError("SENSITIVE SYNTHETIC CONTENT")
    with pytest.raises(InputContractError, match="^synthetic_pipeline_callback_failed$") as error:
        run_synthetic_cv(synthetic_dataset(), request(), factory=broken)
    assert error.value.__suppress_context__


@pytest.mark.parametrize("change", [
    {"observation_ids": ("x", "x")}, {"observation_ids": ("x",)}, {"scores": (.1,)},
    {"scores": (float("nan"), .8)}, {"positive_label": 0},
    {"score_kind": "unknown"}, {"score_kind": "probability", "scores": (-1, 2)},
    {"probabilities": (0, 2)},
])
def test_malformed_or_misaligned_scores_fail(change):
    class Bad(RecordingPipeline):
        def score(self, x, *, observation_ids):
            args = dict(observation_ids=observation_ids, scores=(.2, .8), score_kind="probability", positive_label=1)
            args.update(change)
            return ScoreBatch(**args)
    with pytest.raises(InputContractError):
        run_synthetic_cv(synthetic_dataset(), request(), factory=lambda *args: Bad([], "E1", 1))


def test_behavioral_and_explicit_feature_family_ablations_preserve_population():
    ds = synthetic_dataset()
    base = run_synthetic_cv(ds, request(configurations=("E3",)), factory=factory_for([]))
    for dimension, columns in dimension_ablations(ds).items():
        ablated = run_synthetic_cv(ds, request(configurations=("E3",), omitted_features=columns), factory=factory_for([]))
        assert all(not set(columns) & set(f["feature_names"]) for f in ablated["fold_reports"])
        assert all(len(f["feature_names"]) == 8 for f in ablated["fold_reports"])
        paired = compare_synthetic_results(base, ablated, left_configuration="E3", right_configuration="E3")
        assert paired["observations"] == 10 and not paired["selection_performed"]
    feature_ablated = run_synthetic_cv(ds, request(configurations=("E1",), omitted_features=("record_code",)), factory=factory_for([]))
    assert all(f["feature_names"] == ["signal"] for f in feature_ablated["fold_reports"])


def test_comparison_refuses_different_populations_or_metadata():
    r = run_synthetic_cv(synthetic_dataset(), request(), factory=factory_for([]))
    wrong = deepcopy(r);wrong["input_fingerprint"] = "another"
    with pytest.raises(InputContractError):
        compare_synthetic_results(r, wrong, left_configuration="E1", right_configuration="E3")
    wrong = deepcopy(r)
    next(x for x in wrong["oof_predictions"] if x["configuration"] == "E3")["fold"] = 5
    with pytest.raises(InputContractError):
        compare_synthetic_results(r, wrong, left_configuration="E1", right_configuration="E3")


def test_source_slices_preserve_one_class_undefined_metrics():
    ds = synthetic_dataset()
    r = run_synthetic_cv(ds, request(), factory=factory_for([]))
    slices = {row.observation_id: "positive_source" if row.target else "negative_source" for row in ds.observations}
    report = slice_synthetic_metrics(r, "E1", slices_by_id=slices)
    assert report["slices"]["positive_source"]["roc_auc"] is None
    assert report["slices"]["negative_source"]["average_precision"] is None
    assert not report["source_independence_established"]
    with pytest.raises(InputContractError):
        slice_synthetic_metrics(r, "E1", slices_by_id={})


@pytest.mark.parametrize("change", [{"seed": 8}, {"score_comparability_reference": "different"},
    {"family": "random_forest"}, {"parameters": {"stub": False}}])
def test_representation_comparison_requires_matching_controls_and_classifier(change):
    ds = synthetic_dataset()
    a = run_synthetic_cv(ds, request(), factory=factory_for([]))
    b = run_synthetic_cv(ds, request(**change), factory=factory_for([]))
    with pytest.raises(InputContractError):
        compare_synthetic_results(a, b, left_configuration="E1", right_configuration="E3")


def test_immutable_bundle_roundtrip_hashes_and_no_raw_features(tmp_path):
    r = run_synthetic_cv(synthetic_dataset(), request(), factory=factory_for([]))
    folder = tmp_path / "synthetic-smoke"
    write_synthetic_bundle(folder, r, code_reference="synthetic-code", code_hashes={"test.py": "a" * 64})
    manifest = verify_synthetic_bundle(folder)
    assert set(p.name for p in folder.iterdir()) == {"manifest.json", "metrics.json", "oof_predictions.csv"}
    assert manifest["result_category"] == "SYNTHETIC RESULT"
    assert "conventional" not in (folder / "oof_predictions.csv").read_text()
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    with pytest.raises(InputContractError):
        write_synthetic_bundle(folder, r, code_reference="synthetic-code", code_hashes={"test.py": "a" * 64})
    assert before == {p.name: p.read_bytes() for p in folder.iterdir()}
    (folder / "metrics.json").write_text("{}")
    with pytest.raises(InputContractError, match="synthetic_output_hash_mismatch"):
        verify_synthetic_bundle(folder)


def test_late_bundle_write_failure_leaves_no_manifest_or_partial_bundle(tmp_path, monkeypatch):
    r = run_synthetic_cv(synthetic_dataset(), request(), factory=factory_for([]))
    original = Path.open
    def fail(path, mode="r", *args, **kwargs):
        if path.name == "manifest.json" and mode == "xb": raise OSError("synthetic failure")
        return original(path, mode, *args, **kwargs)
    monkeypatch.setattr(Path, "open", fail)
    with pytest.raises(InputContractError, match="synthetic_bundle_write_failed"):
        write_synthetic_bundle(tmp_path / "failed", r, code_reference="synthetic-code", code_hashes={"test.py": "a" * 64})
    assert list(tmp_path.iterdir()) == []


def test_manifest_cannot_redirect_verifier_to_arbitrary_files(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({"result_category": "SYNTHETIC RESULT",
        "research_execution": "BLOCKED", "outputs": {"../historical.csv": "a" * 64}}))
    with pytest.raises(InputContractError, match="invalid_synthetic_manifest"):
        verify_synthetic_bundle(tmp_path)

