"""Synthetic integration only; no corpus, classifier, or calibration fitting."""
from dataclasses import fields, replace

import pytest

from ml.datasets import PhishingLabel
from ml.experiment_inputs import (
    Availability, DatasetIdentity, DocumentedLabelMapping, EmailFieldMapping, InputContractError,
    PartitionAssignment, MappedEmailAdapter, TextField, validate_population,
)
from ml.experiment_integration import EmailEvidenceInput, evaluate_development_lexical
from ml.preprocessing import preprocess
from ml.se_brl.extraction import RuleEngine


def fixture_batch(language="en"):
    identity = DatasetIdentity("SyntheticEmail", "synthetic-only-v1", "synthetic-provenance")
    mapping = DocumentedLabelMapping(((0, PhishingLabel.LEGITIMATE), (1, PhishingLabel.PHISHING)),
                                     "synthetic-label-mapping")
    adapter = MappedEmailAdapter(identity, mapping, language=language, columns=EmailFieldMapping("record_id", "native_label", "subject", "body", sender="sender", receiver="receiver", links="urls"))
    texts = (
        ("A: Act now!", "First record: Submit your password immediately."),
        ("Record number two: Your access will be locked.",
         "Second record with a longer prefix: Enter your verification code."),
        ("Calibration notice: Claim your prize.", "Calibration record only: Transfer your money."),
        ("Reserved test notice: Click here.", "Reserved test record only: Pay this fee."),
    )
    observations = tuple(adapter.adapt({"record_id": f"fixture-{i}", "subject": subject,
        "body": body, "native_label": i % 2}) for i, (subject, body) in enumerate(texts))
    assignments = tuple(PartitionAssignment(o.observation_id, f"group-{i}", partition,
        i + 1 if partition == "development" else None)
        for i, (o, partition) in enumerate(zip(observations,
            ("development", "development", "calibration", "test"))))
    return observations, assignments, dict(identity=identity, expected_total=4,
        expected_targets={PhishingLabel.LEGITIMATE: 2, PhishingLabel.PHISHING: 2})


@pytest.mark.parametrize("assignment_order", [(3, 2, 1, 0), (2, 0, 3, 1)])
@pytest.mark.parametrize("reverse_observations", [False, True])
def test_adapter_to_existing_rule_engine_preserves_original_evidence_spans(
        assignment_order, reverse_observations):
    observations, assignments, options = fixture_batch()
    by_id = {o.observation_id: o for o in observations}
    development_ids = {a.observation_id for a in assignments if a.partition == "development"}
    anchors = {
        observations[0].observation_id: (("subject", "Act now"), ("body", "Submit your password")),
        observations[1].observation_id: (("subject", "Your access will be locked"),
                                         ("body", "Enter your verification code")),
    }
    assignments = tuple(assignments[i] for i in assignment_order)
    if reverse_observations:
        observations = tuple(reversed(observations))
    calls = []
    def evaluate(view):
        calls.append(view)
        assert {f.name for f in fields(view)} == {"subject", "body", "sender", "links"}
        for metadata in ("target", "source_label", "label_reference", "partition", "cv_fold",
                         "group_id", "dataset", "observation_id", "original_record_id", "language"):
            assert not hasattr(view, metadata)
        assert view.links.availability is Availability.UNAVAILABLE
        artifact = preprocess({"kind": "email", "subject": view.subject.value,
            "body": view.body.value, "body_collection_authorized": True,
            "study_purpose": "Synthetic integration fixture only"})
        return RuleEngine().extract(artifact)
    result = evaluate_development_lexical(observations, assignments, evaluate=evaluate, **options)
    assert len(calls) == len(result) == 2
    assert [r.observation_id for r in result] == [o.observation_id for o in observations
                                                if o.observation_id in development_ids]
    assert {view.subject.value for view in calls} == {by_id[i].subject.value for i in development_ids}
    assert {view.body.value for view in calls} == {by_id[i].body.value for i in development_ids}
    for row, view in zip(result, calls):
        observation = by_id[row.observation_id]
        assert view.subject is observation.subject and view.body is observation.body
        assert row.evaluation.status == "evaluated"
        evidence = [e for i in row.evaluation.result.indicators for e in i.evidence]
        assert evidence
        assert {item.span.field for item in evidence} == {"subject", "body"}
        for item in evidence:
            original = getattr(observation, item.span.field).value
            assert 0 <= item.span.start < item.span.end <= len(original)
            assert original[item.span.start:item.span.end] == item.span.text
            # Every fixture has different text and offsets: reusing another
            # record's extraction must fail even if IDs are returned correctly.
            for other in observations:
                if other.observation_id != row.observation_id:
                    assert getattr(other, item.span.field).value[item.span.start:item.span.end] != item.span.text
            assert item.provenance == "rule-based"
        spans = {(item.span.field, item.span.start, item.span.end, item.span.text) for item in evidence}
        for source_field, phrase in anchors[row.observation_id]:
            start = getattr(observation, source_field).value.index(phrase)
            assert (source_field, start, start + len(phrase), phrase) in spans


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate", "cross_partition", "cross_fold",
                                      "wrong_total", "wrong_target", "mixed_snapshot", "empty",
                                      "mismatched_identifier"])
def test_invalid_batch_never_calls_evaluator(mutation):
    observations, assignments, options = fixture_batch()
    if mutation == "missing": assignments = assignments[:-1]
    elif mutation == "extra": assignments += (PartitionAssignment("foreign-id", "extra", "test"),)
    elif mutation == "duplicate": assignments += (assignments[0],)
    elif mutation == "mismatched_identifier":
        assignments = (*assignments[:-1], replace(assignments[-1], observation_id="foreign-id"))
    elif mutation == "cross_partition":
        assignments = (*assignments[:3], replace(assignments[3], group_id=assignments[0].group_id))
    elif mutation == "cross_fold":
        assignments = (assignments[0], replace(assignments[1], group_id=assignments[0].group_id), *assignments[2:])
    elif mutation == "wrong_total": options["expected_total"] = 38759
    elif mutation == "wrong_target":
        options["expected_targets"] = {PhishingLabel.LEGITIMATE: 3, PhishingLabel.PHISHING: 1}
    elif mutation == "mixed_snapshot":
        observations = (replace(observations[0], dataset=replace(options["identity"], snapshot_id="other")), *observations[1:])
    elif mutation == "empty":
        observations, assignments = (), ()
        options.update(expected_total=0, expected_targets={label: 0 for label in PhishingLabel})
    with pytest.raises(InputContractError):
        evaluate_development_lexical(observations, assignments,
            evaluate=lambda _: pytest.fail("Invalid batch reached evaluator"), **options)


@pytest.mark.parametrize("expected_total", [None, True, False, -1, 4.0, "4"])
def test_invalid_total_expectation_never_calls_evaluator(expected_total):
    observations, assignments, options = fixture_batch()
    options["expected_total"] = expected_total
    with pytest.raises(InputContractError, match="^invalid_population_expectation$"):
        evaluate_development_lexical(observations, assignments,
            evaluate=lambda _: pytest.fail("Invalid total reached evaluator"), **options)


@pytest.mark.parametrize("expected_targets,reason", [
    (None, "explicit_target_counts_required"),
    (True, "explicit_target_counts_required"),
    ("phishing", "explicit_target_counts_required"),
    ([(PhishingLabel.LEGITIMATE, 2), (PhishingLabel.PHISHING, 2)], "explicit_target_counts_required"),
    ({}, "explicit_target_counts_required"),
    ({PhishingLabel.PHISHING: 4}, "explicit_target_counts_required"),
    ({"other": 2, PhishingLabel.PHISHING: 2}, "explicit_target_counts_required"),
    ({PhishingLabel.LEGITIMATE: True, PhishingLabel.PHISHING: 3}, "explicit_target_counts_required"),
    ({PhishingLabel.LEGITIMATE: -1, PhishingLabel.PHISHING: 5}, "explicit_target_counts_required"),
    ({PhishingLabel.LEGITIMATE: 2.0, PhishingLabel.PHISHING: 2}, "explicit_target_counts_required"),
    ({PhishingLabel.LEGITIMATE: "2", PhishingLabel.PHISHING: 2}, "explicit_target_counts_required"),
    ({PhishingLabel.LEGITIMATE: None, PhishingLabel.PHISHING: 2}, "explicit_target_counts_required"),
    ({PhishingLabel.LEGITIMATE: 2, PhishingLabel.PHISHING: 1}, "contradictory_expected_counts"),
])
def test_invalid_target_expectation_never_calls_evaluator(expected_targets, reason):
    observations, assignments, options = fixture_batch()
    options["expected_targets"] = expected_targets
    with pytest.raises(InputContractError, match=f"^{reason}$"):
        evaluate_development_lexical(observations, assignments,
            evaluate=lambda _: pytest.fail("Invalid target counts reached evaluator"), **options)


def test_standalone_population_validation_keeps_optional_expectations():
    observations, _, options = fixture_batch()
    expected = {"total": 4, "legitimate": 2, "phishing": 2}
    assert validate_population(observations, identity=options["identity"]) == expected
    assert validate_population(observations, identity=options["identity"],
        expected_total=None, expected_targets=None) == expected


@pytest.mark.parametrize("language,reason", [("es", "unsupported_english_lexical_language"),
    ("und", "unknown_language")])
def test_language_gate_is_enforced_at_integration_boundary(language, reason):
    observations, assignments, options = fixture_batch(language)
    result = evaluate_development_lexical(observations, assignments,
        evaluate=lambda _: pytest.fail("Unsupported language reached evaluator"), **options)
    assert len(result) == 2
    assert all(r.evaluation.status == "unavailable" and r.evaluation.reason == reason
               and r.evaluation.result is None for r in result)


@pytest.mark.parametrize("subject,body", [(" ", None), (None, None), (None, ""), ("", " ")])
def test_known_empty_and_missing_text_are_preserved_without_absence_claims(subject, body):
    observations, assignments, options = fixture_batch()
    subject_field, body_field = TextField(subject), TextField(body)
    observations = tuple(replace(o, subject=subject_field, body=body_field) for o in observations)
    result = evaluate_development_lexical(observations, assignments,
        evaluate=lambda _: pytest.fail("No text reached evaluator"), **options)
    assert len(result) == 2
    assert all(r.evaluation.status == "unavailable" and r.evaluation.reason == "missing_text_evidence"
               and r.evaluation.result is None for r in result)
    assert observations[0].subject is subject_field and observations[0].body is body_field
    for value, wrapped in ((subject, subject_field), (body, body_field)):
        assert wrapped.availability is (Availability.UNAVAILABLE if value is None else Availability.KNOWN_EMPTY)


def test_no_development_records_means_no_evaluation():
    observations, assignments, options = fixture_batch()
    assignments = tuple(replace(a, partition="test", cv_fold=None) for a in assignments)
    assert evaluate_development_lexical(observations, assignments,
        evaluate=lambda _: pytest.fail("Reserved records reached evaluator"), **options) == ()


def test_evaluator_failures_are_sanitized_and_no_partial_results_are_returned():
    observations, assignments, options = fixture_batch()
    def failing(_):
        raise ValueError("SENSITIVE FIXTURE CONTENT")
    with pytest.raises(InputContractError, match="^lexical_evaluator_failed$") as error:
        evaluate_development_lexical(observations, assignments, evaluate=failing, **options)
    assert error.value.__suppress_context__
    assert "SENSITIVE" not in str(error.value)


@pytest.mark.parametrize("callback_result", [None, object(), {"arbitrary": "opaque result"}])
def test_callback_result_is_passed_through_without_evidence_schema_validation(callback_result):
    observations, assignments, options = fixture_batch()
    result = evaluate_development_lexical(observations, assignments,
        evaluate=lambda _: callback_result, **options)
    assert len(result) == 2
    assert all(r.evaluation.status == "evaluated" and r.evaluation.reason is None
               and r.evaluation.result is callback_result for r in result)


def test_evidence_view_repr_does_not_print_content_and_is_immutable():
    view = EmailEvidenceInput(TextField("sensitive subject"), TextField("sensitive body"), TextField(),
                              fixture_batch()[0][0].links)
    assert "sensitive" not in repr(view)
    with pytest.raises(AttributeError):
        view.body = TextField("changed")
