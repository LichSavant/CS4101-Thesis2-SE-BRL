"""Versioned, content-free feature configuration manifests; never model artifacts."""

import json
from dataclasses import asdict, dataclass

from ml.metadata import canonical_json, fingerprint, require_text

FEATURE_SCHEMA_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class FeatureSchema:
    preprocessing_version: str | None
    conventional_configuration: str | None
    codebook_version: str
    ruleset_version: str
    experiment_configuration: str
    schema_version: str = FEATURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (self.schema_version != FEATURE_SCHEMA_VERSION or type(self.experiment_configuration) is not str
                or self.experiment_configuration not in {"E1", "E2", "E3"}):
            raise ValueError("Unsupported feature schema version or experiment configuration")
        for value in (self.codebook_version, self.ruleset_version):
            require_text(value)
        if self.preprocessing_version is not None:
            require_text(self.preprocessing_version)
        if self.conventional_configuration is not None:
            if type(self.conventional_configuration) is not str:
                raise ValueError("Conventional configuration must be canonical JSON")
            parsed = json.loads(self.conventional_configuration)
            if not isinstance(parsed, dict) or canonical_json(parsed) != self.conventional_configuration:
                raise ValueError("Conventional configuration must be a canonical JSON object")

    def to_json(self) -> str:
        return canonical_json(asdict(self))

    @classmethod
    def from_json(cls, value: str) -> "FeatureSchema":
        parsed = json.loads(value)
        expected = set(cls.__dataclass_fields__)
        if not isinstance(parsed, dict) or set(parsed) != expected:
            raise ValueError("Invalid feature schema fields")
        return cls(**parsed)

    @property
    def configuration_id(self) -> str:
        return fingerprint(asdict(self))
