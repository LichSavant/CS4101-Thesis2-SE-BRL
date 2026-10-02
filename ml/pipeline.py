"""Internal pre-training orchestration. It never fits features or predicts risk.

Evidence stays in this offline result. Only the existing lifecycle envelope may
cross the existing API adapter; no new raw-content endpoint is introduced.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from ml.features import (
    ConventionalExtractor, ConventionalFeatureBuilder, ExperimentFeatureBuilder,
    FeatureBundle, FeatureConfiguration,
)
from ml.models import UnavailableModel
from ml.preprocessing import (
    ArtifactParserError, ArtifactValidationError, PreparedArtifact, detect_modality, preprocess,
)
from ml.se_brl import ResultEnvelope, failed_result, not_evaluated_result, review_required_result
from ml.se_brl.extraction import RuleEngine
from ml.se_brl.representation import BrlRepresentation


class ComponentExecutionError(RuntimeError):
    """Expected component operational failure; internal details stay out of results."""


@dataclass(frozen=True, slots=True)
class PipelineResult:
    envelope: ResultEnvelope
    artifact: PreparedArtifact | None = None
    representation: BrlRepresentation | None = None
    features: tuple[FeatureBundle, ...] = ()

    def model_input(self, configuration: FeatureConfiguration) -> FeatureBundle:
        if self.envelope.overall_status in {"failed", "review_required"}:
            raise ValueError("Processing did not reach the feature boundary")
        for bundle in self.features:
            if bundle.configuration == configuration:
                bundle.block.require_numeric()
                return bundle
        raise ValueError("Feature configuration was not prepared")


class PretrainingPipeline:
    def __init__(self, conventional: ConventionalExtractor | None = None,
                 rules: RuleEngine | None = None) -> None:
        self.conventional = conventional if conventional is not None else ConventionalFeatureBuilder()
        self.rules = rules if rules is not None else RuleEngine()
        self.model = UnavailableModel()

    def run(self, raw: Mapping[str, object]) -> PipelineResult:
        try:
            modality = detect_modality(raw)
        except ArtifactValidationError:
            return PipelineResult(review_required_result("unknown", ("unsupported_modality",)))
        try:
            artifact = preprocess(raw)
        except ArtifactValidationError:
            return PipelineResult(review_required_result(modality, ("invalid_schema",)))
        except ArtifactParserError:
            return PipelineResult(review_required_result(modality, ("parser_failure",)))
        try:
            conventional = self.conventional.transform(artifact)
            extraction = self.rules.extract(artifact)
            brl = BrlRepresentation(extraction)
            bundles = tuple(ExperimentFeatureBuilder(config).build(conventional, brl)
                            for config in FeatureConfiguration)
        except ComponentExecutionError:
            # The existing envelope has no preprocessing/feature component IDs.
            # The pre-model analytical branch belongs to behavior_identification.
            return PipelineResult(failed_result(modality, "behavior_identification"))
        envelope = not_evaluated_result(modality, extraction.assessment)
        if modality in {"content_bearing_email", "content_bearing_webpage"} and not artifact.required_content_available:
            envelope = review_required_result(modality, ("missing_required_evidence",), extraction.assessment)
        return PipelineResult(envelope, artifact, brl, bundles)
