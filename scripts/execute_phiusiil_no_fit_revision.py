"""Execute only the jointly approved PhiUSIIL no-fit C/D path.

Uses real supplied approvals; hashes establish bytes, not outside authentication.
No fitting, source CSV read, protected observation access or split substitution.
"""
import argparse
import json
from pathlib import Path
import shutil

from scripts.phiusiil_reconcile import digest, write_json
from ml.no_fit_authority import (VERSION,POLICY_PATH,POLICY_SHA256,FEATURE_SOURCE,
    FEATURE_SOURCE_SHA256,approved_policy)
from ml.scoped_json_records import object_spans, selected_rows
from ml.preparation_execution import run_preparation, _assignments
from ml.research_protocol import code_hashes, parse_specification, specification_record, fit_estimate
from ml.execution_identity import verify_integrity_receipt
from ml.development_experiments import DevelopmentSpecification,FeatureColumn,load_development_dataset


def receipt(root,policy,vera,stage,inputs,access):
    prefix='C' if stage=='C-allocation' else 'D'
    return {'version':VERSION,'stage':stage,'branch':'PhiUSIIL',
        'authority':{'name':vera['researcher'],'role':vera['role'],'date':vera['date'],
            'response_reference':policy['joint_approval']['Vera']['path'],'response_text':vera['message_verbatim']},
        'output_run_id':policy['scope'][prefix+'_output_run'],'input_sha256':inputs,
        'code_sha256':code_hashes(root),
        'access':{'researcher_controlled_policy':{'path':POLICY_PATH,'sha256':POLICY_SHA256},
            'body':False,'links':False,'purpose':'Jointly accepted PhiUSIIL metadata/technical-feature no-fit preparation only',**access}}


def stage_c(root):
    policy,vera=approved_policy(root);scope=policy['scope']
    c_input=root/'experiments/runs'/scope['C_input_run']
    source=root/FEATURE_SOURCE
    if digest(source)!=FEATURE_SOURCE_SHA256:raise ValueError('original_feature_delivery_changed')
    population=json.loads((c_input/'protocol/population.json').read_bytes())['records']
    expected={r['observation_id'] for r in population}
    index={}
    # All these records are still former-development inputs BEFORE allocation.
    # After allocation only index offsets for the new development IDs are decoded.
    with source.open('rb') as stream:
        for offset,length in object_spans(source):
            stream.seek(offset);row=json.loads(stream.read(length));oid=row['observation_id']
            if oid in index or oid not in expected:raise ValueError('feature_index_population_changed')
            index[oid]=[offset,length]
    if set(index)!=expected:raise ValueError('feature_index_coverage_changed')
    index_path=c_input/'feature_record_index.json'
    write_json(index_path,{'source_sha256':FEATURE_SOURCE_SHA256,'records':index})
    actual_inputs={name:digest(c_input/name) for name in scope['C_input_sha256']}
    record=receipt(root,policy,vera,'C-allocation',actual_inputs,{'feature_record_index_sha256':digest(index_path)})
    path=c_input/'protocol/allocation_acceptance.json';write_json(path,record)
    result=run_preparation(root,scope['C_input_run'],stage='C-allocation',expected_authorization_sha256=digest(path))
    output=root/'experiments/runs'/scope['C_output_run']
    verify_integrity_receipt(output,expected_sha256=result['completion_integrity_sha256'])
    report=json.loads((output/'allocation_report.json').read_bytes())
    summary={'stage':'C-allocation','result':result,'receipt_integrity_sha256':digest(path),
        'digest_semantics':'Integrity under jointly accepted researcher-controlled policy; not third-party trust',
        'report':report,'feature_index_sha256':digest(index_path),'model_fits':0}
    write_json(c_input/'C_execution_summary.json',summary)
    return summary


def stage_d(root):
    policy,vera=approved_policy(root);scope=policy['scope']
    c_input=root/'experiments/runs'/scope['C_input_run']
    c_output=root/'experiments/runs'/scope['C_output_run']
    # The completion marker binds the original output set. Do not append files to
    # it; stage summaries live in the separate input namespace.
    completion=digest(c_output/'completion_integrity.json')
    verify_integrity_receipt(c_output,expected_sha256=completion)
    assignments=_assignments((c_output/'assignments.csv').read_bytes())
    byid={a['observation_id']:a for a in assignments}
    dev_ids={oid for oid,a in byid.items() if a['partition']=='development'}
    index=json.loads((c_input/'feature_record_index.json').read_bytes())['records']
    d_input=root/'experiments/runs'/scope['D_input_run']
    (d_input/'protocol').mkdir(parents=True,exist_ok=False)
    (d_input/'data/development').mkdir(parents=True)
    prior=root/'experiments/runs/phiusiil-development-20261118'
    shutil.copyfile(c_input/'protocol/population.json',d_input/'protocol/population.json')
    shutil.copyfile(c_output/'assignments.csv',d_input/'protocol/assignments.csv')
    shutil.copyfile(prior/'protocol/dictionary.json',d_input/'protocol/dictionary.json')
    rows_path=d_input/'data/development/phiusiil_records.json'
    count=0
    with rows_path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write('[')
        for row in selected_rows(root/FEATURE_SOURCE,index,dev_ids):
            a=byid[row['observation_id']]
            if row['target']!=a['target'] or row['source_dataset']!=a['source_dataset']:
                raise ValueError('original_target_or_source_changed')
            row.update({k:a[k] for k in ('group_id','partition','cv_fold')})
            if count:stream.write(',')
            json.dump(row,stream,separators=(',',':'),allow_nan=False);count+=1
        stream.write(']')
    if count!=len(dev_ids):raise ValueError('new_development_coverage_changed')
    freeze={'code_sha256':code_hashes(root),'assignment_sha256':digest(d_input/'protocol/assignments.csv'),
        'dictionary_sha256':digest(d_input/'protocol/dictionary.json'),'data_scope':'development_only'}
    write_json(d_input/'protocol/feature_freeze.json',freeze)
    files=('protocol/population.json','protocol/assignments.csv','protocol/dictionary.json',
           'protocol/feature_freeze.json','data/development/phiusiil_records.json')
    record=receipt(root,policy,vera,'D-features',{n:digest(d_input/n) for n in files},
        {'allocation_integrity_sha256':completion})
    path=d_input/'protocol/feature_acceptance.json';write_json(path,record)
    result=run_preparation(root,scope['D_input_run'],stage='D-features',expected_authorization_sha256=digest(path))
    output=root/'experiments/runs'/scope['D_output_run']
    verify_integrity_receipt(output,expected_sha256=result['completion_integrity_sha256'])
    dictionary=json.loads((d_input/'protocol/dictionary.json').read_bytes())
    specification=DevelopmentSpecification('PhiUSIIL',tuple(FeatureColumn(c['name'],c['kind']) for c in dictionary['conventional']),
        dictionary['protocol_reference'],dictionary['feature_dictionary_reference'])
    loaded=load_development_dataset(root,scope['D_output_run'],specification=specification)
    if {r.observation_id for r in loaded.observations}!=dev_ids:raise ValueError('handoff_readback_IDs_changed')
    # Prepare just the previously proposed fixed baseline; do not authorize it.
    candidate=json.loads((root/'docs/research/2026-11-18_phiusiil_descriptive/candidate_experiment_configuration.json').read_bytes())
    baseline=candidate['plans'][0]['runner_specification']
    baseline['candidates']=[c for c in baseline['candidates'] if c['id']=='logistic_regression-004']
    spec=parse_specification(baseline)
    fixed={'status':'PREPARED FIXED BASELINE; FITTING NOT AUTHORIZED','runner_specification':specification_record(spec),
        'fit_estimate_if_separately_authorized':fit_estimate(spec),'input_run':scope['D_output_run'],
        'note':'One fixed candidate; training-only nested calibration still performs multiple fits. No protected evaluation or behavioral comparison.'}
    write_json(d_input/'fixed_baseline.candidate.json',fixed)
    summary={'stage':'D-features','result':result,'new_development_feature_records':count,
        'new_calibration_or_evaluation_predictors_decoded':0,'historical_protected_records_accessed':0,
        'receipt_integrity_sha256':digest(path),'independent_third_party_authentication_claimed':False,
        'handoff_readback':'PASS; exact development IDs and group-safe folds','fixed_baseline':fixed,
        'scientific_fitting_admission':'Not granted by no-fit handoff; separate exact fitting evidence/settings/authority required','model_fits':0}
    write_json(d_input/'D_execution_summary.json',summary)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('C','D'),required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    result=stage_c(root) if args.stage=='C' else stage_d(root)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
