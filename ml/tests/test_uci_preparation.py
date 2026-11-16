"""Synthetic supplied-assignment UCI preparation; never read research data."""
from copy import deepcopy
from dataclasses import replace
import csv
import json
from pathlib import Path
import subprocess
import sys

import pytest

import ml.uci_preparation as preparation
from ml.development_experiments import (
    METADATA, DevelopmentSpecification, FeatureColumn, behavioral_columns,
    development_folds, load_development_dataset,
)
from ml.experiment_inputs import InputContractError
from ml.notebook_contracts import canonical_notebook_codebook


def synthetic():
    specification = DevelopmentSpecification(
        "UCI", (FeatureColumn("URL_Length", "numeric"), FeatureColumn("Redirect", "numeric")),
        "synthetic-protocol-only", "synthetic-dictionary-only",
    )
    rows, manifest = [], []
    for fold in range(1, 6):
        for target in (0, 1):
            position = len(rows)
            row = dict(observation_id=f"UCI::{position}", source_dataset="UCI Phishing Websites",
                       source_row_id=position, Result=-1 if target else 1, target=target,
                       group_id=f"synthetic-pair-{fold}", partition="development", cv_fold=fold,
                       URL_Length=(-1, 0, 1)[position % 3], Redirect=position % 2)
            rows.append(row)
            manifest.append({key: row[key] for key in (*METADATA, "source_dataset")})
    for part in ("calibration", "test"):
        for target in (0, 1):
            manifest.append(dict(observation_id=f"UCI::{len(manifest)}",
                                 source_dataset="UCI Phishing Websites", target=target,
                                 group_id=f"synthetic-{part}-{target}", partition=part, cv_fold=None))
    return rows, manifest, frozenset(r["observation_id"] for r in manifest), specification


def invoke(root, rows, manifest, ids, spec):
    return preparation.prepare_uci_handoff(
        root, "synthetic-uci-v1", rows, assignment_manifest=manifest,
        expected_observation_ids=ids, specification=spec,
    )


def inventory(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_valid_assignments_native_codes_and_d9_folds_are_preserved(tmp_path):
    rows, manifest, ids, spec = synthetic()
    original = deepcopy((rows, manifest))
    # Order is independent: joins must never zip differently ordered records.
    manifest.reverse()
    original_manifest = deepcopy(manifest)
    outputs = invoke(tmp_path, rows, manifest, ids, spec)
    assert rows == original[0] and manifest == original_manifest
    expected_paths = {
        "experiments/runs/synthetic-uci-v1/data/processed/features/development/uci_development.csv",
        "experiments/runs/synthetic-uci-v1/data/processed/features/sebrl/uci_sebrl_features.csv",
        "experiments/runs/synthetic-uci-v1/data/processed/features/development/development_input_manifest.json",
    }
    assert {p.relative_to(tmp_path).as_posix() for p in outputs} == expected_paths
    assert set(inventory(tmp_path)) == expected_paths
    with outputs[0].open(newline="", encoding="utf-8") as f:
        exported = list(csv.DictReader(f))
    assert [r["observation_id"] for r in exported] == [r["observation_id"] for r in rows]
    for actual, source in zip(exported, rows):
        assert all(actual[key] == str(value) for key, value in source.items())
    assert {r["URL_Length"] for r in exported} == {"-1", "0", "1"}
    assert set(json.loads(outputs[-1].read_text())["inputs"]) == {"UCI"}
    loaded = load_development_dataset(tmp_path, "synthetic-uci-v1", specification=spec)
    assert loaded.configurations == ("U1",)
    assert [r.observation_id for r in loaded.observations] == [r["observation_id"] for r in rows]
    assert all(r.behavioral == (0,) * 8 for r in loaded.observations)
    for item, source in zip(loaded.observations, rows):
        assert item.conventional == (source["URL_Length"], source["Redirect"])
        assert item.target == source["target"] and item.group_id == source["group_id"] and item.fold == source["cv_fold"]
    plans = development_folds(loaded, "U1")
    assert len(plans) == 5
    assert all(p.feature_names == ("URL_Length", "Redirect") for p in plans)
    assert all(not set(p.training_ids) & set(p.validation_ids) for p in plans)
    assert manifest == original_manifest


@pytest.mark.parametrize("change", ["drop_dev", "drop_reserved", "extra_dev", "extra_reserved", "duplicate", "conflicting_duplicate"])
def test_missing_unexpected_and_duplicate_assignments_fail_without_output(tmp_path, change):
    rows, manifest, ids, spec = synthetic()
    if change == "drop_dev": manifest.pop(0)
    elif change == "drop_reserved": manifest.pop()
    elif change.startswith("extra"):
        row = dict(manifest[0] if change == "extra_dev" else manifest[-1])
        row.update(observation_id="UCI::unexpected", group_id="unrecognized")
        manifest.append(row)
    else:
        row = dict(manifest[0])
        if change == "conflicting_duplicate": row["target"] = 1 - row["target"]
        manifest.append(row)
    before = deepcopy((rows, manifest))
    with pytest.raises(InputContractError):
        invoke(tmp_path, rows, manifest, ids, spec)
    assert list(tmp_path.iterdir()) == [] and (rows, manifest) == before


@pytest.mark.parametrize("change", ["cross_partition", "cross_fold", "missing_fold", "invalid_fold",
    "fractional_fold", "bool_fold", "string_fold", "reserved_fold", "missing_partition", "empty_group", "list_partition"])
def test_bad_group_partition_and_fold_metadata_fail(tmp_path, change):
    rows, manifest, ids, spec = synthetic()
    if change == "cross_partition": manifest[-1]["group_id"] = manifest[0]["group_id"]
    elif change == "cross_fold": manifest[2]["group_id"] = manifest[0]["group_id"]
    elif change == "reserved_fold": manifest[-1]["cv_fold"] = 1
    elif change == "missing_partition": manifest = [r for r in manifest if r["partition"] != "test"]
    elif change == "empty_group": manifest[0]["group_id"] = ""
    elif change == "list_partition": manifest[0]["partition"] = []
    else:
        manifest[0]["cv_fold"] = {"missing_fold": None, "invalid_fold": 6,
            "fractional_fold": 1.5, "bool_fold": True, "string_fold": "1"}[change]
    with pytest.raises(InputContractError):
        invoke(tmp_path, rows, manifest, ids, spec)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("field,value", [
    ("target", 1), ("target", True), ("Result", 0), ("Result", "1"),
    ("source_dataset", "PhiUSIIL"), ("source_row_id", -1), ("source_row_id", "0"),
    ("group_id", "another-group"), ("cv_fold", 2), ("partition", "test"),
])
def test_development_label_source_and_assignment_mismatches_fail(tmp_path, field, value):
    rows, manifest, ids, spec = synthetic()
    rows[0][field] = value
    with pytest.raises(InputContractError):
        invoke(tmp_path, rows, manifest, ids, spec)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("change", ["drop", "extra", "duplicate", "foreign", "reserved"])
def test_payload_must_cover_exactly_supplied_development_ids(tmp_path, change):
    rows, manifest, ids, spec = synthetic()
    if change == "drop": rows.pop()
    elif change == "duplicate": rows.append(dict(rows[0]))
    elif change == "extra":
        rows.append({**rows[0], "observation_id": "UCI::999", "source_row_id": 999})
    elif change == "foreign": rows[0]["observation_id"] = "UCI::foreign"
    else:
        rows[0]["observation_id"] = manifest[-1]["observation_id"]
    with pytest.raises(InputContractError):
        invoke(tmp_path, rows, manifest, ids, spec)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("change", ["missing_feature", "unexpected_feature", "missing_metadata",
    "extra_assignment_column", "missing_assignment_column", "no_manifest", "no_payload"])
def test_exact_feature_and_manifest_schemas_are_required(tmp_path, change):
    rows, manifest, ids, spec = synthetic()
    if change == "missing_feature": rows[0].pop("Redirect")
    elif change == "unexpected_feature": rows[0]["unapproved_extra"] = 1
    elif change == "missing_metadata": rows[0].pop("Result")
    elif change == "extra_assignment_column": manifest[0]["URL_Length"] = -1
    elif change == "missing_assignment_column": manifest[0].pop("target")
    elif change == "no_manifest": manifest = None
    else: rows = None
    with pytest.raises(InputContractError):
        invoke(tmp_path, rows, manifest, ids, spec)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("name", ["Result", "target", "group_id", "source_dataset", "feature_hash",
    "provenance_reference", "pressure_threat_cues_available"])
def test_dictionary_cannot_select_labels_provenance_or_compact_behavior(name):
    with pytest.raises(InputContractError):
        FeatureColumn(name, "numeric")


@pytest.mark.parametrize("name", ["urgency_available", "urgency_supported", "urgency_evidence", "pressure_threat_cues_state"])
def test_dictionary_cannot_select_indicator_derived_fields(tmp_path, name):
    rows, manifest, ids, spec = synthetic()
    spec = replace(spec, conventional=(*spec.conventional, FeatureColumn(name, "numeric")))
    with pytest.raises(InputContractError, match="technical_behavioral_evidence_forbidden"):
        invoke(tmp_path, rows, manifest, ids, spec)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("change", ["no_spec", "email", "phiusiil", "empty", "duplicate",
    "text", "missing_protocol", "missing_dictionary"])
def test_invalid_dictionary_or_branch_specification_is_rejected(tmp_path, change):
    rows, manifest, ids, spec = synthetic()
    with pytest.raises(InputContractError):
        if change == "no_spec": spec = None
        elif change in ("email", "phiusiil"): spec = replace(spec, dataset="Email" if change == "email" else "PhiUSIIL")
        elif change == "empty": spec = replace(spec, conventional=())
        elif change == "duplicate": spec = replace(spec, conventional=(spec.conventional[0],) * 2)
        elif change == "text": spec = replace(spec, conventional=(FeatureColumn("URL_Length", "text"),))
        elif change == "missing_protocol": spec = replace(spec, protocol_reference="")
        else: spec = replace(spec, feature_dictionary_reference="")
        invoke(tmp_path, rows, manifest, ids, spec)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("ids", [None, frozenset(), set(("UCI::0",)), frozenset((True,)), frozenset(("",))])
def test_population_id_expectation_is_required(tmp_path, ids):
    rows, manifest, _, spec = synthetic()
    with pytest.raises(InputContractError, match="explicit_uci_population_ids_required"):
        invoke(tmp_path, rows, manifest, ids, spec)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("value", [True, "0", float("nan"), float("inf"), float("-inf")])
def test_invalid_numeric_features_cannot_reach_export(tmp_path, value):
    rows, manifest, ids, spec = synthetic()
    rows[0]["URL_Length"] = value
    with pytest.raises(InputContractError, match="invalid_numeric_predictor"):
        invoke(tmp_path, rows, manifest, ids, spec)
    assert list(tmp_path.iterdir()) == []


def test_missing_numeric_value_is_preserved_without_imputation(tmp_path):
    rows, manifest, ids, spec = synthetic()
    rows[0]["URL_Length"] = None
    outputs = invoke(tmp_path, rows, manifest, ids, spec)
    with outputs[0].open(newline="") as f: exported = list(csv.DictReader(f))
    assert exported[0]["URL_Length"] == ""
    loaded = load_development_dataset(tmp_path, "synthetic-uci-v1", specification=spec)
    assert loaded.observations[0].conventional == (None, rows[0]["Redirect"])


def test_lossless_nullable_fold_encoding_does_not_change_supplied_records(tmp_path):
    rows, manifest, ids, spec = synthetic()
    for row in rows: row["cv_fold"] = float(row["cv_fold"])
    for row in manifest:
        if row["partition"] == "development": row["cv_fold"] = float(row["cv_fold"])
    original = deepcopy((rows, manifest))
    outputs = invoke(tmp_path, rows, manifest, ids, spec)
    with outputs[0].open(newline="") as f: exported = list(csv.DictReader(f))
    assert [r["cv_fold"] for r in exported] == [str(r["cv_fold"]) for r in rows]
    assert (rows, manifest) == original
    assert len(load_development_dataset(tmp_path, "synthetic-uci-v1", specification=spec).observations) == 10


def test_existing_optional_audit_columns_remain_metadata(tmp_path):
    rows, manifest, ids, spec = synthetic()
    for row in rows:
        row["source_label"] = row["Result"]
        row["feature_hash"] = f"synthetic-opaque-{row['source_row_id']}"
    outputs = invoke(tmp_path, rows, manifest, ids, spec)
    loaded = load_development_dataset(tmp_path, "synthetic-uci-v1", specification=spec)
    assert all(len(r.conventional) == 2 for r in loaded.observations)
    with outputs[0].open(newline="") as f: exported = list(csv.DictReader(f))
    assert [r["feature_hash"] for r in exported] == [r["feature_hash"] for r in rows]


def test_unavailable_states_remain_unavailable_before_compact_export(tmp_path, monkeypatch):
    rows, manifest, ids, spec = synthetic()
    original = preparation.prepare_selected_branches
    calls = []
    def inspect(inputs, branches):
        assert branches == ("UCI",) and set(inputs) == {"UCI"}
        result = original(inputs, branches)
        calls.append(result)
        for row in result["UCI"]:
            for dimension, data in canonical_notebook_codebook().items():
                assert row[f"{dimension}_state"] == "Unavailable"
                for indicator in data["indicators"]:
                    assert row[f"{indicator}_available"] is False
                    assert row[f"{indicator}_supported"] is False
                    assert row[f"{indicator}_evidence"] == "[]"
            assert not {"urls", "subject", "body"} & set(row)
        return result
    monkeypatch.setattr(preparation, "prepare_selected_branches", inspect)
    invoke(tmp_path, rows, manifest, ids, spec)
    assert len(calls) == 1


def test_entry_point_opens_no_dataset_or_other_branch_inputs(tmp_path, monkeypatch):
    rows, manifest, ids, spec = synthetic()
    original = Path.open
    opened = []
    def guarded(path, mode="r", *args, **kwargs):
        opened.append((path, mode))
        if mode == "xb":
            assert path.is_relative_to(tmp_path)
            assert path.name in {"uci_development.csv", "uci_sebrl_features.csv", "development_input_manifest.json"}
        else:
            assert path.resolve() == (Path(preparation.__file__).parent / "se_brl/codebook.v0.1.0.json").resolve()
        assert not any(t in path.name.lower() for t in ("email", "phiusiil"))
        return original(path, mode, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    invoke(tmp_path, rows, manifest, ids, spec)
    assert len([item for item in opened if item[1] == "xb"]) == 3


@pytest.mark.parametrize("collision", ["uci_development.csv", "uci_sebrl_features.csv", "development_input_manifest.json"])
def test_existing_outputs_are_never_overwritten(tmp_path, collision):
    rows, manifest, ids, spec = synthetic()
    folder = "sebrl" if collision == "uci_sebrl_features.csv" else "development"
    path = tmp_path / "experiments/runs/synthetic-uci-v1/data/processed/features" / folder / collision
    path.parent.mkdir(parents=True)
    path.write_bytes(b"pre-existing synthetic work")
    before = inventory(tmp_path)
    with pytest.raises(InputContractError, match="output_exists_or_duplicate_path"):
        invoke(tmp_path, rows, manifest, ids, spec)
    assert inventory(tmp_path) == before


@pytest.mark.parametrize("failure", ["behavioral_open", "manifest_open", "manifest_write"])
def test_export_failure_does_not_leave_a_completed_or_partial_bundle(tmp_path, monkeypatch, failure):
    rows, manifest, ids, spec = synthetic()
    original = Path.open
    class BrokenWrite:
        def __init__(self, stream): self.stream = stream
        def __enter__(self): return self
        def write(self, content):
            self.stream.write(content[:8])
            raise OSError("synthetic write failure")
        def __exit__(self, *args): self.stream.close()
    def fail(path, mode="r", *args, **kwargs):
        if mode == "xb":
            if ((failure == "behavioral_open" and path.name == "uci_sebrl_features.csv")
                    or (failure == "manifest_open" and path.name == "development_input_manifest.json")):
                raise OSError("synthetic open failure")
            if failure == "manifest_write" and path.name == "development_input_manifest.json":
                return BrokenWrite(original(path, mode, *args, **kwargs))
        return original(path, mode, *args, **kwargs)
    monkeypatch.setattr(Path, "open", fail)
    with pytest.raises(InputContractError, match="preparation_export_failed"):
        invoke(tmp_path, rows, manifest, ids, spec)
    assert list(tmp_path.iterdir()) == []


def test_preparation_import_and_execution_need_no_scientific_or_email_rules(tmp_path):
    # Fresh process guards against hidden estimator/Email-rule imports even when
    # the complete pytest process has imported unrelated runtime modules.
    code = """
import builtins, pathlib, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'numpy','pandas','scipy','sklearn','xgboost','torch','transformers'} or name in {
        'ml.models','ml.se_brl.rules','ml.se_brl.detectors','ml.se_brl.extraction'}:
        raise AssertionError('Forbidden scientific or Email-rule import: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from ml.tests.test_uci_preparation import synthetic, invoke
rows, manifest, ids, spec = synthetic()
invoke(pathlib.Path(sys.argv[1]), rows, manifest, ids, spec)
"""
    # This test helper imports pytest, which is already available; no estimator
    # package, data file or research notebook is needed by the guarded subprocess.
    result = subprocess.run([sys.executable, "-B", "-c", code, str(tmp_path)],
                            text=True, capture_output=True, cwd=Path(__file__).resolve().parents[2])
    assert result.returncode == 0, result.stderr

