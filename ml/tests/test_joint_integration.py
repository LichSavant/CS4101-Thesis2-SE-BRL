"""Actual pinned counterpart + Vera runtime; synthetic inputs, no acceptance claim."""
from copy import deepcopy
from dataclasses import replace
import os
from pathlib import Path

import pytest

from ml.counterpart_checkout import load_counterpart
from ml.se_brl.joint_integration import (
    EvidenceAuthorization, JointIntegrationError, evidence_fingerprint,
    integrate_email_batch, joint_preprocess,
)
from ml.se_brl.review_adapter import analyze_evidence
from ml.se_brl.representation_contract import contract


@pytest.fixture(scope="module")
def peer():
    source = os.environ.get("SEBRL_R22_COUNTERPART_ROOT")
    if not source:
        pytest.fail("Actual selected counterpart checkout required; no synthetic substitute or silent skip")
    manifest = Path(__file__).resolve().parents[2] / "docs/r22-parser-repair-2026-11-16/counterpart-source-manifest.json"
    return load_counterpart(Path(source), manifest)


def batch(peer):
    p = peer.inputs
    identity = p.DatasetIdentity("SyntheticR22", "software-only-v1", "synthetic-engineering")
    texts = (("🙂 A: Act now!", "First: Submit your password."),
             ("B: Your access will be locked.", "Second: Enter your verification code."),
             ("Unsupported", None), ("Reserved calibration", "DO_NOT_ANALYZE_CLOSED_CALIBRATION"),
             ("Reserved test", "DO_NOT_ANALYZE_CLOSED_TEST"))
    rows = tuple(p.EmailObservation(f"r22:{i}", f"original:{i}", identity, "es" if i == 2 else "en", i % 2,
                 p.PhishingLabel.LEGITIMATE if i % 2 == 0 else p.PhishingLabel.PHISHING, "synthetic-label-map",
                 p.TextField(subject), p.TextField(body)) for i, (subject, body) in enumerate(texts))
    assignments = tuple(p.PartitionAssignment(row.observation_id, f"group:{i}", partition, i + 1 if i < 3 else None)
                        for i, (row, partition) in enumerate(zip(rows, ("development", "development", "development", "calibration", "test"))))
    grants = {r.observation_id: EvidenceAuthorization(evidence_fingerprint(r), True, False, "synthetic engineering acceptance") for r in rows[:2]}
    options = dict(identity=identity, expected_total=5, expected_targets={p.PhishingLabel.LEGITIMATE: 3, p.PhishingLabel.PHISHING: 2}, engineering_only=True)
    return rows, assignments, grants, options


def execute(peer, data=None, **extra):
    rows, assignments, grants, options = batch(peer) if data is None else data
    return integrate_email_batch(peer, rows, assignments, grants, **{**options, **extra})


@pytest.mark.parametrize("order", [(4, 3, 2, 1, 0), (2, 4, 0, 3, 1), (1, 0, 4, 2, 3)])
def test_reordered_actual_join_binds_each_record_and_original_unicode_span(peer, order):
    rows, assignments, grants, options = batch(peer)
    result = execute(peer, (rows, tuple(assignments[i] for i in order), grants, options)).to_dict()
    assert [r["observation_id"] for r in result["records"]] == [r.observation_id for r in rows[:3]]
    assert set(result["excluded_partition_ids"]) == {"r22:3", "r22:4"}
    assert result["joint_acceptance"] is result["research_release"] is result["predictor_export"] is False
    for row in result["records"][:2]:
        source = next(r for r in rows if r.observation_id == row["observation_id"])
        report = row["review"]
        assert report["artifact_id"] == source.observation_id
        assert report["semantic_changes_labels"] is False and report["learned_values"] == [None] * 4
        assert row["evidence_sha256"] == evidence_fingerprint(source)
        assert row["peer_lifecycle"]["overall_status"] == "not_evaluated"
        assert "subject" not in row["peer_lifecycle"] and "body" not in row["peer_lifecycle"]
        for indicator in report["indicators"]:
            for hit in indicator["evidence"]:
                span = hit["span"]
                assert getattr(source, span["field"]).value[span["start"]:span["end"]] == span["text"]
    assert result["records"][2]["review"] is None


def test_reordered_observations_and_identical_contents_never_merge_identity(peer):
    rows, assignments, grants, options = batch(peer)
    second = replace(rows[1], subject=rows[0].subject, body=rows[0].body)
    rows = (second, rows[0], *rows[2:])
    grants[second.observation_id] = replace(grants[second.observation_id], evidence_sha256=evidence_fingerprint(second))
    result = execute(peer, (rows, assignments[::-1], grants, options)).to_dict()
    assert [r["review"]["artifact_id"] for r in result["records"][:2]] == ["r22:1", "r22:0"]
    assert result["records"][0]["evidence_sha256"] != result["records"][1]["evidence_sha256"]


@pytest.mark.parametrize("value,availability", [(None, "unavailable"), ("", "known_empty"), ("  ", "known_empty")])
def test_actual_missingness_remains_distinct_without_fabricated_absence(peer, value, availability):
    rows, assignments, _, options = batch(peer)
    row = replace(rows[0], subject=peer.inputs.TextField(value), body=peer.inputs.TextField())
    rows = (row, *rows[1:])
    grants = {rows[1].observation_id: EvidenceAuthorization(evidence_fingerprint(rows[1]), True, False, "software only")}
    result = execute(peer, (rows, assignments, grants, options)).to_dict()["records"][0]
    assert result["status"] == "unavailable" and result["reason"] == "missing_text_evidence"
    assert result["field_availability"]["subject"] == availability and result["review"] is None


@pytest.mark.parametrize("language", ["es", "und", "fr", "en-us"])
def test_actual_language_gate_has_no_implicit_translation_or_language_guess(peer, language):
    rows, assignments, grants, options = batch(peer)
    row = replace(rows[0], language=language)
    rows = (row, *rows[1:])
    grants.pop(row.observation_id)
    if language.startswith("en"):
        grants[row.observation_id] = EvidenceAuthorization(evidence_fingerprint(row), True, False, "software only")
    result = execute(peer, (rows, assignments, grants, options)).to_dict()["records"][0]
    assert (result["review"] is not None) == language.startswith("en")


@pytest.mark.parametrize("mutation", ["body_false", "body_bool_type", "purpose_missing", "link_false", "wrong_hash", "swapped_grants", "missing_id", "extra_id", "evidence_drift", "snapshot_drift"])
def test_all_consent_and_identity_checks_finish_before_any_reviewer(peer, mutation):
    rows, assignments, grants, options = batch(peer)
    original = grants["r22:0"]
    if mutation == "body_false": grants["r22:0"] = replace(original, body_collection_authorized=False)
    elif mutation == "body_bool_type": grants["r22:0"] = replace(original, body_collection_authorized=1)
    elif mutation == "purpose_missing": grants["r22:0"] = replace(original, study_purpose="")
    elif mutation == "link_false":
        row = replace(rows[0], links=peer.inputs.LinkField(("https://example.invalid/",)))
        rows = (row, *rows[1:]); grants["r22:0"] = replace(original, evidence_sha256=evidence_fingerprint(row))
    elif mutation == "wrong_hash": grants["r22:0"] = replace(original, evidence_sha256="0" * 64)
    elif mutation == "swapped_grants": grants["r22:0"], grants["r22:1"] = grants["r22:1"], grants["r22:0"]
    elif mutation == "missing_id": del grants["r22:0"]
    elif mutation == "extra_id": grants["foreign"] = original
    elif mutation == "evidence_drift": rows = (replace(rows[0], body=peer.inputs.TextField("Changed evidence")), *rows[1:])
    elif mutation == "snapshot_drift":
        other = replace(rows[0].dataset, snapshot_id="changed")
        rows = tuple(replace(r, dataset=other) for r in rows);options["identity"] = other
    calls = []
    with pytest.raises(JointIntegrationError):
        execute(peer, (rows, assignments, grants, options), reviewer=lambda *a, **k: calls.append(a))
    assert calls == []


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate", "cross_partition", "cross_fold", "wrong_total", "wrong_targets", "duplicate_observation", "scope"])
def test_actual_peer_batch_rejections_never_reach_reviewer(peer, mutation):
    rows, assignments, grants, options = batch(peer)
    if mutation == "missing": assignments = assignments[:-1]
    elif mutation == "extra": assignments += (peer.inputs.PartitionAssignment("extra", "foreign", "test"),)
    elif mutation == "duplicate": assignments += (assignments[0],)
    elif mutation == "cross_partition": assignments = (*assignments[:3], replace(assignments[3], group_id=assignments[0].group_id), assignments[4])
    elif mutation == "cross_fold": assignments = (assignments[0], replace(assignments[1], group_id=assignments[0].group_id), *assignments[2:])
    elif mutation == "wrong_total": options["expected_total"] = 6
    elif mutation == "wrong_targets": options["expected_targets"] = {peer.inputs.PhishingLabel.LEGITIMATE: 2, peer.inputs.PhishingLabel.PHISHING: 3}
    elif mutation == "duplicate_observation": rows = (rows[0], rows[0], *rows[2:])
    elif mutation == "scope": options["engineering_only"] = False
    calls = []
    with pytest.raises(JointIntegrationError):
        execute(peer, (rows, assignments, grants, options), reviewer=lambda *a, **k: calls.append(a))
    assert calls == []


@pytest.mark.parametrize("mutation", ["identity", "swap", "semantic_promotion", "learned_z", "release", "source_span", "boolean_offset", "unknown_target", "provider_exception"])
def test_each_untrusted_output_validated_against_its_own_original_record(peer, mutation):
    other = analyze_evidence({"schema_version": "1.0.0", "codebook_version": "0.1.0", "artifact_id": "other",
        "source_id": "SyntheticR22", "source_reference": "synthetic-engineering", "modality": "content_bearing_email",
        "language": "en", "fields": {"subject": "Other: Act now!"}, "body_collection_authorized": False,
        "link_extraction_authorized": False, "study_purpose": ""})
    def corrupt(request, **kwargs):
        if mutation == "provider_exception": raise RuntimeError("PRIVATE_PROVIDER_DETAIL")
        report = analyze_evidence(request)
        if mutation == "identity": report["artifact_id"] = "wrong"
        elif mutation == "swap": report = deepcopy(other)
        elif mutation == "semantic_promotion": report["semantic_changes_labels"] = True
        elif mutation == "learned_z": report["learned_values"][0] = .5
        elif mutation == "release": report["research_release"] = True
        elif mutation == "unknown_target": report["target"] = 1
        else:
            hit = next(hit for i in report["indicators"] for hit in i["evidence"])
            if mutation == "source_span": hit["span"]["text"] = "wrong original"
            elif mutation == "boolean_offset": hit["span"]["start"] = True
        return report
    with pytest.raises(JointIntegrationError, match="^review_output_rejected$") as error:
        execute(peer, reviewer=corrupt)
    assert "PRIVATE" not in str(error.value)


@pytest.mark.parametrize("top", ["entailment", "neutral", "contradiction"])
def test_explicit_software_scores_never_change_deterministic_labels(peer, top):
    class SoftwareScorer:
        def score(self, text, indicator):
            return [{k: .9 if k == top else .05 for k in ("entailment", "neutral", "contradiction")}] * 3
    base = execute(peer).to_dict()
    result = execute(peer, scorer=SoftwareScorer()).to_dict()
    for original, scored in zip(base["records"][:2], result["records"][:2]):
        assert [r["deterministic_state"] for r in original["review"]["indicators"]] == [r["deterministic_state"] for r in scored["review"]["indicators"]]
        assert scored["review"]["semantic_changes_labels"] is False
        assert all(r["candidate_state"] in {"abstained", "unavailable"} for r in scored["review"]["indicators"])
    assert result["joint_acceptance"] is result["research_release"] is False


@pytest.mark.parametrize("html", ["<![CDATA[hidden]]><p>Act now.</p>", "<![unsupported]><p>Notice</p>", "<![bogus]>"])
def test_proposed_strict_preprocessing_intersection_rejects_peer_permissive_declarations(peer, html):
    raw = {"kind": "webpage", "html": html}
    with pytest.raises(ValueError): joint_preprocess(raw, peer)


def test_actual_behavioral_compatibility_and_backend_envelope_remain_review_only(peer):
    descriptor = contract()
    descriptor["approved_for_E2_E3"] = True  # Counterpart explicitly ignores claimed approval.
    review = peer.compatibility.review_contract(descriptor)
    assert review.structurally_compatible and review.research_ready is False
    extraction = peer.extraction.RuleEngine().extract(peer.preprocessing.preprocess({"kind": "email", "subject": "Act now!", "sender": "sender@example.invalid"}))
    representation = peer.representation.BrlRepresentation(extraction)
    vector = peer.compatibility.review_rule_vector(descriptor, representation_type="rule_derived_binary_v1",
        feature_names=representation.deterministic_names, values=representation.deterministic_slots)
    assert vector.review.research_ready is False and any(v is None for v in vector.values)


def test_no_stale_cross_record_result_and_returned_report_is_immutable(peer):
    frozen = execute(peer)
    result = frozen.to_dict(); result["records"][0]["review"]["artifact_id"] = "changed"
    assert frozen.to_dict()["records"][0]["review"]["artifact_id"] == "r22:0"
    with pytest.raises(TypeError): frozen.document["joint_acceptance"] = True


def test_closed_partitions_never_reach_preprocessing_or_review(peer, monkeypatch):
    raw_calls, review_calls = [], []
    original = peer.preprocessing.preprocess
    def inspected(raw):
        assert "DO_NOT_ANALYZE_CLOSED" not in str(raw)
        raw_calls.append(raw)
        return original(raw)
    monkeypatch.setattr(peer.preprocessing, "preprocess", inspected)
    def inspected_review(request, **kwargs):
        assert "DO_NOT_ANALYZE_CLOSED" not in str(request)
        review_calls.append(request["artifact_id"])
        return analyze_evidence(request, **kwargs)
    execute(peer, reviewer=inspected_review)
    assert len(raw_calls) == 2 and review_calls == ["r22:0", "r22:1"]


def test_metadata_only_and_explicit_link_opt_in(peer):
    rows, assignments, grants, options = batch(peer)
    first = replace(rows[0], body=peer.inputs.TextField(), links=peer.inputs.LinkField(("https://example.invalid/",)))
    rows = (first, *rows[1:])
    grants[first.observation_id] = EvidenceAuthorization(evidence_fingerprint(first), False, True, "")
    report = execute(peer, (rows, assignments, grants, options)).to_dict()["records"][0]
    assert report["field_availability"]["body"] == "unavailable"
    assert report["field_availability"]["links"] == "available"
    assert report["review"]["artifact_id"] == first.observation_id


def test_bounded_batch_has_no_reviewer_side_effects(peer):
    rows, assignments, grants, options = batch(peer)
    with pytest.raises(JointIntegrationError, match="batch_size_limit"):
        execute(peer, (iter([rows[0]] * 129), assignments, grants, options))
