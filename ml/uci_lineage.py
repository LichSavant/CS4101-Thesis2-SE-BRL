"""Consistency checks for a future custodian-supplied prospective UCI ledger.

No ARFF/file loader, identity reconstruction, assignments, approvals or model
execution. Call only on metadata already permitted for inspection. Hash equality
cannot authenticate a source record or turn prospective IDs into historical IDs.
"""
from collections import defaultdict
import re

from ml.experiment_inputs import InputContractError
from ml.research_protocol import prospective_id


FIELDS = frozenset({"source_row_id", "observation_id", "native_label", "record_sha256",
                    "predictor_sha256", "action", "representative_id", "cleaned_position"})


def validate_prospective_uci_ledger(records, *, snapshot_sha256, original_count, retained_count):
    """Check original-position coverage and declared first-occurrence deduplication.

    The proposed policy preserves distinct native-label records sharing a
    predictor vector. Supplied digests must ultimately be recomputed by the
    authorized custodian; this metadata-only function cannot verify their truth.
    Counts are explicit protocol inputs, never estimated from a partial ledger.
    Returned aggregates neither authenticate custody nor authorize source access.
    """
    if (type(records) not in (list, tuple) or type(original_count) is not int
            or type(retained_count) is not int or not 0 < retained_count <= original_count
            or len(records) != original_count or type(snapshot_sha256) is not str
            or not re.fullmatch(r"[a-f0-9]{64}", snapshot_sha256)):
        raise InputContractError("explicit_complete_uci_ledger_scope_required")
    by_id, positions, buckets = {}, set(), defaultdict(list)
    for row in records:
        if type(row) is not dict or set(row) != FIELDS:
            raise InputContractError("exact_uci_lineage_metadata_schema_required")
        position = row["source_row_id"]
        if (type(position) is not int or not 0 <= position < original_count
                or position in positions or type(row["native_label"]) is not int
                or row["native_label"] not in {-1, 1}
                or any(type(row[k]) is not str or not re.fullmatch(r"[a-f0-9]{64}", row[k])
                       for k in ("record_sha256", "predictor_sha256"))):
            raise InputContractError("invalid_uci_original_position_or_native_record")
        expected_id = prospective_id("UCI Phishing Websites", snapshot_sha256,
                                     "Training Dataset.arff", position)
        if type(row["observation_id"]) is not str or row["observation_id"] != expected_id:
            raise InputContractError("uci_original_locator_identifier_mismatch")
        if row["observation_id"] in by_id:
            raise InputContractError("duplicate_uci_original_identifier")
        positions.add(position)
        by_id[row["observation_id"]] = row
        buckets[row["record_sha256"]].append(row)
    retained = []
    for bucket in buckets.values():
        representative = min(bucket, key=lambda row: row["source_row_id"])
        for row in bucket:
            if (row["native_label"] != representative["native_label"]
                    or row["predictor_sha256"] != representative["predictor_sha256"]):
                raise InputContractError("uci_record_digest_has_conflicting_assertions")
            action = "retain" if row is representative else "duplicate"
            if row["action"] != action or row["representative_id"] != representative["observation_id"]:
                raise InputContractError("uci_first_occurrence_or_duplicate_receipt_mismatch")
            if action == "retain":
                retained.append(row)
            elif row["cleaned_position"] is not None:
                raise InputContractError("uci_removed_record_has_cleaned_position")
    retained.sort(key=lambda row: row["source_row_id"])
    if len(retained) != retained_count:
        raise InputContractError("uci_retained_count_mismatch")
    for position, row in enumerate(retained):
        if type(row["cleaned_position"]) is not int or row["cleaned_position"] != position:
            raise InputContractError("uci_cleaned_order_or_coverage_mismatch")
    predictor_labels = defaultdict(set)
    # Equal predictors plus equal labels must have been the same complete record.
    predictor_label_records = {}
    for row in retained:
        key = (row["predictor_sha256"], row["native_label"])
        if key in predictor_label_records:
            raise InputContractError("uci_complete_duplicate_not_removed")
        predictor_label_records[key] = row["record_sha256"]
        predictor_labels[row["predictor_sha256"]].add(row["native_label"])
    return {
        "scope": "supplied_prospective_lineage_metadata_consistency_only",
        "original_records": original_count, "retained_records": retained_count,
        "removed_complete_duplicates": original_count - retained_count,
        "predictor_groups": len(predictor_labels),
        "mixed_native_label_groups": sum(len(labels) > 1 for labels in predictor_labels.values()),
        "source_record_digests_recomputed": False, "source_custody_established": False,
        "historical_identity_bridge_established": False, "scientific_admission": False,
        "model_fits": 0,
    }
