"""Explicit offline CPU smoke test; synthetic fixtures only, no acquisition.

Uses the existing review policy and existing synthetic fixtures. Successful
execution verifies engineering integration, never semantic accuracy or release.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True


def process_memory():
    """Native OS process counters, including native tensor allocations."""
    if sys.platform != "win32":
        raise RuntimeError("This measurement harness requires Windows process counters")
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (key, ctypes.c_size_t) for key in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return {key: getattr(counters, key) for key in (
        "PeakWorkingSetSize", "WorkingSetSize", "PeakPagefileUsage", "PrivateUsage")}


def verify_snapshot(cache, manifest):
    snapshot = cache / ("models--" + manifest["repository"].replace("/", "--")) / "snapshots" / manifest["revision"]
    if {p.name for p in snapshot.iterdir()} != set(manifest["files"]):
        raise RuntimeError("Snapshot must contain exactly the seven approved files")
    verified = {}
    for name, expected in manifest["files"].items():
        path = snapshot / name
        size = path.stat().st_size
        if size != expected["size"]:
            raise RuntimeError("Snapshot size mismatch: " + name)
        sha, blob = hashlib.sha256(), hashlib.sha1()
        blob.update(f"blob {size}\0".encode())
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                sha.update(chunk)
                blob.update(chunk)
        actual = {"size": size, "sha256": sha.hexdigest(), "git_blob_sha1": blob.hexdigest()}
        if any(actual[key] != value for key, value in expected.items()):
            raise RuntimeError("Snapshot integrity mismatch: " + name)
        verified[name] = actual
    return verified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cache, output = args.cache.resolve(), args.output.resolve()
    local = (ROOT / ".venv-transformer").resolve()
    if not cache.is_relative_to(local) or not output.is_relative_to(local):
        raise ValueError("Cache and output must stay inside the ignored isolated runtime")
    temporary = local / "offline-tmp"
    temporary.mkdir(exist_ok=True)
    tempfile.tempdir = str(temporary)
    os.environ.update(HF_HUB_CACHE=str(cache), HUGGINGFACE_HUB_CACHE=str(cache),
                      HF_HOME=str(cache.parent), HF_HUB_DISABLE_IMPLICIT_TOKEN="1",
                      HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
                      PYTHONDONTWRITEBYTECODE="1", TOKENIZERS_PARALLELISM="false",
                      TMP=str(temporary), TEMP=str(temporary), TMPDIR=str(temporary),
                      TORCH_HOME=str(local / "torch-cache"))
    host = {"python": platform.python_version(), "platform": platform.platform(),
            "processor": os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
            "logical_cpus": os.cpu_count(), "torch_threads": 2, "torch_interop_threads": 1}
    blocked = []

    def audit(event, values):
        if event in {"socket.connect", "socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr",
                     "socket.getnameinfo", "socket.sendto", "socket.sendmsg",
                     "socket.bind", "subprocess.Popen", "os.system"}:
            blocked.append({"event": event, "caller": [
                Path(frame.filename).name + ":" + frame.name for frame in traceback.extract_stack(limit=5)[:-1]]})
            raise RuntimeError("Offline verification prohibits network and subprocesses")
        if event == "open" and isinstance(values[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(values[0])).resolve()
            mode, flags = values[1:3]
            write = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)))
            if write and not path.is_relative_to(local):
                blocked.append("write_outside_isolated_runtime")
                raise RuntimeError("Output scope violation")
            if (path.suffix.lower() in {".csv", ".arff", ".parquet", ".xlsx", ".ipynb", ".jsonl"}
                    or any(part in path.as_posix().lower() for part in (
                        "/datasets-raw/", "/experiments/data/", "/experiments/results/", "/sealed"))):
                blocked.append("research_input_access")
                raise RuntimeError("Research inputs prohibited")

    sys.addaudithook(audit)
    manifest = json.loads((ROOT / "tools/verification/pinned-minilm-files.json").read_text())
    from ml.se_brl.semantic_candidates import (
        MODEL_ID, MODEL_REVISION, PinnedLocalNliScorer, SemanticInferenceUnavailable, semantic_configuration)
    if manifest["repository"] != MODEL_ID or manifest["revision"] != MODEL_REVISION:
        raise RuntimeError("Acquisition identity differs from approved runtime")
    verified = verify_snapshot(cache, manifest)  # Must finish before native model imports or loading.
    spec, _ = semantic_configuration()
    import torch
    import transformers
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    before = process_memory()
    start = time.perf_counter()
    model = PinnedLocalNliScorer()
    loading_seconds = time.perf_counter() - start
    if model.model.training or any(parameter.device.type != "cpu" for parameter in model.model.parameters()):
        raise RuntimeError("CPU evaluation mode required")
    from ml.datasets import DatasetRecord
    from ml.se_brl.detectors import DetectorContext
    from ml.se_brl.semantic_review import ReviewContractError, predictor_values, review_record, validate_review
    from ml.tests.test_semantic_review import EXAMPLES, source

    class Measured:
        def __init__(self):
            self.latencies = []
        def score(self, text, indicator):
            if len(self.latencies) >= 512:
                raise RuntimeError("Bounded smoke test call limit exceeded")
            started = time.perf_counter()
            result = model.score(text, indicator)
            self.latencies.append(time.perf_counter() - started)
            return result

    measured = Measured()
    cases, reasons = [], Counter()

    def compare(name, record, context=None, target=None):
        baseline = review_record(record, detector_context=context).to_dict()
        started = time.perf_counter()
        result = review_record(record, scorer=measured, detector_context=context).to_dict()
        elapsed = time.perf_counter() - started
        validate_review(result, record, detector_context=context)
        for old, new in zip(baseline["indicators"], result["indicators"], strict=True):
            for key in ("indicator_id", "dimension_id", "deterministic_state", "evaluation_status", "evidence"):
                assert old[key] == new[key], (name, key)
            assert new["candidate_state"] in {"abstained", "unavailable"}
            assert not new["failure_codes"], (name, new["failure_codes"])
            reasons.update(new["review_reasons"])
        assert result["availability_mask"] == baseline["availability_mask"]
        assert result["learned_values"] == [None] * 4
        assert result["semantic_changes_labels"] is False
        assert not any(result["research_release"].values())
        row = next((r for r in result["indicators"] if r["indicator_id"] == target), None)
        if target:
            assert row["semantic_candidates"], (name, "target never scored")
            assert row["deterministic_state"] == "supported", (name, "synthetic positive rule fixture failed")
        cases.append({"name": name, "seconds": elapsed, "candidate_count": sum(
            len(r["semantic_candidates"]) for r in result["indicators"]), "target": target,
            "target_deterministic_state": row["deterministic_state"] if row else None,
            "target_review_reasons": row["review_reasons"] if row else [],
            "target_nli_labels": [[max(s, key=s.get) for s in c["scores"]]
                                  for c in row["semantic_candidates"]] if row else []})
        return result

    for indicator, example in EXAMPLES.items():
        record, context = source(example)
        compare(indicator, record, context, indicator)
        print("PASS", indicator, flush=True)
    for name, text in (("negation", "Never submit your password."),
                       ("quotation", 'The poster says "Submit your password."'),
                       ("hypothetical", "Hypothetical: Submit your password.")):
        record, context = source(text)
        result = compare(name, record, context)
        row = next(r for r in result["indicators"] if r["indicator_id"] == "credential_sensitive_data_request")
        assert row["needs_review"]
        assert all("submit your password" not in c["evidence"]["text"].lower() for c in row["semantic_candidates"])
    record, _ = source("Click here.")
    result = compare("identity_unavailable", record, DetectorContext())
    assert all(r["candidate_state"] == "unavailable" and not r["semantic_candidates"]
               for r in result["indicators"] if r["indicator_id"] in {"impersonation", "brand_exploitation"})
    for kind, modality, fields in (("url", "standalone_url", {"url": "https://example.test/"}),
                                   ("technical", "engineered_technical_record", {}),
                                   ("email", "content_bearing_email", {})):
        record = DatasetRecord("synthetic:missing", "synthetic-engineering", modality,
                               {"kind": kind, **fields}, tuple(fields), None, {"reference": "synthetic-only"})
        calls = len(measured.latencies)
        result = compare("unavailable_" + kind, record)
        assert calls == len(measured.latencies)
        assert all(r["candidate_state"] == "unavailable" for r in result["indicators"])
    record, context = source("Act now.")
    result = compare("evidence_tamper_baseline", record, context)
    forged = deepcopy(result)
    candidate = next(c for r in forged["indicators"] for c in r["semantic_candidates"])
    candidate["evidence"]["start"] += 1
    try:
        validate_review(forged, record, detector_context=context)
    except (ValueError, ReviewContractError):
        pass
    else:
        raise AssertionError("Forged evidence accepted")
    try:
        predictor_values(result)
    except ReviewContractError:
        pass
    else:
        raise AssertionError("Predictor export gate opened")
    try:
        model.score("synthetic " * 600, "urgency")
    except SemanticInferenceUnavailable as error:
        assert "token limit" in str(error)
    else:
        raise AssertionError("Oversized evidence was truncated or scored")
    assert reasons["semantic_rule_disagreement"] > 0, "No real semantic disagreement exercised"
    assert reasons["hypothesis_disagreement"] > 0, "No real hypothesis disagreement exercised"
    # urllib3 probes local IPv6 support during import and tolerates denial.
    # The bind remains prohibited; this expected denied probe is not traffic.
    expected_probes = [entry for entry in blocked if isinstance(entry, dict)
                       and entry["event"] == "socket.bind"
                       and entry["caller"][-1] == "connection.py:_has_ipv6"]
    unexpected = [entry for entry in blocked if entry not in expected_probes]
    assert not unexpected, unexpected
    after = process_memory()
    latencies = sorted(measured.latencies)
    storage = sum(p.stat().st_size for p in cache.rglob("*") if p.is_file())
    report = {"status": "PASS", "verification_kind": "offline_real_model_synthetic_engineering_only",
              "repository": MODEL_ID, "revision": MODEL_REVISION, "files": verified,
              "integrity_verified_before_loading": True, "snapshot_bytes": sum(f["size"] for f in verified.values()),
              "cache_file_bytes_including_metadata": storage, "runtime": {
                  **host, "torch": torch.__version__, "transformers": transformers.__version__, "device": "cpu"},
              "load_seconds_excluding_imports": loading_seconds,
              "load_measurement": "After integrity hashing; OS file cache may be warm; imports excluded",
              "memory_measurement": "Whole-process Windows counters including native tensors; not model-only memory",
              "memory_before_load_bytes": before,
              "memory_after_tests_bytes": after, "scorer_calls": len(latencies),
              "scorer_latency_seconds_three_hypothesis_pairs": {
                  "first": measured.latencies[0], "mean": statistics.mean(latencies),
                  "median": statistics.median(latencies), "p95": latencies[max(0, (95 * len(latencies) + 99) // 100 - 1)],
                  "min": min(latencies), "max": max(latencies), "total": sum(latencies)},
              "cases_passed": len(cases), "cases": cases, "review_reasons": dict(reasons),
              "network_blocked_by_process_audit": True, "blocked_operations": blocked,
              "expected_denied_ipv6_probes": len(expected_probes), "unexpected_blocked_operations": unexpected,
              "evidence_tamper_rejected": True, "oversized_evidence_abstained": True,
              "deterministic_labels_and_evidence_unchanged": True, "research_gates_closed": True,
              "predictor_export_blocked": True, "datasets_accessed": False, "training_performed": False,
              "semantic_accuracy_validated": False, "hypotheses_sha256": spec["hypotheses_sha256"]}
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("VERIFICATION", output, flush=True)
    print(json.dumps({k: report[k] for k in ("status", "cases_passed", "scorer_calls", "load_seconds_excluding_imports",
                     "memory_after_tests_bytes", "scorer_latency_seconds_three_hypothesis_pairs", "snapshot_bytes")}))


if __name__ == "__main__":
    main()
