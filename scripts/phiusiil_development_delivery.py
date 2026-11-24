"""Materialize the reported-direction development subset, never acceptance/fit.

Reuses existing reconciliation evidence; decodes original development positions
only. No source discovery, reserved predictor access or new partition allocation.
"""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

from scripts.phiusiil_reconcile import digest, selected_records, write_json
from ml.development_experiments import (DevelopmentSpecification, FeatureColumn,
    METADATA, behavioral_columns, build_development_dataset)
from ml.experiment_inputs import InputContractError
from ml.notebook_contracts import validate_feature_boundary
from ml.preparation_integrity import (validate_prospective_population,
    validate_population_assignments, validate_preparation_sources, validate_development_locators)
from ml.preparation_execution import _assignments
from ml.preflight import require_research_fitting
from ml.research_protocol import prospective_id, code_hashes


FEATURES = ('URLLength', 'DomainLength', 'IsDomainIP', 'TLDLength',
    'NoOfSubDomain', 'HasObfuscation', 'NoOfObfuscatedChar', 'NoOfLettersInURL',
    'NoOfDegitsInURL', 'IsHTTPS')
SOURCE_FILE = 'PhiUSIIL_Phishing_URL_Dataset.csv'
REGISTER = 'docs/research/2026-11-18_technical_admission/PHIUSIIL_DECISION_REGISTER.md'


def numeric(value):
    try:
        number = Decimal(value)
        if not number.is_finite() or number != number.to_integral_value():
            raise ValueError('finite_integral_source_value_required')
        return int(number)
    except InvalidOperation:
        raise ValueError('finite_integral_source_value_required') from None


def produce(root, source, reconciliation, output):
    root, source, reconciliation, output = map(Path, (root, source, reconciliation, output))
    status = json.loads((root/'docs/research/2026-11-18_technical_admission/d-features-delivery-status.json').read_bytes())
    upstream = status['latest_reconciliation']
    receipt_path = reconciliation/'reconciliation_receipt.json'
    if digest(receipt_path) != upstream['receipt_sha256']:
        raise ValueError('reconciliation_receipt_changed')
    prior = json.loads(receipt_path.read_bytes())
    for name, expected in prior['output_sha256'].items():
        if digest(reconciliation/name) != expected:
            raise ValueError('reconciliation_output_changed')
    if digest(source) != prior['input_sha256']['original']:
        raise ValueError('original_source_changed')
    with (reconciliation/'development_assignments.normalized.csv').open(newline='') as stream:
        supplied = {int(r['observation_id'].split('::')[1]): r for r in csv.DictReader(stream)}
    if len(supplied) != prior['development_assignment_rows']:
        raise ValueError('upstream_development_count_changed')
    metadata_path=root/'docs/research/2026-11-18_technical_admission/phiusiil/official-metadata.json'
    if digest(metadata_path) != prior['numeric_representation_evidence_sha256']:
        raise ValueError('official_feature_metadata_changed')
    variables=json.loads(metadata_path.read_bytes())['data']['variables']
    declared={v['name'] for v in variables if v['role']=='Feature' and v['type'] in {'Integer','Continuous','Real'}}
    if not set(FEATURES) <= declared:
        raise ValueError('selected_feature_not_source_declared_numeric')
    output.mkdir(parents=True, exist_ok=False)
    (output/'protocol').mkdir()
    (output/'data/development').mkdir(parents=True)
    dictionary={'dataset':'PhiUSIIL', 'conventional':[{'name':name,'kind':'numeric'} for name in FEATURES],
        'protocol_reference':REGISTER, 'feature_dictionary_reference':REGISTER+'#ordered-numeric-fields',
        'attribution':'Implementation under user-reported joint direction; not independent acceptance',
        'missingness':'reject_missing_nonfinite_nonintegral; no imputation',
        'encoding':'source numeric scalars; no learned transforms; later scaling training-fold-only',
        'claim_scope':'exploratory previously-exposed U1 URL-structure subset only',
        'decision_register_sha256':digest(root/REGISTER)}
    write_json(output/'protocol/dictionary.json', dictionary)
    population, assignments, rows = [], [], []
    raw_iter=selected_records(source, supplied)
    _, header=next(raw_iter)
    positions={name:header.index(name) for name in (*FEATURES,'label')}
    snapshot=prior['input_sha256']['original']
    alias_path=output/'historical_id_aliases.jsonl'
    with (reconciliation/'development_lineage.candidate.jsonl').open() as upstream_lineage, alias_path.open('x',encoding='utf-8',newline='\n') as aliases:
        for position, values in raw_iter:
            evidence=json.loads(next(upstream_lineage))
            original_hash=hashlib.sha256(json.dumps(values,ensure_ascii=True,separators=(',',':')).encode()).hexdigest()
            historical=supplied[position]
            if (evidence['observation_id'] != historical['observation_id']
                    or evidence['original_position_candidate'] != position
                    or evidence['original_cells_sha256'] != original_hash
                    or evidence['status'] not in {'exact_cell_and_target_match','declared_numeric_representation_match'}):
                raise ValueError('source_row_differs_from_reconciliation')
            native=numeric(values[positions['label']])
            target=int(historical['target'])
            if native not in (0,1) or target != 1-native:
                raise ValueError('source_target_changed')
            oid=prospective_id('PhiUSIIL',snapshot,SOURCE_FILE,position)
            record={'observation_id':oid,'source_dataset':'PhiUSIIL','source_file':SOURCE_FILE,
                'source_row_id':position,'snapshot_sha256':snapshot,'native_label':native,'target':target}
            population.append(record)
            assignment={'observation_id':oid,'source_dataset':'PhiUSIIL','target':target,
                'group_id':historical['group_id'],'partition':'development','cv_fold':int(historical['cv_fold'])}
            assignments.append(assignment)
            row={**assignment,'source_row_id':position,'label':native}
            row.update({name:numeric(values[positions[name]]) for name in FEATURES})
            rows.append(row)
            aliases.write(json.dumps({'historical_observation_id':historical['observation_id'],
                'observation_id':oid,'original_position':position},sort_keys=True)+'\n')
        if upstream_lineage.read(1):
            raise ValueError('unexpected_extra_upstream_lineage')
    if len(rows) != len(supplied):
        raise ValueError('selected_source_records_missing')
    # Existing checks run as checks, not as alternate scientific admission.
    population_check=validate_prospective_population(population)
    validate_preparation_sources(population,'PhiUSIIL')
    validate_population_assignments(population,assignments)
    validate_development_locators(population,rows,'PhiUSIIL')
    boundary=validate_feature_boundary(rows,dataset='PhiUSIIL',development_only=True)
    specification=DevelopmentSpecification('PhiUSIIL',tuple(FeatureColumn(n,'numeric') for n in FEATURES),REGISTER,REGISTER)
    zero_bits=dict.fromkeys(behavioral_columns(),0)
    dataset=build_development_dataset(rows,({**{k:r[k] for k in METADATA},**zero_bits} for r in rows),specification=specification)
    if dataset.configurations != ('U1',):
        raise ValueError('technical_branch_configuration_changed')
    write_json(output/'protocol/population.json',{'records':population,
        'scope':'reconstructed development only; incomplete three-role admission population'})
    assignment_path=output/'protocol/assignments.csv'
    with assignment_path.open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,('observation_id','target','group_id','partition','cv_fold','source_dataset'),lineterminator='\n')
        writer.writeheader();writer.writerows(assignments)
    strict_assignments=_assignments(assignment_path.read_bytes())
    if strict_assignments != assignments:
        raise ValueError('serialized_assignment_contract_changed')
    data_path=output/'data/development/phiusiil_records.json'
    # Compact JSON stays within the unchanged gate's 100 MB per-input bound.
    with data_path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(rows,stream,separators=(',',':'),allow_nan=False)
    freeze={'code_sha256':code_hashes(root),'assignment_sha256':digest(assignment_path),
        'dictionary_sha256':digest(output/'protocol/dictionary.json'),'data_scope':'development_only',
        'status':'implementation freeze under reported joint direction; not accepted scientific freeze'}
    write_json(output/'protocol/feature_freeze.json',freeze)
    for path in (output/'protocol/population.json',data_path):
        if path.stat().st_size > 100_000_000:
            raise ValueError('unchanged_gate_input_byte_limit_exceeded')
    if digest(source) != snapshot:
        raise ValueError('original_source_changed_during_delivery')
    try:
        require_research_fitting()
    except InputContractError as error:
        fitting_gate=str(error)
    else:
        raise ValueError('fitting_gate_unexpectedly_open')
    files=[p for p in output.rglob('*') if p.is_file()]
    result={'genuine_feature_records':len(rows),'predictor_count':len(FEATURES),
        'adapter_sha256':digest(Path(__file__)),'upstream_receipt_sha256':digest(receipt_path),
        'decision_register_sha256':digest(root/REGISTER),'population_check':population_check,'feature_boundary':boundary,
        'existing_dataset_builder':'PASS; U1 only; behavioral support and availability zero/unavailable',
        'existing_source_locator_and_assignment_checks':'PASS','strict_assignment_parser':'PASS',
        'original_source_rows_decoded':len(rows),'reserved_source_rows_decoded':0,
        'contract_files_created':5,'feature_acceptance_created':False,'no_fit_admission':'BLOCKED',
        'three_role_population_coverage':'BLOCKED: development-only population; authenticated reserved source-locator metadata absent',
        'fitting_gate':fitting_gate,'fits':0,'metrics':None,
        'independently_trusted_acceptance_digest_supplied':False,
        'output_sha256':{p.relative_to(output).as_posix():digest(p) for p in files}}
    write_json(output/'delivery_checks.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--reconciliation',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    result=produce(root,args.source_root/'experiments/datasets-raw/webpage/PhiUSIL'/SOURCE_FILE,args.reconciliation,args.output)
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':
    main()
