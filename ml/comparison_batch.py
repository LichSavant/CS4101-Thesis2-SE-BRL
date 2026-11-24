"""Separately authorized fixed SVM/RF/XGBoost batch; LR is never refitted.

One dataset load, one immutable checkpoint per family. No calibration/search,
reserved data, implicit approval, or bypass of formal model-selection gates.
"""
import argparse
import csv
from dataclasses import dataclass,field
from datetime import date
import hashlib
import json
from pathlib import Path
import statistics
import threading
import time
import os

from ml.classifier_adapters import ClassifierSpecification,PreprocessingSpecification,FoldClassifier
from ml.development_experiments import DevelopmentSpecification,FeatureColumn,load_development_dataset,development_folds,_within
from ml.development_runner import dataset_fingerprint
from ml.evaluation_metrics import binary_metrics
from ml.execution_identity import verify_integrity_receipt,execution_identity
from ml.experiment_inputs import InputContractError
from ml.metadata import freeze_json,json_value,fingerprint
from ml.no_fit_authority import approved_policy
from ml.research_protocol import code_hashes,_read,_json


REQUEST='docs/research/2026-11-19_phiusiil_comparison_request.json'
REQUEST_SHA256='a513d557307b7f5d73e64c543703b7d158d8b5c9635efbf7d31244189237ac84'
AUTHORIZATION='docs/research/2026-11-19_phiusiil_comparison_fitting_authorization.json'
PERSONAL='docs/research/2026-11-19_phiusiil_comparison_personal_acceptance.json'
OUTPUT='experiments/runs/phiusiil-fixed-comparison-v1'
FAMILIES=('linear_svm','random_forest','xgboost')
METRICS=('precision','recall','f1','balanced_accuracy','average_precision')
_TOKEN=object()


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def compact_metrics(metrics):
    return {k:v for k,v in metrics.items() if k not in {'precision_recall_curve','reliability_bins'}}


def validate_request(request):
    if (tuple(m['family'] for m in request['models'])!=FAMILIES or request['additional_base_fits']!=15
            or request['calibration_fits']!=0 or request['hyperparameter_search'] is not False
            or request['threshold_optimization'] is not False or request['eligible_observations']!=115563
            or request['development_folds']!=5):
        raise InputContractError('exact_three_family_fixed_scope_required')
    for model in request['models']:
        ClassifierSpecification(model['family'],model['parameters'],model['seed'])
        PreprocessingSpecification(**model['preprocessing'])
        if (model['base_fits']!=5 or model['calibration_fits']!=0 or model['seed']!=42
                or model['decision_threshold']!=(0. if model['family']=='linear_svm' else .5)
                or model['score_kind']!=('margin' if model['family']=='linear_svm' else 'probability')):
            raise InputContractError('fixed_margin_probability_thresholds_required')


@dataclass(frozen=True,slots=True)
class VerifiedComparison:
    root:Path=field(repr=False)
    authorization_sha256:str
    request:dict=field(repr=False)
    code_sha256:dict=field(repr=False)
    _token:object=field(repr=False)
    _state:dict=field(default_factory=dict,repr=False,compare=False)

    def __post_init__(self):
        object.__setattr__(self,'request',freeze_json(self.request))
        object.__setattr__(self,'code_sha256',freeze_json(self.code_sha256))

    def require_verified(self):
        if self._token is not _TOKEN or code_hashes(self.root)!=self.code_sha256:
            raise InputContractError('exact_comparison_authority_or_code_required')

    def bind(self,dataset,specification=None):
        self.require_verified()
        if specification is not None or self._state or dataset_fingerprint(dataset)!=self.request['input_fingerprint']:
            raise InputContractError('comparison_context_used_or_dataset_changed')
        self._state.update(start=time.monotonic(),fits=set(),dataset=dataset)

    def check_budget(self):
        if not self._state or time.monotonic()-self._state['start']>self.request['budget']['max_total_seconds']:
            raise InputContractError('comparison_wall_time_budget_exceeded')

    def before_fold(self,family,fold,rows):
        self.require_verified();self.check_budget()
        key=(family,fold)
        if (family not in FAMILIES or fold not in range(1,6) or key in self._state['fits']
                or len(self._state['fits'])>=15 or rows>self.request['budget']['max_training_rows']):
            raise InputContractError('comparison_fit_scope_or_budget_exceeded')
        self._state['fits'].add(key)

    def before_fit(self,kind,rows):
        raise InputContractError('comparison_context_cannot_authorize_calibration_or_nested_fit')


def verify_authorization(root):
    root=Path(root).resolve();path=_within(root,AUTHORIZATION)
    if not path.is_file():raise InputContractError('exact_combined_comparison_acceptance_missing')
    body=path.read_bytes();auth=_json(body)
    keys={'version','request_sha256','authority','code_sha256','D_manifest_sha256','baseline_manifest_sha256','output_run_id'}
    if (set(auth)!=keys or auth['version']!='phiusiil-fixed-comparison-fitting-1'
            or auth['request_sha256']!=REQUEST_SHA256 or auth['output_run_id']!='phiusiil-fixed-comparison-v1'):
        raise InputContractError('comparison_authority_is_not_LR_authority')
    authority=auth['authority']
    if (not isinstance(authority,dict) or set(authority)!={'name','role','date','response_reference','response_text'}
            or any(type(v) is not str or not v.strip() for v in authority.values())
            or authority['role'] not in {'researcher','adviser'} or date.fromisoformat(authority['date'])>date.today()
            or len(authority['response_text'])<40 or authority['response_reference']!=PERSONAL):
        raise InputContractError('actual_dated_comparison_response_required')
    response_path=_within(root,PERSONAL)
    if response_path.stat().st_size>1_000_000:raise InputContractError('comparison_response_oversized')
    response=_json(response_path.read_bytes())
    if (response.get('decision')!='ACCEPT_FIXED_THREE_FAMILY_COMPARISON'
            or response.get('request_sha256')!=REQUEST_SHA256 or response.get('authority')!=authority):
        raise InputContractError('actual_recorded_combined_acceptance_required')
    request=_json(_read(_within(root,REQUEST),REQUEST_SHA256,1_000_000));validate_request(request)
    code=code_hashes(root)
    if not code or auth['code_sha256']!=code:raise InputContractError('accepted_comparison_code_changed')
    if (auth['D_manifest_sha256']!=request['D_manifest_sha256']
            or auth['baseline_manifest_sha256']!=request['baseline']['manifest_sha256']):
        raise InputContractError('comparison_input_or_baseline_identity_changed')
    policy,_=approved_policy(root)
    croot=_within(root,'experiments/runs/'+policy['scope']['C_output_run'])
    droot=_within(root,'experiments/runs/'+policy['scope']['D_output_run'])
    verify_integrity_receipt(croot,expected_sha256=request['C_completion_sha256'])
    verify_integrity_receipt(droot,expected_sha256=request['D_completion_sha256'])
    _read(_within(root,request['D_manifest_path']),request['D_manifest_sha256'],1_000_000)
    _read(_within(root,request['baseline']['manifest_path']),request['baseline']['manifest_sha256'],1_000_000)
    prediction=_within(root,request['baseline']['run']+'/oof_predictions.csv')
    if digest(prediction)!=request['baseline']['prediction_sha256']:raise InputContractError('existing_LR_predictions_changed')
    dictionary=_json((root/'experiments/runs'/policy['scope']['D_input_run']/'protocol/dictionary.json').read_bytes())
    spec=DevelopmentSpecification('PhiUSIIL',tuple(FeatureColumn(c['name'],c['kind']) for c in dictionary['conventional']),dictionary['protocol_reference'],dictionary['feature_dictionary_reference'])
    dataset=load_development_dataset(root,policy['scope']['D_output_run'],specification=spec)
    if len(dataset.observations)!=115563 or tuple(c.name for c in spec.conventional)!=tuple(request['feature_columns']):
        raise InputContractError('matched_comparison_population_and_predictors_required')
    # One baseline metadata join, no LR fitting or repeated feature loading.
    expected={r.observation_id:(r.target,r.group_id,r.fold) for r in dataset.observations}
    seen=set()
    with prediction.open(newline='') as stream:
        for r in csv.DictReader(stream):
            oid=r['observation_id']
            if oid in seen or expected.get(oid)!=(int(r['target']),r['group_id'],int(r['fold'])):
                raise InputContractError('LR_and_comparison_ID_group_fold_or_label_mismatch')
            seen.add(oid)
    if seen!=set(expected):raise InputContractError('LR_prediction_coverage_changed')
    return VerifiedComparison(root,hashlib.sha256(body).hexdigest(),request,code,_TOKEN),dataset


def run_model(dataset,context,model,*,classifier_type=FoldClassifier):
    from ml.preflight import require_research_fitting
    require_research_fitting(context)
    if not isinstance(context,VerifiedComparison):raise InputContractError('comparison_context_required')
    if context._state.get('dataset') is not dataset:raise InputContractError('bound_comparison_dataset_required')
    frozen=next((m for m in context.request['models'] if m['family']==model['family']),None)
    if frozen is None or freeze_json(model)!=frozen:raise InputContractError('exact_fixed_family_settings_required')
    classifier_spec=ClassifierSpecification(model['family'],model['parameters'],42)
    preprocessing=PreprocessingSpecification(**model['preprocessing'])
    predictions=[];reports=[];audits=[]
    for plan in development_folds(dataset,'U1'):
        context.before_fold(model['family'],plan.validation_fold,len(plan.training_ids))
        pipe=classifier_type(dataset.specification,classifier_spec,preprocessing,'U1');start=time.perf_counter()
        pipe.fit(plan.x_train,plan.y_train,feature_names=plan.feature_names,seed=42)
        scores=pipe.score(plan.x_validation,observation_ids=plan.validation_ids);context.check_budget()
        if scores.observation_ids!=plan.validation_ids or scores.score_kind!=model['score_kind']:
            raise InputContractError('exact_margin_or_probability_scores_required')
        metrics=binary_metrics(plan.y_validation,scores.scores,positive_label=1,threshold=model['decision_threshold'])
        reports.append({'fold':plan.validation_fold,'training_rows':len(plan.training_ids),'validation_rows':len(plan.validation_ids),
            'seconds':time.perf_counter()-start,'metrics':compact_metrics(metrics)})
        groups={r.observation_id:r.group_id for r in dataset.observations if r.fold==plan.validation_fold}
        predictions.extend({'observation_id':oid,'group_id':groups[oid],'fold':plan.validation_fold,'target':y,'score':score,
            'decision':int(score>=model['decision_threshold'])} for oid,y,score in zip(plan.validation_ids,plan.y_validation,scores.scores))
        audits.append(pipe.audit_record())
    if len(predictions)!=len(dataset.observations) or len({p['observation_id'] for p in predictions})!=len(predictions):
        raise InputContractError('exact_comparison_OOF_coverage_required')
    pooled=binary_metrics(tuple(p['target'] for p in predictions),tuple(p['score'] for p in predictions),positive_label=1,threshold=model['decision_threshold'])
    variability={}
    for metric in METRICS:
        values=[r['metrics'][metric] for r in reports]
        variability[metric]={'mean':statistics.mean(values) if all(v is not None for v in values) else None,
            'population_sd':statistics.pstdev(values) if all(v is not None for v in values) else None}
    return {'family':model['family'],'settings':json_value(model),'base_fits':5,'calibration_fits':0,
        'pooled_metrics':compact_metrics(pooled),'fold_reports':reports,'fold_variability':variability,
        'pipeline_audits':audits,'predictions':predictions}


def save_model(directory,result,context):
    context.require_verified();context.check_budget()
    if ({(result['family'],fold) for fold in range(1,6)}-context._state['fits']
            or result['base_fits']!=5 or result['calibration_fits']!=0):
        raise InputContractError('five_authorized_family_fits_required_before_save')
    directory.mkdir(exist_ok=False)
    with (directory/'oof_predictions.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,tuple(result['predictions'][0]));writer.writeheader();writer.writerows(result['predictions'])
    with (directory/'metrics.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,('scope',*METRICS));writer.writeheader()
        writer.writerows({'scope':'fold-'+str(r['fold']),**{m:r['metrics'][m] for m in METRICS}} for r in result['fold_reports'])
        writer.writerow({'scope':'pooled',**{m:result['pooled_metrics'][m] for m in METRICS}})
    summary={k:v for k,v in result.items() if k!='predictions'}
    (directory/'result.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    with (directory/'oof_predictions.csv').open(newline='') as stream:rows=list(csv.DictReader(stream))
    if compact_metrics(binary_metrics(tuple(int(r['target']) for r in rows),tuple(float(r['score']) for r in rows),positive_label=1,
            threshold=result['settings']['decision_threshold']))!=result['pooled_metrics']:
        raise InputContractError('saved_comparison_metrics_do_not_reproduce')
    manifest={'schema':'fixed-family-comparison-result-1','family':result['family'],'request_sha256':REQUEST_SHA256,
        'authorization_sha256':context.authorization_sha256,'input_fingerprint':context.request['input_fingerprint'],
        'identity':execution_identity(context.root,code_sha256=dict(context.code_sha256),settings_sha256=fingerprint(result['settings'])),
        'outputs':{p.name:digest(p) for p in directory.iterdir() if p.is_file()},'base_fits':5,'calibration_fits':0}
    # Completion marker is last: interruption never turns a partial result valid.
    with (directory/'completed.json').open('x',encoding='utf-8') as stream:json.dump(manifest,stream,indent=2)


def completed_model(directory,model,context):
    context.require_verified()
    if not directory.exists():return None
    if directory.is_symlink() or any(p.is_symlink() or p.is_dir() for p in directory.iterdir()):
        raise InputContractError('redirected_or_extra_model_outputs_forbidden')
    marker=directory/'completed.json'
    if not marker.is_file():raise InputContractError('partial_model_output_requires_explicit_recovery_no_overwrite')
    m=_json(marker.read_bytes())
    if (m['request_sha256']!=REQUEST_SHA256 or m['authorization_sha256']!=context.authorization_sha256
            or m['input_fingerprint']!=context.request['input_fingerprint'] or m['family']!=model['family']
            or m['identity']['code_sha256']!=context.code_sha256 or m['base_fits']!=5 or m['calibration_fits']!=0):
        raise InputContractError('completed_comparison_identity_changed')
    actual={p.name for p in directory.iterdir() if p.is_file() and p.name!='completed.json'}
    if actual!=set(m['outputs']) or any(digest(directory/n)!=h for n,h in m['outputs'].items()):
        raise InputContractError('completed_comparison_outputs_changed')
    result=_json((directory/'result.json').read_bytes())
    if freeze_json(result['settings'])!=freeze_json(model):raise InputContractError('completed_family_settings_changed')
    return result


def comparison_table(root,results,context):
    baseline=_json((context.root/context.request['baseline']['manifest_path']).read_bytes())
    combined=[{'family':'logistic_regression','pooled_metrics':baseline['pooled_metrics'],
        'fold_mean_AP':statistics.mean(f['metrics']['average_precision'] for f in baseline['fold_results']),
        'seconds':sum(f['seconds'] for f in baseline['fold_results'])}]
    combined.extend({'family':r['family'],'pooled_metrics':r['pooled_metrics'],
        'fold_mean_AP':r['fold_variability']['average_precision']['mean'],'seconds':sum(f['seconds'] for f in r['fold_reports'])} for r in results)
    with (root/'comparison.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,('family',*METRICS,'fold_mean_AP','fold_computation_seconds'));writer.writeheader()
        writer.writerows({'family':r['family'],**{m:r['pooled_metrics'][m] for m in METRICS},'fold_mean_AP':r['fold_mean_AP'],
            'fold_computation_seconds':r['seconds']} for r in combined)
    highest=max(r['pooled_metrics']['average_precision'] for r in combined)
    descriptive=[r['family'] for r in combined if r['pooled_metrics']['average_precision']==highest]
    text='# Fixed four-family exploratory comparison\n\nLogistic Regression was reused without refitting; additional families used identical admitted records and folds. '
    text+='Highest observed pooled AP: '+', '.join(descriptive)+'. This is descriptive point ranking, not the approved formal implementation-selection gate. '
    text+='Uncalibrated SVM fold margins may differ in scale; per-fold AP and mean AP accompany pooled AP. No significance, calibration, deployment, behavioral or Transformer claim.\n'
    (root/'comparison_results.md').write_text(text,encoding='utf-8')
    return combined


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    try:
        context,dataset=verify_authorization(root)
        if not args.execute:
            print(json.dumps({'status':'EXACT_COMBINED_AUTHORITY_VERIFIED','rows':len(dataset.observations),'fits':0}));return 0
        context.bind(dataset);out=_within(root,OUTPUT);out.mkdir(exist_ok=True)
        def timeout():
            print('Comparison wall-time budget exhausted; completed model checkpoints remain intact.',flush=True);os._exit(124)
        watchdog=threading.Timer(context.request['budget']['max_total_seconds'],timeout);watchdog.daemon=True;watchdog.start()
        try:
            from threadpoolctl import threadpool_limits
            results=[]
            with threadpool_limits(limits=1):
                for model in context.request['models']:
                    directory=out/model['family'];result=completed_model(directory,model,context)
                    if result is None:
                        print(json.dumps({'event':'model_started','family':model['family']}),flush=True)
                        result=run_model(dataset,context,model);save_model(directory,result,context)
                    else:print(json.dumps({'event':'verified_completed_model_skipped','family':model['family']}),flush=True)
                    results.append(result)
                    print(json.dumps({'family':model['family'],'metrics':{m:result['pooled_metrics'][m] for m in METRICS}}),flush=True)
            combined=comparison_table(out,results,context)
        finally:watchdog.cancel()
        print(json.dumps({'status':'COMPARISON_COMPLETE','output':OUTPUT,'LR_refitted':False,'families':[r['family'] for r in combined]}));return 0
    except (InputContractError,OSError,ValueError,KeyError,TypeError) as error:
        print(json.dumps({'status':'BLOCKED_OR_FAILED','reason':str(error),'no_unverified_result_claimed':True}));return 2


if __name__=='__main__':
    from ml.comparison_batch import main as canonical_main
    raise SystemExit(canonical_main())
