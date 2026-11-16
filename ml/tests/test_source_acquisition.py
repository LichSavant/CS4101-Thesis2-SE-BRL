import hashlib
import io
import json

import pytest

from ml.source_acquisition import acquire_zenodo
from ml.experiment_inputs import InputContractError


def specification(tmp_path):
    payload = b"synthetic,fixture\nvalue,value\n"
    record = {"id": 8041387, "metadata": {"access_right": "open", "license": {"id": "cc-by-4.0"}, "title": "synthetic source"},
              "files": [{"key": "phishing.csv", "size": len(payload), "checksum": "md5:"+hashlib.md5(payload).hexdigest()}]}
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps(record))
    options = dict(expected_record_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), record_id=8041387,
        filenames=("phishing.csv",), directory=tmp_path/"snapshot", max_total_bytes=1000, max_elapsed_seconds=60, authorization_reference="synthetic:access")
    return path, payload, options


class Response(io.BytesIO):
    def geturl(self):
        return "https://zenodo.org/records/8041387/files/phishing.csv"


def test_snapshot_integrity_receipt_and_exclusive_creation(tmp_path):
    path, payload, options = specification(tmp_path)
    original = path.read_bytes()
    report = acquire_zenodo(path, **options, opener=lambda *a, **k: Response(payload))
    assert (tmp_path/"snapshot/phishing.csv").read_bytes() == payload
    assert report["model_fits"] == 0 and report["population_status"] == "not_screened_not_frozen"
    assert report["files"][0]["sha256"] == hashlib.sha256(payload).hexdigest()
    assert (tmp_path/"snapshot/source_manifest.json").exists() and path.read_bytes() == original
    with pytest.raises(InputContractError):
        acquire_zenodo(path, **options, opener=lambda *a, **k: pytest.fail("must not request existing snapshot"))


@pytest.mark.parametrize("change", ({"max_total_bytes": 1}, {"max_total_bytes": True}, {"expected_record_sha256": "0"*64},
    {"filenames": ("../escape",)}, {"record_id": 42}, {"authorization_reference": ""}))
def test_invalid_requests_fail_before_network_or_directories(tmp_path, change):
    path, payload, options = specification(tmp_path)
    options.update(change)
    with pytest.raises(InputContractError):
        acquire_zenodo(path, **options, opener=lambda *a, **k: pytest.fail("network must not be reached"))
    assert not (tmp_path/"snapshot").exists()


@pytest.mark.parametrize("mode", ("truncated", "oversized", "corrupt", "redirect"))
def test_incomplete_or_untrusted_payload_never_leaves_a_completed_snapshot(tmp_path, mode):
    path, payload, options = specification(tmp_path)
    class UnsafeResponse(Response):
        def geturl(self):
            return "https://untrusted.test/data" if mode == "redirect" else super().geturl()
    data = payload[:-1] if mode == "truncated" else payload+b"x" if mode == "oversized" else b"x"*len(payload) if mode == "corrupt" else payload
    with pytest.raises(InputContractError):
        acquire_zenodo(path, **options, opener=lambda *a, **k: UnsafeResponse(data))
    assert not (tmp_path/"snapshot").exists()


def test_elapsed_budget_aborts_without_a_completed_snapshot(tmp_path, monkeypatch):
    import ml.source_acquisition as module
    path, payload, options = specification(tmp_path)
    options["max_elapsed_seconds"] = 1
    ticks = iter((0, 2))
    monkeypatch.setattr(module, "monotonic", lambda: next(ticks))
    with pytest.raises(InputContractError, match="time_budget"):
        acquire_zenodo(path, **options, opener=lambda *a, **k: pytest.fail("budget exhausted before network"))
    assert not (tmp_path/"snapshot").exists()


def test_other_corpora_in_same_curated_record_are_not_silent_replacements(tmp_path):
    path, payload, options = specification(tmp_path)
    options.update(record_id=8339691, filenames=("TREC_07.csv",))
    with pytest.raises(InputContractError, match="not_named_by_approved"):
        acquire_zenodo(path, **options, opener=lambda *a, **k: pytest.fail("unapproved corpus must not be downloaded"))
    assert not (tmp_path/"snapshot").exists()
