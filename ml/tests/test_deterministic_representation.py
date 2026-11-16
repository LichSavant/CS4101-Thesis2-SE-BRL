"""Proposal Table 4.13: deterministic bits, no learned behavioral prerequisite."""
import pytest

from ml.features import ConventionalFeatureBuilder, FeatureUnavailableError
from ml.development_experiments import behavioral_columns
from ml.pipeline import PretrainingPipeline
from ml.preprocessing import preprocess
from ml.se_brl.extraction import RuleEngine
from ml.se_brl.representation import BrlRepresentation


def test_e2_order_matches_development_contract_and_no_model_is_fitted():
    pipeline = PretrainingPipeline(ConventionalFeatureBuilder(include_tfidf=False))
    result = pipeline.run({"kind": "email", "subject": "Act now! Share your password."})
    e1, e2, e3 = result.features
    assert tuple(e2.block.values) == behavioral_columns()
    assert e2.block.values["pressure_threat_cues_supported"] == 1
    assert e2.block.values["requested_action_consequence_supported"] == 1
    assert e2.block.values["trust_identity_manipulation_supported"] == 0
    assert e2.block.values["trust_identity_manipulation_available"] == 0
    assert dict(e3.block.values) == dict(e1.block.values) | dict(e2.block.values)
    assert e2.block.require_numeric()
    assert result.envelope.overall_status == "not_evaluated"  # no classifier/risk claim
    assert all(i.evidence_state == "unavailable" for i in result.representation.extraction.indicators
               if i.dimension_id == "trust_identity_manipulation")


def test_unevaluated_rule_cannot_turn_into_a_negative_model_input():
    pipeline = PretrainingPipeline(ConventionalFeatureBuilder(include_tfidf=False), rules=RuleEngine(rules=()))
    result = pipeline.run({"kind": "email", "subject": "Observe only."})
    e2 = result.features[1]
    assert e2.block.missing_components == ("behavioral_evaluation_incomplete",)
    assert e2.block.values["pressure_threat_cues_supported"] is None
    assert e2.block.values["pressure_threat_cues_available"] is None
    with pytest.raises(FeatureUnavailableError):
        e2.block.require_numeric()
    assert result.representation.unevaluated_indicators


@pytest.mark.parametrize("raw", ({"kind": "url", "url": "https://example.test/act-now"},
    {"kind": "technical"}))
def test_technical_evidence_is_wholly_unavailable_not_assessed_absent(raw):
    result = BrlRepresentation(RuleEngine().extract(preprocess(raw)))
    assert result.deterministic_slots == (0,)*8
    assert all(i.evidence_state == "unavailable" for i in result.extraction.indicators)


def test_legacy_placeholder_layout_remains_separate_and_cannot_reenter_features():
    result = PretrainingPipeline(ConventionalFeatureBuilder(include_tfidf=False)).run({"kind": "email", "subject": "Hello"})
    assert result.representation.slots[:4] == (None,)*4  # historical accessor only
    assert tuple(result.features[1].block.values) == behavioral_columns()
    assert result.features[1].schema.schema_version == "0.2.0"
