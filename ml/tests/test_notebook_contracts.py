"""Synthetic Notebook 03/04 boundaries; never execute notebook cells or fit models."""
import json

import pytest

from ml.experiment_inputs import InputContractError, select_predictors
from ml.notebook_contracts import (
    DATASET_ROLES, assert_new_outputs, build_email_population,
    canonical_notebook_codebook, capture_population, email_evidence_availability,
    technical_indicator_columns, validate_feature_boundary,
    validate_metadata_alignment, validate_population_coverage,
)
from ml.se_brl.codebook import load_codebook


def source_row(label, n=0):
    return {"label": label, "subject": f"Synthetic subject {n}", "body": f"Synthetic body {n}"}


def sources():
    return {
        "Nazario": [source_row(1, i) for i in range(7)],
        "Enron": [source_row(1)] + [source_row(0, i) for i in range(7)],
        "SpamAssassin": [source_row(1), source_row(0, 20)],
        "CEAS-08": [source_row(0, 30), source_row(1, 31)],
    }


def batch():
    rows = [dict(row) for row in build_email_population(sources())]
    counts = {0: 0, 1: 0}
    for row in rows:
        counts[row["target"]] += 1
        n = counts[row["target"]]
        row.update(group_id=f"group::{row['observation_id']}",
                   partition="development" if n <= 5 else ("calibration" if n == 6 else "test"),
                   cv_fold=n if n <= 5 else None)
    return rows


def manifest(rows):
    keys = ("observation_id", "source_dataset", "target", "group_id", "partition", "cv_fold")
    return [{key: row[key] for key in keys} for row in rows]


def test_restored_construction_preserves_native_semantics_and_pre_filter_positions():
    data = sources()
    class AuxiliaryMustNotBeRead:
        def __iter__(self):
            pytest.fail("Auxiliary CEAS records reached primary construction")
    data["CEAS-08"] = AuxiliaryMustNotBeRead()
    rows = build_email_population(data)
    assert len(rows) == 15
    assert {r["source_dataset"] for r in rows} == {"Nazario", "Enron", "SpamAssassin"}
    enron = [r for r in rows if r["source_dataset"] == "Enron"]
    assert enron[0]["source_row_id"] == 1 and enron[0]["observation_id"] == "Enron::1"
    assert all(r["label"] == r["source_label"] == r["target"] for r in rows)
    assert all(r["language"] == "und" and "urls" not in r for r in rows)
    assert "source_dataset" not in data["Nazario"][0]


@pytest.mark.parametrize("native", [None, True, "1", 2, -1, 0])
def test_unexpected_nazario_labels_are_rejected_instead_of_relabeling(native):
    data = sources()
    data["Nazario"][0]["label"] = native
    with pytest.raises(InputContractError, match="unexpected_native_email_label"):
        build_email_population(data)


@pytest.mark.parametrize("field", ["subject", "body", "label"])
def test_missing_required_email_fields_fail(field):
    data = sources()
    del data["Nazario"][0][field]
    with pytest.raises(InputContractError, match="missing_required_email_fields"):
        build_email_population(data)


def test_unavailable_text_is_preserved_for_screening_not_silently_filled():
    data = sources()
    data["Nazario"][0].update(subject=None, body=None)
    assert build_email_population(data)[0]["body"] is None


def test_runtime_transport_bounds_do_not_become_new_corpus_exclusions():
    data = sources()
    original = "synthetic " * 21_000
    data["Nazario"][0]["body"] = original
    assert build_email_population(data)[0]["body"] == original


@pytest.mark.parametrize("language", [True, 1, "", "English"])
def test_language_encoding_is_validated_without_inferring_english(language):
    data = sources()
    data["Nazario"][0]["language"] = language
    with pytest.raises(InputContractError, match="invalid_language_encoding"):
        build_email_population(data)


@pytest.mark.parametrize("mutation", ["drop", "extra", "duplicate", "id", "target", "native", "source", "position"])
def test_exact_population_coverage_rejects_changed_records(mutation):
    rows = batch()
    expected = capture_population(rows, dataset="Email")
    if mutation == "drop": rows.pop()
    elif mutation in {"extra", "duplicate"}:
        row = dict(rows[0])
        if mutation == "extra": row.update(observation_id="new-id", source_row_id=100)
        rows.append(row)
    elif mutation == "id": rows[0]["observation_id"] = "foreign-id"
    elif mutation == "target": rows[0]["target"] = 0
    elif mutation == "native": rows[0]["source_label"] = 0
    elif mutation == "source": rows[0]["source_dataset"] = "CEAS-08"
    elif mutation == "position": rows[0]["source_row_id"] = rows[1]["source_row_id"]
    with pytest.raises(InputContractError):
        validate_population_coverage(rows, expected, dataset="Email")


def test_reordered_observations_and_manifest_preserve_exact_assignments():
    rows = batch()
    expected = capture_population(rows, dataset="Email")
    report = validate_feature_boundary(list(reversed(rows)), dataset="Email", expected_population=expected)
    validate_metadata_alignment(rows, list(reversed(manifest(rows))), dataset="Email")
    assert report["total"] == 15 and report["targets"] == {1: 7, 0: 8}
    assert report["partitions"] == {"development": 10, "calibration": 2, "test": 3}
    dev = [r for r in rows if r["partition"] == "development"]
    validate_feature_boundary(dev, dataset="Email", development_only=True,
                             expected_population={r["observation_id"]: expected[r["observation_id"]] for r in dev})


@pytest.mark.parametrize("mutation", ["group_cross_partition", "group_cross_fold", "reserved_fold",
    "missing_fold", "fractional_fold", "boolean_fold", "string_fold", "large_fold",
    "unknown_partition", "missing_group", "duplicate_id", "missing_fold_class", "missing_partition_class"])
def test_partition_and_fold_boundaries_fail_closed(mutation):
    rows = batch()
    if mutation == "group_cross_partition": rows[5]["group_id"] = rows[0]["group_id"]
    elif mutation == "group_cross_fold": rows[1]["group_id"] = rows[0]["group_id"]
    elif mutation == "reserved_fold": rows[5]["cv_fold"] = 1
    elif mutation == "missing_fold": rows[0]["cv_fold"] = None
    elif mutation == "fractional_fold": rows[0]["cv_fold"] = 1.5
    elif mutation == "boolean_fold": rows[0]["cv_fold"] = True
    elif mutation == "string_fold": rows[0]["cv_fold"] = "1"
    elif mutation == "large_fold": rows[0]["cv_fold"] = 6
    elif mutation == "unknown_partition": rows[0]["partition"] = "other"
    elif mutation == "missing_group": del rows[0]["group_id"]
    elif mutation == "duplicate_id": rows[0]["observation_id"] = rows[1]["observation_id"]
    elif mutation == "missing_fold_class": rows.pop(0)
    elif mutation == "missing_partition_class": rows.pop(5)
    with pytest.raises(InputContractError):
        validate_feature_boundary(rows, dataset="Email")


def test_csv_nullable_folds_are_decoded_losslessly():
    rows = batch()
    for row in rows:
        row["cv_fold"] = float(row["cv_fold"]) if row["cv_fold"] else float("nan")
    validate_feature_boundary(rows, dataset="Email")
    validate_metadata_alignment(rows, manifest(rows), dataset="Email")


def test_development_only_boundary_cannot_include_reserved_records():
    with pytest.raises(InputContractError, match="partition_coverage_mismatch"):
        validate_feature_boundary(batch(), dataset="Email", development_only=True)


@pytest.mark.parametrize("column,value", [("observation_id", "foreign-id"), ("source_dataset", "other"),
    ("target", 0), ("target", True), ("target", 1.0), ("group_id", "other"),
    ("partition", "test"), ("cv_fold", 2)])
def test_same_count_manifest_mismatches_are_rejected(column, value):
    rows = batch()
    supplied = manifest(rows)
    supplied[0][column] = value
    with pytest.raises(InputContractError):
        validate_metadata_alignment(rows, supplied, dataset="Email")


@pytest.mark.parametrize("mutation", ["duplicate", "drop", "extra"])
def test_manifest_identifier_coverage_is_exact(mutation):
    rows = batch()
    supplied = manifest(rows)
    if mutation == "drop": supplied.pop()
    elif mutation == "duplicate": supplied.append(dict(supplied[0]))
    else: supplied.append(dict(supplied[0], observation_id="extra-id"))
    with pytest.raises(InputContractError):
        validate_metadata_alignment(rows, supplied, dataset="Email")


def test_missing_links_and_identity_are_unavailable_and_explicit_empty_is_distinct():
    report = email_evidence_availability([
        {"subject": None, "body": None},
        {"subject": "", "body": "text", "sender": "", "urls": []},
        {"subject": "subject", "body": "", "urls": '["https://synthetic.invalid/"]'},
        {"urls": "[]"},
    ])
    assert report["links"] == {"unavailable": 1, "known_empty": 2, "available": 1}
    assert report["sender"] == {"unavailable": 3, "known_empty": 1}
    assert report["subject"] == {"unavailable": 2, "known_empty": 1, "available": 1}


@pytest.mark.parametrize("links", ["", "['untyped']", "{}", '[1]', False])
def test_unknown_link_encodings_are_never_silently_empty(links):
    with pytest.raises(InputContractError):
        email_evidence_availability([{"urls": links}])


@pytest.mark.parametrize("dataset,source,native", [("PhiUSIIL", "PhiUSIIL", {0: 1, 1: 0}),
    ("UCI", "UCI Phishing Websites", {-1: 1, 1: 0})])
def test_technical_target_mapping_and_behavioral_unavailability(dataset, source, native):
    rows = batch()
    reverse = {v: k for k, v in native.items()}
    for row in rows:
        row.update(source_dataset=source, source_row_id=rows.index(row),
                   source_label=reverse[row["target"]], label=reverse[row["target"]],
                   Result=reverse[row["target"]], Title="Act now! Enter your password!",
                   HasPasswordField=1)
    validate_feature_boundary(rows, dataset=dataset)
    values = technical_indicator_columns(dataset)
    assert len(values) == 36
    assert all(value is False for key, value in values.items() if key.endswith(("_supported", "_available")))
    assert all(json.loads(value) == [] for key, value in values.items() if key.endswith("_evidence"))


def test_codebook_ids_and_order_match_existing_canonical_contract():
    book = load_codebook()
    actual = canonical_notebook_codebook()
    assert list(actual) == list(book["vector_ordering"]["dimension_order"])
    assert {i for d in actual.values() for i in d["indicators"]} == {
        i["id"] for d in book["dimensions"] for i in d["indicators"]}
    assert "credential_sensitive_data_request" in actual["requested_action_consequence"]["indicators"]
    # Approved Table 4.7 includes content-bearing Web separately from U1.
    assert set(DATASET_ROLES) == {"Email", "Web", "PhiUSIIL", "UCI"}


@pytest.mark.parametrize("name", ["source_label", "source_row_id", "group_id", "partition", "target",
    "provenance_contract_version", "provenance_rule_status"])
def test_added_provenance_and_labels_are_not_predictors(name):
    with pytest.raises(InputContractError, match="bookkeeping_predictor_forbidden"):
        select_predictors({name: 1}, (name,))


def test_export_preflight_rejects_any_collision_before_writing(tmp_path):
    historical = tmp_path / "historical.csv"
    historical.write_bytes(b"preserve exactly")
    fresh = tmp_path / "fresh.csv"
    with pytest.raises(InputContractError, match="output_exists_or_duplicate_path"):
        assert_new_outputs([fresh, historical])
    assert not fresh.exists() and historical.read_bytes() == b"preserve exactly"
    with pytest.raises(InputContractError):
        assert_new_outputs([fresh, fresh])
    assert_new_outputs([fresh])
    assert not fresh.exists()
