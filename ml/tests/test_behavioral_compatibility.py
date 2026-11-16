"""Synthetic metadata/vector contracts only; no inference or model fitting."""
from copy import deepcopy

import pytest

from ml.behavioral_compatibility import BehavioralCompatibilityError, review_contract, review_rule_vector
from ml.se_brl.codebook import load_codebook


def descriptor():
    book = load_codebook()
    return dict(contract_version='1.0.0', codebook_version=book['codebook_version'],
                source_schema_version=book['schema_version'],
                dimension_order=list(book['vector_ordering']['dimension_order']),
                indicator_order=[i['id'] for d in book['dimensions'] for i in d['indicators']],
                learned_feature_order=list(book['vector_ordering']['future_structure']),
                approved_for_E2_E3=False)


def names():
    return tuple(f'{d}_{s}' for s in ('supported', 'available')
                 for d in ('pressure_threat', 'lure_attention', 'trust_identity', 'requested_action_consequence'))


def test_structural_match_never_grants_authority_or_mutates_input():
    supplied = descriptor()
    before = deepcopy(supplied)
    for approval in (False, True, 'approved'):
        supplied['approved_for_E2_E3'] = approval
        result = review_contract(supplied)
        assert result.structurally_compatible and not result.research_ready
        assert len(result.policy_blockers) == 3
    supplied['approved_for_E2_E3'] = False
    assert supplied == before


@pytest.mark.parametrize('field', ['contract_version', 'codebook_version', 'source_schema_version',
                                  'dimension_order', 'indicator_order', 'learned_feature_order'])
def test_each_version_or_order_mismatch_blocks_vector_review(field):
    supplied = descriptor()
    supplied[field] = 'PRIVATE malformed metadata'
    assert field in review_contract(supplied).mismatches
    with pytest.raises(BehavioralCompatibilityError, match='^incompatible_representation_contract$'):
        review_rule_vector(supplied, representation_type='rule_derived_binary_v1', feature_names=names(), values=(0,) * 8)


def test_explicit_name_mapping_preserves_unknown_unavailable_and_assessed_absence():
    values = (1, None, 0, 0, 1, None, 0, 1)
    result = review_rule_vector(descriptor(), representation_type='rule_derived_binary_v1', feature_names=names(), values=values)
    assert result.values == values and not result.numeric_complete
    assert result.feature_names[0] == 'pressure_threat_cues_supported'
    assert not result.review.research_ready
    same = review_rule_vector(descriptor(), representation_type=result.representation_type,
                            feature_names=result.feature_names, values=values)
    assert same == result


@pytest.mark.parametrize('kind', ['semantic_candidate_v1', 'validated_behavioral_decision_v1',
                                 'learned_dimension_values_v1', 'unknown', None])
def test_nonrule_representations_never_become_numeric_rule_evidence(kind):
    with pytest.raises(BehavioralCompatibilityError, match='only_rule_binary_review_supported'):
        review_rule_vector(descriptor(), representation_type=kind, feature_names=names(), values=(0,) * 8)


@pytest.mark.parametrize('values', [(True,) * 8, (0.0,) * 8, (float('nan'),) * 8,
                                   (1, 0, 0, 0, 0, 1, 1, 1),
                                   (None, 0, 0, 0, 1, 1, 1, 1), (0,) * 7, [0] * 8])
def test_malformed_or_contradictory_vectors_rejected(values):
    with pytest.raises(BehavioralCompatibilityError):
        review_rule_vector(descriptor(), representation_type='rule_derived_binary_v1', feature_names=names(), values=values)


@pytest.mark.parametrize('dictionary', [names()[::-1], names()[:-1], ('z1',) * 8, list(names())])
def test_no_implicit_reordering_dictionary_inference_or_z_aliases(dictionary):
    with pytest.raises(BehavioralCompatibilityError, match='unknown_or_reordered_feature_dictionary'):
        review_rule_vector(descriptor(), representation_type='rule_derived_binary_v1', feature_names=dictionary, values=(0,) * 8)


def test_complete_unavailable_vector_remains_review_only():
    result = review_rule_vector(descriptor(), representation_type='rule_derived_binary_v1', feature_names=names(), values=(0,) * 8)
    assert result.numeric_complete and not result.review.research_ready


def test_invalid_descriptor_is_sanitized():
    with pytest.raises(BehavioralCompatibilityError, match='^invalid_representation_descriptor$'):
        review_contract('PRIVATE')
