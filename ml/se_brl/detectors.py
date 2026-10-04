"""Evidence-aware trust detector ports; independent references are never inferred.

Caller-supplied references must come from a documented independent audit. These
types validate their structure and linkage, not the truth of that audit.
"""

from dataclasses import dataclass
from email.utils import parseaddr
import re
from typing import Literal, Protocol
from urllib.parse import urlsplit

from ml.preprocessing import PreparedArtifact, TextEvidence
from .context import ContextIndex

ROLE = re.compile(r"\b(?:as your|I am your|by order of (?:your|the))\s+(?:administrator|manager|CEO|security team|director)\b", re.I)
SENTENCE_END = re.compile(r"[.!?\n]")
MAX_REFERENCE_ITEMS = 64
DIRECTIVE = re.compile(r"\b(?:please\s+)?(?:submit|send|share|provide|enter|transfer|pay|click|download|reply|verify)\b[^.!?\n]{0,100}", re.I)
DOMAIN = re.compile(r"(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")


def _nonempty(value: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError("Independent evidence requires nonempty reference metadata")


@dataclass(frozen=True, slots=True)
class IdentityReference:
    indicator_id: Literal["impersonation", "brand_exploitation"]
    entity: str
    claim: TextEvidence
    authorized_domains: tuple[str, ...]
    reference_id: str
    delegation_audited: bool = False

    def __post_init__(self) -> None:
        if self.indicator_id not in {"impersonation", "brand_exploitation"}:
            raise ValueError("Invalid identity indicator")
        _nonempty(self.entity)
        _nonempty(self.reference_id)
        if (type(self.authorized_domains) is not tuple or not self.authorized_domains
                or any(type(d) is not str or not DOMAIN.fullmatch(d) for d in self.authorized_domains)
                or len(set(self.authorized_domains)) != len(self.authorized_domains)
                or type(self.delegation_audited) is not bool or not isinstance(self.claim, TextEvidence)):
            raise ValueError("Invalid identity reference domains or claim")


@dataclass(frozen=True, slots=True)
class AuthorityReview:
    role: TextEvidence
    directive: TextEvidence
    authorization: Literal["authorized", "contradicted", "unknown"]
    reference_id: str

    def __post_init__(self) -> None:
        _nonempty(self.reference_id)
        if (self.authorization not in {"authorized", "contradicted", "unknown"}
                or not isinstance(self.role, TextEvidence) or not isinstance(self.directive, TextEvidence)):
            raise ValueError("Invalid authority review")


@dataclass(frozen=True, slots=True)
class DetectorContext:
    identities: tuple[IdentityReference, ...] = ()
    authority_reviews: tuple[AuthorityReview, ...] = ()

    def __post_init__(self) -> None:
        for entries, expected in ((self.identities, IdentityReference), (self.authority_reviews, AuthorityReview)):
            if type(entries) is not tuple or len(entries) > MAX_REFERENCE_ITEMS or any(not isinstance(i, expected) for i in entries):
                raise ValueError("Detector references must be immutable typed tuples")
        keys = [(r.role, r.directive) for r in self.authority_reviews]
        identity_keys = [(r.indicator_id, r.claim) for r in self.identities]
        if len(set(keys)) != len(keys) or len(set(identity_keys)) != len(identity_keys):
            raise ValueError("Duplicate or contradictory evidence reviews")


@dataclass(frozen=True, slots=True)
class DetectorObservation:
    spans: tuple[TextEvidence, ...]
    detector_id: str
    reference_id: str | None = None


@dataclass(frozen=True, slots=True)
class DetectorReport:
    indicator_id: str
    evaluated: bool
    qualifying: tuple[DetectorObservation, ...] = ()
    observations: tuple[DetectorObservation, ...] = ()
    reason: str = "independent_evidence_missing"


class EvidenceAwareDetector(Protocol):
    def detect(self, artifact: PreparedArtifact, context: DetectorContext,
               guards: ContextIndex) -> tuple[DetectorReport, ...]: ...


def _locate(artifact: PreparedArtifact, span: TextEvidence) -> tuple[TextEvidence, int, int]:
    for segment in artifact.segments:
        if (segment.field == span.field and segment.location == span.location
                and segment.start <= span.start < span.end <= segment.end
                and span.quoted == segment.quoted
                and segment.text[span.start - segment.start:span.end - segment.start] == span.text):
            return segment, span.start - segment.start, span.end - segment.start
    raise ValueError("Independent evidence span does not belong to this artifact")


def _span(segment: TextEvidence, match: re.Match) -> TextEvidence:
    return TextEvidence(segment.field, segment.start + match.start(), segment.start + match.end(),
                        match.group(), segment.location, segment.quoted)


def _identity_fields(artifact: PreparedArtifact) -> tuple[tuple[str, TextEvidence], ...]:
    fields = []
    for field, value in (("sender", artifact.sender), ("reply_to", artifact.reply_to)):
        if value:
            address = parseaddr(value)[1]
            domain = address.rpartition("@")[2].lower()
            if address.count("@") == 1 and DOMAIN.fullmatch(domain):
                fields.append((domain, TextEvidence(field, 0, len(value), value, field)))
    for link in artifact.link_evidence:
        if link.field == "page_url":
            domain = urlsplit(link.url).hostname or ""
            if DOMAIN.fullmatch(domain):
                fields.append((domain, TextEvidence("page_url", link.start, link.end, link.original_text, link.location)))
    return tuple(fields)


class ConservativeTrustDetector:
    def detect(self, artifact: PreparedArtifact, context: DetectorContext,
               guards: ContextIndex) -> tuple[DetectorReport, ...]:
        if artifact.modality_id not in {"content_bearing_email", "content_bearing_webpage"}:
            return tuple(DetectorReport(i, False, reason="modality_unavailable")
                         for i in ("authority", "impersonation", "brand_exploitation"))
        # Validate supplied locators even when no corresponding pattern fires.
        for reference in context.identities:
            _locate(artifact, reference.claim)
        for review in context.authority_reviews:
            _locate(artifact, review.role)
            _locate(artifact, review.directive)
        fields = _identity_fields(artifact)
        reports = []
        for indicator in ("impersonation", "brand_exploitation"):
            hits = []
            evaluated_count = 0
            relevant = tuple(r for r in context.identities if r.indicator_id == indicator)
            for reference in context.identities:
                if reference.indicator_id != indicator or not reference.delegation_audited or not fields:
                    continue
                segment, start, end = _locate(artifact, reference.claim)
                explicit = re.fullmatch(r"(?:we are|this is|official notice from|on behalf of)\s+" + re.escape(reference.entity), reference.claim.text, re.I)
                if not explicit or guards.suppressed(segment, start, end):
                    continue
                evaluated_count += 1
                # Exact host membership: suffix similarity is not identity proof.
                conflicts = tuple(span for domain, span in fields if domain not in reference.authorized_domains)
                if conflicts:
                    hits.append(DetectorObservation((reference.claim,) + tuple(span for _, span in fields),
                                                    "identity.audited_domain_conflict", reference.reference_id))
            evaluated = bool(hits) or bool(relevant and evaluated_count == len(relevant))
            reports.append(DetectorReport(indicator, evaluated, tuple(hits), reason="audited_domain_comparison" if evaluated else "independent_evidence_missing"))
        observations = []
        hits = []
        reviewed_count = 0
        reviews = {(r.role, r.directive): r for r in context.authority_reviews}
        for segment in guards.positions:
            for role_match in ROLE.finditer(segment.text):
                # Only the following directive in the same sentence is a candidate.
                tail = segment.text[role_match.end():]
                tail = SENTENCE_END.split(tail[:160], maxsplit=1)[0]
                directive_match = DIRECTIVE.search(tail)
                if not directive_match:
                    continue
                role = _span(segment, role_match)
                start = role_match.end() + directive_match.start()
                end = role_match.end() + directive_match.end()
                directive = TextEvidence(segment.field, segment.start + start, segment.start + end,
                                         segment.text[start:end], segment.location)
                if guards.suppressed(segment, role_match.start(), end):
                    continue
                review = reviews.get((role, directive))
                observation = DetectorObservation((role, directive), "authority.role_with_directive",
                                                  review.reference_id if review else None)
                observations.append(observation)
                if review and review.authorization != "unknown":
                    reviewed_count += 1
                    if review.authorization == "contradicted":
                        hits.append(observation)
        # Partial reviews cannot silently mark all remaining candidates absent.
        evaluated = bool(hits) or bool(observations and reviewed_count == len(observations))
        reports.insert(0, DetectorReport("authority", evaluated, tuple(hits), tuple(observations),
                                        "authorization_review" if evaluated else "authority_legitimacy_unresolved"))
        return tuple(reports)
