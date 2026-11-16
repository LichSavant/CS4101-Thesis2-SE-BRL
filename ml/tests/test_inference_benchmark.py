"""Deterministic-clock synthetic benchmark checks; no workstation speed claims."""
import pytest
from ml.inference_benchmark import benchmark_synthetic_inference
from ml.experiment_inputs import InputContractError


def test_exact_timing_warmup_and_throughput_without_per_artifact_tail_claim():
    calls = []
    clock = iter((0, .01, .01, .03, .03, .06))
    memory = iter((100, 120, 110))
    def predict(rows):
        calls.append(rows)
        return (.2, .8)
    r = benchmark_synthetic_inference(predict, ((0, 1), (1, 0)), warmup=2,
        repetitions=3, batch_size=2, thread_reference="synthetic-single-thread",
        timer=lambda: next(clock), memory_probe=lambda: next(memory), serialized_model_bytes=10)
    assert len(calls) == 5
    assert r["p50_batch_ms"] == pytest.approx(20)
    assert r["p95_batch_ms"] == pytest.approx(29)
    assert r["throughput_artifacts_per_second"] == pytest.approx(100)
    assert r["measured_memory_bytes_max"] == 120 and r["serialized_model_bytes"] == 10
    assert r["result_category"] == "SYNTHETIC RESULT" and not r["selection_performed"]


def test_missing_resource_measurements_stay_unavailable():
    clock = iter((0, .01))
    r = benchmark_synthetic_inference(lambda x: (.5,), ((1,),), warmup=0,
        repetitions=1, batch_size=1, thread_reference="synthetic", timer=lambda: next(clock))
    assert r["measured_memory_bytes_max"] is None and r["serialized_model_bytes"] is None


@pytest.mark.parametrize("change", [
    {"warmup": -1}, {"warmup": True}, {"repetitions": 0}, {"batch_size": 2},
    {"thread_reference": ""}, {"serialized_model_bytes": -1}, {"serialized_model_bytes": True},
    {"rows": ((float("nan"),),)}, {"rows": ((None,),)}, {"rows": ((),)},
])
def test_invalid_benchmark_configuration_fails_without_prediction(change):
    settings = dict(rows=((1,),), warmup=0, repetitions=1, batch_size=1, thread_reference="synthetic")
    settings.update(change)
    with pytest.raises(InputContractError):
        benchmark_synthetic_inference(lambda x: pytest.fail("invalid benchmark called predictor"), **settings)


@pytest.mark.parametrize("clock", [(0, 0), (1, 0), (0, float("inf"))])
def test_nonpositive_or_invalid_duration_is_rejected(clock):
    values = iter(clock)
    with pytest.raises(InputContractError):
        benchmark_synthetic_inference(lambda x: (.5,), ((1,),), warmup=0,
            repetitions=1, batch_size=1, thread_reference="synthetic", timer=lambda: next(values))


def test_callback_error_is_sanitized():
    def broken(rows): raise RuntimeError("SENSITIVE SYNTHETIC CONTENT")
    with pytest.raises(InputContractError, match="^synthetic_benchmark_callback_failed$") as error:
        benchmark_synthetic_inference(broken, ((1,),), warmup=0, repetitions=1,
                                     batch_size=1, thread_reference="synthetic")
    assert error.value.__suppress_context__

