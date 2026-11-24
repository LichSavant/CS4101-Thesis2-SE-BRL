"""Exact-request, separately authorized five-fold baseline. No calibration/search.

The existing nested runner is unchanged. Missing actual fitting acceptance fails
before feature loading or classifier construction. Approval is not inferred from
methodological/no-fit decisions or a caller boolean.
"""
import argparse
import csv
from dataclasses import dataclass,field
from datetime import date
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

from ml.classifier_adapters import ClassifierSpecification,PreprocessingSpecification,FoldClassifier
from ml.development_experiments import (DevelopmentSpecification,FeatureColumn,
    load_development_dataset,development_folds,_within)
from ml.development_runner import dataset_fingerprint
from ml.evaluation_metrics import binary_metrics
from ml.experiment_inputs import InputContractError
from ml.execution_identity import verify_integrity_receipt
from ml.metadata import fingerprint,freeze_json,json_value
from ml.no_fit_authority import approved_policy
from ml.research_protocol import code_hashes,_read,_json


REQUEST='docs/research/2026-11-19_phiusiil_fixed_baseline_request.json'
REQUEST_SHA256='ecfb31e52af4f11d6f0ac480504361d618034151585eedba5a7ef59ab426687c'
AUTHORIZATION='docs/research/2026-11-19_phiusiil_fixed_baseline_fitting_authorization.json'
PERSONAL_ACCEPTANCE='docs/research/2026-11-19_phiusiil_fixed_baseline_personal_acceptance.json'
OUTPUT='experiments/runs/phiusiil-fixed-logreg-oof-v1'
_TOKEN=object()
METRICS=('precision','recall','f1','balanced_accuracy')


@dataclass(frozen=True,slots=True)
class VerifiedFixedBaseline:
    root:Path=field(repr=False)
    authorization_sha256:str
    input_fingerprint:str
    settings:dict=field(repr=False)
    code_sha256:dict=field(repr=False)
    _token:object=field(repr=False)
    _state:dict=field(default_factory=dict,repr=False,compare=False)

    def __post_init__(self):
        object.__setattr__(self,'settings',freeze_json(self.settings))
        object.__setattr__(self,'code_sha256',freeze_json(self.code_sha256))

    def require_verified(self):
        if self._token is not _TOKEN:
            raise InputContractError('fixed_baseline_fitting_not_authorized')
        if code_hashes(self.root)!=self.code_sha256:
            raise InputContractError('fixed_baseline_runtime_code_changed')

    def check_time(self):
        if self._state and time.monotonic()-self._state['start']>self.settings['candidate_budget']['max_seconds']:
            raise InputContractError('fixed_baseline_time_budget_exceeded')

    def bind(self,dataset,specification=None):
        self.require_verified()
        if specification is not None:
            raise InputContractError('fixed_context_cannot_authorize_nested_or_calibrated_run')
        if self._state or dataset_fingerprint(dataset)!=self.input_fingerprint:
            raise InputContractError('fixed_baseline_context_used_or_data_changed')
        self._state.update(start=time.monotonic(),folds=set())

    def before_fold(self,fold,rows):
        self.require_verified()
        if (not self._state or fold not in range(1,6) or fold in self._state['folds']
                or len(self._state['folds'])>=5 or rows>self.settings['candidate_budget']['max_training_rows']):
            raise InputContractError('fixed_baseline_fit_or_row_budget_exceeded')
        self.check_time()
        self._state['folds'].add(fold)

    def before_fit(self,kind,rows):
        raise InputContractError('fixed_context_only_authorizes_exact_development_folds')


def verify_authorization(root):
    root=Path(root).resolve()
    auth_path=_within(root,AUTHORIZATION)
    if not auth_path.is_file():
        raise InputContractError('exact_fixed_baseline_fitting_acceptance_missing')
    auth_body=auth_path.read_bytes();auth=_json(auth_body)
    required={'version','request_sha256','authority','code_sha256','D_manifest_sha256','output_run_id'}
    if (set(auth)!=required or auth['version']!='phiusiil-fixed-uncalibrated-fitting-1'
            or auth['request_sha256']!=REQUEST_SHA256 or auth['output_run_id']!='phiusiil-fixed-logreg-oof-v1'):
        raise InputContractError('exact_fixed_baseline_authorization_required')
    a=auth['authority']
    if (not isinstance(a,dict) or set(a)!={'name','role','date','response_reference','response_text'}
            or any(type(v) is not str or not v.strip() for v in a.values())
            or a['role'] not in {'researcher','adviser'} or date.fromisoformat(a['date'])>date.today()
            or len(a['response_text'])<40):
        raise InputContractError('actual_dated_fitting_response_required')
    # The real personal response is recorded separately; this exact-file receipt
    # must match it, not invent one. No such production response is generated here.
    if a['response_reference']!=PERSONAL_ACCEPTANCE:
        raise InputContractError('fixed_personal_acceptance_document_required')
    response_path=_within(root,PERSONAL_ACCEPTANCE)
    if response_path.stat().st_size>1_000_000:
        raise InputContractError('fixed_personal_acceptance_document_oversized')
    response=_json(response_path.read_bytes())
    if (response.get('request_sha256')!=REQUEST_SHA256 or response.get('authority')!=a
            or response.get('decision')!='ACCEPT_FIXED_UNCALIBRATED_FITTING'):
        raise InputContractError('recorded_exact_personal_fitting_acceptance_required')
    request=_json(_read(_within(root,REQUEST),REQUEST_SHA256,1_000_000))
    actual_code=code_hashes(root)
    if not actual_code or auth['code_sha256']!=actual_code:
        raise InputContractError('accepted_fixed_baseline_code_changed')
    policy,_=approved_policy(root)
    droot=_within(root,'experiments/runs/'+policy['scope']['D_output_run'])
    croot=_within(root,'experiments/runs/'+policy['scope']['C_output_run'])
    verify_integrity_receipt(croot,expected_sha256=request['data_admission']['C_completion_sha256'])
    verify_integrity_receipt(droot,expected_sha256=request['data_admission']['D_completion_sha256'])
    manifest=request['data_admission']['D_manifest_sha256']
    _read(_within(root,request['data_admission']['D_manifest_path']),manifest,1_000_000)
    if auth['D_manifest_sha256']!=manifest or _within(root,OUTPUT).exists():
        raise InputContractError('exact_development_input_and_unused_output_required')
    settings=request['fixed_settings']
    if (settings['base_fits']!=5 or settings['calibrator_fits']!=0 or settings['calibration']!='none'
            or settings['hyperparameter_search'] is not False or settings['threshold']!=.5):
        raise InputContractError('fixed_uncalibrated_scope_required')
    dictionary=_json((root/'experiments/runs'/policy['scope']['D_input_run']/'protocol/dictionary.json').read_bytes())
    specification=DevelopmentSpecification('PhiUSIIL',tuple(FeatureColumn(c['name'],c['kind']) for c in dictionary['conventional']),
        dictionary['protocol_reference'],dictionary['feature_dictionary_reference'])
    dataset=load_development_dataset(root,policy['scope']['D_output_run'],specification=specification)
    if len(dataset.observations)!=115563 or tuple(c.name for c in specification.conventional)!=tuple(settings['feature_columns']):
        raise InputContractError('exact_fixed_baseline_population_or_predictors_required')
    context=VerifiedFixedBaseline(root,hashlib.sha256(auth_body).hexdigest(),dataset_fingerprint(dataset),settings,actual_code,_TOKEN)
    return context,dataset


def run_fixed(dataset,context,*,classifier_type=FoldClassifier,progress=None):
    from ml.preflight import require_research_fitting
    require_research_fitting(context)
    if not isinstance(context,VerifiedFixedBaseline):raise InputContractError('fixed_baseline_context_required')
    context.bind(dataset)
    s=context.settings
    if tuple(c.name for c in dataset.specification.conventional)!=tuple(s['feature_columns']):
        raise InputContractError('fixed_baseline_predictor_order_changed')
    model=ClassifierSpecification(s['family'],s['parameters'],s['seed'])
    preprocessing=PreprocessingSpecification(**s['preprocessing'])
    predictions=[];fold_reports=[];audits=[]
    for plan in development_folds(dataset,'U1'):
        require_research_fitting(context)
        if set(plan.training_ids)&set(plan.validation_ids):raise InputContractError('fold_ID_leakage')
        context.before_fold(plan.validation_fold,len(plan.training_ids))
        # A new FoldClassifier owns a new training-fold-only StandardScaler and LR.
        classifier=classifier_type(dataset.specification,model,preprocessing,'U1')
        start=time.perf_counter()
        if progress:progress({'event':'fit_started','fold':plan.validation_fold})
        classifier.fit(plan.x_train,plan.y_train,feature_names=plan.feature_names,seed=s['seed'])
        if progress:progress({'event':'fit_completed','fold':plan.validation_fold})
        batch=classifier.score(plan.x_validation,observation_ids=plan.validation_ids)
        context.check_time()
        if batch.observation_ids!=plan.validation_ids or batch.score_kind!='probability':
            raise InputContractError('unaltered_raw_probability_predictions_required')
        metrics=binary_metrics(plan.y_validation,batch.scores,positive_label=1,threshold=.5)
        fold_reports.append({'fold':plan.validation_fold,'training_rows':len(plan.training_ids),
            'validation_rows':len(plan.validation_ids),'seconds':time.perf_counter()-start,'metrics':metrics})
        group_by_id={r.observation_id:r.group_id for r in dataset.observations if r.fold==plan.validation_fold}
        predictions.extend({'observation_id':oid,'group_id':group_by_id[oid],'fold':plan.validation_fold,
            'target':target,'raw_probability':score,'decision':int(score>=.5)}
            for oid,target,score in zip(plan.validation_ids,plan.y_validation,batch.scores))
        audits.append(classifier.audit_record())
    if len(predictions)!=len(dataset.observations) or len({p['observation_id'] for p in predictions})!=len(predictions):
        raise InputContractError('exact_once_OOF_coverage_required')
    if context._state['folds']!={1,2,3,4,5}:raise InputContractError('exact_five_fits_required')
    metrics=binary_metrics(tuple(p['target'] for p in predictions),tuple(p['raw_probability'] for p in predictions),positive_label=1,threshold=.5)
    aggregate={}
    for name in METRICS:
        values=[r['metrics'][name] for r in fold_reports]
        aggregate[name]={'fold_mean':statistics.mean(values) if all(v is not None for v in values) else None,
            'fold_population_sd':statistics.pstdev(values) if all(v is not None for v in values) else None,
            'defined_folds':sum(v is not None for v in values)}
    return {'category':'AUTHORIZED EXPLORATORY DEVELOPMENT RESULT','authorization_sha256':context.authorization_sha256,
        'request_sha256':REQUEST_SHA256,'settings':json_value(s),'input_fingerprint':context.input_fingerprint,
        'base_fits':5,'calibration_fits':0,'pooled_metrics':metrics,'fold_descriptives':aggregate,
        'fold_reports':fold_reports,'predictions':predictions,'pipeline_audits':audits,
        'limitations':'Historically exposed technical subset; no calibration, protected evaluation, behavioral or Transformer claim'}


def save_result(root,result,context):
    from ml.execution_identity import execution_identity
    context.require_verified();context.check_time()
    if (context._state.get('folds')!={1,2,3,4,5} or result.get('base_fits')!=5
            or result.get('calibration_fits')!=0 or result.get('authorization_sha256')!=context.authorization_sha256
            or result.get('input_fingerprint')!=context.input_fingerprint):
        raise InputContractError('completed_authorized_fivefold_result_required')
    out=_within(root,OUTPUT);out.mkdir(exist_ok=False)
    with (out/'oof_predictions.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,tuple(result['predictions'][0]));writer.writeheader();writer.writerows(result['predictions'])
    with (out/'metrics.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,('scope',*METRICS));writer.writeheader()
        writer.writerows({'scope':'fold-'+str(r['fold']),**{m:r['metrics'][m] for m in METRICS}} for r in result['fold_reports'])
        writer.writerow({'scope':'pooled',**{m:result['pooled_metrics'][m] for m in METRICS}})
    summary={k:v for k,v in result.items() if k!='predictions'}
    with (out/'result.json').open('x',encoding='utf-8') as stream:json.dump(summary,stream,indent=2)
    prose='# Exploratory PhiUSIIL baseline results\n\nFive uncalibrated, fixed logistic-regression development fits produced once-only out-of-fold predictions. '
    prose+='; '.join(m+'='+('undefined' if result['pooled_metrics'][m] is None else f'{result["pooled_metrics"][m]:.6f}') for m in METRICS)+'.\n\n'+result['limitations']+'.\n'
    (out/'baseline_results.md').write_text(prose,encoding='utf-8')
    identity=execution_identity(root,code_sha256=dict(context.code_sha256),settings_sha256=fingerprint(context.settings))
    # Specialized research manifest: never label model results software validation.
    manifest={'schema':'fixed-baseline-research-result-1','category':'AUTHORIZED EXPLORATORY DEVELOPMENT RESULT',
        'identity':identity,'actual_fitting_authorization_sha256':context.authorization_sha256,
        'request_sha256':REQUEST_SHA256,'input_fingerprint':context.input_fingerprint,
        'base_fits':5,'calibration_fits':0,
        'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}}
    body=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
    with (out/'reproducibility_manifest.json').open('xb') as stream:stream.write(body)
    with (out/'oof_predictions.csv').open(newline='') as stream:saved=list(csv.DictReader(stream))
    recomputed=binary_metrics(tuple(int(p['target']) for p in saved),tuple(float(p['raw_probability']) for p in saved),positive_label=1,threshold=.5)
    if recomputed!=result['pooled_metrics']:raise InputContractError('saved_baseline_metrics_do_not_reproduce')
    for name,want in manifest['outputs'].items():
        if hashlib.sha256((out/name).read_bytes()).hexdigest()!=want:raise InputContractError('saved_baseline_output_changed')
    return {'output':OUTPUT,'manifest_sha256':hashlib.sha256(body).hexdigest(),'base_fits':5,'calibration_fits':0,'metrics':result['pooled_metrics']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    try:
        context,dataset=verify_authorization(root)
        if args.execute:
            if not args.worker:
                # Enforce the declared wall-time bound even inside a native fit.
                try:
                    child=subprocess.run([sys.executable,'-B','-m','ml.fixed_baseline','--execute','--worker'],
                        cwd=root,capture_output=True,text=True,timeout=context.settings['candidate_budget']['max_seconds'],
                        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                except subprocess.TimeoutExpired:
                    raise InputContractError('fixed_baseline_wall_time_limit_exceeded') from None
                if child.returncode!=0:
                    print(child.stdout.strip())
                    if child.stderr:print(child.stderr[-4000:],file=sys.stderr)
                    raise InputContractError('fixed_baseline_worker_failed_no_result_claimed')
                print(child.stdout.strip());return 0
            from threadpoolctl import threadpool_limits
            def progress(event):
                print(json.dumps(event),flush=True)
            with threadpool_limits(limits=1):result=run_fixed(dataset,context,progress=progress)
            print(json.dumps(save_result(root,result,context)))
        else:print(json.dumps({'status':'EXACT_FITTING_AUTHORITY_VERIFIED','rows':len(dataset.observations),'fits':0}))
    except (InputContractError,ValueError,KeyError,OSError) as error:
        print(json.dumps({'status':'BLOCKED_OR_FAILED','reason':str(error),'results_claimed':False}));return 2
    return 0


if __name__=='__main__':
    # Use the canonical module's context class/token, including in CLI workers.
    from ml.fixed_baseline import main as canonical_main
    raise SystemExit(canonical_main())
