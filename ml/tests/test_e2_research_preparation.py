"""Synthetic engineering tests only; no research records, labels or fitting."""
from copy import deepcopy
import hashlib
import json

import pytest

from ml import e2_research_preparation as prep
from ml.annotation_validation import indicator_ids, validate_judgment
from ml.preprocessing import preprocess
from ml.research_policy import ResearchPolicyError
from ml.se_brl.extraction import RuleEngine


def metadata():
    return [{'record_id': f'synthetic-{target}-{supported}-{n}', 'group_id': f'g-{target}-{supported}-{n}',
             'content_sha256': hashlib.sha256(f'{target}-{supported}-{n}'.encode()).hexdigest(),
             'source_dataset': 'synthetic-only', 'partition': 'development',
             'target': target, 'supported': supported}
            for target, supported in prep.PILOT for n in range(80)]


def test_pilot_exact_reproducible_blended_and_group_unique():
    rows = metadata()
    selected = prep.sample_pilot(rows)
    assert selected == prep.sample_pilot(list(reversed(rows)))
    assert len(selected) == len({r['group_id'] for r in selected}) == 200
    assert {(t, s): sum((r['target'], r['supported']) == (t, s) for r in selected)
            for t, s in prep.PILOT} == prep.PILOT
    assert selected != prep.sample_pilot(rows, seed=43)


def test_matching_recovers_feasible_allocation_instead_of_greedy_shortage():
    rows = metadata()
    # One shared group crosses strata; each group can enter at most one slot.
    rows[80]['group_id'] = rows[0]['group_id']
    selected = prep.sample_pilot(rows)
    assert len({r['group_id'] for r in selected}) == 200


@pytest.mark.parametrize('change', ['reserved', 'duplicate', 'bad_target', 'bad_support', 'duplicate_group'])
def test_sampling_rejects_unsafe_metadata(change):
    rows = metadata()
    if change == 'reserved': rows[0]['partition'] = 'test'
    if change == 'duplicate': rows[1]['record_id'] = rows[0]['record_id']
    if change == 'bad_target': rows[0]['target'] = True
    if change == 'bad_support': rows[0]['supported'] = 1
    if change == 'duplicate_group': rows[1]['content_sha256'] = rows[0]['content_sha256']
    with pytest.raises(ValueError): prep.sample_pilot(rows)


def test_pilot_shortage_does_not_reallocate_or_sample_twice():
    with pytest.raises(ValueError, match='distinct groups'):
        prep.sample_pilot(metadata()[:10])


def test_real_ingestion_and_packets_are_blocked_before_input_consumption():
    class ForbiddenInput:
        def __iter__(self): pytest.fail('Content must not be consumed before admission')
    with pytest.raises(ResearchPolicyError):
        prep.prepare_annotation_delivery(ForbiddenInput(), ForbiddenInput())
    with pytest.raises(ResearchPolicyError):
        prep.prepare_ingestion(ForbiddenInput(), 'synthetic-only', 'a'*64, 'synthetic.csv', [], policy_reference='synthetic')


def test_blank_response_cannot_masquerade_as_human_validation():
    response = prep.blank_response()
    assert set(response['indicators']) == set(indicator_ids())
    assert all(v is None for v in response['indicators'].values())
    assert response['independent'] is None
    with pytest.raises(ValueError): validate_judgment(response, {'body': 'Synthetic text'})


def test_annotation_custody_binding_rejects_replaced_fields_and_duplicate_ids():
    fields = {'body': 'Synthetic engineering fixture'}
    selected = [{'record_id': 'synthetic', 'group_id': 'group', 'source_dataset': 'synthetic-only',
                 'content_sha256': hashlib.sha256(json.dumps(fields, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}]
    record = {'record_id': 'synthetic', 'group_id': 'group', 'source_dataset': 'synthetic-only',
              'partition': 'development', 'fields': fields}
    assert prep._bound_annotation_records([record], selected) == [record]
    with pytest.raises(ValueError): prep._bound_annotation_records([record, record], selected)
    with pytest.raises(ValueError): prep._bound_annotation_records([{**record, 'fields': {'body': 'Changed'}}], selected)
    with pytest.raises(ValueError): prep._bound_annotation_records([], selected)


def trust_fixture():
    fields = {'subject': 'Synthetic example', 'body': 'We are Example', 'sender': 'notice@other.example'}
    record = {'kind': 'identity', 'reference_id': 'synthetic-independent-document',
              'document_sha256': 'a'*64,
              'artifact_sha256': hashlib.sha256(json.dumps(fields, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
              'independent_of_labels_and_model': True, 'verified_by': 'synthetic-custodian',
              'source_uri': 'https://independent.example/reference',
              'verified_on': '2026-11-25', 'indicator_id': 'impersonation', 'entity': 'Example',
              'claim': {'field': 'body', 'start': 0, 'end': 14, 'text': 'We are Example', 'location': 'body'},
              'authorized_domains': ['example.org'], 'delegation_audited': True}
    return fields, record


def test_trust_import_requires_external_anchor_and_exact_original_span():
    fields, record = trust_fixture()
    with pytest.raises(ValueError): prep.import_trust_context(fields, [record], trusted_document_hashes={})
    anchored = {record['reference_id']: record['document_sha256']}
    context = prep.import_trust_context(fields, [record], trusted_document_hashes=anchored)
    assert len(context.identities) == 1
    bad = deepcopy(record); bad['claim']['start'] = True
    with pytest.raises(ValueError): prep.import_trust_context(fields, [bad], trusted_document_hashes=anchored)
    with pytest.raises(ValueError): prep.import_trust_context({**fields, 'body': 'Changed'}, [record], trusted_document_hashes=anchored)


def test_missing_reference_import_keeps_trust_unevaluated():
    artifact = preprocess({'kind': 'email', 'subject': 'Synthetic', 'body': 'We are Example',
                           'sender': 'notice@other.example', 'body_collection_authorized': True,
                           'study_purpose': 'Synthetic engineering fixture'})
    context = prep.import_trust_context({}, [], trusted_document_hashes={})
    result = RuleEngine().extract(artifact, context)
    trust = [i for i in result.indicators if i.indicator_id in ('authority', 'impersonation', 'brand_exploitation')]
    assert all(i.evidence_state not in ('supported', 'absent') for i in trust)


def matrices():
    rows = [{'observation_id': f'synthetic-{fold}-{target}', 'source_dataset': f'source-{target}',
             'group_id': f'g-{fold}-{target}', 'target': target, 'partition': 'development', 'cv_fold': fold}
            for fold in range(1, 6) for target in (0, 1)]
    return {'E1': [{**r, 'technical_count': 1} for r in rows],
            'E2': [{**r, 'urgency_supported': 0} for r in rows],
            'E3': [{**r, 'technical_count': 1, 'urgency_supported': 0} for r in rows]}, {
            'E1': ['technical_count'], 'E2': ['urgency_supported'], 'E3': ['technical_count', 'urgency_supported']}


def test_matched_preparation_flags_confounding_without_claiming_admission():
    data, dictionary = matrices()
    result = prep.validate_matched(data, dictionary)
    assert result['complete_source_class_confounding']
    assert result['structural_conformance'] and not result['scientifically_admitted']
    data['E2'].reverse()
    assert prep.validate_matched(data, dictionary)['observations'] == 10


@pytest.mark.parametrize('change', ['population', 'reserved', 'group', 'combined', 'leakage', 'nonfinite', 'class'])
def test_matched_rejects_leakage_and_misalignment(change):
    data, dictionary = matrices()
    if change == 'population': data['E2'].pop()
    if change == 'reserved': data['E1'][0]['partition'] = 'test'
    if change == 'group': data['E1'][2]['group_id'] = data['E1'][0]['group_id']
    if change == 'combined': data['E3'][0]['urgency_supported'] = 1
    if change == 'leakage': dictionary['E2'] = ['target']
    if change == 'nonfinite': data['E2'][0]['urgency_supported'] = float('nan')
    if change == 'class': data['E1'][0]['target'] = 1
    with pytest.raises(ValueError): prep.validate_matched(data, dictionary)


def test_cli_refuses_external_output_and_existing_receipt(tmp_path, monkeypatch):
    import sys
    monkeypatch.setattr(prep, 'ROOT', tmp_path)
    monkeypatch.setattr(prep, 'build_acceptance_packet', lambda: {'status': 'SYNTHETIC_PREPARATION'})
    monkeypatch.setattr(sys, 'argv', ['prepare', '--output', str(tmp_path / 'public')])
    with pytest.raises(SystemExit): prep.main()
    output = tmp_path / '.local/prepared'
    monkeypatch.setattr(sys, 'argv', ['prepare', '--output', str(output)])
    prep.main()
    receipt = output / 'exact-run-acceptance.json'
    original = receipt.read_bytes()
    with pytest.raises(FileExistsError): prep.main()
    assert receipt.read_bytes() == original
