"""Source-bound automated C review; never human attestation or allocation.

Run from checkout: python -B -m scripts.verify_phiusiil_c_acceptance --source-root ..
No inputs are rewritten. Only accepted former-development source rows are decoded.
"""
import argparse
import csv
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from scripts.phiusiil_reconcile import digest, selected_records, write_json
from ml.prospective_allocation import connected_groups
from ml.research_protocol import code_hashes, prospective_id


def verify(root, source_root):
    base=root/'docs/research/2026-11-18_technical_admission'
    packet_path=base/'PHIUSIIL_C_ALLOCATION_ACCEPTANCE_PACKET.json'
    packet=json.loads(packet_path.read_bytes())
    run=root/packet['input_run_root']
    for entry in (*packet['exact_inputs'],*packet['supporting_evidence']):
        path=root/entry['path']
        if digest(path)!=entry['sha256'] or path.stat().st_size!=entry['bytes']:
            raise ValueError('bound_evidence_changed:'+entry['path'])
    preparation=json.loads((run/'preparation_checks.json').read_bytes())
    if preparation['code_sha256']!=code_hashes(root):
        raise ValueError('executed_ml_code_changed')
    records=json.loads((run/'protocol/population.json').read_bytes())['records']
    by_position={r['source_row_id']:r for r in records}
    if len(records)!=165089 or len(by_position)!=len(records):
        raise ValueError('population_size_or_duplicate_position')
    manifest=source_root/'experiments/results/preprocessing/partitions/phiusiil_partition_manifest.csv'
    if hashlib.sha256(manifest.read_bytes().replace(b'\r\n',b'\n')).hexdigest()!='5e8fd44753f8bef7ac9987d7cdc35c7172a0bcbdf9ad42925a058ce20334847e':
        raise ValueError('upstream_manifest_changed')
    allowed={}
    with manifest.open(encoding='utf-8-sig',newline='') as stream:
        for row in csv.DictReader(stream):
            if row['partition']!='development':
                continue  # Reserved target fields are not evaluated.
            position=int(row['observation_id'].removeprefix('PhiUSIIL::'))
            if position in allowed:
                raise ValueError('duplicate_upstream_position')
            allowed[position]=row
    if set(allowed)!=set(by_position):
        raise ValueError('population_not_exact_original_development_universe')
    source=source_root/packet['scope']['source_path_relative_to_original_repository']
    snapshot=digest(source)
    if snapshot!=packet['scope']['source_snapshot_sha256']:
        raise ValueError('authenticated_source_changed')
    keys={'domain':{},'exact_duplicate':{}}
    labels={}; historical=defaultdict(set)
    iterator=selected_records(source,by_position)
    _,header=next(iterator)
    indices=[header.index(n) for n in ('Domain','URL','label')]
    processed=0
    for position,values in iterator:
        record=by_position[position]
        oid=prospective_id('PhiUSIIL',snapshot,'PhiUSIIL_Phishing_URL_Dataset.csv',position)
        domain,url,native=(values[i] for i in indices)
        if (record['observation_id']!=oid or native not in {'0','1'} or record['native_label']!=int(native)
                or record['target']!=1-int(native) or str(record['target'])!=allowed[position]['target']
                or record['snapshot_sha256']!=snapshot or record['source_file']!='PhiUSIIL_Phishing_URL_Dataset.csv'):
            raise ValueError('source_locator_native_label_or_target_mismatch')
        keys['domain'][oid]=hashlib.sha256(domain.strip().lower().encode()).hexdigest()
        keys['exact_duplicate'][oid]=hashlib.sha256(url.encode()).hexdigest()
        labels[oid]=int(native)
        historical[allowed[position]['group_id']].add(oid)
        processed+=1
    if processed!=len(records):
        raise ValueError('source_position_missing')
    relation=json.loads((run/'protocol/relationships.json').read_bytes())
    settings=json.loads((run/'protocol/allocation_settings.json').read_bytes())
    if (settings['fractions']!=[.7,.15,.15] or settings['seed']!=42 or settings['maximum_fraction_error']!=.05
            or settings['policy_reference']!=relation['policy_reference']):
        raise ValueError('accepted_allocation_settings_mismatch')
    for edge in relation['edges']:
        table=keys[edge['kind']]
        if table[edge['left']]!=table[edge['right']]:
            raise ValueError('relationship_not_supported_by_original_values')
    components=connected_groups(tuple(labels),tuple(relation['edges']),policy_reference=relation['policy_reference'])
    for table in keys.values():
        buckets=defaultdict(set)
        for oid,key in table.items():buckets[key].add(components[oid])
        if any(len(v)!=1 for v in buckets.values()):
            raise ValueError('source_equality_relationship_not_connected')
    if any(len({components[i] for i in members})!=1 for members in historical.values()):
        raise ValueError('historical_group_split')
    component_labels=defaultdict(set)
    for oid,native in labels.items():component_labels[components[oid]].add(native)
    mixed=sum(len(v)>1 for v in component_labels.values())
    if mixed!=36:raise ValueError('mixed_group_count_changed')
    if digest(source)!=snapshot:raise ValueError('source_changed_during_review')
    return {'automated_checks':'PASS','verification_mode':'Separate source-bound automated comparison by the same agent; NOT independent human verification or trusted acceptance',
        'command':'python -B -m scripts.verify_phiusiil_c_acceptance --source-root ..',
        'verifier_sha256':digest(Path(__file__)),'acceptance_packet_sha256':digest(packet_path),
        'source_snapshot_sha256':snapshot,'historical_manifest_lf_sha256':'5e8fd44753f8bef7ac9987d7cdc35c7172a0bcbdf9ad42925a058ce20334847e',
        'input_sha256':preparation['input_sha256'],'source_records_checked':processed,
        'expected_original_development_positions_exact_match':True,'native_labels_targets_and_locator_ids':'PASS',
        'all_supplied_relationship_edges_match_source_values':True,'domain_and_exact_url_connectivity_complete_within_scope':True,
        'components':len(component_labels),'mixed_label_components':mixed,'historical_groups_split':0,
        'historical_protected_source_records_decoded':0,'inputs_rewritten':False,
        'independent_historical_lineage_or_human_acceptance_established':False,
        'allocation_acceptance_exists':(run/'protocol/allocation_acceptance.json').exists(),
        'allocation_executed':False,'model_fits':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    report=verify(root,args.source_root)
    path=root/'docs/research/2026-11-18_technical_admission/PHIUSIIL_C_SOURCE_VERIFICATION.json'
    write_json(path,report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
