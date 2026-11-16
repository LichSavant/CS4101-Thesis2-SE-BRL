"""Minimal accepted-artifact verifier for one exact development run.

The operator must independently authenticate the dated researcher's response
and its receipt digest. Hashes verify identity, never scientific truth. This is
a trusted research CLI boundary, not a sandbox against arbitrary Python code.
Only fixed development/protocol files are read; no raw or reserved predictors.
"""
from dataclasses import asdict, dataclass, field
from datetime import date
import csv
import hashlib
from importlib import metadata
import io
import json
import math
from pathlib import Path
import re
import time

from ml.classifier_adapters import ClassifierSpecification, PreprocessingSpecification
from ml.development_experiments import (DevelopmentSpecification, FeatureColumn, load_development_dataset,
    development_folds, _manifest_object, _within, _read_csv, DEVELOPMENT_FILES)
from ml.development_runner import dataset_fingerprint
from ml.experiment_engine import Candidate, NestedSpecification, SigmoidSpecification, ThresholdSpecification
from ml.experiment_inputs import (InputContractError, PartitionAssignment, validate_supplied_partitions,
                                  reject_excluded_source_identifiers)
from ml.metadata import fingerprint, freeze_json, json_value
from ml.model_selection import SelectionPolicy

VERSION = "accepted-development-run-1"
FILES = ("source_audit.json", "population.json", "screening.json", "assignments.csv", "dictionary.json",
         "feature_freeze.json", "experiment.json", "selection.json", "environment.json", "development_input_manifest.json")
_TOKEN = object()


def code_hashes(root):
    """Actual executed ML code, including rules/codebook, not a Git HEAD claim."""
    root = Path(root)
    paths = sorted(p for p in (root / "ml").rglob("*") if p.is_file()
                   and "tests" not in p.parts and "__pycache__" not in p.parts
                   and p.suffix in {".py", ".json", ".txt"})
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def specification_record(spec):
    return json_value(freeze_json({"candidates": [{"id": c.identifier, "family": c.model.family,
        "parameters": c.model.parameters, "seed": c.model.seed,
        "preprocessing": {"numeric_missing": c.preprocessing.numeric_missing,
            "numeric_scaling": c.preprocessing.numeric_scaling, "text_parameters": c.preprocessing.text_parameters}}
        for c in spec.candidates], "configurations": spec.configurations,
        "calibration": {"parameters": spec.calibration.model.parameters, "seed": spec.calibration.model.seed,
            "transform": spec.calibration.transform, "clip_epsilon": spec.calibration.clip_epsilon},
        "threshold": asdict(spec.threshold), "calibration_edges": spec.calibration_edges,
        "protocol_reference": spec.protocol_reference, "omitted_features": spec.omitted_features}))


def parse_specification(record):
    try:
        candidates = tuple(Candidate(c["id"], ClassifierSpecification(c["family"], c["parameters"], c["seed"]),
            PreprocessingSpecification(**c["preprocessing"])) for c in record["candidates"])
        calibration = record["calibration"]
        spec = NestedSpecification(candidates, tuple(record["configurations"]),
            SigmoidSpecification(ClassifierSpecification("logistic_regression", calibration["parameters"], calibration["seed"]),
                calibration["transform"], calibration["clip_epsilon"]), ThresholdSpecification(**record["threshold"]),
            tuple(record["calibration_edges"]), record["protocol_reference"], tuple(record["omitted_features"]))
        if specification_record(spec) != record:
            raise InputContractError("exact_experiment_settings_required")
        return spec
    except (KeyError, TypeError, ValueError):
        raise InputContractError("invalid_explicit_research_settings") from None


def fit_estimate(spec):
    """Exactly five outer folds, four reusable inner folds; includes retuning."""
    c, k = len(spec.candidates), len(spec.configurations)
    return {"base_fits": k * ((80*c+25) if spec.threshold.mode == "fixed" else (260*c+105)),
            "calibration_fits": k * (5 if spec.threshold.mode == "fixed" else 25)}


def prospective_id(source, snapshot_sha256, source_file, position):
    if (type(source) is not str or not source or not _digest(snapshot_sha256)
            or type(source_file) is not str or not source_file or type(position) is not int or position < 0):
        raise InputContractError("verified_original_ingestion_locator_required")
    reject_excluded_source_identifiers(source, source_file)
    return "source-v1-" + fingerprint({"source": source, "snapshot_sha256": snapshot_sha256,
                                      "source_file": source_file, "original_position": position})


def _digest(value):
    return type(value) is str and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _text(value):
    return type(value) is str and bool(value.strip())


def _read(path, expected, limit):
    if not _digest(expected) or not path.is_file() or path.stat().st_size > limit:
        raise InputContractError("accepted_artifact_missing_or_oversized")
    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != expected:
        raise InputContractError("accepted_artifact_digest_mismatch")
    return body


def _json(body):
    try:
        result = json.loads(body, object_pairs_hook=_manifest_object)
        freeze_json(result)
        return result
    except Exception:
        raise InputContractError("accepted_artifact_invalid_json") from None


@dataclass(frozen=True, slots=True)
class VerifiedResearchRun:
    authorization_sha256: str
    input_fingerprint: str
    specification_fingerprint: str
    input_run_id: str
    output_run_id: str
    branch: str
    exposure_disposition: str
    accepted_by: str
    code_sha256: object = field(repr=False)
    budget: object = field(repr=False)
    sources_by_id: object = field(repr=False)
    expected_fits: object = field(repr=False)
    selection_record: object = field(repr=False)
    _token: object = field(repr=False)
    _state: dict = field(default_factory=dict, repr=False, compare=False)

    def require_verified(self):
        if self._token is not _TOKEN:
            raise InputContractError("research_fitting_not_authorized")

    def bind(self, dataset, specification):
        self.require_verified()
        if self._state.get("bound") or self._state.get("readback_only"):
            raise InputContractError("research_context_is_single_use")
        if (dataset_fingerprint(dataset) != self.input_fingerprint
                or fingerprint(specification_record(specification)) != self.specification_fingerprint
                or not specification.protocol_reference.startswith("research:")):
            raise InputContractError("accepted_run_input_or_settings_changed")
        self._state.update(bound=True, started=time.monotonic(), base=0, calibration=0)

    def check_budget(self):
        self.require_verified()
        if self._state.get("bound") and time.monotonic()-self._state["started"] > self.budget["max_seconds"]:
            raise InputContractError("research_wall_time_budget_exceeded")

    def verify_result(self, result):
        self.require_verified()
        if (result.get("result_category") != "RESEARCH RESULT"
                or result.get("research_execution") != "AUTHORIZED DEVELOPMENT ONLY"
                or result.get("execution_scope") != self._state.get("boundary")
                or result.get("authorization_sha256") != self.authorization_sha256
                or result.get("input_fingerprint") != self.input_fingerprint
                or result.get("accepted_specification_fingerprint") != self.specification_fingerprint
                or result.get("base_fits") != self.expected_fits["base_fits"]
                or result.get("calibration_fits") != self.expected_fits["calibration_fits"]
                or (self._state.get("bound") and (result.get("base_fits") != self._state["base"]
                    or result.get("calibration_fits") != self._state["calibration"]))):
            raise InputContractError("research_result_scope_or_execution_mismatch")

    def before_fit(self, kind, rows):
        self.check_budget()
        if not self._state.get("bound") or kind not in {"base", "calibration"}:
            raise InputContractError("research_run_not_bound")
        key = "max_base_fits" if kind == "base" else "max_calibration_fits"
        if rows > self.budget["max_training_rows"] or self._state[kind] >= self.budget[key]:
            raise InputContractError("research_fit_or_row_budget_exceeded")
        self._state[kind] += 1


def audited_snapshots(audit):
    """Retain exact source/file identity, not just a pool of valid digests."""
    entries = ([(audit.get("source_file"), audit)] if "snapshot_sha256" in audit
               else list(audit["source_files"].items()))
    result = {}
    for file, entry in entries:
        source = entry.get("source_dataset", entry.get("dataset", audit.get("dataset")))
        digest = entry["snapshot_sha256"]
        if not _text(source) or not _text(file) or not _digest(digest) or (source, file) in result:
            raise InputContractError("explicit_audited_source_file_snapshot_required")
        result[source, file] = digest
    if not result:
        raise InputContractError("explicit_audited_source_file_snapshot_required")
    return result


def verify_accepted_run(checkout, input_run_id, *, expected_authorization_sha256, max_metadata_bytes=50_000_000, purpose="fit"):
    """Validate a trusted dated acceptance and recompute actual data safeguards.

    The human acceptance covers the exact evidence map, code, inputs, experiment
    and output namespace. It must be supplied through the operator, not an API
    approval flag. Earlier source-audit permission cannot satisfy this boundary.
    """
    if (type(input_run_id) is not str or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", input_run_id)
            or type(max_metadata_bytes) is not int or max_metadata_bytes < 1 or purpose not in {"fit", "readback", "diagnostic", "diagnostic-readback", "ablation", "ablation-readback"}):
        raise InputContractError("explicit_research_run_and_metadata_limit_required")
    root = Path(checkout).resolve()
    run = _within(root, "experiments/runs/" + input_run_id)
    protocol = _within(run, "protocol")
    receipt = _json(_read(_within(protocol, "acceptance.json"), expected_authorization_sha256, min(1_000_000, max_metadata_bytes)))
    try:
        if set(receipt) != {"version", "boundary", "authority", "input_run_id", "output_run_id", "branch",
                            "evidence_sha256", "code_sha256", "input_fingerprint", "budget", "exposure_disposition"}:
            raise InputContractError("exact_scoped_acceptance_required")
        authority = receipt["authority"]
        diagnostic = purpose in {"diagnostic", "diagnostic-readback"}
        ablation = purpose in {"ablation", "ablation-readback"}
        readback = purpose in {"readback", "diagnostic-readback", "ablation-readback"}
        boundary = ("E-development-diagnostic-only" if diagnostic else
                    "E-development-ablation-only" if ablation else "E-development-fitting-only")
        if (receipt["version"] != VERSION or receipt["boundary"] != boundary
                or set(authority) != {"name", "role", "date", "response_reference", "response_text"}
                or authority["role"] not in {"researcher", "adviser"}
                or not all(_text(authority[k]) for k in authority)
                or len(authority["response_text"].strip()) < 40
                or date.fromisoformat(authority["date"]) > date.today()
                or receipt["input_run_id"] != input_run_id
                or receipt["branch"] not in {"Email", "Web", "UCI", "PhiUSIIL"}
                or receipt["exposure_disposition"] not in {"exploratory_previously_exposed", "documented_unexposed_scope"}):
            raise InputContractError("genuine_dated_development_acceptance_required")
        output = receipt["output_run_id"]
        if (type(output) is not str or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", output)
                or output == input_run_id
                or (not readback and _within(root, "experiments/runs/"+output).exists())
                or (readback and not _within(root, "experiments/runs/"+output+"/run_manifest.json").is_file())):
            raise InputContractError("unused_separate_research_output_required")
        if set(receipt["evidence_sha256"]) != set(FILES):
            raise InputContractError("complete_accepted_evidence_map_required")
        evidence = {}
        for name in FILES:
            path = (_within(run, "data/processed/features/development/"+name) if name == "development_input_manifest.json"
                    else _within(protocol, name))
            body = _read(path, receipt["evidence_sha256"][name], max_metadata_bytes)
            evidence[name] = body if name.endswith(".csv") else _json(body)
        actual_code = code_hashes(root)
        if (not actual_code or actual_code != code_hashes(Path(__file__).resolve().parents[1])
                or receipt["code_sha256"] != actual_code):
            raise InputContractError("accepted_execution_code_changed")
        audit, population, screening = (evidence[n] for n in ("source_audit.json", "population.json", "screening.json"))
        if (audit["category"] != "ACTUAL SOURCE AUDIT; NOT A MODEL RESULT" or type(audit["model_fits"]) is not int or audit["model_fits"] != 0
                or type(audit["source_records"]) is not int or audit["source_records"] < 1):
            raise InputContractError("actual_source_audit_required")
        records = population["records"]
        if (population["identity_policy"] != "snapshot-original-position-sha256-v1"
                or population["source_audit_sha256"] != receipt["evidence_sha256"]["source_audit.json"]
                or population["branch"] != receipt["branch"] or type(records) is not list or not records):
            raise InputContractError("accepted_prospective_population_required")
        sources = audited_snapshots(audit)
        index, locators = {}, set()
        mappings = population["source_label_mappings"]
        for record in records:
            oid = record["observation_id"]
            locator = record["source_dataset"], record["snapshot_sha256"], record["source_file"], record["source_row_id"]
            if (oid in index or locator in locators or sources.get((record["source_dataset"], record["source_file"])) != record["snapshot_sha256"]
                    or oid != prospective_id(*locator) or type(record["target"]) is not int or record["target"] not in (0, 1)):
                raise InputContractError("population_identity_not_unique_or_provenance_mismatch")
            matches = [m for m in mappings if m["source_dataset"] == record["source_dataset"]
                       and type(m["native"]) is type(record["native_label"]) and m["native"] == record["native_label"]]
            if (len(matches) != 1 or matches[0]["target"] != record["target"]
                    or matches[0]["meaning"] not in ({"phishing"} if record["target"] else {"legitimate", "ham"})
                    or not _text(matches[0]["primary_source_reference"])):
                raise InputContractError("source_backed_native_mapping_required_no_spam_relabel")
            index[oid] = record; locators.add(locator)
        exclusions = screening["excluded_by_primary_reason"]
        if (screening["source_audit_sha256"] != population["source_audit_sha256"]
                or screening["eligible_population_fingerprint"] != fingerprint(records)
                or type(exclusions) is not dict or any(not _text(k) or type(v) is not int or v < 0 for k, v in exclusions.items())
                or len(records) + sum(exclusions.values()) != audit["source_records"]):
            raise InputContractError("screening_attrition_not_reconciled")
        assignment_rows = list(csv.DictReader(io.StringIO(evidence["assignments.csv"].decode("utf-8-sig")), strict=True))
        required = {"observation_id", "source_dataset", "target", "group_id", "partition", "cv_fold"}
        assignments = {}
        for row in assignment_rows:
            if set(row) != required or row["observation_id"] in assignments or row["observation_id"] not in index:
                raise InputContractError("exact_assignment_population_required")
            original = index[row["observation_id"]]
            if (row["target"] not in {"0", "1"} or int(row["target"]) != original["target"]
                    or row["source_dataset"] != original["source_dataset"]
                    or not re.fullmatch(r"[1-5]?", row["cv_fold"])):
                raise InputContractError("assignment_source_target_or_fold_mismatch")
            assignments[row["observation_id"]] = PartitionAssignment(row["observation_id"], row["group_id"], row["partition"],
                int(row["cv_fold"]) if row["cv_fold"] else None)
        if set(assignments) != set(index):
            raise InputContractError("exact_assignment_population_required")
        counts = validate_supplied_partitions(tuple(assignments.values()), folds=5)
        if any(n < 1 for n in counts.values()):
            raise InputContractError("three_partition_roles_required")
        for role in counts:
            if {index[oid]["target"] for oid, a in assignments.items() if a.partition == role} != {0, 1}:
                raise InputContractError("two_class_partition_required")
        freeze = evidence["feature_freeze.json"]
        if (freeze["code_sha256"] != actual_code or freeze["assignment_sha256"] != receipt["evidence_sha256"]["assignments.csv"]
                or freeze["dictionary_sha256"] != receipt["evidence_sha256"]["dictionary.json"]
                or not _text(freeze["rule_language_availability_reference"])
                or not _text(freeze["group_policy_reference"]) or type(freeze["grouping_limitations"]) is not list
                or freeze["data_scope"] != "development_only"):
            raise InputContractError("actual_feature_group_freeze_required")
        d = evidence["dictionary.json"]
        dictionary = DevelopmentSpecification(d["dataset"], tuple(FeatureColumn(c["name"], c["kind"]) for c in d["conventional"]),
            d["protocol_reference"], d["feature_dictionary_reference"])
        if dictionary.dataset != receipt["branch"]:
            raise InputContractError("accepted_branch_dictionary_mismatch")
        dataset = load_development_dataset(root, input_run_id, specification=dictionary)
        entry = evidence["development_input_manifest.json"]["inputs"][dictionary.dataset]
        supplied = _read_csv(_within(run, "data/processed/features/development/"+DEVELOPMENT_FILES[dictionary.dataset]),
            entry["development_sha256"], behavioral=False, specification=dictionary)
        for row in supplied:
            original = index.get(row["observation_id"])
            native = row.get("source_label" if dictionary.dataset == "Web" else "Result" if dictionary.dataset == "UCI" else "label")
            if (original is None or row["source_dataset"] != original["source_dataset"]
                    or row["source_row_id"] != original["source_row_id"] or native != original["native_label"]
                    or (dictionary.dataset == "Web" and row["source_file"] != original["source_file"])):
                raise InputContractError("development_source_locator_or_native_label_changed")
        ids = {oid for oid, a in assignments.items() if a.partition == "development"}
        if (ids != {r.observation_id for r in dataset.observations}
                or dataset_fingerprint(dataset) != receipt["input_fingerprint"]):
            raise InputContractError("actual_development_population_mismatch")
        for r in dataset.observations:
            a = assignments[r.observation_id]
            if (r.target, r.group_id, r.fold) != (index[r.observation_id]["target"], a.group_id, a.cv_fold):
                raise InputContractError("actual_development_assignments_changed")
        specification = parse_specification(evidence["experiment.json"])
        if any(c.model.parameters.get("n_jobs", 1) != 1 for c in specification.candidates):
            raise InputContractError("accepted_single_thread_candidate_required")
        if diagnostic and dataset.specification.dataset not in {"Email", "Web"}:
            raise InputContractError("source_controls_require_content_branch")
        expected_configurations = (("E1",) if diagnostic else
            (("E3",) if dictionary.dataset in {"Email", "Web"} else ("U1",)) if ablation else dataset.configurations)
        if (specification.configurations != expected_configurations
                or (not ablation and specification.omitted_features) or (ablation and not specification.omitted_features)):
            raise InputContractError("principal_run_requires_complete_matched_configurations")
        for c in expected_configurations:
            plans = development_folds(dataset, c)
            names = set(plans[0].feature_names)
            if (not set(specification.omitted_features) <= names
                    or names <= set(specification.omitted_features)):
                raise InputContractError("invalid_accepted_ablation_features")
        selection = evidence["selection.json"]
        if (selection["primary_pr_auc"] != "noninterpolated_average_precision_pooled_oof"
                or selection["bootstrap_resamples"] != 2000 or selection["confidence"] != .95
                or type(selection["delta_pr"]) not in (int, float) or not math.isfinite(selection["delta_pr"])
                or not 0 <= selection["delta_pr"] <= 1 or not _text(selection["delta_pr_justification"])
                or selection["candidate_families"] != ["logistic_regression", "linear_svm", "random_forest", "xgboost"]
                or not _text(selection["benchmark_protocol_reference"]) or not _text(selection["srs_disposition"])):
            raise InputContractError("frozen_selection_and_benchmark_settings_required")
        p = selection["policy"]
        # Diagnostics do not select an implementation representation. Validate the
        # shared numeric/tie settings through the existing policy validator while
        # checking their actual E1-only scope separately below.
        policy = SelectionPolicy(tuple(p["families"]), "E3" if diagnostic else p["configuration"], p["delta_pr"], p["resamples"], p["confidence"], p["seed"],
            p["hard_limits"], p["memory_evidence"], tuple(p["calibration_order"]), tuple(p["efficiency_order"]), p["protocol_reference"])
        benchmark = selection["benchmark"]
        if (policy.families != tuple(selection["candidate_families"]) or policy.delta_pr != selection["delta_pr"]
                or policy.resamples != 2000 or policy.confidence != .95 or policy.seed != specification.candidates[0].model.seed
                or policy.protocol_reference != specification.protocol_reference
                or p["configuration"] != ("E1" if diagnostic else
                    "E3" if receipt["branch"] in {"Email", "Web"} else "U1")
                or set(benchmark) != {"warmup", "repetitions", "batch_size", "thread_reference", "hardware_reference", "payload_class", "cold_warm"}
                or type(benchmark["warmup"]) is not int or benchmark["warmup"] < 0
                or type(benchmark["repetitions"]) is not int or benchmark["repetitions"] < 1
                or benchmark["batch_size"] != 1 or benchmark["cold_warm"] != "warm"
                or any(not _text(benchmark[k]) for k in ("thread_reference", "hardware_reference", "payload_class"))):
            raise InputContractError("exact_frozen_selection_policy_and_benchmark_required")
        environment = evidence["environment.json"]
        required_packages = {"numpy", "scipy", "scikit-learn", "xgboost", "skops", "joblib", "threadpoolctl"}
        if not required_packages <= set(environment) or any(metadata.version(package) != version for package, version in environment.items()):
            raise InputContractError("accepted_scientific_environment_mismatch")
        budget = receipt["budget"]
        if (set(budget) != {"max_base_fits", "max_calibration_fits", "max_seconds", "max_training_rows", "threads"}
                or any(type(budget[k]) is not int or budget[k] < 1 for k in budget)
                or budget["threads"] != 1):
            raise InputContractError("explicit_bounded_research_budget_required")
        estimate = fit_estimate(specification)
        if (estimate["base_fits"] > budget["max_base_fits"] or estimate["calibration_fits"] > budget["max_calibration_fits"]
                or len(dataset.observations) > budget["max_training_rows"]):
            raise InputContractError("estimated_research_budget_exceeded")
        context = VerifiedResearchRun(expected_authorization_sha256, receipt["input_fingerprint"],
            fingerprint(specification_record(specification)), input_run_id, output, receipt["branch"],
            receipt["exposure_disposition"], authority["name"], freeze_json(actual_code), freeze_json(budget),
            freeze_json({oid: index[oid]["source_dataset"] for oid in ids}), freeze_json(estimate), freeze_json(selection), _TOKEN)
        context._state.update(boundary=boundary, checkout_root=str(root),
            environment_sha256=fingerprint(environment),
            source_population_sha256=fingerprint(records),
            source_audit_sha256=receipt["evidence_sha256"]["source_audit.json"])
        if readback:
            context._state["readback_only"] = True
        return context, dataset, specification
    except InputContractError:
        raise
    except Exception:
        raise InputContractError("accepted_research_evidence_invalid_or_incomplete") from None
