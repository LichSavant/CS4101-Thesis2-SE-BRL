"""Synthetic development CV orchestration; no research-data loader.

Consumes validated D9 development objects. Factories are trusted callback ports:
they own a fresh fold-local pipeline, including every learned transform. This
module has no sklearn dependency, tuning, calibration fit, family selection, test
loader or permission to run research data. Outputs are always SYNTHETIC RESULT.
"""
from collections.abc import Mapping
from dataclasses import dataclass
import csv
import hashlib
import io
import math
from pathlib import Path
import platform
import sys
import json
from importlib import metadata

from ml.development_experiments import (
    CLASSIFIER_FAMILIES, DevelopmentDataset, DevelopmentObservation, DevelopmentSpecification, _within, _manifest_object,
    behavioral_columns, development_folds,
)
from ml.evaluation_metrics import binary_metrics, _numbers
from ml.experiment_inputs import InputContractError, PartitionAssignment, validate_supplied_partitions
from ml.metadata import canonical_json, freeze_json, fingerprint, json_value, require_text
from ml.notebook_contracts import canonical_notebook_codebook


@dataclass(frozen=True, slots=True)
class CVSpecification:
    family: str
    configurations: tuple[str, ...]
    seed: int
    threshold: float
    parameters: Mapping
    implementation_reference: str
    score_comparability_reference: str
    calibration_edges: tuple | None = None
    omitted_features: tuple[str, ...] = ()

    def __post_init__(self):
        if self.family not in CLASSIFIER_FAMILIES:
            raise InputContractError("unsupported_classifier_family")
        if (type(self.configurations) is not tuple or not self.configurations
                or any(type(v) is not str for v in self.configurations)
                or len(set(self.configurations)) != len(self.configurations)):
            raise InputContractError("explicit_unique_configurations_required")
        if type(self.seed) is not int or self.seed < 0:
            raise InputContractError("explicit_seed_required")
        _numbers((self.threshold,))
        if not isinstance(self.parameters, Mapping):
            raise InputContractError("explicit_parameters_required")
        object.__setattr__(self, "parameters", freeze_json(self.parameters))
        for value in (self.implementation_reference, self.score_comparability_reference):
            require_text(value)
        if not self.implementation_reference.startswith("synthetic:"):
            raise InputContractError("synthetic_implementation_reference_required")
        if (type(self.omitted_features) is not tuple
                or any(type(v) is not str for v in self.omitted_features)
                or len(set(self.omitted_features)) != len(self.omitted_features)):
            raise InputContractError("explicit_unique_omissions_required")
        if self.calibration_edges is not None:
            edges = _numbers(self.calibration_edges)
            if (type(self.calibration_edges) is not tuple or len(edges) < 2 or edges[0] != 0 or edges[-1] != 1
                    or any(a >= b for a, b in zip(edges, edges[1:]))):
                raise InputContractError("invalid_calibration_edges")


@dataclass(frozen=True, slots=True)
class ScoreBatch:
    observation_ids: tuple[str, ...]
    scores: tuple[float, ...]
    score_kind: str
    positive_label: int
    probabilities: tuple[float, ...] | None = None

    def __post_init__(self):
        if (type(self.observation_ids) is not tuple or not self.observation_ids
                or any(type(i) is not str or not i.strip() for i in self.observation_ids)
                or len(set(self.observation_ids)) != len(self.observation_ids)):
            raise InputContractError("unique_prediction_ids_required")
        if type(self.positive_label) is not int or self.positive_label != 1:
            raise InputContractError("explicit_positive_label_one_required")
        if self.score_kind not in {"margin", "probability"}:
            raise InputContractError("explicit_score_kind_required")
        if type(self.scores) is not tuple:
            raise InputContractError("immutable_score_tuple_required")
        _numbers(self.scores, len(self.observation_ids), probability=self.score_kind == "probability")
        if self.probabilities is not None:
            if type(self.probabilities) is not tuple:
                raise InputContractError("immutable_probability_tuple_required")
            _numbers(self.probabilities, len(self.observation_ids), probability=True)


def _validate_dataset(dataset):
    if (not isinstance(dataset, DevelopmentDataset)
            or not isinstance(dataset.specification, DevelopmentSpecification)
            or type(dataset.observations) is not tuple or not dataset.observations):
        raise InputContractError("validated_development_dataset_required")
    for row in dataset.observations:
        if not isinstance(row, DevelopmentObservation):
            raise InputContractError("typed_development_observations_required")
        if type(row.target) is not int or row.target not in (0, 1):
            raise InputContractError("binary_integer_labels_required")
        if type(row.conventional) is not tuple or len(row.conventional) != len(dataset.specification.conventional):
            raise InputContractError("conventional_width_mismatch")
        if type(row.behavioral) is not tuple or len(row.behavioral) != 8:
            raise InputContractError("behavioral_width_mismatch")
        if any(type(v) not in (int, bool) or v not in (0, 1) for v in row.behavioral):
            raise InputContractError("binary_behavioral_value_required")
        if any(s > a for s, a in zip(row.behavioral[:4], row.behavioral[4:])):
            raise InputContractError("support_without_availability")
        if dataset.specification.dataset not in {"Email", "Web"} and any(row.behavioral):
            raise InputContractError("technical_behavioral_evidence_forbidden")
        for column, value in zip(dataset.specification.conventional, row.conventional):
            if value is not None:
                if column.kind == "text":
                    if type(value) is not str:
                        raise InputContractError("invalid_text_predictor")
                else:
                    _numbers((value,))
    validate_supplied_partitions(tuple(PartitionAssignment(r.observation_id, r.group_id, "development", r.fold)
                                       for r in dataset.observations), folds=5)


def dataset_fingerprint(dataset):
    """Hash inputs in memory; raw conventional text/values are never exported."""
    _validate_dataset(dataset)
    return fingerprint({"dataset": dataset.specification.dataset,
        "protocol_reference": dataset.specification.protocol_reference,
        "dictionary_reference": dataset.specification.feature_dictionary_reference,
        "columns": [(c.name, c.kind) for c in dataset.specification.conventional],
        "observations": [(r.observation_id, r.target, r.group_id, r.fold, r.conventional, r.behavioral)
                         for r in dataset.observations]})


def dimension_ablations(dataset):
    _validate_dataset(dataset)
    if dataset.specification.dataset not in {"Email", "Web"}:
        raise InputContractError("behavioral_ablation_requires_content_branch")
    return {d: (f"{d}_supported", f"{d}_available") for d in canonical_notebook_codebook()}


def run_synthetic_cv(dataset, specification, *, factory):
    """Fresh callback pipeline per configuration/fold; exactly one OOF score/ID.

    factory(family, configuration, fold, seed, parameters) -> pipeline
    pipeline.fit(x_train, y_train, feature_names=..., seed=...)
    pipeline.score(x_validation, observation_ids=...) -> ScoreBatch

    IDs are control metadata for score alignment, never columns in x. Validation
    labels are never passed to score. Callbacks must not access external research
    data: this is a software interface, not a sandbox. A fit exception discards
    the run; no partial result is returned or files written.
    """
    input_hash = dataset_fingerprint(dataset)
    if not isinstance(specification, CVSpecification) or not callable(factory):
        raise InputContractError("cv_specification_and_factory_required")
    plans = {}
    expected_ids = {r.observation_id for r in dataset.observations}
    for config in specification.configurations:
        folds = development_folds(dataset, config)
        ids = [oid for plan in folds for oid in plan.validation_ids]
        if len(ids) != len(expected_ids) or set(ids) != expected_ids:
            raise InputContractError("oof_population_mismatch")
        for plan in folds:
            if not set(specification.omitted_features) <= set(plan.feature_names):
                raise InputContractError("unknown_ablation_feature")
            if set(plan.feature_names) <= set(specification.omitted_features):
                raise InputContractError("empty_ablation_feature_space")
        plans[config] = folds
    indexed = {r.observation_id: r for r in dataset.observations}
    live_pipelines = []
    oof, fold_reports, pooled = [], [], {}
    pipeline_records = []
    kind = None
    for config, folds in plans.items():
        for plan in folds:
            selected = tuple(i for i, name in enumerate(plan.feature_names) if name not in specification.omitted_features)
            names = tuple(plan.feature_names[i] for i in selected)
            x_train = tuple(tuple(row[i] for i in selected) for row in plan.x_train)
            x_valid = tuple(tuple(row[i] for i in selected) for row in plan.x_validation)
            try:
                pipeline = factory(specification.family, config, plan.validation_fold,
                                   specification.seed, specification.parameters)
                if any(pipeline is old for old in live_pipelines):
                    raise InputContractError("fresh_fold_pipeline_required")
                live_pipelines.append(pipeline)  # Retain references to detect reuse.
                pipeline.fit(x_train, plan.y_train, feature_names=names, seed=specification.seed)
                batch = pipeline.score(x_valid, observation_ids=plan.validation_ids)
                audit = getattr(pipeline, "audit_record", None)
                if audit is not None:
                    pipeline_records.append({"configuration": config, "fold": plan.validation_fold,
                                             "pipeline": json_value(freeze_json(audit()))})
            except InputContractError:
                raise
            except Exception:
                raise InputContractError("synthetic_pipeline_callback_failed") from None
            if not isinstance(batch, ScoreBatch) or set(batch.observation_ids) != set(plan.validation_ids):
                raise InputContractError("prediction_population_mismatch")
            current_kind = (batch.score_kind, batch.probabilities is not None)
            if kind is not None and kind != current_kind:
                raise InputContractError("inconsistent_fold_score_contract")
            kind = current_kind
            scores = dict(zip(batch.observation_ids, batch.scores))
            probabilities = dict(zip(batch.observation_ids, batch.probabilities)) if batch.probabilities is not None else None
            ordered_scores = tuple(scores[i] for i in plan.validation_ids)
            ordered_probs = tuple(probabilities[i] for i in plan.validation_ids) if probabilities is not None else None
            metrics = binary_metrics(plan.y_validation, ordered_scores, positive_label=1,
                threshold=specification.threshold, probabilities=ordered_probs,
                calibration_edges=specification.calibration_edges if ordered_probs is not None else None)
            fold_reports.append({"configuration": config, "fold": plan.validation_fold,
                                 "feature_names": names, "metrics": metrics})
            for oid in plan.validation_ids:
                row = indexed[oid]
                oof.append({"configuration": config, "observation_id": oid, "group_id": row.group_id,
                            "fold": row.fold, "target": row.target, "score": scores[oid],
                            "probability": probabilities[oid] if probabilities is not None else None})
        records = [row for row in oof if row["configuration"] == config]
        pooled[config] = binary_metrics(tuple(r["target"] for r in records), tuple(r["score"] for r in records),
            positive_label=1, threshold=specification.threshold,
            probabilities=tuple(r["probability"] for r in records) if records[0]["probability"] is not None else None,
            calibration_edges=specification.calibration_edges if records[0]["probability"] is not None else None)
    request = {"family": specification.family, "configurations": specification.configurations,
               "seed": specification.seed, "threshold": specification.threshold,
               "parameters": specification.parameters, "implementation_reference": specification.implementation_reference,
               "score_comparability_reference": specification.score_comparability_reference,
               "calibration_edges": specification.calibration_edges, "omitted_features": specification.omitted_features}
    return json_value(freeze_json({"result_category": "SYNTHETIC RESULT",
        "research_execution": "BLOCKED", "dataset": dataset.specification.dataset,
        "input_fingerprint": input_hash, "request": request, "score_kind": kind[0],
        "preprocessing_fit_boundary": "trusted_fresh_training_fold_callback",
        "calibration_fits": 0, "selection_performed": False,
        "pipeline_records": pipeline_records,
        "oof_predictions": oof, "fold_reports": fold_reports, "pooled_metrics": pooled}))


def compare_synthetic_results(left, right, *, left_configuration, right_configuration):
    if (left.get("result_category") != "SYNTHETIC RESULT" or right.get("result_category") != "SYNTHETIC RESULT"
            or left.get("input_fingerprint") != right.get("input_fingerprint")):
        raise InputContractError("matched_synthetic_inputs_required")
    a_request, b_request = left["request"], right["request"]
    if any(a_request[k] != b_request[k] for k in ("seed", "score_comparability_reference")):
        raise InputContractError("paired_controls_mismatch")
    representation_change = (left_configuration != right_configuration
                             or a_request["omitted_features"] != b_request["omitted_features"])
    if representation_change and any(a_request[k] != b_request[k] for k in ("family", "parameters", "implementation_reference")):
        raise InputContractError("representation_comparison_requires_fixed_classifier")
    if representation_change:
        def recorded_preprocessing(result, config):
            return {canonical_json(r["pipeline"]["preprocessing"]) for r in result.get("pipeline_records", ())
                    if r["configuration"] == config and "preprocessing" in r["pipeline"]}
        a_preprocessing = recorded_preprocessing(left, left_configuration)
        b_preprocessing = recorded_preprocessing(right, right_configuration)
        if a_preprocessing != b_preprocessing or len(a_preprocessing) > 1:
            raise InputContractError("representation_comparison_preprocessing_mismatch")
    def indexed(result, config):
        rows = [r for r in result["oof_predictions"] if r["configuration"] == config]
        index = {r["observation_id"]: r for r in rows}
        if not rows or len(index) != len(rows):
            raise InputContractError("unique_matched_oof_rows_required")
        return index
    a, b = indexed(left, left_configuration), indexed(right, right_configuration)
    if set(a) != set(b) or any(any(a[i][k] != b[i][k] for k in ("target", "group_id", "fold")) for i in a):
        raise InputContractError("paired_oof_metadata_mismatch")
    return {"result_category": "SYNTHETIC RESULT", "statistic": "average_precision_left_minus_right",
            "difference": left["pooled_metrics"][left_configuration]["average_precision"]
                        - right["pooled_metrics"][right_configuration]["average_precision"],
            "observations": len(a), "selection_performed": False}


def environment_record():
    packages = {}
    for name in ("numpy", "pandas", "scipy", "scikit-learn", "xgboost", "joblib", "threadpoolctl", "pytest"):
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            packages[name] = None
    return {"python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
            "processor": platform.processor(), "packages": packages}


def slice_synthetic_metrics(result, configuration, *, slices_by_id):
    if result.get("result_category") != "SYNTHETIC RESULT":
        raise InputContractError("synthetic_result_required")
    rows = [r for r in result["oof_predictions"] if r["configuration"] == configuration]
    if (not rows or not isinstance(slices_by_id, Mapping)
            or set(slices_by_id) != {r["observation_id"] for r in rows}
            or any(type(s) is not str or not s.strip() for s in slices_by_id.values())):
        raise InputContractError("exact_slice_metadata_required")
    reports = {}
    for name in sorted(set(slices_by_id.values())):
        selected = [r for r in rows if slices_by_id[r["observation_id"]] == name]
        probabilities = tuple(r["probability"] for r in selected) if selected[0]["probability"] is not None else None
        reports[name] = binary_metrics(tuple(r["target"] for r in selected), tuple(r["score"] for r in selected),
            positive_label=1, threshold=result["request"]["threshold"], probabilities=probabilities,
            calibration_edges=result["request"]["calibration_edges"] if probabilities is not None else None)
    return {"result_category": "SYNTHETIC RESULT", "slices": reports,
            "source_independence_established": False}


def write_synthetic_bundle(directory, result, *, code_reference, code_hashes):
    if (result.get("result_category") != "SYNTHETIC RESULT" or result.get("research_execution") != "BLOCKED"):
        raise InputContractError("synthetic_result_required")
    return _write_result_bundle(directory, result, code_reference=code_reference, code_hashes=code_hashes)


def _write_result_bundle(directory, result, *, code_reference, code_hashes, execution_context=None):
    """Exclusive leaf directory; manifest last; no raw predictor text or values.

    The parent must exist. Ordinary IO rollback removes only this call's files
    and leaf directory. Process termination is not an atomic transaction.
    """
    require_text(code_reference)
    if execution_context is not None:
        from ml.preflight import require_research_fitting
        require_research_fitting(execution_context)
        execution_context.verify_result(result)
    elif (result.get("result_category") != "SYNTHETIC RESULT"
            or result.get("research_execution") != "BLOCKED"):
        raise InputContractError("synthetic_result_required")
    if not isinstance(code_hashes, Mapping) or not code_hashes:
        raise InputContractError("explicit_code_hashes_required")
    import re
    if any(type(p) is not str or type(h) is not str or not re.fullmatch("[a-f0-9]{64}", h) for p, h in code_hashes.items()):
        raise InputContractError("valid_code_hashes_required")
    rows = result["oof_predictions"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=("configuration", "observation_id", "group_id", "fold", "target", "score", "probability"))
    writer.writeheader()
    writer.writerows(rows)
    payloads = {"oof_predictions.csv": stream.getvalue().encode("utf-8"),
                "metrics.json": canonical_json({"result_category": result["result_category"],
                    "fold_reports": result["fold_reports"], "pooled_metrics": result["pooled_metrics"]}).encode("utf-8")}
    manifest = {k: v for k, v in result.items() if k not in {"oof_predictions", "fold_reports", "pooled_metrics"}}
    manifest.update(code_reference=code_reference, code_hashes=dict(code_hashes),
                    environment=environment_record(),
                    outputs={name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()})
    payloads["manifest.json"] = canonical_json(manifest).encode("utf-8")
    directory = Path(directory)
    if directory.exists():
        raise InputContractError("synthetic_bundle_already_exists")
    created = []
    made_directory = False
    try:
        directory.mkdir()
        made_directory = True
        for name, data in payloads.items():
            path = directory / name
            with path.open("xb") as f:
                created.append(path)
                f.write(data)
    except OSError:
        for path in reversed(created):
            path.unlink()
        if made_directory:
            directory.rmdir()
        raise InputContractError("synthetic_bundle_write_failed") from None
    return directory / "manifest.json"


def verify_synthetic_bundle(directory):
    return _verify_result_bundle(directory)


def _verify_result_bundle(directory, execution_context=None):
    """Read only the three fixed synthetic files; hashes establish identity only."""
    directory = Path(directory)
    try:
        manifest = json.loads(_within(directory, "manifest.json").read_text(encoding="utf-8"),
                              object_pairs_hook=_manifest_object)
        freeze_json(manifest)
        if execution_context is not None:
            from ml.preflight import require_research_fitting
            require_research_fitting(execution_context)
            execution_context.verify_result(manifest)
        elif manifest["result_category"] != "SYNTHETIC RESULT" or manifest["research_execution"] != "BLOCKED":
            raise InputContractError("invalid_synthetic_manifest")
        if set(manifest["outputs"]) != {"oof_predictions.csv", "metrics.json"}:
            raise InputContractError("invalid_synthetic_manifest")
        import re
        for name, expected in manifest["outputs"].items():
            if type(expected) is not str or not re.fullmatch("[a-f0-9]{64}", expected):
                raise InputContractError("invalid_synthetic_manifest")
            if hashlib.sha256(_within(directory, name).read_bytes()).hexdigest() != expected:
                raise InputContractError("synthetic_output_hash_mismatch")
    except InputContractError:
        raise
    except (OSError, UnicodeError, ValueError, TypeError, KeyError):
        raise InputContractError("synthetic_bundle_missing_or_invalid") from None
    return manifest

