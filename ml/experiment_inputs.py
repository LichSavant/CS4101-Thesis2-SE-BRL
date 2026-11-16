"""Offline preparation contracts, not corpus approval, extraction, or model training.

Nothing here downloads, reads files, creates splits, or changes runtime SE-BRL.
Caller-supplied provenance/label documentation is retained, not authenticated.
Constructing an observation does not authorize body/link collection or transport.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
import re
import unicodedata
from types import MappingProxyType
from typing import Protocol

from ml.datasets import PhishingLabel
from ml.metadata import fingerprint

ADAPTER_CONTRACT_VERSION = "0.1.0"


class InputContractError(ValueError):
    """Stable errors deliberately omit source values and message content."""


def reject_excluded_source_identifiers(*values: str) -> None:
    """Reject excluded source aliases in metadata, never scan artifact content.

    This is an additional deny rule, not dataset admission or an allowlist.
    It does not identify renamed payloads or authenticate supplied provenance.
    """
    for value in values:
        _identifier(value)
        normalized = re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKC', value).casefold())
        if any(alias in normalized for alias in ('spaphish', 'spafish')):
            raise InputContractError('excluded_source_identifier')


def _identifier(value: object) -> str:
    if type(value) is not str or not value.strip() or len(value) > 1024 or any(ord(c) < 32 for c in value):
        raise InputContractError("invalid_identifier")
    return value


class Availability(Enum):
    UNAVAILABLE = "unavailable"
    KNOWN_EMPTY = "known_empty"
    AVAILABLE = "available"


@dataclass(frozen=True, slots=True)
class TextField:
    value: str | None = None

    def __post_init__(self) -> None:
        if self.value is not None and (type(self.value) is not str or len(self.value) > 200_000 or "\x00" in self.value):
            raise InputContractError("invalid_text_field")

    @property
    def availability(self) -> Availability:
        if self.value is None:
            return Availability.UNAVAILABLE
        return Availability.AVAILABLE if self.value.strip() else Availability.KNOWN_EMPTY


@dataclass(frozen=True, slots=True)
class LinkField:
    """Only supplied links. None is unknown; an explicit empty tuple is known-empty.

    This field does not extract, fetch, normalize or certify URLs. Runtime input
    authorization and URL validation must still be applied before analysis.
    """

    value: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.value is not None and (type(self.value) is not tuple or len(self.value) > 500
                                      or any(type(v) is not str or not v.strip() or len(v) > 8192 for v in self.value)):
            raise InputContractError("invalid_link_field")

    @property
    def availability(self) -> Availability:
        if self.value is None:
            return Availability.UNAVAILABLE
        return Availability.AVAILABLE if self.value else Availability.KNOWN_EMPTY


@dataclass(frozen=True, slots=True)
class DatasetIdentity:
    dataset_id: str
    snapshot_id: str
    provenance_reference: str

    def __post_init__(self) -> None:
        for value in (self.dataset_id, self.snapshot_id, self.provenance_reference):
            _identifier(value)
        reject_excluded_source_identifiers(self.dataset_id, self.snapshot_id, self.provenance_reference)


@dataclass(frozen=True, slots=True)
class DocumentedLabelMapping:
    entries: tuple[tuple[str | int, PhishingLabel], ...]
    documentation_reference: str

    def __post_init__(self) -> None:
        _identifier(self.documentation_reference)
        if type(self.entries) is not tuple or len(self.entries) < 2:
            raise InputContractError("explicit_label_mapping_required")
        keys = set()
        meanings = set()
        for entry in self.entries:
            if type(entry) is not tuple or len(entry) != 2:
                raise InputContractError("invalid_label_mapping")
            native, meaning = entry
            if type(native) not in (str, int):
                raise InputContractError("invalid_native_label")
            if type(native) is str:
                _identifier(native)
            if not isinstance(meaning, PhishingLabel) or (type(native), native) in keys:
                raise InputContractError("contradictory_label_mapping")
            keys.add((type(native), native))
            meanings.add(meaning)
        if meanings != set(PhishingLabel):
            raise InputContractError("both_label_meanings_required")

    def resolve(self, native: object) -> PhishingLabel:
        # No guessed numeric/string coercion, truthiness mapping, or default class.
        for source, meaning in self.entries:
            if type(source) is type(native) and source == native:
                return meaning
        raise InputContractError("unmapped_source_label")


@dataclass(frozen=True, slots=True)
class EmailObservation:
    observation_id: str
    original_record_id: str
    dataset: DatasetIdentity
    language: str
    source_label: str | int
    target: PhishingLabel
    label_reference: str
    subject: TextField
    body: TextField
    sender: TextField = TextField()
    receiver: TextField = TextField()
    links: LinkField = LinkField()
    contract_version: str = ADAPTER_CONTRACT_VERSION

    def __post_init__(self) -> None:
        for value in (self.observation_id, self.original_record_id, self.label_reference):
            _identifier(value)
        if not isinstance(self.dataset, DatasetIdentity) or not isinstance(self.target, PhishingLabel):
            raise InputContractError("invalid_observation_metadata")
        if type(self.source_label) not in (str, int):
            raise InputContractError("invalid_native_label")
        if type(self.language) is not str or not re.fullmatch(r"[a-z]{2,3}(?:-[a-z0-9]{2,8})*", self.language):
            raise InputContractError("explicit_language_required_use_und_if_unknown")
        if not all(isinstance(f, TextField) for f in (self.subject, self.body, self.sender, self.receiver)) or not isinstance(self.links, LinkField):
            raise InputContractError("typed_evidence_fields_required")
        if self.contract_version != ADAPTER_CONTRACT_VERSION:
            raise InputContractError("incompatible_adapter_contract")


class EmailDatasetAdapter(Protocol):
    contract_version: str

    def adapt(self, row: Mapping[str, object]) -> EmailObservation: ...


@dataclass(frozen=True, slots=True)
class EmailFieldMapping:
    """Explicit source column names; no corpus schema or label semantics inferred."""
    record_id: str
    label: str
    subject: str
    body: str
    sender: str | None = None
    receiver: str | None = None
    links: str | None = None

    def __post_init__(self) -> None:
        supplied = []
        for name in (self.record_id, self.label, self.subject, self.body):
            supplied.append(_identifier(name))
        for name in (self.sender, self.receiver, self.links):
            if name is not None:
                supplied.append(_identifier(name))
        if len(set(supplied)) != len(supplied):
            raise InputContractError("duplicate_source_column_mapping")


class MappedEmailAdapter:
    """Dataset-neutral in-memory adapter; mappings are assertions, not approval.

    Source decoding, language verification and corpus eligibility remain external.
    Link values must already be typed tuples, never guessed from CSV strings.
    """
    contract_version = ADAPTER_CONTRACT_VERSION

    def __init__(self, identity: DatasetIdentity, labels: DocumentedLabelMapping, *,
                 language: str, columns: EmailFieldMapping):
        if not isinstance(identity, DatasetIdentity):
            raise InputContractError("explicit_dataset_identity_required")
        if not isinstance(labels, DocumentedLabelMapping):
            raise InputContractError("explicit_label_mapping_required")
        if not isinstance(columns, EmailFieldMapping):
            raise InputContractError("explicit_source_columns_required")
        if type(language) is not str or not re.fullmatch(r"[a-z]{2,3}(?:-[a-z0-9]{2,8})*", language):
            raise InputContractError("explicit_language_required_use_und_if_unknown")
        self.identity, self.labels, self.language, self.columns = identity, labels, language, columns

    def adapt(self, row: Mapping[str, object]) -> EmailObservation:
        columns = self.columns
        required = {columns.record_id, columns.label, columns.subject, columns.body}
        if not isinstance(row, Mapping) or not required.issubset(row):
            raise InputContractError("missing_required_fields")
        record_id = _identifier(row[columns.record_id])
        native = row[columns.label]
        return EmailObservation(
            observation_id=f"{self.identity.dataset_id}:{fingerprint([self.identity.snapshot_id, record_id])}",
            original_record_id=record_id, dataset=self.identity, language=self.language,
            source_label=native, target=self.labels.resolve(native),
            label_reference=self.labels.documentation_reference,
            subject=TextField(row[columns.subject]), body=TextField(row[columns.body]),
            sender=TextField(row.get(columns.sender) if columns.sender is not None else None),
            receiver=TextField(row.get(columns.receiver) if columns.receiver is not None else None),
            links=LinkField(row.get(columns.links) if columns.links is not None else None),
        )



def validate_population(observations: Iterable[EmailObservation], *, identity: DatasetIdentity,
                        expected_total: int | None = None,
                        expected_targets: Mapping[PhishingLabel, int] | None = None) -> dict[str, int]:
    if not isinstance(identity, DatasetIdentity):
        raise InputContractError("dataset_identity_required")
    if expected_total is not None and (type(expected_total) is not int or expected_total < 0):
        raise InputContractError("invalid_population_expectation")
    if expected_targets is not None:
        if (set(expected_targets) != set(PhishingLabel)
                or any(type(n) is not int or n < 0 for n in expected_targets.values())):
            raise InputContractError("explicit_target_counts_required")
        if expected_total is not None and sum(expected_targets.values()) != expected_total:
            raise InputContractError("contradictory_expected_counts")
    seen = set()
    originals = set()
    counts = {label: 0 for label in PhishingLabel}
    for observation in observations:
        if not isinstance(observation, EmailObservation) or observation.dataset != identity:
            raise InputContractError("mixed_dataset_identity")
        if observation.observation_id in seen or observation.original_record_id in originals:
            raise InputContractError("duplicate_observation_identifier")
        seen.add(observation.observation_id)
        originals.add(observation.original_record_id)
        counts[observation.target] += 1
    if expected_total is not None and len(seen) != expected_total:
        raise InputContractError("population_count_mismatch")
    if expected_targets is not None and counts != dict(expected_targets):
        raise InputContractError("target_count_mismatch")
    return {"total": len(seen), **{label.value: n for label, n in counts.items()}}


@dataclass(frozen=True, slots=True)
class PartitionAssignment:
    observation_id: str
    group_id: str
    partition: str
    cv_fold: int | None = None


def validate_supplied_partitions(assignments: Iterable[PartitionAssignment], *, folds: int = 5) -> dict[str, int]:
    """Validate supplied assertions only. Never infer groups or allocate records."""
    if type(folds) is not int or folds < 2:
        raise InputContractError("invalid_fold_count")
    seen = set()
    group_partitions: dict[str, str] = {}
    group_folds: dict[str, int] = {}
    counts = {p: 0 for p in ("development", "calibration", "test")}
    for row in assignments:
        if not isinstance(row, PartitionAssignment):
            raise InputContractError("typed_partition_assignment_required")
        _identifier(row.observation_id)
        _identifier(row.group_id)
        if row.observation_id in seen:
            raise InputContractError("duplicate_partition_identifier")
        seen.add(row.observation_id)
        if row.partition not in counts:
            raise InputContractError("invalid_partition")
        if group_partitions.setdefault(row.group_id, row.partition) != row.partition:
            raise InputContractError("group_crosses_partitions")
        if row.partition == "development":
            if type(row.cv_fold) is not int or not 1 <= row.cv_fold <= folds:
                raise InputContractError("invalid_development_fold")
            if group_folds.setdefault(row.group_id, row.cv_fold) != row.cv_fold:
                raise InputContractError("group_crosses_folds")
        elif row.cv_fold is not None:
            raise InputContractError("nondevelopment_fold_assigned")
        counts[row.partition] += 1
    return counts


BOOKKEEPING = frozenset({
    "target", "label", "result", "source_label", "native_label", "observation_id", "record_id",
    "original_record_id", "original_hash", "hash", "body_hash", "feature_hash", "group_id",
    "partition", "cv_fold", "source_dataset", "source_row_id", "source_file", "snapshot_sha256", "snapshot_id", "dataset_id",
    "language", "label_reference", "contract_version", "provenance", "provenance_reference", "dataset", "source",
    "filename",  # Native PhiUSIIL record identifier; never a predictor.
})


def select_predictors(values: Mapping[str, object], fields: tuple[str, ...], *,
                      extra_bookkeeping: tuple[str, ...] = ()) -> Mapping[str, object]:
    """Explicit allowlist selection, not dtype discovery or scientific feature choice."""
    if (not isinstance(values, Mapping) or type(fields) is not tuple or not fields
            or any(type(name) is not str for name in fields) or len(set(fields)) != len(fields)):
        raise InputContractError("explicit_unique_predictor_fields_required")
    if type(extra_bookkeeping) is not tuple:
        raise InputContractError("explicit_bookkeeping_fields_required")
    for name in extra_bookkeeping:
        _identifier(name)
    forbidden = BOOKKEEPING | {name.casefold() for name in extra_bookkeeping}
    for name in fields:
        _identifier(name)
        if name.casefold() in forbidden or name.casefold().startswith(("source_", "provenance_")):
            raise InputContractError("bookkeeping_predictor_forbidden")
        if name not in values:
            raise InputContractError("missing_predictor_field")
    return MappingProxyType({name: values[name] for name in fields})


@dataclass(frozen=True, slots=True)
class LexicalGateResult:
    status: str
    reason: str | None
    result: object = None


def gate_english_lexical(observation: EmailObservation,
                         evaluate: Callable[[EmailObservation], object]) -> LexicalGateResult:
    """Gate the new preparation path; unsupported language is never absence.

    No translation, language detection, canonical dimension aggregation, or change
    to the existing notebook/runtime extractors is implied by this boundary.
    """
    if not isinstance(observation, EmailObservation):
        raise InputContractError("typed_observation_required")
    if observation.language.split("-")[0] == "und":
        return LexicalGateResult("unavailable", "unknown_language")
    if observation.language.split("-")[0] != "en":
        return LexicalGateResult("unavailable", "unsupported_english_lexical_language")
    return LexicalGateResult("evaluated", None, evaluate(observation))
