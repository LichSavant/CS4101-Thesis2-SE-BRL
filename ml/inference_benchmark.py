"""Synthetic model-only timing port; no fitted model, hard SRS limit or selection.

The trusted callback must be prediction on an already model-compatible numeric
matrix. Parsing/features/calibration/attribution/API/rendering stay outside this
boundary. Timing results are batch latency, not per-artifact tail latency.
"""
import math
from time import perf_counter

from ml.evaluation_metrics import _numbers, _quantile
from ml.experiment_inputs import InputContractError


def benchmark_synthetic_inference(predict, rows, *, warmup, repetitions, batch_size,
                                  thread_reference, serialized_model_bytes=None,
                                  memory_probe=None, timer=perf_counter):
    return _benchmark_inference(predict, rows, warmup=warmup, repetitions=repetitions, batch_size=batch_size,
        thread_reference=thread_reference, serialized_model_bytes=serialized_model_bytes, memory_probe=memory_probe, timer=timer)


def _benchmark_inference(predict, rows, *, warmup, repetitions, batch_size,
                         thread_reference, serialized_model_bytes=None, memory_probe=None,
                         timer=perf_counter, execution_context=None):
    rows = tuple(tuple(row) for row in rows)
    if (not callable(predict) or type(warmup) is not int or warmup < 0
            or type(repetitions) is not int or repetitions < 1
            or type(batch_size) is not int or batch_size < 1 or len(rows) != batch_size
            or not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows)
            or type(thread_reference) is not str or not thread_reference.strip()):
        raise InputContractError("explicit_benchmark_configuration_required")
    for row in rows:
        _numbers(row)
    if serialized_model_bytes is not None and (type(serialized_model_bytes) is not int or serialized_model_bytes < 0):
        raise InputContractError("invalid_serialized_model_size")
    if not callable(timer) or (memory_probe is not None and not callable(memory_probe)):
        raise InputContractError("benchmark_callbacks_required")
    latencies, memory = [], []
    try:
        for _ in range(warmup):
            if execution_context is not None:
                execution_context.check_budget()
            predictions = predict(rows)
            if not isinstance(predictions, tuple) or len(predictions) != batch_size:
                raise InputContractError("benchmark_prediction_width_mismatch")
            _numbers(predictions)
        for _ in range(repetitions):
            if execution_context is not None:
                execution_context.check_budget()
            start = timer()
            predictions = predict(rows)
            stop = timer()
            _numbers((start, stop))
            elapsed = stop - start
            if elapsed <= 0:
                raise InputContractError("positive_benchmark_duration_required")
            if not isinstance(predictions, tuple) or len(predictions) != batch_size:
                raise InputContractError("benchmark_prediction_width_mismatch")
            _numbers(predictions)
            latencies.append(elapsed)
            if memory_probe is not None:
                value = memory_probe()
                if type(value) is not int or value < 0:
                    raise InputContractError("invalid_memory_probe")
                memory.append(value)
    except InputContractError:
        raise
    except Exception:
        raise InputContractError("synthetic_benchmark_callback_failed") from None
    return {"result_category": "SYNTHETIC RESULT" if execution_context is None else "RESEARCH RESULT", "boundary": "trusted_model_only_predict_callback",
            "warmup": warmup, "repetitions": repetitions, "batch_size": batch_size,
            "thread_reference": thread_reference, "thread_configuration_authenticated": False,
            "p50_batch_ms": _quantile(latencies, .5) * 1000,
            "p95_batch_ms": _quantile(latencies, .95) * 1000,
            "throughput_artifacts_per_second": batch_size * repetitions / sum(latencies),
            "timed_batch_seconds": latencies,
            "measured_memory_bytes_max": max(memory) if memory else None,
            "memory_probe_scope": "caller_supplied_not_authenticated" if memory else "unavailable",
            "serialized_model_bytes": serialized_model_bytes,
            "selection_performed": False}


def process_working_set_bytes():
    """Observed process working set, not isolated model memory or peak training."""
    import os
    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (n, ctypes.c_size_t) for n in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
            "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")]
    kernel, psapi = ctypes.windll.kernel32, ctypes.windll.psapi
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = (wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD)
    value = Counters(); value.cb = ctypes.sizeof(value)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(value), value.cb):
        return None
    return int(value.WorkingSetSize)


def benchmark_research_model(classifier, rows, *, execution_context, settings, serialized_model_bytes):
    """Genuine estimator only, after fitted preprocessing; batch size one for p95."""
    from ml.preflight import require_research_fitting
    from ml.classifier_adapters import FoldClassifier
    require_research_fitting(execution_context)
    if (not isinstance(classifier, FoldClassifier) or classifier.pipeline is None
            or settings != execution_context.selection_record["benchmark"]
            or type(rows) is not tuple or len(rows) != 1
            or set(settings) != {"warmup", "repetitions", "batch_size", "thread_reference", "hardware_reference", "payload_class", "cold_warm"}
            or settings["batch_size"] != 1 or settings["cold_warm"] != "warm"
            or any(type(settings[k]) is not str or not settings[k].strip() for k in ("hardware_reference", "payload_class"))):
        raise InputContractError("frozen_single_artifact_benchmark_required")
    # Both conversions occur before the first measured estimator invocation.
    ready = classifier.pipeline.named_steps["preprocess"].transform(classifier._matrix(rows))
    estimator = classifier.pipeline.named_steps["classifier"]
    def predict(_):
        return tuple(float(v) for v in (estimator.decision_function(ready) if classifier.model.family == "linear_svm" else estimator.predict_proba(ready)[:, 1]))
    memory_available = process_working_set_bytes() is not None
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        result = _benchmark_inference(predict, ((0.,),), warmup=settings["warmup"], repetitions=settings["repetitions"],
            batch_size=1, thread_reference=settings["thread_reference"], serialized_model_bytes=serialized_model_bytes,
            memory_probe=process_working_set_bytes if memory_available else None, execution_context=execution_context)
    from ml.metadata import fingerprint
    from ml.development_runner import environment_record
    result.update(authorization_sha256=execution_context.authorization_sha256,
        comparison_fingerprint=fingerprint({"settings": settings, "environment": environment_record()}),
        hardware_reference=settings["hardware_reference"], payload_class=settings["payload_class"], cold_warm="warm",
        thread_configuration_authenticated=True, memory_probe_scope="process_working_set_not_model_increment" if memory_available else "unavailable",
        p50_model_ms_per_artifact=result["p50_batch_ms"], p95_model_ms_per_artifact=result["p95_batch_ms"],
        timing_excludes=["parsing", "features", "fitted_transform", "calibration", "attribution", "API", "rendering"])
    return result

