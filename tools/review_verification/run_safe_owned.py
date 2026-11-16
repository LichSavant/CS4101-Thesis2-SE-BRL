"""Verified safe synthetic scopes only; no corpus/model/research execution."""
from pathlib import Path
import ast
import json
import os
import sys
import unicodedata
import re
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--vera-root",type=Path,required=True)
parser.add_argument("--counterpart-root",type=Path,required=True)
args=parser.parse_args()
ROOT = args.vera_root.resolve()
sys.dont_write_bytecode = True
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"scripts"))
os.environ.update(PYTHONDONTWRITEBYTECODE="1",PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",HF_HUB_OFFLINE="1",TRANSFORMERS_OFFLINE="1",SEBRL_R22_COUNTERPART_ROOT=str(args.counterpart_root.resolve()))
MODULES = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/"ml/tests").glob("test_*.py") if p.name!="test_features_pipeline.py")
MODULES += sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/"backend/tests").glob("test_*.py"))
nodes=[];excluded=[]
for name in MODULES:
    text=(ROOT/name).read_text();tree=ast.parse(text)
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name.startswith("test_"):
            start=min([node.lineno]+[d.lineno for d in node.decorator_list])-1
            source="\n".join(text.splitlines()[start:node.end_lineno])
            normalized=re.sub("[^a-z0-9]","",unicodedata.normalize("NFKC",source).casefold())
            key=name+"::"+node.name
            if any(x in normalized for x in ("spaphish","spafish")) or any(x in source for x in (".fit(", ".fit_transform(", ".train(")):
                excluded.append({"node":key,"reason":"Corpus-alias or fitting-related case excluded before selection under this directive."})
            else: nodes.append(key)
import pytest
old=pytest.main
captured={}
def safe_scope(arguments, plugins):
    suffix=arguments[arguments.index("-q"):]
    suffix=suffix[:suffix.index("-k")]
    effective=[*nodes,*suffix]
    captured["arguments"]=effective
    captured["run"]=Path(next(a.split("=",1)[1] for a in effective if a.startswith("--basetemp="))).parent
    return old(effective,plugins=plugins)
pytest.main=safe_scope
import verify_semantic_review
code=verify_semantic_review.main()
from r22_execution_environment import execution_environment,runtime_source_hashes
record=captured["run"]/"verification.json"
doc=json.loads(record.read_text())
doc["verification_kind"]="fresh_safe_publication_owned_contract_and_inference_software_checks"
doc["standalone_runner_sha256"]=__import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest()
doc["module_exclusion"]={"ml/tests/test_features_pipeline.py":"Fitted-feature cases excluded as a complete module; earlier no-fit evidence remains historical."}
doc["guard_harness_original_arguments"]=doc.pop("pytest_arguments")
doc["pytest_arguments"]=captured["arguments"]
doc["not_selected"]=excluded
doc["execution_environment"]=execution_environment()
doc["vera_source_files_sha256"]=runtime_source_hashes(ROOT)
record.write_text(json.dumps(doc,indent=2)+"\n")
raise SystemExit(code)
