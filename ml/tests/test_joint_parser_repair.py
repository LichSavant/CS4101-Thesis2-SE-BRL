"""Repaired actual peer parser plus strict joint boundary; synthetic HTML only."""
from copy import deepcopy
import json
import os
from pathlib import Path
import pytest
from ml.counterpart_checkout import COUNTERPART_COMMIT, load_counterpart, verify_source_manifest
from ml.se_brl.joint_integration import joint_preprocess

MANIFEST = Path(__file__).resolve().parents[2] / "docs/r22-parser-repair-2026-11-16/counterpart-source-manifest.json"

@pytest.fixture(scope="module")
def peer():
    root = os.environ.get("SEBRL_R22_COUNTERPART_ROOT")
    if not root: pytest.fail("Actual pinned checkout required")
    return load_counterpart(Path(root), MANIFEST)

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
def test_repaired_peer_and_joint_boundary_reject_declarations_without_leakage(peer, html):
    raw = dict(kind="webpage", html=html)
    with pytest.raises(peer.preprocessing.ArtifactParserError) as error:
        peer.preprocessing.preprocess(raw)
    assert type(error.value) is peer.preprocessing.ArtifactParserError
    assert str(error.value) == "Static HTML parsing failed"
    with pytest.raises(Exception) as joint_error:
        joint_preprocess(raw, peer)
    assert type(joint_error.value).__name__ == "ArtifactParserError"
    assert html not in str(joint_error.value)

@pytest.mark.parametrize("doctype", [
    "<!DOCTYPE html>", "<!doctype HTML>", "<!DoCtYpE hTmL>",
    "<!DOCTYPE\t\nhtml >", "<!DOCTYPE\r\fhtml\t>",
])
@pytest.mark.parametrize("links_authorized", [False, True])
def test_joint_valid_doctype_opaque_content_original_offsets_and_opt_in(peer, doctype, links_authorized):
    html = (doctype + '\n<!-- <![bogus]> -->'
            '<div title="<![bogus]>"><p>🙂 A &amp; B &#33;</p>'
            '<script>const s = "<![bogus]>";</script>'
            '<a href="/help">Help</a></div>')
    local, remote = joint_preprocess(dict(kind="webpage", html=html,
        page_url="https://example.test/page", link_extraction_authorized=links_authorized), peer)
    assert local.model_text == "🙂 a & b ! help"
    assert remote.model_text == "🙂 a & b ! help"
    for segment in remote.segments: assert html[segment.start:segment.end] == segment.text
    for segment in local.segments: assert html[segment.start:segment.end] == segment.text
    sources = {"html": html, "page_url": "https://example.test/page"}
    for view in (local, remote):
        for link in view.link_evidence:
            source_span = sources[link.field][link.start:link.end]
            if link.locator_kind == "enclosing_tag":
                assert link.field == "html" and source_span == '<a href="/help">'
                assert link.original_text == "/help"
            else:
                assert link.locator_kind == "exact_text" and source_span == link.original_text
    assert local.urls == (("https://example.test/help", "https://example.test/page") if links_authorized else ("https://example.test/page",))

def test_joint_escaped_declaration_is_source_content(peer):
    local, _ = joint_preprocess(dict(kind="webpage", html="<p>&lt;!DOCTYPE html&gt; 2 < 3</p>"), peer)
    assert local.model_text == "<!doctype html> 2 < 3"

def test_previous_manifest_cannot_authorize_new_baseline(peer):
    old = json.loads(MANIFEST.read_text())
    old["commit"] = "6a2c0333626d0629e054c09a73d1e2a0111a4f80"
    with pytest.raises(ValueError, match="selected_counterpart_source_manifest_required"):
        verify_source_manifest(peer.root, old)
    assert peer.commit == COUNTERPART_COMMIT == "ae20372db6014d4f83153c03ccc2cd92f445ca8c"

def test_same_commit_string_does_not_substitute_for_actual_source_hashes(peer):
    forged = deepcopy(peer.manifest)
    forged["source_files"]["ml/preprocessing.py"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="counterpart_source_hash_mismatch"):
        verify_source_manifest(peer.root, forged)
