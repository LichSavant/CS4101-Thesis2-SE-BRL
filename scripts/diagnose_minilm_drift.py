"""Bounded drift diagnosis; isolated artifacts, no scientific-policy changes.

Maximum three predeclared candidates. Diagnostics use at most three already
frozen mismatches, and never grant scientific release or deployment authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import gc
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

sys.dont_write_bytecode = True
os.environ.update(OPENBLAS_NUM_THREADS="2", OMP_NUM_THREADS="2", MKL_NUM_THREADS="2")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import verify_minilm_int8 as prior
fp = prior.fp
BUDGET = ROOT / "tools/verification/minilm-drift-budget.json"
DIRECTORY = fp.TOOL / "drift-diagnosis"


def setup():
    info, blocked = prior.setup()
    old = json.loads((ROOT / "docs/research/minilm-int8-verification.json").read_text(encoding="utf-8"))
    assert fp.sha(prior.INT8) == old["generation"]["int8_sha256"]
    assert fp.sha(ROOT / "scripts/verify_minilm_int8.py") == old["verifier_sha256"]
    plan = json.loads(BUDGET.read_text(encoding="utf-8"))
    DIRECTORY.mkdir(exist_ok=True)
    info.update(base_commit="c95d33a", phase4_verifier_sha256=old["verifier_sha256"],
                verifier_sha256=fp.sha(__file__), budget=plan, budget_sha256=fp.sha(BUDGET),
                original_int8_sha256=fp.sha(prior.INT8))
    return info, blocked, old


def diagnostic_records(old, plan):
    votes = []
    for record in old["disagreements"]:
        if record.get("baseline") != "fp32" or record["type"] != "nli_maxima_or_tie":
            continue
        for index in record["hypothesis_indices"]:
            left, right = record["baseline_probabilities"][index], record["int8_probabilities"][index]
            ranked = sorted(left.values(), reverse=True)
            votes.append({"case": record["case"], "text": record["synthetic_text"], "indicator": record["indicator"],
                          "hypothesis_index": index, "top_score": ranked[0], "margin": ranked[0] - ranked[1],
                          "drift": max(abs(left[k] - right[k]) for k in left),
                          "old_class": max(left, key=left.get), "new_class": max(right, key=right.get)})
    selections = [max(votes, key=lambda v: v["top_score"]), max(votes, key=lambda v: v["drift"])]
    unicode_votes = [v for v in votes if v["case"] == "unicode"]
    if unicode_votes:
        selections.append(max(unicode_votes, key=lambda v: v["drift"]))
    unique = {(v["text"], v["indicator"]): v for v in selections}
    assert len(unique) <= plan["diagnostic_inputs_max"]
    return votes, list(unique.values())


def analyze(info, old):
    from ml.se_brl.semantic_candidates import semantic_configuration
    import numpy as np
    _, hypotheses = semantic_configuration()
    source_config = fp.CACHE / ("models--" + info["source_repository"].replace("/", "--")) / "snapshots" / info["source_revision"] / "config.json"
    labels = json.loads(source_config.read_text())["id2label"]
    assert labels == {"0": "contradiction", "1": "entailment", "2": "neutral"}
    records = [d for d in old["disagreements"] if d.get("baseline") == "fp32"]
    votes, selections = diagnostic_records(old, info["budget"])
    scored_calls = [d for d in records if d["type"] == "nli_maxima_or_tie"]
    fields = [d for d in records if d["type"] == "review_outcome"]
    review_source = (ROOT / "ml/se_brl/semantic_review.py").read_text(encoding="utf-8")
    assert 'tops = [max(LABELS' in review_source and 'ties are uncertainty' in review_source.lower()
    # Diagnostic graphs expose raw logits; no zero-shot pipeline, sigmoid,
    # temperature or threshold transformation is introduced.
    original = prior.scorer(prior.INT8)
    transforms = []
    for record in selections:
        scores = original.score(record["text"], record["indicator"])
        logits = original.last_logits
        values = np.exp(logits - logits.max(axis=-1, keepdims=True))
        values /= values.sum(axis=-1, keepdims=True)
        manual = [{labels[str(i)]: float(row[i]) for i in range(3)} for row in values]
        assert scores == manual
        transforms.append({"text": record["text"], "indicator": record["indicator"],
                           "stable_softmax_and_label_mapping_exact": True})
    import onnxruntime as ort
    worst = max(selections, key=lambda row: row["drift"])
    original.score(worst["text"], worst["indicator"])
    feed = original.last_tokens
    fusion_check = {"text": worst["text"], "indicator": worst["indicator"],
                    "int8_default_logits": original.last_logits.tolist()}
    for name, path, level in (("fp32", fp.ARTIFACT, ort.GraphOptimizationLevel.ORT_ENABLE_ALL),
                              ("int8_unfused", prior.INT8, ort.GraphOptimizationLevel.ORT_DISABLE_ALL)):
        options = ort.SessionOptions(); options.intra_op_num_threads = 2; options.inter_op_num_threads = 1
        options.graph_optimization_level = level
        session = ort.InferenceSession(str(path), sess_options=options, providers=["CPUExecutionProvider"])
        fusion_check[name + "_logits"] = session.run(["logits"], feed)[0].tolist()
        del session
        gc.collect()
    fusion_check["default_vs_unfused_max_absolute"] = float(np.max(np.abs(
        np.array(fusion_check["int8_default_logits"]) - np.array(fusion_check["int8_unfused_logits"]))))
    del original
    gc.collect()
    info.update(status="PASS", changed_calls=len(scored_calls), changed_hypothesis_votes=len(votes),
                distinct_changed_calls=len({(d["synthetic_text"], d["indicator"]) for d in scored_calls}),
                near_margin_votes=sum(v["margin"] <= info["budget"]["diagnostic_margin_bin"] for v in votes),
                high_top_score_votes=sum(v["top_score"] >= info["budget"]["diagnostic_high_top_score_bin"] for v in votes),
                maximum_changed_top_score=max(v["top_score"] for v in votes),
                maximum_changed_margin=max(v["margin"] for v in votes), changed_numeric_threshold_decisions=0,
                decision_rule="Argmax and exact ties; no numerical confidence threshold in canonical semantic review",
                indicator_counts=dict(Counter(d["indicator"] for d in scored_calls)),
                changed_review_fields=dict(Counter(d["field"] for d in fields)),
                evidence_or_semantic_status_changes=sum(d["field"] in {"evidence", "semantic_status", "candidate_state"} for d in fields),
                context_case_records=[d for d in records if d["case"] in {"negation", "quotation", "hypothetical"}],
                all_categorized_mismatches=records, diagnostic_votes=votes, diagnostic_inputs=selections,
                transformation_checks=transforms, label_order=labels,
                fusion_check=fusion_check)
    return info


def source_nodes(model):
    import onnx
    tensors = {t.name: t for t in model.graph.initializer}
    return [n for n in model.graph.node if n.op_type == "MatMul" and n.input[1] in tensors
            and tensors[n.input[1]].data_type == onnx.TensorProto.FLOAT and len(tensors[n.input[1]].dims) == 2]


def generate(info, candidate):
    import onnx
    from onnxruntime.quantization import quantize_dynamic, QuantType
    output = DIRECTORY / (candidate + ".onnx")
    source = onnx.load(str(fp.ARTIFACT))
    nodes = source_nodes(source)
    assert len(nodes) == 36
    retained = []
    if candidate != "range_reduced":
        ranking = json.loads((DIRECTORY / "probe-result.json").read_text(encoding="utf-8"))
        ordered = sorted(ranking["local_node_errors"], key=lambda v: (v["max_relative_rms"], v["node"]))
        if candidate == "retain_sensitive_blocks":
            blocks = sorted(ranking["block_scores"].items(), key=lambda x: (-x[1], x[0]))[:2]
            retained = [key for key, _ in blocks]
            nodes = [node for node in nodes if re.search(r"/layer\.(\d+)/", node.name).group(1) not in retained]
        else:
            nodes = [node for node in nodes if node.name == ordered[0]["node"]]
    names = [n.name for n in nodes]
    assert names
    settings = {"op_types_to_quantize": ["MatMul"], "per_channel": True, "reduce_range": True,
                "extra_options": {"MatMulConstBOnly": True, "WeightSymmetric": True, "ActivationSymmetric": False}}
    quantize_dynamic(str(fp.ARTIFACT), str(output), nodes_to_quantize=names, weight_type=QuantType.QInt8,
                     use_external_data_format=False, **settings)
    graph = onnx.load(str(output))
    # Undo ORT's unrelated Gemm normalization, as independently verified in Phase 4.
    gemms = [n for n in source.graph.node if n.op_type == "Gemm"]
    replacement = {n.name + "_MatMul": n for n in gemms}
    removed = {n.name + "_Add" for n in gemms}
    new_nodes = [deepcopy(replacement.get(n.name, n)) for n in graph.graph.node if n.name not in removed]
    graph.graph.ClearField("node")
    graph.graph.node.extend(new_nodes)
    initializers = {t.name: t for t in source.graph.initializer}
    restored = {n.input[1] for n in gemms}
    for tensor in graph.graph.initializer:
        if tensor.name in restored:
            tensor.CopyFrom(initializers[tensor.name])
    stale = restored | {n.output[0] + "_MatMul" for n in gemms}
    values = [deepcopy(v) for v in graph.graph.value_info if v.name not in stale]
    graph.graph.ClearField("value_info")
    graph.graph.value_info.extend(values)
    graph.graph.ClearField("output")
    graph.graph.output.extend(deepcopy(source.graph.output))
    changed = {n.input[1] for n in nodes}
    dest = {t.name: t for t in graph.graph.initializer}
    for name, tensor in initializers.items():
        if name not in changed:
            assert name in dest and tensor.data_type == dest[name].data_type
            assert list(tensor.dims) == list(dest[name].dims) and tensor.raw_data == dest[name].raw_data
            for field in ("float_data", "int32_data", "int64_data", "double_data", "uint64_data", "string_data"):
                assert list(getattr(tensor, field)) == list(getattr(dest[name], field))
    assert sum(n.op_type == "MatMulInteger" for n in graph.graph.node) == len(nodes)
    assert all(n.domain in {"", "ai.onnx"} for n in graph.graph.node)
    onnx.checker.check_model(graph, full_check=True)
    onnx.save(graph, str(output))
    info.update(status="PASS", candidate=candidate, artifact_sha256=fp.sha(output), artifact_bytes=output.stat().st_size,
                settings=settings, weight_type="QInt8 (range reduced to signed 7-bit values stored in INT8)",
                selected_nodes=names, retained_blocks=retained, unselected_weights_preserved=True)
    return info


def probe(info):
    """Three frozen inputs, local same-input errors, and sampled exact integer math."""
    import onnx
    from onnx import numpy_helper as nh, helper as oh, TensorProto as tp
    import numpy as np
    import onnxruntime as ort
    analysis = json.loads((DIRECTORY / "analyze-result.json").read_text(encoding="utf-8"))
    cases = analysis["diagnostic_inputs"]
    assert len(cases) <= 3
    source = onnx.load(str(fp.ARTIFACT))
    original_q = onnx.load(str(prior.INT8))
    reduced = onnx.load(str(DIRECTORY / "range_reduced.onnx"))
    nodes = source_nodes(source)
    original_initializers = {t.name: nh.to_array(t).copy() for t in original_q.graph.initializer if t.data_type != tp.FLOAT or "scale" in t.name}
    reduced_initializers = {t.name: nh.to_array(t).copy() for t in reduced.graph.initializer if t.data_type != tp.FLOAT or "scale" in t.name}
    weights = {t.name: nh.to_array(t).copy() for t in source.graph.initializer if t.name in {n.input[1] for n in nodes}}
    qnodes = {n.name.removesuffix("_quant"): n for n in original_q.graph.node if n.op_type == "MatMulInteger"}
    rqnodes = {n.name.removesuffix("_quant"): n for n in reduced.graph.node if n.op_type == "MatMulInteger"}
    producers = {output: n for n in original_q.graph.node for output in n.output}
    fp_outputs = set(o.name for o in source.graph.output)
    q_outputs = set(o.name for o in original_q.graph.output)

    def add(graph, names, name, dtype, shape):
        if name not in names:
            graph.graph.output.append(oh.make_tensor_value_info(name, dtype, shape))
            names.add(name)
    for n in nodes:
        k, width = weights[n.input[1]].shape
        add(source, fp_outputs, n.input[0], tp.FLOAT, [3, None, k])
        add(source, fp_outputs, n.output[0], tp.FLOAT, [3, None, width])
        q = qnodes[n.name]
        add(original_q, q_outputs, q.input[0], tp.UINT8, [3, None, k])
        add(original_q, q_outputs, q.input[2], tp.UINT8, [])
        add(original_q, q_outputs, q.output[0], tp.INT32, [3, None, width])
    fp_path, q_path = DIRECTORY / "fp32-probe.onnx", DIRECTORY / "original-int8-probe.onnx"
    onnx.save(source, str(fp_path)); onnx.save(original_q, str(q_path))
    f_names, q_names = [o.name for o in source.graph.output], [o.name for o in original_q.graph.output]
    del source, original_q, reduced
    gc.collect()
    options = ort.SessionOptions(); options.intra_op_num_threads = 2; options.inter_op_num_threads = 1
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
    f_session = ort.InferenceSession(str(fp_path), sess_options=options, providers=["CPUExecutionProvider"])
    q_session = ort.InferenceSession(str(q_path), sess_options=options, providers=["CPUExecutionProvider"])
    tok = fp.tokenizer()
    from ml.se_brl.semantic_candidates import semantic_configuration
    _, hypotheses = semantic_configuration()
    errors = {n.name: [] for n in nodes}
    sampled_cells = unequal_cells = saturation_matches = 0
    kernel_examples = []
    for case in cases:
        tokens = tok([case["text"]] * 3, hypotheses[case["indicator"]], padding=True, truncation=False, return_tensors="np")
        feed = {k: tokens[k].astype(np.int64) for k in ("input_ids", "attention_mask")}
        f = dict(zip(f_names, f_session.run(f_names, feed), strict=True))
        q = dict(zip(q_names, q_session.run(q_names, feed), strict=True))
        for node in nodes:
            qn, rn = qnodes[node.name], rqnodes[node.name]
            a = q[qn.input[0]][:, :3, :].reshape(-1, weights[node.input[1]].shape[0]).astype(np.int64)
            azp = q[qn.input[2]].astype(np.int64)
            b = original_initializers[qn.input[1]][:, :32].astype(np.int64)
            bz = original_initializers[qn.input[3]].astype(np.int64)
            if bz.ndim:
                bz = bz[:32]
            expected = (a - azp) @ (b - bz)
            actual = q[qn.output[0]][:, :3, :32].reshape(expected.shape).astype(np.int64)
            sampled_cells += expected.size
            mismatch = actual != expected
            unequal_cells += int(mismatch.sum())
            # VPMADDUBSW-like saturation fingerprint on sampled raw U8*S8 pairs.
            for row, column in np.argwhere(mismatch)[:3]:
                products = a[row] * b[:, column]
                pairs = products.reshape(-1, 2).sum(axis=1)
                saturating_error = int(np.clip(pairs, -32768, 32767).sum() - products.sum())
                observed_error = int(actual[row, column] - expected[row, column])
                matched = observed_error == saturating_error and saturating_error != 0
                saturation_matches += int(matched)
                kernel_examples.append({"case": case["case"], "node": node.name,
                    "row": int(row), "column": int(column), "exact_integer": int(expected[row,column]),
                    "runtime_integer": int(actual[row,column]), "pair_saturation_error": saturating_error,
                    "matches_pair_saturation": matched})
            # Isolate each range-reduced linear operation using the SAME FP32
            # activation input, rather than conflating upstream propagated drift.
            x = f[node.input[0]]
            lo, hi = min(0.0, float(x.min())), max(0.0, float(x.max()))
            scale = np.float32((hi - lo) / 255) if hi != lo else np.float32(1)
            zp = np.clip(np.round(-lo / scale), 0, 255)
            activation = (np.clip(np.round(x / scale) + zp, 0, 255) - zp).astype(np.float32) * scale
            qb = reduced_initializers[rn.input[1]].astype(np.float32)
            zpb = reduced_initializers[rn.input[3]].astype(np.float32)
            weight_scale = reduced_initializers[rn.input[1].removesuffix("_quantized") + "_scale"]
            w = (qb - zpb) * weight_scale
            reference = f[node.output[0]]
            local = activation @ w
            relative = float(np.sqrt(np.mean((local.astype(np.float64) - reference) ** 2)) /
                             max(np.sqrt(np.mean(reference.astype(np.float64) ** 2)), 1e-12))
            errors[node.name].append(relative)
    local_errors = [{"node": n, "max_relative_rms": max(values), "per_input_relative_rms": values}
                    for n, values in errors.items()]
    blocks = {}
    for row in local_errors:
        block = re.search(r"/layer\.(\d+)/", row["node"]).group(1)
        blocks[block] = max(blocks.get(block, 0), row["max_relative_rms"])
    info.update(status="PASS", diagnostic_inputs=cases, sampled_integer_cells=sampled_cells,
                integer_cells_differing_from_exact_math=unequal_cells,
                sampled_saturation_fingerprints=saturation_matches, kernel_examples=kernel_examples,
                local_node_errors=local_errors, block_scores=blocks,
                ranking_scope="Same-input ideal quantized linear outputs on three frozen inputs; no labels used for ranking")
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("analyze", "generate", "probe", "compare", "benchmark"))
    parser.add_argument("--candidate", choices=("range_reduced", "retain_sensitive_blocks", "single_low_error"), default="range_reduced")
    args = parser.parse_args()
    info, blocked, old = setup()
    output = DIRECTORY / (args.candidate + ".onnx")
    if args.mode == "analyze":
        info = analyze(info, old)
    elif args.mode == "generate":
        info = generate(info, args.candidate)
    elif args.mode == "probe":
        info = probe(info)
    else:
        generation = json.loads((DIRECTORY / (args.candidate + "-generate-result.json")).read_text(encoding="utf-8"))
        assert generation["artifact_sha256"] == fp.sha(output)
        info.update(candidate=args.candidate, artifact_sha256=fp.sha(output), artifact_bytes=output.stat().st_size)
        if args.mode == "compare":
            prior.INT8 = output
            info = prior.compare(info)
        else:
            comparison = json.loads((DIRECTORY / (args.candidate + "-compare-result.json")).read_text(encoding="utf-8"))
            assert comparison["status"] == "PASS", "Only exact-parity candidates may be benchmarked"
            fp.ARTIFACT = output
            info = fp.benchmark(info, args.candidate)
    assert fp.sha(fp.TOOL / "minilm-linear-int8.onnx") == old["generation"]["int8_sha256"]
    assert fp.sha(fp.TOOL / "minilm-fp32.onnx") == info["source_fp32_sha256"]
    assert all(e == "socket.bind" for e in blocked), blocked
    info["denied_optional_loopback_probes"] = blocked
    info["command"] = [".venv-transformer/onnx-tooling/Scripts/python", "-B", "scripts/diagnose_minilm_drift.py", *sys.argv[1:]]
    name = ((args.candidate + "-") if args.mode in {"generate", "compare", "benchmark"} else "") + args.mode + "-result.json"
    (DIRECTORY / name).write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    print("RESULT", name, info["status"], flush=True)
    if info["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
