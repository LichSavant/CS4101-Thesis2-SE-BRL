"""Synthetic branch selection, preparation and exclusive handoff; no notebooks run."""
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path

import pytest

from ml.branch_preparation import (
    ALL_BRANCHES, PARTITION_FILES, PREPROCESSED_FILES, SHARED_OUTPUTS,
    export_selected_handoff, load_selected_inputs, prepare_selected_branches, select_branches,
)
from ml.development_experiments import METADATA, behavioral_columns, load_development_dataset
from ml.experiment_inputs import InputContractError
from ml.notebook_contracts import canonical_notebook_codebook, technical_indicator_columns
from ml.tests.test_development_experiments import fixture_rows, spec


def put_inputs(root, names):
    """Full synthetic populations include reserved metadata; no real observations."""
    for name in names:
        rows, _ = fixture_rows(name)
        # Remove Email-like text from technical fixtures: U1 must not need it.
        if name != "Email":
            for row in rows:
                row.pop("subject")
                row.pop("body")
                row["Title"] = "Act now! Enter your password!"
        for partition in ("calibration", "test"):
            for target in (0, 1):
                row = deepcopy(next(r for r in rows if r["target"] == target))
                row.update(observation_id=f"{partition}-{target}", group_id=f"{partition}-{target}",
                           source_row_id=len(rows), partition=partition, cv_fold=None)
                rows.append(row)
        paths = (root / "data/processed/preprocessed" / PREPROCESSED_FILES[name],
                 root / "results/preprocessing/partitions" / PARTITION_FILES[name])
        manifest = [{k: r[k] for k in (*METADATA, "source_dataset")} for r in rows]
        for path, items in zip(paths, (rows, manifest)):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=tuple(items[0]))
                writer.writeheader()
                writer.writerows(items)


def read_records(path):
    """Decode synthetic fixture scalars in place of the notebook's pandas decoder."""
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, strict=True))
    for row in rows:
        for key in ("target", "source_row_id", "cv_fold", "label", "Result"):
            if key in row:
                row[key] = None if row[key] == "" else int(row[key])
    return rows


def compact(prepared):
    return {name: [{k: r[k] for k in (*METADATA, *behavioral_columns())} for r in rows]
            for name, rows in prepared.items()}


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("names", [("PhiUSIIL",), ("UCI",), ("PhiUSIIL", "UCI")])
def test_technical_preparation_never_opens_email_or_calls_email_rules(tmp_path, monkeypatch, names):
    run = tmp_path / "experiments/runs/synthetic-v1"
    put_inputs(run, names)
    before = snapshot(tmp_path)
    opened = []
    def reader(path):
        opened.append(path)
        assert path.name in {PREPROCESSED_FILES[n] for n in names} | {PARTITION_FILES[n] for n in names}
        return read_records(path)
    def forbidden(_):
        pytest.fail("Email behavioral rules were invoked by U1 preparation")
    inputs = load_selected_inputs(run, names, read_records=reader)
    prepared = prepare_selected_branches(inputs, names, prepare_email=forbidden)
    assert len(opened) == len(names) * 2
    assert snapshot(tmp_path) == before
    for name in names:
        assert len(inputs[name]) == len(prepared[name]) == 10
        for original, row in zip(inputs[name], prepared[name]):
            assert all(row[k] == value for k, value in original.items())
            assert row["partition"] == "development"
            assert all(row[f"{d}_state"] == "Unavailable" for d in canonical_notebook_codebook())
            assert all(row[c] == 0 for c in behavioral_columns())
            assert "urls" not in row and "sender" not in row
    outputs = export_selected_handoff(run, names, inputs, compact(prepared))
    assert len(outputs) == 2 * len(names) + 1
    manifest = json.loads((run / "data/processed/features/development/development_input_manifest.json").read_text())
    assert set(manifest["inputs"]) == set(names)
    for name in names:
        # Actual D9 consumer accepts the produced filenames, hashes and vectors.
        from ml.development_experiments import DevelopmentSpecification, FeatureColumn
        specification = DevelopmentSpecification(name, (FeatureColumn("length", "numeric"),), "synthetic", "synthetic")
        result = load_development_dataset(tmp_path, "synthetic-v1", specification=specification)
        assert result.configurations == ("U1",)
        assert len(result.observations) == 10


@pytest.mark.parametrize("selection", [None, (), [], "UCI", ("UCI", "UCI"),
    ("url",), ("ISCX",), ("Email", "unknown"), (True,)])
def test_invalid_selections_fail_without_reading_or_creating_paths(tmp_path, selection):
    def forbidden(_):
        pytest.fail("Invalid selection reached a reader")
    with pytest.raises(InputContractError, match="explicit_unique_preparation_branches_required"):
        load_selected_inputs(tmp_path / "synthetic-v1", selection, read_records=forbidden)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("missing", ["source", "manifest", "other_selected_branch"])
def test_all_required_selected_files_are_checked_before_any_read(tmp_path, missing):
    run = tmp_path / "synthetic-v1"
    put_inputs(run, ("UCI",))
    names = ("UCI", "PhiUSIIL") if missing == "other_selected_branch" else ("UCI",)
    if missing == "source": (run / "data/processed/preprocessed" / PREPROCESSED_FILES["UCI"]).unlink()
    if missing == "manifest": (run / "results/preprocessing/partitions" / PARTITION_FILES["UCI"]).unlink()
    before = snapshot(tmp_path)
    with pytest.raises(InputContractError, match="required_selected_preparation_input_missing"):
        load_selected_inputs(run, names, read_records=lambda _: pytest.fail("Reader called before preflight"))
    assert snapshot(tmp_path) == before
    assert not (run / "data/processed/features").exists()


def test_combined_mode_preserves_email_callback_and_all_three_handoffs(tmp_path):
    run = tmp_path / "experiments/runs/synthetic-v1"
    put_inputs(run, ALL_BRANCHES)
    inputs = load_selected_inputs(run, ALL_BRANCHES, read_records=read_records)
    calls = []
    _, expected_vectors = fixture_rows()
    by_id = {r["observation_id"]: r for r in expected_vectors}
    def email(rows):
        calls.append(rows)
        return tuple({**r, **by_id[r["observation_id"]]} for r in rows)
    prepared = prepare_selected_branches(inputs, ALL_BRANCHES, prepare_email=email)
    assert len(calls) == 1 and len(calls[0]) == 10
    assert compact(prepared)["Email"] == expected_vectors
    outputs = export_selected_handoff(run, ALL_BRANCHES, inputs, compact(prepared))
    assert len(outputs) == 7
    for name in ALL_BRANCHES:
        if name == "Email": specification = spec(name)
        else:
            from ml.development_experiments import DevelopmentSpecification, FeatureColumn
            specification = DevelopmentSpecification(name, (FeatureColumn("length", "numeric"),), "synthetic", "synthetic")
        assert len(load_development_dataset(tmp_path, "synthetic-v1", specification=specification).observations) == 10


def test_email_selection_does_not_bypass_its_existing_freeze_gate(tmp_path):
    run = tmp_path / "synthetic-v1"
    put_inputs(run, ("Email",))
    inputs = load_selected_inputs(run, ("Email",), read_records=read_records)
    def blocked(_):
        raise RuntimeError("behavioral_specification_not_frozen")
    with pytest.raises(RuntimeError, match="behavioral_specification_not_frozen"):
        prepare_selected_branches(inputs, ("Email",), prepare_email=blocked)
    assert not (run / "data/processed/features").exists()


@pytest.mark.parametrize("mutation", ["id", "source", "fold", "target", "body", "extra_branch"])
def test_preparation_cannot_change_original_records(tmp_path, mutation):
    run = tmp_path / "synthetic-v1"
    put_inputs(run, ("Email",))
    inputs = load_selected_inputs(run, ("Email",), read_records=read_records)
    before = deepcopy(inputs)
    def email(rows):
        key = {"id": "observation_id", "source": "source_dataset", "fold": "cv_fold", "target": "target", "body": "body"}[mutation]
        rows[0][key] = "changed"
        return rows
    if mutation == "extra_branch":
        inputs = {**inputs, "UCI": ()}
    with pytest.raises(InputContractError):
        prepare_selected_branches(inputs, ("Email",), prepare_email=email)
    if mutation != "extra_branch": assert inputs == before


@pytest.mark.parametrize("collision", ["behavioral", "manifest", "shared"])
def test_collisions_create_nothing_and_preserve_existing_files(tmp_path, collision):
    run = tmp_path / "synthetic-v1"
    put_inputs(run, ("UCI",))
    inputs = load_selected_inputs(run, ("UCI",), read_records=read_records)
    prepared = prepare_selected_branches(inputs, ("UCI",))
    path = run / {"behavioral": "data/processed/features/sebrl/uci_sebrl_features.csv",
                  "manifest": "data/processed/features/development/development_input_manifest.json",
                  "shared": SHARED_OUTPUTS[0]}[collision]
    path.parent.mkdir(parents=True)
    path.write_bytes(b"existing work")
    before = snapshot(tmp_path)
    with pytest.raises(InputContractError, match="output_exists_or_duplicate_path"):
        export_selected_handoff(run, ("UCI",), inputs, compact(prepared), shared_outputs={SHARED_OUTPUTS[0]: b"synthetic"})
    assert snapshot(tmp_path) == before


def test_io_failure_rolls_back_only_files_and_directories_created_by_this_export(tmp_path, monkeypatch):
    run = tmp_path / "synthetic-v1"
    put_inputs(run, ("UCI",))
    inputs = load_selected_inputs(run, ("UCI",), read_records=read_records)
    prepared = prepare_selected_branches(inputs, ("UCI",))
    before = snapshot(tmp_path)
    dirs_before = {p for p in tmp_path.rglob("*") if p.is_dir()}
    original = Path.open
    def fail_second_write(path, mode="r", *args, **kwargs):
        if mode == "xb" and path.name == "uci_sebrl_features.csv":
            raise OSError("synthetic IO failure")
        return original(path, mode, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", fail_second_write)
        with pytest.raises(InputContractError, match="preparation_export_failed"):
            export_selected_handoff(run, ("UCI",), inputs, compact(prepared))
    assert snapshot(tmp_path) == before
    assert {p for p in tmp_path.rglob("*") if p.is_dir()} == dirs_before


def test_selected_output_and_metadata_validation_happens_before_writes(tmp_path):
    run = tmp_path / "synthetic-v1"
    put_inputs(run, ("UCI",))
    inputs = load_selected_inputs(run, ("UCI",), read_records=read_records)
    vectors = compact(prepare_selected_branches(inputs, ("UCI",)))
    vectors["UCI"][0][behavioral_columns()[0]] = 1
    before = snapshot(tmp_path)
    with pytest.raises(InputContractError):
        export_selected_handoff(run, ("UCI",), inputs, vectors)
    assert snapshot(tmp_path) == before
    assert not (run / "data/processed/features").exists()


@pytest.mark.parametrize("field,value", [("observation_id", "foreign"), ("group_id", "other"), ("cv_fold", 2)])
def test_supplied_manifest_mismatch_does_not_create_output_paths(tmp_path, field, value):
    run = tmp_path / "synthetic-v1"
    put_inputs(run, ("UCI",))
    before = snapshot(tmp_path)
    def reader(path):
        rows = read_records(path)
        if path.name == PARTITION_FILES["UCI"]: rows[0][field] = value
        return rows
    with pytest.raises(InputContractError, match="partition_manifest_mismatch"):
        load_selected_inputs(run, ("UCI",), read_records=reader)
    assert snapshot(tmp_path) == before and not (run / "data/processed/features").exists()


def test_only_allowlisted_shared_outputs_can_be_created(tmp_path):
    run = tmp_path / "synthetic-v1"
    put_inputs(run, ("UCI",))
    inputs = load_selected_inputs(run, ("UCI",), read_records=read_records)
    vectors = compact(prepare_selected_branches(inputs, ("UCI",)))
    before = snapshot(tmp_path)
    with pytest.raises(InputContractError, match="invalid_shared_preparation_output"):
        export_selected_handoff(run, ("UCI",), inputs, vectors, shared_outputs={"../historical.csv": b"invalid"})
    assert snapshot(tmp_path) == before and not (run / "data/processed/features").exists()
    outputs = export_selected_handoff(run, ("UCI",), inputs, vectors,
                                      shared_outputs={SHARED_OUTPUTS[0]: b"synthetic evidence metadata"})
    assert len(outputs) == 4
    assert (run / SHARED_OUTPUTS[0]).read_bytes() == b"synthetic evidence metadata"


def test_csv_parser_failures_are_sanitized_without_writes(tmp_path):
    run = tmp_path / "synthetic-v1"
    put_inputs(run, ("UCI",))
    before = snapshot(tmp_path)
    def broken(_):
        raise ValueError("SENSITIVE SYNTHETIC CONTENT")
    with pytest.raises(InputContractError, match="^selected_preparation_input_invalid$") as error:
        load_selected_inputs(run, ("UCI",), read_records=broken)
    assert "SENSITIVE" not in str(error.value) and error.value.__suppress_context__
    assert snapshot(tmp_path) == before


def test_notebook_calls_selected_boundaries_and_keeps_email_rules_unchanged():
    import ast
    root = Path(__file__).resolve().parents[2]
    nb = json.loads((root / "experiments/notebooks/04_feature_extraction.ipynb").read_text(encoding="utf-8"))
    cells = {c["id"]: ''.join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"}
    assert "select_branches(ALL_BRANCHES)" in cells["2a7ff1dd"]
    assert "load_selected_inputs(" in cells["ef42ccf9"]
    assert "prepare_selected_branches(" in cells["a1617aaa"]
    assert "export_selected_handoff(" in cells["a8cef068"]
    examples = ast.parse(cells["bc7bf1a9"])
    assert isinstance(examples.body[0], ast.If)
    assert ast.unparse(examples.body[0].test) == "'Email' in SELECTED_BRANCHES"
    class TechnicalPath(ast.NodeVisitor):
        def __init__(self): self.email_references = []
        def visit_FunctionDef(self, node): pass  # Definitions do not execute their bodies.
        def visit_If(self, node):
            if ((isinstance(node.test, ast.Constant) and node.test.value is False)
                    or ast.unparse(node.test) == "'Email' in SELECTED_BRANCHES"):
                for child in node.orelse: self.visit(child)
            else:
                self.generic_visit(node)
        def visit_Name(self, node):
            if node.id in {"evaluate_lexical_indicator", "extract_pattern_evidence", "normalize_match_text",
                           "apply_lexical_rules", "email_evidence_availability"}:
                self.email_references.append(node.id)
    visitor = TechnicalPath()
    for source in cells.values(): visitor.visit(ast.parse(source))
    assert visitor.email_references == []
