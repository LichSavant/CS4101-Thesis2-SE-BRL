"""Exact, jointly accepted PhiUSIIL researcher-controlled C/D authority.

This policy grants no fitting. Digests bind actual reviewed evidence/code bytes;
they do not claim third-party authentication. Legacy receipt policy is unchanged.
"""
import hashlib
import json
from pathlib import Path

from ml.experiment_inputs import InputContractError
from ml.metadata import fingerprint


VERSION = 'scoped-no-fit-preparation-researcher-2'
POLICY_PATH = 'docs/research/2026-11-18_technical_admission/PHIUSIIL_AUTHENTICATION_REVISION_ACCEPTED.json'
POLICY_SHA256 = '7eac4d55f0a8a56241484772f7433daa932f96890cba2615106cb47697788d7f'
FEATURE_SOURCE = 'experiments/runs/phiusiil-development-20261118/data/development/phiusiil_records.json'
FEATURE_SOURCE_SHA256 = 'f632bcd1f9bee5117528ae1afc499325ad526666d721418dcdac3d1a29ac4320'


def _bound_json(root, relative, expected):
    path=(Path(root)/relative)
    if path.is_symlink() or not path.resolve().is_relative_to(Path(root).resolve()):
        raise InputContractError('authority_evidence_redirected')
    body=path.read_bytes()
    if len(body)>1_000_000 or hashlib.sha256(body).hexdigest()!=expected:
        raise InputContractError('joint_revision_evidence_changed')
    return json.loads(body)


def approved_policy(root):
    policy=_bound_json(root,POLICY_PATH,POLICY_SHA256)
    proposal=(Path(root)/policy['proposal_path']).read_bytes()
    if hashlib.sha256(proposal).hexdigest()!=policy['proposal_sha256']:
        raise InputContractError('joint_revision_proposal_changed')
    d=_bound_json(root,**{'relative':policy['joint_approval']['Dhanwil']['path'],'expected':policy['joint_approval']['Dhanwil']['sha256']})
    v=_bound_json(root,**{'relative':policy['joint_approval']['Vera']['path'],'expected':policy['joint_approval']['Vera']['sha256']})
    if (d['governing_proposal']!=policy['proposal_path'] or v['proposal_path']!=policy['proposal_path']
            or not d['Dhanwil']['supersedes_personal_independent_verification_condition']
            or v['proposal_sha256']!=policy['proposal_sha256']
            or policy['model_fitting_authorized'] is not False or v['fitting_authorized'] is not False):
        raise InputContractError('joint_no_fit_revision_scope_required')
    return policy,v


def validate_authority(root,receipt,stage,input_run_id):
    policy,v=approved_policy(root)
    access=receipt['access']
    if (not isinstance(access,dict) or access.get('researcher_controlled_policy')!={'path':POLICY_PATH,'sha256':POLICY_SHA256}
            or receipt['branch']!='PhiUSIIL' or stage not in {'C-allocation','D-features'}
            or receipt['authority']!={'name':v['researcher'],'role':v['role'],'date':v['date'],
                'response_reference':policy['joint_approval']['Vera']['path'],'response_text':v['message_verbatim']}):
        raise InputContractError('exact_recorded_researcher_no_fit_authority_required')
    scope=policy['scope'];prefix='C' if stage=='C-allocation' else 'D'
    if input_run_id!=scope[prefix+'_input_run'] or receipt['output_run_id']!=scope[prefix+'_output_run']:
        raise InputContractError('approved_no_fit_run_namespace_required')
    if stage=='C-allocation' and receipt['input_sha256']!=scope['C_input_sha256']:
        raise InputContractError('approved_C_inputs_changed')
    if stage=='D-features':
        from ml.execution_identity import verify_integrity_receipt
        c_run=Path(root)/'experiments/runs'/scope['C_output_run']
        integrity=verify_integrity_receipt(c_run,expected_sha256=access['allocation_integrity_sha256'])
        c_receipt_path=Path(root)/'experiments/runs'/scope['C_input_run']/'protocol/allocation_acceptance.json'
        c_body=c_receipt_path.read_bytes();c_receipt=json.loads(c_body)
        validate_authority(root,c_receipt,'C-allocation',scope['C_input_run'])
        if (hashlib.sha256(c_body).hexdigest()!=integrity['input_sha256']['researcher_authorization_receipt']
                or c_receipt['code_sha256']!=receipt['code_sha256']
                or receipt['input_sha256']['protocol/assignments.csv']!=integrity['output_sha256']['assignments.csv']):
            raise InputContractError('D_assignment_not_from_accepted_C_allocation')
    return policy


def validate_population(policy,records,stage,inputs):
    scope=policy['scope']
    actual=fingerprint(sorted((dict(r) for r in records),key=lambda r:r['observation_id']))
    if (len(records)!=scope['observations'] or actual!=scope['population_fingerprint']
            or any(r['snapshot_sha256']!=scope['source_snapshot_sha256'] for r in records)
            or inputs['protocol/population.json']!=scope['population_file_sha256']):
        raise InputContractError('approved_original_population_changed')
    if stage=='D-features' and inputs['protocol/dictionary.json']!=scope['feature_dictionary_sha256']:
        raise InputContractError('approved_technical_dictionary_changed')


def validate_allocation_settings(policy,settings):
    if any(settings[k]!=policy['scope'][k] for k in ('fractions','seed','maximum_fraction_error')):
        raise InputContractError('approved_group_allocation_settings_changed')


def validate_feature_derivation(root,receipt,rows,dictionary):
    """Read only newly assigned development source spans, never reserved rows."""
    from ml.scoped_json_records import selected_rows
    source=Path(root)/FEATURE_SOURCE
    with source.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=FEATURE_SOURCE_SHA256:
            raise InputContractError('original_feature_delivery_changed')
    policy,_=approved_policy(root)
    c_root=Path(root)/'experiments/runs'/policy['scope']['C_input_run']
    c_receipt=json.loads((c_root/'protocol/allocation_acceptance.json').read_bytes())
    index_path=c_root/'feature_record_index.json'
    index_bytes=index_path.read_bytes()
    if hashlib.sha256(index_bytes).hexdigest()!=c_receipt['access']['feature_record_index_sha256']:
        raise InputContractError('accepted_feature_index_changed')
    index=json.loads(index_bytes)['records']
    actual={r['observation_id']:r for r in rows}
    keys=tuple(c['name'] for c in dictionary['conventional'])+('label','source_row_id','source_dataset','target')
    for original in selected_rows(source,index,set(actual)):
        if any(original[k]!=actual[original['observation_id']][k] for k in keys):
            raise InputContractError('D_original_feature_or_target_changed')
