from dataclasses import replace

import pytest

from ml.preprocessing import TextEvidence, preprocess
from ml.se_brl.detectors import AuthorityReview, DetectorContext, IdentityReference
from ml.se_brl.extraction import RuleEngine
from ml.se_brl.representation import BrlRepresentation
from ml.tests.test_preprocessing import email


def artifact(text, **fields):
    return preprocess(email(text, sender=fields.pop("sender", "a@outside.test"), **fields))


def claim(text="We are Acme", **fields):
    return artifact(text, **fields), TextEvidence("body", 0, len(text), text, "body")


def reference(span, indicator="impersonation", **fields):
    return IdentityReference(indicator, "Acme", span, ("acme.test",), "fixture-independent-audit", **fields)


@pytest.mark.parametrize("text", [
    "Do not share your password.", "We will never ask for your password.",
    "Scammers may say your account will be suspended.",
    "Example phishing email: verify your account immediately.",
    "Don’t SHARE your password!", "The email said: share your password.",
    'The message reads: “Your account will be suspended.”',
    "Security awareness. Your account will be suspended.",
    "Share your password. This is a phishing example.",
    "BEGIN FORWARDED MESSAGE:\nShare your password.",
    "on monday alex wrote:\nAct now!",
    '"Share your password',
])
def test_context_abstains_without_losing_evidence(text):
    prepared = artifact(text)
    result = RuleEngine().extract(prepared)
    assert not any(i.evidence for i in result.indicators)
    assert "".join(s.text for s in prepared.segments) == text


def test_duplicate_segments_deduplicated_but_rule_overlap_retained():
    prepared = artifact("SHARE\tYOUR PASSWORD! Submit your password.")
    prepared = replace(prepared, segments=prepared.segments * 2)
    result = RuleEngine().extract(prepared)
    by_id = {i.indicator_id: i for i in result.indicators}
    assert len(by_id["credential_sensitive_data_request"].evidence) == 2
    assert len(by_id["call_to_action"].evidence) == 1
    assert by_id["credential_sensitive_data_request"].evidence[0].span.text == "SHARE\tYOUR PASSWORD"


def test_authority_role_alone_and_unreviewed_directive_do_not_assert_manipulation():
    engine = RuleEngine()
    alone = engine.extract(artifact("I am your CEO."))
    assert not alone.detector_reports[0].observations
    result = engine.extract(artifact("As your administrator, submit your password."))
    observation = result.detector_reports[0].observations[0]
    assert [s.text for s in observation.spans] == ["As your administrator", "submit your password"]
    authority = next(i for i in result.indicators if i.indicator_id == "authority")
    assert authority.evaluation_status == "not_evaluated" and not authority.evidence


@pytest.mark.parametrize("authorization,state", [("authorized", "absent"), ("contradicted", "supported"), ("unknown", None)])
def test_authority_independent_review(authorization, state):
    prepared = artifact("As your administrator, submit your password.")
    engine = RuleEngine()
    observation = engine.extract(prepared).detector_reports[0].observations[0]
    review = AuthorityReview(*observation.spans, authorization, "fixture-authorization-audit")
    result = engine.extract(prepared, DetectorContext(authority_reviews=(review,)))
    authority = next(i for i in result.indicators if i.indicator_id == "authority")
    assert authority.evidence_state == state
    if authority.evidence:
        assert authority.evidence[0].supporting_spans == observation.spans[1:]
    assert BrlRepresentation(result).z_values == (None,) * 4


@pytest.mark.parametrize("indicator", ["impersonation", "brand_exploitation"])
def test_explicit_claim_with_independent_domain_conflict(indicator):
    prepared, span = claim()
    result = RuleEngine().extract(prepared, DetectorContext((reference(span, indicator, delegation_audited=True),)))
    finding = next(i for i in result.indicators if i.indicator_id == indicator)
    assert finding.evidence_state == "supported"
    assert finding.evidence[0].span == span
    assert finding.evidence[0].supporting_spans[0].text == "a@outside.test"
    assert finding.evidence[0].reference_id == "fixture-independent-audit"
    BrlRepresentation(result)


def test_brand_mention_alone_missing_reference_or_unknown_delegation_abstains():
    for text in ("Acme", "We are Acme"):
        prepared, span = claim(text)
        for refs in ((), (reference(span),)):
            result = RuleEngine().extract(prepared, DetectorContext(refs))
            assert all(i.evaluation_status == "not_evaluated" for i in result.indicators if i.indicator_id in {"impersonation", "brand_exploitation"})
    prepared, span = claim("Acme")
    result = RuleEngine().extract(prepared, DetectorContext((reference(span, delegation_audited=True),)))
    assert not result.detector_reports[1].evaluated


def test_aligned_identity_and_sender_reply_mismatch_require_audited_reference():
    prepared, span = claim(sender="a@acme.test", reply_to="b@outside.test")
    assert not RuleEngine().extract(prepared).detector_reports[1].evaluated
    result = RuleEngine().extract(prepared, DetectorContext((reference(span, delegation_audited=True),)))
    assert result.detector_reports[1].qualifying[0].spans[-1].field == "reply_to"
    aligned, span = claim(sender="a@acme.test")
    result = RuleEngine().extract(aligned, DetectorContext((reference(span, delegation_audited=True),)))
    indicator = next(i for i in result.indicators if i.indicator_id == "impersonation")
    assert indicator.evidence_state == "absent"


def test_bad_locators_and_contradictory_reviews_rejected():
    prepared, span = claim()
    with pytest.raises(ValueError, match="belong"):
        RuleEngine().extract(prepared, DetectorContext((reference(replace(span, text="wrong"), delegation_audited=True),)))
    with pytest.raises(ValueError, match="contradictory"):
        DetectorContext((reference(span), reference(span)))
    with pytest.raises(ValueError):
        replace(reference(span), authorized_domains=("*.test",))


def test_url_modality_never_becomes_behavior_from_references():
    _, span = claim()
    result = RuleEngine().extract(preprocess({"kind": "url", "url": "https://outside.test"}),
                                  DetectorContext((reference(span, delegation_audited=True),)))
    assert all(i.evidence_state == "unavailable" and not i.evidence for i in result.indicators)
    assert all(not r.evaluated and not r.qualifying and not r.observations for r in result.detector_reports)


def test_missing_conditional_evidence_does_not_leak_authority_observations():
    prepared = preprocess({"kind": "email", "subject": "As your administrator, submit your password."})
    result = RuleEngine().extract(prepared)
    assert result.assessment.availability_mask[2] == 0
    assert all(not r.evaluated and not r.qualifying and not r.observations for r in result.detector_reports)


def test_webpage_identity_uses_page_locator_and_does_not_treat_mentions_as_claims():
    prepared = preprocess({"kind": "webpage", "html": "<p>We are Acme</p>", "page_url": "https://outside.test"})
    span = prepared.segments[0]
    result = RuleEngine().extract(prepared, DetectorContext((reference(span, "brand_exploitation", delegation_audited=True),)))
    evidence = next(i for i in result.indicators if i.indicator_id == "brand_exploitation").evidence
    assert evidence[0].supporting_spans[0].field == "page_url"


def test_partially_audited_identity_claims_do_not_become_absent():
    prepared = artifact("We are Acme. We are Acme", sender="a@acme.test")
    first = TextEvidence("body", 0, 11, "We are Acme", "body")
    second = TextEvidence("body", 13, 24, "We are Acme", "body")
    result = RuleEngine().extract(prepared, DetectorContext((reference(first, delegation_audited=True), reference(second))))
    assert not result.detector_reports[1].evaluated
