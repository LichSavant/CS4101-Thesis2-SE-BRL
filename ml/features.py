"""Conventional features and shared E1/E2/E3 boundaries, without model fitting.

TF-IDF uses raw term counts, smoothed IDF log((1+n)/(1+df))+1 and L2
normalization. Vocabulary/IDF are learned only by an explicit training fit.
The small dependency-free implementation is an interface baseline, not a
large-corpus optimized vectorizer. No scalers or encoders are fitted implicitly.
"""

from __future__ import annotations

import ipaddress
import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from email.utils import parseaddr
from enum import StrEnum
from types import MappingProxyType
from typing import Protocol
from urllib.parse import urlsplit

from ml.preprocessing import PreparedArtifact, PREPROCESSING_VERSION
from ml.se_brl.codebook import load_codebook
from ml.se_brl.representation import BrlRepresentation
from ml.feature_schema import FeatureSchema
from ml.feature_storage import CombinedFeatureValues, SparseFeatureValues
from ml.metadata import canonical_json, fingerprint

CONVENTIONAL_FEATURE_VERSION = "0.1.0"
WORD_TOKENS = re.compile(r"\b\w+\b")


class FeatureUnavailableError(ValueError):
    """Required fitted or learned features do not exist."""


@dataclass(frozen=True, slots=True)
class SplitManifest:
    manifest_id: str
    train_ids: tuple[str, ...]
    validation_ids: tuple[str, ...] = ()
    test_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        groups = (self.train_ids, self.validation_ids, self.test_ids)
        if any(type(group) is not tuple for group in groups):
            raise ValueError("Split IDs must be immutable tuples")
        all_ids = self.train_ids + self.validation_ids + self.test_ids
        if (not isinstance(self.manifest_id, str) or not self.manifest_id.strip()
                or not self.train_ids or any(type(i) is not str or not i for i in all_ids)
                or len(set(all_ids)) != len(all_ids)):
            raise ValueError("Split manifest requires unique, disjoint record IDs")

    def validate_training(self, record_ids: Sequence[str]) -> None:
        if len(record_ids) != len(self.train_ids) or set(record_ids) != set(self.train_ids):
            raise ValueError("Fit accepts exactly the manifest training records")


@dataclass(frozen=True, slots=True)
class FeatureBlock:
    values: Mapping[str, float | None]
    missing_components: tuple[str, ...] = ()
    configuration_json: str | None = None
    preprocessing_version: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.values, (SparseFeatureValues, CombinedFeatureValues)):
            return  # These implementations validate and freeze their own storage.
        values = dict(self.values)
        if any(not isinstance(k, str) or not k for k in values):
            raise ValueError("Feature names must be nonempty strings")
        if any(v is not None and (type(v) not in (float, int) or not math.isfinite(v)) for v in values.values()):
            raise ValueError("Features must be finite numeric values or explicit None")
        object.__setattr__(self, "values", MappingProxyType(values))

    def require_numeric(self) -> Mapping[str, float]:
        sparse = isinstance(self.values, (SparseFeatureValues, CombinedFeatureValues))
        missing = self.values.has_missing_values if sparse else any(value is None for value in self.values.values())
        if self.missing_components or missing:
            raise FeatureUnavailableError("Required feature components are unavailable")
        if sparse:
            return self.values
        return MappingProxyType({key: float(value) for key, value in self.values.items()})


class ConventionalExtractor(Protocol):
    def fit(self, artifacts: Mapping[str, PreparedArtifact], manifest: SplitManifest) -> None: ...
    def transform(self, artifact: PreparedArtifact) -> FeatureBlock: ...


class TfidfExtractor:
    def __init__(self, analyzer: str = "word", ngram_range: tuple[int, int] = (1, 1)) -> None:
        if (analyzer not in {"word", "char"} or type(ngram_range) is not tuple
                or len(ngram_range) != 2 or any(type(n) is not int for n in ngram_range)
                or not 1 <= ngram_range[0] <= ngram_range[1] <= 5):
            raise ValueError("Invalid TF-IDF configuration")
        self.analyzer = analyzer
        self.ngram_range = ngram_range
        self._vocabulary: tuple[str, ...] | None = None
        self._idf: Mapping[str, float] | None = None
        self._fit_manifest: SplitManifest | None = None
        self._fitted_state_id: str | None = None
        self._fitted_configuration: tuple[str, tuple[int, int]] | None = None

    @property
    def vocabulary(self) -> tuple[str, ...] | None:
        return self._vocabulary

    @property
    def idf(self) -> Mapping[str, float] | None:
        return self._idf

    @property
    def fit_manifest(self) -> SplitManifest | None:
        return self._fit_manifest

    @property
    def fitted_state_id(self) -> str | None:
        return self._fitted_state_id

    def _terms(self, text: str) -> Counter[str]:
        tokens = WORD_TOKENS.findall(text) if self.analyzer == "word" else list(text)
        joiner = " " if self.analyzer == "word" else ""
        return Counter(joiner.join(tokens[start:start + n])
                       for n in range(self.ngram_range[0], self.ngram_range[1] + 1)
                       for start in range(len(tokens) - n + 1))

    def fit(self, artifacts: Mapping[str, PreparedArtifact], manifest: SplitManifest) -> None:
        manifest.validate_training(tuple(artifacts))
        if self.fit_manifest is not None:
            raise ValueError("Use a fresh extractor for each training split")
        frequencies: Counter[str] = Counter()
        for artifact in artifacts.values():
            if not isinstance(artifact, PreparedArtifact) or artifact.preprocessing_version != PREPROCESSING_VERSION:
                raise ValueError("Incompatible preprocessing")
            frequencies.update(set(self._terms(artifact.model_text)))
        # Empty training text is a valid zero-column text block, never invented tokens.
        vocabulary = tuple(sorted(frequencies))
        self._idf = MappingProxyType({term: math.log((1 + len(artifacts)) / (1 + frequencies[term])) + 1
                                     for term in vocabulary})
        self._vocabulary = vocabulary
        self._fit_manifest = manifest
        self._fitted_configuration = (self.analyzer, self.ngram_range)
        self._fitted_state_id = fingerprint({
            "vocabulary": vocabulary, "idf": self.idf,
            "split": {"id": manifest.manifest_id, "train": manifest.train_ids,
                      "validation": manifest.validation_ids, "test": manifest.test_ids},
            "training_text": {key: fingerprint(value.model_text) for key, value in artifacts.items()},
        })

    def describe_configuration(self) -> dict[str, object]:
        if self._fitted_configuration is not None and self._fitted_configuration != (self.analyzer, self.ngram_range):
            raise ValueError("TF-IDF configuration changed after fitting")
        return {"analyzer": self.analyzer, "ngram_range": self.ngram_range,
                "tf": "raw_count", "idf": "smoothed_log", "normalization": "l2",
                "fitted_state_id": self.fitted_state_id}

    def transform(self, artifact: PreparedArtifact) -> FeatureBlock:
        self.describe_configuration()
        if self.vocabulary is None or self.idf is None:
            raise FeatureUnavailableError("TF-IDF has not been fitted on training data")
        if artifact.preprocessing_version != PREPROCESSING_VERSION:
            raise ValueError("Incompatible preprocessing")
        counts = self._terms(artifact.model_text)
        weights = {term: counts[term] * self.idf[term] for term in self.vocabulary}
        norm = math.sqrt(sum(value * value for value in weights.values())) or 1.0
        return FeatureBlock({f"{self.analyzer}_tfidf:{term}": value / norm for term, value in weights.items()})


def url_features(urls: tuple[str, ...]) -> dict[str, float]:
    parsed = [urlsplit(url) for url in urls]
    ip_count = 0
    for item in parsed:
        try:
            ipaddress.ip_address(item.hostname or "")
        except ValueError:
            continue
        ip_count += 1
    return {
        "url_count": float(len(urls)),
        "url_max_length": float(max(map(len, urls), default=0)),
        "url_digit_count": float(sum(c.isdigit() for url in urls for c in url)),
        "url_http_count": float(sum(item.scheme == "http" for item in parsed)),
        "url_ip_host_count": float(ip_count),
        "url_max_host_labels": float(max(((item.hostname or "").count(".") + 1 for item in parsed), default=0)),
        "url_query_count": float(sum(bool(item.query) for item in parsed)),
    }


def structural_features(artifact: PreparedArtifact) -> FeatureBlock:
    def domain(address: str | None) -> str:
        return parseaddr(address or "")[1].rpartition("@")[2].casefold()

    sender_domain, reply_domain = domain(artifact.sender), domain(artifact.reply_to)
    tags = Counter(item.tag for item in artifact.structures)
    values = {
        "text_char_count": float(len(artifact.model_text)),
        "text_word_count": float(len(artifact.model_text.split())),
        "content_available": float(artifact.required_content_available),
        "body_supplied": float("body" in artifact.supplied_fields),
        "html_supplied": float("html" in artifact.supplied_fields),
        "links_authorized": float(artifact.link_extraction_authorized),
        "sender_available": float(bool(sender_domain)),
        "reply_to_available": float(bool(reply_domain)),
        "sender_reply_domain_differ": float(bool(sender_domain and reply_domain and sender_domain != reply_domain)),
        "header_count": float(len(artifact.headers)),
        "quoted_segment_count": float(sum(segment.quoted for segment in artifact.segments)),
        "html_element_count": float(len(artifact.structures)),
        "form_count": float(tags["form"]),
        "input_count": float(tags["input"]),
        "link_element_count": float(tags["a"]),
        "password_input_count": float(sum(item.tag == "input" and dict(item.attributes).get("type", "").casefold() == "password" for item in artifact.structures)),
    }
    values.update(url_features(artifact.urls))
    return FeatureBlock({f"conventional:{key}": value for key, value in values.items()})


class ConventionalFeatureBuilder:
    def __init__(self, *, include_tfidf: bool = True) -> None:
        self.text_extractors = (TfidfExtractor("word", (1, 2)), TfidfExtractor("char", (3, 5))) if include_tfidf else ()

    def fit(self, artifacts: Mapping[str, PreparedArtifact], manifest: SplitManifest) -> None:
        manifest.validate_training(tuple(artifacts))
        for extractor in self.text_extractors:
            extractor.fit(artifacts, manifest)

    def transform(self, artifact: PreparedArtifact) -> FeatureBlock:
        values = dict(structural_features(artifact).values)
        missing = []
        for extractor in self.text_extractors:
            if extractor.fit_manifest is None:
                missing.append(f"{extractor.analyzer}_tfidf_not_fitted")
            else:
                values.update(extractor.transform(artifact).values)
        configuration = canonical_json({"version": CONVENTIONAL_FEATURE_VERSION,
                                        "tfidf": tuple(e.describe_configuration() for e in self.text_extractors)})
        return FeatureBlock(values, tuple(missing), configuration, artifact.preprocessing_version)


class FeatureConfiguration(StrEnum):
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"


@dataclass(frozen=True, slots=True)
class FeatureBundle:
    configuration: FeatureConfiguration
    block: FeatureBlock
    schema: FeatureSchema | None = None


class ExperimentFeatureBuilder:
    """One preprocessed artifact and BRL representation feed every configuration."""

    def __init__(self, configuration: FeatureConfiguration) -> None:
        self.configuration = FeatureConfiguration(configuration)
        self.slots = load_codebook()["vector_ordering"]["future_structure"]

    def build(self, conventional: FeatureBlock, brl: BrlRepresentation) -> FeatureBundle:
        parts = []
        missing = []
        if self.configuration in {FeatureConfiguration.E1, FeatureConfiguration.E3}:
            parts.append(conventional.values)
            missing.extend(conventional.missing_components)
        if self.configuration in {FeatureConfiguration.E2, FeatureConfiguration.E3}:
            slots = self.slots
            parts.append({f"se_brl:{name}": value for name, value in zip(slots, brl.slots, strict=True)})
            missing.append("learned_behavioral_values_not_available")
        values = parts[0] if len(parts) == 1 else CombinedFeatureValues(tuple(parts))
        schema = FeatureSchema(conventional.preprocessing_version,
                               conventional.configuration_json if self.configuration != FeatureConfiguration.E2 else None,
                               brl.extraction.assessment.codebook_version, brl.extraction.ruleset_version,
                               self.configuration.value)
        return FeatureBundle(self.configuration, FeatureBlock(values, tuple(missing)), schema)
