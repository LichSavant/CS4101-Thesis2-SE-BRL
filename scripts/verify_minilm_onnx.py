"""Offline FP32 export/comparison; synthetic engineering only, no quantization.

Run export, compare, and each backend's benchmark in separate fresh processes.
All model artifacts and temporary outputs stay inside the ignored tooling venv.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
from importlib.metadata import distributions
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.dont_write_bytecode = True
LOCAL = ROOT / ".venv-transformer"
TOOL = LOCAL / "onnx-tooling"
CACHE = LOCAL / "model-cache/hub"
ARTIFACT = TOOL / "minilm-fp32.onnx"
TOL = {"logits_atol": 1e-4, "logits_rtol": 1e-3, "probabilities_max_absolute_error": 1e-4,
       "token_ids_and_attention_masks": "exact", "nli_decisions_and_review_outcomes": "exact; zero discrepancies"}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def setup():
    # Platform metadata may use a Windows subprocess; collect before the guard.
    host = {"python": platform.python_version(), "platform": platform.platform(),
            "processor": os.environ.get("PROCESSOR_IDENTIFIER"), "threads": 2, "interop_threads": 1}
    tmp = TOOL / "tmp"
    tmp.mkdir(exist_ok=True)
    tempfile.tempdir = str(tmp)
    os.environ.update(HF_HOME=str(CACHE.parent), HF_HUB_CACHE=str(CACHE), HUGGINGFACE_HUB_CACHE=str(CACHE),
                      HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
                      HF_HUB_DISABLE_IMPLICIT_TOKEN="1", TOKENIZERS_PARALLELISM="false",
                      TEMP=str(tmp), TMP=str(tmp), TMPDIR=str(tmp), TORCH_HOME=str(tmp / "torch"))
    blocked = []

    def audit(event, args):
        if event.startswith("socket.") and event not in {"socket.__new__", "socket.gethostname"}:
            # Deny all network operations, including urllib3's optional local IPv6 probe.
            blocked.append(event)
            raise RuntimeError("offline_network_denied")
        if event in {"subprocess.Popen", "os.system"}:
            raise RuntimeError("offline_subprocess_denied")
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            mode, flags = args[1:3]
            write = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)))
            if write and not path.is_relative_to(TOOL):
                raise RuntimeError("write_outside_onnx_tooling_denied")
            if (path.suffix.lower() in {".csv", ".arff", ".parquet", ".xlsx", ".ipynb", ".jsonl"}
                    or any(s in path.as_posix().lower() for s in (
                        "/datasets-raw/", "/experiments/data/", "/experiments/results/", "/sealed"))):
                raise RuntimeError("research_input_denied")

    sys.addaudithook(audit)
    from verify_pinned_minilm import verify_snapshot
    from ml.se_brl.semantic_candidates import MODEL_ID, MODEL_REVISION, semantic_configuration
    manifest = json.loads((ROOT / "tools/verification/pinned-minilm-files.json").read_text())
    assert manifest["repository"] == MODEL_ID and manifest["revision"] == MODEL_REVISION
    verified = verify_snapshot(CACHE, manifest)
    spec, _ = semantic_configuration()
    assert json.loads((TOOL / "preflight.json").read_text())["tolerances_declared_before_any_comparison"] == TOL
    info = {"source_revision": MODEL_REVISION, "source_repository": MODEL_ID, "source_files": verified,
            "hypotheses_sha256": spec["hypotheses_sha256"], "tolerances": TOL, "host": host,
            "versions": {d.metadata["Name"]: d.version for d in distributions()},
            "verification_kind": "synthetic_engineering_only", "network_denied": True,
            "research_inputs_permitted": False, "training_or_calibration": False,
            "scientific_release": False, "verifier_sha256": sha(__file__)}
    return info, blocked


def tokenizer():
    from transformers import AutoTokenizer
    from ml.se_brl.semantic_candidates import MODEL_ID, MODEL_REVISION
    return AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION, local_files_only=True)


def canonical():
    import torch
    from ml.se_brl.semantic_candidates import PinnedLocalNliScorer
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    return PinnedLocalNliScorer()


class OrtScorer:
    def __init__(self):
        import onnxruntime as ort
        from ml.se_brl.semantic_candidates import semantic_configuration
        self.spec, self.hypotheses = semantic_configuration()
        self.tokenizer = tokenizer()
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.session = ort.InferenceSession(str(ARTIFACT), sess_options=options, providers=["CPUExecutionProvider"])
        assert self.session.get_providers() == ["CPUExecutionProvider"]
        self.last_tokens = self.last_logits = None
        self.forward_calls = 0

    def score(self, text, indicator):
        import numpy as np
        from ml.se_brl.semantic_candidates import SemanticInferenceUnavailable, validate_scores
        tokens = self.tokenizer([text] * 3, self.hypotheses[indicator], truncation=False, padding=True, return_tensors="np")
        self.last_tokens = {key: tokens[key].astype(np.int64, copy=False) for key in ("input_ids", "attention_mask")}
        if tokens["input_ids"].shape[1] > 512:
            raise SemanticInferenceUnavailable("Evidence exceeds token limit; abstain without truncation")
        self.last_logits = self.session.run(["logits"], self.last_tokens)[0]
        self.forward_calls += 1
        values = np.exp(self.last_logits - self.last_logits.max(axis=-1, keepdims=True))
        values /= values.sum(axis=-1, keepdims=True)
        # Immutable source config: 0 contradiction, 1 entailment, 2 neutral.
        return validate_scores([{label: float(row[i]) for label, i in (
            ("contradiction", 0), ("entailment", 1), ("neutral", 2))} for row in values])


def export(info):
    import torch
    import onnx
    model = canonical()
    assert model.indices == {"contradiction": 0, "entailment": 1, "neutral": 2}
    assert all(p.dtype == torch.float32 and p.device.type == "cpu" for p in model.model.parameters())

    class Logits(torch.nn.Module):
        def __init__(self, wrapped):
            super().__init__()
            self.wrapped = wrapped
        def forward(self, input_ids, attention_mask):
            return self.wrapped(input_ids=input_ids, attention_mask=attention_mask).logits

    sample = model.tokenizer(["Synthetic compatibility check."] * 3, model.hypotheses["urgency"],
                             truncation=False, padding=True, return_tensors="pt")
    started = time.perf_counter()
    with torch.inference_mode():
        torch.onnx.export(Logits(model.model).eval(), (sample["input_ids"], sample["attention_mask"]),
                          str(ARTIFACT), input_names=["input_ids", "attention_mask"], output_names=["logits"],
                          dynamic_axes={"input_ids": {1: "sequence"}, "attention_mask": {1: "sequence"}},
                          opset_version=17, dynamo=False, external_data=False)
    graph = onnx.load(str(ARTIFACT))
    onnx.checker.check_model(graph, full_check=True)
    assert [(o.domain, o.version) for o in graph.opset_import] == [("", 17)]
    assert all(n.domain in {"", "ai.onnx"} for n in graph.graph.node)
    assert all(t.data_type not in {onnx.TensorProto.FLOAT16, onnx.TensorProto.BFLOAT16, onnx.TensorProto.DOUBLE}
               for t in graph.graph.initializer)
    assert [x.name for x in graph.graph.input] == ["input_ids", "attention_mask"]
    assert all(x.type.tensor_type.elem_type == onnx.TensorProto.INT64 for x in graph.graph.input)
    assert len(graph.graph.output) == 1 and graph.graph.output[0].type.tensor_type.elem_type == onnx.TensorProto.FLOAT
    info.update(status="PASS", export_seconds=time.perf_counter() - started,
                onnx_sha256=sha(ARTIFACT), onnx_bytes=ARTIFACT.stat().st_size,
                operators=dict(Counter(n.op_type for n in graph.graph.node)), opset=17,
                exporter="torch.onnx.export(dynamo=False)", model_training=model.model.training)
    assert model.model.training is False
    return info


def frozen_cases():
    from ml.tests.test_semantic_review import EXAMPLES, source
    from ml.datasets import DatasetRecord
    from ml.se_brl.detectors import DetectorContext
    cases = [(i, *source(text)) for i, text in EXAMPLES.items()]
    for name, text in (("negation", "Never submit your password."),
                       ("quotation", 'The poster says "Submit your password."'),
                       ("hypothetical", "Hypothetical: Submit your password."),
                       ("unicode", "\U0001f9ea Caf\u00e9 e\u0301: Submit your password.")):
        cases.append((name, *source(text)))
    record, _ = source("Click here.")
    cases.append(("identity_unavailable", record, DetectorContext()))
    for kind, modality, fields in (("url", "standalone_url", {"url": "https://example.test/"}),
                                   ("technical", "engineered_technical_record", {}),
                                   ("email", "content_bearing_email", {})):
        cases.append(("missing_" + kind, DatasetRecord("synthetic:missing", "synthetic-engineering", modality,
                     {"kind": kind, **fields}, tuple(fields), None, {"reference": "synthetic-only"}), None))
    return cases


def normalize(report):
    value = deepcopy(report)
    for row in value["indicators"]:
        for candidate in row["semantic_candidates"]:
            candidate["scores"] = "numerically_compared_separately"
    return value


def compare(info):
    import numpy as np
    from ml.se_brl.semantic_candidates import LABELS, SemanticInferenceUnavailable
    from ml.se_brl.semantic_review import review_record, validate_review, predictor_values, ReviewContractError
    from ml.tests.test_semantic_review import source
    pt, ort = canonical(), OrtScorer()
    recordings, failures, cases = {}, [], []
    stats = {"logits": [], "probabilities": []}
    exact_tokens = exact_decisions = 0

    def capture(module, args, kwargs, output):
        pt.last_tokens = {k: v.detach().cpu().numpy().copy() for k, v in kwargs.items()}
        pt.last_logits = output.logits.detach().cpu().numpy().copy()

    hook = pt.model.register_forward_hook(capture, with_kwargs=True)

    class Record:
        def score(self, text, indicator):
            scores = pt.score(text, indicator)
            recordings[text, indicator] = (deepcopy(pt.last_tokens), pt.last_logits.copy(), scores)
            return scores

    class Compare:
        def score(self, text, indicator):
            nonlocal exact_tokens, exact_decisions
            result = ort.score(text, indicator)
            tokens, logits, scores = recordings[text, indicator]
            token_equal = all(np.array_equal(tokens[k], ort.last_tokens[k]) for k in ("input_ids", "attention_mask"))
            exact_tokens += int(token_equal)
            if not token_equal:
                failures.append("tokens_or_masks")
            delta = np.abs(logits.astype(np.float64) - ort.last_logits.astype(np.float64))
            stats["logits"].extend(delta.ravel().tolist())
            if not np.allclose(ort.last_logits, logits, atol=TOL["logits_atol"], rtol=TOL["logits_rtol"]):
                failures.append("logits_tolerance")
            left = np.array([[r[k] for k in LABELS] for r in scores])
            right = np.array([[r[k] for k in LABELS] for r in result])
            delta = np.abs(left - right)
            stats["probabilities"].extend(delta.ravel().tolist())
            if delta.max() > TOL["probabilities_max_absolute_error"]:
                failures.append("probabilities_tolerance")
            decisions_equal = np.array_equal(left == left.max(axis=-1, keepdims=True), right == right.max(axis=-1, keepdims=True))
            exact_decisions += int(decisions_equal)
            if not decisions_equal:
                failures.append("nli_decision_or_tie")
            return result

    record_scorer, compare_scorer = Record(), Compare()
    frozen = frozen_cases()
    fixture_bytes = json.dumps([{ "name": n, "artifact": dict(r.artifact_input), "modality": r.modality}
                               for n, r, _ in frozen], sort_keys=True, ensure_ascii=False).encode()
    info["frozen_fixture_sha256"] = hashlib.sha256(fixture_bytes).hexdigest()
    info["fixture_source_sha256"] = sha(ROOT / "ml/tests/test_semantic_review.py")
    (TOOL / "frozen-synthetic-inputs.json").write_bytes(fixture_bytes)
    real_calls = 0
    for name, record, context in frozen:
        baseline = review_record(record, detector_context=context).to_dict()
        left = review_record(record, scorer=record_scorer, detector_context=context).to_dict()
        right = review_record(record, scorer=compare_scorer, detector_context=context).to_dict()
        validate_review(left, record, detector_context=context)
        validate_review(right, record, detector_context=context)
        equal = normalize(left) == normalize(right)
        if not equal:
            failures.append("review_outcome:" + name)
        for old, row in zip(baseline["indicators"], right["indicators"], strict=True):
            assert old["deterministic_state"] == row["deterministic_state"] and old["evidence"] == row["evidence"]
            assert row["candidate_state"] in {"abstained", "unavailable"} and not row["failure_codes"]
        assert right["learned_values"] == [None] * 4 and not any(right["research_release"].values())
        if name.startswith("missing_"):
            assert all(r["candidate_state"] == "unavailable" for r in right["indicators"])
        cases.append({"name": name, "equal": equal})
        print("COMPARE", name, equal, flush=True)
        real_calls = ort.forward_calls

    # Exercise the exact limit with real tokenization and real model execution.
    boundary_text = None
    for words in range(450, 513):
        text = "synthetic " * words
        ids = ort.tokenizer([text] * 3, ort.hypotheses["urgency"], padding=True, truncation=False, return_tensors="np")["input_ids"]
        if ids.shape[1] == 512:
            boundary_text = text
            break
    assert boundary_text is not None
    record_scorer.score(boundary_text, "urgency")
    compare_scorer.score(boundary_text, "urgency")
    cases.append({"name": "exact_512_tokens", "equal": True})
    for scorer in (pt, ort):
        before = ort.forward_calls
        try:
            scorer.score(boundary_text + "synthetic ", "urgency")
        except SemanticInferenceUnavailable as error:
            assert "token limit" in str(error)
        else:
            raise AssertionError("Oversized input was executed")
        assert ort.forward_calls == before
    cases.append({"name": "513_tokens_abstain", "equal": True})

    # Replay already compared real scores to test the actual 64-unit/512-call
    # controller limits without executing hundreds of redundant forwards.
    class Replay:
        def __init__(self, backend):
            self.backend, self.calls = backend, 0
        def score(self, text, indicator):
            self.calls += 1
            return recordings[text, indicator][2]
    record, context = source("Act now. " * 65)
    replay_a, replay_b = Replay("torch"), Replay("onnx")
    # ONNX replay must contain its own scores, not canonical substitutes.
    onnx_replay = {}
    for text, indicator in recordings:
        if text in {"We are Contoso.", "Act now."}:
            onnx_replay[text, indicator] = ort.score(text, indicator)
    replay_b.score = lambda text, indicator: onnx_replay[text, indicator]
    a = review_record(record, scorer=replay_a, detector_context=context).to_dict()
    b = review_record(record, scorer=replay_b, detector_context=context).to_dict()
    assert replay_a.calls == 512 and normalize(a) == normalize(b)
    assert any("semantic_budget_exhausted" in r["failure_codes"] for r in b["indicators"])
    cases.append({"name": "64_unit_512_call_budget_real_score_replay", "equal": True})
    record, context = source("Act now.")
    valid = review_record(record, scorer=record_scorer, detector_context=context).to_dict()
    for mutation in (lambda r: r["indicators"][0]["semantic_candidates"][0]["evidence"].update(start=True),
                     lambda r: r["indicators"][0].update(candidate_state="supported")):
        invalid = deepcopy(valid)
        mutation(invalid)
        try:
            validate_review(invalid, record, detector_context=context)
        except ValueError:
            pass
        else:
            raise AssertionError("Malformed evidence or promotion accepted")
    class Bad:
        def score(self, *args):
            return [{"entailment": float("nan"), "neutral": 0, "contradiction": 0}] * 3
    bad = review_record(record, scorer=Bad(), detector_context=context).to_dict()
    assert all(not r["semantic_candidates"] for r in bad["indicators"])
    try:
        predictor_values(valid)
    except ReviewContractError:
        pass
    else:
        raise AssertionError("Predictor export gate opened")
    cases.append({"name": "malformed_scores_evidence_promotion_and_export_rejected", "equal": True})
    hook.remove()
    info.update(status="FAIL" if failures else "PASS", failures=dict(Counter(failures)), cases=cases,
                cases_passed=sum(c["equal"] for c in cases), cases_failed=sum(not c["equal"] for c in cases),
                real_review_calls_per_backend=real_calls, exact_token_mask_comparisons=exact_tokens,
                exact_nli_decision_comparisons=exact_decisions, onnx_sha256=sha(ARTIFACT),
                deviations={k: {"max_absolute": max(v), "mean_absolute": statistics.mean(v), "values": len(v)}
                            for k, v in stats.items()},
                deterministic_authority_preserved=True, research_gates_closed=True,
                fixture_boundary_sha256=hashlib.sha256(boundary_text.encode()).hexdigest())
    return info


def benchmark(info, backend):
    from verify_pinned_minilm import process_memory
    # Warm dependency imports and metadata checks before timing model loading.
    import torch
    import onnxruntime
    tokenizer()
    before = process_memory()
    started = time.perf_counter()
    scorer = canonical() if backend == "torch" else OrtScorer()
    load = time.perf_counter() - started
    from ml.tests.test_semantic_review import EXAMPLES
    samples = list(EXAMPLES.items())
    scorer.score(samples[0][1], samples[0][0])  # One excluded warm-up.
    elapsed = []
    for _ in range(3):
        for indicator, text in samples:
            started = time.perf_counter()
            scorer.score(text, indicator)
            elapsed.append(time.perf_counter() - started)
    ordered = sorted(elapsed)
    info.update(status="PASS", backend=backend, load_seconds_excluding_imports=load,
                file_cache="may be warm; integrity hashing precedes load", samples=len(elapsed),
                scorer_latency_seconds={"median": statistics.median(elapsed), "p95": ordered[34],
                                        "mean": statistics.mean(elapsed)},
                memory_before_load_bytes=before, memory_peak_and_final_bytes=process_memory(),
                memory_scope="whole fresh process including identical dependency imports; native allocations included",
                onnx_sha256=sha(ARTIFACT), onnx_bytes=ARTIFACT.stat().st_size,
                canonical_weight_bytes=328499560, benchmark_fixture_sha256=hashlib.sha256(
                    json.dumps(samples).encode()).hexdigest())
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("export", "compare", "benchmark"))
    parser.add_argument("--backend", choices=("torch", "onnx"), default="onnx")
    args = parser.parse_args()
    info, blocked = setup()
    if args.mode == "export":
        info = export(info)
    else:
        exported = json.loads((TOOL / "export-result.json").read_text())
        assert sha(ARTIFACT) == exported["onnx_sha256"], "Export artifact integrity mismatch"
        info = compare(info) if args.mode == "compare" else benchmark(info, args.backend)
    assert all(event == "socket.bind" for event in blocked), blocked
    info["denied_optional_loopback_probes"] = blocked
    info["command"] = [".venv-transformer/onnx-tooling/Scripts/python", "-B", "scripts/verify_minilm_onnx.py", *sys.argv[1:]]
    name = args.mode + ("-" + args.backend if args.mode == "benchmark" else "") + "-result.json"
    (TOOL / name).write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    print("RESULT", name, info["status"], flush=True)
    if info["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
