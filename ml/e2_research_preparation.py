"""E2 preparation only: no inference, fitting, downloads or scientific admission.

Pure metadata helpers are software interfaces, not permission to process a corpus.
Actual ingestion and annotation delivery retain the existing fail-closed policy.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

from ml.annotation_validation import blinded_packet, indicator_ids, validate_span
from ml.preprocessing import TextEvidence
from ml.prospective_allocation import connected_groups
from ml.research_policy import reject_excluded, require_stage_authorization
from ml.research_protocol import prospective_id
from ml.se_brl.detectors import AuthorityReview, DetectorContext, IdentityReference

ROOT = Path(__file__).resolve().parents[1]
E2 = ROOT / 'experiments/e2_enrichment_20261124'
METADATA = ('observation_id', 'source_dataset', 'target', 'group_id', 'partition', 'cv_fold')
PILOT = {(1, False): 75, (1, True): 25, (0, False): 75, (0, True): 25}
FAMILIES = ('logistic_regression', 'linear_svm', 'random_forest', 'xgboost')


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _digest(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def _rank(seed, purpose, key):
    return _sha(json.dumps([seed, purpose, key], separators=(',', ':')).encode())


def sample_pilot(metadata, *, seed=42, quotas=None):
    """Deterministic maximum matching: one member per group, exact diagnostic quotas.

    Accepts custody metadata only. Returns researcher-only selection, never labels
    for an annotator. Conflicting exact-duplicate grouping must be resolved first.
    Input order cannot affect selection; shortages fail without reallocating quotas.
    """
    quotas = dict(PILOT if quotas is None else quotas)
    if type(seed) is not int or set(quotas) != set(PILOT) or any(type(n) is not int or n < 0 for n in quotas.values()):
        raise ValueError('Explicit seed and four nonnegative integer stratum quotas required')
    candidates = defaultdict(dict)
    ids, hash_groups = set(), {}
    for row in metadata:
        if not isinstance(row, dict):
            raise ValueError('Pilot metadata rows must be mappings')
        reject_excluded(row)
        rid, group, digest = (row.get(k) for k in ('record_id', 'group_id', 'content_sha256'))
        if (type(rid) is not str or not rid or rid in ids or type(group) is not str or not group
                or not _digest(digest) or row.get('partition') != 'development'
                or type(row.get('source_dataset')) is not str or not row['source_dataset']
                or type(row.get('target')) is not int or row['target'] not in (0, 1)
                or type(row.get('supported')) is not bool):
            raise ValueError('Unique development identities, binary target and explicit support required')
        ids.add(rid)
        if digest in hash_groups and hash_groups[digest] != group:
            raise ValueError('Exact duplicates have inconsistent groups; do not silently repartition')
        hash_groups[digest] = group
        stratum = (row['target'], row['supported'])
        old = candidates[stratum].get(group)
        if old is None or _rank(seed, 'member', rid) < _rank(seed, 'member', old['record_id']):
            candidates[stratum][group] = dict(row)
    slots = [key for key in sorted(quotas) for _ in range(quotas[key])]
    ordered = {key: sorted(candidates[key], key=lambda g: _rank(seed, 'group', g)) for key in quotas}
    owners = {}

    def assign(slot, visited):
        for group in ordered[slots[slot]]:
            if group in visited:
                continue
            visited.add(group)
            if group not in owners or assign(owners[group], visited):
                owners[group] = slot
                return True
        return False

    if not all(assign(slot, set()) for slot in range(len(slots))):
        raise ValueError('Insufficient distinct groups for the exact pilot allocation')
    selected = [candidates[slots[slot]][group] for group, slot in owners.items()]
    return sorted(selected, key=lambda row: _rank(seed, 'delivery-order', row['record_id']))


def prepare_ingestion(rows, source, snapshot_sha256, source_file, relationships, *, policy_reference):
    """Future approved ingestion boundary; cannot execute under the current gate."""
    require_stage_authorization('preprocessing')  # before reading any row
    reject_excluded((source, source_file))
    records = []
    for position, row in enumerate(rows):
        records.append({**row, 'observation_id': prospective_id(source, snapshot_sha256, source_file, position)})
    groups = connected_groups([r['observation_id'] for r in records], relationships,
                              policy_reference=policy_reference)
    return [{**r, 'group_id': groups[r['observation_id']]} for r in records]


def _bound_annotation_records(records, selected):
    """Pure custody binding, also testable without enabling the delivery gate."""
    by_id = {}
    for record in records:
        key = record['record_id']
        if key in by_id:
            raise ValueError('Duplicate annotation source record')
        by_id[key] = record
    ordered = []
    for row in selected:
        if row['record_id'] not in by_id:
            raise ValueError('Selected observation is absent from the authorized delivery')
        record = by_id[row['record_id']]
        digest = _sha(json.dumps(dict(record['fields']), sort_keys=True, ensure_ascii=False).encode())
        if (digest != row['content_sha256'] or record['source_dataset'] != row['source_dataset']
                or record['group_id'] != row['group_id'] or record['partition'] != 'development'):
            raise ValueError('Sampling custody does not match the unchanged original artifact')
        ordered.append(record)
    return ordered


def prepare_annotation_delivery(records, metadata, *, seed=42):
    """No packet generation until lawful access/protocol authorization is admitted."""
    require_stage_authorization('annotation')  # before sampling or reading content
    selected = sample_pilot(metadata, seed=seed)
    packet = blinded_packet(_bound_annotation_records(records, selected))
    # Exact schema projection prevents accidental source/target/prediction delivery.
    safe = ('record_id', 'modality', 'fields', 'text_hash', 'indicators', 'evidence',
            'uncertainty', 'annotation_notes')
    items = [{k: item[k] for k in safe} for item in packet['items']]
    return {'reviewer_a': items, 'reviewer_b': json.loads(json.dumps(items)),
            'researcher_only_custody_manifest': packet['researcher_only_custody_manifest'],
            'researcher_only_sampling_manifest': selected, 'judgments_generated': 0}


def blank_response():
    """Unfilled material; deliberately invalid as an independent completed judgment."""
    return {'record_id': '', 'text_hash': '', 'modality': 'content_bearing_email',
            'codebook_version': '0.1.0', 'annotator_id': '', 'role': 'independent_human',
            'qualifications': '', 'review_date': '', 'protocol_version': '',
            'independent': None, 'model_output_visible': None,
            'indicators': dict.fromkeys(indicator_ids()), 'evidence': {},
            'uncertainty': {}, 'identity_reference_ids': {}, 'annotation_notes': ''}


def import_trust_context(fields, manifest, *, trusted_document_hashes):
    """Import externally authenticated reference bindings, not self-certified truth.

    trusted_document_hashes must come from an independent custody review, never
    from the submitted manifest. This adapter validates linkage only. The existing
    detector still checks exact artifact segment locators and admissible claims.
    """
    allowed = {'subject', 'body', 'sender', 'reply_to', 'title', 'visible_text', 'html', 'page_url', 'url'}
    if not isinstance(fields, dict) or set(fields) - allowed or any(type(value) is not str for value in fields.values()):
        raise ValueError('Original artifact fields only; source labels and predictions are forbidden')
    identities, reviews = [], []
    expected_artifact = _sha(json.dumps(dict(fields), sort_keys=True, ensure_ascii=False).encode())
    seen = set()
    for row in manifest:
        if not isinstance(row, dict):
            raise ValueError('Reference rows must be mappings')
        reject_excluded(row)
        ref = row.get('reference_id')
        if (not isinstance(ref, str) or not ref or ref in seen
                or not _digest(row.get('document_sha256'))
                or trusted_document_hashes.get(ref) != row['document_sha256']
                or row.get('artifact_sha256') != expected_artifact
                or row.get('independent_of_labels_and_model') is not True
                or not isinstance(row.get('verified_by'), str) or not row['verified_by'].strip()):
            raise ValueError('Independently trusted document and exact artifact binding required')
        date.fromisoformat(row['verified_on'])
        uri = urlsplit(row.get('source_uri', ''))
        if uri.scheme != 'https' or not uri.hostname or uri.username or uri.password:
            raise ValueError('Independent document provenance requires an HTTPS source URI without credentials')
        seen.add(ref)

        def span(name):
            value = row[name]
            validate_span(value, fields)
            return TextEvidence(**value)

        if row.get('kind') == 'identity':
            identities.append(IdentityReference(row['indicator_id'], row['entity'], span('claim'),
                                                 tuple(row['authorized_domains']), ref,
                                                 row.get('delegation_audited', False)))
        elif row.get('kind') == 'authority':
            reviews.append(AuthorityReview(span('role'), span('directive'), row['authorization'], ref))
        else:
            raise ValueError('Unknown independent reference kind')
    return DetectorContext(tuple(identities), tuple(reviews))


def validate_matched(matrices, dictionaries, *, folds=5):
    """Metadata/representation conformance only; cannot establish label truth."""
    if set(matrices) != {'E1', 'E2', 'E3'} or set(dictionaries) != set(matrices) or type(folds) is not int or folds < 2:
        raise ValueError('Three explicit matched representations and at least two folds required')
    technical, behavior = dictionaries['E1'], dictionaries['E2']
    forbidden = set(METADATA) | {'label', 'source_row_id', 'source_file', 'filename', 'record_id'}
    for features in dictionaries.values():
        if (not isinstance(features, list) or not features
                or any(type(f) is not str or not f or f.casefold() in forbidden
                       or f.casefold().startswith(('source_', 'target_', 'group_', 'partition_', 'cv_fold_')) for f in features)
                or len(set(features)) != len(features)):
            raise ValueError('Explicit nonempty unique predictor dictionaries without metadata required')
    if set(technical) & set(behavior) or dictionaries['E3'] != technical + behavior:
        raise ValueError('E3 must concatenate disjoint technical E1 and behavioral E2 dictionaries')
    reference, populations = None, {}
    for name, rows in matrices.items():
        if not isinstance(rows, list):
            raise ValueError('Materialized matched rows required; no consumed iterator may silently disappear')
        population, group_folds = {}, {}
        classes = defaultdict(set)
        for row in rows:
            if not isinstance(row, dict) or set(row) != set(METADATA) | set(dictionaries[name]):
                raise ValueError('Unexpected row columns or leaked metadata')
            identity = row['observation_id']
            if (type(identity) is not str or not identity or identity in population
                    or any(type(row[k]) is not str or not row[k] for k in ('source_dataset', 'group_id'))
                    or row['partition'] != 'development' or type(row['target']) is not int
                    or row['target'] not in (0, 1) or type(row['cv_fold']) is not int
                    or row['cv_fold'] not in range(1, folds + 1)):
                raise ValueError('Invalid/duplicate identity, class, partition or fold')
            reject_excluded(row['source_dataset'])
            old = group_folds.setdefault(row['group_id'], row['cv_fold'])
            if old != row['cv_fold']:
                raise ValueError('Group crosses validation folds')
            classes[row['cv_fold']].add(row['target'])
            for feature in dictionaries[name]:
                value = row[feature]
                if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
                    raise ValueError('Only finite numeric predictors or explicit missing values allowed')
            population[identity] = tuple(row[k] for k in METADATA)
        if not population or any(classes[f] != {0, 1} for f in range(1, folds + 1)):
            raise ValueError('Both classes are required in each outer validation fold')
        if reference is None:
            reference = population
        elif population != reference:
            raise ValueError('Unmatched population, labels, groups or assignments')
        populations[name] = {r['observation_id']: r for r in rows}
    for identity, combined in populations['E3'].items():
        if any(combined[f] != populations[family][identity][f]
               for family, features in [('E1', technical), ('E2', behavior)] for f in features):
            raise ValueError('E3 values differ from matched component representations')
    sources = defaultdict(set)
    for row in populations['E1'].values():
        sources[row['source_dataset']].add(row['target'])
    return {'structural_conformance': True, 'observations': len(reference),
            'complete_source_class_confounding': all(len(labels) == 1 for labels in sources.values()),
            'feature_semantics_independently_accepted': False, 'scientifically_admitted': False}


def build_acceptance_packet():
    """Read existing aggregate metadata and one matrix header, never research rows."""
    gate_path = ROOT / 'docs/research/2026-11-17_scientific_validation/research-gate.json'
    gate = json.loads(gate_path.read_text())
    run = E2 / 'primary_v53_features_run01'
    receipt = json.loads((run / 'extraction_receipt.json').read_text())
    assessment = json.loads((run / 'representation_assessment.json').read_text())
    candidate = E2 / 'candidate_context_v6.py'
    if receipt['candidate'] != 'V5.3' or _sha(candidate.read_bytes()) != receipt['candidate_sha256']:
        raise ValueError('V5.3 candidate/receipt mismatch; do not repeat extraction')
    with (run / 'e2-e.csv').open(newline='', encoding='utf-8-sig') as stream:
        header = next(csv.reader(stream))
    if header[:len(METADATA)] != list(METADATA) or len(header) != 102:
        raise ValueError('Expected explicit V5.3 E2-E metadata plus 96 predictors')
    evidence_files = {
        'population': ['v42_exact_run_acceptance_packet.json'],
        'source_labels': ['external_source_provenance.json', 'primary_source_label_evidence.json'],
        'identity': ['historical_identity_code_evidence.json', 'lineage_resolution_record.json'],
        'assignments': ['historical_grouping_verification_receipt.json'],
        'custody': ['researcher_authorization_record.json', 'restricted_delivery/delivery_receipt.json'],
        'behavior': ['candidate_context_v6.py', 'integrated_behavioral_rules_v42.json'],
        'dictionaries': ['ordered_predictor_dictionary.json', 'supplementary_feature_dictionary.json'],
        'evaluation': ['proposed_classifier_search.json', 'nested_experimental_engine.py', 'nested_calibration.py'],
        'leakage': ['experiment_execution_coordinator.py'],
        'reproducibility': ['primary_v53_features_run01/extraction_receipt.json', 'statistical_evaluation.py']}
    bindings = {check: [{'path': str((E2 / rel).relative_to(ROOT)), 'sha256': _sha((E2 / rel).read_bytes())}
                        for rel in files] for check, files in evidence_files.items()}
    return {'status': 'PREPARED_NOT_ADMITTED', 'classifier_fitting_performed': False,
            'researcher_agreement_scope': 'engineering preparation only; no fabricated independent approvals',
            'candidate': {'path': str(candidate.relative_to(ROOT)), 'sha256': receipt['candidate_sha256']},
            'persisted_extraction_receipt': receipt,
            'latest_in_sample_diagnostics': {k: v for k, v in assessment['results'].items() if k.startswith('v53_')},
            'diagnostics_are_classifier_performance': False,
            'gate_sha256': _sha(gate_path.read_bytes()), 'gate_status': gate['status'],
            'outstanding_checks': gate['checks'],
            'supporting_evidence_not_acceptance': bindings,
            'pilot': [{'target': target, 'supported': supported, 'count': count} for (target, supported), count in PILOT.items()],
            'pilot_protocol': 'diagnostic allocation, one observation per established group; no prevalence claim',
            'blank_human_response': blank_response(),
            'e2e_predictors_pending_acceptance': header[len(METADATA):],
            'matched_evaluation': {'families': FAMILIES, 'outer_folds': 5, 'inner_folds': 3, 'seed': 42,
                'runner': 'experiments/e2_enrichment_20261124/nested_experimental_engine.py',
                'calibration': 'experiments/e2_enrichment_20261124/nested_calibration.py',
                'statistics': 'experiments/e2_enrichment_20261124/statistical_evaluation.py',
                'settings_proposal': 'experiments/e2_enrichment_20261124/proposed_classifier_search.json',
                'e1_dictionary': None, 'e3_dictionary': None,
                'required': ['matched development identities/groups/folds', 'no reserved records',
                    'inner-training preprocessing and tuning', 'cross-fitted training calibration',
                    'training-only thresholds', 'report all valid configurations and failures',
                    'AP/F1/precision/recall/ROC-AUC/Brier/fold metrics/group-bootstrap intervals',
                    'coverage, ablations, error analysis and source-confounding limitations']},
            'decisions_required': ['prospective supplementary population with comparable class collection',
                'phishing-specific native label validation; no spam relabeling',
                'source/access/protocol acceptance before annotation delivery',
                'two independent humans and separately documented adjudication',
                'authenticated artifact-linked identity/authority/delegation references',
                'accepted E1/E2/E3 dictionaries and exact nested settings',
                'adviser/institutional approval where required and all ten admission checks'],
            'ingestion_entrypoints': ['ml.source_acquisition.acquire_zenodo', 'ml.research_protocol.prospective_id',
                'ml.prospective_allocation.connected_groups', 'ml.prospective_allocation.allocate'],
            'independent_behavioral_validation': False, 'scientific_admission': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--inspect', type=Path)
    args = parser.parse_args()
    if bool(args.output) == bool(args.inspect):
        parser.error('Choose one exclusive preparation output or metadata inspection')
    if args.inspect:
        packet = json.loads(args.inspect.read_text())
        print(packet['status'], '; outstanding admission checks:', len(packet['outstanding_checks']), '; no fitting')
        return
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.local'):
        parser.error('Preparation outputs must remain under ignored canonical .local/')
    packet = build_acceptance_packet()
    output.mkdir(parents=True, exist_ok=False)  # never overwrite existing receipts
    (output / 'exact-run-acceptance.json').write_text(json.dumps(packet, indent=2) + '\n')
    print('Prepared aggregate acceptance packet and blank response; no emails, human judgments or fits generated')


if __name__ == '__main__':
    main()
