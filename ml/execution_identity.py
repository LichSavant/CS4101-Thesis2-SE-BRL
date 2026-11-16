"""Content-free code/environment identity for software and future no-fit runs."""
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

from ml.experiment_inputs import InputContractError
from ml.metadata import canonical_json


def execution_identity(root, *, code_sha256, settings_sha256):
    """HEAD alone cannot reproduce a dirty tree; retain exact code digests too."""
    if (type(code_sha256) is not dict or not code_sha256
            or any(type(k) is not str or not k or not _digest(v) for k,v in code_sha256.items())
            or not _digest(settings_sha256)):
        raise InputContractError("exact_code_and_settings_digests_required")
    root=Path(root)
    git={"head":None,"branch":None,"dirty":None,"status_sha256":None,"state":"unavailable"}
    try:
        def read(*args):
            return subprocess.check_output(["git","--no-optional-locks","-C",str(root),*args],stderr=subprocess.DEVNULL,
                timeout=5,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        head=read("rev-parse","HEAD").decode().strip()
        branch=read("branch","--show-current").decode().strip()
        status=read("status","--porcelain=v1","--untracked-files=all")
        git=dict(head=head,branch=branch,dirty=bool(status),status_sha256=hashlib.sha256(status).hexdigest(),state="observed")
    except (OSError,subprocess.SubprocessError):
        pass  # Unknown is explicit, never represented as a clean checkout.
    libraries={}
    for name in ("numpy","scipy","scikit-learn","xgboost","skops","joblib","threadpoolctl","fastapi","pydantic"):
        try:libraries[name]=metadata.version(name)
        except metadata.PackageNotFoundError:libraries[name]=None
    return {"schema":"execution-identity-1","git":git,"code_sha256":dict(sorted(code_sha256.items())),
        "settings_sha256":settings_sha256,"python":sys.version,"platform":platform.platform(),
        "libraries":libraries,"reproducible_from_head_alone":False,
        "source_custody_established":False}


def _digest(value):
    return type(value) is str and re.fullmatch(r"[a-f0-9]{64}",value) is not None


def write_integrity_receipt(directory, *, identity, input_sha256, category):
    """Exclusive completion marker for a newly created directory, never a reseal.

    Only these neutral categories are supported. A model/research bundle must
    still use its existing specialized authorized writer and reload validation.
    """
    if category not in {"software_validation","no_fit_preparation"}:
        raise InputContractError("neutral_receipt_category_required")
    if (type(input_sha256) is not dict or not input_sha256
            or any(type(k) is not str or not k or not _digest(v) for k,v in input_sha256.items())
            or not isinstance(identity,dict) or identity.get("schema")!="execution-identity-1"):
        raise InputContractError("receipt_identity_and_input_digests_required")
    directory=Path(directory).resolve()
    target=directory/"completion_integrity.json"
    if target.exists():
        raise InputContractError("integrity_receipt_already_exists")
    outputs={}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink() or not path.resolve().is_relative_to(directory):
            raise InputContractError("redirected_receipt_output_forbidden")
        if path.is_file():outputs[path.relative_to(directory).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    if not outputs:
        raise InputContractError("nonempty_completed_output_required")
    record={"schema":"completion-integrity-1","category":category,"identity":identity,
        "input_sha256":input_sha256,"output_sha256":outputs,"research_readiness_established":False}
    body=canonical_json(record).encode()
    with target.open("xb") as stream:stream.write(body)
    return hashlib.sha256(body).hexdigest()


def verify_integrity_receipt(directory, *, expected_sha256):
    directory=Path(directory).resolve()
    target=directory/"completion_integrity.json"
    if not _digest(expected_sha256) or target.is_symlink():
        raise InputContractError("independent_integrity_digest_required")
    body=target.read_bytes()
    if hashlib.sha256(body).hexdigest()!=expected_sha256:
        raise InputContractError("integrity_receipt_digest_mismatch")
    record=json.loads(body)
    actual={p.relative_to(directory).as_posix():p for p in directory.rglob("*") if p.is_file() and p!=target}
    if set(actual)!=set(record["output_sha256"]):
        raise InputContractError("integrity_output_set_changed")
    for name,path in actual.items():
        if path.is_symlink() or not path.resolve().is_relative_to(directory) or hashlib.sha256(path.read_bytes()).hexdigest()!=record["output_sha256"][name]:
            raise InputContractError("integrity_output_changed")
    return record
