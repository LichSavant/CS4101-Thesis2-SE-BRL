from dataclasses import replace

import pytest

from ml.datasets import PhishingLabel
from ml.experiment_inputs import (
    Availability, DatasetIdentity, DocumentedLabelMapping, EmailFieldMapping, EmailObservation, InputContractError,
    LinkField, PartitionAssignment, MappedEmailAdapter, TextField, gate_english_lexical,
    select_predictors, validate_population, validate_supplied_partitions,
)


def identity(snapshot="synthetic-v1"):
    return DatasetIdentity("SyntheticEmail", snapshot, "synthetic-source-description")


def labels():
    # Synthetic mapping, not a verification of any research corpus's labels.
    return DocumentedLabelMapping(((0, PhishingLabel.LEGITIMATE), (1, PhishingLabel.PHISHING)), "synthetic-label-spec")


def adapter(language="es", columns=EmailFieldMapping("record_id", "native_label", "subject", "body")):
    return MappedEmailAdapter(identity(), labels(), language=language, columns=EmailFieldMapping("record_id", "native_label", "subject", "body", sender="sender", receiver="receiver", links="urls"))


def row(**changes):
    return {"record_id": "synthetic-original-1", "subject": "Synthetic subject", "body": "Synthetic text", "native_label": 1, **changes}


def test_mapped_adapter_requires_documented_identity_and_mapping_and_preserves_original():
    result = adapter().adapt(row())
    assert result.original_record_id == "synthetic-original-1"
    assert result.dataset == identity()
    assert result.language == "es"
    assert result.source_label == 1 and result.target is PhishingLabel.PHISHING
    assert result.label_reference == "synthetic-label-spec"
    assert result.contract_version == adapter().contract_version
    assert result.observation_id != adapter().adapt(row(record_id="other-original")).observation_id
    with pytest.raises(InputContractError, match="identity"):
        MappedEmailAdapter(None, labels(), language="es", columns=EmailFieldMapping("record_id", "native_label", "subject", "body"))
    with pytest.raises(InputContractError, match="mapping"):
        MappedEmailAdapter(identity(), None, language="es", columns=EmailFieldMapping("record_id", "native_label", "subject", "body"))


def test_observation_identity_is_stable_and_tuple_encoding_is_unambiguous():
    a = MappedEmailAdapter(identity("a:b"), labels(), language="es", columns=EmailFieldMapping("record_id", "native_label", "subject", "body")).adapt(row(record_id="c"))
    b = MappedEmailAdapter(identity("a"), labels(), language="es", columns=EmailFieldMapping("record_id", "native_label", "subject", "body")).adapt(row(record_id="b:c"))
    assert a.observation_id != b.observation_id
    assert adapter().adapt(row()).observation_id == adapter().adapt(row()).observation_id


@pytest.mark.parametrize("entries,reference", [
    (((0, PhishingLabel.LEGITIMATE), (1, PhishingLabel.PHISHING)), ""),
    (((0, PhishingLabel.LEGITIMATE), (0, PhishingLabel.PHISHING)), "fixture"),
    (((False, PhishingLabel.LEGITIMATE), (1, PhishingLabel.PHISHING)), "fixture"),
    (((0, PhishingLabel.PHISHING), (1, PhishingLabel.PHISHING)), "fixture"),
    (((0, "legitimate"), (1, "phishing")), "fixture"),
])
def test_label_mapping_rejects_undocumented_or_contradictory_entries(entries, reference):
    with pytest.raises(InputContractError):
        DocumentedLabelMapping(entries, reference)


@pytest.mark.parametrize("native", [None, True, "1", 1.0, 2])
def test_labels_are_not_coerced_or_guessed(native):
    with pytest.raises(InputContractError, match="unmapped"):
        adapter().adapt(row(native_label=native))


def test_optional_evidence_is_unavailable_rather_than_synthetic_negative():
    missing = adapter().adapt(row())
    assert missing.sender.value is None and missing.links.value is None
    assert missing.sender.availability is Availability.UNAVAILABLE
    assert missing.links.availability is Availability.UNAVAILABLE
    empty = adapter().adapt(row(sender="", receiver=None, urls=()))
    assert empty.sender.availability is Availability.KNOWN_EMPTY
    assert empty.links.availability is Availability.KNOWN_EMPTY
    assert empty.receiver.availability is Availability.UNAVAILABLE
    assert TextField("  ").value == "  "  # Original evidence not normalized away.
    assert LinkField(("https://synthetic.example.test/",)).availability is Availability.AVAILABLE
    with pytest.raises(InputContractError, match="link"):
        adapter().adapt(row(urls="[]"))


@pytest.mark.parametrize("record_id", [None, "", "  ", float("nan"), 7])
def test_missing_or_invalid_original_identifiers_are_rejected(record_id):
    with pytest.raises(InputContractError, match="identifier"):
        adapter().adapt(row(record_id=record_id))


def test_missing_fields_and_missing_observation_id_are_rejected():
    with pytest.raises(InputContractError, match="required_fields"):
        adapter().adapt({"record_id": "id"})
    original = adapter().adapt(row())
    with pytest.raises(InputContractError, match="identifier"):
        replace(original, observation_id="")


def test_population_identity_duplicate_ids_and_count_boundaries():
    first = adapter().adapt(row())
    second = adapter().adapt(row(record_id="synthetic-original-2", native_label=0))
    assert validate_population([first, second], identity=identity(), expected_total=2,
                              expected_targets={PhishingLabel.PHISHING: 1, PhishingLabel.LEGITIMATE: 1}) == {
        "total": 2, "phishing": 1, "legitimate": 1,
    }
    with pytest.raises(InputContractError, match="duplicate"):
        validate_population([first, replace(second, observation_id=first.observation_id)], identity=identity())
    with pytest.raises(InputContractError, match="duplicate"):
        validate_population([first, replace(second, original_record_id=first.original_record_id)], identity=identity())
    with pytest.raises(InputContractError, match="mixed_dataset"):
        validate_population([replace(first, dataset=identity("different"))], identity=identity())
    with pytest.raises(InputContractError, match="contradictory_expected_counts"):
        validate_population([], identity=identity(), expected_total=9,
                            expected_targets={PhishingLabel.PHISHING: 1, PhishingLabel.LEGITIMATE: 1})
    with pytest.raises(InputContractError, match="population_count_mismatch"):
        validate_population([first, second], identity=identity(), expected_total=38759)
    with pytest.raises(InputContractError, match="target_count_mismatch"):
        validate_population([first, second], identity=identity(),
                            expected_targets={PhishingLabel.PHISHING: 2, PhishingLabel.LEGITIMATE: 0})


@pytest.mark.parametrize("language,reason", [("es", "unsupported_english_lexical_language"),
                                            ("es-es", "unsupported_english_lexical_language"), ("und", "unknown_language")])
def test_unsupported_language_does_not_call_extractor_or_become_absent(language, reason):
    def forbidden_extract(_):
        pytest.fail("Unsupported content must not reach the English extractor")
    result = gate_english_lexical(adapter(language).adapt(row()), forbidden_extract)
    assert result.status == "unavailable" and result.reason == reason and result.result is None


def test_explicit_english_can_reach_supplied_evaluator():
    observation = adapter("en-us").adapt(row())
    result = gate_english_lexical(observation, lambda value: ("synthetic-evaluation", value.observation_id))
    assert result.status == "evaluated" and result.reason is None
    assert result.result == ("synthetic-evaluation", observation.observation_id)


@pytest.mark.parametrize("field", ["target", "Label", "Result", "hash", "original_hash", "observation_id",
                                   "group_id", "partition", "cv_fold", "source_dataset", "snapshot_id",
                                   "language", "provenance_reference", "dataset", "source", "source_custom", "custom_native_label"])
def test_bookkeeping_and_native_labels_cannot_be_predictors(field):
    with pytest.raises(InputContractError, match="bookkeeping"):
        select_predictors({field: 1}, (field,), extra_bookkeeping=("custom_native_label",))


def test_explicit_predictor_allowlist_never_passes_extra_metadata():
    selected = select_predictors({"length": 5, "target": 1, "source_dataset": "fixture"}, ("length",))
    assert dict(selected) == {"length": 5}
    with pytest.raises(TypeError):
        selected["target"] = 1


def test_supplied_partitions_only_validate_isolation_without_assigning_or_mutating():
    supplied = (PartitionAssignment("a", "g1", "development", 1),
                PartitionAssignment("b", "g1", "development", 1),
                PartitionAssignment("c", "g2", "calibration"), PartitionAssignment("d", "g3", "test"))
    assert validate_supplied_partitions(supplied) == {"development": 2, "calibration": 1, "test": 1}
    assert supplied[0].cv_fold == 1
    with pytest.raises(InputContractError, match="crosses_partitions"):
        validate_supplied_partitions([supplied[0], PartitionAssignment("e", "g1", "test")])
    with pytest.raises(InputContractError, match="crosses_folds"):
        validate_supplied_partitions([supplied[0], PartitionAssignment("e", "g1", "development", 2)])
    with pytest.raises(InputContractError, match="duplicate_partition"):
        validate_supplied_partitions([supplied[0], supplied[0]])
    with pytest.raises(InputContractError, match="nondevelopment"):
        validate_supplied_partitions([PartitionAssignment("e", "g4", "test", 1)])
    with pytest.raises(InputContractError, match="identifier"):
        validate_supplied_partitions([PartitionAssignment("", "g4", "test")])


def test_explicit_field_mapping_accepts_different_source_schemas_without_defaults():
    columns = EmailFieldMapping("message_key", "verdict", "heading", "content")
    mapped = MappedEmailAdapter(DatasetIdentity("OtherFixture", "v1", "fixture-provenance"),
        labels(), language="en", columns=columns)
    result = mapped.adapt({"message_key": "id-1", "verdict": 0, "heading": "Hello", "content": "Fixture",
                          "urls": ("https://ignored.example.test",), "sender": "ignored"})
    assert result.original_record_id == "id-1" and result.subject.value == "Hello"
    assert result.target is PhishingLabel.LEGITIMATE
    assert result.sender.availability is Availability.UNAVAILABLE
    assert result.links.availability is Availability.UNAVAILABLE
    with pytest.raises(InputContractError, match="missing_required_fields"):
        mapped.adapt(row())


def test_source_field_mapping_requires_unique_explicit_columns():
    with pytest.raises(InputContractError, match="duplicate_source_column_mapping"):
        EmailFieldMapping("id", "label", "text", "text")
    with pytest.raises(InputContractError, match="duplicate_source_column_mapping"):
        EmailFieldMapping("id", "label", "subject", "body", sender="body")
    with pytest.raises(InputContractError, match="identifier"):
        EmailFieldMapping("", "label", "subject", "body")
    with pytest.raises(InputContractError, match="explicit_source_columns_required"):
        MappedEmailAdapter(identity(), labels(), language="en", columns=None)
