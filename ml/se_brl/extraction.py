"""Evidence-linked rule execution with conservative contextual suppression."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from ml.preprocessing import PreparedArtifact, TextEvidence
from .assessment import AssessmentInput, AssessmentResult, assess
from .codebook import load_codebook
from .rules import RULES, RULESET_VERSION, Rule


@dataclass(frozen=True, slots=True)
class IndicatorEvidence:
    indicator_id: str
    evidence_state: Literal["supported"]
    span: TextEvidence
    rule_id: str
    ruleset_version: str
    modality_id: str
    provenance: Literal["rule-based"] = "rule-based"


@dataclass(frozen=True, slots=True)
class IndicatorResult:
    indicator_id: str
    dimension_id: str
    evidence_state: Literal["supported", "absent", "unavailable"] | None
    evaluation_status: Literal["rule_evaluated", "not_evaluated", "unavailable"]
    evidence: tuple[IndicatorEvidence, ...]


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    indicators: tuple[IndicatorResult, ...]
    assessment: AssessmentResult
    ruleset_version: str


NEGATION = re.compile(r"\b(?:not|never|don't|do not|shouldn't|mustn't|cannot|can't|no need to|avoid|without)\b", re.I)
EDUCATIONAL = re.compile(r"\b(?:example|scam|phishing|training|beware|warning|fraud|we (?:will )?never ask)\b", re.I)
QUOTATION = re.compile(r'''"[^"\n]*"|“[^”\n]*”|‘[^’\n]*’|(?<!\w)'[^'\n]*'(?!\w)''')


def _suppressed(context: str, rule: Rule) -> bool:
    # Sentence-wide suppression deliberately favors abstention. This is not a
    # general negation parser, semantic verifier, or multilingual model.
    if EDUCATIONAL.search(context):
        return True
    if not rule.allow_negative_instruction and NEGATION.search(context):
        return True
    if rule.allow_negative_instruction and re.search(r"\b(?:not true|false|ignore|disregard)\b", context, re.I):
        return True
    return False


class RuleEngine:
    def __init__(self, rules: tuple[Rule, ...] = RULES, version: str = RULESET_VERSION) -> None:
        codebook = load_codebook()
        canonical = {i["id"] for d in codebook["dimensions"] for i in d["indicators"]}
        if (type(rules) is not tuple or any(not isinstance(rule, Rule) for rule in rules)
                or len({rule.rule_id for rule in rules}) != len(rules)
                or any(rule.indicator_id not in canonical or not rule.rule_id for rule in rules)
                or not isinstance(version, str) or not version.strip()):
            raise ValueError("Invalid rule registry")
        self.rules = rules
        self.version = version
        self.compiled = tuple((rule, re.compile(rule.pattern, re.I)) for rule in rules)

    def extract(self, artifact: PreparedArtifact) -> ExtractionResult:
        if not isinstance(artifact, PreparedArtifact):
            raise TypeError("Expected a preprocessed artifact")
        codebook = load_codebook()
        order = codebook["vector_ordering"]["dimension_order"]
        base = assess(AssessmentInput(artifact.modality_id, artifact.required_content_available,
                                     artifact.conditional_evidence_available, {d: False for d in order}))
        available = {d.dimension_id: bool(a) for d, a in zip(base.dimension_results, base.availability_mask)}
        parents = {i["id"]: d["id"] for d in codebook["dimensions"] for i in d["indicators"]}
        evidence: dict[str, list[IndicatorEvidence]] = {i: [] for i in parents}
        seen = set()
        # Context spans adjacent inline HTML text nodes, preventing e.g.
        # 'Do not <b>share your password</b>' from losing its negation.
        active = [s for s in artifact.segments if not s.quoted]
        field_text: dict[str, str] = {}
        positions = []
        for segment in active:
            current = field_text.get(segment.field, "")
            positions.append(len(current))
            field_text[segment.field] = current + segment.text + "\n"
        for segment, position in zip(active, positions):
            if not segment.text.strip():
                continue
            full = field_text[segment.field]
            for rule, pattern in self.compiled:
                if not available[parents[rule.indicator_id]]:
                    continue
                for match in pattern.finditer(segment.text):
                    absolute = position + match.start()
                    left = max(full.rfind(mark, 0, absolute) for mark in ".!?") + 1
                    endings = [p for mark in ".!?" if (p := full.find(mark, position + match.end())) >= 0]
                    right = min(endings) if endings else len(full)
                    context = full[left:right]
                    quoted = any(q.start() <= absolute < q.end() for q in QUOTATION.finditer(full))
                    if quoted or _suppressed(context, rule):
                        continue
                    start, end = segment.start + match.start(), segment.start + match.end()
                    key = (rule.rule_id, segment.field, start, end)
                    if key in seen:
                        continue
                    seen.add(key)
                    evidence[rule.indicator_id].append(IndicatorEvidence(
                        rule.indicator_id, "supported",
                        TextEvidence(segment.field, start, end, match.group(), segment.location),
                        rule.rule_id, self.version, artifact.modality_id,
                    ))
        implemented = {rule.indicator_id for rule in self.rules}
        results = []
        for indicator, parent in parents.items():
            hits = tuple(evidence[indicator])
            if not available[parent]:
                state, status = "unavailable", "unavailable"
            elif indicator not in implemented:
                state, status = None, "not_evaluated"
            else:
                state, status = ("supported" if hits else "absent"), "rule_evaluated"
            results.append(IndicatorResult(indicator, parent, state, status, hits))
        assessment = assess(AssessmentInput(
            artifact.modality_id, artifact.required_content_available, artifact.conditional_evidence_available,
            {d: any(evidence[i] for i, parent in parents.items() if parent == d) for d in order},
        ))
        return ExtractionResult(tuple(results), assessment, self.version)
