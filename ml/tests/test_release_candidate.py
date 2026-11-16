"""No-fit release contracts; all dossiers/engine seams are synthetic/inert."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ml.experiment_inputs import InputContractError
from ml.metadata import canonical_json, fingerprint
from ml.research_protocol import verify_accepted_run, specification_record, fit_estimate
from ml.research_execution import launch, benchmark_outer_models
from ml.run_preflight import candidate_budget_report, verified_run_report
from ml.tests.test_research_protocol import fixture_packet


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def ablation_packet(root, omitted=('Redirect',)):
    protocol, receipt, _, run_id, dataset, settings = fixture_packet(root)
    settings=replace(settings,omitted_features=omitted)
    (protocol/'experiment.json').write_text(canonical_json(specification_record(settings)))
    receipt['boundary']='E-development-ablation-only'
    receipt['evidence_sha256']['experiment.json']=digest(protocol/'experiment.json')
    (protocol/'acceptance.json').write_text(canonical_json(receipt))
    return protocol,receipt,digest(protocol/'acceptance.json'),run_id,dataset,settings


def test_exact_ablation_admission_dry_run_and_readback_are_separate(tmp_path,monkeypatch):
    protocol,receipt,sha,run_id,dataset,settings=ablation_packet(tmp_path)
    def forbidden(*a,**k): pytest.fail('Dry run invoked experiment engine')
    monkeypatch.setattr('ml.research_execution.run_research_nested_cv',forbidden)
    with pytest.raises(InputContractError):verify_accepted_run(tmp_path,run_id,expected_authorization_sha256=sha)
    summary=launch(tmp_path,run_id,expected_authorization_sha256=sha,purpose='ablation')
    report=summary['dry_run']
    assert report['execution_scope']=='E-development-ablation-only'
    assert report['omitted_features']==['Redirect'] and report['feature_dictionaries']['U1']==['URL_Length']
    assert report['expected_fits']=={'base_fits':105,'calibration_fits':5}
    assert report['model_fits']==0 and report['measured_runtime_seconds'] is None
    output=protocol.parent.parent/receipt['output_run_id'];assert not output.exists()
    output.mkdir();(output/'run_manifest.json').write_text('INERT existence fixture; not model state')
    context,loaded,specification=verify_accepted_run(tmp_path,run_id,expected_authorization_sha256=sha,purpose='ablation-readback')
    assert context._state['readback_only']
    with pytest.raises(InputContractError):context.bind(loaded,specification)


@pytest.mark.parametrize('omitted',[(),('unknown',),('URL_Length','Redirect')])
def test_invalid_ablation_never_calls_engine_or_creates_output(tmp_path,monkeypatch,omitted):
    protocol,receipt,sha,run_id,_,_=ablation_packet(tmp_path,omitted)
    monkeypatch.setattr('ml.research_execution.run_research_nested_cv',lambda *a,**k:pytest.fail('Invalid ablation reached engine'))
    with pytest.raises(InputContractError):launch(tmp_path,run_id,expected_authorization_sha256=sha,purpose='ablation',execute=True)
    assert not (protocol.parent.parent/receipt['output_run_id']).exists()


@pytest.mark.parametrize('change',['branch','dictionary','target','group','fold','source','scope','collision'])
def test_verified_preflight_rejects_changed_contracts(tmp_path,change):
    protocol,receipt,sha,run_id,dataset,settings=fixture_packet(tmp_path)
    context,_,_=verify_accepted_run(tmp_path,run_id,expected_authorization_sha256=sha)
    if change=='branch':context=replace(context,branch='Email')
    elif change=='dictionary':dataset=replace(dataset,specification=replace(dataset.specification,feature_dictionary_reference='changed'))
    elif change=='source':context=replace(context,sources_by_id={})
    elif change=='scope':context._state['readback_only']=True
    elif change=='collision':(protocol.parent.parent/receipt['output_run_id']).mkdir()
    else:
        row=dataset.observations[0]
        values={'target':{'target':1-row.target},'group':{'group_id':'changed'},'fold':{'fold':2}}[change]
        dataset=replace(dataset,observations=(replace(row,**values),)+dataset.observations[1:])
    with pytest.raises(InputContractError):verified_run_report(tmp_path,context,dataset,settings)


def test_budget_matches_current_candidate_and_estimator_without_fit():
    report=candidate_budget_report(Path(__file__).resolve().parents[2])
    assert report['expected_fits']=={'base_fits':98080,'calibration_fits':160}
    assert report['recorded_estimate_matches'] and report['research_execution_authorized'] is False
    assert {k:v['candidates'] for k,v in report['families'].items()}=={'logistic_regression':8,'linear_svm':8,'random_forest':72,'xgboost':64}
    assert report['runtime_seconds'] is report['storage_bytes'] is report['output_directory'] is None


def test_result_scope_rejects_cross_evidence_substitution(tmp_path):
    _,_,sha,run_id,_,_=ablation_packet(tmp_path)
    context,_,_=verify_accepted_run(tmp_path,run_id,expected_authorization_sha256=sha,purpose='ablation')
    result=dict(result_category='RESEARCH RESULT',research_execution='AUTHORIZED DEVELOPMENT ONLY',
        authorization_sha256=context.authorization_sha256,input_fingerprint=context.input_fingerprint,
        accepted_specification_fingerprint=context.specification_fingerprint,base_fits=105,calibration_fits=5,
        execution_scope='E-development-ablation-only')
    context.verify_result(result)
    for scope in ('E-development-fitting-only','E-development-diagnostic-only',None):
        with pytest.raises(InputContractError):context.verify_result(dict(result,execution_scope=scope))


def test_ablation_benchmark_uses_only_retained_columns(tmp_path,monkeypatch):
    _,_,sha,run_id,dataset,_=ablation_packet(tmp_path)
    context,_,_=verify_accepted_run(tmp_path,run_id,expected_authorization_sha256=sha,purpose='ablation')
    calls=[]
    def benchmark(classifier,rows,**kwargs):
        assert len(rows[0])==1
        calls.append(rows)
        return dict(p95_batch_ms=1.,p50_batch_ms=1.,throughput_artifacts_per_second=1.,serialized_model_bytes=1,
            measured_memory_bytes_max=None,timed_batch_seconds=[])
    monkeypatch.setattr('ml.inference_benchmark.benchmark_research_model',benchmark)
    monkeypatch.setattr('ml.model_persistence.serialized_fold_bytes',lambda *_:1)
    fitted=tuple(('U1',fold,SimpleNamespace(feature_names=('URL_Length',)),None,None) for fold in range(1,6))
    benchmark_outer_models(fitted,dataset,context)
    assert len(calls)==5


def test_e1_e2_e3_dry_run_has_one_population_fold_and_source_identity(tmp_path):
    from ml.tests.test_development_experiments import fixture_rows,spec
    from ml.development_experiments import build_development_dataset
    from ml.tests.test_experiment_engine import spec as experiment_spec
    from ml.development_runner import dataset_fingerprint
    _,_,sha,run_id,_,_=fixture_packet(tmp_path)
    base,_,_=verify_accepted_run(tmp_path,run_id,expected_authorization_sha256=sha)
    rows,vectors=fixture_rows()
    dictionary=spec()
    # Numeric fixture dictionary avoids any learned text transform.
    from ml.development_experiments import FeatureColumn
    dictionary=replace(dictionary,conventional=(FeatureColumn('length','numeric'),))
    dataset=build_development_dataset(rows,vectors,specification=dictionary)
    settings=replace(experiment_spec(configs=('E1','E2','E3')),protocol_reference='research:synthetic-alignment')
    context=replace(base,branch='Email',input_fingerprint=dataset_fingerprint(dataset),
        specification_fingerprint=fingerprint(specification_record(settings)),expected_fits=fit_estimate(settings),
        sources_by_id={r['observation_id']:r['source_dataset'] for r in rows})
    result=verified_run_report(tmp_path,context,dataset,settings)
    assert len(set(result['alignment_sha256'].values()))==1
    assert result['feature_dictionaries']['E3']==result['feature_dictionaries']['E1']+result['feature_dictionaries']['E2']
    assert len(result['feature_dictionaries']['E2'])==8


def test_ablation_cannot_enter_principal_family_selection(tmp_path):
    from ml.model_selection import SelectionPolicy,select_research_family
    _,_,sha,run_id,_,_=ablation_packet(tmp_path)
    context,_,_=verify_accepted_run(tmp_path,run_id,expected_authorization_sha256=sha,purpose='ablation')
    p=context.selection_record['policy']
    policy=SelectionPolicy(tuple(p['families']),p['configuration'],p['delta_pr'],p['resamples'],p['confidence'],p['seed'],
        p['hard_limits'],p['memory_evidence'],tuple(p['calibration_order']),tuple(p['efficiency_order']),p['protocol_reference'])
    with pytest.raises(InputContractError,match='principal_model_selection_scope_required'):
        select_research_family({f:{} for f in policy.families},policy,execution_contexts={f:context for f in policy.families})


def test_inert_ablation_launcher_reuses_persistence_and_reload(tmp_path,monkeypatch):
    protocol,receipt,sha,run_id,_,_=ablation_packet(tmp_path)
    order=[]
    def engine(dataset,specification,*,execution_context):
        order.append('engine')
        assert specification.omitted_features==('Redirect',)
        return dict(base_fits=105,calibration_fits=5,execution_scope=execution_context._state['boundary']),()
    monkeypatch.setattr('ml.research_execution.run_research_nested_cv',engine)
    monkeypatch.setattr('ml.research_execution.research_summaries',lambda *a:{'synthetic_contract_fixture':True})
    monkeypatch.setattr('ml.research_execution.benchmark_outer_models',lambda *a:{'synthetic_contract_fixture':True})
    def writer(path,*a,**k):
        order.append('write');path.mkdir();return 'a'*64
    def reader(*a,**k):order.append('reload');return {},()
    monkeypatch.setattr('ml.research_execution.write_nested_bundle',writer)
    monkeypatch.setattr('ml.research_execution.load_nested_bundle',reader)
    result=launch(tmp_path,run_id,expected_authorization_sha256=sha,purpose='ablation',execute=True)
    assert order==['engine','write','reload']
    assert result['dry_run']['execution_scope']=='E-development-ablation-only'
    assert result['status']=='authorized_development_run_completed'
