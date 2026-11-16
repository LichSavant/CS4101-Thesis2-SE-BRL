"""Deterministic BRL features; deprecated z placeholders remain read-only legacy data."""

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
        """Historical layout only; never used by the deterministic feature builder."""
        return self.z_values + self.extraction.assessment.availability_mask

    @property
    def deterministic_names(self) -> tuple[str, ...]:
        order = load_codebook()["vector_ordering"]["dimension_order"]
        return tuple(f"{d}_supported" for d in order) + tuple(f"{d}_available" for d in order)

    @property
    def deterministic_slots(self) -> tuple[int | None, ...]:
        """Four support values then four availability values, proposal Table 4.13.

        An unevaluated indicator is not assessed absence. Until the partial-
        evaluation policy is accepted, an affected dimension has None/None and
        cannot enter a numeric model. Wholly unavailable dimensions retain 0/0.
        This changes no detector, language rule or availability resolver.
        """
        support, availability = [], []
        for dimension in self.extraction.assessment.dimension_results:
            indicators = [i for i in self.extraction.indicators if i.dimension_id == dimension.dimension_id]
            if dimension.evidence_state == "unavailable":
                support.append(0); availability.append(0)
            elif any(i.evaluation_status != "rule_evaluated" for i in indicators):
                support.append(None); availability.append(None)
            else:
                support.append(int(dimension.evidence_state == "supported")); availability.append(1)
        return tuple(support + availability)

    @property
    def unevaluated_indicators(self) -> tuple[str, ...]:
        return tuple(i.indicator_id for i in self.extraction.indicators if i.evaluation_status == "not_evaluated")
