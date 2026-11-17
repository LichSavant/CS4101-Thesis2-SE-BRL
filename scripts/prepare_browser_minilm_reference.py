"""Freeze native reference and unchanged Python source for an isolated browser.

No downloads. Output is staged inside the existing ignored ONNX tooling folder.
"""
import base64
from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import verify_minilm_onnx as fp


def serialize(name, record, context):
    from ml.metadata import json_value
    assert not record.groups and record.phishing_label is None
    return {"name": name, "record": {field: json_value(getattr(record, field)) for field in (
        "record_id", "source_dataset", "modality", "artifact_input", "fields_available", "content_available",
        "provenance", "source_record_id", "source_metadata")}, "context": asdict(context) if context else None}


def main():
    info, blocked = fp.setup()
    output = fp.TOOL / "browser-reference"
    output.mkdir(exist_ok=True)
    bridge_path = ROOT / "tools/verification/browser-fp32/bridge.py"
    spec = importlib.util.spec_from_file_location("browser_bridge", bridge_path)
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    pt = fp.canonical()
    cases = fp.frozen_cases()
    frozen = json.dumps([{"name": n, "artifact": dict(r.artifact_input), "modality": r.modality}
                         for n, r, _ in cases], sort_keys=True, ensure_ascii=False).encode()
    prior = json.loads((ROOT / "docs/research/minilm-onnx-verification.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(frozen).hexdigest() == prior["comparison"]["frozen_fixture_sha256"]
    assert fp.sha(fp.ARTIFACT) == prior["export"]["onnx_sha256"]
    boundary = None
    for n in range(450, 513):
        text = "synthetic " * n
        tokens = pt.tokenizer([text] * 3, pt.hypotheses["urgency"], padding=True, truncation=False, return_tensors="pt")
        if tokens["input_ids"].shape[1] == 512:
            boundary = text
            break
    assert boundary is not None
    from ml.tests.test_semantic_review import source
    record, context = source("Act now. " * 65)
    payload = {"cases": [serialize(n, r, c) for n, r, c in cases], "boundary_text": boundary,
               "budget_case": serialize("budget", record, context), "hypotheses": pt.hypotheses,
               "frozen_fixture_sha256": hashlib.sha256(frozen).hexdigest()}
    requests = bridge.discover(payload)
    scored = []
    for request in requests:
        text, indicator = request["text"], request["indicator"]
        tokens = pt.tokenizer([text] * 3, pt.hypotheses[indicator], padding=True, truncation=False, return_tensors="pt")
        oversized = tokens["input_ids"].shape[1] > 512
        item = {**request, "input_ids": tokens["input_ids"].tolist(), "attention_mask": tokens["attention_mask"].tolist(),
                "oversized": oversized, "logits": None, "scores": None}
        if not oversized:
            with pt.torch.inference_mode():
                logits = pt.model(**tokens).logits
                values = pt.torch.softmax(logits, dim=-1).cpu().tolist()
            item["logits"] = logits.cpu().tolist()
            item["scores"] = [{label: float(row[i]) for label, i in pt.indices.items()} for row in values]
        else:
            from ml.se_brl.semantic_candidates import SemanticInferenceUnavailable
            try:
                pt.score(text, indicator)
            except SemanticInferenceUnavailable:
                pass
            else:
                raise AssertionError("Native oversized input was executed")
        scored.append(item)
    expected = bridge.run_suite(payload, scored)
    # Package only actually imported framework modules; never corpus loaders,
    # test helpers or Python's native ML/inference dependencies.
    sources = {}
    for name, module in list(sys.modules.items()):
        filename = getattr(module, "__file__", None)
        if not name.startswith("ml") or name.startswith("ml.tests") or not filename:
            continue
        path = Path(filename)
        if path.suffix == ".py" and path.is_relative_to(ROOT):
            relative = path.relative_to(ROOT).as_posix()
            sources[relative] = path.read_text(encoding="utf-8").encode("utf-8")
    for relative in ("ml/research-inputs.v1.json", "ml/se_brl/codebook.v0.1.0.json",
                     "ml/se_brl/result-envelope.v0.1.0.json", "ml/se_brl/semantic-model.v1.json",
                     "experiments/vera_validation/V13_nli_hypotheses_v0.1.0.json"):
        sources[relative] = (ROOT / relative).read_bytes()
    sources["bridge.py"] = bridge_path.read_bytes()
    package = [{"path": relative, "sha256": hashlib.sha256(data).hexdigest(),
                "base64": base64.b64encode(data).decode()} for relative, data in sorted(sources.items())]
    bundle = {"payload": payload, "requests": scored, "expected": expected, "python_sources": package,
              "tolerances": fp.TOL, "onnx_sha256": fp.sha(fp.ARTIFACT), "onnx_bytes": fp.ARTIFACT.stat().st_size}
    (output / "reference.json").write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    info.update(status="PASS", cases=24, unique_nli_requests=len(scored),
                scored_requests=sum(not r["oversized"] for r in scored),
                frozen_fixture_sha256=payload["frozen_fixture_sha256"], reference_sha256=fp.sha(output / "reference.json"),
                package_source_hashes={p["path"]: p["sha256"] for p in package},
                bridge_py_sha256=fp.sha(bridge_path), preparation_script_sha256=fp.sha(__file__))
    (output / "preparation.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    assert all(event == "socket.bind" for event in blocked)
    print("REFERENCE_READY", len(scored), "requests; 24 cases", flush=True)


if __name__ == "__main__":
    main()
