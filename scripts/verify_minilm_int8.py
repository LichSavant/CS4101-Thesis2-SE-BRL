"""One controlled dynamic INT8 candidate; offline synthetic engineering only.

Reuses the unchanged Phase 3 fixtures, tokenization, review and benchmark tools.
INT8 acceptance is exact decision/contract parity, not FP32 numeric tolerance.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import statistics
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
import verify_minilm_onnx as fp

INT8 = fp.TOOL / "minilm-linear-int8.onnx"
POLICY = ROOT / "tools/verification/minilm-int8-policy.json"


def setup():
    info, blocked = fp.setup()
    provenance = json.loads((ROOT / "docs/research/minilm-onnx-verification.json").read_text(encoding="utf-8"))
    assert fp.sha(fp.ARTIFACT) == provenance["export"]["onnx_sha256"]
    assert fp.sha(ROOT / "scripts/verify_minilm_onnx.py") == provenance["verifier_sha256"]
    for filename in ("requirements-transformer.txt", "requirements-onnx.txt"):
        for line in (ROOT / "tools/verification" / filename).read_text().splitlines():
            if "==" in line and not line.startswith("#"):
                name, expected = line.split("==")
                assert version(name) == expected, name
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    # The committed policy is read before generation or any comparative inference.
    info.pop("tolerances")
    info.update(base_commit="4e74da4", acceptance_policy=policy, acceptance_policy_sha256=fp.sha(POLICY),
                source_fp32_sha256=fp.sha(fp.ARTIFACT), verifier_sha256=fp.sha(__file__),
                phase3_verifier_sha256=provenance["verifier_sha256"], candidate_status="experimental")
    return info, blocked


def generate(info):
    import onnx
    from onnxruntime.quantization import quantize_dynamic, QuantType
    source = onnx.load(str(fp.ARTIFACT))
    initializers = {t.name: t for t in source.graph.initializer}
    selected = [n for n in source.graph.node if n.op_type == "MatMul" and n.input[1] in initializers
                and initializers[n.input[1]].data_type == onnx.TensorProto.FLOAT
                and len(initializers[n.input[1]].dims) == 2]
    assert selected and len({n.name for n in selected}) == len(selected)
    settings = info["acceptance_policy"]["quantization"]
    started = time.perf_counter()
    quantize_dynamic(str(fp.ARTIFACT), str(INT8), op_types_to_quantize=settings["op_types_to_quantize"],
                     nodes_to_quantize=[n.name for n in selected],
                     per_channel=settings["per_channel"], reduce_range=settings["reduce_range"],
                     weight_type=QuantType.QInt8, use_external_data_format=False,
                     extra_options=settings["extra_options"])
    graph = onnx.load(str(INT8))
    # ORT 1.20 normalizes every Gemm before applying the quantization allowlist.
    # Restore excluded classifier nodes/tensors exactly from the source so this
    # candidate changes only the explicitly selected linear MatMuls.
    gemms = [node for node in source.graph.node if node.op_type == "Gemm"]
    replacements = {node.name + "_MatMul": node for node in gemms}
    removed_adds = {node.name + "_Add" for node in gemms}
    removed_values = {node.output[0] + "_MatMul" for node in gemms}
    restored_weights = {node.input[1] for node in gemms}
    nodes = []
    restored = []
    for node in graph.graph.node:
        if node.name in replacements:
            original = replacements[node.name]
            nodes.append(deepcopy(original))
            restored.append(original.name)
        elif node.name not in removed_adds:
            nodes.append(deepcopy(node))
    assert set(restored) == {node.name for node in gemms}
    graph.graph.ClearField("node")
    graph.graph.node.extend(nodes)
    for tensor in graph.graph.initializer:
        if tensor.name in restored_weights:
            tensor.CopyFrom(initializers[tensor.name])
    values = [deepcopy(v) for v in graph.graph.value_info if v.name not in removed_values | restored_weights]
    graph.graph.ClearField("value_info")
    graph.graph.value_info.extend(values)
    # Shape inference may replace symbolic output dimensions with inferred
    # values. Preserve the exact source-facing output declaration as well.
    graph.graph.ClearField("output")
    graph.graph.output.extend(deepcopy(source.graph.output))
    onnx.save_model(graph, str(INT8))
    onnx.checker.check_model(graph, full_check=True)
    assert fp.sha(fp.ARTIFACT) == info["source_fp32_sha256"]
    output_tensors = {t.name: t for t in graph.graph.initializer}
    changed = {n.input[1] for n in selected}
    # Byte-exact validation of every unselected initializer, including all
    # embedding tables, normalization/bias tensors and classifier weights.
    preserved = 0
    for name, tensor in initializers.items():
        if name not in changed:
            assert name in output_tensors
            output = output_tensors[name]
            # ORT explicitly writes data_location=DEFAULT. That metadata change
            # is not a weight change: require identical type, shape and all data.
            assert tensor.data_type == output.data_type and list(tensor.dims) == list(output.dims), name
            assert tensor.raw_data == output.raw_data, name
            for field in ("float_data", "int32_data", "int64_data", "double_data", "uint64_data", "string_data"):
                assert list(getattr(tensor, field)) == list(getattr(output, field)), (name, field)
            preserved += 1
    operators = Counter(n.op_type for n in graph.graph.node)
    assert operators["MatMulInteger"] == len(selected)
    assert all(n.domain in {"", "ai.onnx"} for n in graph.graph.node)
    assert [x.SerializeToString() for x in source.graph.input] == [x.SerializeToString() for x in graph.graph.input]
    assert [x.SerializeToString() for x in source.graph.output] == [x.SerializeToString() for x in graph.graph.output]
    assert all(t.data_location != onnx.TensorProto.EXTERNAL for t in graph.graph.initializer)
    info.update(status="PASS", generation_seconds=time.perf_counter() - started,
                int8_sha256=fp.sha(INT8), int8_bytes=INT8.stat().st_size,
                selected_linear_nodes=[n.name for n in selected], quantized_linear_nodes=len(selected),
                unselected_initializer_data_byte_exact=preserved, operators=dict(operators), graph_validated=True,
                excluded_classifier_gemm_nodes_restored_from_source=restored)
    return info


def scorer(path):
    # Change only the test tool's artifact selector while constructing a session.
    original = fp.ARTIFACT
    try:
        fp.ARTIFACT = path
        return fp.OrtScorer()
    finally:
        fp.ARTIFACT = original


def compare(info):
    import numpy as np
    from ml.se_brl.semantic_candidates import LABELS, SemanticInferenceUnavailable
    from ml.se_brl.semantic_review import review_record, validate_review, predictor_values, ReviewContractError
    from ml.tests.test_semantic_review import source
    pt, f32, q8 = fp.canonical(), scorer(fp.ARTIFACT), scorer(INT8)
    cached = {name: {} for name in ("pytorch", "fp32", "int8")}
    comparisons, disagreements, cases = [], [], []

    def capture(module, args, kwargs, output):
        pt.last_tokens = {k: v.detach().cpu().numpy().copy() for k, v in kwargs.items()}
        pt.last_logits = output.logits.detach().cpu().numpy().copy()
    hook = pt.model.register_forward_hook(capture, with_kwargs=True)

    class Record:
        def __init__(self, name, backend):
            self.name, self.backend = name, backend
        def score(self, text, indicator):
            result = self.backend.score(text, indicator)
            assert np.isfinite(self.backend.last_logits).all()
            cached[self.name][text, indicator] = (
                deepcopy(self.backend.last_tokens), self.backend.last_logits.copy(), deepcopy(result))
            return result
    wrappers = [Record("pytorch", pt), Record("fp32", f32), Record("int8", q8)]

    def compare_calls(case_name, keys):
        all_equal = True
        for text, indicator in sorted(keys):
            q_tokens, q_logits, q_scores = cached["int8"][text, indicator]
            for name in ("pytorch", "fp32"):
                tokens, logits, scores = cached[name][text, indicator]
                token_equal = all(np.array_equal(tokens[k], q_tokens[k]) for k in ("input_ids", "attention_mask"))
                assert token_equal, "Quantization changed tokens/masks"
                left = np.array([[r[k] for k in LABELS] for r in scores])
                right = np.array([[r[k] for k in LABELS] for r in q_scores])
                maxima_a = left == left.max(axis=-1, keepdims=True)
                maxima_b = right == right.max(axis=-1, keepdims=True)
                delta_l = np.abs(logits.astype(np.float64) - q_logits.astype(np.float64))
                delta_p = np.abs(left - right)
                comparisons.append({"baseline": name, "logits": delta_l.ravel().tolist(),
                                    "probabilities": delta_p.ravel().tolist()})
                if not np.array_equal(maxima_a, maxima_b):
                    all_equal = False
                    disagreements.append({"case": case_name, "baseline": name, "indicator": indicator,
                        "synthetic_text": text, "type": "nli_maxima_or_tie",
                        "hypothesis_indices": np.where(np.any(maxima_a != maxima_b, axis=1))[0].tolist(),
                        "baseline_maxima": [[LABELS[i] for i in np.where(row)[0]] for row in maxima_a],
                        "int8_maxima": [[LABELS[i] for i in np.where(row)[0]] for row in maxima_b],
                        "baseline_probabilities": scores, "int8_probabilities": q_scores})
        return all_equal

    frozen = fp.frozen_cases()
    payload = json.dumps([{"name": n, "artifact": dict(r.artifact_input), "modality": r.modality}
                          for n, r, _ in frozen], sort_keys=True, ensure_ascii=False).encode()
    info["frozen_fixture_sha256"] = hashlib.sha256(payload).hexdigest()
    previous = json.loads((fp.TOOL / "compare-result.json").read_text(encoding="utf-8"))
    assert info["frozen_fixture_sha256"] == previous["frozen_fixture_sha256"]
    review_differences = 0
    for name, record, context in frozen:
        reports = [review_record(record, scorer=w, detector_context=context).to_dict() for w in wrappers]
        keys = {(c["evidence"]["text"], row["indicator_id"]) for row in reports[0]["indicators"]
                for c in row["semantic_candidates"]}
        for report in reports:
            validate_review(report, record, detector_context=context)
            assert report["learned_values"] == [None] * 4 and not any(report["research_release"].values())
            assert all(not row["failure_codes"] for row in report["indicators"])
        # Revalidate existing FP32 parity independently of the INT8 criteria.
        assert fp.normalize(reports[0]) == fp.normalize(reports[1])
        decision_equal = compare_calls(name, keys)
        for base_name, baseline in zip(("pytorch", "fp32"), reports[:2]):
            for old, new in zip(baseline["indicators"], reports[2]["indicators"], strict=True):
                for field in ("deterministic_state", "evidence", "evaluation_status", "candidate_state", "constraints"):
                    assert old[field] == new[field], (name, field)
                for field in ("needs_review", "review_reasons", "semantic_status", "failure_codes"):
                    if old[field] != new[field]:
                        review_differences += 1
                        disagreements.append({"case": name, "baseline": base_name, "indicator": old["indicator_id"],
                                              "type": "review_outcome", "field": field,
                                              "baseline_value": old[field], "int8_value": new[field]})
            if fp.normalize(baseline) != fp.normalize(reports[2]):
                decision_equal = False
        cases.append({"name": name, "decision_parity": decision_equal, "safeguards_preserved": True})
        print("INT8_COMPARE", name, decision_equal, flush=True)

    boundary = None
    for n in range(450, 513):
        text = "synthetic " * n
        tokens = q8.tokenizer([text] * 3, q8.hypotheses["urgency"], padding=True, truncation=False, return_tensors="np")
        if tokens["input_ids"].shape[1] == 512:
            boundary = text
            break
    assert boundary is not None
    for wrapper in wrappers:
        wrapper.score(boundary, "urgency")
    cases.append({"name": "exact_512_tokens", "decision_parity": compare_calls("exact_512_tokens", {(boundary, "urgency")}),
                  "safeguards_preserved": True})
    for backend in (pt, f32, q8):
        try:
            backend.score(boundary + "synthetic ", "urgency")
        except SemanticInferenceUnavailable as error:
            assert "token limit" in str(error)
        else:
            raise AssertionError("513-token input was executed")
    cases.append({"name": "513_tokens_abstain", "decision_parity": True, "safeguards_preserved": True})

    class Replay:
        def __init__(self, name):
            self.name, self.calls = name, 0
        def score(self, text, indicator):
            self.calls += 1
            return cached[self.name][text, indicator][2]
    record, context = source("Act now. " * 65)
    replays = [Replay(name) for name in cached]
    reports = [review_record(record, scorer=w, detector_context=context).to_dict() for w in replays]
    assert all(r.calls == 512 for r in replays)
    equal = all(fp.normalize(r) == fp.normalize(reports[2]) for r in reports[:2])
    if not equal:
        for baseline_name, baseline in zip(("pytorch", "fp32"), reports[:2]):
            for old, new in zip(baseline["indicators"], reports[2]["indicators"], strict=True):
                for field in ("needs_review", "review_reasons", "semantic_status", "failure_codes"):
                    if old[field] != new[field]:
                        disagreements.append({"case": "budget_replay", "baseline": baseline_name,
                            "indicator": old["indicator_id"], "type": "review_outcome", "field": field,
                            "baseline_value": old[field], "int8_value": new[field]})
    cases.append({"name": "64_unit_512_call_budget_replay", "decision_parity": equal, "safeguards_preserved": True})
    for report in reports:
        assert any("semantic_budget_exhausted" in row["failure_codes"] for row in report["indicators"])
    record, context = source("Act now.")
    for wrapper in wrappers:
        valid = review_record(record, scorer=wrapper, detector_context=context).to_dict()
        for field, value in (("start", True), ("start", -1)):
            invalid = deepcopy(valid)
            invalid["indicators"][0]["semantic_candidates"][0]["evidence"][field] = value
            try:
                validate_review(invalid, record, detector_context=context)
            except ValueError:
                pass
            else:
                raise AssertionError("Malformed evidence accepted")
        try:
            predictor_values(valid)
        except ReviewContractError:
            pass
        else:
            raise AssertionError("Scientific export gate opened")
    class Bad:
        def score(self, *args):
            return [{"entailment": float("nan"), "neutral": 0, "contradiction": 0}] * 3
    bad = review_record(record, scorer=Bad(), detector_context=context).to_dict()
    assert all(not row["semantic_candidates"] and "semantic_failed" in row["failure_codes"]
               for row in bad["indicators"] if row["candidate_state"] != "unavailable")
    cases.append({"name": "malformed_inputs_and_export_gate", "decision_parity": True, "safeguards_preserved": True})
    hook.remove()
    deviations = {}
    for baseline in ("pytorch", "fp32"):
        deviations[baseline] = {}
        for metric in ("logits", "probabilities"):
            values = [v for c in comparisons if c["baseline"] == baseline for v in c[metric]]
            deviations[baseline][metric] = {"max_absolute": max(values), "mean_absolute": statistics.mean(values),
                                            "values": len(values)}
    failed = sum(not c["decision_parity"] for c in cases)
    info.update(status="FAIL" if failed else "PASS", cases=cases, cases_passed=len(cases) - failed,
                cases_failed=failed, safeguards_cases_passed=len(cases), disagreements=disagreements,
                review_field_differences=review_differences, deviations=deviations,
                numeric_thresholds_applied=False, compared_unique_calls_per_baseline=len(comparisons) // 2,
                int8_sha256=fp.sha(INT8), int8_bytes=INT8.stat().st_size)
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("generate", "compare", "benchmark"))
    parser.add_argument("--backend", choices=("torch", "fp32", "int8"), default="int8")
    args = parser.parse_args()
    info, blocked = setup()
    if args.mode == "generate":
        info = generate(info)
    else:
        generated = json.loads((fp.TOOL / "int8-generate-result.json").read_text(encoding="utf-8"))
        assert generated["status"] == "PASS" and generated["int8_sha256"] == fp.sha(INT8)
        if args.mode == "compare":
            info = compare(info)
        else:
            if args.backend == "int8":
                fp.ARTIFACT = INT8
            info = fp.benchmark(info, args.backend)
    assert all(event == "socket.bind" for event in blocked), blocked
    info["denied_optional_loopback_probes"] = blocked
    assert fp.sha(fp.TOOL / "minilm-fp32.onnx") == info["source_fp32_sha256"]
    info["command"] = [".venv-transformer/onnx-tooling/Scripts/python", "-B", "scripts/verify_minilm_int8.py", *sys.argv[1:]]
    name = "int8-" + args.mode + ("-" + args.backend if args.mode == "benchmark" else "") + "-result.json"
    (fp.TOOL / name).write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    print("RESULT", name, info["status"], flush=True)
    if info["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
