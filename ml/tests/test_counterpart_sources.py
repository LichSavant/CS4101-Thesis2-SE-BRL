"""Loader security unit tests; these do not assert counterpart compatibility."""
import hashlib
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("counterpart_probe", Path(__file__).resolve().parents[2] / "scripts/verify_counterpart_contracts.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def manifest(raw):
    return {"source_files": {"component.py": {"sha256": hashlib.sha256(raw).hexdigest(),
             "git_blob_sha1": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()}}}


def test_source_hashes_and_git_blob_identity_both_required(tmp_path):
    raw = b"# no execution\r\n"
    path = tmp_path / "component.py"
    path.write_bytes(raw)
    expected = manifest(raw)
    assert probe.verify_sources(tmp_path, expected) == 1
    expected["source_files"]["component.py"]["git_blob_sha1"] = "0" * 40
    with pytest.raises(ValueError, match="hash_mismatch"):
        probe.verify_sources(tmp_path, expected)
    path.write_bytes(b"# changed under same version\n")
    with pytest.raises(ValueError, match="hash_mismatch"):
        probe.verify_sources(tmp_path, manifest(raw))


def test_counterpart_source_symlinks_and_escape_rejected(tmp_path):
    external = tmp_path / "outside"
    external.write_bytes(b"# fixture\n")
    root = tmp_path / "mirror"
    root.mkdir()
    (root / "component.py").symlink_to(external)
    with pytest.raises(ValueError, match="path_rejected"):
        probe.verify_sources(root, manifest(external.read_bytes()))
    expected = {"source_files": {"../outside": manifest(external.read_bytes())["source_files"]["component.py"]}}
    with pytest.raises(ValueError, match="path_rejected"):
        probe.verify_sources(root, expected)
