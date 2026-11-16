"""Aggregate audit of an acquired Zenodo 8041387 CSV snapshot; no feature fit.

Class-file roles are explicit in the producer's description. HTML tag lists are
not raw HTML/DOM evidence. Per-record brand annotations are not predictors.
"""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re

from ml.development_experiments import _within, _manifest_object
from ml.experiment_inputs import InputContractError
from ml.source_audit import write_source_audit

VERSION = "web-archived-source-audit-0.1.0"


class _HashedReader(io.RawIOBase):
    def __init__(self, stream, limit):
        self.stream, self.limit, self.count = stream, limit, 0
        self.digest = hashlib.sha256()

    def readable(self):
        return True

    def readinto(self, buffer):
        data = self.stream.read(min(len(buffer), self.limit-self.count+1))
        self.count += len(data)
        if self.count > self.limit:
            raise InputContractError("web_source_exceeds_recorded_size")
        self.digest.update(data)
        buffer[:len(data)] = data
        return len(data)


def audit_web_snapshot(directory, *, expected_manifest_sha256, expected_class_counts, max_field_chars):
    """Verify snapshots while streaming; emit only aggregate native/source facts.

    IDs are checked in memory, not exported or replaced. Missing/invalid source
    opportunities are diagnostics; this function selects no modeling population.
    No normalization, grouping, partitioning, language inference or rule runs.
    """
    if (type(expected_manifest_sha256) is not str or not re.fullmatch("[a-f0-9]{64}", expected_manifest_sha256)
            or type(max_field_chars) is not int or not 0 < max_field_chars <= 32_000_000
            or not isinstance(expected_class_counts, dict) or set(expected_class_counts) != {"phishing", "legitimate"}
            or any(type(c) is not int or c < 1 for c in expected_class_counts.values())):
        raise InputContractError("explicit_web_snapshot_and_audit_expectations_required")
    directory = Path(directory)
    body = _within(directory, "source_manifest.json").read_bytes()
    if hashlib.sha256(body).hexdigest() != expected_manifest_sha256:
        raise InputContractError("web_snapshot_manifest_digest_mismatch")
    try:
        manifest = json.loads(body, object_pairs_hook=_manifest_object)
        files = {f["file"]: f for f in manifest["files"]}
        if (manifest["source_record"] != 8041387 or manifest["license"] != "CC-BY-4.0"
                or set(files) != {"phishing.csv", "not-phishing.csv", "brands.csv"}
                or len(files) != len(manifest["files"])):
            raise InputContractError("expected_open_web_snapshot_required")
        for entry in files.values():
            if (type(entry["bytes"]) is not int or entry["bytes"] < 1
                    or type(entry["sha256"]) is not str or not re.fullmatch("[a-f0-9]{64}", entry["sha256"])):
                raise InputContractError("web_snapshot_file_contract_invalid")
    except InputContractError:
        raise
    except (KeyError, ValueError, TypeError):
        raise InputContractError("web_snapshot_manifest_invalid") from None
    output = {}
    all_ids = Counter()
    prior_limit = csv.field_size_limit()
    csv.field_size_limit(max_field_chars)
    try:
        for filename, native_class in (("phishing.csv", "phishing"), ("not-phishing.csv", "legitimate")):
            entry = files[filename]
            path = _within(directory, filename)
            if path.stat().st_size != entry["bytes"]:
                raise InputContractError("web_snapshot_size_mismatch")
            count, reasons, languages, text_hashes, ids = 0, Counter(), Counter(), Counter(), Counter()
            tag_types = Counter()
            opportunities = Counter()
            with path.open("rb") as raw:
                hashed = _HashedReader(raw, entry["bytes"])
                with io.TextIOWrapper(io.BufferedReader(hashed), encoding="utf-8-sig", newline="") as stream:
                    reader = csv.DictReader(stream, strict=True)
                    fields = reader.fieldnames
                    if (not fields or len(set(fields)) != len(fields)
                            or not {"_id", "features.html", "features.text", "language", "url", "domain"} <= set(fields)):
                        raise InputContractError("web_native_schema_mismatch")
                    for row in reader:
                        count += 1
                        if None in row or any(v is None for v in row.values()):
                            reasons["malformed_native_record"] += 1
                            continue
                        native_id = row["_id"]
                        if native_id.strip():
                            ids[native_id] += 1; all_ids[native_id] += 1
                        else:
                            reasons["missing_native_id"] += 1
                        languages[row["language"] or "<empty-native-cell>"] += 1
                        text = row["features.text"]
                        opportunities["nonempty_stored_text"] += int(bool(text.strip()))
                        if text:
                            text_hashes[hashlib.sha256(text.encode()).hexdigest()] += 1
                        for field in ("url", "domain"):
                            opportunities["nonempty_"+field] += int(bool(row[field].strip()))
                        try:
                            tags = json.loads(row["features.html"])
                        except ValueError:
                            reasons["html_feature_cell_not_json"] += 1
                            continue
                        tag_types[type(tags).__name__] += 1
                        if isinstance(tags, list) and all(type(t) is str for t in tags):
                            opportunities["html_tag_list"] += 1
                            opportunities["simple_tag_name_list"] += int(all(re.fullmatch(r"[A-Za-z][A-Za-z0-9:_-]*", t) for t in tags))
                        else:
                            reasons["html_feature_cell_not_string_list"] += 1
                    if hashed.count != entry["bytes"] or hashed.digest.hexdigest() != entry["sha256"]:
                        raise InputContractError("web_snapshot_payload_digest_mismatch")
            output[filename] = {"native_class": native_class, "source_records": count,
                "expected_source_records": expected_class_counts[native_class],
                "count_matches_source_expectation": count == expected_class_counts[native_class],
                "columns": fields, "native_language_counts": dict(sorted(languages.items())),
                "diagnostic_reason_counts": dict(sorted(reasons.items())), "opportunity_counts": dict(opportunities),
                "html_feature_value_types": dict(tag_types), "distinct_native_ids": len(ids),
                "duplicate_native_id_records": sum(v-1 for v in ids.values()),
                "repeated_exact_stored_texts_no_normalization": sum(v-1 for v in text_hashes.values()),
                "snapshot_sha256": entry["sha256"]}
        # The independent brand-reference table is inventoried, not used as
        # per-record behavioral ground truth or as an automatic rule freeze.
        brand_path = _within(directory, "brands.csv")
        brand = brand_path.read_bytes()
        if len(brand) != files["brands.csv"]["bytes"] or hashlib.sha256(brand).hexdigest() != files["brands.csv"]["sha256"]:
            raise InputContractError("web_brand_reference_digest_mismatch")
    except (OSError, UnicodeError, csv.Error):
        raise InputContractError("web_source_unreadable_or_exceeds_parser_budget") from None
    finally:
        csv.field_size_limit(prior_limit)
    return {"version": VERSION, "category": "ACTUAL SOURCE AUDIT; NOT A MODEL RESULT",
        "dataset": "Phishing Website Dataset", "source_record": 8041387,
        "source_manifest_sha256": expected_manifest_sha256, "source_files": output,
        "source_records": sum(v["source_records"] for v in output.values()),
        "all_source_counts_match": all(v["count_matches_source_expectation"] for v in output.values()),
        "distinct_native_ids_across_sources": len(all_ids),
        "repeated_native_ids_across_sources": sum(v-1 for v in all_ids.values()),
        "population_status": "not_screened_not_frozen", "class_semantics": "producer-documented textual source classes",
        "raw_html_or_dom_attributes_established": False, "brand_annotation_used_as_predictor": False,
        "groups_generated": 0, "assignments_generated": 0, "model_fits": 0,
        "limitations": ["Stored text and tag-name arrays do not reconstruct raw HTML, DOM locators, form attributes or embedded links.",
            "Source language codes are preserved, not inferred, normalized or treated as English.",
            "Native-ID/text collisions are diagnostics, not accepted grouping or exclusion rules."]}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot", required=True)
    p.add_argument("--expected-manifest-sha256", required=True)
    p.add_argument("--expected-phishing-records", type=int, required=True)
    p.add_argument("--expected-legitimate-records", type=int, required=True)
    p.add_argument("--max-field-chars", type=int, required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args(argv)
    try:
        report = audit_web_snapshot(args.snapshot, expected_manifest_sha256=args.expected_manifest_sha256,
            expected_class_counts={"phishing": args.expected_phishing_records, "legitimate": args.expected_legitimate_records},
            max_field_chars=args.max_field_chars)
        digest = write_source_audit(args.output, report)
    except (InputContractError, OSError):
        print(json.dumps({"status": "failed", "reason": "web_source_audit_contract_or_io_failure"}))
        return 2
    print(json.dumps({"status": "source_audited_not_frozen", "source_records": report["source_records"],
        "source_counts_match": report["all_source_counts_match"], "report_sha256": digest, "model_fits": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
