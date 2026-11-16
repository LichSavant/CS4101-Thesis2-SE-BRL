"""Named approved Email/PhiUSIIL snapshots: aggregate native-data audit only.

No semantic relabeling, eligibility decision, group/partition allocation, learned
processing or row export. Original ingestion positions are counted before any
filtering; content hashes are transient duplicate diagnostics, not lineage proof.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re

from ml.experiment_inputs import InputContractError
from ml.metadata import fingerprint
from ml.source_audit import write_source_audit, _reference

VERSION = "named-csv-native-source-audit-0.1.0"
EMAIL = {"Enron", "Nazario", "SpamAssassin", "CEAS-08"}


def audit_csv(source, *, dataset, expected_sha256, expected_md5, max_bytes,
              source_reference, license_reference, authorization_reference, max_field_chars):
    if (dataset not in EMAIL | {"PhiUSIIL"} or type(expected_sha256) is not str
            or not re.fullmatch(r"[a-f0-9]{64}", expected_sha256)
            or (expected_md5 is not None and (type(expected_md5) is not str or not re.fullmatch(r"[a-f0-9]{32}", expected_md5)))
            or type(max_bytes) is not int or max_bytes < 1
            or type(max_field_chars) is not int or max_field_chars < 1):
        raise InputContractError("explicit_named_source_audit_contract_required")
    references = {"source": _reference(source_reference), "license": _reference(license_reference),
                  "access_authorization": _reference(authorization_reference)}
    path = Path(source)
    if not path.is_file() or path.stat().st_size > max_bytes:
        raise InputContractError("bounded_materialized_source_required")
    payload = path.read_bytes()
    if (len(payload) > max_bytes or hashlib.sha256(payload).hexdigest() != expected_sha256
            or (expected_md5 is not None and hashlib.md5(payload).hexdigest() != expected_md5)
            or payload.startswith(b"version https://git-lfs.github.com/spec/v1")):
        raise InputContractError("source_digest_or_materialization_mismatch")
    old_limit = csv.field_size_limit()
    counts, empty, reasons, literal_missing = Counter(), Counter(), Counter(), Counter()
    duplicate_labels, native_keys = defaultdict(set), Counter()
    repeated = Counter()
    count = 0
    try:
        csv.field_size_limit(max_field_chars)
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig"), newline=""), strict=True)
        headers = reader.fieldnames
        required = {"label", "subject", "body"} if dataset in EMAIL else {"FILENAME", "URL", "Domain", "TLD", "Title", "label"}
        if (not headers or len(set(headers)) != len(headers) or not required <= set(headers)
                or any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", n) for n in headers)):
            raise InputContractError("named_source_schema_mismatch")
        for row in reader:
            count += 1
            if None in row or any(v is None for v in row.values()):
                reasons["malformed_column_count"] += 1
                continue
            native = row["label"]
            if native not in {"0", "1"}:
                reasons["unexpected_native_label"] += 1
            counts[native if native in {"0", "1"} else "other"] += 1
            for name in headers:
                if not row[name].strip():
                    empty[name] += 1
                if row[name].casefold() in {"nan", "null", "none", "na"}:
                    literal_missing[name] += 1  # diagnostic, not a missingness conversion
            if dataset in EMAIL:
                # Exact decoded strings; NO normalization. Source labels are
                # excluded from duplicate identity, retained only for conflicts.
                key = fingerprint({"subject": row["subject"], "body": row["body"]})
            else:
                key = fingerprint({"native_url_string": row["URL"]})
                native_keys[hashlib.sha256(row["FILENAME"].encode()).hexdigest()] += 1
            duplicate_labels[key].add(native)
            repeated[key] += 1
        if count < 1:
            raise InputContractError("source_population_empty")
    except (csv.Error, UnicodeError, OverflowError):
        raise InputContractError("source_csv_parse_or_field_budget_failed") from None
    finally:
        csv.field_size_limit(old_limit)
    return {"version": VERSION, "category": "ACTUAL SOURCE AUDIT; NOT A MODEL RESULT", "dataset": dataset, "source_file": source.name,
            "snapshot_sha256": expected_sha256, "official_md5_matched": expected_md5,
            "source_bytes": len(payload), "references": references, "schema": headers,
            "source_records": count, "native_label_counts": dict(sorted(counts.items())),
            "reason_counts": dict(reasons), "empty_or_whitespace_field_counts": dict(empty),
            "literal_missing_token_counts_not_converted": dict(literal_missing),
            "distinct_exact_content_keys": len(repeated), "repeated_exact_content_records": sum(n-1 for n in repeated.values()),
            "mixed_native_label_exact_content_keys": sum(len(v) > 1 for v in duplicate_labels.values()),
            "distinct_native_filename_keys": len(native_keys) if dataset == "PhiUSIIL" else None,
            "duplicate_native_filename_records": sum(n-1 for n in native_keys.values()) if dataset == "PhiUSIIL" else None,
            "diagnostic_key_normalization": "exact decoded subject/body strings" if dataset in EMAIL else "exact native URL string",
            "diagnostic_keys_exported": False, "target_mapping_status": "native codes retained; no mapping applied",
            "population_status": "not_screened_not_frozen", "language_status": "not_inferred",
            "groups_generated": 0, "assignments_generated": 0, "model_fits": 0,
            "limitations": ["Checksum equivalence establishes release bytes, not native class meaning or row-level historical lineage.",
                            "Duplicate diagnostics do not select a scientific exclusion or grouping policy.",
                            "No previously exposed observations are resealed by this audit."]}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True)
    p.add_argument("--dataset", required=True, choices=sorted(EMAIL | {"PhiUSIIL"}))
    p.add_argument("--expected-sha256", required=True)
    p.add_argument("--expected-md5")
    p.add_argument("--max-bytes", required=True, type=int)
    p.add_argument("--max-field-chars", required=True, type=int)
    p.add_argument("--source-reference", required=True)
    p.add_argument("--license-reference", required=True)
    p.add_argument("--authorization-reference", required=True)
    p.add_argument("--output", required=True)
    args = vars(p.parse_args(argv))
    output = args.pop("output")
    try:
        report = audit_csv(**args)
        digest = write_source_audit(output, report)
    except (InputContractError, OSError):
        print(json.dumps({"status": "failed", "code": "named_source_audit_failed"}))
        return 2
    print(json.dumps({"status": "source_audited_not_frozen", "dataset": report["dataset"],
        "source_records": report["source_records"], "native_label_counts": report["native_label_counts"],
        "report_sha256": digest, "model_fits": 0, "assignments_generated": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
