import pytest

from ml import annotation_validation as validation
from ml.research_policy import ResearchPolicyError


def judgment():
    return {"record_id": "fixture:1", "annotator_id": "human-a", "role": "independent_human",
            "qualifications": "fixture only", "review_date": "2026-11-13", "protocol_version": "fixture-v1",
            "codebook_version": "0.1.0", "modality": "content_bearing_email", "independent": True, "model_output_visible": False,
            "indicators": {"urgency": "supported"},
            "evidence": {"urgency": [{"field": "subject", "start": 0, "end": 6, "text": "Urgent"}]}}


def test_partial_labels_remain_missing_and_supported_requires_exact_evidence():
    item = judgment()
    validation.validate_judgment(item, {"subject": "Urgent"})
    assert validation.coverage([item])["indicators"]["scarcity"]["missing"] == 1
    item["evidence"]["urgency"][0]["start"] = True
    with pytest.raises(ValueError, match="span"):
        validation.validate_judgment(item, {"subject": "Urgent"})


@pytest.mark.parametrize("change", [{"role": "vera"}, {"independent": False}, {"model_output_visible": True}, {"qualifications": ""}, {"codebook_version": "other"}])
def test_ai_or_self_review_cannot_be_independent_reference(change):
    item = {**judgment(), **change}
    with pytest.raises(ValueError):
        validation.validate_judgment(item, {"subject": "Urgent"})


def test_agreement_missing_and_abstention_are_not_negative_labels():
    left = [{"record_id": str(i), "indicators": {"urgency": value}} for i, value in enumerate(["supported", "absent", None, "unavailable"])]
    right = [{"record_id": str(i), "indicators": {"urgency": value}} for i, value in enumerate(["supported", "absent", "abstained", "unavailable"])]
    report = validation.pairwise_agreement(left, right)["indicators"]["urgency"]
    assert report["comparable"] == 3 and report["excluded_missing_or_abstained"] == 1
    assert report["cohens_kappa"] == 1
    assert validation.pairwise_agreement([], [])["indicators"]["urgency"]["cohens_kappa"] is None
    with pytest.raises(ValueError, match="Duplicate"):
        validation.pairwise_agreement([left[0], left[0]], right)


def test_packet_requires_approved_source_and_never_copies_labels(monkeypatch):
    source = {"record_id": "fixture:1", "group_id": "fixture:g", "source_dataset": "fixture", "partition": "development",
              "modality": "content_bearing_email", "fields": {"subject": "Urgent"}, "target": 1,
              "indicators": {"urgency": "supported"}, "AI_rationale": "PRIVATE", "provenance": {"source": "fixture"}}
    with pytest.raises(ResearchPolicyError):
        validation.blinded_packet([source])
    monkeypatch.setattr(validation, "load_policy", lambda: {"approved_annotation_sources": ["fixture"]})
    packet = validation.blinded_packet([source])
    assert packet["judgments_generated"] == 0
    assert set(packet["items"][0]["indicators"].values()) == {None}
    assert "PRIVATE" not in str(packet) and "target" not in packet["items"][0]
    assert packet["items"][0]["record_id"] == "annotation_000001"
    assert "fixture:1" not in str(packet["items"])
    assert packet["researcher_only_custody_manifest"][0]["source_record_id"] == "fixture:1"
    source["partition"] = "test"
    with pytest.raises(ResearchPolicyError):
        validation.blinded_packet([source])
    source["source_dataset"] = "Spa Phish"
    with pytest.raises(ResearchPolicyError):
        validation.blinded_packet([source])


def test_adjudication_requires_separate_human_and_real_reference_ids():
    item = {"record_id": "fixture:1", "indicator_id": "urgency", "adjudicator_id": "human-c", "review_date": "2026-11-13",
            "reason": "fixture", "reference_annotator_ids": ["human-a", "human-b"], "value": "supported",
            "role": "independent_human", "adjudicator_qualifications": "fixture only", "protocol_version": "fixture-v1",
            "independent": True, "model_output_visible": False,
            "evidence": [{"field": "subject", "start": 0, "end": 6, "text": "Urgent"}]}
    refs = [judgment(), {**judgment(), "annotator_id": "human-b"}]
    validation.validate_adjudication(item, refs, {"subject": "Urgent"})
    item["adjudicator_id"] = "human-a"
    with pytest.raises(ValueError):
        validation.validate_adjudication(item, refs, {"subject": "Urgent"})
    assert not any(validation.acceptance_gate().values())


def test_bare_url_cannot_supply_content_labels_and_identity_needs_references():
    item = {**judgment(), "modality": "standalone_url"}
    with pytest.raises(ValueError, match="modality"):
        validation.validate_judgment(item, {"subject": "Urgent"})
    item = judgment()
    item["indicators"] = {"impersonation": "supported"}
    item["evidence"] = {"impersonation": [{"field": "subject", "start": 0, "end": 6, "text": "Urgent"}]}
    with pytest.raises(ValueError, match="Identity"):
        validation.validate_judgment(item, {"subject": "Urgent", "sender": "sender@example.test"})


@pytest.mark.parametrize("bad", [False, 0, "", "phishing", [], {}])
def test_descriptive_reports_reject_invalid_labels_instead_of_silently_losing_them(bad):
    row = {"record_id": "fixture:1", "indicators": {"urgency": bad}}
    with pytest.raises(ValueError, match="Malformed"):
        validation.coverage([row])
    with pytest.raises(ValueError, match="Malformed"):
        validation.pairwise_agreement([row], [row])


def test_full_synthetic_blinded_human_response_and_adjudication_workflow(monkeypatch):
    from copy import deepcopy
    monkeypatch.setattr(validation, "load_policy", lambda: {"approved_annotation_sources": ["fixture"]})
    source = {"record_id": "fixture:source", "group_id": "fixture:g", "source_dataset": "fixture",
              "partition": "development", "modality": "content_bearing_email", "fields": {"subject": "Urgent"},
              "provenance": {"source": "synthetic-only"}, "target": 1, "AI_rationale": "must be removed"}
    packet = validation.blinded_packet([source])
    assert list(packet["items"][0]["indicators"]) == list(validation.indicator_ids())
    blinded = packet["items"][0]
    a = {**judgment(), "record_id": blinded["record_id"], "text_hash": blinded["text_hash"]}
    b = {**a, "annotator_id": "human-b", "indicators": {"urgency": "absent"}, "evidence": {}}
    validation.validate_packet_response(blinded, a)
    validation.validate_packet_response(blinded, b)
    assert validation.coverage([a, b])["indicators"]["scarcity"]["missing"] == 2
    assert validation.pairwise_agreement([a], [b])["indicators"]["urgency"]["observed_agreement"] == 0
    decision = {"record_id": a["record_id"], "indicator_id": "urgency", "adjudicator_id": "human-c",
                "review_date": "2026-11-13", "reason": "synthetic software fixture", "reference_annotator_ids": ["human-a", "human-b"],
                "value": "supported", "evidence": a["evidence"]["urgency"], "role": "independent_human",
                "adjudicator_qualifications": "fixture only", "protocol_version": "fixture-v1", "independent": True, "model_output_visible": False}
    validation.validate_adjudication(decision, [a, b], blinded["fields"])
    assert a["indicators"]["urgency"] == "supported" and b["indicators"]["urgency"] == "absent"
    changed = deepcopy(blinded)
    changed["fields"]["subject"] = "Changed original"
    with pytest.raises(ValueError, match="unchanged"):
        validation.validate_packet_response(changed, a)
    with pytest.raises(ValueError, match="belong"):
        validation.validate_packet_response(blinded, {**a, "record_id": "other"})
    assert not any(validation.acceptance_gate().values())


@pytest.mark.parametrize("left,right,expected", [
    (["supported", "supported", "absent", "absent"], ["supported", "absent", "supported", "absent"], 0),
    (["supported", "absent"], ["absent", "supported"], -1),
    (["absent"], ["absent"], None),
])
def test_agreement_arithmetic_including_degenerate_and_negative_kappa(left, right, expected):
    def rows(labels):
        return [{"record_id": str(index), "indicators": {"urgency": value}} for index, value in enumerate(labels)]
    assert validation.pairwise_agreement(rows(left), rows(right))["indicators"]["urgency"]["cohens_kappa"] == expected


def test_agreement_rejects_same_id_with_different_artifact_hash_or_modality():
    left = {**judgment(), "text_hash": "a" * 64}
    with pytest.raises(ValueError, match="incompatible"):
        validation.pairwise_agreement([left], [{**left, "text_hash": "b" * 64}])


def test_orphan_evidence_and_missing_content_are_not_valid_judgments():
    item = {**judgment(), "indicators": {}}
    with pytest.raises(ValueError, match="Missing/unavailable"):
        validation.validate_judgment(item, {"subject": "Urgent"})
    item = {**judgment(), "indicators": {"urgency": "absent"}, "evidence": {}}
    with pytest.raises(ValueError, match="opportunity"):
        validation.validate_judgment(item, {"subject": ""})


@pytest.mark.parametrize("indicator", ["impersonation", "brand_exploitation"])
def test_identity_absence_also_requires_independent_references(indicator):
    item = {**judgment(), "indicators": {indicator: "absent"}, "evidence": {}}
    with pytest.raises(ValueError, match="Identity"):
        validation.validate_judgment(item, {"subject": "Urgent", "sender": "sender@example.test"})


def test_adjudication_rejects_unjudged_and_unblinded_references():
    item = {"record_id": "fixture:1", "indicator_id": "scarcity", "adjudicator_id": "human-c", "review_date": "2026-11-13",
            "reason": "fixture", "reference_annotator_ids": ["human-a", "human-b"], "value": "absent"}
    refs = [judgment(), {**judgment(), "annotator_id": "human-b"}]
    with pytest.raises(ValueError, match="unjudged"):
        validation.validate_adjudication(item, refs, {"subject": "Urgent"})
    item["indicator_id"] = "urgency"
    refs[1]["model_output_visible"] = True
    with pytest.raises(ValueError, match="blinded"):
        validation.validate_adjudication(item, refs, {"subject": "Urgent"})


def test_coverage_duplicate_responses_and_missing_source_custody_are_rejected(monkeypatch):
    with pytest.raises(ValueError, match="unique"):
        validation.coverage([judgment(), judgment()])
    monkeypatch.setattr(validation, "load_policy", lambda: {"approved_annotation_sources": ["fixture"]})
    with pytest.raises(ValueError, match="provenance"):
        validation.blinded_packet([{"record_id": "fixture", "source_dataset": "fixture", "partition": "development"}])
