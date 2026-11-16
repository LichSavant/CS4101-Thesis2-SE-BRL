import hashlib
import json
from pathlib import Path

import pytest

from ml import research_policy as policy
from ml.datasets import DatasetRecord
from ml.se_brl.representation_contract import contract, validate_values, require_experiment_ready


@pytest.mark.parametrize("alias", ["SpaPhish", "SPA PHISH", "spa-phish", "spa_phish", "ＳｐａＰｈｉｓｈ", "spa\u200bphish"])
@pytest.mark.parametrize("stage", policy.RESEARCH_STAGES)
def test_excluded_aliases_cannot_enter_any_stage(alias, stage):
    with pytest.raises(policy.ResearchPolicyError):
        policy.reject_excluded({"stage": stage, "nested": [{"source_dataset": alias}]})


def test_every_research_stage_stays_closed():
    for stage in policy.RESEARCH_STAGES:
        with pytest.raises(policy.ResearchPolicyError, match="blocked"):
            policy.require_stage_authorization(stage)
    with pytest.raises(policy.ResearchPolicyError, match="Unknown"):
        policy.require_stage_authorization("fallback")


def test_generic_loader_rejects_alias_and_unknown_file_before_read(tmp_path):
    with pytest.raises(policy.ResearchPolicyError):
        policy.read_research_csv(tmp_path / "Spa Phish.csv")
    with pytest.raises(policy.ResearchPolicyError):
        policy.read_research_csv(tmp_path / "renamed.csv")
    with pytest.raises(policy.ResearchPolicyError, match="Unregistered"):
        policy.verify_artifact(tmp_path / "unknown.csv", tmp_path)


def test_registered_fingerprints_and_renamed_excluded_payload(tmp_path, monkeypatch):
    file = tmp_path / "fixture.csv"
    payload = b"source_dataset,target\nfixture,0\n"
    file.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    fixture_policy = {"artifacts": {"fixture.csv": {"sha256": digest, "role": "integrity_only"}}, "excluded_file_sha256": []}
    monkeypatch.setattr(policy, "load_policy", lambda: fixture_policy)
    assert policy.read_verified_csv(file, tmp_path) == [{"source_dataset": "fixture", "target": "0"}]
    fixture_policy["excluded_file_sha256"] = [digest]
    with pytest.raises(policy.ResearchPolicyError, match="fingerprint"):
        policy.read_verified_csv(file, tmp_path)
    fixture_policy["excluded_file_sha256"] = []
    file.write_bytes(b"source_dataset,target\nchanged,1\n")
    with pytest.raises(policy.ResearchPolicyError, match="fingerprint"):
        policy.verify_artifact(file, tmp_path)


def test_renamed_csv_with_excluded_record_source_is_rejected(tmp_path, monkeypatch):
    file = tmp_path / "fixture.csv"
    file.write_text("source_dataset,target\nSPA PHISH,1\n")
    monkeypatch.setattr(policy, "load_policy", lambda: {"artifacts": {"fixture.csv": {"sha256": policy.fingerprint(file)}}, "excluded_file_sha256": []})
    with pytest.raises(policy.ResearchPolicyError):
        policy.read_verified_csv(file, tmp_path)
    with pytest.raises(policy.ResearchPolicyError):
        list(policy.iter_verified_csv(file, tmp_path))


def test_canonical_record_rejects_indirect_excluded_provenance():
    with pytest.raises(policy.ResearchPolicyError):
        DatasetRecord("fixture:1", "fixture", "content_bearing_email", {"kind": "email", "subject": "Hello"},
                      ("subject",), True, {"parent_artifacts": [{"source": "spa-phish"}]})


@pytest.mark.parametrize("configuration", ["E1", "E2", "E3"])
def test_representation_cannot_bypass_experiment_approval(configuration):
    with pytest.raises(policy.ResearchPolicyError):
        require_experiment_ready(configuration, "rule_derived_binary_v1")
    validate_values("rule_derived_binary_v1", (1, 0, 0, 0, 1, 1, 0, 1))
    validate_values("learned_dimension_values_v1", (None, None, None, None, 1, 1, 0, 1))
    with pytest.raises(policy.ResearchPolicyError):
        validate_values("learned_dimension_values_v1", (1, 0, 0, 0, 1, 1, 0, 1))
    assert contract()["accepted_behavioral_features"] == []


def test_all_notebooks_gate_before_side_effects_and_use_checked_loaders():
    from ml.notebook_sources import NOTEBOOK_STAGES, verify_projection
    root = Path(__file__).resolve().parents[2]
    paths = sorted((root / "experiments/notebook-sources").glob("*.source.json"))
    assert len(paths) == 5  # An absent directory must never pass vacuously.
    sources = [json.loads(path.read_text()) for path in paths]
    assert {d["notebook"] for d in sources} == set(NOTEBOOK_STAGES)
    for document in sources:
        assert verify_projection(document)["guard_verified"]


def test_registry_has_no_active_or_excluded_inputs():
    document = policy.load_policy()
    assert not document["approved_training_datasets"]
    assert not document["approved_annotation_sources"]
    assert not document["accepted_experiments"]
    for path, entry in document["artifacts"].items():
        policy.reject_excluded((path, entry))
        assert entry["accepted_for_research"] is False


def test_excluded_hash_in_nested_provenance_is_rejected_even_with_an_alias_free_name():
    digest = policy.load_policy()["excluded_file_sha256"][0]
    with pytest.raises(policy.ResearchPolicyError, match="fingerprint"):
        policy.reject_excluded({"source": "renamed", "parents": [{"artifact_sha256": digest.upper()}]})
    with pytest.raises(policy.ResearchPolicyError, match="fingerprint"):
        DatasetRecord("fixture:1", "fixture", "content_bearing_email", {"kind": "email", "subject": "Hello"},
                      ("subject",), True, {"source": "fixture", "original_file_sha256": digest})
