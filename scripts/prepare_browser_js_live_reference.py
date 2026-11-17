"""Fresh offline PyTorch oracle for the Pyodide-free browser harness.

Synthetic engineering inputs only. Existing pinned artifacts only; no downloads.
"""
from copy import deepcopy
from dataclasses import asdict, replace
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
sys.dont_write_bytecode=True
import verify_minilm_onnx as fp
from prepare_browser_minilm_reference import serialize
from freeze_js_review_contracts import generate, OUT as CONTRACT


def main():
    assert CONTRACT.read_text(encoding="utf-8")==generate()
    phase6=json.loads((ROOT/"docs/research/minilm-browser-fp32-verification.json").read_text())
    phase7=json.loads((ROOT/"docs/research/js-review-parity.json").read_text())
    for name,digest in phase7["provenance"]["source_sha256"].items():
        assert fp.sha(ROOT/"tools/verification/js-review"/name)==digest, name
    info,blocked=fp.setup()
    assert fp.sha(fp.ARTIFACT)==phase6["source_model"]["onnx_sha256"]
    from ml.se_brl.semantic_review import review_record,validate_review,predictor_values
    from ml.se_brl.semantic_candidates import SemanticInferenceUnavailable
    from ml.se_brl.detectors import DetectorContext
    from ml.preprocessing import preprocess
    from ml.datasets import DatasetRecord
    from ml.se_brl.review_adapter import record_from_request
    from ml.tests.test_semantic_review import source
    native=fp.canonical()
    prior=json.loads((ROOT/".venv-transformer/browser-harness/data/reference.json").read_text(encoding="utf-8"))
    assert fp.sha(ROOT/".venv-transformer/browser-harness/data/reference.json")==phase7["provenance"]["frozen_reference_sha256"]
    payload=deepcopy(prior["payload"])
    spec=importlib.util.spec_from_file_location("synthetic_bridge",ROOT/"tools/verification/browser-fp32/bridge.py")
    bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
    extras=[]
    r,c=source("🧪 Act now.","content_bearing_webpage")
    r=replace(r,artifact_input={**dict(r.artifact_input),"html":'<p>We are Contoso. 🧪 Act now. <a href="../help?x=1&amp;y=2">Submit your password.</a></p>',"link_extraction_authorized":True})
    extras.append(serialize("edge:html_authorized_unicode",r,c))
    for name,sender in (("nested_comment","sender@other.example (Outer (Inner) audit)"),
                        ("quoted_name",'"Sender (literal)" <sender@official.example>'),
                        ("malformed_header","sender@other.example (unclosed")):
        r,c=source("Act now. Submit your password.")
        extras.append(serialize("edge:"+name,replace(r,artifact_input={**dict(r.artifact_input),"sender":sender}),c))
    r,c=source("Do not not contact your bank. Could you submit your password?")
    extras.append(serialize("edge:double_negation_question",r,c))
    r,c=source("synthetic "*512)
    extras.append(serialize("edge:oversized_review",r,c))
    raw={"kind":"email","body":'> Act now.\nOn Monday X wrote:\nSubmit your password.',"body_collection_authorized":True,"study_purpose":"Synthetic engineering only"}
    r=DatasetRecord("synthetic:quoted","synthetic","content_bearing_email",raw,("body",),None,{"reference":"synthetic-only"})
    extras.append(serialize("edge:quoted_body",r,None))
    r,c=source("Act now.")
    extras.append(serialize("edge:unaudited_identity",r,DetectorContext(tuple(replace(ref,delegation_audited=False) for ref in c.identities))))
    payload["extra_cases"]=extras
    captures={};forward_times=[];last={}
    def capture(_module,_args,kwargs,output):
        last["tokens"]={k:v.detach().cpu().tolist() for k,v in kwargs.items()}
        last["logits"]=output.logits.detach().cpu().tolist()
    hook=native.model.register_forward_hook(capture,with_kwargs=True)
    class Live:
        def __init__(self):self.calls=0
        def score(self,text,indicator):
            self.calls+=1
            key=bridge.key(text,indicator)
            if key not in captures:
                tokens=native.tokenizer([text]*3,native.hypotheses[indicator],padding=True,truncation=False,return_tensors="pt")
                over=tokens["input_ids"].shape[1]>512
                entry={"text":text,"indicator":indicator,"input_ids":tokens["input_ids"].tolist(),"attention_mask":tokens["attention_mask"].tolist(),"oversized":over,"scores":None,"logits":None}
                if not over:
                    start=time.perf_counter()
                    scores=native.score(text,indicator)
                    forward_times.append((time.perf_counter()-start)*1000)
                    assert entry["input_ids"]==last["tokens"]["input_ids"] and entry["attention_mask"]==last["tokens"]["attention_mask"]
                    entry.update(logits=last["logits"],scores=scores)
                else:
                    try:native.score(text,indicator)
                    except SemanticInferenceUnavailable:pass
                    else:raise AssertionError("Canonical oversized input executed")
                captures[key]=entry
            entry=captures[key]
            if entry["oversized"]:raise SemanticInferenceUnavailable("oversized synthetic input")
            return deepcopy(entry["scores"])
    live=Live();expected=[];preprocessing=[]
    start=time.perf_counter()
    for case in payload["cases"]+extras:
        record,ctx=bridge.reconstruct(case)
        before=review_record(record,detector_context=ctx).to_dict()
        value=review_record(record,scorer=live,detector_context=ctx).to_dict()
        assert all((a["deterministic_state"],a["evidence"])==(b["deterministic_state"],b["evidence"]) for a,b in zip(before["indicators"],value["indicators"]))
        expected.append({"name":case["name"],"outcome":bridge.normalize(value)})
        preprocessing.append(asdict(preprocess(record.artifact_input)))
    # Original frozen guard cases execute with newly computed live scores.
    scores=live.score(payload["boundary_text"],"urgency")
    expected.append({"name":"exact_512_tokens","outcome":{"scored":True,"maxima":[[k for k,v in row.items() if v==max(row.values())] for row in scores]}})
    try:live.score(payload["boundary_text"]+"synthetic ","urgency")
    except SemanticInferenceUnavailable:pass
    else:raise AssertionError("oversized input executed")
    expected.append({"name":"513_tokens_abstain","outcome":{"abstained_without_truncation":True}})
    record,ctx=bridge.reconstruct(payload["budget_case"]);budget=Live()
    value=review_record(record,scorer=budget,detector_context=ctx).to_dict();assert budget.calls==512
    expected.append({"name":"64_unit_512_call_budget_replay","outcome":bridge.normalize(value)})
    record,ctx=bridge.reconstruct(payload["cases"][0]);valid=review_record(record,scorer=live,detector_context=ctx).to_dict();rejected=0
    for bad_start in (True,-1):
        bad=deepcopy(valid);bad["indicators"][0]["semantic_candidates"][0]["evidence"]["start"]=bad_start
        try:validate_review(bad,record,detector_context=ctx)
        except ValueError:rejected+=1
    bad=deepcopy(valid);bad["indicators"][0]["candidate_state"]="supported"
    try:validate_review(bad,record,detector_context=ctx)
    except ValueError:rejected+=1
    class Bad:
        def score(self,*args):return [{"entailment":float("nan"),"neutral":0,"contradiction":0}]*3
    invalid=review_record(record,scorer=Bad(),detector_context=ctx).to_dict()
    nan_rejected=all(not row["semantic_candidates"] for row in invalid["indicators"])
    export_blocked=False
    try:predictor_values(valid)
    except ValueError:export_blocked=True
    assert rejected==3 and nan_rejected and export_blocked
    expected.append({"name":"malformed_inputs_and_export_gate","outcome":{"invalid_spans_and_promotion_rejected":rejected,"nan_scores_rejected":nan_rejected,"predictor_export_blocked":export_blocked}})
    hook.remove()
    # Supplementary rejected-input tests; no fake scores enter primary reports.
    request={"schema_version":"1.0.0","codebook_version":"0.1.0","artifact_id":"synthetic:consent","source_id":"synthetic","source_reference":"synthetic-only","modality":"content_bearing_email","language":"en","fields":{"body":"Act now."},"body_collection_authorized":False,"link_extraction_authorized":False,"study_purpose":""}
    consent=[]
    for changes in ({},{"body_collection_authorized":True,"study_purpose":"synthetic"},{"language":"und"},{"fields":{"urls":["https://example.test/"]}}):
        item={**request,**changes}
        try:record_from_request(item);accepted=True
        except ValueError:accepted=False
        consent.append({"request":item,"accepted":accepted})
    payload["consent"]=consent
    output=fp.TOOL/"browser-js-live";output.mkdir(exist_ok=True)
    bundle={"payload":payload,"requests":list(captures.values()),"expected":{"cases":expected,"preprocessing":preprocessing},"onnx_sha256":fp.sha(fp.ARTIFACT),"onnx_bytes":fp.ARTIFACT.stat().st_size,"tolerances":fp.TOL}
    reference=output/"reference.json";reference.write_text(json.dumps(bundle,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    info.update(status="PASS",reference_sha256=fp.sha(reference),phase6_record_sha256=fp.sha(ROOT/"docs/research/minilm-browser-fp32-verification.json"),phase7b_record_sha256=fp.sha(ROOT/"docs/research/js-review-parity.json"),frozen_fixture_sha256=payload["frozen_fixture_sha256"],cases=len(expected),unique_requests=len(captures),actual_forwards=len(forward_times),oracle_ms=(time.perf_counter()-start)*1000,script_sha256=fp.sha(__file__))
    (output/"preparation.json").write_text(json.dumps(info,indent=2)+"\n")
    print("LIVE_ORACLE_READY",len(expected),"cases;",len(forward_times),"actual pinned PyTorch forwards",flush=True)


if __name__=="__main__":main()
