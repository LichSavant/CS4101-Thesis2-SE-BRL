"""Factual software/research readiness, separate from the analytical API envelope."""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ml.pipeline import PipelineResult


class ReadinessStatus(Enum):
    READY = "ready"
    PARTIAL = "partial"
    STRUCTURALLY_READY = "structurally_ready"
    NOT_AVAILABLE = "not_available"
    NOT_TRAINED = "not_trained"
    NOT_FITTED = "not_fitted"
    BLOCKED_BY_Z_VALUES = "blocked_by_z_values"
    NOT_FROZEN = "not_frozen"
    UNAVAILABLE = "unavailable"


class Dependency(Enum):
    DATASET = "dataset_dependent"
    GROUND_TRUTH = "ground_truth_dependent"
    INDEPENDENT_EVIDENCE = "independent_evidence_dependent"
    TRAINING = "training_dependent"
    VALIDATION = "validation_dependent"


@dataclass(frozen=True, slots=True)
class StageReadiness:
    stage: str
    status: ReadinessStatus
    dependencies: tuple[Dependency, ...] = ()
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    stages: tuple[StageReadiness, ...]
    report_version: str = "0.1.0"

    def to_dict(self) -> dict[str, object]:
        return {"report_version": self.report_version, "stages": [
            {"stage": s.stage, "status": s.status.value,
             "dependencies": [d.value for d in s.dependencies], "blockers": list(s.blockers)}
            for s in self.stages
        ]}


def pipeline_readiness(result: "PipelineResult | None" = None) -> ReadinessReport:
    """READY describes implemented infrastructure, never trained-model readiness.

    Without a run, report only structural readiness. A supplied run can further
    restrict input/feature readiness; it cannot promote research stages.
    """
    status = ReadinessStatus
    dep = Dependency
    unavailable_input = result is not None and result.envelope.overall_status in {"review_required", "failed"}
    unavailable_behavior = unavailable_input or (result is not None and result.representation is not None
                                                 and not any(result.representation.extraction.assessment.availability_mask))
    stages = [
        StageReadiness("preprocessing", status.UNAVAILABLE if unavailable_input else status.READY),
        StageReadiness("dataset_adapters", status.STRUCTURALLY_READY, (dep.DATASET,), ("corpus_specific_loaders_not_implemented",)),
        StageReadiness("group_validation", status.READY, (dep.DATASET,)),
        StageReadiness("feature_schema", status.READY),
        StageReadiness("conventional_features", status.UNAVAILABLE if unavailable_input else status.READY),
        StageReadiness("candidate_rule_extraction", status.UNAVAILABLE if unavailable_behavior else status.PARTIAL, (dep.INDEPENDENT_EVIDENCE, dep.GROUND_TRUTH),
                       ("candidate_rules_not_validated", "trust_detectors_require_independent_evidence")),
        StageReadiness("behavioral_ground_truth", status.NOT_AVAILABLE, (dep.DATASET, dep.GROUND_TRUTH)),
        StageReadiness("behavioral_model", status.NOT_TRAINED, (dep.GROUND_TRUTH, dep.TRAINING, dep.VALIDATION)),
    ]
    bundles = {b.configuration.value: b for b in result.features} if result else {}
    for configuration in ("E1", "E2", "E3"):
        bundle = bundles.get(configuration)
        if unavailable_input:
            current, blockers = status.UNAVAILABLE, ("input_processing_incomplete",)
        elif configuration != "E1":
            current, blockers = status.BLOCKED_BY_Z_VALUES, ("learned_behavioral_values_not_available",)
        elif bundle is not None and not bundle.block.missing_components and all(v is not None for v in bundle.block.values.values()):
            current, blockers = status.READY, ()
        else:
            current = status.STRUCTURALLY_READY
            blockers = bundle.block.missing_components if bundle else ("feature_fit_or_explicit_configuration_required",)
        stages.append(StageReadiness(configuration, current,
                                     (dep.DATASET,) if configuration == "E1" else (dep.GROUND_TRUTH, dep.TRAINING), blockers))
    stages.extend((
        StageReadiness("classifier", status.NOT_TRAINED, (dep.DATASET, dep.TRAINING, dep.VALIDATION)),
        StageReadiness("calibration", status.NOT_TRAINED, (dep.DATASET, dep.TRAINING, dep.VALIDATION)),
        StageReadiness("SHAP", status.NOT_AVAILABLE, (dep.TRAINING, dep.VALIDATION)),
        StageReadiness("decision_rules", status.NOT_FROZEN, (dep.GROUND_TRUTH, dep.VALIDATION)),
    ))
    return ReadinessReport(tuple(stages))
