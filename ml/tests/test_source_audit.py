"""Fixtures for no-fit source auditing; no research files are loaded."""
import hashlib
import json
from pathlib import Path

import pytest

from ml.source_audit import audit_uci_arff, write_source_audit, main
from ml.experiment_inputs import InputContractError


def source(tmp_path, rows=None):
    rows = rows if rows is not None else [([0]*30, -1), ([0]*30, -1), ([0]*30, 1), ([-1]*30, 1)]
    text = "@relation synthetic\n" + "\n".join(f"@attribute f{i} {{-1,0,1}}" for i in range(30))
    text += "\n@attribute Result {-1,1}\n@data\n"
    text += "\n".join(",".join(map(str, values+[label])) for values, label in rows)
    path = tmp_path / "source.arff"
    path.write_text(text)
    return path


def audit(path, **changes):
    options = dict(expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), source_reference="synthetic:source",
                   license_reference="synthetic:license", authorization_reference="synthetic:operator", max_bytes=100000)
    options.update(changes)
    return audit_uci_arff(path, **options)


def test_native_codes_duplicates_and_conflicts_are_diagnostics_not_assignments(tmp_path):
    path = source(tmp_path)
    before = path.read_bytes()
    report = audit(path)
    assert report["source_records"] == 4 and report["valid_native_records"] == 4
    assert report["native_result_counts"] == {"-1": 2, "1": 2}
    assert report["distinct_full_native_rows"] == 3 and report["repeated_full_native_rows"] == 1
    assert report["distinct_native_feature_vectors"] == 2 and report["mixed_native_result_feature_vectors"] == 1
    assert report["native_feature_value_counts"]["f0"] == {"-1": 1, "0": 3}
    assert report["groups_generated"] == report["assignments_generated"] == report["model_fits"] == 0
    assert report["target_mapping_status"].startswith("not_interpreted")
    assert path.read_bytes() == before
    digest = write_source_audit(tmp_path / "run", report)
    assert digest == hashlib.sha256((tmp_path / "run/source_audit.json").read_bytes()).hexdigest()
    with pytest.raises(InputContractError):
        write_source_audit(tmp_path / "run", report)


def test_invalid_rows_are_reason_coded_without_silent_eligibility_filter(tmp_path):
    path = source(tmp_path)
    with path.open("a") as stream:
        stream.write("\n1,1\n" + ",".join(["?"]+["0"]*29+["1"]) + "\n" + ",".join(["9"]+["0"]*29+["1"]))
    report = audit(path)
    assert report["source_records"] == 7 and report["invalid_native_records"] == 3
    assert report["reason_counts"] == {"wrong_field_count": 1, "missing_native_cell": 1, "outside_declared_native_domain": 1}
    assert report["eligibility_status"].startswith("not_frozen")


@pytest.mark.parametrize("options", ({"expected_sha256": None}, {"expected_sha256": "0"*64},
    {"max_bytes": True}, {"max_bytes": 1}, {"authorization_reference": ""}))
def test_fail_closed_snapshot_and_access_references(tmp_path, options):
    with pytest.raises(InputContractError):
        audit(source(tmp_path), **options)
    assert not (tmp_path / "run").exists()


def test_malformed_schema_and_lfs_pointer_rejected_without_output(tmp_path):
    for text in ("version https://git-lfs.github.com/spec/v1\n", "@relation fixture\n@data\n0,1", "@relation x\n@attribute Result numeric\n@data\n1"):
        path = tmp_path / "bad.arff"
        path.write_text(text)
        with pytest.raises(InputContractError):
            audit(path)


def test_failed_export_rolls_back_only_owned_new_output(tmp_path, monkeypatch):
    report = audit(source(tmp_path))
    original = Path.open
    def failed(path, *args, **kwargs):
        if path.name == "source_audit.json" and args and args[0] == "xb":
            raise OSError("synthetic denied")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", failed)
    with pytest.raises(InputContractError):
        write_source_audit(tmp_path / "run", report)
    assert not (tmp_path / "run").exists()


def test_cli_failure_does_not_create_output(tmp_path, capsys):
    path = source(tmp_path)
    result = main(["--source", str(path), "--expected-sha256", "0"*64, "--source-reference", "synthetic:x",
                   "--license-reference", "synthetic:x", "--authorization-reference", "synthetic:x",
                   "--max-bytes", "100000", "--output", str(tmp_path / "run")])
    assert result == 2 and json.loads(capsys.readouterr().out)["status"] == "failed"
    assert not (tmp_path / "run").exists()
