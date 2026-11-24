"""Synthetic orchestration/gate checks; all estimator fitting remains prohibited."""
from dataclasses import replace
import json
from pathlib import Path
from datetime import date

import pytest

from ml import fixed_baseline as baseline
from ml.preflight import require_research_fitting
from ml.experiment_inputs import InputContractError
from ml.development_experiments import (DevelopmentSpecification,FeatureColumn,
    build_development_dataset,behavioral_columns)
from ml.development_runner import ScoreBatch,dataset_fingerprint


def fixture(tmp_path):
    settings=json.loads((Path(__file__).resolve().parents[2]/baseline.REQUEST).read_bytes())['fixed_settings']
    rows=[];vectors=[]
    for fold in range(1,6):
        for target in (0,1):
            row={'observation_id':f'synthetic-{fold}-{target}','target':target,'source_dataset':'PhiUSIIL',
                'source_row_id':len(rows),'label':1-target,'group_id':f'g-{fold}-{target}',
                'partition':'development','cv_fold':fold}
            row.update({n:target+1 for n in settings['feature_columns']});rows.append(row)
            vectors.append({**{k:row[k] for k in ('observation_id','target','group_id','partition','cv_fold')},
                **dict.fromkeys(behavioral_columns(),0)})
    spec=DevelopmentSpecification('PhiUSIIL',tuple(FeatureColumn(n,'numeric') for n in settings['feature_columns']),'synthetic-only','synthetic-only')
    dataset=build_development_dataset(rows,vectors,specification=spec)
    ctx=baseline.VerifiedFixedBaseline(tmp_path,'a'*64,dataset_fingerprint(dataset),settings,{},baseline._TOKEN)
    return dataset,ctx


def test_missing_authorization_stops_before_dataset_loading(tmp_path,monkeypatch):
    monkeypatch.setattr(baseline,'load_development_dataset',lambda *a,**k:pytest.fail('data must not load'))
    with pytest.raises(InputContractError,match='acceptance_missing'):baseline.verify_authorization(tmp_path)


def test_forged_context_and_boolean_never_authorize_fitting(tmp_path):
    _,ctx=fixture(tmp_path)
    with pytest.raises(InputContractError):require_research_fitting(True)
    with pytest.raises(InputContractError):require_research_fitting(replace(ctx,_token=object()))


def test_exact_five_disjoint_folds_and_no_calibration(tmp_path):
    dataset,ctx=fixture(tmp_path);calls=[]
    class SyntheticSpy:
        def __init__(self,*args):self.training=None
        def fit(self,rows,labels,**kwargs):
            assert len(rows)==8 and len(labels)==8 and kwargs['seed']==42
            calls.append(kwargs);return self
        def score(self,rows,*,observation_ids):
            assert len(rows)==2
            return ScoreBatch(observation_ids,(.2,.8),'probability',1)
        def audit_record(self):return {'category':'synthetic spy; no estimator fit'}
    result=baseline.run_fixed(dataset,ctx,classifier_type=SyntheticSpy)
    assert len(calls)==5 and len(result['predictions'])==10
    assert result['base_fits']==5 and result['calibration_fits']==0
    with pytest.raises(InputContractError,match='used_or_data_changed'):
        baseline.run_fixed(dataset,ctx,classifier_type=SyntheticSpy)


def test_fold_budget_refuses_extra_or_repeated_fits(tmp_path):
    dataset,ctx=fixture(tmp_path);ctx.bind(dataset)
    ctx.before_fold(1,8)
    with pytest.raises(InputContractError,match='budget'):ctx.before_fold(1,8)
    with pytest.raises(InputContractError,match='budget'):ctx.before_fold(6,8)


def test_altered_data_cannot_use_verified_context(tmp_path):
    dataset,ctx=fixture(tmp_path)
    altered=replace(dataset,observations=tuple(replace(r,target=1-r.target) for r in dataset.observations))
    with pytest.raises(InputContractError,match='data_changed'):ctx.bind(altered)


def test_fixed_context_cannot_open_nested_or_calibration_scopes(tmp_path):
    dataset,ctx=fixture(tmp_path)
    with pytest.raises(InputContractError,match='nested_or_calibrated'):ctx.bind(dataset,object())
    with pytest.raises(InputContractError,match='only_authorizes'):ctx.before_fit('calibration',8)


def test_verified_fixed_settings_are_immutable(tmp_path):
    _,ctx=fixture(tmp_path)
    with pytest.raises(TypeError):ctx.settings['parameters']['C']=10.0
    with pytest.raises(TypeError):ctx.settings['calibration']='sigmoid'


def test_acceptance_reference_cannot_trigger_reserved_data_reads(tmp_path):
    path=tmp_path/baseline.AUTHORIZATION;path.parent.mkdir(parents=True)
    auth={'version':'phiusiil-fixed-uncalibrated-fitting-1','request_sha256':baseline.REQUEST_SHA256,
        'authority':{'name':'synthetic fixture','role':'researcher','date':date.today().isoformat(),
            'response_reference':'data/test/protected.json','response_text':'Synthetic fixture only; no actual researcher authorization.'},
        'code_sha256':{},'D_manifest_sha256':'a'*64,'output_run_id':'phiusiil-fixed-logreg-oof-v1'}
    path.write_text(json.dumps(auth))
    with pytest.raises(InputContractError,match='personal_acceptance_document_required'):
        baseline.verify_authorization(tmp_path)


def test_module_cli_dispatches_through_canonical_context_module(monkeypatch):
    import runpy
    import warnings
    monkeypatch.setattr(baseline,'main',lambda:17)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        with pytest.raises(SystemExit) as result:
            runpy.run_module('ml.fixed_baseline',run_name='__main__')
    assert result.value.code==17


def test_behavioral_csv_validates_codebook_once_not_per_observation(tmp_path,monkeypatch):
    import csv
    import hashlib
    from ml import development_experiments as development
    dataset,_=fixture(tmp_path)
    path=tmp_path/'synthetic_behavior.csv'
    fields=('observation_id','target','group_id','partition','cv_fold',*behavioral_columns())
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fields);writer.writeheader()
        writer.writerows({**dict(observation_id=r.observation_id,target=r.target,group_id=r.group_id,partition='development',cv_fold=r.fold),
                         **dict.fromkeys(behavioral_columns(),0)} for r in dataset.observations)
    original=development.behavioral_columns;calls=[]
    def counted():calls.append(1);return original()
    monkeypatch.setattr(development,'behavioral_columns',counted)
    rows=development._read_csv(path,hashlib.sha256(path.read_bytes()).hexdigest(),behavioral=True,specification=dataset.specification)
    assert len(rows)==10 and len(calls)==1


def test_classifier_matrix_uses_frozen_codebook_fields_and_preserves_bit_checks(tmp_path,monkeypatch):
    from ml import classifier_adapters as adapters
    dataset,ctx=fixture(tmp_path);s=ctx.settings
    original=adapters.behavioral_columns;calls=[]
    def counted():calls.append(1);return original()
    monkeypatch.setattr(adapters,'behavioral_columns',counted)
    model=adapters.ClassifierSpecification(s['family'],s['parameters'],42)
    prep=adapters.PreprocessingSpecification(**s['preprocessing'])
    classifier=adapters.FoldClassifier(dataset.specification,model,prep,'U1')
    classifier.feature_names=tuple(s['feature_columns'])
    matrix=classifier._matrix(tuple(r.conventional for r in dataset.observations))
    assert matrix.shape==(10,10) and len(calls)==1
    email=DevelopmentSpecification('Email',(FeatureColumn('length','numeric'),),'synthetic','synthetic')
    behavior=adapters.FoldClassifier(email,model,prep,'E2');behavior.feature_names=original()
    with pytest.raises(InputContractError,match='binary_behavioral'):
        behavior._matrix(((2,0,0,0,1,1,1,1),))
