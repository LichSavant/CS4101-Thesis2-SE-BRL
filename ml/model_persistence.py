"""Pinned, digest-bound synthetic fold persistence; never pickle or auto-trust.

Load only artifacts from a trusted producer using an independently trusted
manifest digest. Hashes establish integrity, not scientific authorization.
Vocabulary/weights can disclose learned data: future research artifacts require
restricted custody. This module currently writes SYNTHETIC RESULT only.
"""
from importlib import import_module, metadata
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
import zipfile

from ml.classifier_adapters import (ADAPTER_VERSION, ClassifierSpecification, FoldClassifier,
                                    PreprocessingSpecification, require_dependencies)
from ml.development_experiments import DevelopmentSpecification, FeatureColumn, _within, _manifest_object
from ml.experiment_inputs import InputContractError
from ml.metadata import canonical_json

PERSISTENCE_VERSION = "fold-artifact-0.1.0"


def _reviewed_types():
    # skops 0.13 DTypeNode returns its child's ndarray.dtype; NdArrayNode uses
    # np.load(allow_pickle=False). Reviewed for these exact packages. This is a
    # fixed policy, NEVER the scanner's returned list or a caller override.
    pins = {"numpy": "2.2.6", "scipy": "1.15.3", "scikit-learn": "1.6.1", "skops": "0.13.0"}
    try:
        return frozenset({"numpy.dtype"}) if all(metadata.version(p) == v for p, v in pins.items()) else frozenset()
    except metadata.PackageNotFoundError:
        return frozenset()


def _skops():
    try:
        return import_module("skops.io")
    except (ImportError, OSError):
        raise InputContractError("safe_persistence_dependency_unavailable") from None


def _versions(family):
    return {p: metadata.version(p) for p in ("numpy", "scipy", "scikit-learn", "skops")
            + (("xgboost",) if family == "xgboost" else ())}


def _fold_payloads(classifier):
    sio = _skops()
    if classifier.model.family == "xgboost":
        with tempfile.TemporaryDirectory(prefix="sebrl-native-model-") as temporary:
            path = Path(temporary) / "model.json"
            classifier.pipeline.named_steps["classifier"].save_model(path)
            native = path.read_bytes()
        return {"preprocess.skops": sio.dumps(classifier.pipeline.named_steps["preprocess"]), "model.json": native}
    return {"pipeline.skops": sio.dumps(classifier.pipeline)}


def serialized_fold_bytes(classifier):
    """Actual encoded inference pipeline payload bytes, excluding manifests."""
    if not isinstance(classifier, FoldClassifier) or classifier.pipeline is None:
        raise InputContractError("fitted_fold_classifier_required")
    return sum(len(v) for v in _fold_payloads(classifier).values())


def save_fold_artifact(directory, classifier, *, code_reference, execution_context=None):
    """Exclusive leaf directory; payloads first/manifest last; ordinary IO rollback."""
    if not isinstance(classifier, FoldClassifier) or classifier.pipeline is None:
        raise InputContractError("fitted_fold_classifier_required")
    if type(code_reference) is not str or not code_reference.strip():
        raise InputContractError("code_reference_required")
    if execution_context is not None:
        from ml.preflight import require_research_fitting
        require_research_fitting(execution_context)
        if not execution_context._state.get("bound"):
            raise InputContractError("research_run_not_bound")
    directory = Path(directory)
    if directory.exists() or not directory.parent.is_dir():
        raise InputContractError("unused_model_directory_and_existing_parent_required")
    sio = _skops()
    record = classifier.audit_record()
    payloads = _fold_payloads(classifier)
    for name, payload in payloads.items():
        if name.endswith(".skops") and set(sio.get_untrusted_types(data=payload)) - _reviewed_types():
            raise InputContractError("untrusted_model_types_rejected")
    manifest = {"version": PERSISTENCE_VERSION, "adapter_version": ADAPTER_VERSION,
        "result_category": "SYNTHETIC RESULT" if execution_context is None else "RESEARCH RESULT",
        "research_execution": "BLOCKED" if execution_context is None else "AUTHORIZED DEVELOPMENT ONLY",
        "authorization_sha256": None if execution_context is None else execution_context.authorization_sha256,
        "code_reference": code_reference, "family": classifier.model.family, "configuration": classifier.configuration,
        "dictionary": {"dataset": classifier.dictionary.dataset,
            "columns": [{"name": c.name, "kind": c.kind} for c in classifier.dictionary.conventional],
            "protocol_reference": classifier.dictionary.protocol_reference,
            "feature_dictionary_reference": classifier.dictionary.feature_dictionary_reference},
        "audit": record, "versions": _versions(classifier.model.family),
        "outputs": {n: hashlib.sha256(v).hexdigest() for n, v in payloads.items()}}
    body = canonical_json(manifest).encode()
    payloads["manifest.json"] = body
    created = []
    directory.mkdir()
    try:
        for name, payload in payloads.items():
            with (directory / name).open("xb") as f:
                created.append(directory / name)
                f.write(payload)
    except OSError:
        for path in reversed(created):
            path.unlink()
        directory.rmdir()
        raise InputContractError("model_artifact_write_failed") from None
    return hashlib.sha256(body).hexdigest()


def _bounded_file(directory, name, limit):
    path = _within(directory, name)
    if not path.is_file() or path.stat().st_size > limit:
        raise InputContractError("model_artifact_missing_or_oversized")
    return path.read_bytes()


def _safe_skops_load(sio, payload, limit):
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            members = archive.infolist()
            if len(members) > 100000 or sum(m.file_size for m in members) > limit:
                raise InputContractError("model_archive_resource_limit")
            if any(m.filename.startswith(("/", "\\")) or ".." in m.filename.replace("\\", "/").split("/") for m in members):
                raise InputContractError("model_archive_path_rejected")
        if set(sio.get_untrusted_types(data=payload)) - _reviewed_types():
            raise InputContractError("untrusted_model_types_rejected")
        return sio.loads(payload, trusted=sorted(_reviewed_types()))
    except InputContractError:
        raise
    except Exception:
        raise InputContractError("model_archive_invalid") from None


def load_fold_artifact(directory, *, expected_manifest_sha256, max_bytes, execution_context=None):
    """Verify independent digest, fixed paths, sizes, versions and types before load.

    No approval flag or arbitrary trusted-type list is accepted. A malicious
    producer is outside this trusted-artifact interface: do not treat digests
    taken from the same untrusted download as authentication.
    """
    if type(expected_manifest_sha256) is not str or not re.fullmatch("[a-f0-9]{64}", expected_manifest_sha256):
        raise InputContractError("independent_manifest_digest_required")
    if type(max_bytes) is not int or max_bytes < 1:
        raise InputContractError("explicit_model_resource_limit_required")
    directory = Path(directory)
    body = _bounded_file(directory, "manifest.json", max_bytes)
    if hashlib.sha256(body).hexdigest() != expected_manifest_sha256:
        raise InputContractError("model_manifest_digest_mismatch")
    try:
        manifest = json.loads(body, object_pairs_hook=_manifest_object)
        family = manifest["family"]
        require_dependencies(family)
        if execution_context is not None:
            from ml.preflight import require_research_fitting
            require_research_fitting(execution_context)
            scope_valid = (manifest["result_category"] == "RESEARCH RESULT"
                           and manifest["research_execution"] == "AUTHORIZED DEVELOPMENT ONLY"
                           and manifest.get("authorization_sha256") == execution_context.authorization_sha256)
        else:
            scope_valid = manifest["result_category"] == "SYNTHETIC RESULT" and manifest["research_execution"] == "BLOCKED"
        if (manifest["version"] != PERSISTENCE_VERSION or manifest["adapter_version"] != ADAPTER_VERSION
                or not scope_valid
                or manifest["versions"] != _versions(family)):
            raise InputContractError("model_version_or_scope_mismatch")
        expected = {"preprocess.skops", "model.json"} if family == "xgboost" else {"pipeline.skops"}
        if set(manifest["outputs"]) != expected or {p.name for p in directory.iterdir()} != expected | {"manifest.json"}:
            raise InputContractError("model_artifact_files_mismatch")
        payloads = {n: _bounded_file(directory, n, max_bytes) for n in expected}
        if any(hashlib.sha256(v).hexdigest() != manifest["outputs"][n] for n, v in payloads.items()):
            raise InputContractError("model_payload_digest_mismatch")
        d, audit = manifest["dictionary"], manifest["audit"]
        dictionary = DevelopmentSpecification(d["dataset"], tuple(FeatureColumn(c["name"], c["kind"]) for c in d["columns"]),
                                              d["protocol_reference"], d["feature_dictionary_reference"])
        model = ClassifierSpecification(family, audit["parameters"], audit["seed"])
        preprocessing = PreprocessingSpecification(**audit["preprocessing"])
        restored = FoldClassifier(dictionary, model, preprocessing, manifest["configuration"])
        names = tuple(audit["feature_names"])
        if not names or tuple(n for n in restored.expected if n in names) != names or len(set(names)) != len(names):
            raise InputContractError("restored_predictor_order_mismatch")
        sio = _skops()
        from sklearn.pipeline import Pipeline
        if family == "xgboost":
            from xgboost import XGBClassifier
            transform = _safe_skops_load(sio, payloads["preprocess.skops"], max_bytes)
            estimator = XGBClassifier()
            estimator.load_model(bytearray(payloads["model.json"]))
            pipeline = Pipeline((("preprocess", transform), ("classifier", estimator)))
        else:
            pipeline = _safe_skops_load(sio, payloads["pipeline.skops"], max_bytes)
        if not isinstance(pipeline, Pipeline) or tuple(pipeline.named_steps) != ("preprocess", "classifier"):
            raise InputContractError("restored_pipeline_structure_mismatch")
        estimator = pipeline.named_steps["classifier"]
        expected_estimators = {"logistic_regression": "sklearn.linear_model._logistic.LogisticRegression",
                               "linear_svm": "sklearn.svm._classes.LinearSVC",
                               "random_forest": "sklearn.ensemble._forest.RandomForestClassifier",
                               "xgboost": "xgboost.sklearn.XGBClassifier"}
        actual_estimator = f"{type(estimator).__module__}.{type(estimator).__name__}"
        if (actual_estimator != audit["estimator"] or actual_estimator != expected_estimators[family]
                or tuple(int(v) for v in estimator.classes_) != (0, 1)):
            raise InputContractError("restored_classifier_mismatch")
        restored.feature_names, restored.pipeline = names, pipeline
        restored._record, restored._attempted = audit, True
        return restored
    except InputContractError:
        raise
    except Exception:
        raise InputContractError("model_artifact_invalid") from None
