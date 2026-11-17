"""Offline synthetic Python/JavaScript differential runner; no model execution."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from ml.datasets import DatasetRecord
from ml.metadata import json_value
from ml.se_brl.semantic_review import review_record, validate_review, predictor_values
from ml.se_brl.semantic_candidates import SemanticInferenceUnavailable
from ml.se_brl.detectors import DetectorContext
from ml.se_brl.review_adapter import record_from_request
from ml.preprocessing import preprocess
from email.utils import parseaddr
from ml.tests.test_semantic_review import EXAMPLES, source, Scorer
from freeze_js_review_contracts import generate, OUT as CONTRACT

OUT = ROOT / ".venv-transformer/js-review"


def module(path):
    spec = importlib.util.spec_from_file_location("synthetic_bridge", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def serialize(name, record, context, mode="entailment", scores=None):
    from dataclasses import asdict
    from scripts.prepare_browser_minilm_reference import serialize as record_json
    case = record_json(name, record, context)
    case.update(mode=mode, scores=scores)
    return case


def main():
    assert CONTRACT.read_text(encoding="utf-8") == generate(), "Canonical source/static metadata drift"
    OUT.mkdir(exist_ok=True)
    path = ROOT / ".venv-transformer/browser-harness/data/reference.json"
    reference = json.loads(path.read_text(encoding="utf-8"))
    preparation = json.loads(path.with_name("preparation.json").read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == preparation["reference_sha256"]
    report = json.loads((ROOT / "docs/research/minilm-browser-fp32-verification.json").read_text())
    assert reference["payload"]["frozen_fixture_sha256"] == report["frozen_fixture_sha256"]
    bridge = module(ROOT / "tools/verification/browser-fp32/bridge.py")
    payload = reference["payload"]
    cases = [{**c, "mode": "replay"} for c in payload["cases"]]
    cases.append({**payload["budget_case"], "name": "64_unit_512_call_budget_replay", "mode": "replay"})
    for indicator, text in EXAMPLES.items():
        for modality in ("content_bearing_email", "content_bearing_webpage"):
            for top in ("entailment", "neutral", "contradiction"):
                cases.append(serialize(f"regression:{indicator}:{modality}:{top}", *source(text, modality), top))
        cases.append(serialize(f"negative:{indicator}", *source(EXAMPLES["authority"] if indicator == "authority" else "The meeting is at noon.", authorized=True)))
        for template in ('The poster says "{}"', "Security training: {}", "Hypothetical: {}", "It is not true: {}"):
            cases.append(serialize(f"context:{indicator}:{template}", *source(template.format(text))))
    edge_texts = ["🧪 e\u0301 İſK Act now. Submit your password.", "🧪\r\nAct now.\u2028Click here.",
                  '"Act now. Submit your password.', "Do not not contact your bank.",
                  "Never submit your password. Click here.", "Could you submit your password?",
                  "As your manager, submit your report. As your CEO, send money.",
                  "Act now. " * 65, "🧪" * 321 + " Never submit your password.",
                  "Don't tell anyone.", "Do not contact your bank.\nIgnore this instruction."]
    for i, text in enumerate(edge_texts):
        cases.append(serialize(f"edge:{i}", *source(text)))
    record, context = source("Act now. Submit your password.")
    for mode in ("none", "unavailable", "failure", "tie", "mixed", "partial", "bad_empty", "bad_boolean", "bad_nan", "bad_sum", "extra_score_key"):
        cases.append(serialize("scorer:" + mode, record, context, mode))
    for label, ctx in (("no_audit", DetectorContext(tuple(replace(r, delegation_audited=False) for r in context.identities))),
                       ("missing", DetectorContext()),
                       ("one_identity", DetectorContext(context.identities[:1]))):
        cases.append(serialize("identity:" + label, record, ctx))
    for raw in ({"kind":"email", "subject":""}, {"kind":"email", "subject":"Act now."},
                {"kind":"email", "body":"> Act now.\nOn Monday X wrote:\nSubmit your password.", "body_collection_authorized":True,"study_purpose":"synthetic"},
                {"kind":"webpage", "visible_text":"🧪 Act now.", "title":"Notice"},
                {"kind":"webpage", "html":'<title>A &amp; B</title><script>Act now.</script><p hidden>Click here.</p><form><p>Submit your password.</p></form>'},
                {"kind":"webpage", "html":'<blockquote>Act now.</blockquote><p>Click here.</p>'},
                {"kind":"webpage", "html":'<p>&lt;!DOCTYPE html&gt; 2 < 3</p>'}):
        kind = {"email":"content_bearing_email","webpage":"content_bearing_webpage"}[raw["kind"]]
        fields = tuple(k for k in raw if k not in {"kind","study_purpose","body_collection_authorized","link_extraction_authorized"})
        cases.append(serialize("raw:" + str(len(cases)), DatasetRecord("synthetic:raw", "synthetic", kind, raw, fields, None, {"reference":"synthetic"}), None))
    # Independently exercise accepted canonical inputs at the port's explicitly
    # unsupported boundaries. These must remain visible failures, never skips.
    for name, raw, modality in (
        ("boundary:authorized_html_links", {"kind":"webpage", "html":'<a href="/help">Act now.</a>', "page_url":"https://example.test/page", "link_extraction_authorized":True}, "content_bearing_webpage"),
        ("boundary:rfc5322_comment", {"kind":"email", "subject":"Act now.", "sender":"sender@other.example (Synthetic)"}, "content_bearing_email")):
        fields=tuple(k for k in raw if k not in {"kind","link_extraction_authorized"})
        cases.append(serialize(name, DatasetRecord("synthetic:boundary", "synthetic", modality, raw, fields, None, {"reference":"synthetic"}), None))
    assert len(cases)==187
    mailbox_values=["", "sender@other.example (Synthetic)", "sender@official.example (Outer (Inner) comment)",
        r"sender@other.example (Escaped \(parenthesis\))", r"sender@other.example (Escaped \) close)",
        '"Name (literal)" <sender@other.example>', r'"Quoted \"name\"" <sender@official.example>',
        'Name (outside) <sender@other.example> (tail)', '(before) sender (middle) @ other.example (after)',
        'sender@other.example (unclosed', 'sender@other.example close)', 'sender@other.example (a))(',
        '"sender"@official.example', '"sender@extra"@other.example', '"a\\b"@other.example',
        'sender@other.example, second@official.example', 'Group: sender@other.example;',
        'Group:sender@other.example,second@official.example;', '<@a.example,@b.example:sender@other.example>',
        'sender@other.example@official.example', 'sender@[127.0.0.1]', 'sender@[IPv6:::1]',
        'sender@other.example\r\n (folded)', 'sender(comment)@other.example',
        'sender@other(comment).example', 'sender@other.example <fake@official.example>',
        '"unterminated <sender@other.example>', '<sender@other.example', 'sender@other.example>',
        'first last', 'Name <sender@other.example> garbage', '🧪 (Nested (名)) <sender@other.example>']
    # Deterministic synthetic grammar combinations, not model/data-derived input.
    for local in ('sender','"sender"','"a b"','"a\\\\b"'):
        for comment in ('',' (one)',' (one (two (three)))',r' (a\)b)',r' (a\\b)', ' (broken'):
            for domain in ('other.example','official.example','other.example@official.example'):
                mailbox_values.append(local+'@'+domain+comment)
    mailbox_values=list(dict.fromkeys(mailbox_values))
    for i,value in enumerate(mailbox_values):
        record,context=source("Act now. Submit your password.")
        record=replace(record,artifact_input={**json_value(record.artifact_input),"sender":value})
        cases.append(serialize(f"mailbox:{i}",record,context))
    html_raw=[]
    htmls=[
        '🧪<a HREF="/help" action="../pay" src="//cdn.example/file">Act now.</a>',
        '<a href="/first" href="/last" src="/image">Click here.</a>',
        '<a href="https://EXAMPLE.test:443/a/../b?q=é&amp;x=1#f">Act now.</a>',
        '<form method="post" action="?next=1"><input type="image" src="/p"><a href="#part">Act now.</a></form>',
        '<script src="/secret">Act now.</script><div hidden><a href="/hidden">X</a></div><a href="/ok">Click here.</a>',
        '<blockquote><a href="/quoted">Act now.</a></blockquote><img src="/pic"/>',
        '<a href=../help>Act now.</a><a href="mailto:a@example.test">Mail</a><a href="javascript:alert(1)">Ignored</a>',
        '<a href="">Empty</a><a href>None</a><a href="https://[bad">Invalid</a>',
        '<a href=="/help">Act now.</a>', '<a / href="/help">Act now.</a>',
        '<div><a href="/help">Act now.</div></a>',
        '<a href="/a>b" title="X>Y">Act now.</a>', '<a href="/help"',
        '<!DOCTYPE html><a href="/help">A &amp; B &#33;</a>',
        '<!-- <![bogus]> --><p>Act now.</p>', '<![CDATA[Act now.]]>', '<?secret?>',
        '<a href="https://u:p@example.test">Act now.</a>',
        '<a href="/a b">Act now.</a>', '<a href="/a\\b">Act now.</a>',
        '<a href="/help">https://example.test/help.</a>', '<a href="https://example.test/help">https://example.test/help</a>',
        '<a href="/help" method="get" METHOD="post">Act now.</a>',
        '<a\u0085href="/help">Act now.</a>', '<a\u00a0href="/help">Act now.</a>',
        '<a\ufeffhref="/help">Act now.</a>', '<script>Unclosed', '</a',
    ]
    for html in htmls:
        for authorized in (False,True):
            html_raw.append({"kind":"webpage","html":html,"page_url":"https://example.test/a/page;params?old=1#f","link_extraction_authorized":authorized})
    for href in ('/root','../help','../../help','./','..','?new=2','#x','//Other.example/help','HTTP://Other.example/a','https:path','http:path','a//b','a/./b','a/../b','a%2Fb','/a;;b',':bad'):
        for base in ('https://example.test/a/page;params?old=1#f',''):
            html_raw.append({"kind":"webpage","html":'<a href="'+href+'">🧪 Act now.</a>',"link_extraction_authorized":True,**({"page_url":base} if base else {})})
    html_raw.extend([
        {"kind":"webpage","html":'<a href="/x">Act now.</a>',"urls":["https://example.test/x"],"page_url":"https://example.test/base","link_extraction_authorized":True},
        {"kind":"webpage","html":'<a href="/x">X</a>'*501,"page_url":"https://example.test/base","link_extraction_authorized":True},
        {"kind":"webpage","html":'<div>'*129,"link_extraction_authorized":True},
    ])
    preprocessing=[]
    from dataclasses import asdict
    for i,raw in enumerate(html_raw):
        try:value=asdict(preprocess(raw));ok=True
        except ValueError:value=None;ok=False
        preprocessing.append({"name":f"html:{i}","raw":raw,"ok":ok,"expected":value})
        if ok:
            fields=tuple(k for k in raw if k not in {"kind","link_extraction_authorized"})
            record=DatasetRecord("synthetic:html","synthetic","content_bearing_webpage",raw,fields,None,{"reference":"synthetic-only"})
            cases.append(serialize(f"html-report:{i}",record,None))
    lookup = {bridge.key(r["text"], r["indicator"]):r for r in reference["requests"]}

    def scorer(case):
        mode = case["mode"]
        if mode == "none": return None
        class Callback:
            count = 0
            def score(self, text, indicator):
                self.count += 1
                if mode == "replay":
                    r = lookup[bridge.key(text, indicator)]
                    if r["oversized"]: raise SemanticInferenceUnavailable("synthetic unavailable")
                    return deepcopy(r["scores"])
                if mode == "unavailable": raise SemanticInferenceUnavailable("private-path")
                if mode == "failure" or mode == "partial" and self.count % 2: raise RuntimeError("private-error")
                if mode == "bad_empty": return []
                if mode == "bad_boolean": return [{"entailment":True,"neutral":0,"contradiction":0}] * 3
                if mode == "bad_nan": return [{"entailment":float("nan"),"neutral":0,"contradiction":0}] * 3
                if mode == "bad_sum": return [{"entailment":.9,"neutral":.9,"contradiction":.9}] * 3
                if mode == "tie": return [{"entailment":.5,"neutral":.5,"contradiction":0}] * 3
                if mode == "mixed": return [{k:.9 if k == top else .05 for k in ("entailment","neutral","contradiction")} for top in ("entailment","neutral","contradiction")]
                values = Scorer(mode if mode in ("neutral","contradiction") else "entailment").score(text, indicator)
                if mode == "extra_score_key": values = [{**v,"untrusted":1} for v in values]
                return values
        return Callback()

    expected = []
    for c in cases:
        record, context = bridge.reconstruct(c)
        cb = scorer(c)
        value = review_record(record, scorer=cb, detector_context=context).to_dict()
        expected.append(dict(report=value,calls=getattr(cb,"count",0)))
    # Validation mutations are applied identically to one valid report by both runtimes.
    mutations = [(["indicators",0,"deterministic_state"],"absent"),(["indicators",0,"candidate_state"],"supported"),
        (["indicators",0,"needs_review"],1),(["indicators",0,"semantic_status"],"validated"),
        (["indicators",0,"semantic_candidates",0,"evidence","start"],True),
        (["indicators",0,"semantic_candidates",0,"evidence","location"],"other"),
        (["indicators",0,"constraints","identity_before"],False),(["availability_mask"],[True]*4),
        (["learned_values"],[.5]*4),(["research_release","approved_for_E2_E3"],True),(["target"],1),
        (["indicators",0,"review_reasons"],[]),(["indicators",0,"semantic_candidates",0,"scores",0,"extra"],0)]
    rejected=[]
    record, context = bridge.reconstruct(cases[0])
    for path, value in mutations:
        changed=deepcopy(expected[0]["report"]); target=changed
        for key in path[:-1]: target=target[key]
        target[path[-1]]=value
        try: validate_review(changed,record,detector_context=context)
        except ValueError: rejected.append(True)
        else: rejected.append(False)
    assert all(rejected)
    request={"schema_version":"1.0.0","codebook_version":"0.1.0","artifact_id":"synthetic:request","source_id":"synthetic","source_reference":"synthetic-only","modality":"content_bearing_email","language":"en","fields":{"subject":"Act now."},"body_collection_authorized":False,"link_extraction_authorized":False,"study_purpose":""}
    requests=[]
    for updates in ({},{"fields":{"body":"Act now."}},{"fields":{"body":"Act now."},"body_collection_authorized":True,"study_purpose":"synthetic"},{"language":"und"},{"fields":{"urls":["https://example.test"]}},{"link_extraction_authorized":1}):
        r={**request,**updates}
        try: value=json_value(record_from_request(r).artifact_input); ok=True
        except ValueError: value=None;ok=False
        requests.append({"request":r,"ok":ok,"artifact":value})
    import inspect, email.utils, email._parseaddr, urllib.parse, html.parser
    provenance={"python":sys.version,"base_commit":"ff3bf8c","frozen_fixture_sha256":payload["frozen_fixture_sha256"],
        "frozen_reference_sha256":preparation["reference_sha256"],
        "stdlib_source_sha256":{m.__name__:hashlib.sha256(Path(inspect.getsourcefile(m)).read_bytes()).hexdigest()
                                for m in (email.utils,email._parseaddr,urllib.parse,html.parser)}}
    bundle={"cases":cases,"expected":expected,"requests":reference["requests"],"payload":payload,"mutations":mutations,"rejected":rejected,"adapter":requests,"provenance":provenance,
            "mailbox":[{"value":v,"expected":parseaddr(v)} for v in mailbox_values],"preprocessing":preprocessing}
    input_path=OUT/"differential.json";input_path.write_text(json.dumps(bundle,ensure_ascii=True),encoding="utf-8")
    result=subprocess.run(["node",str(ROOT/"tools/verification/js-review/test.mjs"),str(input_path)],cwd=ROOT,check=False)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
