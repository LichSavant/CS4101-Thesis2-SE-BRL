"""Notebook 03/04 mechanics from the approved paper; no IO, fitting or splitting.

These checks do not certify source provenance, screening, language or grouping
science. Population construction is pre-audit, not an Audited and Frozen claim.
"""
from collections import Counter
from collections.abc import Iterable, Mapping
import json
import math
from pathlib import Path
import re

from ml.experiment_inputs import (
    Availability, InputContractError, PartitionAssignment,
    validate_supplied_partitions,
)
from ml.se_brl.codebook import load_codebook

PREPARATION_RUN_ID = "paper-preparation-v1"
CONTRACT_VERSION = "notebook-boundary-0.1.0"
DATASET_ROLES = {"Email": "Email-E1/E2/E3", "Web": "Web-E1/E2/E3", "PhiUSIIL": "U1-Ph", "UCI": "U1-UCI"}
EMAIL_SOURCES = ("Nazario", "Enron", "SpamAssassin")
LABEL_MAPPINGS = {
    "Nazario": {1: 1}, "Enron": {0: 0}, "SpamAssassin": {0: 0},
    "PhiUSIIL": {0: 1, 1: 0}, "UCI Phishing Websites": {-1: 1, 1: 0},
    # Zenodo 8041387 explicitly documents these class-file roles. Retain the
    # producer's textual class names, not an invented numeric native label.
    "Phishing Website Dataset": {"phishing": 1, "legitimate": 0},
}


def _language(value) -> str:
    if value is None:
        return "und"
    if type(value) is not str or not re.fullmatch(r"[a-z]{2,3}(?:-[a-z0-9]{2,8})*", value):
        raise InputContractError("invalid_language_encoding")
    return value


def _text_availability(value) -> Availability:
    # A notebook type check is not a new corpus length/exclusion policy. Runtime
    # transport bounds must not silently become research eligibility limits.
    if value is None:
        return Availability.UNAVAILABLE
    if type(value) is not str:
        raise InputContractError("invalid_text_encoding")
    return Availability.AVAILABLE if value.strip() else Availability.KNOWN_EMPTY


def build_email_population(sources: Mapping[str, Iterable[Mapping]]) -> tuple[dict, ...]:
    """Restore historical construction with CEAS kept auxiliary (P 4.2.1/T4.2).

    Native ham is 0 in the inspected release. Spam (1) in the ham sources is
    excluded, never relabeled. Source positions are assigned BEFORE filtering;
    they locate cleaned-input rows, not recovered raw-file identifiers.
    """
    if not isinstance(sources, Mapping) or not set(EMAIL_SOURCES).issubset(sources):
        raise InputContractError("required_email_sources_missing")
    result = []
    for source in EMAIL_SOURCES:
        for position, supplied in enumerate(sources[source]):
            if not isinstance(supplied, Mapping) or not {"label", "subject", "body"}.issubset(supplied):
                raise InputContractError("missing_required_email_fields")
            native = supplied["label"]
            if type(native) is not int or native not in {0, 1} or (source == "Nazario" and native != 1):
                raise InputContractError("unexpected_native_email_label")
            if source != "Nazario" and native == 1:
                continue
            for name in ("source_dataset", "source_row_id", "source_label", "observation_id", "target"):
                if name in supplied:
                    raise InputContractError("constructed_metadata_already_present")
            row = dict(supplied)
            row.update(source_dataset=source, source_row_id=position, source_label=native,
                       observation_id=f"{source}::{position}", target=LABEL_MAPPINGS[source][native])
            # No language detection or corpus-wide English assumption.
            row["language"] = _language(row.get("language"))
            for name in ("subject", "body", "sender", "receiver"):
                _text_availability(row.get(name))
            result.append(row)
    capture_population(result, dataset="Email")
    return tuple(result)


def capture_population(records: Iterable[Mapping], *, dataset: str) -> dict[str, tuple]:
    """Freeze exact ID/target/native-label/source-position coverage in memory."""
    if dataset not in DATASET_ROLES:
        raise InputContractError("dataset_not_in_approved_notebook_scope")
    allowed = set(EMAIL_SOURCES) if dataset == "Email" else {
        {"Web": "Phishing Website Dataset", "PhiUSIIL": "PhiUSIIL", "UCI": "UCI Phishing Websites"}[dataset]}
    result = {}
    positions = set()
    for row in records:
        if not isinstance(row, Mapping):
            raise InputContractError("record_mapping_required")
        source = row.get("source_dataset")
        native = row.get("source_label" if dataset == "Web" else "label" if dataset != "UCI" else "Result")
        target, position, oid = row.get("target"), row.get("source_row_id"), row.get("observation_id")
        native_type = str if dataset == "Web" else int
        if type(source) is not str or source not in allowed or type(native) is not native_type or native not in LABEL_MAPPINGS[source]:
            raise InputContractError("invalid_source_target_mapping")
        if type(target) is not int or target != LABEL_MAPPINGS[source][native]:
            raise InputContractError("invalid_source_target_mapping")
        if "source_label" in row and (type(row["source_label"]) is not native_type or row["source_label"] != native):
            raise InputContractError("native_label_not_preserved")
        if type(position) is not int or position < 0:
            raise InputContractError("invalid_source_position")
        source_file = row.get("source_file") if dataset == "Web" else None
        if dataset == "Web" and source_file != {"phishing": "phishing.csv", "legitimate": "not-phishing.csv"}[native]:
            raise InputContractError("web_native_class_file_mismatch")
        locator = (source, source_file, position) if dataset == "Web" else (source, position)
        if type(oid) is not str or not oid.strip() or oid in result or locator in positions:
            raise InputContractError("invalid_or_duplicate_observation_id")
        result[oid] = (source, source_file, position, native, target) if dataset == "Web" else (source, position, native, target)
        positions.add(locator)
    if not result or {value[-1] for value in result.values()} != {0, 1}:
        raise InputContractError("nonempty_binary_population_required")
    return result


def validate_population_coverage(records, expected: Mapping, *, dataset: str) -> None:
    if not isinstance(expected, Mapping) or not expected:
        raise InputContractError("explicit_population_required")
    if capture_population(records, dataset=dataset) != expected:
        raise InputContractError("population_coverage_or_mapping_changed")


def _fold(value):
    # CSV columns with reserved null folds may be inferred as floating point.
    # Only lossless integer decoding is allowed; booleans/strings are rejected.
    if value is None or (type(value) is float and math.isnan(value)):
        return None
    if type(value) is int:
        return value
    if type(value) is float and math.isfinite(value) and value.is_integer():
        return int(value)
    raise InputContractError("invalid_fold_encoding")


def validate_feature_boundary(records, *, dataset: str, expected_population=None,
                              development_only: bool = False) -> dict:
    """Validate supplied metadata; never allocate or repair groups/partitions."""
    rows = tuple(records)
    population = capture_population(rows, dataset=dataset)
    if expected_population is not None:
        validate_population_coverage(rows, expected_population, dataset=dataset)
    assignments = []
    for row in rows:
        if not {"group_id", "partition", "cv_fold"}.issubset(row):
            raise InputContractError("required_partition_metadata_missing")
        assignments.append(PartitionAssignment(row["observation_id"], row["group_id"],
                                               row["partition"], _fold(row["cv_fold"])))
        if dataset == "Email":
            if not {"subject", "body"}.issubset(row):
                raise InputContractError("missing_required_email_fields")
            for field in ("subject", "body", "sender", "receiver"):
                _text_availability(row.get(field))
            _language(row.get("language"))
        elif dataset == "Web":
            if not {"html", "visible_text"}.issubset(row):
                raise InputContractError("explicit_web_evidence_availability_required")
            for field in ("html", "visible_text"):
                _text_availability(row[field])
            if all(row[field] is None for field in ("html", "visible_text")):
                raise InputContractError("content_bearing_web_evidence_required")
            _language(row.get("language"))
    counts = validate_supplied_partitions(assignments, folds=5)
    expected_parts = {"development"} if development_only else {"development", "calibration", "test"}
    if {a.partition for a in assignments} != expected_parts:
        raise InputContractError("partition_coverage_mismatch")
    for partition in expected_parts:
        if {r["target"] for r in rows if r["partition"] == partition} != {0, 1}:
            raise InputContractError("partition_requires_both_classes")
    for fold in range(1, 6):
        if {r["target"] for r, a in zip(rows, assignments)
                if a.partition == "development" and a.cv_fold == fold} != {0, 1}:
            raise InputContractError("fold_requires_both_classes")
    return {"total": len(population), "targets": dict(Counter(r["target"] for r in rows)),
            "partitions": counts, "role": DATASET_ROLES[dataset], "contract_version": CONTRACT_VERSION}


def validate_metadata_alignment(records, manifest, *, dataset: str) -> None:
    """Require an exact one-to-one manifest join, including reserved null folds."""
    rows, supplied = tuple(records), tuple(manifest)
    validate_feature_boundary(rows, dataset=dataset)
    columns = ("source_dataset", "target", "group_id", "partition", "cv_fold")
    def index(items):
        result = {}
        for row in items:
            if not {"observation_id", *columns}.issubset(row):
                raise InputContractError("required_partition_metadata_missing")
            oid = row["observation_id"]
            if type(oid) is not str or oid in result:
                raise InputContractError("invalid_or_duplicate_observation_id")
            if type(row["target"]) is not int or row["target"] not in {0, 1}:
                raise InputContractError("invalid_source_target_mapping")
            result[oid] = tuple(_fold(row[c]) if c == "cv_fold" else row[c] for c in columns)
        return result
    if index(rows) != index(supplied):
        raise InputContractError("partition_manifest_mismatch")


def email_evidence_availability(records) -> dict:
    """Inspect supplied fields only; no URL extraction or empty-list fabrication."""
    counts = {field: Counter() for field in ("subject", "body", "sender", "links")}
    for row in records:
        for name in ("subject", "body", "sender"):
            counts[name][_text_availability(row.get(name)).value] += 1
        links = row.get("urls")
        if isinstance(links, str):
            try:
                links = json.loads(links)
            except ValueError:
                raise InputContractError("links_require_documented_json_array") from None
        if links is None:
            availability = Availability.UNAVAILABLE
        elif type(links) in (list, tuple) and all(type(link) is str and link.strip() for link in links):
            availability = Availability.AVAILABLE if links else Availability.KNOWN_EMPTY
        else:
            raise InputContractError("links_require_documented_json_array")
        counts["links"][availability.value] += 1
    return {name: dict(values) for name, values in counts.items()}


def canonical_notebook_codebook() -> dict:
    book = load_codebook()
    by_id = {d["id"]: d for d in book["dimensions"]}
    return {key: {"name": by_id[key]["name"],
                  "indicators": {i["id"]: i["name"] for i in by_id[key]["indicators"]}}
            for key in book["vector_ordering"]["dimension_order"]}


def technical_indicator_columns(dataset: str) -> dict:
    """P Table 4.7: technical fields never establish behavioral evidence."""
    if dataset not in {"PhiUSIIL", "UCI"}:
        raise InputContractError("approved_technical_branch_required")
    result = {}
    for dimension in canonical_notebook_codebook().values():
        for indicator in dimension["indicators"]:
            result.update({f"{indicator}_supported": False,
                           f"{indicator}_available": False,
                           f"{indicator}_evidence": "[]"})
    return result


def assert_new_outputs(paths: Iterable[Path]) -> None:
    """Preflight the complete export set; callers also use exclusive creation."""
    paths = tuple(Path(p) for p in paths)
    if len({p.resolve() for p in paths}) != len(paths) or any(p.exists() for p in paths):
        raise InputContractError("output_exists_or_duplicate_path")
