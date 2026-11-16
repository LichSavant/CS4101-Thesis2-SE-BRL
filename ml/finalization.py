"""Non-mutating integrity preflight and no-fit research handoff.

Run: python -B -m ml.finalization --root /path/to/repo
Optional --output uses exclusive creation. This module never imports the backend,
loads a model, fits features, executes a notebook, or writes research artifacts.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

from ml.annotation_validation import acceptance_gate, indicator_ids
from ml.research_policy import fingerprint, iter_verified_csv, load_policy, verify_artifact
from ml.se_brl.representation_contract import contract


DATASETS = {
    "email": "email_preprocessed.csv", "phiusiil": "phiusiil_preprocessed.csv",
    "iscx": "iscx_url2016_preprocessed.csv", "uci": "uci_phishing_websites_preprocessed.csv",
}
METADATA = ("target", "group_id", "partition", "cv_fold")
XML_NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def metadata(root: Path, relative: str) -> dict:
    result = {}
    for row in iter_verified_csv(root / relative, root):
        key = row.get("observation_id")
        if not key or key in result:
            raise ValueError("Missing or duplicated observation ID")
        result[key] = tuple(row.get(field, "") for field in METADATA)
    return result


def partition_report(rows: dict) -> dict:
    parts, folds, targets, group_parts, group_folds = Counter(), Counter(), Counter(), defaultdict(set), defaultdict(set)
    errors = []
    if not rows:
        errors.append("empty_dataset")
    for key, (target, group, part, fold) in rows.items():
        if target not in {"0", "1"} or not group or part not in {"development", "calibration", "test"}:
            errors.append("invalid_metadata")
        if (part == "development" and fold not in {"1", "2", "3", "4", "5", "1.0", "2.0", "3.0", "4.0", "5.0"}) or (part != "development" and fold):
            errors.append("invalid_fold_membership")
        parts[part] += 1
        targets[target] += 1
        group_parts[group].add(part)
        if part == "development":
            folds[fold] += 1
            group_folds[group].add(fold)
    cross_parts = sum(len(value) > 1 for value in group_parts.values())
    cross_folds = sum(len(value) > 1 for value in group_folds.values())
    metadata_hash = hashlib.sha256(json.dumps(sorted(rows.items()), separators=(",", ":")).encode()).hexdigest()
    group_hash = hashlib.sha256(json.dumps(sorted((key, value[1]) for key, value in rows.items()), separators=(",", ":")).encode()).hexdigest()
    return {"rows": len(rows), "partitions": dict(parts), "targets": dict(targets),
            "development_folds": dict(folds), "groups_crossing_partitions": cross_parts,
            "groups_crossing_folds": cross_folds, "errors": dict(Counter(errors)),
            "partition_metadata_sha256": metadata_hash, "group_membership_sha256": group_hash,
            "supplied_group_integrity": not errors and not cross_parts and not cross_folds,
            "campaign_source_temporal_independence_established": False}


def phiusiil_lineage(root: Path) -> dict:
    raw_path = "experiments/datasets-raw/webpage/PhiUSIL/PhiUSIIL_Phishing_URL_Dataset.csv"
    clean_path = "experiments/data/interim/webpage/phiusiil_clean.csv"
    processed_path = "experiments/data/processed/preprocessed/phiusiil_preprocessed.csv"
    string_fields = {"FILENAME", "URL", "Domain", "TLD", "Title"}
    rows, headers, labels = [], None, []
    def row_digest(row):
        values = []
        for key in headers:
            value = row.get(key, "")
            if key not in string_fields and value:
                try:
                    number = Decimal(value)
                    if not number.is_finite():
                        raise ValueError("Non-finite native value")
                    value = str(number.normalize())
                except InvalidOperation:
                    raise ValueError("Invalid native numeric value") from None
            values.append(value)
        return hashlib.sha256(json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode()).digest()
    for row in iter_verified_csv(root / raw_path, root):
        if headers is None:
            headers = tuple(row)
        rows.append(row_digest(row))
        labels.append(row["label"])
    clean_count = clean_mismatch = 0
    for index, row in enumerate(iter_verified_csv(root / clean_path, root)):
        clean_count += 1
        clean_mismatch += index >= len(rows) or row_digest(row) != rows[index]
    seen, processed_mismatch, target_mismatch = set(), 0, 0
    for row in iter_verified_csv(root / processed_path, root):
        source_id = int(row["source_row_id"])
        if source_id in seen or not 0 <= source_id < len(rows):
            raise ValueError("Invalid PhiUSIIL source-row identity")
        seen.add(source_id)
        processed_mismatch += row_digest(row) != rows[source_id]
        target_mismatch += row["target"] != {"0": "1", "1": "0"}[labels[source_id]]
        if row["observation_id"] != f"PhiUSIIL::{source_id}":
            raise ValueError("PhiUSIIL observation identity changed")
    archive = root / "experiments/datasets-raw/webpage/PhiUSIL/phiusiil+phishing+url+dataset.zip"
    with zipfile.ZipFile(archive) as stream:
        members = stream.namelist()
        archive_matches = members == ["PhiUSIIL_Phishing_URL_Dataset.csv"] and hashlib.sha256(stream.read(members[0])).hexdigest() == fingerprint(root / raw_path)
    complete = clean_count == len(rows) == len(seen)
    return {"raw_rows": len(rows), "clean_rows": clean_count, "processed_source_rows": len(seen),
            "raw_to_clean_native_field_mismatches": clean_mismatch,
            "raw_to_processed_native_field_mismatches": processed_mismatch,
            "native_label_mapping_mismatches": target_mismatch,
            "numeric_comparison_policy": "Decimal normalization only; text fields exact",
            "archive_csv_matches_raw": archive_matches,
            "local_lineage_verified": complete and not clean_mismatch and not processed_mismatch and not target_mismatch and archive_matches,
            "upstream_acquisition_receipt_verified": False, "license_independently_verified": False,
            "native_web_evidence": ["Title", "URL", "Domain", "engineered structural columns"],
            "original_html_screenshots_identity_evidence_available": False}


def worksheet_rows(path: Path) -> list[dict[str, str]]:
    """Read first-sheet values without formulas/macros, retaining no workbook edits."""
    with zipfile.ZipFile(path) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ["".join(item.itertext()) for item in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("s:si", XML_NS)]
        rows = []
        for row in ET.fromstring(archive.read("xl/worksheets/sheet1.xml")).findall("s:sheetData/s:row", XML_NS):
            values = {}
            for cell in row.findall("s:c", XML_NS):
                col = "".join(char for char in cell.attrib["r"] if char.isalpha())
                value = cell.find("s:v", XML_NS)
                text = value.text if value is not None else ""
                if cell.get("t") == "s":
                    text = strings[int(text)] if text else ""
                elif cell.get("t") == "inlineStr":
                    text = "".join(item.text or "" for item in cell.findall(".//s:t", XML_NS))
                values[col] = text or ""
            rows.append(values)
    if not rows:
        return []
    return [{header: row.get(col, "") for col, header in rows[0].items()} for row in rows[1:] if any(row.values())]


def annotation_inventory(root: Path) -> dict:
    folder = root / "experiments/vera_validation"
    with (folder / "vera_behavioral_annotations.csv").open(newline="") as stream:
        vera = list(csv.DictReader(stream))
    independent = worksheet_rows(folder / "independent_annotator_blank.xlsx")
    ids = indicator_ids()
    return {"vera_items": len(vera), "vera_populated_indicator_cells": sum(bool(row.get(i, "").strip()) for row in vera for i in ids),
            "independent_items": len(independent), "independent_populated_indicator_cells": sum(bool(row.get(i, "").strip()) for row in independent for i in ids),
            "independent_validation_complete": False, "expert_provenance_verified": False,
            "annotation_source_approved": False, "new_blinded_packet_generated": False}


def preflight(root: Path) -> dict:
    root = root.resolve()
    policy = load_policy()
    checks, failures = [], []
    for relative in policy["artifacts"]:
        try:
            checks.append(verify_artifact(root / relative, root))
        except (OSError, ValueError) as error:
            failures.append({"path": relative, "reason": str(error)})
    datasets = {}
    for name, filename in DATASETS.items():
        try:
            main = metadata(root, f"experiments/data/processed/preprocessed/{filename}")
            feature = metadata(root, f"experiments/data/processed/features/sebrl/{name}_sebrl_features.csv")
            partition = metadata(root, f"experiments/results/preprocessing/partitions/{name}_partition_manifest.csv")
            report = partition_report(main)
            report.update(feature_metadata_matches=main == feature, partition_manifest_matches=main == partition)
            datasets[name] = report
            if not report["supplied_group_integrity"] or main != feature or main != partition:
                failures.append({"dataset": name, "reason": "metadata_integrity_failed"})
        except (OSError, ValueError, KeyError) as error:
            failures.append({"dataset": name, "reason": str(error)})
    contingency = Counter()
    try:
        for row in iter_verified_csv(root / "experiments/data/processed/preprocessed/email_preprocessed.csv", root):
            contingency[(row["source_dataset"], row["target"])] += 1
        lineage = phiusiil_lineage(root)
        if not lineage["local_lineage_verified"]:
            failures.append({"dataset": "phiusiil", "reason": "native_lineage_not_verified"})
    except (OSError, ValueError, KeyError) as error:
        lineage = {"local_lineage_verified": False, "reason": str(error)}
        failures.append({"dataset": "custody", "reason": str(error)})
    report = {"report_version": "1.1.0", "mode": "integrity_inspection_only_no_fit",
            "integrity_checks_pass": not failures, "failures": failures, "checked_artifacts": checks,
            "datasets": datasets, "phiusiil_lineage": lineage,
            "historical_email_source_target_counts": [{"source": source, "target": target, "rows": count} for (source, target), count in sorted(contingency.items())],
            "historical_email_source_independent_performance_established": False,
            "historical_holdout": "already_evaluated; no new model selection authorized",
            "representation_contract": contract(), "acceptance_gates": acceptance_gate(),
            "annotation_inventory": annotation_inventory(root),
            "excluded_datasets": policy["excluded_dataset_identifiers"],
            "approved_active_dataset_ids": [], "accepted_experiment_features": [],
            "model_inference_executed": False, "actual_data_fitting_executed": False,
            "upstream_provenance_independently_verified": False,
            "Dhanwil_interface_verified": False,
            "remaining_gates": ["primary_email_dataset_decision", "scientific_representation_approval",
                "independent_annotations_and_adjudication", "semantic_policy_validation",
                "upstream_custody_and_license", "evaluation_exposure_policy", "Dhanwil_authoritative_interface"]}
    from ml.handoff import integration_interface, compare_interface
    report["integrity_dimensions"] = {
        "local_artifact_integrity_verified": not failures,
        "partition_consistency_verified": bool(datasets) and all(entry["supplied_group_integrity"]
            and entry["feature_metadata_matches"] and entry["partition_manifest_matches"] for entry in datasets.values()),
        "upstream_source_custody_verified": False, "scientific_dataset_validity_approved": False}
    report["integration_interface"] = integration_interface(report) if not failures else None
    report["integration_comparison"] = compare_interface(report["integration_interface"] or {}, None)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="Create a new engineering report exclusively; never overwrite")
    parser.add_argument("--compare-interface", type=Path, help="Compare a supplied declaration only; never modify another checkout")
    args = parser.parse_args()
    report = preflight(args.root)
    if args.compare_interface and report["integration_interface"] is not None:
        from ml.handoff import compare_interface, load_interface
        try:
            supplied = load_interface(args.compare_interface)
            report["integration_comparison"] = compare_interface(report["integration_interface"], supplied)
        except (OSError, ValueError):
            report["integration_comparison"] = {"status": "INCOMPATIBLE", "actual_interface_supplied": True,
                "declaration_compatible": False, "research_release_approved": False, "mismatches": ["interface_unreadable_or_malformed"]}
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(payload)
    else:
        print(payload, end="")
    if not report["integrity_checks_pass"]:
        return 1
    return 2 if report["integration_comparison"]["status"] == "INCOMPATIBLE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
