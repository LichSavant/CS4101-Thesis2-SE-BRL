"""Verify and import the selected public source-only counterpart checkout.

For the serial, offline integration verifier only. Namespace switching during
import is not a concurrent web-server facility. No peer entry point is run on
import, and no models, datasets, notebooks or research runners are imported.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
import json
from pathlib import Path
import sys


COUNTERPART_COMMIT = "ae20372db6014d4f83153c03ccc2cd92f445ca8c"


def verify_source_manifest(root: Path, manifest: dict) -> dict:
    root = Path(root).resolve()
    if (manifest.get("commit") != COUNTERPART_COMMIT
            or manifest.get("repository") != "https://github.com/LichSavant/-SE-BRL-Research-Review.git"
            or not isinstance(manifest.get("source_files"), dict) or not manifest["source_files"]):
        raise ValueError("selected_counterpart_source_manifest_required")
    verified = {}
    for name, expected in manifest["source_files"].items():
        path = root / name
        if (not isinstance(name, str) or Path(name).is_absolute() or ".." in Path(name).parts
                or path.is_symlink() or root not in path.resolve().parents):
            raise ValueError("counterpart_path_rejected")
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if sha != expected.get("sha256") or blob != expected.get("git_blob_sha1"):
            raise ValueError("counterpart_source_hash_mismatch")
        verified[name] = sha
    return verified


@dataclass(frozen=True)
class CounterpartRuntime:
    root: Path
    manifest: dict
    inputs: object
    integration: object
    preprocessing: object
    extraction: object
    compatibility: object
    representation: object
    envelope: object
    api_adapter: object
    modules: tuple
    commit: str = COUNTERPART_COMMIT

    def verify(self):
        hashes = verify_source_manifest(self.root, self.manifest)
        # Bind every actually loaded peer source to the verified allowlist.
        for module in self.modules:
            file = Path(module.__file__).resolve()
            if self.root not in file.parents or file.relative_to(self.root).as_posix() not in hashes:
                raise ValueError("unmanifested_counterpart_import")
        return hashes


def load_counterpart(root: Path, manifest_path: Path) -> CounterpartRuntime:
    root = Path(root).resolve()
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    verify_source_manifest(root, manifest)
    prefixes = ("ml", "backend")
    def selected(name):
        return any(name == p or name.startswith(p + ".") for p in prefixes)
    local = {name: module for name, module in sys.modules.items() if selected(name)}
    old_path = list(sys.path)
    for name in local:
        del sys.modules[name]
    sys.path.insert(0, str(root))
    try:
        names = ("ml.experiment_inputs", "ml.experiment_integration", "ml.preprocessing",
                 "ml.se_brl.extraction", "ml.behavioral_compatibility", "ml.se_brl.representation",
                 "ml.se_brl.result_envelope", "backend.app.sebrl_adapter")
        imported = [importlib.import_module(name) for name in names]
        modules = tuple(module for name, module in sys.modules.items() if selected(name) and getattr(module, "__file__", None))
    finally:
        for name in list(sys.modules):
            if selected(name):
                del sys.modules[name]
        sys.modules.update(local)
        sys.path[:] = old_path
    runtime = CounterpartRuntime(root, manifest, *imported, modules)
    runtime.verify()
    return runtime
