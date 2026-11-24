"""Source/contract claims only; fixtures do not assert external integration."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from ml.preprocessing import normalize_text, preprocess
from ml.se_brl.runtime_compatibility import compare_runtime_declaration, parse_runtime_declaration, runtime_declaration


@pytest.fixture
def expected():
    return runtime_declaration(base_commit="25677a98236895ad16c6acf6aa75499dd2552fd9")


def peer(expected):
    # Fictitious peer identity solely for declaration-comparison tests.
    result=deepcopy(expected);result.update(base_commit="1"*40,source_state="committed")
    return result


def test_declaration_roundtrip_and_matching_claim_never_approve_integration(expected):
    assert parse_runtime_declaration(json.dumps(expected))==expected
    result=compare_runtime_declaration(expected,peer(expected))
    assert result["declaration_compatible"] and result["status"]=="DECLARATION_MATCH_INTEGRATION_PENDING"
    assert not result["checkout_independently_verified"] and not result["integration_accepted"] and not result["research_release"]
    assert compare_runtime_declaration(expected,None)["declaration_compatible"] is None


def test_equal_preprocessing_version_with_different_source_is_incompatible(expected):
    supplied=peer(expected)
    supplied["contracts"]["preprocessing"]["source_utf8_lf_sha256"]="0"*64
    assert supplied["contracts"]["preprocessing"]["version"]==expected["contracts"]["preprocessing"]["version"]
    result=compare_runtime_declaration(expected,supplied)
    assert not result["declaration_compatible"] and "contract:preprocessing" in result["mismatches"]


@pytest.mark.parametrize("field",["codebook","admission","normalization","taxonomy","input","output","representation","semantic_model","reference_validation","policy","source_files_utf8_lf_sha256"])
def test_each_contract_area_is_compared_exactly(expected,field):
    supplied=peer(expected);supplied["contracts"][field]={"unapproved":True}
    result=compare_runtime_declaration(expected,supplied)
    assert not result["declaration_compatible"] and "contract:"+field in result["mismatches"]


@pytest.mark.parametrize("mutate",[
    lambda d:d.update(target=1),lambda d:d.update(base_commit=None),lambda d:d.update(source_state="working_tree"),
    lambda d:d["research_release"].update(approved_for_E2_E3=True),
    lambda d:d["contracts"]["representation"]["learned_values"].__setitem__(0,0),
    lambda d:d["contracts"]["taxonomy"]["indicator_order"].reverse(),
    lambda d:d["contracts"]["representation"]["historical_binary_feature_order"].reverse(),
    lambda d:d["contracts"].update(hidden_fallback={"source":"unapproved"})])
def test_bookkeeping_fallback_ordering_and_premature_approval_are_rejected(expected,mutate):
    supplied=peer(expected);mutate(supplied)
    assert not compare_runtime_declaration(expected,supplied)["declaration_compatible"]


@pytest.mark.parametrize("payload",['{"a":1,"a":2}','{"a":NaN}','[]','[broken','['*2000+']'*2000,'{"a":"'+"x"*1_000_001+'"}'],
                         ids=["duplicate","nonfinite","array","malformed","deep","oversized"])
def test_runtime_parser_is_bounded_strict_and_nonexecuting(payload):
    with pytest.raises(ValueError):parse_runtime_declaration(payload)


def test_normalized_model_text_and_original_fields_have_distinct_contracts(expected):
    original="ＦＯＯ&nbsp;Bar\t BAZ"
    prepared=preprocess({"kind":"email","subject":original})
    assert normalize_text(original)==prepared.model_text=="foo bar baz"
    assert prepared.segments[0].text==original
    assert expected["contracts"]["normalization"]["known_empty_text"]==""
    assert expected["contracts"]["normalization"]["unknown"] is None
    assert expected["contracts"]["representation"]["learned_values"]==[None]*4


def test_expected_contract_cannot_self_approve_research(expected):
    expected["research_release"]["approved_for_E2_E3"]=True
    with pytest.raises(ValueError):compare_runtime_declaration(expected,peer(expected))


def test_runtime_emitter_refuses_an_unreviewed_admission_configuration(monkeypatch):
    from ml.se_brl import runtime_compatibility as module
    policy=module.load_policy();policy["approved_annotation_sources"]=["unapproved-source"]
    monkeypatch.setattr(module,"load_policy",lambda:policy)
    with pytest.raises(ValueError,match="closed_research_admission"):module.runtime_declaration()


def test_saved_local_declaration_binds_the_current_uncommitted_runtime(expected):
    saved=Path(__file__).parents[1]/"fixtures/runtime-compatibility-v1/declaration.local.json"
    assert parse_runtime_declaration(saved.read_text())==expected
    assert expected["source_state"]=="working_tree"
