"""Prepare accepted-scope C inputs only; no allocation, receipt or fitting.

Reuses the existing population and reads URL/domain/label only at its verified
former-development original positions. Never calls the gated allocator.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import shutil

from scripts.phiusiil_reconcile import digest, selected_records, write_json
from ml.preparation_integrity import validate_prospective_population
from ml.prospective_allocation import connected_groups
from ml.research_protocol import code_hashes


def relationships(observations, policy_reference):
    """Observations: (ID, domain, exact URL, native label, historical group)."""
    first = {'domain': {}, 'exact_duplicate': {}}
    edges, ids, native_by_id, old_groups = [], [], {}, defaultdict(set)
    seen = set()
    for oid, domain, url, native, old_group in observations:
        if oid in seen or native not in (0, 1) or not domain.strip() or not url.strip():
            raise ValueError('duplicate_id_or_missing_relationship_source')
        seen.add(oid); ids.append(oid); native_by_id[oid] = native
        old_groups[old_group].add(oid)
        for kind, value in (('domain', domain.strip().lower()), ('exact_duplicate', url)):
            key = hashlib.sha256(value.encode('utf-8')).hexdigest()
            previous = first[kind].setdefault(key, oid)
            if previous != oid:
                edges.append({'left': previous, 'right': oid, 'kind': kind,
                    'evidence_reference': policy_reference + '; original development-only ' + kind})
    groups = connected_groups(tuple(ids), tuple(edges), policy_reference=policy_reference)
    if any(len({groups[i] for i in members}) != 1 for members in old_groups.values()):
        raise ValueError('historical_group_would_be_split')
    components, component_old = defaultdict(set), defaultdict(set)
    for old, members in old_groups.items():
        for oid in members:
            components[groups[oid]].add(native_by_id[oid])
            component_old[groups[oid]].add(old)
    return edges, {'observations': len(ids), 'historical_groups': len(old_groups),
        'components': len(components), 'edge_counts': dict(Counter(e['kind'] for e in edges)),
        'mixed_native_label_components': sum(len(v)>1 for v in components.values()),
        'components_merging_historical_groups': sum(len(v)>1 for v in component_old.values()),
        'historical_groups_split': 0, 'raw_url_domain_values_exported': False}


def prepare(root, source_root, output):
    root, source_root, output = map(Path, (root, source_root, output))
    decision_path = root/'docs/research/2026-11-18_technical_admission/PHIUSIIL_SCOPE_DECISION.json'
    decision = json.loads(decision_path.read_bytes())
    if (not decision['attribution']['exact_proposal_acceptance_supplied']
            or not decision['boundaries']['preparation_authorized_by_direct_response']):
        raise ValueError('actual_methodological_preparation_acceptance_required')
    if digest(root/decision['proposal_path']) != decision['proposal_sha256']:
        raise ValueError('accepted_proposal_bytes_changed')
    prior = root/'experiments/runs/phiusiil-development-20261118'
    check = json.loads((prior/'delivery_checks.json').read_bytes())
    for name, expected in check['output_sha256'].items():
        if digest(prior/name) != expected:
            raise ValueError('existing_delivery_changed')
    records = json.loads((prior/'protocol/population.json').read_bytes())['records']
    population_check = validate_prospective_population(records)
    if len(records) != decision['proposed_scope']['population_records']:
        raise ValueError('accepted_population_count_changed')
    by_position = {r['source_row_id']:r for r in records}
    if len(by_position) != len(records):
        raise ValueError('duplicate_original_position')
    import csv
    with (prior/'protocol/assignments.csv').open(newline='') as stream:
        historical = {r['observation_id']:r for r in csv.DictReader(stream)}
    if set(historical) != {r['observation_id'] for r in records}:
        raise ValueError('historical_population_mismatch')
    source = source_root/'experiments/datasets-raw/webpage/PhiUSIL/PhiUSIIL_Phishing_URL_Dataset.csv'
    source_hash = digest(source)
    if source_hash != decision['proposed_scope']['snapshot_sha256']:
        raise ValueError('source_snapshot_changed')
    policy = 'phiusiil-former-development-exploratory-v1; decision-sha256:' + digest(decision_path)
    def observations():
        source_rows = selected_records(source, by_position)
        _, header = next(source_rows)
        fields = [header.index(n) for n in ('Domain','URL','label')]
        count = 0
        for position, values in source_rows:
            record = by_position[position]
            domain, url, native = (values[i] for i in fields)
            if native not in {'0','1'} or int(native) != record['native_label'] or record['target'] != 1-int(native):
                raise ValueError('source_native_target_correspondence_changed')
            count += 1
            yield record['observation_id'], domain, url, int(native), historical[record['observation_id']]['group_id']
        if count != len(records):
            raise ValueError('missing_selected_source_positions')
    edges, report = relationships(observations(), policy)
    if digest(source) != source_hash:
        raise ValueError('source_changed_during_preparation')
    output.mkdir(parents=True, exist_ok=False)
    protocol = output/'protocol'; protocol.mkdir()
    # A distinct immutable input namespace needs its own bytes for the existing
    # C contract. This is a byte-identical copy, not regenerated population data.
    shutil.copyfile(prior/'protocol/population.json', protocol/'population.json')
    relationship_record = {'policy_reference': policy, 'edges': edges,
        'coverage': {'domain':'source_verified','exact_duplicate':'source_verified',
            'near_duplicate':'unavailable_with_accepted_limitation','template':'unavailable_with_accepted_limitation',
            'campaign':'unavailable_with_accepted_limitation'}}
    write_json(protocol/'relationships.json', relationship_record)
    write_json(protocol/'allocation_settings.json', {'fractions':[.7,.15,.15], 'seed':42,
        'maximum_fraction_error':.05, 'policy_reference':policy})
    files = ('population.json','relationships.json','allocation_settings.json')
    result = {'scope_decision_sha256':digest(decision_path),'adapter_sha256':digest(Path(__file__)),
        'source_snapshot_sha256':source_hash,'population_check':population_check,'relationship_checks':report,
        'original_source_rows_decoded':len(records),'historical_protected_rows_decoded':0,
        'input_sha256':{'protocol/'+n:digest(protocol/n) for n in files},'code_sha256':code_hashes(root),
        'population_copy_byte_identical':digest(protocol/'population.json') == check['output_sha256']['protocol/population.json'],
        'scope_attribution':'Direct user acceptance dated 2026-11-18; joint acceptance reported, Vera confirmation not independently documented',
        'gated_C_allocation':'NOT_EXECUTED: exact-file allocation acceptance/independently trusted digest absent',
        'allocation_acceptance_created':False,'independent_trust_asserted':False,'fits':0}
    write_json(output/'preparation_checks.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = prepare(root,args.source_root,args.output)
    print(json.dumps({k:v for k,v in result.items() if k != 'code_sha256'},indent=2))


if __name__ == '__main__':
    main()
