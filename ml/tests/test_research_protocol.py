"""Fixture-only acceptance mechanics; no real acceptance or research fitting."""
from dataclasses import replace
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil

import pytest

from ml.development_experiments import load_development_dataset
from ml.development_runner import dataset_fingerprint
from ml.experiment_engine import run_research_nested_cv, run_synthetic_nested_cv
from ml.experiment_inputs import InputContractError
from ml.metadata import canonical_json, fingerprint
from ml.preflight import require_research_fitting, research_fit_gate
from ml.research_protocol import (FILES, VERSION, code_hashes, prospective_id, specification_record,
    fit_estimate, verify_accepted_run, VerifiedResearchRun)
from ml.research_execution import launch
from ml.tests.test_uci_preparation import synthetic
from ml.uci_preparation import prepare_uci_handoff
from ml.tests.test_experiment_engine import spec


def fixture_packet(root):
    # Copy only code for identity checking, never any existing research files.
    source = Path(__file__).resolve().parents[2]
    from importlib import metadata
    packages = ("numpy", "scipy", "scikit-learn", "xgboost", "skops", "joblib", "threadpoolctl")
    try:
        environment = {p: metadata.version(p) for p in packages}
    except metadata.PackageNotFoundError:
        pytest.skip("isolated scientific packages required for environment identity fixtures")
    for relative in code_hashes(source):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, target)
    rows, assignments, _, dictionary = synthetic()
    dictionary = replace(dictionary, protocol_reference="research:verifier-fixture-only-not-actual-approval")
    snapshot = "e"*64
    mapping = {r["observation_id"]: prospective_id("UCI Phishing Websites", snapshot, "fixture.arff", i) for i, r in enumerate(assignments)}
    population = []
    for i, row in enumerate(assignments):
        row["observation_id"] = mapping[row["observation_id"]]
        population.append(dict(observation_id=row["observation_id"], source_dataset=row["source_dataset"], source_row_id=i,
            snapshot_sha256=snapshot, source_file="fixture.arff", native_label=-1 if row["target"] else 1, target=row["target"]))
    for row in rows:
        row["observation_id"] = mapping[row["observation_id"]]
    run_id = "synthetic-verifier-input"
    prepare_uci_handoff(root, run_id, rows, assignment_manifest=assignments,
        expected_observation_ids=frozenset(mapping.values()), specification=dictionary)
    dataset = load_development_dataset(root, run_id, specification=dictionary)
    protocol = root / "experiments/runs" / run_id / "protocol"
    protocol.mkdir()
    experiment = replace(spec(configs=("U1",)), protocol_reference="research:verifier-fixture-only-not-actual-approval")
    code = code_hashes(root)
    values = {
        "source_audit.json": {"category": "ACTUAL SOURCE AUDIT; NOT A MODEL RESULT", "source_records": len(assignments),
            "model_fits": 0, "snapshot_sha256": snapshot, "dataset": "UCI Phishing Websites", "source_file": "fixture.arff", "fixture_note": "SYNTHETIC verifier fixture; not an actual-data audit"},
        "population.json": {"records": population, "branch": "UCI", "identity_policy": "snapshot-original-position-sha256-v1",
            "source_label_mappings": [{"source_dataset": "UCI Phishing Websites", "native": native, "target": target,
                "meaning": meaning, "primary_source_reference": "synthetic:fixture-native-meaning-not-UCI-evidence"}
                for native, target, meaning in ((-1, 1, "phishing"), (1, 0, "legitimate"))]},
        "screening.json": {"eligible_population_fingerprint": fingerprint(population), "excluded_by_primary_reason": {}},
        "dictionary.json": {"dataset": "UCI", "conventional": [{"name": c.name, "kind": c.kind} for c in dictionary.conventional],
            "protocol_reference": dictionary.protocol_reference, "feature_dictionary_reference": dictionary.feature_dictionary_reference},
        "feature_freeze.json": {"code_sha256": code, "rule_language_availability_reference": "synthetic:U1-unavailable",
            "group_policy_reference": "synthetic:supplied-pairs", "grouping_limitations": ["No domain/campaign facts in fixture"], "data_scope": "development_only"},
        "experiment.json": specification_record(experiment),
        "selection.json": {"primary_pr_auc": "noninterpolated_average_precision_pooled_oof", "bootstrap_resamples": 2000,
            "confidence": .95, "delta_pr": .01, "delta_pr_justification": "synthetic fixture only, not a research recommendation",
            "candidate_families": ["logistic_regression", "linear_svm", "random_forest", "xgboost"],
            "benchmark_protocol_reference": "synthetic:test", "srs_disposition": "synthetic:no SRS limit invented"},
        "environment.json": environment,
    }
    values["selection.json"]["policy"] = dict(families=["logistic_regression", "linear_svm", "random_forest", "xgboost"],
        configuration="U1", delta_pr=.01, resamples=2000, confidence=.95, seed=17,
        hard_limits={n:None for n in ("minimum_recall", "minimum_precision", "maximum_p95_ms", "maximum_memory_bytes")},
        memory_evidence="unavailable_allowed_without_limit", calibration_order=["brier_score", "ece"],
        efficiency_order=["p95_batch_ms", "throughput_artifacts_per_second", "measured_memory_bytes_max", "serialized_model_bytes"],
        protocol_reference=experiment.protocol_reference)
    values["selection.json"]["benchmark"] = dict(warmup=1, repetitions=2, batch_size=1, thread_reference="synthetic:threads-one",
        hardware_reference="synthetic:CPU-fixture-not-a-physical-hardware-claim", payload_class="synthetic-U1", cold_warm="warm")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=tuple(assignments[0]))
    writer.writeheader(); writer.writerows(assignments)
    (protocol / "assignments.csv").write_text(stream.getvalue(), encoding="utf-8", newline="")
    for name in ("source_audit.json", "dictionary.json"):
        (protocol / name).write_text(canonical_json(values[name]), encoding="utf-8")
    sha = lambda name: hashlib.sha256((protocol / name).read_bytes()).hexdigest()
    for name in ("population.json", "screening.json"):
        values[name]["source_audit_sha256"] = sha("source_audit.json")
    values["feature_freeze.json"].update(assignment_sha256=sha("assignments.csv"), dictionary_sha256=sha("dictionary.json"))
    for name, value in values.items():
        (protocol / name).write_text(canonical_json(value), encoding="utf-8")
    evidence = {name: sha(name) for name in FILES if name != "development_input_manifest.json"}
    evidence["development_input_manifest.json"] = hashlib.sha256((protocol.parent / "data/processed/features/development/development_input_manifest.json").read_bytes()).hexdigest()
    acceptance = {"version": VERSION, "boundary": "E-development-fitting-only", "authority": {
        "name": "Synthetic verifier fixture", "role": "researcher", "date": "2026-01-01",
        "response_reference": "synthetic:test-fixture-not-user-approval", "response_text": "SYNTHETIC TEST RECORD ONLY: exercise exact-run verification; not an actual approval or research result."},
        "input_run_id": run_id, "output_run_id": "synthetic-verifier-output", "branch": "UCI", "evidence_sha256": evidence,
        "code_sha256": code, "input_fingerprint": dataset_fingerprint(dataset),
        "budget": {"max_base_fits": 105, "max_calibration_fits": 5, "max_seconds": 60, "max_training_rows": 10, "threads": 1},
        "exposure_disposition": "exploratory_previously_exposed"}
    path = protocol / "acceptance.json"
    path.write_text(canonical_json(acceptance), encoding="utf-8")
    return protocol, acceptance, hashlib.sha256(path.read_bytes()).hexdigest(), run_id, dataset, experiment


def test_complete_fixture_verification_has_no_fit_or_output_and_binds_once(tmp_path):
    protocol, receipt, digest, run_id, dataset, experiment = fixture_packet(tmp_path)
    context, loaded, settings = verify_accepted_run(tmp_path, run_id, expected_authorization_sha256=digest)
    assert dataset_fingerprint(loaded) == dataset_fingerprint(dataset)
    assert fit_estimate(settings) == {"base_fits": 105, "calibration_fits": 5}
    assert research_fit_gate(context)["research_fitting_enabled"]
    assert not research_fit_gate(context)["final_evaluation_authorized"]
    summary = launch(tmp_path, run_id, expected_authorization_sha256=digest)
    assert summary["fitting_performed"] is False
    assert not (protocol.parent.parent / receipt["output_run_id"]).exists()
    context.bind(loaded, settings)
    with pytest.raises(InputContractError, match="single_use"):
        context.bind(loaded, settings)
    context.before_fit("base", 8)
    with pytest.raises(InputContractError, match="row_budget"):
        context.before_fit("base", 11)


@pytest.mark.parametrize("case", ("wrong_digest", "boolean_approval", "wrong_boundary", "changed_code", "changed_assignment",
    "bad_screening", "source_relabel", "wrong_input", "too_many_fits", "wrong_bootstrap", "source_locator", "group_crossing"))
def test_invalid_evidence_never_reaches_fit_or_creates_output(tmp_path, case, monkeypatch):
    protocol, receipt, digest, run_id, dataset, experiment = fixture_packet(tmp_path)
    def fail(*args, **kwargs):
        pytest.fail("Invalid evidence reached an estimator")
    monkeypatch.setattr("ml.classifier_adapters.FoldClassifier.fit", fail)
    if case == "wrong_digest": digest = "0"*64
    elif case == "boolean_approval": receipt = {"approved": True}
    elif case == "wrong_boundary": receipt["boundary"] = "B-no-fit-audit"
    elif case == "changed_code": (tmp_path / "ml/classifier_adapters.py").write_text("# changed")
    elif case == "changed_assignment": (protocol / "assignments.csv").write_text("changed")
    elif case == "wrong_input": receipt["input_fingerprint"] = "0"*64
    elif case == "too_many_fits": receipt["budget"]["max_base_fits"] = 104
    else:
        name = {"bad_screening": "screening.json", "source_relabel": "population.json", "wrong_bootstrap": "selection.json",
                "source_locator": "population.json", "group_crossing": "assignments.csv"}[case]
        if case == "group_crossing":
            rows = list(csv.DictReader((protocol / name).open(newline="")))
            rows[-1]["group_id"] = rows[0]["group_id"]
            stream = io.StringIO(newline=""); writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]));writer.writeheader();writer.writerows(rows)
            (protocol / name).write_text(stream.getvalue(), newline="")
        else:
            value = json.loads((protocol / name).read_bytes())
            if case == "bad_screening": value["excluded_by_primary_reason"] = {"invented": 1}
            elif case == "source_relabel": value["source_label_mappings"][0]["meaning"] = "spam"
            elif case == "source_locator": value["records"][0]["source_row_id"] = 999
            elif case == "wrong_bootstrap": value["bootstrap_resamples"] = 25
            (protocol / name).write_text(canonical_json(value))
        receipt["evidence_sha256"][name] = hashlib.sha256((protocol / name).read_bytes()).hexdigest()
    if case != "wrong_digest":
        (protocol / "acceptance.json").write_text(canonical_json(receipt))
        digest = hashlib.sha256((protocol / "acceptance.json").read_bytes()).hexdigest()
    with pytest.raises(InputContractError):
        launch(tmp_path, run_id, expected_authorization_sha256=digest, execute=True)
    assert not (protocol.parent.parent / "synthetic-verifier-output").exists()


def test_research_context_checks_exact_input_before_shared_engine(tmp_path, monkeypatch):
    _, _, digest, run_id, _, _ = fixture_packet(tmp_path)
    context, dataset, settings = verify_accepted_run(tmp_path, run_id, expected_authorization_sha256=digest)
    called = []
    def shared(*args, **kwargs):
        called.append(kwargs)
        return {"fixture": "not an actual research fit"}, ()
    monkeypatch.setattr("ml.experiment_engine._run_nested_cv", shared)
    with pytest.raises(InputContractError, match="synthetic_protocol"):
        run_synthetic_nested_cv(dataset, settings)
    with pytest.raises(InputContractError, match="not_authorized"):
        run_research_nested_cv(dataset, settings, execution_context={"approved": True})
    run_research_nested_cv(dataset, settings, execution_context=context)
    assert len(called) == 1 and called[0]["execution_context"] is context
    other = replace(context, _token=object())
    with pytest.raises(InputContractError, match="not_authorized"):
        require_research_fitting(other)
