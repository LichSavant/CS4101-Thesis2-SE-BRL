"""D9 synthetic handoff checks. No scientific package or estimator is imported."""
from dataclasses import replace
import builtins
import csv
import hashlib
import json
from pathlib import Path

import pytest

from ml.development_experiments import (
    BEHAVIORAL_FILES, DEVELOPMENT_FILES, DevelopmentSpecification, FeatureColumn,
    behavioral_columns, build_development_dataset, development_folds,
    load_development_dataset, preparation_summary,
)
from ml.experiment_inputs import InputContractError
from ml.notebook_contracts import CONTRACT_VERSION


def spec(dataset="Email"):
    return DevelopmentSpecification(dataset, (FeatureColumn("subject", "text"), FeatureColumn("length", "numeric")),
                                    "synthetic-protocol", "synthetic-feature-dictionary")


def fixture_rows(dataset="Email"):
    rows, vectors = [], []
    for fold in range(1, 6):
        for target in (0, 1):
            position = (fold - 1) * 2 + target
            source = ("Nazario" if target else "Enron") if dataset == "Email" else (
                "PhiUSIIL" if dataset == "PhiUSIIL" else "UCI Phishing Websites")
            native = target if dataset == "Email" else (1 - target if dataset == "PhiUSIIL" else (1 if target == 0 else -1))
            row = dict(observation_id=f"fixture-{position}", source_dataset=source, source_row_id=position,
                target=target, group_id=f"group-{position}", partition="development", cv_fold=fold,
                subject=f"synthetic unique text {position}", body="synthetic body", length=position + 0.5)
            row["Result" if dataset == "UCI" else "label"] = native
            rows.append(row)
            vector = {c: row[c] for c in ("observation_id", "target", "group_id", "partition", "cv_fold")}
            vector.update({c: 0 for c in behavioral_columns()})
            if dataset == "Email":
                vector[behavioral_columns()[0]] = target
                vector.update({c: 1 for c in behavioral_columns()[4:]})
            vectors.append(vector)
    return rows, vectors


def test_matched_configurations_keep_ids_groups_and_labels_out_of_predictors():
    rows, vectors = fixture_rows()
    dataset = build_development_dataset(rows, reversed(vectors), specification=spec())
    plans = {c: development_folds(dataset, c) for c in dataset.configurations}
    assert set(plans) == {"E1", "E2", "E3"}
    for fold in range(5):
        baseline = plans["E1"][fold]
        assert len(baseline.training_ids) == 8 and len(baseline.validation_ids) == 2
        assert not set(baseline.training_ids) & set(baseline.validation_ids)
        assert baseline.feature_names == ("subject", "length")
        for c in plans:
            assert plans[c][fold].training_ids == baseline.training_ids
            assert plans[c][fold].validation_ids == baseline.validation_ids
            assert plans[c][fold].y_train == baseline.y_train
            assert plans[c][fold].y_validation == baseline.y_validation
        assert plans["E3"][fold].x_train[0] == baseline.x_train[0] + plans["E2"][fold].x_train[0]
    assert dict(preparation_summary(dataset))["model_fits"] == 0


@pytest.mark.parametrize("dataset", ["PhiUSIIL", "UCI"])
def test_technical_branches_only_prepare_u1(dataset):
    rows, vectors = fixture_rows(dataset)
    prepared = build_development_dataset(rows, vectors, specification=spec(dataset))
    assert prepared.configurations == ("U1",)
    assert len(development_folds(prepared, "U1")) == 5
    with pytest.raises(InputContractError): development_folds(prepared, "E3")
    vectors[0][behavioral_columns()[4]] = 1
    with pytest.raises(InputContractError, match="technical_behavioral"):
        build_development_dataset(rows, vectors, specification=spec(dataset))


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate", "target", "group", "fold", "reserved", "bit", "mask"])
def test_behavioral_alignment_and_state_errors_are_rejected(mutation):
    rows, vectors = fixture_rows()
    if mutation == "missing": vectors.pop()
    elif mutation == "extra": vectors.append(dict(vectors[0], observation_id="foreign"))
    elif mutation == "duplicate": vectors.append(vectors[0])
    elif mutation == "target": vectors[0]["target"] = 1
    elif mutation == "group": vectors[0]["group_id"] = "wrong-group"
    elif mutation == "fold": vectors[0]["cv_fold"] = 2
    elif mutation == "reserved": vectors[0]["partition"] = "test"
    elif mutation == "bit": vectors[0][behavioral_columns()[0]] = float("nan")
    elif mutation == "mask":
        vectors[0][behavioral_columns()[0]] = 1
        vectors[0][behavioral_columns()[4]] = 0
    with pytest.raises(InputContractError):
        build_development_dataset(rows, vectors, specification=spec())


@pytest.mark.parametrize("mutation", ["reserved", "cross_fold", "missing_class", "duplicate_id", "wrong_native"])
def test_main_population_and_group_errors_fail(mutation):
    rows, vectors = fixture_rows()
    if mutation == "reserved": rows[0]["partition"] = "calibration"
    elif mutation == "cross_fold": rows[2]["group_id"] = rows[0]["group_id"]
    elif mutation == "missing_class": rows = rows[1:]
    elif mutation == "duplicate_id": rows[1]["observation_id"] = rows[0]["observation_id"]
    elif mutation == "wrong_native": rows[0]["label"] = 1
    with pytest.raises(InputContractError):
        build_development_dataset(rows, vectors, specification=spec())


@pytest.mark.parametrize("name", ["target", "source_label", "source_dataset", "cv_fold", "Result", "group_id"])
def test_predictor_metadata_cannot_be_selected(name):
    with pytest.raises(InputContractError): FeatureColumn(name, "numeric")


def test_feature_specification_is_explicit_and_rejects_invalid_values():
    with pytest.raises(InputContractError): DevelopmentSpecification("Email", (), "p", "f")
    with pytest.raises(InputContractError): replace(spec(), protocol_reference="")
    with pytest.raises(InputContractError): replace(spec(), dataset="ISCX")
    with pytest.raises(InputContractError): FeatureColumn(behavioral_columns()[0], "numeric")
    rows, vectors = fixture_rows()
    rows[0]["length"] = float("inf")
    with pytest.raises(InputContractError): build_development_dataset(rows, vectors, specification=spec())


def write_handoff(root, rows, vectors, dataset="Email"):
    run = root / "experiments/runs/synthetic-v1/data/processed/features"
    main = run / "development" / DEVELOPMENT_FILES[dataset]
    behavior = run / "sebrl" / BEHAVIORAL_FILES[dataset]
    for path, items in ((main, rows), (behavior, vectors)):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(items[0]))
            writer.writeheader(); writer.writerows(items)
    manifest = main.parent / "development_input_manifest.json"
    manifest.write_text(json.dumps({"contract_version": CONTRACT_VERSION, "run_id": "synthetic-v1",
        "inputs": {dataset: {"development_file": main.name, "behavioral_file": behavior.name,
          "development_sha256": hashlib.sha256(main.read_bytes()).hexdigest(),
          "behavioral_sha256": hashlib.sha256(behavior.read_bytes()).hexdigest()}}}), encoding="utf-8")
    return main, behavior, manifest


@pytest.mark.parametrize("dataset", ["Email", "PhiUSIIL", "UCI"])
def test_csv_handoff_to_fold_inputs_is_read_only_and_never_opens_reserved_paths(tmp_path, monkeypatch, dataset):
    rows, vectors = fixture_rows(dataset)
    write_handoff(tmp_path, rows, vectors, dataset)
    before = {p: (p.stat().st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest()) for p in tmp_path.rglob('*') if p.is_file()}
    opened = []
    original = Path.open
    codebook_path = Path(__file__).resolve().parents[1] / "se_brl/codebook.v0.1.0.json"
    def guard(path, *args, **kwargs):
        if path == codebook_path:
            return original(path, *args, **kwargs)
        opened.append(path)
        assert path.is_relative_to(tmp_path / "experiments/runs/synthetic-v1")
        assert not any(token in path.name for token in ("holdout", "calibration", "test"))
        return original(path, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", guard)
        result = load_development_dataset(tmp_path, "synthetic-v1", specification=spec(dataset))
    assert len(result.observations) == 10
    assert len(development_folds(result, result.configurations[0])) == 5
    assert len(opened) == 3
    assert {p: (p.stat().st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest()) for p in tmp_path.rglob('*') if p.is_file()} == before


@pytest.mark.parametrize("mutation", ["hash", "filename", "contract", "reserved", "malformed", "duplicate_header", "outside_run"])
def test_corrupt_or_untrusted_handoffs_fail_closed(tmp_path, mutation):
    rows, vectors = fixture_rows()
    main, behavior, manifest_path = write_handoff(tmp_path, rows, vectors)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest["inputs"]["Email"]
    if mutation == "hash": entry["development_sha256"] = "0" * 64
    elif mutation == "filename": entry["development_file"] = "../../holdout_predictions.csv"
    elif mutation == "contract": manifest["contract_version"] = "unknown"
    elif mutation in {"reserved", "malformed", "duplicate_header"}:
        text = main.read_text(encoding="utf-8")
        if mutation == "reserved": text = text.replace("development", "test", 1)
        elif mutation == "malformed": text += "too,few,columns\n"
        else: text = text.replace("observation_id", "target", 1)
        main.write_text(text, encoding="utf-8")
        entry["development_sha256"] = hashlib.sha256(main.read_bytes()).hexdigest()
    elif mutation == "outside_run":
        with pytest.raises(InputContractError):
            load_development_dataset(tmp_path, "../outside", specification=spec())
        return
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(InputContractError):
        load_development_dataset(tmp_path, "synthetic-v1", specification=spec())


def test_long_text_is_not_truncated_or_rejected_by_default_csv_field_limit(tmp_path):
    rows, vectors = fixture_rows()
    rows[0]["subject"] = "synthetic " * 20_000
    write_handoff(tmp_path, rows, vectors)
    limit = csv.field_size_limit()
    result = load_development_dataset(tmp_path, "synthetic-v1", specification=spec())
    assert result.observations[0].conventional[0] == rows[0]["subject"]
    assert csv.field_size_limit() == limit


def test_handoff_imports_no_scientific_packages_and_uses_no_model_fit(tmp_path, monkeypatch):
    rows, vectors = fixture_rows()
    write_handoff(tmp_path, rows, vectors)
    original = builtins.__import__
    def guard(name, *args, **kwargs):
        assert name.split('.')[0] not in {'numpy', 'pandas', 'scipy', 'sklearn', 'xgboost'}
        return original(name, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(builtins, '__import__', guard)
        dataset = load_development_dataset(tmp_path, 'synthetic-v1', specification=spec())
        for configuration in dataset.configurations: development_folds(dataset, configuration)


def test_missing_handoff_has_no_historical_fallback_or_directory_creation(tmp_path):
    historical = tmp_path / "experiments/data/processed/preprocessed/email_preprocessed.csv"
    historical.parent.mkdir(parents=True)
    historical.write_text("DO NOT LOAD HISTORICAL DATA", encoding="utf-8")
    before = {p.relative_to(tmp_path) for p in tmp_path.rglob('*')}
    with pytest.raises(InputContractError, match="development_handoff_missing_or_invalid"):
        load_development_dataset(tmp_path, "synthetic-v1", specification=spec())
    assert {p.relative_to(tmp_path) for p in tmp_path.rglob('*')} == before


def test_companion_notebook_has_no_execution_results_and_handoff_writes_are_exclusive():
    root = Path(__file__).resolve().parents[2]
    companion = json.loads((root / "experiments/notebooks/05_development_preparation.ipynb").read_text(encoding="utf-8"))
    for cell in companion["cells"]:
        if cell["cell_type"] == "code":
            assert cell["execution_count"] is None and cell["outputs"] == []
    import ast
    nb04 = json.loads((root / "experiments/notebooks/04_feature_extraction.ipynb").read_text(encoding="utf-8"))
    export = next(c for c in nb04["cells"] if c.get("id") == "a8cef068")
    tree = ast.parse(''.join(export['source']))
    # The notebook delegates writes to the selected exporter; its exclusive
    # creation, no-overwrite and rollback behavior have executable tests.
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    assert any(isinstance(n.func, ast.Name) and n.func.id == "export_selected_handoff" for n in calls)
    assert not any(isinstance(n.func, ast.Attribute) and n.func.attr in {"to_csv", "open"} for n in calls)


def update_handoff_hash(path, manifest_path, *, behavioral=False):
    """Update only task-owned synthetic fixtures, never research manifests."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    key = "behavioral_sha256" if behavioral else "development_sha256"
    manifest["inputs"]["Email"][key] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


@pytest.mark.parametrize("behavioral", [False, True])
@pytest.mark.parametrize("malformation", ["unterminated_quote", "junk_after_quote", "extra_field", "short_row"])
def test_strict_csv_rejects_malformed_records_even_with_matching_hash(tmp_path, behavioral, malformation):
    rows, vectors = fixture_rows()
    main, behavior, manifest = write_handoff(tmp_path, rows, vectors)
    path = behavior if behavioral else main
    original = path.read_text(encoding="utf-8")
    if malformation == "unterminated_quote":
        prefix, last = original.rsplit(",", 1)
        modified = prefix + ',"' + last.rstrip("\n")
    elif malformation == "junk_after_quote":
        modified = original.replace("fixture-0", '"fixture-0"unexpected', 1)
    elif malformation == "extra_field":
        modified = original.rstrip("\n") + ",unexpected\n"
    else:
        modified = original.rsplit(",", 1)[0] + "\n"
    path.write_text(modified, encoding="utf-8")
    update_handoff_hash(path, manifest, behavioral=behavioral)
    previous_limit = csv.field_size_limit()
    with pytest.raises(InputContractError):
        load_development_dataset(tmp_path, "synthetic-v1", specification=spec())
    assert csv.field_size_limit() == previous_limit


@pytest.mark.parametrize("behavioral", [False, True])
def test_blank_column_names_are_rejected(tmp_path, behavioral):
    rows, vectors = fixture_rows()
    for row in vectors if behavioral else rows:
        row[""] = "unexpected"
    main, behavior, manifest = write_handoff(tmp_path, rows, vectors)
    with pytest.raises(InputContractError):
        load_development_dataset(tmp_path, "synthetic-v1", specification=spec())


@pytest.mark.parametrize("column", ["unexpected", "source_label", "legacy_support"])
def test_compact_behavioral_schema_rejects_unexpected_columns(tmp_path, column):
    rows, vectors = fixture_rows()
    for vector in vectors:
        vector[column] = 0
    write_handoff(tmp_path, rows, vectors)
    with pytest.raises(InputContractError):
        load_development_dataset(tmp_path, "synthetic-v1", specification=spec())


@pytest.mark.parametrize("behavioral,column", [
    (False, "source_dataset"), (False, "source_row_id"), (False, "label"),
    (False, "subject"), (False, "body"), (False, "length"),
    (True, "observation_id"), (True, "target"), (True, "group_id"),
    (True, "partition"), (True, "cv_fold"), (True, behavioral_columns()[4]),
])
def test_csv_required_columns_are_checked_before_consumption(tmp_path, behavioral, column):
    rows, vectors = fixture_rows()
    for row in vectors if behavioral else rows:
        del row[column]
    write_handoff(tmp_path, rows, vectors)
    with pytest.raises(InputContractError):
        load_development_dataset(tmp_path, "synthetic-v1", specification=spec())


@pytest.mark.parametrize("behavioral", [False, True])
def test_duplicate_csv_observation_ids_are_rejected(tmp_path, behavioral):
    rows, vectors = fixture_rows()
    items = vectors if behavioral else rows
    items[1]["observation_id"] = items[0]["observation_id"]
    write_handoff(tmp_path, rows, vectors)
    with pytest.raises(InputContractError):
        load_development_dataset(tmp_path, "synthetic-v1", specification=spec())


@pytest.mark.parametrize("behavioral,column,value", [
    (False, "target", "True"), (False, "cv_fold", "1.5"),
    (False, "source_row_id", "-1"), (False, "label", "unmapped"),
    (False, "length", "nan"), (False, "length", "inf"),
    (True, "target", "False"), (True, "cv_fold", "6"),
    (True, behavioral_columns()[0], "2"), (True, behavioral_columns()[4], ""),
])
def test_invalid_csv_field_values_cannot_reach_fold_preparation(tmp_path, behavioral, column, value):
    rows, vectors = fixture_rows()
    (vectors if behavioral else rows)[0][column] = value
    write_handoff(tmp_path, rows, vectors)
    with pytest.raises(InputContractError):
        load_development_dataset(tmp_path, "synthetic-v1", specification=spec())


def test_valid_multiline_csv_and_unselected_source_fields_remain_compatible(tmp_path):
    rows, vectors = fixture_rows()
    original = 'First line, "quoted"\r\nSecond line\nUnicode: \u00e9'
    rows[0]["subject"] = original
    rows[0]["length"] = None
    for row in rows:
        row["unselected_source_field"] = 'original, "audit-only"'
    main, _, manifest = write_handoff(tmp_path, rows, vectors)
    main.write_bytes(b"\xef\xbb\xbf" + main.read_bytes())
    update_handoff_hash(main, manifest)
    result = load_development_dataset(tmp_path, "synthetic-v1", specification=spec())
    assert result.observations[0].conventional == (original, None)
    assert development_folds(result, "E1")[0].feature_names == ("subject", "length")


@pytest.mark.parametrize("location", ["run", "development_directory", "manifest", "main", "behavior"])
@pytest.mark.parametrize("outside_run", [False, True])
def test_fixed_handoff_paths_reject_redirection_before_opening_files(tmp_path, monkeypatch, location, outside_run):
    rows, vectors = fixture_rows()
    main, behavior, manifest = write_handoff(tmp_path, rows, vectors)
    run = tmp_path / "experiments/runs/synthetic-v1"
    source = {"run": run, "development_directory": main.parent, "manifest": manifest,
              "main": main, "behavior": behavior}[location]
    target = (tmp_path / "elsewhere" if outside_run else run / "test") / source.name
    original_resolve, original_open = Path.resolve, Path.open
    def redirected(path, *args, **kwargs):
        if path == source or source in path.parents:
            return target / path.relative_to(source)
        return original_resolve(path, *args, **kwargs)
    def guard(path, *args, **kwargs):
        assert path != target and target not in path.parents, "Redirected input was opened"
        return original_open(path, *args, **kwargs)
    with monkeypatch.context() as patch:
        # Model a resolved symlink/junction without Windows privilege requirements.
        patch.setattr(Path, "resolve", redirected)
        patch.setattr(Path, "open", guard)
        with pytest.raises(InputContractError):
            load_development_dataset(tmp_path, "synthetic-v1", specification=spec())


def test_explicit_checkout_alias_can_resolve_to_the_intended_checkout(tmp_path, monkeypatch):
    rows, vectors = fixture_rows()
    write_handoff(tmp_path, rows, vectors)
    alias = tmp_path / "caller-checkout-alias"
    original_resolve = Path.resolve
    def resolve(path, *args, **kwargs):
        return original_resolve(tmp_path) if path == alias else original_resolve(path, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(Path, "resolve", resolve)
        assert len(load_development_dataset(alias, "synthetic-v1", specification=spec()).observations) == 10


@pytest.mark.parametrize("run_id", ["../other", "nested/run", "C:\\other", "/absolute", "", None, True])
def test_invalid_run_paths_are_rejected_without_any_input_read(tmp_path, monkeypatch, run_id):
    def forbidden(*args, **kwargs):
        pytest.fail("An input was read for an invalid run ID")
    monkeypatch.setattr(Path, "read_text", forbidden)
    with pytest.raises(InputContractError, match="invalid_run_id"):
        load_development_dataset(tmp_path, run_id, specification=spec())


@pytest.mark.parametrize("key", ["contract_version", "development_file", "behavioral_sha256"])
def test_conflicting_duplicate_manifest_keys_are_rejected(tmp_path, key):
    rows, vectors = fixture_rows()
    _, _, manifest = write_handoff(tmp_path, rows, vectors)
    text = manifest.read_text(encoding="utf-8")
    text = text.replace(f'"{key}": ', f'"{key}": "conflicting", "{key}": ', 1)
    manifest.write_text(text, encoding="utf-8")
    with pytest.raises(InputContractError):
        load_development_dataset(tmp_path, "synthetic-v1", specification=spec())
