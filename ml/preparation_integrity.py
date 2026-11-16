"""Prospective metadata checks; hashes establish identity, never source custody."""
from collections.abc import Mapping

from ml.experiment_inputs import InputContractError
from ml.metadata import fingerprint
from ml.research_protocol import prospective_id


def validate_preparation_sources(records, branch):
    """Apply the existing notebook branch/source boundary to C and D metadata."""
    from ml.notebook_contracts import EMAIL_SOURCES
    allowed = set(EMAIL_SOURCES) if branch == "Email" else {
        {"Web": "Phishing Website Dataset", "PhiUSIIL": "PhiUSIIL", "UCI": "UCI Phishing Websites"}[branch]}
    if any(r["source_dataset"] not in allowed for r in records):
        raise InputContractError("preparation_population_source_outside_branch")


def validate_development_locators(records, rows, branch):
    """Keep delivered native labels and original positions bound to their IDs."""
    indexed = {r["observation_id"]: r for r in records}
    native_key = {"Email": "label", "Web": "source_label", "PhiUSIIL": "label", "UCI": "Result"}[branch]
    for row in rows:
        expected = indexed.get(row.get("observation_id"))
        if expected is None:
            raise InputContractError("development_locator_not_in_population")
        for key, source_key in (("source_row_id", "source_row_id"), (native_key, "native_label")):
            if type(row.get(key)) is not type(expected[source_key]) or row.get(key) != expected[source_key]:
                raise InputContractError("development_original_locator_or_native_label_changed")
        for key in ("source_file", "snapshot_sha256"):
            if key in row and row[key] != expected[key]:
                raise InputContractError("development_source_snapshot_changed")


def validate_population_assignments(records, assignments):
    """Bind supplied role metadata to accepted source/target population facts."""
    population = {r["observation_id"]: r for r in records}
    indexed = {r["observation_id"]: r for r in assignments}
    if len(indexed) != len(assignments) or set(indexed) != set(population):
        raise InputContractError("exact_assignment_population_required")
    if any(any(row[key] != population[oid][key] for key in ("source_dataset", "target"))
           for oid, row in indexed.items()):
        raise InputContractError("assignment_source_or_target_differs_from_population")


def validate_prospective_population(records):
    """Recompute accepted P3 locators before C allocation or D feature export.

    Native meanings must be supplied in accepted evidence elsewhere; this check
    only ensures a native code has one consistent target within a snapshot.
    No source data, reserved features, or outcomes are loaded.
    """
    if type(records) not in (list, tuple) or not records:
        raise InputContractError("nonempty_prospective_population_required")
    locators, ids, snapshots, meanings = set(), set(), {}, {}
    required = {"observation_id", "source_dataset", "source_file", "source_row_id",
                "snapshot_sha256", "native_label", "target"}
    for row in records:
        if not isinstance(row, Mapping) or not required <= set(row):
            raise InputContractError("prospective_source_snapshot_and_original_position_required")
        source, file, snapshot = row["source_dataset"], row["source_file"], row["snapshot_sha256"]
        oid = prospective_id(source, snapshot, file, row["source_row_id"])
        if row["observation_id"] != oid:
            raise InputContractError("prospective_identifier_does_not_match_source_locator")
        locator = (source, snapshot, file, row["source_row_id"])
        if oid in ids or locator in locators:
            raise InputContractError("duplicate_prospective_identifier_or_original_position")
        ids.add(oid); locators.add(locator)
        if snapshots.setdefault((source, file), snapshot) != snapshot:
            raise InputContractError("source_file_snapshot_changed_within_population")
        native, target = row["native_label"], row["target"]
        if (type(native) not in (str, int) or (type(native) is str and not native.strip())
                or type(target) is not int or target not in (0, 1)):
            raise InputContractError("explicit_native_and_binary_target_required")
        key = (source, snapshot, type(native), native)
        if meanings.setdefault(key, target) != target:
            raise InputContractError("conflicting_native_label_mapping")
    return {"observations":len(ids), "original_locators_sha256":fingerprint(sorted(locators)),
        "population_sha256":fingerprint(sorted((dict(r) for r in records), key=lambda r:r["observation_id"])),
        "source_custody_established":False, "model_fits":0}
