import hashlib
from importlib import metadata
import json
from pathlib import Path
import subprocess
import sys

import pytest

from ml.preflight import check_environment, inspect_input, run_preflight, research_fit_gate, require_research_fitting


def put(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def notebook(root, name, cells):
    return put(root, f"experiments/notebooks/{name}.ipynb", json.dumps({"cells": [
        {"cell_type": "code", "id": cid, "source": source.splitlines(keepends=True), "outputs": []}
        for cid, source in cells
    ]}))


def installed(_):
    return "synthetic-version"


def snapshot(root):
    return {p.relative_to(root).as_posix(): (p.stat().st_mtime_ns, p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())
            for p in root.rglob("*") if p.is_file()}


def test_missing_files_and_lfs_pointers_do_not_become_csv_payloads(tmp_path):
    assert inspect_input(tmp_path, "missing.csv", ("hash",))["status"] == "missing"
    path = "fixtures/email.csv"
    put(tmp_path, path, "version https://git-lfs.github.com/spec/v1\noid sha256:" + "a" * 64 + "\nsize 999\n")
    report = inspect_input(tmp_path, path, ("hash", "subject"))
    assert report["status"] == "lfs_pointer" and report["declared_payload_bytes"] == 999
    assert "schema" not in report and "actual_sha256" not in report


def test_headers_required_fields_and_no_row_values(tmp_path):
    source = "experiments/datasets-raw/email/ceas_08/CEAS_08.csv"
    put(tmp_path, source, "subject,body,label\nDO-NOT-PRINT,DO-NOT-PRINT,1\n")
    result = run_preflight(tmp_path, version_lookup=installed)
    info = next(x for x in result["inputs"] if x["path"] == source)
    assert info["status"] == "header_compatible"
    assert "DO-NOT-PRINT" not in json.dumps(result)
    put(tmp_path, source, "subject,body\n")
    assert inspect_input(tmp_path, source, ("subject", "body", "label"))["missing_required_fields"] == ["label"]



def test_arff_inspection_stops_before_data_and_rejects_invalid_header(tmp_path):
    put(tmp_path, "fixture.arff", "@relation fixture\n@attribute 'Result' {-1,1}\n@data\nDO-NOT-PRINT\n")
    result = inspect_input(tmp_path, "fixture.arff", ("Result",))
    assert result["schema"] == ["Result"] and result["status"] == "header_compatible"
    put(tmp_path, "fixture.csv", "duplicate,duplicate\n")
    assert inspect_input(tmp_path, "fixture.csv")["status"] == "unreadable_or_invalid_metadata"


def test_migration_conflicts_and_stored_exceptions_are_metadata_only(tmp_path):
    notebook(tmp_path, "03_preprocessing", [
        ("new", 'email_binary["source_dataset"] = "SyntheticEmail"\nassert len(email_binary) == 12'),
        ("old", "assert len(email_binary) == 38759\nassert len(email_dev) == 27129"),
    ])
    notebook(tmp_path, "04_feature_extraction", [("urls", 'quality = email_features["urls"]')])
    put(tmp_path, "experiments/results/preprocessing/partitions/email_partition_manifest.csv",
        "observation_id,source_dataset,target,group_id,partition,cv_fold\na,Nazario,1,g,development,1\n")
    report = run_preflight(tmp_path, version_lookup=installed)
    codes = {i["code"] for i in report["issues"]}
    assert {"dataset_identity_conflict", "recorded_population_conflict", "conflicting_population_assumptions",
            "requires_email_urls",
            "development_population_conflict"} <= codes
    assert report["research_execution_authorized"] is False
    xgboost = next(item for item in report["optional_dependencies"] if item["package"] == "xgboost")
    assert xgboost["role"] == "genuine_offline_candidate; research_execution_not_authorized"
    assert xgboost["required_for_preflight"] is False
    assert all(not stage["can_run"] for stage in report["stages"])
    assert [a["rows"] for a in report["population_assumptions"]] == [12, 38759, 27129]


def test_syntax_errors_are_reported_without_executing_source(tmp_path):
    notebook(tmp_path, "01_data_audit", [("prose", "This is explanatory prose."),
                                           ("side-effect", 'raise RuntimeError("must not execute")')])
    report = run_preflight(tmp_path, version_lookup=installed)
    issue = next(x for x in report["issues"] if x["code"] == "notebook_syntax_error")
    assert issue["cell_id"] == "prose"
    assert report["notebooks"][0]["syntax"] == "invalid"


def test_processed_hash_verification_and_missing_inputs(tmp_path):
    relative = "experiments/data/processed/preprocessed/email_preprocessed.csv"
    p = put(tmp_path, relative, "observation_id,target,group_id,partition,cv_fold\na,0,g,development,1\n")
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = "dataset,input_type,filename,sha256\nemail,preprocessed,email_preprocessed.csv,{}\n"
    mpath = "experiments/results/experiments/input_manifest.csv"
    put(tmp_path, mpath, manifest.format(digest))
    report = run_preflight(tmp_path, version_lookup=installed)
    assert next(x for x in report["inputs"] if x["path"] == relative)["hash_status"] == "match"
    put(tmp_path, mpath, manifest.format("0" * 64))
    report = run_preflight(tmp_path, version_lookup=installed)
    assert any(x["code"] == "processed_hash_mismatch" for x in report["issues"])
    assert any(x["code"] == "processed_missing" for x in report["issues"])


def test_manifest_cannot_redirect_reads_to_holdout_or_outside_checkout(tmp_path):
    put(tmp_path, "experiments/results/experiments/input_manifest.csv",
        "dataset,input_type,filename,sha256\nemail,preprocessed,../../holdout_predictions.csv," + "a" * 64 + "\n")
    report = run_preflight(tmp_path, version_lookup=installed)
    assert any(i["code"] == "input_manifest_invalid_or_missing" for i in report["issues"])
    assert inspect_input(tmp_path, "../outside.csv")["status"] == "unreadable_or_invalid_metadata"
    assert inspect_input(tmp_path, "holdout_predictions.csv")["status"] == "forbidden_prediction_path"


def test_missing_and_historically_different_environment_is_explicit():
    def versions(name):
        if name == "numpy":
            raise metadata.PackageNotFoundError(name)
        return "synthetic-new-version"
    result = check_environment({"numpy_version": "old", "pandas_version": "old"}, versions)
    assert next(x for x in result if x["package"] == "numpy")["status"] == "missing"
    assert next(x for x in result if x["package"] == "pandas")["status"] == "recorded_version_mismatch"
    assert all(x["compatibility"] == "not_established" for x in result)


def test_preflight_never_opens_row_level_predictions_or_changes_files(tmp_path, monkeypatch):
    forbidden = put(tmp_path, "experiments/results/experiments/holdout_predictions.csv", "NEVER OPEN\n")
    before = snapshot(tmp_path)
    original = Path.open
    def guard(path, *args, **kwargs):
        if path == forbidden:
            pytest.fail("Preflight opened historical row predictions")
        return original(path, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", guard)
        run_preflight(tmp_path, version_lookup=installed)
    assert snapshot(tmp_path) == before


def test_command_is_stdout_only_no_bytecode_or_output_directories(tmp_path):
    before = snapshot(tmp_path)
    process = subprocess.run([sys.executable, "-B", "-m", "ml.preflight", "--root", str(tmp_path)],
                             cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True)
    assert process.returncode == 2
    report = json.loads(process.stdout)
    assert report["report_version"] == "0.1.0"
    assert report["research_execution_authorized"] is False
    assert report["real_data_fit_gate"]["research_fitting_enabled"] is False
    assert snapshot(tmp_path) == before
    assert list(tmp_path.iterdir()) == []


def test_research_gate_has_all_ten_obligations_and_no_filesystem_access(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("admission report opened a file")
    monkeypatch.setattr(Path, "open", forbidden)
    gate = research_fit_gate()
    assert gate["status"] == "FAIL" and not gate["research_fitting_enabled"]
    assert [c["id"] for c in gate["checks"]] == ["population", "source_labels", "identity", "assignments",
        "custody", "behavior", "dictionaries", "evaluation", "leakage", "reproducibility"]
    assert all(c["status"] == "FAIL" and c["required_evidence"] for c in gate["checks"])
    assert not gate["synthetic_success_authorizes_research"] and not gate["reference_strings_authorize_research"]
    gate["checks"][0]["status"] = "PASS"
    assert research_fit_gate()["checks"][0]["status"] == "FAIL"


def test_guard_rejects_self_declared_approvals_and_never_enables_fitting(tmp_path):
    from ml.experiment_inputs import InputContractError
    put(tmp_path, "approval.json", json.dumps({"all_approved": True, "reference": "synthetic-passed"}))
    with pytest.raises(InputContractError, match="research_fitting_not_authorized"):
        require_research_fitting()
    with pytest.raises(TypeError):
        require_research_fitting(approved=True)
    assert not research_fit_gate()["research_fitting_enabled"]


def test_gate_only_cli_ignores_corpus_paths_and_keeps_outputs_read_only(tmp_path):
    before = snapshot(tmp_path)
    process = subprocess.run([sys.executable, "-B", "-m", "ml.preflight", "--research-gate-only", "--root", str(tmp_path / "absent")],
                             cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True)
    assert process.returncode == 2
    result = json.loads(process.stdout)
    assert result["status"] == "FAIL" and len(result["checks"]) == 10
    assert snapshot(tmp_path) == before


def test_unselected_email_benchmark_is_reported_without_loading_an_alternative(tmp_path):
    notebook(tmp_path, "03_preprocessing", [
        ("selection", 'raise RuntimeError("primary_email_benchmark_not_selected: select an approved source")'),
    ])
    result = run_preflight(tmp_path, version_lookup=installed)
    assert any(i["code"] == "primary_email_benchmark_not_selected" for i in result["issues"])
    assert all(i["role"] in {"historical_source", "historical_cleaned", "preprocessed", "behavioral"}
               for i in result["inputs"])
    assert not next(s for s in result["stages"] if s["stage"] == "03")["can_run"]
