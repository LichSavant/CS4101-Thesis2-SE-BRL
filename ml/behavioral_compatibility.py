"""Read-only integration review, outside Vera's inference implementation.

These checks establish names, order and missingness only. They never establish
semantic equivalence, authenticated custody, scientific approval or fit authority.
No scorer, model, file loader, corpus reader or experiment launcher is invoked.
"""
from collections.abc import Mapping
from dataclasses import dataclass

from ml.se_brl.codebook import load_codebook


class BehavioralCompatibilityError(ValueError):
    """Sanitized boundary error; never includes supplied evidence or values."""


@dataclass(frozen=True, slots=True)
class CompatibilityReview:
    structurally_compatible: bool
    mismatches: tuple[str, ...]
    policy_blockers: tuple[str, ...] = (
        'P6_behavioral_semantics_unreconciled',
        'P7_feature_dictionary_not_accepted',
        'P11_research_authorization_required',
    )

    @property
    def research_ready(self) -> bool:
        # Deliberately not caller-configurable. Review never grants authority.
        return False


def _orders() -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    book = load_codebook()
    dimensions = tuple(book['vector_ordering']['dimension_order'])
    indicators = tuple(i['id'] for d in book['dimensions'] for i in d['indicators'])
    names = tuple(f'{d}_{suffix}' for suffix in ('supported', 'available') for d in dimensions)
    return dimensions, indicators, names


def review_contract(descriptor: Mapping) -> CompatibilityReview:
    """Compare a supplied descriptor; its approval flags are not authoritative.

    This consumes metadata explicitly supplied by a trusted operator, not remote
    Python code. Structural success leaves all scientific gates closed.
    """
    if not isinstance(descriptor, Mapping):
        raise BehavioralCompatibilityError('invalid_representation_descriptor')
    book = load_codebook()
    dimensions, indicators, _ = _orders()
    expected = {
        'contract_version': '1.0.0',
        'codebook_version': book['codebook_version'],
        'source_schema_version': book['schema_version'],
        'dimension_order': list(dimensions),
        'indicator_order': list(indicators),
        'learned_feature_order': list(book['vector_ordering']['future_structure']),
    }
    mismatches = tuple(key for key, value in expected.items()
                       if type(descriptor.get(key)) is not type(value) or descriptor[key] != value)
    return CompatibilityReview(not mismatches, mismatches)


@dataclass(frozen=True, slots=True)
class RuleVectorReview:
    feature_names: tuple[str, ...]
    values: tuple[int | None, ...]
    review: CompatibilityReview
    representation_type: str = 'rule_derived_binary_v1'

    @property
    def numeric_complete(self) -> bool:
        return all(value is not None for value in self.values)


def review_rule_vector(descriptor: Mapping, *, representation_type: str,
                       feature_names: tuple[str, ...],
                       values: tuple[int | None, ...]) -> RuleVectorReview:
    """Explicit legacy-name mapping for review only; no semantic-score coercion.

    None/None retains incomplete assessment. 0/0 retains unavailable evidence.
    Neither becomes assessed absence. The output is not an experiment input or
    a validated behavioral judgment, even when every numeric value is present.
    """
    review = review_contract(descriptor)
    if not review.structurally_compatible:
        raise BehavioralCompatibilityError('incompatible_representation_contract')
    if type(representation_type) is not str or representation_type != 'rule_derived_binary_v1':
        raise BehavioralCompatibilityError('only_rule_binary_review_supported')
    _, _, canonical = _orders()
    legacy_dimensions = ('pressure_threat', 'lure_attention', 'trust_identity', 'requested_action_consequence')
    legacy = tuple(f'{d}_{suffix}' for suffix in ('supported', 'available') for d in legacy_dimensions)
    if type(feature_names) is not tuple or feature_names not in (canonical, legacy):
        raise BehavioralCompatibilityError('unknown_or_reordered_feature_dictionary')
    if (type(values) is not tuple or len(values) != 8
            or any(v is not None and (type(v) is not int or v not in (0, 1)) for v in values)):
        raise BehavioralCompatibilityError('invalid_rule_binary_values')
    for support, available in zip(values[:4], values[4:], strict=True):
        if (support is None) != (available is None) or (support is not None and support > available):
            raise BehavioralCompatibilityError('contradictory_support_availability')
    return RuleVectorReview(canonical, values, review)
