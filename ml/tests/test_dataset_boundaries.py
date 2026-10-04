from dataclasses import replace

import pytest

from ml.datasets import (BehavioralAnnotation, BehavioralGroundTruth, BehavioralLabel, DatasetRecord,
                         PhishingLabel, SourcePhishingLabel, prepare_record)
from ml.features import SplitManifest
from ml.grouping import GroupAwareManifest, GroupIdentifier, GroupKind


def record(**changes):
    values = dict(record_id="fixture:1", source_dataset="unit-fixture", source_record_id="1",
                  modality="content_bearing_email", artifact_input={"kind": "email", "subject": "Hello"},
                  fields_available=("subject",), content_available=True,
                  provenance={"source": "unit-test", "revision": "v1"})
    values.update(changes)
    return DatasetRecord(**values)


def test_adapter_record_preserves_provenance_and_freezes_input():
    source = {"kind": "email", "subject": "Hello"}
    result = record(artifact_input=source, source_metadata={"columns": ["subject"]})
    source["subject"] = "changed"
    prepared = prepare_record(result)
    assert prepared.artifact.model_text == "hello"
    assert prepared.record.source_dataset == "unit-fixture"
    assert prepared.record.source_record_id == "1"
    assert prepared.record.provenance["revision"] == "v1"
    assert prepared.record.source_metadata["columns"] == ("subject",)
    with pytest.raises(TypeError):
        result.artifact_input["subject"] = "changed"


def test_phishing_and_behavioral_labels_cannot_be_interchanged():
    label = SourcePhishingLabel(PhishingLabel.PHISHING, "fixture-source-label")
    item = record(phishing_label=label)
    assert item.phishing_label == label and not hasattr(item, "behavioral_ground_truth")
    for wrong in (label, PhishingLabel.PHISHING, "phishing", True):
        with pytest.raises(ValueError):
            BehavioralAnnotation("urgency", wrong, "fixture-evidence")
    with pytest.raises(ValueError):
        SourcePhishingLabel(BehavioralLabel.SUPPORTED, "fixture-source")
    with pytest.raises(ValueError):
        record(phishing_label="phishing")
    annotation = BehavioralAnnotation("urgency", BehavioralLabel.UNAVAILABLE, "fixture-protocol")
    truth = BehavioralGroundTruth(item.record_id, "0.1.0", "fixture-protocol", (annotation,))
    assert len(truth.annotations) == 1  # other indicators remain unannotated
    with pytest.raises(ValueError):
        replace(truth, annotations=(replace(annotation, indicator_id="phishing"),))


@pytest.mark.parametrize("changes", [
    {"modality": "standalone_url"}, {"fields_available": ()}, {"content_available": 1},
    {"provenance": {}}, {"provenance": {"bad": float("nan")}},
    {"source_metadata": {"bad": object()}}, {"record_id": ""},
])
def test_invalid_dataset_metadata(changes):
    with pytest.raises(ValueError):
        record(**changes)


def test_malformed_artifact_and_false_availability_rejected_at_preparation():
    with pytest.raises(ValueError):
        prepare_record(record(artifact_input={"kind": "email", "subject": 12}))
    with pytest.raises(ValueError, match="availability"):
        prepare_record(record(content_available=False))
    assert prepare_record(record(content_available=None)).artifact.required_content_available


def test_known_groups_cannot_cross_partitions():
    split = SplitManifest("fixture", ("a",), ("b",), ("c",))
    group = GroupIdentifier(GroupKind.DUPLICATE_CLUSTER, "fixture-audit", "duplicate-1")
    with pytest.raises(ValueError, match="crosses"):
        GroupAwareManifest(split, {"a": (group,), "b": (group,), "c": ()})
    with pytest.raises(ValueError, match="contradictory"):
        record(groups=(group, replace(group, value="different")))
    with pytest.raises(ValueError):
        GroupAwareManifest(split, {"a": (), "b": ()})


def test_unknown_groups_remain_explicit_and_namespaces_do_not_collide():
    split = SplitManifest("fixture", ("a",), (), ("b",))
    group = GroupIdentifier(GroupKind.EMAIL_THREAD, "source-a", "1")
    manifest = GroupAwareManifest(split, {"a": (group,), "b": ()}, (GroupKind.EMAIL_THREAD,))
    assert manifest.missing_group_metadata == (("b", GroupKind.EMAIL_THREAD),)
    with pytest.raises(ValueError, match="incomplete"):
        manifest.require_complete()
    complete = GroupAwareManifest(split, {"a": (group,), "b": (replace(group, namespace="source-b"),)}, (GroupKind.EMAIL_THREAD,))
    complete.require_complete()
    with pytest.raises(TypeError):
        complete.groups_by_record["a"] = ()
