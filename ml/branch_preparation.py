"""Selected Notebook 04 branches; no data discovery, split allocation or fitting.

The notebook supplies its existing CSV decoding and Email rule implementation.
Technical branches never invoke that implementation. Scientific approval is not
established by this software boundary or by a caller-supplied reference string.
"""
from collections.abc import Mapping
from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
import re

from ml.development_experiments import (
    BEHAVIORAL_FILES, DEVELOPMENT_FILES, METADATA, _bit, _within, behavioral_columns,
)
from ml.experiment_inputs import InputContractError
from ml.metadata import canonical_json
from ml.notebook_contracts import (
    CONTRACT_VERSION, assert_new_outputs, canonical_notebook_codebook,
    technical_indicator_columns, validate_feature_boundary, validate_metadata_alignment,
)

# Preserve the historical combined selection for existing notebook callers.
# Web is selected explicitly; adding support must not add a new input dependency.
ALL_BRANCHES = ("Email", "PhiUSIIL", "UCI")
SUPPORTED_BRANCHES = ALL_BRANCHES + ("Web",)
PREPROCESSED_FILES = {"Email": "email_preprocessed.csv", "PhiUSIIL": "phiusiil_preprocessed.csv",
                      "UCI": "uci_phishing_websites_preprocessed.csv", "Web": "web_preprocessed.csv"}
PARTITION_FILES = {"Email": "email_partition_manifest.csv", "PhiUSIIL": "phiusiil_partition_manifest.csv",
                   "UCI": "uci_partition_manifest.csv", "Web": "web_partition_manifest.csv"}
SHARED_OUTPUTS = (
    "results/feature_extraction/evidence/indicator_evidence.csv",
    "results/feature_extraction/sebrl_codebook.csv",
    "results/feature_extraction/evidence_availability.csv",
    "results/feature_extraction/summaries/lexical_support_summary.csv",
    "results/feature_extraction/summaries/dimension_state_summary.csv",
    "results/feature_extraction/summaries/vector_summary.csv",
)


def select_branches(branches) -> tuple[str, ...]:
    if (type(branches) is not tuple or not branches
            or any(type(name) is not str or name not in SUPPORTED_BRANCHES for name in branches)
            or len(set(branches)) != len(branches)):
        raise InputContractError("explicit_unique_preparation_branches_required")
    return branches


def _selected_mapping(values, branches):
    if not isinstance(values, Mapping) or set(values) != set(branches):
        raise InputContractError("selected_branch_population_mismatch")


def load_selected_inputs(run_root: Path, branches, *, read_records) -> dict:
    """Read/validate only selected fixed inputs; return development rows only.

    read_records is the existing notebook CSV decoder followed by as_records.
    All selected files must exist before the first read; this creates no paths.
    """
    branches = select_branches(branches)
    paths = {name: (
        _within(run_root, "data/processed/preprocessed/" + PREPROCESSED_FILES[name]),
        _within(run_root, "results/preprocessing/partitions/" + PARTITION_FILES[name]),
    ) for name in branches}
    if any(not p.is_file() for pair in paths.values() for p in pair):
        raise InputContractError("required_selected_preparation_input_missing")
    result = {}
    for name, (main, manifest) in paths.items():
        try:
            rows, assignments = tuple(read_records(main)), tuple(read_records(manifest))
        except InputContractError:
            raise
        except (OSError, UnicodeError, ValueError, TypeError):
            raise InputContractError("selected_preparation_input_invalid") from None
        validate_metadata_alignment(rows, assignments, dataset=name)
        result[name] = tuple(dict(r) for r in rows if r["partition"] == "development")
        validate_feature_boundary(result[name], dataset=name, development_only=True)
    return result


def _same_source_rows(before, after):
    index = {r["observation_id"]: r for r in after}
    if len(index) != len(after) or set(index) != {r["observation_id"] for r in before}:
        raise InputContractError("preparation_changed_observation_population")
    if any(any(k not in index[r["observation_id"]] or index[r["observation_id"]][k] != v
               for k, v in r.items()) for r in before):
        raise InputContractError("preparation_changed_source_fields")


def prepare_selected_branches(inputs, branches, *, prepare_email=None, prepare_web=None) -> dict:
    """Dispatch Email only when explicitly selected; preserve original fields.

    The callback owns the unchanged Email rules and their existing freeze gate.
    Technical branches add the already defined unavailable indicator encoding.
    """
    branches = select_branches(branches)
    _selected_mapping(inputs, branches)
    if "Email" in branches and not callable(prepare_email):
        raise InputContractError("selected_email_preparer_required")
    if "Web" in branches and not callable(prepare_web):
        raise InputContractError("selected_web_preparer_required")
    result = {}
    for name in branches:
        original = tuple(deepcopy(dict(row)) for row in inputs[name])
        validate_feature_boundary(original, dataset=name, development_only=True)
        if name == "Email":
            prepared = tuple(prepare_email(deepcopy(original)))
        elif name == "Web":
            prepared = tuple(prepare_web(deepcopy(original)))
        else:
            derived = technical_indicator_columns(name)
            for dimension in canonical_notebook_codebook():
                derived.update({f"{dimension}_state": "Unavailable",
                                f"{dimension}_supported": 0, f"{dimension}_available": 0})
            prepared = tuple({**row, **derived} for row in deepcopy(original))
        validate_feature_boundary(prepared, dataset=name, development_only=True)
        _same_source_rows(original, prepared)
        result[name] = prepared
    return result


def _csv_bytes(rows):
    rows = tuple(rows)
    if not rows or any(set(r) != set(rows[0]) for r in rows):
        raise InputContractError("inconsistent_preparation_export_columns")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]))
    writer.writeheader()
    writer.writerows({k: canonical_json(v) if isinstance(v, (list, tuple, Mapping)) else v for k, v in row.items()} for row in rows)
    return stream.getvalue().encode("utf-8")


def export_selected_handoff(run_root: Path, branches, development, behavioral, *, shared_outputs=None) -> tuple[Path, ...]:
    """Validate/serialize/preflight everything before exclusive creation.

    On ordinary IO failure remove only this call's newly created files and empty
    directories. Pre-existing paths are never removed. A process crash is not a
    transaction: the manifest is written last and collisions prohibit reuse.
    """
    branches = select_branches(branches)
    _selected_mapping(development, branches)
    _selected_mapping(behavioral, branches)
    run_root = Path(run_root)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", run_root.name):
        raise InputContractError("invalid_run_id")
    shared_outputs = {} if shared_outputs is None else shared_outputs
    if (not isinstance(shared_outputs, Mapping) or not set(shared_outputs).issubset(SHARED_OUTPUTS)
            or any(type(value) is not bytes for value in shared_outputs.values())):
        raise InputContractError("invalid_shared_preparation_output")
    payloads, entries = {}, {}
    columns = (*METADATA, *behavioral_columns())
    for name in branches:
        rows, vectors = tuple(development[name]), tuple(behavioral[name])
        validate_feature_boundary(rows, dataset=name, development_only=True)
        if any(not isinstance(r, Mapping) or set(r) != set(columns) for r in vectors):
            raise InputContractError("behavioral_schema_mismatch")
        index = {r["observation_id"]: r for r in vectors}
        if len(index) != len(vectors) or set(index) != {r["observation_id"] for r in rows}:
            raise InputContractError("behavioral_population_mismatch")
        for row in rows:
            vector = index[row["observation_id"]]
            if type(vector["target"]) is not int or type(vector["cv_fold"]) not in (int, float):
                raise InputContractError("invalid_behavioral_metadata_types")
            if any(row[key] != vector[key] for key in METADATA):
                raise InputContractError("behavioral_metadata_mismatch")
            bits = tuple(_bit(vector[key]) for key in behavioral_columns())
            if any(s > a for s, a in zip(bits[:4], bits[4:])) or (name not in {"Email", "Web"} and any(bits)):
                raise InputContractError("invalid_behavioral_preparation_values")
        main = "data/processed/features/development/" + DEVELOPMENT_FILES[name]
        behavior = "data/processed/features/sebrl/" + BEHAVIORAL_FILES[name]
        payloads[main], payloads[behavior] = _csv_bytes(rows), _csv_bytes(vectors)
        entries[name] = {"development_file": DEVELOPMENT_FILES[name], "behavioral_file": BEHAVIORAL_FILES[name],
                         "development_sha256": hashlib.sha256(payloads[main]).hexdigest(),
                         "behavioral_sha256": hashlib.sha256(payloads[behavior]).hexdigest()}
    payloads.update(shared_outputs)
    manifest = "data/processed/features/development/development_input_manifest.json"
    payloads[manifest] = json.dumps({"contract_version": CONTRACT_VERSION, "run_id": run_root.name,
                                    "inputs": entries}, indent=2).encode("utf-8")
    targets = {_within(run_root, name): value for name, value in payloads.items()}
    assert_new_outputs(targets)
    created_files, created_dirs = [], []
    try:
        for path, content in targets.items():
            missing = []
            parent = path.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                directory.mkdir()
                created_dirs.append(directory)
            with path.open("xb") as stream:
                created_files.append(path)
                stream.write(content)
    except OSError:
        for path in reversed(created_files):
            path.unlink()
        for directory in reversed(created_dirs):
            directory.rmdir()
        raise InputContractError("preparation_export_failed") from None
    return tuple(targets)
