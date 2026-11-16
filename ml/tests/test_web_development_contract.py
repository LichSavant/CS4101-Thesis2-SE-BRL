"""Content Web uses its own class provenance, matched folds and deterministic E2."""
from dataclasses import replace
import csv
import hashlib

import pytest

from ml.development_experiments import DevelopmentSpecification, FeatureColumn, behavioral_columns, build_development_dataset, development_folds
from ml.development_experiments import _read_csv
from ml.development_runner import dataset_fingerprint, dimension_ablations
from ml.classifier_adapters import FoldClassifier
from ml.experiment_inputs import InputContractError
from ml.notebook_contracts import capture_population
from ml.tests.test_classifier_adapters import genuine, model, preprocessing


def records():
    raw, behavior = [], []
    for fold in range(1, 6):
        for target in (0, 1):
            i = len(raw)
            row = dict(observation_id=f"synthetic-web-{i}", target=target, source_dataset="Phishing Website Dataset",
                source_file="phishing.csv" if target else "not-phishing.csv", source_row_id=fold-1,
                source_label="phishing" if target else "legitimate", group_id=f"synthetic-supplied-web-group-{fold}",
                partition="development", cv_fold=fold, visible_text=f"Synthetic Web observation {i}", html=None,
                language="en", conventional_signal=target)
            vector = {key: row[key] for key in ("observation_id", "target", "group_id", "partition", "cv_fold")}
            vector.update({name: (1 if name.endswith("_available") else target) for name in behavioral_columns()})
            raw.append(row);behavior.append(vector)
    spec = DevelopmentSpecification("Web", (FeatureColumn("conventional_signal", "numeric"),),
                                    "synthetic:Web-supplied-assignments", "synthetic:Web-dictionary")
    return raw, behavior, spec


def test_web_population_preserves_native_class_files_and_supplied_controls():
    rows, vectors, specification = records()
    dataset = build_development_dataset(rows, vectors, specification=specification)
    assert dataset.configurations == ("E1", "E2", "E3")
    assert len(capture_population(rows, dataset="Web")) == 10
    assert dataset_fingerprint(dataset)
    controls = []
    for config in dataset.configurations:
        folds = development_folds(dataset, config)
        controls.append([(f.validation_fold, f.training_ids, f.validation_ids, f.y_train, f.y_validation) for f in folds])
    assert controls[0] == controls[1] == controls[2]
    assert len(dimension_ablations(dataset)) == 4
    assert [r.observation_id for r in dataset.observations] == [r["observation_id"] for r in rows]


@pytest.mark.parametrize("change", ({"source_label": 1}, {"source_file": "not-phishing.csv"},
    {"source_dataset": "PhiUSIIL"}, {"target": 0}, {"html": None, "visible_text": None}))
def test_web_rejects_relabeling_technical_substitution_or_missing_content(change):
    rows, vectors, spec = records()
    rows[1] = dict(rows[1], **change)
    with pytest.raises(InputContractError):
        build_development_dataset(rows, vectors, specification=spec)


def test_source_native_metadata_never_enters_predictors():
    for name in ("source_file", "source_label", "source_html_available", "target", "cv_fold"):
        with pytest.raises(InputContractError):
            FeatureColumn(name, "numeric")


def test_web_csv_keeps_unavailable_distinct_from_known_empty(tmp_path):
    rows, _, spec = records()
    rows = rows[:2]
    for row in rows:
        row.update(source_html_available=0, source_visible_text_available=1)
    rows[0]["html"] = None
    rows[1]["html"] = ""
    rows[1]["source_html_available"] = 1
    path = tmp_path/"web.csv"
    def write():
        with path.open("w",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        return hashlib.sha256(path.read_bytes()).hexdigest()
    loaded = _read_csv(path,write(),behavioral=False,specification=spec)
    assert loaded[0]["html"] is None and loaded[1]["html"] == ""
    assert loaded[1]["source_label"] == "phishing"
    rows[0]["source_visible_text_available"] = 0
    with pytest.raises(InputContractError,match="unavailable_field_has_content"):
        _read_csv(path,write(),behavioral=False,specification=spec)


@genuine
def test_existing_genuine_adapter_accepts_web_e3_without_a_duplicate_engine():
    rows, vectors, spec = records()
    dataset = build_development_dataset(rows, vectors, specification=spec)
    fold = development_folds(dataset, "E3")[0]
    pipeline = FoldClassifier(spec, model(), preprocessing(), "E3")
    pipeline.fit(fold.x_train, fold.y_train, feature_names=fold.feature_names, seed=17)
    scored = pipeline.score(fold.x_validation, observation_ids=fold.validation_ids)
    assert scored.observation_ids == fold.validation_ids and scored.positive_label == 1
    with pytest.raises(InputContractError):
        FoldClassifier(spec, model(), preprocessing(), "U1")
