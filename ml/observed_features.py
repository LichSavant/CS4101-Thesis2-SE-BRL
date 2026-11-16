"""Ordered available-field E1 mechanics shared by research and artifact intake.

This is a candidate dictionary, not a research freeze. Unknown opportunities stay
None. No source IDs, targets, collection flags, language or annotations predict.
Raw evidence stays in PreparedArtifact; values never stand in for evidence.
"""
from dataclasses import dataclass
from email.utils import parseaddr
from types import MappingProxyType

from ml.features import url_features
from ml.preprocessing import PreparedArtifact, PREPROCESSING_VERSION
from ml.se_brl.detectors import DOMAIN, DetectorContext, _identity_fields, _locate

VERSION = "observed-conventional-candidate-0.1.0"
COMMON = ("model_text", "conventional:text_char_count", "conventional:text_word_count",
          "conventional:quoted_segment_count", "conventional:observed_brand_domain_mismatch")
EMAIL = ("conventional:sender_reply_domain_differ", "conventional:header_count",
         "conventional:message_id_present", "conventional:in_reply_to_present", "conventional:references_present")
WEB = ("conventional:html_element_count", "conventional:form_count", "conventional:input_count",
       "conventional:link_element_count", "conventional:password_input_count", "conventional:resource_element_count")
URL_NAMES = tuple(url_features(()))


def conventional_dictionary(modality):
    if modality not in {"content_bearing_email", "content_bearing_webpage"}:
        raise ValueError("Content E1 cannot replace a frozen technical U1 dictionary")
    names = COMMON + (EMAIL if modality == "content_bearing_email" else WEB)
    names += tuple("conventional:embedded_"+n for n in URL_NAMES)
    if modality == "content_bearing_webpage":
        names += tuple("conventional:page_"+n for n in URL_NAMES if n != "url_count")
    return tuple((name, "text" if name == "model_text" else "numeric") for name in names)


@dataclass(frozen=True, slots=True)
class ObservedConventionalRecord:
    modality: str
    values: object
    unavailable: tuple[str, ...]
    version: str = VERSION

    def __post_init__(self):
        dictionary = conventional_dictionary(self.modality)
        if tuple(self.values) != tuple(n for n, _ in dictionary):
            raise ValueError("Exact ordered conventional dictionary required")
        if tuple(n for n, value in self.values.items() if value is None) != self.unavailable:
            raise ValueError("Explicit conventional unavailability required")
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))


def _domain(address):
    if not address:
        return None
    parsed = parseaddr(address)[1]
    domain = parsed.rpartition("@")[2].lower()
    return domain if parsed.count("@") == 1 and DOMAIN.fullmatch(domain) else None


def observed_conventional(artifact, *, identity_context=None):
    """Compute observed lexical/structure/relation/URL features, never learn.

    Header count is the count of provided allowlisted headers, not all transport
    headers. Missing specific headers remain unknown. Embedded links require
    authorized extraction plus HTML/body or an explicit supplied URL collection.
    A page's own URL is a separate technical surface. An observed brand/domain
    comparison uses linked, independently audited references; it is not a
    behavioral detector or a per-record brand annotation.
    """
    if not isinstance(artifact, PreparedArtifact) or artifact.preprocessing_version != PREPROCESSING_VERSION:
        raise ValueError("Compatible prepared artifact required")
    context = identity_context if identity_context is not None else DetectorContext()
    if not isinstance(context, DetectorContext):
        raise ValueError("Typed independent reference context required")
    values = dict.fromkeys(name for name, _ in conventional_dictionary(artifact.modality_id))
    observed_text = any(name in artifact.supplied_fields for name in ("subject", "body", "title", "visible_text", "html"))
    if observed_text:
        values.update(model_text=artifact.model_text)
        values["conventional:text_char_count"] = len(artifact.model_text)
        values["conventional:text_word_count"] = len(artifact.model_text.split())
        values["conventional:quoted_segment_count"] = sum(s.quoted for s in artifact.segments)
    references = tuple(r for r in context.identities if r.indicator_id == "brand_exploitation")
    fields = _identity_fields(artifact)
    for reference in references:
        _locate(artifact, reference.claim)  # validates exact original-field ownership
    if references and fields and all(r.delegation_audited for r in references):
        values["conventional:observed_brand_domain_mismatch"] = int(any(
            domain not in reference.authorized_domains for reference in references for domain, _ in fields))
    if artifact.modality_id == "content_bearing_email":
        sender, reply = _domain(artifact.sender), _domain(artifact.reply_to)
        if sender is not None and reply is not None:
            values["conventional:sender_reply_domain_differ"] = int(sender != reply)
        if "headers" in artifact.supplied_fields:
            values["conventional:header_count"] = len(artifact.headers)
        headers = dict(artifact.headers)
        for header, column in (("message-id", "message_id_present"), ("in-reply-to", "in_reply_to_present"), ("references", "references_present")):
            if header in headers:
                values["conventional:"+column] = int(bool(headers[header].strip()))
    elif "html" in artifact.supplied_fields:
        structures = artifact.structures
        values["conventional:html_element_count"] = len(structures)
        for tag, column in (("form", "form_count"), ("input", "input_count"), ("a", "link_element_count")):
            values["conventional:"+column] = sum(s.tag == tag for s in structures)
        values["conventional:password_input_count"] = sum(s.tag == "input" and dict(s.attributes).get("type", "").casefold() == "password" for s in structures)
        values["conventional:resource_element_count"] = sum(s.tag in {"img", "script", "link", "iframe", "source"} for s in structures)
    known_links = artifact.link_extraction_authorized and (
        "urls" in artifact.supplied_fields or "html" in artifact.supplied_fields or "body" in artifact.supplied_fields)
    if known_links:
        embedded = tuple(dict.fromkeys(link.url for link in artifact.link_evidence if link.field not in {"page_url", "url"}))
        values.update({"conventional:embedded_"+name: value for name, value in url_features(embedded).items()})
    if artifact.modality_id == "content_bearing_webpage":
        own_urls = tuple(dict.fromkeys(link.url for link in artifact.link_evidence if link.field == "page_url"))
        if own_urls:
            values.update({"conventional:page_"+name: value for name, value in url_features(own_urls).items() if name != "url_count"})
    return ObservedConventionalRecord(artifact.modality_id, values, tuple(n for n, v in values.items() if v is None))
