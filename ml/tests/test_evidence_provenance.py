"""Encoder mechanism tests, not authored phishing/behavioral accuracy cases."""
from types import SimpleNamespace as Record

import pytest

from ml.evidence_provenance import rule_provenance


def fixture(rule_id='rule.a'):
    rules = tuple(Record(rule_id='rule.' + name, indicator_id='urgency') for name in ('a', 'b'))
    evidence = Record(rule_id=rule_id, indicator_id='urgency', ruleset_version='fixture', provenance='rule-based')
    indicator = Record(indicator_id='urgency', evaluation_status='rule_evaluated',
                       evidence_state='supported', evidence=[evidence])
    return Record(indicators=[indicator], ruleset_version='fixture'), rules


def test_rule_identity_survives_equal_rule_count_collision():
    left, rules = fixture('rule.a')
    right, _ = fixture('rule.b')
    assert len(left.indicators[0].evidence) == len(right.indicators[0].evidence)
    assert rule_provenance(left, rules) == {'rule_evidence__rule.a': 1, 'rule_evidence__rule.b': 0}
    assert rule_provenance(right, rules) == {'rule_evidence__rule.a': 0, 'rule_evidence__rule.b': 1}


@pytest.mark.parametrize('status', ['not_evaluated', 'unavailable'])
def test_missing_opportunity_is_not_negative(status):
    result, rules = fixture()
    result.indicators[0].evaluation_status = status
    assert set(rule_provenance(result, rules).values()) == {None}


@pytest.mark.parametrize('change', ['semantic', 'version', 'absent', 'duplicate'])
def test_invalid_evidence_cannot_be_promoted(change):
    result, rules = fixture()
    if change == 'semantic': result.indicators[0].evidence[0].provenance = 'model-generated'
    if change == 'version': result.indicators[0].evidence[0].ruleset_version = 'other'
    if change == 'absent': result.indicators[0].evidence_state = 'absent'
    if change == 'duplicate': rules = rules + (rules[0],)
    with pytest.raises(ValueError): rule_provenance(result, rules)


def test_no_metadata_or_unknown_rule_predictor_is_introduced():
    result, rules = fixture('unknown.detector')
    result.target = 1; result.source_dataset = 'synthetic-only'
    features = rule_provenance(result, rules)
    assert set(features) == {'rule_evidence__rule.a', 'rule_evidence__rule.b'}
    assert set(features.values()) == {0}
