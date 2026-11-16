"""D9 development consumer: schema checks and fold inputs, never estimator fitting.

Only named development exports under experiments/runs are loaded. References are
traceability assertions, not authenticated research approvals. No historical,
calibration, test, output-writer or automatic feature-discovery path is provided.
"""
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
from types import MappingProxyType

from ml.experiment_inputs import InputContractError, select_predictors
from ml.notebook_contracts import (
    CONTRACT_VERSION, canonical_notebook_codebook, validate_feature_boundary,
)

DEVELOPMENT_FILES = {"Email": "email_development.csv", "Web": "web_development.csv", "PhiUSIIL": "phiusiil_development.csv",
                     "UCI": "uci_development.csv"}
BEHAVIORAL_FILES = {"Email": "email_sebrl_features.csv", "Web": "web_sebrl_features.csv", "PhiUSIIL": "phiusiil_sebrl_features.csv",
                    "UCI": "uci_sebrl_features.csv"}
CLASSIFIER_FAMILIES = ("logistic_regression", "linear_svm", "random_forest", "xgboost")
METADATA = ("observation_id", "target", "group_id", "partition", "cv_fold")


def behavioral_columns() -> tuple[str, ...]:
    ids = tuple(canonical_notebook_codebook())
    return tuple(f"{d}_supported" for d in ids) + tuple(f"{d}_available" for d in ids)


@dataclass(frozen=True, slots=True)
class FeatureColumn:
    name: str
    kind: str

    def __post_init__(self):
        select_predictors({self.name: None}, (self.name,))
        if self.name in behavioral_columns() or self.kind not in {"text", "numeric"}:
            raise InputContractError("invalid_conventional_feature_specification")


@dataclass(frozen=True, slots=True)
class DevelopmentSpecification:
    dataset: str
    conventional: tuple[FeatureColumn, ...]
    protocol_reference: str
    feature_dictionary_reference: str

    def __post_init__(self):
        if self.dataset not in DEVELOPMENT_FILES:
            raise InputContractError("unsupported_development_branch")
        if (type(self.conventional) is not tuple or not self.conventional
                or any(not isinstance(c, FeatureColumn) for c in self.conventional)
                or len({c.name for c in self.conventional}) != len(self.conventional)):
            raise InputContractError("explicit_unique_feature_dictionary_required")
        for reference in (self.protocol_reference, self.feature_dictionary_reference):
            if type(reference) is not str or not reference.strip():
                raise InputContractError("explicit_protocol_and_feature_references_required")


@dataclass(frozen=True, slots=True)
class DevelopmentObservation:
    observation_id: str
    target: int
    group_id: str
    fold: int
    conventional: tuple = field(repr=False)
    behavioral: tuple[int, ...] = field(repr=False)


@dataclass(frozen=True, slots=True)
class DevelopmentDataset:
    specification: DevelopmentSpecification
    observations: tuple[DevelopmentObservation, ...] = field(repr=False)

    @property
    def configurations(self):
        return ("E1", "E2", "E3") if self.specification.dataset in {"Email", "Web"} else ("U1",)


@dataclass(frozen=True, slots=True)
class FoldInputs:
    configuration: str
    validation_fold: int
    feature_names: tuple[str, ...]
    training_ids: tuple[str, ...]
    validation_ids: tuple[str, ...]
    x_train: tuple[tuple, ...] = field(repr=False)
    x_validation: tuple[tuple, ...] = field(repr=False)
    y_train: tuple[int, ...] = field(repr=False)
    y_validation: tuple[int, ...] = field(repr=False)


def _bit(value):
    if type(value) is bool:
        return int(value)
    if type(value) is int and value in (0, 1):
        return value
    raise InputContractError("binary_behavioral_value_required")


def _validate_numeric_predictor(value):
    """Stable finite-number failure, including integers outside float range."""
    if value is None:
        return
    valid = type(value) in (int, float)
    if valid:
        try:
            valid = math.isfinite(value)
        except OverflowError:
            valid = False
    if not valid:
        raise InputContractError("invalid_numeric_predictor")


def build_development_dataset(records: Iterable[Mapping], behavioral: Iterable[Mapping], *,
                              specification: DevelopmentSpecification) -> DevelopmentDataset:
    if not isinstance(specification, DevelopmentSpecification):
        raise InputContractError("development_specification_required")
    rows, vectors = tuple(records), tuple(behavioral)
    validate_feature_boundary(rows, dataset=specification.dataset, development_only=True)
    index = {}
    columns = behavioral_columns()
    for row in vectors:
        if not isinstance(row, Mapping) or not set((*METADATA, *columns)).issubset(row):
            raise InputContractError("behavioral_schema_mismatch")
        oid = row["observation_id"]
        if type(oid) is not str or not oid.strip() or oid in index:
            raise InputContractError("duplicate_or_invalid_behavioral_id")
        if row["partition"] != "development":
            raise InputContractError("reserved_behavioral_records_forbidden")
        if type(row["target"]) is not int or type(row["cv_fold"]) is not int:
            raise InputContractError("invalid_behavioral_metadata_types")
        index[oid] = row
    if set(index) != {r["observation_id"] for r in rows}:
        raise InputContractError("behavioral_population_mismatch")
    observations = []
    for row in rows:
        vector = index[row["observation_id"]]
        if any(row[c] != vector[c] for c in METADATA):
            raise InputContractError("behavioral_metadata_mismatch")
        values = tuple(_bit(vector[c]) for c in columns)
        if any(s > a for s, a in zip(values[:4], values[4:])):
            raise InputContractError("support_without_availability")
        if specification.dataset not in {"Email", "Web"} and any(values):
            raise InputContractError("technical_behavioral_evidence_forbidden")
        selected = select_predictors(row, tuple(c.name for c in specification.conventional))
        conventional = []
        for column in specification.conventional:
            value = selected[column.name]
            if column.kind == "text":
                if value is not None and type(value) is not str:
                    raise InputContractError("invalid_text_predictor")
            else:
                _validate_numeric_predictor(value)
            conventional.append(value)
        observations.append(DevelopmentObservation(row["observation_id"], row["target"], row["group_id"],
            int(row["cv_fold"]), tuple(conventional), values))
    return DevelopmentDataset(specification, tuple(observations))


def development_folds(dataset: DevelopmentDataset, configuration: str) -> tuple[FoldInputs, ...]:
    """Expose raw fold inputs; transforms, tuning and calibration must fit inside training.

    No vocabulary, imputation, scaling, score, metric, or model is learned here.
    This is not yet a nested-search or OOF-scoring implementation.
    """
    if not isinstance(dataset, DevelopmentDataset) or configuration not in dataset.configurations:
        raise InputContractError("configuration_not_supported_for_branch")
    conventional_names = tuple(c.name for c in dataset.specification.conventional)
    names = (() if configuration == "E2" else conventional_names) + (
        behavioral_columns() if configuration in {"E2", "E3"} else ())
    def values(row):
        return (() if configuration == "E2" else row.conventional) + (
            row.behavioral if configuration in {"E2", "E3"} else ())
    plans = []
    for fold in range(1, 6):
        training = tuple(r for r in dataset.observations if r.fold != fold)
        validation = tuple(r for r in dataset.observations if r.fold == fold)
        if ({r.target for r in training} != {0, 1} or {r.target for r in validation} != {0, 1}
                or {r.group_id for r in training} & {r.group_id for r in validation}):
            raise InputContractError("invalid_development_fold")
        plans.append(FoldInputs(configuration, fold, names,
            tuple(r.observation_id for r in training), tuple(r.observation_id for r in validation),
            tuple(values(r) for r in training), tuple(values(r) for r in validation),
            tuple(r.target for r in training), tuple(r.target for r in validation)))
    return tuple(plans)


def _within(root: Path, relative: str) -> Path:
    # The caller's checkout may be an explicit alias, but every component below
    # its canonical root must retain its fixed handoff location. Containment
    # alone would permit a symlink/junction into another directory in this run.
    try:
        base = root.resolve()
        expected = base / relative
        path = expected.resolve()
    except (OSError, RuntimeError):
        raise InputContractError("development_input_path_unresolvable") from None
    if not path.is_relative_to(base):
        raise InputContractError("input_path_outside_run")
    if path != expected:
        raise InputContractError("development_input_path_redirected")
    return path


def _manifest_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputContractError("duplicate_development_manifest_key")
        result[key] = value
    return result


def _read_csv(path: Path, expected_hash: str, *, behavioral: bool, specification: DevelopmentSpecification):
    if type(expected_hash) is not str or not re.fullmatch(r"[a-f0-9]{64}", expected_hash):
        raise InputContractError("input_sha256_required")
    original_limit = csv.field_size_limit()
    try:
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != expected_hash:
            raise InputContractError("development_input_hash_mismatch")
        # Parse the very bytes that were hashed. Existing corpus text lengths
        # are not silently truncated by the CSV module's small default limit.
        csv.field_size_limit(max(original_limit, len(payload)))
        with io.StringIO(payload.decode("utf-8-sig"), newline="") as stream:
            reader = csv.DictReader(stream, strict=True)
            headers = reader.fieldnames
            if (not headers or len(set(headers)) != len(headers)
                    or any(not name.strip() for name in headers)):
                raise InputContractError("duplicate_or_missing_csv_columns")
            required = set(METADATA)
            if behavioral:
                required.update(behavioral_columns())
                if set(headers) != required:
                    raise InputContractError("behavioral_csv_schema_mismatch")
            else:
                required.update(("source_dataset", "source_row_id",
                                 "Result" if specification.dataset == "UCI" else "source_label" if specification.dataset == "Web" else "label"))
                required.update(column.name for column in specification.conventional)
                if specification.dataset == "Email":
                    required.update(("subject", "body"))
                elif specification.dataset == "Web":
                    required.update(("source_file", "html", "visible_text", "source_html_available", "source_visible_text_available"))
                # Existing conventional handoffs retain extra source/audit fields.
                # Only the explicit feature dictionary can select predictors.
                if not required.issubset(headers):
                    raise InputContractError("development_csv_schema_mismatch")
            rows = []
            for supplied in reader:
                if None in supplied or any(value is None for value in supplied.values()):
                    raise InputContractError("malformed_development_csv_row")
                if supplied.get("partition") != "development":
                    raise InputContractError("reserved_records_in_development_file")
                row = dict(supplied)
                integer_columns = ("target", "cv_fold") if behavioral else (
                    ("target", "cv_fold", "source_row_id") if specification.dataset == "Web" else
                    ("target", "cv_fold", "source_row_id", "label" if specification.dataset != "UCI" else "Result"))
                for column in integer_columns:
                    value = row.get(column)
                    if type(value) is not str or not re.fullmatch(r"-?[0-9]+(?:\.0)?", value):
                        raise InputContractError("invalid_integer_csv_metadata")
                    row[column] = int(value.removesuffix(".0"))
                if behavioral:
                    for column in behavioral_columns():
                        value = row.get(column)
                        if value not in {"0", "1", "False", "True"}:
                            raise InputContractError("invalid_behavioral_csv_value")
                        row[column] = int(value in {"1", "True"})
                else:
                    if "source_label" in row and specification.dataset != "Web":
                        value = row["source_label"]
                        if not re.fullmatch(r"-?[0-9]+", value):
                            raise InputContractError("invalid_integer_csv_metadata")
                        row["source_label"] = int(value)
                    if specification.dataset == "Web":
                        for field in ("html", "visible_text"):
                            # CSV alone cannot distinguish None from known-empty.
                            # Require explicit source bookkeeping; never select
                            # these source_* fields as predictors.
                            flag = row["source_" + field + "_available"]
                            if flag not in {"0", "1", "False", "True"}:
                                raise InputContractError("explicit_web_field_availability_required")
                            if flag in {"0", "False"}:
                                if row[field] != "":
                                    raise InputContractError("web_unavailable_field_has_content")
                                row[field] = None
                    optional_fields = (("subject", "body", "sender", "reply_to", "headers", "urls") if specification.dataset == "Email"
                                       else ("title", "page_url", "urls") if specification.dataset == "Web" else ())
                    for field in optional_fields:
                        flag_name = "source_"+field+"_available"
                        if flag_name not in row:
                            continue  # legacy handoffs retain their documented encoding
                        flag = row[flag_name]
                        if flag not in {"0", "1", "False", "True"} or field not in row:
                            raise InputContractError("explicit_field_availability_required")
                        if flag in {"0", "False"}:
                            if row[field] != "":
                                raise InputContractError("unavailable_field_has_content")
                            row[field] = None
                        elif field in {"headers", "urls"}:
                            value = json.loads(row[field], object_pairs_hook=_manifest_object)
                            if (field == "headers" and type(value) is not dict) or (field == "urls" and type(value) is not list):
                                raise InputContractError("explicit_structured_source_encoding_required")
                            row[field] = value
                    for column in specification.conventional:
                        if column.name not in row:
                            raise InputContractError("missing_predictor_field")
                        if column.kind == "numeric":
                            row[column.name] = None if row[column.name] == "" else float(row[column.name])
                rows.append(row)
            return tuple(rows)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        if isinstance(error, InputContractError):
            raise
        raise InputContractError("development_input_unreadable_or_invalid") from None
    finally:
        csv.field_size_limit(original_limit)


def load_development_dataset(checkout: Path, run_id: str, *, specification: DevelopmentSpecification) -> DevelopmentDataset:
    """Read fixed development handoff paths only; never fall back to historical inputs."""
    if not isinstance(specification, DevelopmentSpecification):
        raise InputContractError("development_specification_required")
    if type(run_id) is not str or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", run_id):
        raise InputContractError("invalid_run_id")
    checkout = Path(checkout).resolve()
    run = _within(checkout, "experiments/runs/" + run_id)
    manifest_path = _within(run, "data/processed/features/development/development_input_manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"), object_pairs_hook=_manifest_object)
        if manifest["contract_version"] != CONTRACT_VERSION or manifest["run_id"] != run_id:
            raise InputContractError("development_manifest_version_mismatch")
        entry = manifest["inputs"][specification.dataset]
        if (entry["development_file"] != DEVELOPMENT_FILES[specification.dataset]
                or entry["behavioral_file"] != BEHAVIORAL_FILES[specification.dataset]):
            raise InputContractError("development_manifest_filename_mismatch")
        main = _within(run, "data/processed/features/development/" + DEVELOPMENT_FILES[specification.dataset])
        behavior = _within(run, "data/processed/features/sebrl/" + BEHAVIORAL_FILES[specification.dataset])
        rows = _read_csv(main, entry["development_sha256"], behavioral=False, specification=specification)
        vectors = _read_csv(behavior, entry["behavioral_sha256"], behavioral=True, specification=specification)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        raise InputContractError("development_handoff_missing_or_invalid") from None
    return build_development_dataset(rows, vectors, specification=specification)


def preparation_summary(dataset: DevelopmentDataset) -> Mapping:
    return MappingProxyType({"dataset": dataset.specification.dataset,
        "observations": len(dataset.observations), "configurations": dataset.configurations,
        "folds": 5, "class_counts": {str(t): sum(r.target == t for r in dataset.observations) for t in (0, 1)},
        "model_fits": 0, "research_readiness": "not_established_by_software_validation"})
