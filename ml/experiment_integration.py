"""In-memory adapter integration; no corpus loading, split creation, or fitting.

This boundary checks supplied joins and limits lexical callbacks to development.
It does not authenticate provenance, approve a candidate, or replace runtime rules.
"""
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field

from ml.datasets import PhishingLabel
from ml.experiment_inputs import (
    Availability, DatasetIdentity, EmailObservation, InputContractError, LexicalGateResult,
    LinkField, PartitionAssignment, TextField, gate_english_lexical,
    validate_population, validate_supplied_partitions,
)

INTEGRATION_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class EmailEvidenceInput:
    """Evidence-only callback view: no target, native label, source, or partition.

    Collection authorization is not implied. Callers of runtime preprocessing
    must separately supply explicit body/link authorization and study purpose.
    """
    subject: TextField = field(repr=False)
    body: TextField = field(repr=False)
    sender: TextField = field(repr=False)
    links: LinkField = field(repr=False)


@dataclass(frozen=True, slots=True)
class DevelopmentLexicalResult:
    observation_id: str
    evaluation: LexicalGateResult = field(repr=False)


def _bind(observations: Iterable[EmailObservation], assignments: Iterable[PartitionAssignment], *,
          identity: DatasetIdentity, expected_total: int,
          expected_targets: Mapping[PhishingLabel, int], folds: int
          ) -> tuple[tuple[EmailObservation, PartitionAssignment], ...]:
    # Integration requires concrete expectations; the standalone validator also
    # supports callers that intentionally omit either expectation.
    if type(expected_total) is not int or expected_total < 0:
        raise InputContractError("invalid_population_expectation")
    if not isinstance(expected_targets, Mapping):
        raise InputContractError("explicit_target_counts_required")
    observations, assignments = tuple(observations), tuple(assignments)
    validate_population(observations, identity=identity, expected_total=expected_total,
                        expected_targets=expected_targets)
    if not observations:
        raise InputContractError("empty_integration_population")
    validate_supplied_partitions(assignments, folds=folds)
    by_id = {assignment.observation_id: assignment for assignment in assignments}
    if set(by_id) != {observation.observation_id for observation in observations}:
        raise InputContractError("partition_population_mismatch")
    # Keep supplied observation order; assignment order cannot misalign evidence.
    return tuple((observation, by_id[observation.observation_id]) for observation in observations)


def evaluate_development_lexical(
    observations: Iterable[EmailObservation], assignments: Iterable[PartitionAssignment], *,
    identity: DatasetIdentity, expected_total: int,
    expected_targets: Mapping[PhishingLabel, int],
    evaluate: Callable[[EmailEvidenceInput], object], folds: int = 5,
) -> tuple[DevelopmentLexicalResult, ...]:
    """Validate the entire supplied batch before any development callback.

    Calibration/test records never reach the callback. Unsupported language and
    absent assessable text return unavailable with no fabricated support vector.
    This is deterministic feature evaluation, never a training or holdout API.
    Expected total and target counts must be concrete; None is not accepted.
    A callback returns an arbitrary result, passed through without independent
    evidence-schema validation. An evaluated status only means it returned.
    Evaluator exceptions abort the call with a sanitized error; no partial result
    is returned. Arbitrary callbacks can have side effects: use trusted pure ones.
    """
    bound = _bind(observations, assignments, identity=identity, expected_total=expected_total,
                  expected_targets=expected_targets, folds=folds)
    if not callable(evaluate):
        raise InputContractError("lexical_evaluator_required")
    results = []
    for observation, assignment in bound:
        if assignment.partition != "development":
            continue
        if all(f.availability is not Availability.AVAILABLE for f in (observation.subject, observation.body)):
            evaluation = LexicalGateResult("unavailable", "missing_text_evidence")
        else:
            view = EmailEvidenceInput(observation.subject, observation.body, observation.sender, observation.links)
            try:
                evaluation = gate_english_lexical(observation, lambda _: evaluate(view))
            except Exception:
                raise InputContractError("lexical_evaluator_failed") from None
        results.append(DevelopmentLexicalResult(observation.observation_id, evaluation))
    return tuple(results)
