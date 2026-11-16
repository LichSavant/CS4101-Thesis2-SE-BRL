"""Separate activation-rounding from weight-rounding on frozen probes only."""
from __future__ import annotations

import gc
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import diagnose_minilm_drift as diag


def main():
    info, blocked, _ = diag.setup()
    import numpy as np
    import onnx
    from onnx import numpy_helper as nh
    import onnxruntime as ort
    probe = json.loads((diag.DIRECTORY / "probe-result.json").read_text(encoding="utf-8"))
    rank = sorted(probe["local_node_errors"], key=lambda r: (r["max_relative_rms"], r["node"]))
    selected = [rank[0]["node"], rank[-1]["node"], rank[-2]["node"]]
    source = onnx.load(str(diag.fp.ARTIFACT))
    nodes = {n.name: n for n in source.graph.node if n.name in selected}
    weights = {t.name: nh.to_array(t).copy() for t in source.graph.initializer
               if t.name in {n.input[1] for n in nodes.values()}}
    del source
    gc.collect()
    quantized = {}
    for label, path in (("original_full_range", diag.prior.INT8),
                        ("range_reduced", diag.DIRECTORY / "range_reduced.onnx")):
        graph = onnx.load(str(path))
        qnodes = {n.name.removesuffix("_quant"): n for n in graph.graph.node
                  if n.name.removesuffix("_quant") in selected and n.op_type == "MatMulInteger"}
        wanted = {name for n in qnodes.values() for name in (n.input[1], n.input[3], n.input[1].removesuffix("_quantized") + "_scale")}
        values = {t.name: nh.to_array(t).copy() for t in graph.graph.initializer if t.name in wanted}
        quantized[label] = {name: (values[n.input[1]].astype(np.float32) - values[n.input[3]]) *
                             values[n.input[1].removesuffix("_quantized") + "_scale"] for name, n in qnodes.items()}
        del graph
        gc.collect()
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
    session = ort.InferenceSession(str(diag.DIRECTORY / "fp32-probe.onnx"), sess_options=options,
                                   providers=["CPUExecutionProvider"])
    tok = diag.fp.tokenizer()
    from ml.se_brl.semantic_candidates import semantic_configuration
    _, hypotheses = semantic_configuration()
    results = []
    for case in probe["diagnostic_inputs"]:
        tokens = tok([case["text"]] * 3, hypotheses[case["indicator"]], padding=True, truncation=False, return_tensors="np")
        feed = {k: tokens[k].astype(np.int64) for k in ("input_ids", "attention_mask")}
        names = [nodes[n].input[0] for n in selected]
        activations = dict(zip(names, session.run(names, feed), strict=True))
        for name, node in nodes.items():
            x, w = activations[node.input[0]], weights[node.input[1]]
            reference = x @ w
            scale = np.float32((max(0., float(x.max())) - min(0., float(x.min()))) / 255)
            zero = np.clip(np.round(-min(0., float(x.min())) / scale), 0, 255)
            xd = (np.clip(np.round(x / scale) + zero, 0, 255) - zero).astype(np.float32) * scale
            def rms_error(value):
                return float(np.sqrt(np.mean((value.astype(np.float64) - reference) ** 2)) /
                             max(np.sqrt(np.mean(reference.astype(np.float64) ** 2)), 1e-12))
            row = {"case": case["case"], "node": name, "activation_step": float(scale),
                   "input_rms": float(np.sqrt(np.mean(x.astype(np.float64) ** 2))),
                   "input_max_abs": float(np.max(np.abs(x))),
                   "activation_only_relative_rms": rms_error(xd @ w), "weight_schemes": {}}
            for scheme, matrices in quantized.items():
                wd = matrices[name]
                row["weight_schemes"][scheme] = {
                    "weight_only_relative_rms": rms_error(x @ wd),
                    "combined_relative_rms": rms_error(xd @ wd)}
            results.append(row)
    assert all(event == "socket.bind" for event in blocked)
    info.update(status="PASS", selected_nodes=selected, results=results,
                verifier_sha256=diag.fp.sha(__file__),
                method="Same FP32 inputs and same FP32 reference MatMul; separately round U8 activations and per-channel INT8 weights. Descriptive RMS only; no labels or rule changes.")
    (diag.DIRECTORY / "rounding-components-result.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    print("RESULT rounding-components-result.json PASS", flush=True)


if __name__ == "__main__":
    main()
