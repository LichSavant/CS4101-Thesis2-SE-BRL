"""Future classifier/trainer ports. No estimator, training run, or artifact exists.

Classifier labels or decision margins are not calibrated phishing probabilities.
Calibration and decisions remain separate downstream research components.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from ml.features import FeatureBundle, FeatureConfiguration, SplitManifest


class CandidateAlgorithm(StrEnum):
    LOGISTIC_REGRESSION = "logistic_regression"
    LINEAR_SVM = "linear_svm"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"


class ModelUnavailableError(RuntimeError):
    """No validated model is integrated; never return a substitute prediction."""


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    artifact_version: str
    algorithm: CandidateAlgorithm
    feature_names: tuple[str, ...]
    configuration: str
    split_manifest_id: str
    preprocessing_version: str
    codebook_version: str
    ruleset_version: str


class Classifier(Protocol):
    metadata: ModelMetadata

    def predict_labels(self, rows: tuple[tuple[float, ...], ...]) -> tuple[str, ...]: ...


class Trainer(Protocol):
    """Future adapters must validate numeric feature readiness and training IDs."""

    def fit(self, features: Mapping[str, FeatureBundle], labels: Mapping[str, str],
            manifest: SplitManifest) -> Classifier: ...


@dataclass(frozen=True, slots=True)
class TrainingInput:
    record_ids: tuple[str, ...]
    feature_names: tuple[str, ...]
    rows: tuple[tuple[float, ...], ...]
    labels: tuple[str, ...]
    configuration: FeatureConfiguration
    manifest: SplitManifest


def prepare_training_input(features: Mapping[str, FeatureBundle], labels: Mapping[str, str],
                           manifest: SplitManifest) -> TrainingInput:
    """Validate a future adapter's inputs; this function does not train anything."""
    manifest.validate_training(tuple(features))
    manifest.validate_training(tuple(labels))
    first = features[manifest.train_ids[0]]
    names = tuple(first.block.require_numeric())
    rows = []
    for record_id in manifest.train_ids:
        bundle = features[record_id]
        numeric = bundle.block.require_numeric()
        if tuple(numeric) != names or bundle.configuration != first.configuration or bundle.schema != first.schema:
            raise ValueError("Training rows require identical feature schemas and configurations")
        if type(labels[record_id]) is not str or not labels[record_id].strip():
            raise ValueError("Training labels must be explicitly supplied")
        rows.append(tuple(numeric.values()))
    return TrainingInput(manifest.train_ids, names, tuple(rows),
                         tuple(labels[i] for i in manifest.train_ids), first.configuration, manifest)


class UnavailableModel:
    def predict(self, features: FeatureBundle) -> None:
        features.block.require_numeric()
        raise ModelUnavailableError("A validated phishing model is not integrated")
