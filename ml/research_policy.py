"""Fail-closed research input custody. No discovery, fitting, or implicit approval.

Registered files are permitted for integrity inspection only. Registration is not
scientific approval. Anonymous text cannot establish dataset lineage; callers
must retain provenance and use the checked file boundary for corpus processing.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import unicodedata
from collections.abc import Mapping
from pathlib import Path


POLICY_PATH = Path(__file__).with_name("research-inputs.v1.json")
RESEARCH_STAGES = (
    "acquisition", "preprocessing", "annotation", "inference", "features",
    "tokenization", "training", "validation", "calibration", "test",
    "cross_validation", "ablation", "reporting", "handoff",
)


class ResearchPolicyError(ValueError):
    """Input or research operation has no permitted, verified lineage."""


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def normalized_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKC", value).casefold())


def reject_excluded(value: object) -> None:
    """Reject aliases in provenance, paths, record IDs and nested metadata."""
    if isinstance(value, (str, Path)):
        if any(alias in normalized_identifier(str(value)) for alias in ("spaphish", "spafish")):
            raise ResearchPolicyError("Excluded corpus cannot enter active research")
        if (isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value)
                and value.lower() in load_policy().get("excluded_file_sha256", [])):
            raise ResearchPolicyError("Excluded corpus fingerprint cannot enter active research")
    elif isinstance(value, Mapping):
        for key, item in value.items():
            reject_excluded(key)
            reject_excluded(item)
    elif isinstance(value, (tuple, list, set, frozenset)):
        for item in value:
            reject_excluded(item)


def require_stage_authorization(stage: str) -> None:
    """No researcher approval is inferred from a local boolean or file presence."""
    if stage not in RESEARCH_STAGES:
        raise ResearchPolicyError("Unknown research stage")
    # Intentionally closed. A later reviewed change must specify verifiable
    # approval evidence and its scope; editing a JSON flag is insufficient.
    raise ResearchPolicyError(
        f"{stage} blocked: dataset roles, representation, independent validation "
        "and evaluation authorization are not approved; no fallback is permitted"
    )


def verify_artifact(path: Path, root: Path) -> dict:
    """Verify an explicit integrity-only allowlist entry before consuming bytes."""
    original = Path(path)
    reject_excluded(original)
    if original.is_symlink():
        raise ResearchPolicyError("Registered input must not be a symlink")
    path, root = original.resolve(), Path(root).resolve()
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        raise ResearchPolicyError("Input is outside the registered repository") from None
    reject_excluded(relative)
    policy = load_policy()
    entry = policy["artifacts"].get(relative)
    if entry is None:
        raise ResearchPolicyError("Unregistered input; discovery and fallbacks are disabled")
    reject_excluded(entry)
    if not path.is_file() or path.is_symlink():
        raise ResearchPolicyError("Registered input must be a regular file")
    digest = fingerprint(path)
    if digest in policy["excluded_file_sha256"]:
        raise ResearchPolicyError("Excluded corpus fingerprint")
    if digest != entry["sha256"]:
        raise ResearchPolicyError("Input fingerprint differs from its custody record")
    return {"path": relative, **entry}


def read_verified_csv(path: Path, root: Path, columns: tuple[str, ...] | None = None) -> list[dict[str, str]]:
    """Inspection only; check the same in-memory bytes that are parsed."""
    entry = verify_artifact(path, root)
    payload = Path(path).read_bytes()
    if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
        raise ResearchPolicyError("Input changed during verification")
    previous_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(max(previous_limit, 100_000_000))
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
        rows = []
        for row in reader:
            reject_excluded({key: value for key, value in row.items() if key in {
                "source_dataset", "dataset", "observation_id", "record_id", "source"
            }})
            rows.append(row if columns is None else {key: row.get(key, "") for key in columns})
    finally:
        csv.field_size_limit(previous_limit)
    # Scan provenance only: arbitrary message text is not a source identifier.
    for row in rows:
        reject_excluded({key: value for key, value in row.items() if key and (
            key in {"source_dataset", "dataset", "observation_id", "record_id", "source"}
        )})
    return rows


def iter_verified_csv(path: Path, root: Path):
    """Streaming custody inspection, with before/after hashes and no output writes."""
    entry = verify_artifact(path, root)
    previous_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(max(previous_limit, 100_000_000))
        with Path(path).open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                reject_excluded({key: value for key, value in row.items() if key in {
                    "source_dataset", "dataset", "observation_id", "record_id", "source"
                }})
                yield row
        if fingerprint(path) != entry["sha256"]:
            raise ResearchPolicyError("Input changed during custody inspection")
    finally:
        csv.field_size_limit(previous_limit)


def read_research_csv(path: Path, *args, **kwargs):
    """Legacy notebook loading boundary; never delegates to an unchecked loader."""
    reject_excluded(path)
    require_stage_authorization("preprocessing")


def verify_research_path(path: Path) -> Path:
    """Non-CSV legacy notebook loader boundary, closed before parser execution."""
    reject_excluded(path)
    require_stage_authorization("preprocessing")
    return Path(path)  # unreachable until an approved implementation replaces the gate
