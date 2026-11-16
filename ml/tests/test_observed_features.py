from dataclasses import replace

import pytest

from ml.observed_features import observed_conventional, conventional_dictionary
from ml.preprocessing import preprocess, TextEvidence
from ml.se_brl.detectors import DetectorContext, IdentityReference


def test_missing_email_surfaces_are_unknown_not_false_or_zero():
    result = observed_conventional(preprocess({"kind":"email","subject":"Synthetic notice"}))
    assert result.values["model_text"] == "synthetic notice"
    for name in ("sender_reply_domain_differ","header_count","message_id_present","embedded_url_count","observed_brand_domain_mismatch"):
        assert result.values["conventional:"+name] is None
    assert not any(n.endswith(("body_supplied","sender_available","links_authorized")) for n in result.values)
    assert tuple(result.values) == tuple(n for n,_ in conventional_dictionary(result.modality))


def test_known_empty_links_headers_and_relations_are_not_missing():
    artifact = preprocess({"kind":"email","subject":"Hello","urls":[],"link_extraction_authorized":True,
        "headers":{},"sender":"sender@example.test","reply_to":"reply@other.test"})
    values = observed_conventional(artifact).values
    assert values["conventional:embedded_url_count"] == values["conventional:header_count"] == 0
    assert values["conventional:sender_reply_domain_differ"] == 1
    assert values["conventional:message_id_present"] is None
    with pytest.raises(TypeError): values["target"] = 1


def test_web_dom_and_own_url_are_separate_from_unknown_embedded_links():
    text_only = observed_conventional(preprocess({"kind":"webpage","visible_text":"Synthetic content","page_url":"https://example.test/"}))
    assert text_only.values["conventional:form_count"] is None
    assert text_only.values["conventional:embedded_url_count"] is None
    assert text_only.values["conventional:page_url_max_length"] == len("https://example.test/")
    html = observed_conventional(preprocess({"kind":"webpage","html":'<p>Synthetic</p><form><input type="password"></form><a href="/">Home</a>',
        "page_url":"https://example.test/","link_extraction_authorized":True}))
    assert html.values["conventional:form_count"] == html.values["conventional:password_input_count"] == 1
    assert html.values["conventional:embedded_url_count"] == 1  # same URL still has an embedded source locator
    assert html.values["conventional:resource_element_count"] == 0


def test_brand_relation_needs_audited_linked_independent_reference():
    artifact = preprocess({"kind":"email","subject":"We are Acme","sender":"contact@example.test"})
    claim = TextEvidence("subject",0,11,"We are Acme","subject")
    reference = IdentityReference("brand_exploitation","Acme",claim,("example.test",),"synthetic:independent-reference",True)
    context=DetectorContext((reference,))
    assert observed_conventional(artifact,identity_context=context).values["conventional:observed_brand_domain_mismatch"] == 0
    mismatch=DetectorContext((replace(reference,authorized_domains=("other.test",)),))
    assert observed_conventional(artifact,identity_context=mismatch).values["conventional:observed_brand_domain_mismatch"] == 1
    unaudited=DetectorContext((replace(reference,delegation_audited=False),))
    assert observed_conventional(artifact,identity_context=unaudited).values["conventional:observed_brand_domain_mismatch"] is None
    wrong=DetectorContext((replace(reference,claim=replace(claim,text="Other claim")),))
    with pytest.raises(ValueError,match="does not belong"):
        observed_conventional(artifact,identity_context=wrong)


def test_technical_record_cannot_become_a_content_baseline():
    with pytest.raises(ValueError,match="cannot replace"):
        observed_conventional(preprocess({"kind":"technical"}))
