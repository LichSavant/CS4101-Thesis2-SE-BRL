"""UCI-only development preparation from supplied assignments; no input-file loader.

Caller supplies decoded development records, the existing six-column full
partition manifest, an explicit full ID expectation and DevelopmentSpecification.
These assertions do not authenticate source provenance or grant research access.
No source records, groups, labels, partitions, folds or feature definitions are
created here. Actual-data execution remains subject to the research acceptance
gate documented in docs/research/2026-11-01_uci_metadata_readiness.md.
"""
from collections.abc import Iterable, Mapping
from pathlib import Path
import re

from ml.branch_preparation import export_selected_handoff, prepare_selected_branches
from ml.development_experiments import (
    METADATA, DevelopmentSpecification, _within, behavioral_columns,
    build_development_dataset, development_folds, _validate_numeric_predictor,
)
from ml.experiment_inputs import (
    InputContractError, PartitionAssignment, validate_supplied_partitions,
)
from ml.notebook_contracts import (
    _fold, canonical_notebook_codebook, technical_indicator_columns, validate_feature_boundary,
)

# Existing N03 manifest and D9 conventional-input fields, not an alternate schema.
ASSIGNMENT_COLUMNS = frozenset((*METADATA, "source_dataset"))
SOURCE_COLUMNS = frozenset((*METADATA, "source_dataset", "source_row_id", "Result"))
OPTIONAL_AUDIT_COLUMNS = frozenset(("source_label", "feature_hash"))


def _records(values: Iterable[Mapping], reason: str) -> tuple[dict, ...]:
    if isinstance(values, (str, bytes, Mapping)):
        raise InputContractError(reason)
    try:
        rows = tuple(values)
    except TypeError:
        raise InputContractError(reason) from None
    if not rows or any(not isinstance(row, Mapping) for row in rows):
        raise InputContractError(reason)
    return tuple(dict(row) for row in rows)


def prepare_uci_handoff(
    checkout: Path,
    run_id: str,
    development_records: Iterable[Mapping],
    *,
    assignment_manifest: Iterable[Mapping],
    expected_observation_ids: frozenset[str],
    specification: DevelopmentSpecification,
) -> tuple[Path, ...]:
    """Validate the entire supplied batch before creating only three D9 files.

    Manifest rows cover development/calibration/test metadata only. Payload rows
    must cover exactly its development IDs. No reserved predictor payload is
    accepted. expected_observation_ids must come from the caller's independent
    population record; deriving it from the manifest cannot establish completeness.

    Lossless nullable fold decoding uses the existing notebook contract. Original
    records and manifest are never mutated; native numeric codes/nulls are not
    recoded, imputed or learned. Compact zero support WITH zero availability is
    the existing Unavailable encoding, never evidence of behavioral absence.

    This is an in-memory API, not a research authorization check or corpus/CSV
    parser. Nonempty specification references are traceability assertions only.
    """
    if not isinstance(specification, DevelopmentSpecification) or specification.dataset != "UCI":
        raise InputContractError("explicit_uci_specification_required")
    if any(column.kind != "numeric" for column in specification.conventional):
        raise InputContractError("uci_numeric_feature_dictionary_required")
    derived = set(technical_indicator_columns("UCI")) | {
        f"{dimension}_state" for dimension in canonical_notebook_codebook()
    }
    if any(column.name in derived for column in specification.conventional):
        raise InputContractError("technical_behavioral_evidence_forbidden")
    if (type(expected_observation_ids) is not frozenset or not expected_observation_ids
            or any(type(oid) is not str or not oid.strip() for oid in expected_observation_ids)):
        raise InputContractError("explicit_uci_population_ids_required")
    if type(run_id) is not str or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", run_id):
        raise InputContractError("invalid_run_id")
    run_root = _within(Path(checkout), "experiments/runs/" + run_id)

    manifest = _records(assignment_manifest, "uci_assignment_manifest_required")
    if any(set(row) != ASSIGNMENT_COLUMNS for row in manifest):
        raise InputContractError("uci_assignment_schema_mismatch")
    if any(row["source_dataset"] != "UCI Phishing Websites"
           or type(row["target"]) is not int or row["target"] not in (0, 1)
           or type(row["partition"]) is not str
           for row in manifest):
        raise InputContractError("invalid_source_target_mapping")
    assignments = tuple(PartitionAssignment(row["observation_id"], row["group_id"],
                                           row["partition"], _fold(row["cv_fold"]))
                        for row in manifest)
    counts = validate_supplied_partitions(assignments, folds=5)
    if not all(counts.values()):
        raise InputContractError("partition_coverage_mismatch")
    if {row["observation_id"] for row in manifest} != expected_observation_ids:
        raise InputContractError("uci_assignment_population_mismatch")
    for partition in counts:
        if {row["target"] for row in manifest if row["partition"] == partition} != {0, 1}:
            raise InputContractError("partition_requires_both_classes")
    indexed = {row["observation_id"]: row for row in manifest}

    rows = _records(development_records, "uci_development_records_required")
    features = {column.name for column in specification.conventional}
    required = SOURCE_COLUMNS | features
    if any(not required.issubset(row) or set(row) - required - OPTIONAL_AUDIT_COLUMNS for row in rows):
        raise InputContractError("uci_development_schema_mismatch")
    if any("feature_hash" in row and (type(row["feature_hash"]) is not str
                                     or not row["feature_hash"].strip()) for row in rows):
        raise InputContractError("invalid_uci_audit_hash")
    validate_feature_boundary(rows, dataset="UCI", development_only=True)
    development_ids = {row["observation_id"] for row in manifest if row["partition"] == "development"}
    if {row["observation_id"] for row in rows} != development_ids:
        raise InputContractError("uci_development_population_mismatch")
    for row in rows:
        expected = indexed[row["observation_id"]]
        if any((_fold(row[key]) != _fold(expected[key]) if key == "cv_fold"
                else row[key] != expected[key]) for key in ASSIGNMENT_COLUMNS):
            raise InputContractError("partition_manifest_mismatch")
        # Reject nonfinite values before the unchanged-source comparison in the
        # dispatcher (NaN is not equal to itself). Same numeric/null rule as D9.
        for column in specification.conventional:
            value = row[column.name]
            _validate_numeric_predictor(value)

    prepared = prepare_selected_branches({"UCI": rows}, ("UCI",))["UCI"]
    vectors = tuple({key: row[key] for key in (*METADATA, *behavioral_columns())}
                    for row in prepared)
    # D9's typed in-memory vectors use integer folds; normalize only this
    # validation view. Export retains the supplied lossless fold representation.
    typed_vectors = tuple({**row, "cv_fold": _fold(row["cv_fold"])} for row in vectors)
    dataset = build_development_dataset(rows, typed_vectors, specification=specification)
    development_folds(dataset, "U1")  # Validates raw fold plans; never fits anything.
    return export_selected_handoff(run_root, ("UCI",), {"UCI": rows}, {"UCI": vectors})

