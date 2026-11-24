"""Synthetic delivery fixtures; no research acceptance or fitting."""
import csv
import hashlib
import json

import pytest

from scripts.phiusiil_development_delivery import FEATURES, REGISTER, numeric, produce
from scripts.phiusiil_reconcile import digest


@pytest.mark.parametrize('text', ['', 'NaN', 'Infinity', '0.5', 'unknown'])
def test_missing_or_nonintegral_features_are_not_imputed(text):
    with pytest.raises(ValueError):
        numeric(text)


def fixture(tmp_path):
    root=tmp_path/'checkout';root.mkdir()
    (root/'ml').mkdir();(root/'ml/synthetic.py').write_text('# synthetic fixture only\n')
    register=root/REGISTER;register.parent.mkdir(parents=True)
    register.write_text('Synthetic implementation choices; no acceptance or signatures.\n')
    meta=register.parent/'phiusiil/official-metadata.json';meta.parent.mkdir()
    meta.write_text(json.dumps({'data':{'variables':[{'name':n,'role':'Feature','type':'Integer'} for n in FEATURES]}}))
    source=tmp_path/'original.csv'
    header=[*FEATURES,'label']
    rows=[[str(i+1)]*len(FEATURES)+[str(i%2)] for i in range(10)]
    with source.open('w',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(header);writer.writerows(rows)
    reconciliation=tmp_path/'prior';reconciliation.mkdir()
    assignments=[];lineage=[]
    for i,row in enumerate(rows):
        assignments.append({'observation_id':f'PhiUSIIL::{i}','source_dataset':'PhiUSIIL','target':1-i%2,
            'group_id':f'g{i}','partition':'development','cv_fold':i//2+1})
        lineage.append({'observation_id':f'PhiUSIIL::{i}','original_position_candidate':i,
            'original_cells_sha256':hashlib.sha256(json.dumps(row,ensure_ascii=True,separators=(',',':')).encode()).hexdigest(),
            'status':'exact_cell_and_target_match'})
    normalized=reconciliation/'development_assignments.normalized.csv'
    with normalized.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,assignments[0]);writer.writeheader();writer.writerows(assignments)
    ledger=reconciliation/'development_lineage.candidate.jsonl'
    ledger.write_text(''.join(json.dumps(r)+'\n' for r in lineage))
    receipt=reconciliation/'reconciliation_receipt.json'
    receipt.write_text(json.dumps({'input_sha256':{'original':digest(source)},'development_assignment_rows':10,
        'numeric_representation_evidence_sha256':digest(meta),
        'output_sha256':{p.name:digest(p) for p in (normalized,ledger)}}))
    (register.parent/'d-features-delivery-status.json').write_text(json.dumps({'latest_reconciliation':{'receipt_sha256':digest(receipt)}}))
    return root,source,reconciliation


def test_real_contract_subset_and_aliases_without_manufactured_acceptance(tmp_path):
    root,source,prior=fixture(tmp_path)
    out=tmp_path/'delivery'
    result=produce(root,source,prior,out)
    assert result['genuine_feature_records']==10 and result['predictor_count']==10
    assert result['no_fit_admission']=='BLOCKED' and result['fits']==0
    assert not (out/'protocol/feature_acceptance.json').exists()
    rows=json.loads((out/'data/development/phiusiil_records.json').read_bytes())
    assert all(r['observation_id'].startswith('source-v1-') for r in rows)
    assert all('FILENAME' not in r and 'URL' not in r and 'Domain' not in r for r in rows)
    aliases=[json.loads(line) for line in (out/'historical_id_aliases.jsonl').read_text().splitlines()]
    assert {r['historical_observation_id'] for r in aliases}=={f'PhiUSIIL::{i}' for i in range(10)}
    assert result['fitting_gate']=='research_fitting_not_authorized'
    with pytest.raises(FileExistsError):
        produce(root,source,prior,out)


def test_altered_upstream_source_fails_before_output(tmp_path):
    root,source,prior=fixture(tmp_path)
    source.write_bytes(source.read_bytes()+b'0,changed\n')
    with pytest.raises(ValueError,match='original_source_changed'):
        produce(root,source,prior,tmp_path/'delivery')
    assert not (tmp_path/'delivery').exists()
