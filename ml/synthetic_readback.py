"""Repackage existing trusted SYNTHETIC state for current integration checks.

Never fits, calibrates, tunes or promotes research. Old bundles remain intact.
This producer migration verifies independent original digests and lower-level
state versions, then emits NEW code-bound fixture bundles with explicit lineage.
The ordinary runtime loader still rejects the old incompatible component hash.
"""
import argparse
import hashlib
import json
from pathlib import Path

from ml.artifact_analysis import AnalyticalBundle, ArtifactAnalyzer, write_bundle, load_bundle, BUNDLE_VERSION
from ml.decision import RiskPolicy
from ml.development_experiments import _manifest_object, _within
from ml.experiment_engine import FittedSigmoid
from ml.experiment_inputs import InputContractError
from ml.metadata import canonical_json
from ml.model_persistence import load_fold_artifact
from ml.synthetic_system import fixture_artifact


def repackage(source, output, *, expected_receipt_sha256):
    source, output = Path(source), Path(output)
    if output.exists() or not output.parent.is_dir() or not __import__("re").fullmatch(r"[a-f0-9]{64}", expected_receipt_sha256):
        raise InputContractError("unused_output_and_independent_fixture_receipt_required")
    raw = _within(source,"fixture_receipt.json").read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_receipt_sha256:
        raise InputContractError("fixture_receipt_digest_mismatch")
    receipt=json.loads(raw,object_pairs_hook=_manifest_object)
    if (receipt["category"]!="SYNTHETIC RESULT" or type(receipt["research_models_fitted"]) is not int
            or receipt["research_models_fitted"]!=0 or set(receipt["bundles"])!={"Email","Web","UCI","PhiUSIIL"}):
        raise InputContractError("complete_existing_synthetic_fixture_required")
    prepared={}
    for dataset,entry in receipt["bundles"].items():
        directory=_within(source,dataset.lower())
        manifest_bytes=_within(directory,"manifest.json").read_bytes()
        if hashlib.sha256(manifest_bytes).hexdigest()!=entry["manifest_sha256"]:
            raise InputContractError("original_fixture_manifest_changed")
        manifest=json.loads(manifest_bytes,object_pairs_hook=_manifest_object)
        if manifest["scope"]!="synthetic_fixture" or manifest["version"]!=BUNDLE_VERSION:
            raise InputContractError("synthetic_migration_scope_or_version_invalid")
        classifier=load_fold_artifact(_within(directory,"model"),expected_manifest_sha256=manifest["model_manifest_sha256"],max_bytes=20000000)
        state=_within(directory,"calibrator.json").read_bytes()
        if hashlib.sha256(state).hexdigest()!=manifest["calibrator_sha256"]:
            raise InputContractError("original_fixture_calibrator_changed")
        if classifier.dictionary.dataset!=dataset:
            raise InputContractError("original_fixture_branch_mismatch")
        calibrator=FittedSigmoid.from_state(json.loads(state,object_pairs_hook=_manifest_object))
        prepared[dataset]=AnalyticalBundle(classifier,calibrator,RiskPolicy(**manifest["risk_policy"]),
            manifest["classification_threshold"],manifest["identifier"]+"-readback",manifest["scope"],manifest["native_domains"])
    output.mkdir()
    completed={}
    for dataset,bundle in prepared.items():
        digest=write_bundle(output/dataset.lower(),bundle,code_reference="synthetic-state-readback; original receipt SHA256 "+expected_receipt_sha256)
        restored=load_bundle(output/dataset.lower(),expected_manifest_sha256=digest,max_bytes=20000000)
        route={"Email":"content_bearing_email","Web":"content_bearing_webpage","UCI":"UCI","PhiUSIIL":"PhiUSIIL"}[dataset]
        result=ArtifactAnalyzer({route:restored}).analyze(fixture_artifact(dataset,500,1),language="en")
        if result["status"]!="complete":
            raise InputContractError("repackaged_fixture_inference_failed")
        completed[dataset]={"manifest_sha256":digest,"roundtrip_status":"complete"}
    summary={"category":"SYNTHETIC RESULT","research_models_fitted":0,"new_model_fits":0,"new_calibrator_fits":0,
        "source_receipt_sha256":expected_receipt_sha256,"bundles":completed}
    with (output/"fixture_receipt.json").open("x",encoding="utf-8") as f:f.write(canonical_json(summary))
    return summary


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True);p.add_argument("--output",required=True);p.add_argument("--expected-receipt-sha256",required=True)
    args=p.parse_args(argv)
    try:result=repackage(args.source,args.output,expected_receipt_sha256=args.expected_receipt_sha256)
    except (InputContractError,OSError,KeyError,ValueError):
        print(json.dumps({"status":"failed","code":"synthetic_readback_failed","new_model_fits":0}));return 2
    print(json.dumps(result));return 0


if __name__=="__main__":
    raise SystemExit(main())
