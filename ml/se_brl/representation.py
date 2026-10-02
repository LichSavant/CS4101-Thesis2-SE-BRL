"""Pre-training BRL representation: rule evidence is never a learned z value."""

from dataclasses import dataclass
from typing import Literal

from .codebook import load_codebook
from .extraction import ExtractionResult
from .result_envelope import not_evaluated_result


@dataclass(frozen=True, slots=True)
class BrlRepresentation:
    extraction: ExtractionResult
    z_values: tuple[None, None, None, None] = (None, None, None, None)
    z_status: Literal["not_evaluated"] = "not_evaluated"

    def __post_init__(self) -> None:
        if self.z_values != (None,) * 4 or self.z_status != "not_evaluated":
            raise ValueError("Learned behavioral values are not available")
        not_evaluated_result(self.extraction.assessment.modality_id, self.extraction.assessment)
        codebook = load_codebook()
        expected = tuple((i["id"], d["id"]) for d in codebook["dimensions"] for i in d["indicators"])
        actual = tuple((i.indicator_id, i.dimension_id) for i in self.extraction.indicators)
        if actual != expected:
            raise ValueError("Indicators must retain canonical IDs, parents, and ordering")
        available = dict(zip(codebook["vector_ordering"]["dimension_order"],
                             self.extraction.assessment.availability_mask, strict=True))
        for indicator in self.extraction.indicators:
            if not available[indicator.dimension_id]:
                valid = indicator.evidence_state == "unavailable" and indicator.evaluation_status == "unavailable" and not indicator.evidence
            elif indicator.evaluation_status == "not_evaluated":
                valid = indicator.evidence_state is None and not indicator.evidence
            else:
                valid = (indicator.evaluation_status == "rule_evaluated"
                         and indicator.evidence_state == ("supported" if indicator.evidence else "absent"))
            if not valid:
                raise ValueError("Indicator state contradicts availability or detector status")
            for evidence in indicator.evidence:
                if any(span.quoted or span.start < 0 or span.end - span.start != len(span.text)
                       for span in evidence.supporting_spans):
                    raise ValueError("Invalid supporting evidence span")
                if (evidence.indicator_id != indicator.indicator_id
                        or evidence.modality_id != self.extraction.assessment.modality_id
                        or evidence.ruleset_version != self.extraction.ruleset_version
                        or evidence.evidence_state != "supported" or evidence.provenance != "rule-based"
                        or evidence.span.quoted or evidence.span.start < 0
                        or evidence.span.end - evidence.span.start != len(evidence.span.text)):
                    raise ValueError("Invalid indicator evidence provenance or span")
        for dimension in self.extraction.assessment.dimension_results:
            observed = any(i.evidence for i in self.extraction.indicators if i.dimension_id == dimension.dimension_id)
            if (dimension.evidence_state == "supported") != observed:
                raise ValueError("Dimension observations contradict indicator evidence")

    @property
    def slots(self) -> tuple[None | int, ...]:
        return self.z_values + self.extraction.assessment.availability_mask

    @property
    def unevaluated_indicators(self) -> tuple[str, ...]:
        return tuple(i.indicator_id for i in self.extraction.indicators if i.evaluation_status == "not_evaluated")
