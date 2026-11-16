"""Complete, exclusive synthetic nested run bundles, including fitted state.

Trusted producers only. Hashes authenticate integrity relative to a separately
trusted digest; they do not establish scientific approval. Process termination
may leave an incomplete directory, which has no completed run manifest.
"""
import hashlib
import json
from pathlib import Path
import tempfile

from ml.development_experiments import _within, _manifest_object
from ml.development_runner import _write_result_bundle, _verify_result_bundle
from ml.experiment_engine import ENGINE_VERSION, FittedSigmoid
from ml.experiment_inputs import InputContractError
from ml.metadata import canonical_json, fingerprint
from ml.model_persistence import save_fold_artifact, load_fold_artifact

BUNDLE_VERSION = "nested-synthetic-artifacts-0.1.0"


def write_nested_bundle(directory, result, fitted, *, code_reference, code_hashes, execution_context=None):
    """Stage privately, then exclusive files/manifest-last; rollback owned files.

    Contains only explicitly returned outer-fold models; not a selected final
    model, a calibrator fitted on reserved calibration data or research output.
    """
    directory = Path(directory)
    if directory.exists() or not directory.parent.is_dir():
        raise InputContractError("unused_run_directory_and_existing_parent_required")
    if execution_context is not None:
        from ml.preflight import require_research_fitting
        require_research_fitting(execution_context)
        execution_context.verify_result(result)
    if (result.get("engine_version") != ENGINE_VERSION
            or (execution_context is None and (result.get("result_category") != "SYNTHETIC RESULT" or result.get("research_execution") != "BLOCKED"))
            or result.get("request_fingerprint") != fingerprint(result["request"])):
        raise InputContractError("complete_synthetic_nested_result_required")
    reports = {(r["configuration"], r["fold"]): r for r in result["fold_reports"]}
    supplied = {(c, f): (p, s, t) for c, f, p, s, t in fitted}
    if not reports or len(supplied) != len(fitted) or len(reports) != len(result["fold_reports"]) or set(supplied) != set(reports):
        raise InputContractError("exact_outer_model_coverage_required")
    for key, (pipeline, sigmoid, threshold) in supplied.items():
        report = reports[key]
        if (key[0] not in {"E1", "E2", "E3", "U1"} or type(key[1]) is not int or key[1] not in range(1, 6)
                or pipeline.audit_record() != report["pipeline"] or sigmoid.state() != report["calibration"]
                or threshold != report["threshold"]):
            raise InputContractError("outer_model_state_mismatch")
    with tempfile.TemporaryDirectory(prefix="sebrl-nested-artifacts-") as temporary:
        staging = Path(temporary)
        _write_result_bundle(staging / "results", result, code_reference=code_reference, code_hashes=code_hashes, execution_context=execution_context)
        (staging / "models").mkdir()
        models = {}
        for (config, fold), (pipeline, sigmoid, threshold) in supplied.items():
            relative = f"models/{config}-fold-{fold}"
            digest = save_fold_artifact(staging / relative, pipeline, code_reference=code_reference, execution_context=execution_context)
            models[relative] = {"manifest_sha256": digest, "calibration": sigmoid.state(), "threshold": threshold}
        files = {p.relative_to(staging).as_posix(): p.read_bytes() for p in staging.rglob("*") if p.is_file()}
        manifest = {"version": BUNDLE_VERSION, "result_category": result["result_category"], "research_execution": result["research_execution"],
                    "authorization_sha256": result.get("authorization_sha256"),
                    "code_reference": code_reference, "input_fingerprint": result["input_fingerprint"],
                    "request_fingerprint": result["request_fingerprint"], "models": models,
                    "outputs": {n: hashlib.sha256(b).hexdigest() for n, b in files.items()}}
        body = canonical_json(manifest).encode()
        files["run_manifest.json"] = body  # completion marker copied last
        created_files, created_dirs = [], []
        directory.mkdir()
        created_dirs.append(directory)
        try:
            for name, payload in files.items():
                target = _within(directory, name)
                absent = []
                parent = target.parent
                while parent != directory and not parent.exists():
                    absent.append(parent)
                    parent = parent.parent
                for parent in reversed(absent):
                    parent.mkdir()
                    created_dirs.append(parent)
                with target.open("xb") as stream:
                    created_files.append(target)
                    stream.write(payload)
        except OSError:
            for path in reversed(created_files):
                path.unlink()
            for path in reversed(created_dirs):
                path.rmdir()
            raise InputContractError("nested_bundle_write_failed") from None
        return hashlib.sha256(body).hexdigest()


def load_nested_bundle(directory, *, expected_manifest_sha256, max_bytes, execution_context=None):
    """Digest-checked complete bundle; verify all hashes before model loading.

    max_bytes limits the entire encoded bundle plus each decompressed model
    archive. Caller owns the provenance/trust of the independently supplied hash.
    """
    import re
    if (type(expected_manifest_sha256) is not str or not re.fullmatch("[a-f0-9]{64}", expected_manifest_sha256)
            or type(max_bytes) is not int or max_bytes < 1):
        raise InputContractError("explicit_bundle_digest_and_resource_limit_required")
    directory = Path(directory)
    path = _within(directory, "run_manifest.json")
    if not path.is_file() or path.stat().st_size > max_bytes:
        raise InputContractError("bundle_manifest_missing_or_oversized")
    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != expected_manifest_sha256:
        raise InputContractError("run_manifest_digest_mismatch")
    try:
        manifest = json.loads(body, object_pairs_hook=_manifest_object)
        if execution_context is not None:
            from ml.preflight import require_research_fitting
            require_research_fitting(execution_context)
            scope_valid = (manifest["result_category"] == "RESEARCH RESULT"
                           and manifest["research_execution"] == "AUTHORIZED DEVELOPMENT ONLY"
                           and manifest["authorization_sha256"] == execution_context.authorization_sha256)
        else:
            scope_valid = manifest["result_category"] == "SYNTHETIC RESULT" and manifest["research_execution"] == "BLOCKED"
        if manifest["version"] != BUNDLE_VERSION or not scope_valid:
            raise InputContractError("nested_bundle_scope_mismatch")
        expected = manifest["outputs"]
        actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
        if set(expected) | {"run_manifest.json"} != actual:
            raise InputContractError("nested_bundle_files_mismatch")
        total = len(body)
        for name, digest in expected.items():
            path = _within(directory, name)
            total += path.stat().st_size
            if total > max_bytes:
                raise InputContractError("nested_bundle_resource_limit")
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise InputContractError("nested_bundle_payload_mismatch")
        result = _verify_result_bundle(directory / "results", execution_context)
        if (result["input_fingerprint"] != manifest["input_fingerprint"]
                or result["request_fingerprint"] != manifest["request_fingerprint"]):
            raise InputContractError("nested_bundle_result_mismatch")
        fitted = []
        reports = {(r["configuration"], r["fold"]): r for r in json.loads((directory / "results/metrics.json").read_bytes())["fold_reports"]}
        if len(manifest["models"]) != len(reports):
            raise InputContractError("nested_model_coverage_mismatch")
        for name, entry in manifest["models"].items():
            if not re.fullmatch(r"models/(E[123]|U1)-fold-[1-5]", name):
                raise InputContractError("nested_model_path_mismatch")
            config, fold = name.split("/")[1].split("-fold-")
            key = config, int(fold)
            report = reports[key]
            if entry["calibration"] != report["calibration"] or entry["threshold"] != report["threshold"]:
                raise InputContractError("nested_calibration_or_threshold_mismatch")
            pipeline = load_fold_artifact(_within(directory, name), expected_manifest_sha256=entry["manifest_sha256"], max_bytes=max_bytes,
                                          execution_context=execution_context)
            if pipeline.audit_record() != report["pipeline"]:
                raise InputContractError("nested_fitted_pipeline_mismatch")
            fitted.append((config, int(fold), pipeline, FittedSigmoid.from_state(entry["calibration"]), entry["threshold"]))
        return manifest, tuple(fitted)
    except InputContractError:
        raise
    except Exception:
        raise InputContractError("nested_bundle_invalid") from None
