"""Offline, bounded artifact preprocessing. No network, persistence, or DOM execution.

Offsets are half-open Python character offsets in the named original field.
Normalized text is a separate view and must never be used as evidence offsets.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

MAX_FIELD_CHARS = 200_000
MAX_URLS = 500
MAX_DOM_DEPTH = 128
MAX_DOM_NODES = 20_000
PREPROCESSING_VERSION = "0.1.0"
SAFE_HEADERS = frozenset({"date", "message-id", "in-reply-to", "references", "content-type"})
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.I)
MODALITIES = {
    "email": "content_bearing_email",
    "webpage": "content_bearing_webpage",
    "url": "standalone_url",
    "technical": "engineered_technical_record",
}


class ArtifactValidationError(ValueError):
    """Input cannot safely be preprocessed; messages never include input values."""


class ArtifactParserError(ValueError):
    """HTML cannot safely be represented by the conservative static parser."""


@dataclass(frozen=True, slots=True)
class TextEvidence:
    field: str
    start: int
    end: int
    text: str
    location: str
    quoted: bool = False


@dataclass(frozen=True, slots=True)
class StructureEvidence:
    tag: str
    location: str
    start: int
    end: int
    attributes: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class LinkEvidence:
    url: str
    original_text: str
    field: str
    location: str
    start: int
    end: int
    locator_kind: str  # exact_text or enclosing_tag (attribute offsets are not guessed)


@dataclass(frozen=True, slots=True)
class PreparedArtifact:
    modality_id: str
    segments: tuple[TextEvidence, ...]
    model_text: str
    urls: tuple[str, ...]
    sender: str | None
    reply_to: str | None
    headers: tuple[tuple[str, str], ...]
    structures: tuple[StructureEvidence, ...]
    supplied_fields: tuple[str, ...]
    required_content_available: bool
    conditional_evidence_available: bool
    link_extraction_authorized: bool = False
    link_evidence: tuple[LinkEvidence, ...] = ()
    preprocessing_version: str = PREPROCESSING_VERSION


def normalize_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", unescape(text)).casefold().split())


def _text(value: object) -> str:
    if type(value) is not str or len(value) > MAX_FIELD_CHARS or "\x00" in value:
        raise ArtifactValidationError("Invalid or oversized text field")
    return value


def _url(value: object) -> str:
    value = _text(value)
    try:
        parsed = urlsplit(value)
        if (not parsed.hostname or parsed.scheme.lower() not in {"http", "https"}
                or parsed.username is not None or parsed.password is not None
                or any(c.isspace() or ord(c) < 32 for c in value)):
            raise ValueError
        parsed.port
    except ValueError:
        raise ArtifactValidationError("Expected an HTTP(S) URL without credentials") from None
    return value


def detect_modality(raw: Mapping[str, object]) -> str:
    """Route explicit source kind; never guess psychological cues from a URL."""
    if not isinstance(raw, Mapping) or type(raw.get("kind")) is not str:
        raise ArtifactValidationError("Artifact requires a source kind")
    kind = raw["kind"]
    if kind not in MODALITIES:
        raise ArtifactValidationError("Unsupported artifact kind")
    return MODALITIES[kind]


def _email_segments(field: str, text: str) -> list[TextEvidence]:
    segments = []
    offset = 0
    reply_tail = False
    for line in text.splitlines(keepends=True):
        if field == "body" and re.match(
            r"\s*(?:On .+ wrote:|-+\s*(?:Original|Forwarded) [Mm]essage\s*-+)", line
        ):
            reply_tail = True
        quoted = field == "body" and (reply_tail or line.lstrip().startswith(">"))
        segments.append(TextEvidence(field, offset, offset + len(line), line, field, quoted))
        offset += len(line)
    return segments


class _PageParser(HTMLParser):
    """Static visibility approximation; CSS layout and JavaScript are not evaluated."""

    VOID = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"})
    HIDDEN = frozenset({"script", "style", "template", "noscript", "textarea"})

    def __init__(self, html: str, collect_links: bool) -> None:
        super().__init__(convert_charrefs=False)
        self.html = html
        self.collect_links = collect_links
        self.line_starts = [0] + [m.end() for m in re.finditer("\n", html)]
        self.stack: list[tuple[str, str, bool, bool]] = []
        self.segments: list[TextEvidence] = []
        self.structures: list[StructureEvidence] = []
        self.links: list[tuple[str, str, int, int]] = []
        self.node_count = 0

    def source_offset(self) -> int:
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.node_count += 1
        if self.node_count > MAX_DOM_NODES or len(self.stack) >= MAX_DOM_DEPTH:
            raise ArtifactParserError("HTML structure exceeds parser limits")
        attributes = dict(attrs)
        style = re.sub(r"\s+", "", attributes.get("style") or "").lower()
        hidden = (any(node[2] for node in self.stack) or tag in self.HIDDEN
                  or "hidden" in attributes or attributes.get("aria-hidden") == "true"
                  or "display:none" in style or "visibility:hidden" in style
                  or (tag == "input" and (attributes.get("type") or "").lower() == "hidden"))
        quoted = any(node[3] for node in self.stack) or tag == "blockquote"
        location = "/".join([node[1] for node in self.stack] + [f"{tag}[{self.node_count}]"])
        if not hidden:
            # Retain structural types only, never values, event handlers, cookies,
            # arbitrary data attributes, or raw HTML start tags.
            safe = tuple((key, value) for key, value in attrs
                         if key in {"type", "method"} and value is not None)
            start = self.source_offset()
            self.structures.append(StructureEvidence(
                tag, location, start, start + len(self.get_starttag_text()), safe
            ))
            if self.collect_links:
                for key in ("href", "action", "src"):
                    value = attributes.get(key)
                    # Relative links retained as locations; resolution needs page URL.
                    if value:
                        self.links.append((value, location + "/@" + key, start,
                                           start + len(self.get_starttag_text())))
        if tag not in self.VOID:
            self.stack.append((tag, location.split("/")[-1], hidden, quoted))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if any(node[2] for node in self.stack) or not data:
            return
        start = self.source_offset()
        location = "/".join(node[1] for node in self.stack) or "document"
        item = TextEvidence("html", start, start + len(data), data, location,
                            any(node[3] for node in self.stack))
        # Join adjacent entity/data callbacks without losing exact source spelling.
        if self.segments and self.segments[-1].end == start and self.segments[-1].location == location:
            previous = self.segments.pop()
            item = TextEvidence("html", previous.start, item.end, previous.text + data,
                                location, item.quoted)
        self.segments.append(item)

    def handle_entityref(self, name: str) -> None:
        start = self.source_offset()
        length = len(name) + 1
        if self.html[start + length:start + length + 1] == ";":
            length += 1
        self.handle_data(self.html[start:start + length])

    def handle_charref(self, name: str) -> None:
        self.handle_entityref("#" + name)


def preprocess(raw: Mapping[str, object]) -> PreparedArtifact:
    modality = detect_modality(raw)
    kind = raw["kind"]
    fields = {
        "email": {"subject", "body", "sender", "reply_to", "headers", "body_collection_authorized", "study_purpose"},
        "webpage": {"html", "visible_text", "title", "page_url"},
        "url": {"url"},
        "technical": set(),
    }[kind] | {"kind", "urls", "link_extraction_authorized"}
    if set(raw) - fields:
        raise ArtifactValidationError("Unknown or inapplicable artifact fields")
    for flag in ("body_collection_authorized", "link_extraction_authorized"):
        if flag in raw and type(raw[flag]) is not bool:
            raise ArtifactValidationError("Authorization must be a Boolean")
    links_authorized = raw.get("link_extraction_authorized", False) is True
    urls = raw.get("urls", ())
    if not isinstance(urls, (list, tuple)) or len(urls) > MAX_URLS:
        raise ArtifactValidationError("Invalid URL collection")
    if urls and not links_authorized:
        raise ArtifactValidationError("Link extraction requires explicit authorization")
    collected = [_url(url) for url in urls]
    link_evidence = [LinkEvidence(url, url, f"urls[{index}]", f"urls[{index}]", 0, len(url), "exact_text")
                     for index, url in enumerate(collected)]
    segments: list[TextEvidence] = []
    structures: tuple[StructureEvidence, ...] = ()
    headers: tuple[tuple[str, str], ...] = ()
    sender = reply_to = None
    if kind == "email":
        if "body" in raw and (raw.get("body_collection_authorized") is not True
                              or not _text(raw.get("study_purpose", "")).strip()):
            raise ArtifactValidationError("Body requires explicit authorization and study purpose")
        for field in ("subject", "body"):
            if field in raw:
                segments.extend(_email_segments(field, _text(raw[field])))
        sender = _text(raw["sender"]) if "sender" in raw else None
        reply_to = _text(raw["reply_to"]) if "reply_to" in raw else None
        supplied_headers = raw.get("headers", {})
        if (not isinstance(supplied_headers, Mapping)
                or any(type(k) is not str or k.lower() not in SAFE_HEADERS for k in supplied_headers)):
            raise ArtifactValidationError("Only allowlisted email headers are accepted")
        headers = tuple(sorted((key.lower(), _text(value)) for key, value in supplied_headers.items()))
    elif kind == "webpage":
        if "visible_text" in raw and "html" in raw:
            raise ArtifactValidationError("Supply HTML or visible text, not duplicate content views")
        for field in ("title", "visible_text"):
            if field in raw:
                text = _text(raw[field])
                segments.append(TextEvidence(field, 0, len(text), text, field))
        if "html" in raw:
            html = _text(raw["html"])
            parser = _PageParser(html, links_authorized)
            try:
                parser.feed(html)
                parser.close()
            except (AssertionError, ValueError):
                raise ArtifactParserError("Static HTML parsing failed") from None
            if parser.rawdata:
                raise ArtifactParserError("Incomplete HTML token")
            segments.extend(parser.segments)
            structures = tuple(parser.structures)
            if links_authorized:
                base = _url(raw["page_url"]) if "page_url" in raw else ""
                for link, location, start, end in parser.links:
                    try:
                        resolved = urljoin(base, link)
                    except ValueError:
                        raise ArtifactValidationError("Invalid HTML link") from None
                    if resolved.lower().startswith(("https://", "http://")):
                        collected.append(_url(resolved))
                        link_evidence.append(LinkEvidence(resolved, link, "html", location,
                                                          start, end, "enclosing_tag"))
        if "page_url" in raw:
            url = _url(raw["page_url"])
            collected.append(url)
            link_evidence.append(LinkEvidence(url, url, "page_url", "page_url", 0, len(url), "exact_text"))
    elif kind == "url":
        if "url" not in raw:
            raise ArtifactValidationError("Standalone URL requires a URL")
        url = _url(raw["url"])
        collected.append(url)
        link_evidence.append(LinkEvidence(url, url, "url", "url", 0, len(url), "exact_text"))
    if links_authorized:
        for segment in segments:
            for match in URL_PATTERN.finditer(segment.text):
                url = _url(match.group().rstrip(".,;!?)]"))
                collected.append(url)
                start = segment.start + match.start()
                link_evidence.append(LinkEvidence(url, url, segment.field, segment.location,
                                                  start, start + len(url), "exact_text"))
    if len(collected) > MAX_URLS:
        raise ArtifactValidationError("Too many URLs")
    active = [segment for segment in segments if not segment.quoted]
    model_text = normalize_text("\n".join(segment.text for segment in active))
    return PreparedArtifact(
        modality, tuple(segments), model_text, tuple(dict.fromkeys(collected)),
        sender, reply_to, headers, structures, tuple(sorted(raw)), bool(model_text),
        bool(sender and sender.strip()) or bool(structures), links_authorized, tuple(link_evidence),
    )
