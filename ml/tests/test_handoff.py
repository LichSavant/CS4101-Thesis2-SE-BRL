from copy import deepcopy
import json

import pytest

from ml.handoff import compare_interface, integration_interface, load_interface
from ml.research_policy import load_policy


def synthetic_preflight():
    """Explicit fake custody metadata; never a claim about actual corpus files."""
    return {"integrity_checks_pass": True, "failures": [],
            "checked_artifacts": [{"path": "synthetic/inspection.json", "sha256": "a" * 64,
                                   "role": "synthetic_integrity_fixture", "accepted_for_research": False}],
            "datasets": {key: {"supplied_group_integrity": True, "feature_metadata_matches": True,
                               "partition_manifest_matches": True, "partition_metadata_sha256": "b" * 64,
                               "group_membership_sha256": "c" * 64}
                         for key in ("email", "phiusiil", "iscx", "uci")},
            "excluded_datasets": load_policy()["excluded_dataset_identifiers"]}


@pytest.fixture
def expected():
    return integration_interface(synthetic_preflight())


def declaration(expected):
    # Explicit synthetic commit fixture; never a claim about Dhanwil's checkout.
    return {**deepcopy(expected), "authoritative_commit": "1" * 40}


def test_absent_actual_interface_remains_pending(expected):
    result = compare_interface(expected, None)
    assert result["status"] == "PENDING_DHANWIL_INTERFACE"
    assert result["authoritative_commit"] is None
    assert result["declaration_compatible"] is None
    assert not result["research_release_approved"]


def test_matching_declaration_never_grants_release_or_claims_checkout_verification(expected):
    result = compare_interface(expected, declaration(expected))
    assert result["schema_compatible"] and result["data_compatible"] and result["declaration_compatible"]
    assert not result["research_release_approved"] and not result["checkout_independently_verified"]
    assert expected["approved_active_dataset_ids"] == []
    assert expected["state_semantics"]["learned_z_values"] == [None] * 4


@pytest.mark.parametrize("key", ["indicator_order", "dimension_order", "representation_types"])
def test_order_and_representation_mismatch_are_rejected(expected, key):
    supplied = declaration(expected)
    supplied[key].reverse()
    assert not compare_interface(expected, supplied)["schema_compatible"]


@pytest.mark.parametrize("key", ["partition_fingerprints", "group_fingerprints"])
def test_partition_or_group_changes_are_not_compatible(expected, key):
    supplied = declaration(expected)
    supplied[key]["email"] = "0" * 64
    result = compare_interface(expected, supplied)
    assert not result["data_compatible"] and not result["declaration_compatible"]


def test_artifact_fingerprint_and_missingness_changes_are_rejected(expected):
    supplied = declaration(expected)
    supplied["integrity_artifacts"][0]["sha256"] = "0" * 64
    supplied["state_semantics"]["missing"] = 0
    result = compare_interface(expected, supplied)
    assert not result["data_compatible"] and not result["schema_compatible"]


@pytest.mark.parametrize("source", ["SPA PHISH", "spa-phish", "ＳｐａＰｈｉｓｈ"])
def test_excluded_aliases_in_supplied_interface_cannot_become_inputs(expected, source):
    supplied = declaration(expected)
    supplied["approved_active_dataset_ids"] = [source]
    result = compare_interface(expected, supplied)
    assert "excluded_source_or_fingerprint_in_interface_inputs" in result["mismatches"]
    assert not result["declaration_compatible"]


def test_false_approval_and_unexpected_fallback_are_rejected(expected):
    supplied = declaration(expected)
    supplied["research_release"]["approved_for_E2_E3"] = True
    supplied["fallback_dataset"] = "MeAJOR"
    result = compare_interface(expected, supplied)
    assert not result["schema_compatible"] and not result["research_release_approved"]


@pytest.mark.parametrize("payload", ['{"a":1,"a":2}', '{"a":NaN}', '[]', '{broken'])
def test_interface_json_rejects_duplicates_and_malformed_values(tmp_path, payload):
    path = tmp_path / "interface.json"
    path.write_text(payload)
    with pytest.raises(ValueError):
        load_interface(path)


def test_failed_preflight_cannot_be_handed_off():
    with pytest.raises(ValueError, match="failed"):
        integration_interface({"integrity_checks_pass": False})


def test_handoff_requires_explicit_artifact_and_group_fingerprints():
    report = synthetic_preflight()
    report["checked_artifacts"][0]["sha256"] = "unknown"
    with pytest.raises(ValueError, match="Malformed"):
        integration_interface(report)


def test_cli_interface_comparison_is_no_fit_and_returns_distinct_failure_code(expected, tmp_path, monkeypatch, capsys):
    from ml import finalization
    import sys
    supplied = declaration(expected)
    supplied["state_semantics"]["missing"] = 0
    file = tmp_path / "interface.json"
    file.write_text(json.dumps(supplied))
    monkeypatch.setattr(finalization, "preflight", lambda root: {"integrity_checks_pass": True, "integration_interface": expected})
    monkeypatch.setattr(sys, "argv", ["preflight", "--compare-interface", str(file)])
    assert finalization.main() == 2
    result = json.loads(capsys.readouterr().out)
    assert result["integration_comparison"]["status"] == "INCOMPATIBLE"
    assert not result["integration_comparison"]["research_release_approved"]
