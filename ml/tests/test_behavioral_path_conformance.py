"""Neutral source-only Notebook 04 checks; no cell execution or output access.

Only the two pure aggregation functions are compiled. Extraction policy remains
pending P6/P7; the partial-evaluation mismatch is asserted, not normalized away.
"""
import ast
import json
from pathlib import Path

import pytest

from ml.preprocessing import preprocess
from ml.se_brl.codebook import load_codebook
from ml.se_brl.extraction import RuleEngine, unavailable_technical_extraction
from ml.se_brl.representation import BrlRepresentation


def notebook_aggregation():
    path=Path(__file__).resolve().parents[2]/"experiments/notebooks/04_feature_extraction.ipynb"
    document=json.loads(path.read_text(encoding="utf-8"))
    wanted={"derive_dimension_state", "encode_dimension_state"}
    nodes=[]
    for cell in document["cells"]:
        if cell["cell_type"] == "code":
            nodes.extend(n for n in ast.parse("".join(cell["source"])).body
                if isinstance(n,ast.FunctionDef) and n.name in wanted)
    assert {n.name for n in nodes} == wanted and len(nodes)==2
    scope={"__builtins__":{k:v for k,v in {"bool":bool,"any":any,"zip":zip,"ValueError":ValueError}.items()}}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),"exec"),scope)
    return scope["derive_dimension_state"],scope["encode_dimension_state"]


@pytest.mark.parametrize("raw", [
    {"kind":"email","subject":"Act now. Send your password."},
    {"kind":"email","subject":"Meeting notes."},
    {"kind":"email","subject":""},
    {"kind":"webpage","visible_text":"Limited offer. Click here."},
    {"kind":"webpage","html":"<p>Meeting notes.</p>"},
])
def test_fully_evaluated_and_unavailable_dimensions_agree(raw):
    derive,encode=notebook_aggregation()
    representation=BrlRepresentation(RuleEngine().extract(preprocess(raw)))
    indicators=representation.extraction.indicators
    assert len(indicators)==12
    row={}
    for i in indicators:
        row[i.indicator_id+"_available"]=i.evaluation_status=="rule_evaluated"
        row[i.indicator_id+"_supported"]=i.evidence_state=="supported"
    dimensions=load_codebook()["vector_ordering"]["dimension_order"]
    assert len(dimensions)==4
    slots=representation.deterministic_slots
    for n,d in enumerate(dimensions):
        selected=[i for i in indicators if i.dimension_id==d]
        if all(i.evaluation_status in {"rule_evaluated","unavailable"} for i in selected):
            assert encode(derive(row,[i.indicator_id for i in selected]))==(slots[n],slots[n+4])


@pytest.mark.parametrize("supported", [False,True])
def test_all_twelve_identifiers_pass_through_notebook_dimension_contract(supported):
    derive,encode=notebook_aggregation()
    for dimension in load_codebook()["dimensions"]:
        ids=[i["id"] for i in dimension["indicators"]]
        for selected in ids:
            row={i+"_available":True for i in ids}
            row.update({i+"_supported":supported and i==selected for i in ids})
            assert encode(derive(row,ids))==(int(supported),1)


def test_missing_technical_evidence_never_becomes_absence():
    derive,encode=notebook_aggregation()
    representation=BrlRepresentation(unavailable_technical_extraction("engineered_technical_record"))
    assert representation.deterministic_slots==(0,)*8
    for dimension in load_codebook()["dimensions"]:
        ids=[i["id"] for i in dimension["indicators"]]
        row={i+suffix:False for i in ids for suffix in ("_available","_supported")}
        assert derive(row,ids)=="Unavailable" and encode(derive(row,ids))==(0,0)


def test_pending_partial_evaluation_difference_remains_visible():
    derive,_=notebook_aggregation()
    representation=BrlRepresentation(RuleEngine(rules=()).extract(preprocess({"kind":"email","subject":"Observe."})))
    assert representation.deterministic_slots[0] is None
    dimension=load_codebook()["dimensions"][0]
    ids=[i["id"] for i in dimension["indicators"]]
    row={i+"_available":True for i in ids}
    row.update({i+"_supported":False for i in ids})
    assert derive(row,ids)=="Absent"  # P6/P7 decision required before equivalence.
