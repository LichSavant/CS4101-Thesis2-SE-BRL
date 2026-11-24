"""Explicit synthetic metadata fixtures; no real acceptance or source records."""
from datetime import date, timedelta
from copy import deepcopy

import pytest

from scripts.review_phiusiil_c_acceptance import check_receipt


def sample():
    fixed={'version':'scoped-no-fit-preparation-1','stage':'C-allocation','branch':'PhiUSIIL',
           'output_run_id':'synthetic-output-only'}
    receipt={**fixed,'authority':{'name':'synthetic reviewer fixture','role':'researcher',
        'date':date.today().isoformat(),'response_reference':'synthetic test; not an attestation',
        'response_text':'Synthetic test metadata only; this is not human acceptance.'},
        'input_sha256':{'synthetic.json':'a'*64},'code_sha256':{'ml/synthetic.py':'b'*64},'access':{}}
    spec={'root_keys_exact':list(receipt),'fixed_values':fixed,
        'authority_exact_keys':list(receipt['authority']),'input_sha256_exact':receipt['input_sha256']}
    return receipt,spec


def test_structural_check_does_not_create_acceptance_or_execute():
    receipt,spec=sample();before=deepcopy(receipt)
    assert check_receipt(receipt,spec,receipt['code_sha256']) is None
    assert receipt==before


@pytest.mark.parametrize('mutation', ['extra_key','wrong_hash','wrong_scope','future_date','blank_response','wrong_code'])
def test_unbound_or_invalid_receipts_are_refused(mutation):
    receipt,spec=sample()
    actual_code=dict(receipt['code_sha256'])
    # Specification must not alias the field being deliberately mutated.
    spec=deepcopy(spec)
    if mutation=='extra_key':receipt['invented_signature']='synthetic'
    elif mutation=='wrong_hash':receipt['input_sha256']['synthetic.json']='c'*64
    elif mutation=='wrong_scope':receipt['stage']='D-features'
    elif mutation=='future_date':receipt['authority']['date']=(date.today()+timedelta(days=1)).isoformat()
    elif mutation=='blank_response':receipt['authority']['response_text']=''
    elif mutation=='wrong_code':actual_code['ml/synthetic.py']='d'*64
    with pytest.raises(ValueError):check_receipt(receipt,spec,actual_code)
