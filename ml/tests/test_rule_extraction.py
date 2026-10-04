from dataclasses import replace

import pytest

from ml.preprocessing import preprocess
from ml.se_brl import load_codebook
from ml.se_brl.extraction import RuleEngine
from ml.se_brl.representation import BrlRepresentation
from ml.se_brl.rules import Rule
from ml.tests.test_preprocessing import email


def extract(text):
    return RuleEngine().extract(preprocess(email(text, sender="sender@example.test")))


@pytest.mark.parametrize(("indicator", "text"), [
    ("urgency", "Act now!"),
    ("fear_threat", "Your account will be suspended."),
    ("scarcity", "Claim yours before it expires."),
    ("curiosity", "Click here to find out."),
    ("reward_lure", "Click here to claim your prize."),
    ("confidentiality_isolation", "Do not contact your bank."),
    ("call_to_action", "Click here."),
    ("credential_sensitive_data_request", "Please share your password."),
    ("financial_action_request", "Transfer the funds."),
])
def test_each_rule_family_has_exact_evidence(indicator, text):
    result = next(i for i in extract(text).indicators if i.indicator_id == indicator)
    assert result.evidence_state == "supported"
    assert result.evaluation_status == "rule_evaluated"
    for evidence in result.evidence:
        span = evidence.span
        assert text[span.start:span.end] == span.text
        assert evidence.provenance == "rule-based"
        assert evidence.ruleset_version == "0.2.0"


@pytest.mark.parametrize("text", [
    "Do not share your password with anyone.", "Never enter your password here.",
    "We will never ask you to provide your password.",
    "A phishing example: share your password.", 'The notice says "share your password".',
    "The notice says 'share your password'.",
    "> Share your password.", "On Monday Alex wrote:\nShare your password.",
    "The meeting is on Monday.", "Your invoice was paid.", "Password safety tips.",
    "Do not click here.", "Do not act now.", "Do not transfer the funds.",
    "Training example: do not contact your bank.",
])
def test_negation_quotes_and_counterexamples(text):
    assert not any(i.evidence for i in extract(text).indicators)


def test_inline_html_negation_and_blockquote():
    artifact = preprocess(dict(kind="webpage", html='<p>Do not <b>share your password</b>.</p><blockquote>Act now!</blockquote>'))
    assert not any(i.evidence for i in RuleEngine().extract(artifact).indicators)


def test_multiple_overlapping_spans_are_retained_without_count_scores():
    result = extract("Submit your password. Submit your password.")
    by_id = {i.indicator_id: i for i in result.indicators}
    assert len(by_id["credential_sensitive_data_request"].evidence) == 2
    assert len(by_id["call_to_action"].evidence) == 2
    assert by_id["credential_sensitive_data_request"].evidence[0].span == by_id["call_to_action"].evidence[0].span
    representation = BrlRepresentation(result)
    assert representation.slots == (None, None, None, None, 1, 1, 1, 1)
    assert set(representation.unevaluated_indicators) == {"authority", "impersonation", "brand_exploitation"}
    assert len(result.indicators) == 12


@pytest.mark.parametrize("raw", [{"kind": "url", "url": "https://act-now.test/password"}, {"kind": "technical"}, {"kind": "email"}])
def test_unavailable_is_not_absent(raw):
    result = RuleEngine().extract(preprocess(raw))
    assert result.assessment.availability_mask == (0, 0, 0, 0)
    assert all(i.evidence_state == "unavailable" and not i.evidence for i in result.indicators)


def test_conditional_evidence_mask_and_deferred_detectors():
    result = RuleEngine().extract(preprocess({"kind": "email", "subject": "Do not contact your bank."}))
    assert result.assessment.availability_mask == (1, 1, 0, 1)
    assert not any(i.evidence for i in result.indicators)
    assert tuple(d.dimension_id for d in result.assessment.dimension_results) == load_codebook()["vector_ordering"]["dimension_order"]


def test_invalid_registry_and_forged_representation_rejected():
    with pytest.raises(ValueError):
        RuleEngine((Rule("rule", "made_up_indicator", "x"),))
    result = extract("Act now!")
    with pytest.raises(ValueError):
        BrlRepresentation(result, (0.1, 0.2, 0.3, 0.4))
    with pytest.raises(ValueError):
        BrlRepresentation(replace(result, indicators=result.indicators[:-1]))
    forged = replace(result.indicators[0], evidence=())
    with pytest.raises(ValueError):
        BrlRepresentation(replace(result, indicators=(forged,) + result.indicators[1:]))
