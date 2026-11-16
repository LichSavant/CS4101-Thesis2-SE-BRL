"""Bounded, no-fit UCI source audit. No groups, targets, splits or estimators.

Counts native codes without interpreting class meaning. An expected digest pins
the input snapshot; references record caller-established access/source facts,
not authenticated scientific acceptance. No corpus discovery or test loader.
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
from ml.metadata import canonical_json, fingerprint

VERSION = "uci-native-source-audit-0.1.0"


def _reference(value):
    if type(value) is not str or not value.strip() or len(value) > 4096:
        raise InputContractError("explicit_source_access_references_required")
    return value


def audit_uci_arff(source, *, expected_sha256, source_reference, license_reference,
                   authorization_reference, max_bytes):
    """Audit the exact supplied public source snapshot; do not screen it into a pool.

    Exact feature-vector collisions and mixed native codes are diagnostics, not
    a new grouping or deduplication policy. No row identifiers/content exported.
    Missing/invalid cells are counted, never imputed or silently removed. A
    malformed structural schema fails before any output can be created.
    """
    if type(expected_sha256) is not str or not re.fullmatch(r"[a-f0-9]{64}", expected_sha256):
        raise InputContractError("independent_source_digest_required")
    if type(max_bytes) is not int or max_bytes < 1:
        raise InputContractError("explicit_source_size_limit_required")
    references = {"source": _reference(source_reference), "license": _reference(license_reference),
                  "access_authorization": _reference(authorization_reference)}
    source = Path(source)
    if source.suffix.lower() != ".arff" or not source.is_file() or source.stat().st_size > max_bytes:
        raise InputContractError("bounded_named_arff_source_required")
    data = source.read_bytes()
    if len(data) > max_bytes or hashlib.sha256(data).hexdigest() != expected_sha256:
        raise InputContractError("source_snapshot_digest_or_size_mismatch")
    if data.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise InputContractError("materialized_source_required")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeError:
        raise InputContractError("source_encoding_invalid") from None
    attributes, body, relation = [], [], None
    in_data = False
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("%"):
            continue
        if in_data:
            body.append(line)
        elif re.fullmatch(r"@data", line, re.I):
            in_data = True
        elif re.match(r"@relation\s+", line, re.I):
            if relation is not None:
                raise InputContractError("duplicate_arff_relation")
            relation = line.split(None, 1)[1]
        else:
            match = re.fullmatch(r"@attribute\s+(?:'([^']+)'|\"([^\"]+)\"|(\S+))\s+\{([^}]+)\}", line, re.I)
            if not match:
                raise InputContractError("unsupported_arff_schema")
            name = next(s for s in match.groups()[:3] if s is not None)
            domain = tuple(v.strip() for v in match.group(4).split(","))
            if (not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) or len(set(domain)) != len(domain)
                    or not domain or any(v not in {"-1", "0", "1"} for v in domain)):
                raise InputContractError("uci_native_schema_invalid")
            attributes.append((name, domain))
    if (not in_data or relation is None or len(attributes) != 31 or len({n.casefold() for n, _ in attributes}) != 31
            or attributes[-1][0].casefold() != "result" or set(attributes[-1][1]) != {"-1", "1"}):
        raise InputContractError("uci_30_features_and_native_result_required")
    reasons, labels = Counter(), Counter()
    value_counts = {name: Counter() for name, _ in attributes[:-1]}
    full_rows = Counter()
    feature_labels = defaultdict(set)
    valid = 0
    for line in body:
        try:
            values = next(csv.reader(io.StringIO(line), strict=True))
        except csv.Error:
            reasons["malformed_csv_record"] += 1
            continue
        values = tuple(v.strip() for v in values)
        if len(values) != len(attributes):
            reasons["wrong_field_count"] += 1
            continue
        if "?" in values:
            reasons["missing_native_cell"] += 1
            continue
        if any(v not in domain for v, (_, domain) in zip(values, attributes)):
            reasons["outside_declared_native_domain"] += 1
            continue
        valid += 1
        labels[values[-1]] += 1
        full_rows[values] += 1
        feature_labels[values[:-1]].add(values[-1])
        for value, (name, _) in zip(values[:-1], attributes[:-1]):
            value_counts[name][value] += 1
    if not body:
        raise InputContractError("source_population_empty")
    return {"version": VERSION, "category": "ACTUAL SOURCE AUDIT; NOT A MODEL RESULT",
        "dataset": "UCI Phishing Websites", "source_file": source.name, "snapshot_sha256": expected_sha256,
        "source_bytes": len(data), "references": references,
        "schema": [{"name": n, "native_domain": list(d)} for n, d in attributes],
        "schema_fingerprint": fingerprint(attributes), "source_records": len(body), "valid_native_records": valid,
        "invalid_native_records": sum(reasons.values()), "reason_counts": dict(sorted(reasons.items())),
        "native_result_counts": dict(sorted(labels.items())),
        "native_feature_value_counts": {n: dict(sorted(c.items())) for n, c in value_counts.items()},
        "distinct_full_native_rows": len(full_rows), "repeated_full_native_rows": sum(c-1 for c in full_rows.values()),
        "distinct_native_feature_vectors": len(feature_labels),
        "mixed_native_result_feature_vectors": sum(len(labels) > 1 for labels in feature_labels.values()),
        "target_mapping_status": "not_interpreted; source-backed numeric meanings required before target mapping",
        "eligibility_status": "not_frozen; diagnostics do not select or exclude research records",
        "groups_generated": 0, "assignments_generated": 0, "model_fits": 0,
        "native_zero_and_minus_one_are_missing": False,
        "limitations": ["No campaign/domain metadata is reconstructed from engineered vectors.",
                        "Feature-vector collisions are not approved group assignments.",
                        "This source audit cannot establish unexposed final-evaluation observations."]}


def write_source_audit(directory, report):
    """Exclusive new run directory; one aggregate report, no research row export."""
    if (report.get("version") not in {VERSION, "web-archived-source-audit-0.1.0", "named-csv-native-source-audit-0.1.0"}
            or any(type(report.get(k)) is not int or report[k] != 0
                   for k in ("groups_generated", "assignments_generated", "model_fits"))):
        raise InputContractError("no_fit_native_audit_required")
    body = canonical_json(report).encode()
    directory = Path(directory)
    if directory.exists() or not directory.parent.is_dir():
        raise InputContractError("unused_source_audit_directory_required")
    directory.mkdir()
    path = directory / "source_audit.json"
    try:
        with path.open("xb") as stream:
            stream.write(body)
    except OSError:
        # Only this call's new aggregate output; original snapshots are read-only.
        if path.exists():
            path.unlink()
        directory.rmdir()
        raise InputContractError("source_audit_export_failed") from None
    return hashlib.sha256(body).hexdigest()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True)
    p.add_argument("--expected-sha256", required=True)
    p.add_argument("--source-reference", required=True)
    p.add_argument("--license-reference", required=True)
    p.add_argument("--authorization-reference", required=True)
    p.add_argument("--max-bytes", required=True, type=int)
    p.add_argument("--output", required=True)
    args = p.parse_args(argv)
    try:
        report = audit_uci_arff(args.source, expected_sha256=args.expected_sha256,
            source_reference=args.source_reference, license_reference=args.license_reference,
            authorization_reference=args.authorization_reference, max_bytes=args.max_bytes)
        digest = write_source_audit(args.output, report)
    except (InputContractError, OSError):
        print(json.dumps({"status": "failed", "reason": "source_audit_contract_or_io_failure"}))
        return 2
    print(json.dumps({"status": "source_audited_not_frozen", "source_records": report["source_records"],
                      "invalid_native_records": report["invalid_native_records"], "report_sha256": digest,
                      "groups_generated": 0, "assignments_generated": 0, "model_fits": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
