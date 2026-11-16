"""Matched diagnostic preparation and separately authorized future execution.

No normalization policy is chosen here. Callers supply a normalized D9 dataset
and its protocol reference. Research fits still require three exact independent
VerifiedResearchRun contexts through the existing engine. Import/preparation
performs no fitting, source loading, allocation, or reserved-partition access.
"""
from dataclasses import replace
from pathlib import Path

from ml.development_experiments import DevelopmentDataset, DevelopmentSpecification, FeatureColumn, development_folds
from ml.development_runner import _validate_dataset, dataset_fingerprint
from ml.experiment_inputs import InputContractError
from ml.metadata import fingerprint


def prepare_source_controls(baseline, normalized, *, sources_by_id, normalization_reference):
    """Validate matched populations and construct the metadata-only control.

    Source names are hashed into opaque text tokens. Vocabulary and every learned
    transform remain local to training folds in the shared classifier adapter.
    The source token exists only in the dedicated diagnostic dataset.
    """
    for dataset in (baseline, normalized):
        _validate_dataset(dataset)
    if baseline.specification.dataset not in {"Email", "Web"}:
        raise InputContractError("source_controls_require_content_branch")
    if baseline.specification != normalized.specification:
        raise InputContractError("matched_diagnostic_dictionary_required")
    if type(normalization_reference) is not str or not normalization_reference.strip():
        raise InputContractError("explicit_normalization_protocol_required")
    def index(dataset):
        return {r.observation_id: r for r in dataset.observations}
    original, comparison = index(baseline), index(normalized)
    if (set(original) != set(comparison) or type(sources_by_id) is not dict
            or set(sources_by_id) != set(original)
            or any(type(v) is not str or not v.strip() for v in sources_by_id.values())):
        raise InputContractError("exact_matched_diagnostic_population_required")
    ids = tuple(sorted(original))
    for oid in ids:
        a, b = original[oid], comparison[oid]
        if (a.target, a.group_id, a.fold, a.behavioral) != (b.target, b.group_id, b.fold, b.behavioral):
            raise InputContractError("diagnostic_metadata_or_availability_changed")
    baseline = replace(baseline, observations=tuple(original[i] for i in ids))
    # Bind the supplied normalization policy into the accepted input fingerprint.
    normalized = replace(normalized, specification=replace(normalized.specification,
        feature_dictionary_reference=normalized.specification.feature_dictionary_reference+
        "; normalization:"+normalization_reference), observations=tuple(comparison[i] for i in ids))
    source_spec = DevelopmentSpecification(baseline.specification.dataset,
        (FeatureColumn("diagnostic_source_token", "text"),),
        baseline.specification.protocol_reference,
        "source-control-v1:"+fingerprint({i:sources_by_id[i] for i in ids}))
    source = DevelopmentDataset(source_spec, tuple(replace(original[i],
        conventional=("src"+fingerprint(sources_by_id[i]),), behavioral=(0,)*8) for i in ids))
    controls = {"baseline": baseline, "normalized_format": normalized, "source_only": source}
    for dataset in controls.values():
        development_folds(dataset, "E1")
    receipt = {"category": "DIAGNOSTIC PREPARATION; NO EXPERIMENT EXECUTED",
        "normalization_reference": normalization_reference,
        "population_sha256": fingerprint(ids),
        "assignment_sha256": fingerprint([(i,original[i].target,original[i].group_id,original[i].fold) for i in ids]),
        "source_map_sha256": fingerprint({i:sources_by_id[i] for i in ids}),
        "input_fingerprints": {name:dataset_fingerprint(d) for name,d in controls.items()},
        "model_fits": 0, "source_independent_performance_established": False}
    return controls, receipt


def _validate_execution(controls, receipt, specification, contexts, output_directory):
    """Future accepted-input execution; never invoked by verification tests.

    Each exact control needs its own accepted context and fit budget. No approval
    is inferred from the descriptive contingency or from baseline authorization.
    Existing complete model/result serialization is reused, with exclusive paths.
    """
    from ml.research_protocol import VerifiedResearchRun, specification_record
    names = {"baseline", "normalized_format", "source_only"}
    if (set(controls) != names or set(contexts) != names or specification.configurations != ("E1",)
            or specification.omitted_features):
        raise InputContractError("exact_source_diagnostic_controls_required")
    if receipt.get("input_fingerprints") != {n:dataset_fingerprint(d) for n,d in controls.items()}:
        raise InputContractError("diagnostic_inputs_changed")
    baseline = controls["baseline"]
    ids = tuple(sorted(r.observation_id for r in baseline.observations))
    indexed = {r.observation_id:r for r in baseline.observations}
    if (set(receipt) != {"category", "normalization_reference", "population_sha256", "assignment_sha256",
            "source_map_sha256", "input_fingerprints", "model_fits", "source_independent_performance_established"}
            or receipt["category"] != "DIAGNOSTIC PREPARATION; NO EXPERIMENT EXECUTED"
            or type(receipt["model_fits"]) is not int or receipt["model_fits"] != 0
            or receipt["source_independent_performance_established"] is not False
            or receipt["population_sha256"] != fingerprint(ids)
            or receipt["assignment_sha256"] != fingerprint([(i,indexed[i].target,indexed[i].group_id,indexed[i].fold) for i in ids])
            or controls["normalized_format"].specification != replace(baseline.specification,
                feature_dictionary_reference=baseline.specification.feature_dictionary_reference+"; normalization:"+receipt["normalization_reference"])):
        raise InputContractError("diagnostic_preparation_receipt_changed")
    expected = {r.observation_id:(r.target,r.group_id,r.fold) for r in baseline.observations}
    for dataset in controls.values():
        if (dataset.specification.dataset != baseline.specification.dataset
                or {r.observation_id:(r.target,r.group_id,r.fold) for r in dataset.observations} != expected):
            raise InputContractError("exact_matched_diagnostic_population_required")
        development_folds(dataset,"E1")
    if (tuple((c.name,c.kind) for c in controls["source_only"].specification.conventional)
            != (("diagnostic_source_token","text"),)
            or any(r.behavioral != (0,)*8 for r in controls["source_only"].observations)):
        raise InputContractError("isolated_source_only_dictionary_required")
    # Validate ALL authority scopes before any fit or output creation.
    for name in sorted(names):
        context = contexts[name]
        if not isinstance(context, VerifiedResearchRun):
            raise InputContractError("exact_diagnostic_authorization_required")
        context.require_verified()
        if (context.input_fingerprint != dataset_fingerprint(controls[name])
                or context.specification_fingerprint != fingerprint(specification_record(specification))
                or fingerprint(dict(context.sources_by_id)) != receipt["source_map_sha256"]
                or context._state.get("boundary") != "E-development-diagnostic-only"
                or context._state.get("bound") or context._state.get("readback_only")):
            raise InputContractError("diagnostic_authorization_input_or_settings_mismatch")
    for row in controls["source_only"].observations:
        if row.conventional != ("src"+fingerprint(contexts["source_only"].sources_by_id[row.observation_id]),):
            raise InputContractError("source_only_payload_contains_non_source_features")
    if len({c.authorization_sha256 for c in contexts.values()}) != 3:
        raise InputContractError("separate_exact_control_authorizations_required")
    output, destinations = _destinations(contexts, output_directory, existing=False)
    return output, destinations


def _destinations(contexts, output_directory, *, existing):
    from ml.development_experiments import _within
    from ml.research_protocol import VerifiedResearchRun
    import re
    if set(contexts) != {"baseline", "normalized_format", "source_only"}:
        raise InputContractError("exact_source_diagnostic_controls_required")
    roots = set()
    for context in contexts.values():
        if not isinstance(context, VerifiedResearchRun):
            raise InputContractError("exact_diagnostic_authorization_required")
        context.require_verified()
        if context._state.get("boundary") != "E-development-diagnostic-only":
            raise InputContractError("diagnostic_scope_required")
        roots.add(context._state.get("checkout_root"))
    if len(roots) != 1 or None in roots:
        raise InputContractError("trusted_diagnostic_root_required")
    root = Path(next(iter(roots)))
    if ".." in Path(output_directory).parts:
        raise InputContractError("diagnostic_destination_mismatch")
    supplied = Path(output_directory).absolute()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,45}", supplied.name):
        raise InputContractError("diagnostic_destination_mismatch")
    output = _within(root, "experiments/runs/"+supplied.name)
    if supplied != output or supplied.resolve() != output:
        raise InputContractError("diagnostic_destination_mismatch")
    destinations = {}
    for name, context in contexts.items():
        expected_id = output.name+"-"+name.replace("_", "-")
        if context.output_run_id != expected_id:
            raise InputContractError("diagnostic_destination_not_authorized")
        destinations[name] = _within(root, "experiments/runs/"+expected_id)
    if not existing and any(p.exists() for p in (output, *destinations.values())):
        raise InputContractError("unused_diagnostic_destinations_required")
    return output, destinations


def execute_source_controls(controls, receipt, *, specification, contexts, output_directory):
    """One bounded subprocess per authenticated diagnostic batch; no queue."""
    import json
    import subprocess
    import sys
    output, _ = _validate_execution(controls, receipt, specification, contexts, output_directory)
    request = {"root": next(iter(contexts.values()))._state["checkout_root"],
        "output_directory": str(output), "receipt": receipt,
        "controls": {n:{"input_run_id":c.input_run_id, "authorization_sha256":c.authorization_sha256} for n,c in contexts.items()}}
    # Exclusive admission survives concurrent calls. Never remove another call's lock.
    lock = output.parent/(output.name+".diagnostic-worker.lock")
    try:
        stream = lock.open("x")
    except FileExistsError:
        raise InputContractError("diagnostic_worker_busy") from None
    try:
        with stream:
            try:
                process = subprocess.run([sys.executable,"-B","-m","ml.diagnostic_execution"],
                    input=json.dumps(request), text=True, capture_output=True,
                    cwd=Path(__file__).resolve().parents[1],
                    timeout=min(c.budget["max_seconds"] for c in contexts.values()),
                    creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            except subprocess.TimeoutExpired:
                raise InputContractError("diagnostic_worker_wall_time_exceeded") from None
            if process.returncode != 0:
                raise InputContractError("diagnostic_worker_failed")
            try:
                result = json.loads(process.stdout)
                digest = result["completion_sha256"]
            except (ValueError, KeyError, TypeError):
                raise InputContractError("diagnostic_worker_completion_invalid") from None
            return load_source_controls(output, contexts=contexts, expected_sha256=digest)
    finally:
        lock.unlink()


def _execute_verified_controls(controls, receipt, *, specification, contexts, output_directory):
    """Worker-only implementation; all admission checks repeat before fitting."""
    import json
    from threadpoolctl import threadpool_limits
    from ml.experiment_engine import run_research_nested_cv
    from ml.experiment_artifacts import write_nested_bundle, load_nested_bundle
    output, destinations = _validate_execution(controls, receipt, specification, contexts, output_directory)
    output.mkdir(parents=True, exist_ok=False)
    digests = {}
    for name in sorted(controls):
        context = contexts[name]
        with threadpool_limits(limits=1):
            result, fitted = run_research_nested_cv(controls[name], specification, execution_context=context)
        context.check_budget()
        result["diagnostic_preparation"] = receipt
        result["diagnostic_control"] = name
        result["causal_behavioral_learning_established"] = False
        from ml.research_execution import research_summaries
        result["research_summaries"] = research_summaries(result, context)
        digests[name] = write_nested_bundle(destinations[name], result, fitted,
            code_reference="accepted-code-map:"+fingerprint(context.code_sha256),
            code_hashes=context.code_sha256, execution_context=context)
        load_nested_bundle(destinations[name], expected_manifest_sha256=digests[name],
            max_bytes=500_000_000, execution_context=context)
    # Completion receipt appears only after every complete bundle was written.
    completed = {"category":"AUTHORIZED DEVELOPMENT DIAGNOSTIC; NOT FINAL EVALUATION",
        "controls":digests, "preparation":receipt, "source_independent_performance_established":False}
    with (output/"diagnostic_completion.json").open("x", encoding="utf-8") as stream:
        json.dump(completed, stream, sort_keys=True, indent=2)
    return completed


def load_source_controls(output_directory, *, contexts, expected_sha256, max_bytes=500_000_000):
    try:
        return _load_source_controls(output_directory, contexts=contexts, expected_sha256=expected_sha256, max_bytes=max_bytes)
    except InputContractError:
        raise
    except (KeyError, TypeError, ValueError, OSError):
        raise InputContractError("diagnostic_completion_invalid") from None


def _load_source_controls(output_directory, *, contexts, expected_sha256, max_bytes):
    """Reload every exact child and marker; never grants fitting authority."""
    from ml.research_protocol import _read, _json
    from ml.experiment_artifacts import load_nested_bundle
    output, destinations = _destinations(contexts, output_directory, existing=True)
    if {p.name for p in output.iterdir()} != {"diagnostic_completion.json"}:
        raise InputContractError("diagnostic_completion_membership_changed")
    record = _json(_read(output/"diagnostic_completion.json", expected_sha256, min(max_bytes, 1_000_000)))
    if (set(record) != {"category", "controls", "preparation", "source_independent_performance_established"}
            or record["category"] != "AUTHORIZED DEVELOPMENT DIAGNOSTIC; NOT FINAL EVALUATION"
            or record["source_independent_performance_established"] is not False
            or set(record["controls"]) != set(contexts)
            or record["preparation"]["input_fingerprints"] != {n:c.input_fingerprint for n,c in contexts.items()}
            or any(record["preparation"]["source_map_sha256"] != fingerprint(dict(c.sources_by_id)) for c in contexts.values())):
        raise InputContractError("diagnostic_completion_schema_or_scope_changed")
    for name, destination in destinations.items():
        load_nested_bundle(destination, expected_manifest_sha256=record["controls"][name],
            max_bytes=max_bytes, execution_context=contexts[name])
    return record
