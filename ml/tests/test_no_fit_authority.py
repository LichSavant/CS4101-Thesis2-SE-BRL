"""Focused synthetic no-fit policy and selected-record boundary regressions."""
import json

import pytest

from ml.experiment_inputs import InputContractError
from ml import no_fit_authority as authority
from ml.scoped_json_records import object_spans, selected_rows


def test_source_index_handles_strings_and_never_decodes_reserved_record(tmp_path):
    path=tmp_path/'source.json'
    path.write_bytes(b'[{"observation_id":"a","text":"brace } and \\\" quote"},'
                     b'{"observation_id":"reserved","text":"\xff"},'
                     b'{"observation_id":"c","values":[{"n":1}]}]')
    spans=list(object_spans(path));assert len(spans)==3
    index=dict(zip(('a','reserved','c'),spans))
    rows=list(selected_rows(path,index,{'a','c'}))
    assert [r['observation_id'] for r in rows]==['a','c']
    assert rows[1]['values']==[{'n':1}]
    with pytest.raises(InputContractError,match='identity_changed'):
        list(selected_rows(path,{'wrong':spans[0]},{'wrong'}))


def fixture(monkeypatch):
    v={'researcher':'synthetic researcher','role':'researcher','date':'2026-11-18','message_verbatim':'Synthetic acceptance fixture only; no actual authority.'}
    policy={'joint_approval':{'Vera':{'path':'synthetic approval.json'}},'scope':{
        'C_input_run':'synthetic-input','C_output_run':'synthetic-output','C_input_sha256':{'population':'a'*64}}}
    monkeypatch.setattr(authority,'approved_policy',lambda root:(policy,v))
    receipt={'branch':'PhiUSIIL','output_run_id':'synthetic-output','input_sha256':{'population':'a'*64},
        'authority':{'name':v['researcher'],'role':v['role'],'date':v['date'],'response_reference':'synthetic approval.json','response_text':v['message_verbatim']},
        'access':{'researcher_controlled_policy':{'path':authority.POLICY_PATH,'sha256':authority.POLICY_SHA256}}}
    return receipt


def test_new_authority_is_exact_scope_not_boolean_approval(monkeypatch,tmp_path):
    receipt=fixture(monkeypatch)
    authority.validate_authority(tmp_path,receipt,'C-allocation','synthetic-input')
    receipt['access']={'approved':True}
    with pytest.raises(InputContractError,match='exact_recorded'):
        authority.validate_authority(tmp_path,receipt,'C-allocation','synthetic-input')


@pytest.mark.parametrize('mutation',['branch','stage','namespace','hash','response'])
def test_no_fit_policy_cannot_expand_scope(monkeypatch,tmp_path,mutation):
    receipt=fixture(monkeypatch);stage='C-allocation';run='synthetic-input'
    if mutation=='branch':receipt['branch']='Email'
    elif mutation=='stage':stage='fit'
    elif mutation=='namespace':run='other-input'
    elif mutation=='hash':receipt['input_sha256']={'population':'b'*64}
    else:receipt['authority']['response_text']='Invented acceptance is not recorded authority.'
    with pytest.raises(InputContractError):authority.validate_authority(tmp_path,receipt,stage,run)


def test_pinned_approval_evidence_cannot_be_rewritten(tmp_path):
    path=tmp_path/authority.POLICY_PATH;path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'approved':True}))
    with pytest.raises(InputContractError,match='evidence_changed'):
        authority.approved_policy(tmp_path)
