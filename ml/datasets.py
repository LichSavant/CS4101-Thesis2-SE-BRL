"""Canonical offline adapter boundary; no corpus loader, download, or annotation."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from ml.grouping import GroupIdentifier, validate_groups
from ml.metadata import freeze_json, require_text
from ml.preprocessing import PreparedArtifact, detect_modality, preprocess
from ml.se_brl.codebook import load_codebook


class PhishingLabel(Enum):
    PHISHING = "phishing"
    LEGITIMATE = "legitimate"


class BehavioralLabel(Enum):
    SUPPORTED = "supported"
    ABSENT = "absent"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class SourcePhishingLabel:
    value: PhishingLabel
    source_reference: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, PhishingLabel):
            raise ValueError("Expected a source phishing label, not a behavioral label")
        require_text(self.source_reference)


@dataclass(frozen=True, slots=True)
class BehavioralAnnotation:
    indicator_id: str
    value: BehavioralLabel
    evidence_reference: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, BehavioralLabel):
            raise ValueError("Behavioral annotations cannot use phishing source labels")
        require_text(self.indicator_id)
        require_text(self.evidence_reference)


@dataclass(frozen=True, slots=True)
class BehavioralGroundTruth:
    record_id: str
    codebook_version: str
    annotation_protocol: str
    annotations: tuple[BehavioralAnnotation, ...]

    def __post_init__(self) -> None:
        require_text(self.record_id)
        require_text(self.annotation_protocol)
        codebook = load_codebook()
        ids = {i["id"] for d in codebook["dimensions"] for i in d["indicators"]}
        if (self.codebook_version != codebook["codebook_version"]
                or type(self.annotations) is not tuple
                or any(not isinstance(a, BehavioralAnnotation) or a.indicator_id not in ids for a in self.annotations)
                or len({a.indicator_id for a in self.annotations}) != len(self.annotations)):
            raise ValueError("Invalid canonical behavioral annotations")
        # Partial annotations are explicit; omitted indicators are not absent.


@dataclass(frozen=True, slots=True)
class DatasetRecord:
    record_id: str
    source_dataset: str
    modality: str
    artifact_input: Mapping[str, object]
    fields_available: tuple[str, ...]
    content_available: bool | None
    provenance: Mapping[str, object]
    source_record_id: str | None = None
    phishing_label: SourcePhishingLabel | None = None
    groups: tuple[GroupIdentifier, ...] = ()
    source_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.record_id)
        require_text(self.source_dataset)
        if self.source_record_id is not None:
            require_text(self.source_record_id)
        if self.phishing_label is not None and not isinstance(self.phishing_label, SourcePhishingLabel):
            raise ValueError("Record label must be an explicit source phishing label")
        if self.content_available is not None and type(self.content_available) is not bool:
            raise ValueError("Content availability must be Boolean or unknown")
        if detect_modality(self.artifact_input) != self.modality:
            raise ValueError("Dataset modality contradicts artifact kind")
        expected = set(self.artifact_input) - {"kind", "study_purpose", "body_collection_authorized", "link_extraction_authorized"}
        if (type(self.fields_available) is not tuple
                or any(type(f) is not str for f in self.fields_available)
                or len(set(self.fields_available)) != len(self.fields_available)
                or set(self.fields_available) != expected):
            raise ValueError("Available fields must describe exactly the supplied artifact fields")
        if not isinstance(self.provenance, Mapping) or not self.provenance or not isinstance(self.source_metadata, Mapping):
            raise ValueError("Dataset record requires provenance metadata")
        validate_groups(self.groups)
        for name in ("artifact_input", "provenance", "source_metadata"):
            object.__setattr__(self, name, freeze_json(getattr(self, name)))

    def validate_prepared(self, artifact: PreparedArtifact) -> None:
        if artifact.modality_id != self.modality:
            raise ValueError("Prepared modality does not match dataset record")
        if self.content_available is not None and self.content_available != artifact.required_content_available:
            raise ValueError("Declared content availability contradicts prepared evidence")


@dataclass(frozen=True, slots=True)
class PreparedDatasetRecord:
    record: DatasetRecord
    artifact: PreparedArtifact


class DatasetAdapter(Protocol):
    def adapt(self, source_record: Mapping[str, object]) -> DatasetRecord: ...


def prepare_record(record: DatasetRecord) -> PreparedDatasetRecord:
    if not isinstance(record, DatasetRecord):
        raise TypeError("Expected a canonical dataset record")
    artifact = preprocess(record.artifact_input)
    record.validate_prepared(artifact)
    return PreparedDatasetRecord(record, artifact)
