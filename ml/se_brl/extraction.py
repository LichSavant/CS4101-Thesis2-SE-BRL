"""Evidence-linked rule execution with conservative contextual suppression."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from ml.preprocessing import PreparedArtifact, TextEvidence
from .assessment import AssessmentInput, AssessmentResult, assess
from .codebook import load_codebook
from .rules import RULES, RULESET_VERSION, Rule
from .context import ContextIndex
from .detectors import ConservativeTrustDetector, DetectorContext, DetectorReport, EvidenceAwareDetector


@dataclass(frozen=True, slots=True)
class IndicatorEvidence:
    indicator_id: str
    evidence_state: Literal["supported"]
    span: TextEvidence
    rule_id: str
    ruleset_version: str
    modality_id: str
    provenance: Literal["rule-based"] = "rule-based"
    supporting_spans: tuple[TextEvidence, ...] = ()
    reference_id: str | None = None


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
    detector_reports: tuple[DetectorReport, ...] = ()


class RuleEngine:
    def __init__(self, rules: tuple[Rule, ...] = RULES, version: str = RULESET_VERSION,
                 trust_detector: EvidenceAwareDetector | None = None) -> None:
        codebook = load_codebook()
        canonical = {i["id"] for d in codebook["dimensions"] for i in d["indicators"]}
        if (type(rules) is not tuple or any(not isinstance(rule, Rule) for rule in rules)
                or len({rule.rule_id for rule in rules}) != len(rules)
                or any(rule.indicator_id not in canonical or not rule.rule_id for rule in rules)
                or not isinstance(version, str) or not version.strip()):
            raise ValueError("Invalid rule registry")
        self.rules = rules
        self.version = version
        self.codebook = codebook
        self.trust_detector = trust_detector if trust_detector is not None else ConservativeTrustDetector()
        self.compiled = tuple((rule, re.compile(rule.pattern, re.I)) for rule in rules)

    def extract(self, artifact: PreparedArtifact, detector_context: DetectorContext | None = None) -> ExtractionResult:
        if not isinstance(artifact, PreparedArtifact):
            raise TypeError("Expected a preprocessed artifact")
        codebook = self.codebook
        order = codebook["vector_ordering"]["dimension_order"]
        base = assess(AssessmentInput(artifact.modality_id, artifact.required_content_available,
                                     artifact.conditional_evidence_available, {d: False for d in order}))
        available = {d.dimension_id: bool(a) for d, a in zip(base.dimension_results, base.availability_mask)}
        parents = {i["id"]: d["id"] for d in codebook["dimensions"] for i in d["indicators"]}
        evidence: dict[str, list[IndicatorEvidence]] = {i: [] for i in parents}
        seen = set()
        context = ContextIndex(artifact)
        for segment in context.positions:
            if not segment.text.strip():
                continue
            for rule, pattern in self.compiled:
                if not available[parents[rule.indicator_id]]:
                    continue
                for match in pattern.finditer(segment.text):
                    if context.suppressed(segment, match.start(), match.end(),
                                          allow_negative_instruction=rule.allow_negative_instruction):
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
        detector_context = detector_context if detector_context is not None else DetectorContext()
        if not isinstance(detector_context, DetectorContext):
            raise TypeError("Expected typed independent detector context")
        trust_indicators = ("authority", "impersonation", "brand_exploitation")
        reports = (self.trust_detector.detect(artifact, detector_context, context)
                   if available[parents["authority"]] else
                   tuple(DetectorReport(i, False, reason="modality_or_evidence_unavailable") for i in trust_indicators))
        expected = set(trust_indicators)
        if len(reports) != 3 or {r.indicator_id for r in reports} != expected:
            raise ValueError("Trust detector must report the three canonical indicators")
        for report in reports:
            if not available[parents[report.indicator_id]]:
                continue
            if report.qualifying and not report.evaluated:
                raise ValueError("Unevaluated detector cannot supply qualifying evidence")
            if report.evaluated:
                implemented.add(report.indicator_id)
            for finding in dict.fromkeys(report.qualifying):
                if not finding.spans:
                    raise ValueError("Detector findings require evidence")
                evidence[report.indicator_id].append(IndicatorEvidence(
                    report.indicator_id, "supported", finding.spans[0], finding.detector_id,
                    self.version, artifact.modality_id, supporting_spans=finding.spans[1:],
                    reference_id=finding.reference_id,
                ))
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
        return ExtractionResult(tuple(results), assessment, self.version, reports)
