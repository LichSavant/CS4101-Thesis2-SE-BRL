import copy
import hashlib
import json
from pathlib import Path

import pytest

from ml import notebook_sources as sources


def fixture(tmp_path, cell, **extra):
    path = tmp_path / "opaque.fixture"
    path.write_text(json.dumps({"nbformat": 4, "cells": [cell], **extra}))
    return path


def digest(document):
    content = {k: v for k, v in document.items() if k != "code_order_sha256"}
    document["code_order_sha256"] = hashlib.sha256(json.dumps(content, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@pytest.mark.parametrize("source", ["x = 1\n", ["x = ", "1\n"]])
def test_only_code_source_decoded_even_when_source_precedes_type(tmp_path, monkeypatch, source):
    secret = "NEVER_DECODE_RETAINED_VALUE"
    path = fixture(tmp_path, {"source": source, "outputs": [{"source": secret, "data": {"text/plain": secret}}],
                              "cell_type": "code", "metadata": {"private": secret}, "execution_count": 99},
                   metadata={"private": secret})
    original = json.loads
    calls = []
    def checked(value, *args, **kwargs):
        assert secret.encode() not in value
        calls.append(value)
        return original(value, *args, **kwargs)
    monkeypatch.setattr(sources.json, "loads", checked)
    before = path.read_bytes()
    projection = sources.extract_source(path)
    assert projection["cells"] == [{"index": 0, "cell_type": "code", "source": "x = 1\n"}]
    assert path.read_bytes() == before
    assert secret not in json.dumps(projection) and calls


@pytest.mark.parametrize("kind", ["markdown", "raw"])
def test_noncode_source_is_not_decoded(tmp_path, monkeypatch, kind):
    path = fixture(tmp_path, {"cell_type": kind, "source": "NEVER_DECODE_RETAINED_VALUE"})
    original = json.loads
    def checked(raw, *args, **kwargs):
        assert b"NEVER_DECODE_RETAINED_VALUE" not in raw
        return original(raw, *args, **kwargs)
    monkeypatch.setattr(sources.json, "loads", checked)
    assert sources.extract_source(path)["cells"] == [{"index": 0, "cell_type": kind}]


@pytest.mark.parametrize("raw", [
    '{"nbformat":4,"nbformat":4,"cells":[]}',
    '{"nbformat":4,"cells":[{"cell_type":"code","source":"","source":"x"}]}',
    '{"nbformat":4,"cells":[{"cell_type":"code","source":[1]}]}',
    '{"nbformat":true,"cells":[]}', '{"nbformat":3,"cells":[]}',
    '{"nbformat":4,"cells":[]} false', '{"nbformat":4,"cells":[],}',
    '{"nbformat":4,"cells":[{"cell_type":"code","source":"","outputs":[NaN]}]}',
    '{"nbformat":4,"cells":[{"cell_type":"code","source":"","outputs":["\\q"]}]}',
])
def test_ambiguous_or_malformed_sources_rejected(tmp_path, raw):
    path = tmp_path / "opaque.fixture"
    path.write_text(raw)
    with pytest.raises(sources.SourceProjectionError):
        sources.extract_source(path)


def test_symlink_source_rejected(tmp_path):
    path = fixture(tmp_path, {"cell_type": "code", "source": "x=1"})
    alias = tmp_path / "alias.fixture"
    alias.symlink_to(path)
    with pytest.raises(sources.SourceProjectionError):
        sources.extract_source(alias)


@pytest.fixture
def projection():
    path = Path(__file__).resolve().parents[2] / "experiments/notebook-sources/01_data_audit.source.json"
    return json.loads(path.read_text())


@pytest.mark.parametrize("mutation", ["conditional", "side_effect", "wrong_stage", "reordered", "output", "unchecked_csv", "unchecked_arff", "absent", "drift"])
def test_projection_guard_and_loader_mutations_fail_closed(projection, mutation):
    document = copy.deepcopy(projection)
    if mutation == "conditional":
        document["cells"][0]["source"] = 'if False:\n    require_stage_authorization("preprocessing")'
    elif mutation == "side_effect": document["cells"][0]["source"] = 'open("unsafe", "w")\n' + document["cells"][0]["source"]
    elif mutation == "wrong_stage": document["cells"][0]["source"] = document["cells"][0]["source"].replace('"preprocessing"', '"training"')
    elif mutation == "reordered": document["cells"][2]["index"] = 1
    elif mutation == "output": document["cells"][0]["outputs"] = ["private"]
    elif mutation == "unchecked_csv": document["cells"][2]["source"] = 'pd.read_csv("fixture")'
    elif mutation == "unchecked_arff": document["cells"][2]["source"] = 'arff.loadarff("fixture")'
    elif mutation == "absent": document["cells"] = []
    elif mutation == "drift": document["cells"][2]["source"] += '\n# modified\n'
    if mutation != "drift": digest(document)
    with pytest.raises(sources.SourceProjectionError):
        sources.verify_projection(document)


def test_all_five_guards_closed_and_historical_invalid_cell_reported():
    root = Path(__file__).resolve().parents[2] / "experiments/notebook-sources"
    documents = [json.loads(p.read_text()) for p in sorted(root.glob("*.source.json"))]
    assert len(documents) == 5
    results = [sources.verify_projection(d) for d in documents]
    assert sum(r["cell_count"] for r in results) == 410
    assert sum(r["code_cell_count"] for r in results) == 273
    assert [r["historical_syntax_issues"] for r in results] == [[{"cell": 16, "line": 3, "reason": "historical_non_python_code_cell"}], [], [], [], []]
    from ml.research_policy import require_stage_authorization, ResearchPolicyError
    for result in results:
        with pytest.raises(ResearchPolicyError, match="blocked"):
            require_stage_authorization(result["stage"])
