"""Bounded acquisition of named, openly licensed proposal sources; no ingestion.

Snapshot integrity is checked against an independently retrieved Zenodo record.
This creates no eligible population, labels, groups, assignments or model runs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from time import monotonic
from urllib.parse import quote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from ml.experiment_inputs import InputContractError, reject_excluded_source_identifiers
from ml.metadata import canonical_json


class RepositoryRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        if target.scheme != "https" or target.hostname != "zenodo.org":
            raise InputContractError("source_redirect_outside_repository")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def acquire_zenodo(record_path, *, expected_record_sha256, record_id, filenames,
                   directory, max_total_bytes, max_elapsed_seconds, authorization_reference, opener=None):
    """Exclusive snapshot with receipt last; only explicitly requested file names.

    The caller establishes lawful access and trusts the record digest obtained
    from the official repository. An access reference is traceability, never an
    approval to screen, allocate, train or evaluate. Payload bytes are not logged.
    """
    if (type(record_id) is not int or record_id not in {8339691, 8041387}
            or type(max_total_bytes) is not int or max_total_bytes < 1
            or type(max_elapsed_seconds) not in (int, float) or not 0 < max_elapsed_seconds <= 3600
            or type(expected_record_sha256) is not str or not re.fullmatch("[a-f0-9]{64}", expected_record_sha256)
            or type(authorization_reference) is not str or not authorization_reference.strip()):
        raise InputContractError("explicit_named_source_budget_and_reference_required")
    if (type(filenames) is not tuple or not filenames or len(set(filenames)) != len(filenames)
            or any(type(n) is not str or not re.fullmatch(r"[A-Za-z0-9_.+-]+", n) for n in filenames)):
        raise InputContractError("explicit_unique_repository_files_required")
    if record_id == 8339691 and not set(filenames) <= {"Nazario.csv", "Enron.csv", "SpamAssasin.csv", "CEAS_08.csv"}:
        raise InputContractError("email_source_not_named_by_approved_proposal")
    reject_excluded_source_identifiers(*filenames)
    body = Path(record_path).read_bytes()
    if len(body) > 2_000_000 or hashlib.sha256(body).hexdigest() != expected_record_sha256:
        raise InputContractError("source_metadata_digest_mismatch")
    try:
        record = json.loads(body)
        if (int(record["id"]) != record_id or record["metadata"]["access_right"] != "open"
                or record["metadata"]["license"]["id"] != "cc-by-4.0"):
            raise InputContractError("source_terms_require_separate_review")
        files = {f["key"]: f for f in record["files"]}
        selected = [files[n] for n in filenames]
        if (any(type(f["size"]) is not int or f["size"] < 1
                or not re.fullmatch("md5:[a-f0-9]{32}", f["checksum"]) for f in selected)
                or sum(f["size"] for f in selected) > max_total_bytes):
            raise InputContractError("acquisition_budget_or_checksum_invalid")
    except InputContractError:
        raise
    except (KeyError, TypeError, ValueError):
        raise InputContractError("source_metadata_schema_invalid") from None
    directory = Path(directory)
    if directory.exists() or not directory.parent.is_dir():
        raise InputContractError("unused_snapshot_directory_required")
    opener = opener if opener is not None else build_opener(RepositoryRedirects()).open
    created = []
    snapshots = []
    deadline = monotonic() + max_elapsed_seconds
    directory.mkdir()
    try:
        for entry in selected:
            if monotonic() >= deadline:
                raise InputContractError("source_acquisition_time_budget_exceeded")
            url = f"https://zenodo.org/records/{record_id}/files/{quote(entry['key'])}?download=1"
            sha, md5, count = hashlib.sha256(), hashlib.md5(usedforsecurity=False), 0
            path = directory / entry["key"]
            with opener(Request(url, headers={"User-Agent": "SE-BRL bounded academic snapshot acquisition"}), timeout=min(30, max(.1, deadline-monotonic()))) as response:
                effective = urlsplit(response.geturl())
                if effective.scheme != "https" or effective.hostname != "zenodo.org":
                    raise InputContractError("source_redirect_outside_repository")
                with path.open("xb") as output:
                    created.append(path)
                    while True:
                        if monotonic() >= deadline:
                            raise InputContractError("source_acquisition_time_budget_exceeded")
                        block = response.read(min(1024*1024, entry["size"]-count+1))
                        if not block:
                            break
                        count += len(block)
                        if count > entry["size"]:
                            raise InputContractError("source_payload_exceeds_recorded_size")
                        output.write(block); sha.update(block); md5.update(block)
            if count != entry["size"] or "md5:"+md5.hexdigest() != entry["checksum"]:
                raise InputContractError("source_payload_integrity_mismatch")
            snapshots.append({"file": entry["key"], "source_url": url, "bytes": count,
                              "repository_checksum": entry["checksum"], "sha256": sha.hexdigest()})
        receipt = {"version": "named-source-snapshot-0.1.0", "source_record": record_id,
            "source_metadata_sha256": expected_record_sha256, "license": "CC-BY-4.0",
            "citation": record["metadata"]["title"], "source_url": f"https://zenodo.org/records/{record_id}",
            "authorization_reference": authorization_reference, "max_total_bytes": max_total_bytes,
            "max_elapsed_seconds": max_elapsed_seconds,
            "files": snapshots, "population_status": "not_screened_not_frozen", "model_fits": 0,
            "acquisition_is_not_research_population_admission": True}
        path = directory / "source_manifest.json"
        with path.open("xb") as output:
            created.append(path); output.write(canonical_json(receipt).encode())
    except Exception as error:
        for path in reversed(created):
            path.unlink()
        directory.rmdir()
        if isinstance(error, InputContractError):
            raise
        raise InputContractError("source_acquisition_failed") from None
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", required=True)
    parser.add_argument("--expected-record-sha256", required=True)
    parser.add_argument("--record-id", type=int, required=True)
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--directory", required=True)
    parser.add_argument("--max-total-bytes", type=int, required=True)
    parser.add_argument("--max-seconds", type=float, required=True)
    parser.add_argument("--authorization-reference", required=True)
    args = parser.parse_args(argv)
    try:
        receipt = acquire_zenodo(args.record, expected_record_sha256=args.expected_record_sha256,
            record_id=args.record_id, filenames=tuple(args.files), directory=args.directory,
            max_total_bytes=args.max_total_bytes, max_elapsed_seconds=args.max_seconds,
            authorization_reference=args.authorization_reference)
    except (InputContractError, OSError):
        print(json.dumps({"status": "failed", "reason": "source_acquisition_contract_or_io_failure"}))
        return 2
    print(json.dumps({"status": "snapshot_acquired_not_frozen", "files": len(receipt["files"]),
                      "bytes": sum(f["bytes"] for f in receipt["files"]), "model_fits": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
