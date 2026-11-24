"""Synthetic orchestration only: no estimator fits or researcher approvals."""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from ml import comparison_batch as batch
from ml.development_runner import ScoreBatch,dataset_fingerprint
from ml.experiment_inputs import InputContractError
from ml.preflight import require_research_fitting
from ml.research_protocol import code_hashes
from ml.tests.test_fixed_baseline import fixture as baseline_fixture


def fixture(tmp_path):
    dataset,_=baseline_fixture(tmp_path)
    request=json.loads((Path(__file__).resolve().parents[2]/batch.REQUEST).read_bytes())
    batch.validate_request(request)
    request['input_fingerprint']=dataset_fingerprint(dataset)
    (tmp_path/'ml').mkdir()
    (tmp_path/'ml/synthetic.py').write_text('# Synthetic test identity only\n')
    ctx=batch.VerifiedComparison(tmp_path,'a'*64,request,code_hashes(tmp_path),batch._TOKEN)
    ctx.bind(dataset)
    return dataset,ctx


class SyntheticSpy:
    calls=[]
    def __init__(self,dictionary,model,preprocessing,subset):self.family=model.family
    def fit(self,rows,labels,**kwargs):
        assert len(rows)==8 and len(labels)==8 and kwargs['seed']==42
        self.calls.append(self.family)
        return self
    def score(self,rows,*,observation_ids):
        assert len(rows)==2
        margin=self.family=='linear_svm'
        return ScoreBatch(observation_ids,(-.2,.2) if margin else (.2,.8),'margin' if margin else 'probability',1)
    def audit_record(self):return {'category':'synthetic spy; no estimator fit'}


def test_missing_authority_never_loads_data(tmp_path,monkeypatch):
    monkeypatch.setattr(batch,'load_development_dataset',lambda *a,**k:pytest.fail('no data read'))
    with pytest.raises(InputContractError,match='acceptance_missing'):batch.verify_authorization(tmp_path)


def test_LR_authority_cannot_extend_scope(tmp_path):
    path=tmp_path/batch.AUTHORIZATION;path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'version':'phiusiil-fixed-uncalibrated-fitting-1'}))
    with pytest.raises(InputContractError,match='not_LR_authority'):batch.verify_authorization(tmp_path)


def test_three_families_five_folds_and_resume_without_refitting(tmp_path):
    dataset,ctx=fixture(tmp_path);SyntheticSpy.calls=[]
    for model in ctx.request['models']:
        result=batch.run_model(dataset,ctx,model,classifier_type=SyntheticSpy)
        assert len(result['predictions'])==10 and result['pooled_metrics']['f1']==1
        assert result['base_fits']==5 and result['calibration_fits']==0
        directory=tmp_path/model['family']
        batch.save_model(directory,result,ctx)
        assert batch.completed_model(directory,model,ctx)['pooled_metrics']==result['pooled_metrics']
    assert SyntheticSpy.calls==[f for f in batch.FAMILIES for _ in range(5)]
    with pytest.raises(InputContractError,match='budget'):
        batch.run_model(dataset,ctx,ctx.request['models'][0],classifier_type=SyntheticSpy)
    path=tmp_path/'linear_svm/result.json';path.write_text('{}')
    with pytest.raises(InputContractError,match='outputs_changed'):
        batch.completed_model(path.parent,ctx.request['models'][0],ctx)


def test_forged_context_changed_settings_and_data_rejected(tmp_path):
    dataset,ctx=fixture(tmp_path)
    with pytest.raises(InputContractError):require_research_fitting(replace(ctx,_token=object()))
    with pytest.raises(InputContractError,match='bound_comparison_dataset'):
        batch.run_model(replace(dataset),ctx,ctx.request['models'][0],classifier_type=SyntheticSpy)
    altered=dict(ctx.request['models'][0]);altered['decision_threshold']=.5
    with pytest.raises(InputContractError,match='exact_fixed_family'):
        batch.run_model(dataset,ctx,altered,classifier_type=SyntheticSpy)
    with pytest.raises(InputContractError,match='cannot_authorize'):ctx.before_fit('calibration',8)


def test_partial_model_cannot_be_overwritten(tmp_path):
    _,ctx=fixture(tmp_path);directory=tmp_path/'partial';directory.mkdir()
    with pytest.raises(InputContractError,match='partial_model_output'):
        batch.completed_model(directory,ctx.request['models'][0],ctx)


def test_request_hash_and_candidate_grid_points():
    root=Path(__file__).resolve().parents[2]
    assert batch.digest(root/batch.REQUEST)==batch.REQUEST_SHA256
    request=json.loads((root/batch.REQUEST).read_bytes());batch.validate_request(request)
    assert [m['id'] for m in request['models']]==['linear_svm-004','random_forest-000','xgboost-000']
    source=json.loads((root/request['configuration_source']['path']).read_bytes())
    for model in request['models']:
        plan=next(p for p in source['plans'] if p['family']==model['family'])
        candidate=next(c for c in plan['runner_specification']['candidates'] if c['id']==model['id'])
        assert all(model[key]==candidate[key] for key in ('family','parameters','preprocessing','seed'))


def test_module_entrypoint_uses_canonical_context(monkeypatch):
    import runpy
    import warnings
    monkeypatch.setattr(batch,'main',lambda:17)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        with pytest.raises(SystemExit) as result:runpy.run_module('ml.comparison_batch',run_name='__main__')
    assert result.value.code==17
