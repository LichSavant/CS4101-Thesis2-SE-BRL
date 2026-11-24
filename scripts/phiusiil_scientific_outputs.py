"""Authorized former-development descriptives and candidate design, never fitting.

Uses only the existing feature delivery; no raw-source reads or new allocations.
Outputs are aggregate-only. Current invocation grants descriptive access, not
scientific admission, accepted experiment settings or fitted-model execution.
"""
import argparse
from collections import Counter
from copy import deepcopy
import csv
import hashlib
from itertools import product
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts.phiusiil_reconcile import digest, write_json
from ml.classifier_adapters import ClassifierSpecification, PreprocessingSpecification
from ml.experiment_engine import Candidate, NestedSpecification, SigmoidSpecification, ThresholdSpecification
from ml.experiment_inputs import select_predictors, InputContractError
from ml.model_selection import SelectionPolicy
from ml.preflight import require_research_fitting
from ml.research_protocol import specification_record, parse_specification, fit_estimate, code_hashes


REFERENCE='research:candidate-phiusiil-exploratory-design-20261118-not-authorization'
METRICS=('precision','recall','f1','balanced_accuracy','confusion_matrix','specificity',
         'mcc','average_precision','roc_auc','brier_score','ece')


def quality(values, labels):
    missing=sum(v is None for v in values)
    array=np.asarray([np.nan if v is None else v for v in values],dtype=float)
    finite=np.isfinite(array)
    data=array[finite]
    unique,counts=np.unique(data,return_counts=True)
    mode_fraction=float(counts.max()/len(data)) if len(data) else None
    result={'observations':len(values),'missing':missing,'nonfinite_nonmissing':int((~finite).sum())-missing,
        'finite':len(data),'unique_finite':len(unique),'constant':len(unique)==1,
        'near_constant_99pct':mode_fraction is not None and mode_fraction>=.99,
        'modal_fraction':mode_fraction,'zero_fraction':float(np.mean(data==0)) if len(data) else None,
        'mean':float(np.mean(data)) if len(data) else None,'std_population':float(np.std(data)) if len(data) else None,
        'exact_target_copy':bool(len(data)==len(values) and np.array_equal(data,np.asarray(labels))),
        'exact_target_complement':bool(len(data)==len(values) and np.array_equal(data,1-np.asarray(labels)))}
    for name,p in (('min',0),('p01',.01),('p25',.25),('median',.5),('p75',.75),('p99',.99),('max',1)):
        result[name]=float(np.quantile(data,p,method='linear')) if len(data) else None
    return result


def configuration(settings, dictionary):
    names=tuple(c['name'] for c in dictionary['conventional'])
    if dictionary['dataset']!='PhiUSIIL':raise ValueError('technical_only_dictionary_required')
    select_predictors(dict.fromkeys(names),names)
    proposed=settings['experiment'];seed=proposed['seed']
    families=('logistic_regression','linear_svm','random_forest','xgboost')
    plans=[]
    for family in families:
        grid=proposed[family];axes=tuple(grid['axes']);candidates=[]
        for i,values in enumerate(product(*(grid['axes'][k] for k in axes))):
            parameters={**grid['fixed'],**dict(zip(axes,values))}
            candidates.append(Candidate(f'{family}-{i:03d}',ClassifierSpecification(family,parameters,seed),
                PreprocessingSpecification('reject',proposed['numeric_preprocessing'][family],None)))
        calibration=SigmoidSpecification(ClassifierSpecification('logistic_regression',proposed['calibration']['parameters'],seed),
            'identity' if family=='linear_svm' else 'logit_probability',proposed['calibration']['clip_epsilon'])
        spec=NestedSpecification(tuple(candidates),('U1',),calibration,ThresholdSpecification('fixed',.5),
            tuple(proposed['calibration_edges']),REFERENCE)
        record=specification_record(spec)
        parse_specification(record)
        estimate=fit_estimate(spec)
        input_run='phiusiil-u1-'+family.replace('_','-')+'-candidate-v1'
        plans.append({'family':family,'candidate_count':len(candidates),'runner_specification':record,
            'fit_estimate_if_authorized':estimate,
            'candidate_budget_not_approved':{**{'max_base_fits':estimate['base_fits'],'max_calibration_fits':estimate['calibration_fits']},
                'max_seconds':86400,'max_training_rows':165089,'threads':1},
            'launch_after_exact_run_acceptance_only':f'python -B -m ml.research_execution --root . --input-run-id {input_run} --authorization-sha256 <independently-trusted-fitting-receipt-sha256> --purpose fit --execute'})
    ablations=[]
    for name,omitted in (('omit_obfuscation',('HasObfuscation','NoOfObfuscatedChar')),
                         ('omit_host_structure',('DomainLength','IsDomainIP','TLDLength','NoOfSubDomain'))):
        if not set(omitted)<set(names):raise ValueError('ablation_must_leave_existing_technical_features')
        record=deepcopy(plans[0]['runner_specification']);record['omitted_features']=list(omitted)
        parse_specification(record)
        ablations.append({'name':name,'rationale':'Test incremental technical signal of this fixed feature block on identical observations/folds; no behavioral interpretation',
            'runner_specification':record,'fit_estimate_if_authorized':fit_estimate(parse_specification(record)),
            'launch_after_separate_ablation_acceptance_only':f'python -B -m ml.research_execution --root . --input-run-id phiusiil-u1-{name.replace("_","-")}-candidate-v1 --authorization-sha256 <independently-trusted-ablation-receipt-sha256> --purpose ablation --execute'})
    policy=dict(families=list(families),configuration='U1',delta_pr=.01,resamples=2000,confidence=.95,seed=seed,
        hard_limits={k:None for k in ('minimum_recall','minimum_precision','maximum_p95_ms','maximum_memory_bytes')},
        memory_evidence='unavailable_allowed_without_limit',calibration_order=['brier_score','ece'],
        efficiency_order=['p95_batch_ms','throughput_artifacts_per_second','measured_memory_bytes_max','serialized_model_bytes'],protocol_reference=REFERENCE)
    SelectionPolicy(**{**policy,'families':tuple(families),'calibration_order':tuple(policy['calibration_order']),'efficiency_order':tuple(policy['efficiency_order'])})
    return {'status':'CANDIDATE - NOT FITTING AUTHORIZATION','scientific_settings_accepted':False,
        'dataset':'PhiUSIIL','dictionary':dictionary,'population':'165089 former-development observations; new internal development subset size pending C allocation',
        'allocation_candidate':{'fractions':[.7,.15,.15],'seed':seed,'development_folds':5,'maximum_fraction_error':.05,'executed':False},
        'baseline_implementations':'Existing ml/classifier_adapters.py and ml/experiment_engine.py; implementation availability is not approved scientific execution',
        'comparison_policy':'Same accepted observations, groups, outer/inner folds and scoring; no behavioral E2/E3 views',
        'training_boundary':'All scaling/search/calibration learn only within applicable training folds; new internal calibration/evaluation predictors and outcomes excluded from model selection; no historical protected access',
        'grids_source':'ml/research_settings_candidate.v0.1.0.json, status Pending; full recommended grids retained, not silently reduced',
        'plans':plans,'technical_ablations':ablations,'evaluation_metrics':list(METRICS),
        'metric_schema':'Existing ml/evaluation_metrics.py and ml/experiment_artifacts.py; pooled nested OOF AP, confusion matrix [[TN,FP],[FN,TP]], positive target 1; fixed threshold 0.5 after training-only sigmoid calibration',
        'uncertainty':{'method':'paired_group_bootstrap','resamples':2000,'confidence':.95,'seed':seed,'execution':'not run'},
        'candidate_selection_policy_not_accepted':policy,
        'selection_limitations':'delta_pr=0.01 is an unaccepted recommendation; None hard limits explicitly restrict this candidate to exploratory comparisons, with no deployment/SRS compliance claim. Budgets are proposals, not measured feasibility.',
        'prerequisites':['Accepted C allocation and trusted receipt digest','New-split D-feature rebinding/admission and exact accepted code/environment/input manifests','Per-family and ablation exact acceptance.json, independently trusted digest, frozen settings and budgets'],
        'predictive_results':None,'model_fits':0}


def write_csv(path, rows):
    with path.open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,tuple(rows[0]));writer.writeheader();writer.writerows(rows)


def produce(root, output):
    root,output=Path(root),Path(output)
    base=root/'docs/research/2026-11-18_technical_admission'
    status=json.loads((base/'d-features-delivery-status.json').read_bytes())
    run=root/'experiments/runs/phiusiil-development-20261118'
    check=json.loads((run/'delivery_checks.json').read_bytes())
    # One availability/identity check; reuse existing source/group/lineage audits.
    inputs={}
    for name in ('data/development/phiusiil_records.json','protocol/dictionary.json','protocol/assignments.csv','protocol/population.json'):
        path=run/name
        if digest(path)!=check['output_sha256'][name]:raise ValueError('existing_authorized_delivery_changed')
        inputs[path.relative_to(root).as_posix()]=check['output_sha256'][name]
    rows=json.loads((run/'data/development/phiusiil_records.json').read_bytes())
    dictionary=json.loads((run/'protocol/dictionary.json').read_bytes())
    names=tuple(c['name'] for c in dictionary['conventional'])
    if len(rows)!=165089 or any(r['partition']!='development' for r in rows):raise ValueError('permitted_population_changed')
    for row in rows:select_predictors(row,names)
    labels=[r['target'] for r in rows]
    quality_rows=[{'feature':name,'evidence':'observed former-development values; descriptive only',**quality([r[name] for r in rows],labels)} for name in names]
    class_counts=Counter(labels);fold_counts=Counter((r['cv_fold'],r['target']) for r in rows)
    descriptive=[]
    def add(metric,value,scope,unit='records',denominator='',evidence='observed existing feature delivery'):
        descriptive.append(dict(metric=metric,scope=scope,value=value,unit=unit,denominator=denominator,evidence=evidence))
    add('source_records',235795,'original PhiUSIIL snapshot',evidence='reused verified source/assignment aggregate; not reread')
    add('permitted_records',len(rows),'former-development population')
    add('historical_protected_records_excluded',70706,'outside permitted population',evidence='reused verified role accounting')
    for label,count in sorted(class_counts.items()):
        add('target_class_count',count,f'target={label}')
        add('target_class_fraction',count/len(rows),f'target={label}','fraction',len(rows))
    for (fold,label),count in sorted(fold_counts.items()):add('historical_fold_target_count',count,f'fold={fold};target={label}')
    grouping=status['latest_accepted_scope_preparation']['checks']['relationship_checks']
    for key in ('components','mixed_native_label_components','historical_groups_split','components_merging_historical_groups'):
        add(key,grouping[key],'permitted former-development population','groups',evidence='reused hash-bound source relationship verification')
    add('historical_role_group_crossings',0,'historical assignments','groups',evidence='reused unchanged-input recorded group isolation')
    add('historical_fold_group_crossings',0,'historical assignments','groups',evidence='reused unchanged-input recorded group isolation')
    add('numeric_predictors',len(names),'ten-field technical subset','features')
    add('official_feature_coverage_fraction',len(names)/54,'source-declared 54 features','fraction',54)
    add('source_numeric_feature_coverage_fraction',len(names)/50,'source-declared 50 numeric features','fraction',50)
    add('behavioral_indicators_available',0,'technical-only modality','indicators',12,evidence='existing modality constraint; no indicator evidence generated')
    add('constant_predictors',sum(r['constant'] for r in quality_rows),'ten-field technical subset','features')
    add('near_constant_predictors_99pct',sum(r['near_constant_99pct'] for r in quality_rows),'ten-field technical subset','features')
    add('missing_numeric_cells',sum(r['missing'] for r in quality_rows),'ten-field technical subset','cells')
    add('nonfinite_numeric_cells',sum(r['nonfinite_nonmissing'] for r in quality_rows),'ten-field technical subset','cells')
    add('exact_target_or_complement_columns',sum(r['exact_target_copy'] or r['exact_target_complement'] for r in quality_rows),'ten-field technical subset','features')
    settings_path=root/'ml/research_settings_candidate.v0.1.0.json'
    settings=json.loads(settings_path.read_bytes());candidate=configuration(settings,dictionary)
    inputs[settings_path.relative_to(root).as_posix()]=digest(settings_path)
    output.mkdir(parents=True,exist_ok=False)
    write_csv(output/'scientific_descriptive_results.csv',descriptive)
    write_csv(output/'scientific_feature_quality.csv',quality_rows)
    write_json(output/'candidate_experiment_configuration.json',candidate)
    # One final stage-availability check, never a speculative launch or retry.
    c=root/'experiments/runs/phiusiil-former-development-input-v1/protocol/allocation_acceptance.json'
    d=run/'protocol/feature_acceptance.json'
    e=run/'protocol/acceptance.json'
    stages={'C_receipt_present':c.is_file(),'D_receipt_present':d.is_file(),'fitting_receipt_present':e.is_file(),
        'independently_trusted_receipt_digest_supplied':False}
    try:require_research_fitting()
    except InputContractError as error:stages['unverified_fitting_gate']=str(error)
    else:raise ValueError('unverified_fitting_gate_open')
    manuscript=f'''# PhiUSIIL exploratory technical study: methods and descriptive findings

**Draft; descriptive results only. No admitted experiment or predictive result.**

## Dataset source and selection — verified evidence

The authenticated UCI PhiUSIIL-967 snapshot contains 235,795 observations. The
permitted population consists of {len(rows):,} reconciled former-development
positions; all 70,706 historical calibration/test positions remain excluded.
Official UCI class definitions are native 0=phishing and 1=legitimate, mapped to
study target 1 and 0. Existing source verification is reused, not repeated.
The analysis observed {class_counts[1]:,} target-1 and {class_counts[0]:,} target-0
records ({class_counts[1]/len(rows):.4%} and {class_counts[0]/len(rows):.4%}).

## Preprocessing and lineage — verified reconstruction with limitations

The existing source-bound prospective IDs encode snapshot, original file and
original record position. A preserved alias ledger links historical cleaned-rank
IDs. Previous comparison found four exact decoded-cell matches and 165,085
matches differing only by exact decimal representation in declared numeric
fields. This corroborates reconstructed correspondence; it does not independently
authenticate historical processing or human custody. Original datasets remain
unchanged. Integral historical folds were separately normalized without changing
membership, groups or targets. No imputation or model-dependent transformation
was applied to this delivery.

## Feature availability — observed findings

The fixed source-appropriate subset contains ten URL-structure numeric fields,
listed in the candidate configuration. It covers 10/54 declared source features
and 10/50 numeric fields, deliberately omitting corpus-reference/probability
features and content fields. FILENAME and all label/identity/partition metadata
are excluded from predictors. There were {sum(r['missing'] for r in quality_rows)}
missing and {sum(r['nonfinite_nonmissing'] for r in quality_rows)} nonfinite cells;
{sum(r['constant'] for r in quality_rows)} predictors were constant and
{sum(r['near_constant_99pct'] for r in quality_rows)} had at least 99% modal
prevalence. These are descriptive flags, not feature-removal decisions.
Exact target/complement checks flagged
{sum(r['exact_target_copy'] or r['exact_target_complement'] for r in quality_rows)}
columns; this limited check does not establish absence of all leakage.
Feature means, population standard deviations and linear-interpolated quantiles
are in scientific_feature_quality.csv. No psychological/behavioral indicator is
observable from this technical delivery; the existing unavailable encoding is
retained and no E2/E3 or Transformer-effectiveness conclusion is supported.

## Grouping and split policy — recorded decisions versus unexecuted allocation

Existing evidence identifies 154,096 permitted components and 36 mixed-label
components, retained intact. Source-verified literal-domain and exact-URL
relationships have documented scope; near-duplicate/template/campaign coverage
is unavailable with explicit limitations. Historical group-role and group-fold
crossings were zero in the unchanged-input verification. Recorded methodological
acceptance specifies a new group-safe 70/15/15 internal allocation, seed 42 and
five development folds. That allocation is NOT executed or treated as accepted
exact-file execution: the trusted C receipt/digest remains unavailable. Historical
fold accounting in the CSV does not represent the proposed new folds.

## Intended evaluation — candidate, not fitting authorization

Existing logistic regression, linear SVM, random forest and XGBoost adapters are
available engineering implementations. The candidate configuration expands the
existing Pending parameter grids without shrinking them, validates exact runner
schemas, and proposes two technical block-removal ablations. All comparisons
must share the eventual accepted observations/groups/folds. Scaling, tuning and
sigmoid calibration use only the appropriate training folds; the outer fold is
reserved for out-of-fold prediction. The proposed threshold is 0.5. Precision,
recall, F1, balanced accuracy, confusion matrices, AP, ROC AUC and calibration
metrics are specified, with paired group-bootstrap uncertainty. No deployment
limits or practical-equivalence margin are claimed scientifically accepted.

## Reproducibility and limitations

The execution summary binds actual input/output hashes, code identity and the
reproduction command. Full row IDs, predictors and predictions are not committed.
All selected observations were previously visible and possibly evaluated; new
internal roles cannot restore an untouched holdout. Explicit near/template/campaign
limitations and the restricted ten-feature subset bound generalization claims.
Researcher scope acceptance and personal conditional C acceptance are recorded;
joint acceptance is reported rather than independently signed. Independently
trusted exact-file acceptance, D admission, frozen experiment settings/budgets and
separate fitting authority remain required. There are **zero model fits and no
predictive metrics, uncertainty intervals, comparative or significance results**.

Evidence: ../2026-11-18_technical_admission/phiusiil/label-verification.json;
../2026-11-18_technical_admission/d-features-delivery-status.json;
../2026-11-18_technical_admission/PHIUSIIL_C_SOURCE_VERIFICATION.json;
../2026-11-18_technical_admission/PHIUSIIL_C_PERSONAL_ACCEPTANCE_RECORD.json.
'''
    with (output/'scientific_methodology_draft.md').open('x',encoding='utf-8',newline='\n') as stream:stream.write(manuscript)
    for rel,expected in inputs.items():
        if digest(root/rel)!=expected:raise ValueError('input_changed_during_description')
    summary={'category':'ACTUAL DESCRIPTIVE FINDINGS; NOT MODEL RESULTS','real_observations_analyzed':len(rows),
        'baseline_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip(),
        'command':'python -B -m scripts.phiusiil_scientific_outputs --output '+output.relative_to(root).as_posix(),
        'script_sha256':digest(Path(__file__)),'input_sha256':inputs,'ml_code_sha256':code_hashes(root),
        'authorized_scope':'Current instruction permits descriptive analysis of existing former-development feature delivery only; historical protected records excluded',
        'task_disposition':{'A_executed':['Existing-feature aggregate descriptives and quality statistics','Candidate exact-runner schema expansion/roundtrip and no-fit fit-count estimates','Evidence-backed methodology draft'],
            'B_completed':['Previously absent five requested output files created; no software/data defect repaired'],
            'C_external':['C exact-file independent receipt authentication/digest','D exact accepted-split handoff/receipt','Frozen per-family/ablation experiment settings, accepted budgets and fitting authorization']},
        'descriptive_rows':len(descriptive),'feature_quality_rows':len(quality_rows),'quality':{'constant_features':[r['feature'] for r in quality_rows if r['constant']],
            'near_constant_99pct_features':[r['feature'] for r in quality_rows if r['near_constant_99pct']],
            'missing_cells':sum(r['missing'] for r in quality_rows),'nonfinite_cells':sum(r['nonfinite_nonmissing'] for r in quality_rows),
            'exact_target_or_complement_features':[r['feature'] for r in quality_rows if r['exact_target_copy'] or r['exact_target_complement']]},
        'configuration_validation':'PASS: four full family grids and two technical ablations roundtrip existing parser; candidate selection policy constructs without fitting',
        'candidate_counts':{p['family']:p['candidate_count'] for p in candidate['plans']},
        'candidate_base_fits_if_all_authorized':sum(p['fit_estimate_if_authorized']['base_fits'] for p in candidate['plans']),
        'candidate_ablation_base_fits_if_authorized':sum(p['fit_estimate_if_authorized']['base_fits'] for p in candidate['technical_ablations']),
        'final_gate_check_once':stages,'scientific_admission':'BLOCKED','model_fits':0,'predictive_metrics':None,
        'raw_source_predictors_read':False,'historical_protected_records_accessed':0,'existing_inputs_preserved':True,
        'output_sha256':{p.name:digest(p) for p in output.iterdir() if p.is_file()}}
    write_json(output/'scientific_execution_summary.json',summary)
    print(json.dumps({k:summary[k] for k in ('real_observations_analyzed','descriptive_rows','feature_quality_rows','quality','candidate_counts','final_gate_check_once','model_fits')},indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    produce(root,(root/args.output).resolve())


if __name__=='__main__':main()
