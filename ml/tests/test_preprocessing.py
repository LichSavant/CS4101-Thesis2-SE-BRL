import pytest

from ml.preprocessing import ArtifactParserError, ArtifactValidationError, MAX_FIELD_CHARS, detect_modality, preprocess


def email(body: str, **extra: object) -> dict:
    return dict(kind="email", body=body, body_collection_authorized=True,
                study_purpose="Synthetic unit fixture", **extra)


def test_email_preserves_evidence_and_normalizes_separately():
    body = "Please  SHARE your password.\n> Act now!\nOn Monday someone wrote:\nSend money."
    result = preprocess(email(body, subject=" ＨＥＬＬＯ ", sender="Example <a@example.test>",
                              reply_to="b@example.test", headers={"Date": "Monday"}))
    assert result.model_text == "hello please share your password."
    assert result.sender == "Example <a@example.test>"
    assert result.reply_to == "b@example.test"
    assert result.headers == (("date", "Monday"),)
    for segment in result.segments:
        source = body if segment.field == "body" else " ＨＥＬＬＯ "
        assert source[segment.start:segment.end] == segment.text
    assert [s.quoted for s in result.segments[1:]] == [False, True, True, True]


def test_static_page_evidence_visibility_entities_and_structure():
    html = '<title>A &amp; B</title><script>secret</script><p hidden>hidden</p><form method="post"><input type="password" value="secret"><p>Click now.</p></form>'
    result = preprocess(dict(kind="webpage", html=html))
    assert result.model_text == "a & b click now."
    for segment in result.segments:
        assert html[segment.start:segment.end] == segment.text
    assert any(s.tag == "form" for s in result.structures)
    assert any(("type", "password") in s.attributes for s in result.structures)
    assert "secret" not in repr(result)
    assert result.conditional_evidence_available


def test_links_are_opt_in_and_relative_links_resolve():
    raw = dict(kind="webpage", html='<a href="/help">Help</a>', page_url="https://example.test/page")
    assert preprocess(raw).urls == ("https://example.test/page",)
    result = preprocess(dict(raw, link_extraction_authorized=True))
    assert result.urls == ("https://example.test/help", "https://example.test/page")
    link = result.link_evidence[0]
    assert link.original_text == "/help" and link.location.endswith("/@href")
    assert raw["html"][link.start:link.end] == '<a href="/help">'
    assert link.locator_kind == "enclosing_tag"


def test_email_link_span_and_opt_in():
    body = "Go to https://example.test/help."
    assert not preprocess(email(body)).urls
    result = preprocess(email(body, link_extraction_authorized=True))
    link = result.link_evidence[0]
    assert body[link.start:link.end] == link.original_text == link.url


@pytest.mark.parametrize("raw", [
    {}, {"kind": "unknown"}, {"kind": "url"}, {"kind": "email", "subject": 1},
    {"kind": "email", "body": "text"},
    {"kind": "email", "body": "text", "body_collection_authorized": True},
    {"kind": "email", "headers": {"Authorization": "secret"}},
    {"kind": "email", "urls": ["https://example.test"]},
    {"kind": "email", "body_collection_authorized": 1},
    {"kind": "url", "url": "https://user:secret@example.test"},
    {"kind": "url", "url": "https://[bad"},
    {"kind": "technical", "body": "Act now"},
    {"kind": "webpage", "html": "x", "visible_text": "x"},
])
def test_rejects_malformed_or_unauthorized_input(raw):
    with pytest.raises(ArtifactValidationError):
        preprocess(raw)


@pytest.mark.parametrize(("kind", "modality"), [
    ("email", "content_bearing_email"), ("webpage", "content_bearing_webpage"),
    ("url", "standalone_url"), ("technical", "engineered_technical_record"),
])
def test_modality_routing(kind, modality):
    assert detect_modality({"kind": kind}) == modality


def test_empty_and_quoted_only_content_is_unavailable():
    assert not preprocess({"kind": "email"}).required_content_available
    assert not preprocess(email("> Please share your password.")).required_content_available


def test_web_text_and_title_preserved():
    result = preprocess(dict(kind="webpage", title=" Title ", visible_text="  A PAGE  "))
    assert result.model_text == "title a page"
    assert result.segments[1].text == "  A PAGE  "
    assert not result.conditional_evidence_available


def test_invalid_html_parser_token_and_oversized_input():
    with pytest.raises(ArtifactParserError):
        preprocess({"kind": "webpage", "html": "<![bogus]>"})
    with pytest.raises(ArtifactValidationError):
        preprocess({"kind": "email", "subject": "x" * (MAX_FIELD_CHARS + 1)})
    with pytest.raises(ArtifactParserError):
        preprocess({"kind": "webpage", "html": "<div>" * 130})
    with pytest.raises(ArtifactValidationError):
        preprocess({"kind": "webpage", "html": '<a href="https://[bad">Click</a>',
                    "link_extraction_authorized": True})


@pytest.mark.parametrize("html", [
    "<![bogus]>", "<![BOGUS]>", "<![CDATA[text]]>", "<![if IE]>",
    "<!ENTITY secret 'value'>", "<!entity secret 'value'>", "<!>",
    "<!DOCTYPE svg>", "<!DOCTYPEhtml>", "<! DOCTYPE html>",
    '<!DOCTYPE html SYSTEM "legacy.dtd">',
    '<!DOCTYPE html PUBLIC "legacy" "legacy.dtd">',
    '<!DOCTYPE html SYSTEM "about:legacy-compat">',
    "<!DOCTYPE html [<!ENTITY secret 'value'>]>",
    "<!DOCTYPE html []>", "<!DOCTYPE html", "<![bogus", "<!", "<!--secret",
    "<?secret?>", "<?secret",
])
def test_strict_declarations_reject_safely(html):
    with pytest.raises(ArtifactParserError) as caught:
        preprocess(dict(kind="webpage", html=html))
    assert type(caught.value) is ArtifactParserError
    assert str(caught.value) == "Static HTML parsing failed"
    assert html not in str(caught.value)


@pytest.mark.parametrize("doctype", [
    "<!DOCTYPE html>", "<!doctype HTML>", "<!DoCtYpE hTmL>",
    "<!DOCTYPE\t\nhtml >", "<!DOCTYPE\r\fhtml\t>",
])
def test_supported_doctype_preserves_page_evidence_and_links(doctype):
    html = (doctype + '\n<!-- <![bogus]> -->'
            '<div title="<![bogus]>"><p>A &amp; B &#33;</p>'
            '<script>const s = "<![bogus]>";</script>'
            '<a href="/help">Help</a></div>')
    raw = dict(kind="webpage", html=html, page_url="https://example.test/page")
    result = preprocess(raw)
    assert result.model_text == "a & b ! help"
    assert result.urls == ("https://example.test/page",)
    for segment in result.segments:
        assert html[segment.start:segment.end] == segment.text
    authorized = preprocess(dict(raw, link_extraction_authorized=True))
    assert authorized.urls == ("https://example.test/help", "https://example.test/page")
    link = authorized.link_evidence[0]
    assert html[link.start:link.end] == '<a href="/help">'


def test_declaration_like_literal_text_is_ordinary_content():
    result = preprocess(dict(kind="webpage", html='<p>&lt;!DOCTYPE html&gt; 2 < 3</p>'))
    assert result.model_text == "<!doctype html> 2 < 3"


def test_dom_node_limit_still_applies():
    from ml.preprocessing import MAX_DOM_NODES
    with pytest.raises(ArtifactParserError):
        preprocess(dict(kind="webpage", html="<br>" * (MAX_DOM_NODES + 1)))
