"""P3 metadata-only fixtures; no source custody or scientific acceptance claim."""
from copy import deepcopy
import pytest

from ml.experiment_inputs import InputContractError
from ml.preparation_integrity import validate_prospective_population
from ml.research_protocol import prospective_id


def rows():
    return [dict(observation_id=prospective_id("fixture", "a"*64, "fixture.csv", i),
        source_dataset="fixture", snapshot_sha256="a"*64, source_file="fixture.csv",
        source_row_id=i, native_label=i, target=i) for i in (0, 1)]


def test_deterministic_identity_preserves_original_position_and_order_independence():
    source=rows(); before=deepcopy(source)
    result=validate_prospective_population(source)
    assert result == validate_prospective_population(source[::-1])
    assert source == before and result["source_custody_established"] is False
    assert prospective_id("fixture","a"*64,"fixture.csv",0) != prospective_id("fixture","b"*64,"fixture.csv",0)


@pytest.mark.parametrize("branch,source", (("Email", "CEAS"), ("Web", "PhiUSIIL"),
    ("PhiUSIIL", "UCI Phishing Websites"), ("UCI", "PhiUSIIL")))
def test_preparation_cannot_expand_accepted_branch_sources(branch, source):
    from ml.preparation_integrity import validate_preparation_sources
    with pytest.raises(InputContractError, match="source_outside_branch"):
        validate_preparation_sources([{"source_dataset": source}], branch)


@pytest.mark.parametrize("change", ["duplicate", "conflicting_id", "missing", "snapshot", "label", "bool_target", "position"])
def test_invalid_metadata_rejected(change):
    source=rows()
    if change=="duplicate":source.append(dict(source[0]))
    elif change=="conflicting_id":source[1]["observation_id"]=source[0]["observation_id"]
    elif change=="missing":del source[0]["source_file"]
    elif change=="label":source[1]["native_label"]=0
    elif change=="bool_target":source[1]["target"]=True
    elif change=="position":source[1]["source_row_id"]=True
    else:
        source[1]["snapshot_sha256"]="b"*64
        source[1]["observation_id"]=prospective_id("fixture","b"*64,"fixture.csv",1)
    with pytest.raises(InputContractError):validate_prospective_population(source)


def test_d9_receipt_binds_exact_input_code_and_export_bytes(tmp_path):
    from ml.tests.test_preparation_execution import packet
    from ml.preparation_execution import run_preparation
    from ml.execution_identity import verify_integrity_receipt
    protocol,receipt,digest,run_id,_=packet(tmp_path)
    result=run_preparation(tmp_path,run_id,stage="D-features",expected_authorization_sha256=digest)
    output=protocol.parent.parent/receipt["output_run_id"]
    integrity=verify_integrity_receipt(output,expected_sha256=result["completion_integrity_sha256"])
    assert integrity["category"]=="no_fit_preparation"
    assert integrity["identity"]["code_sha256"]==receipt["code_sha256"]
    assert integrity["input_sha256"]["external_authorization_receipt"]==digest
    assert not integrity["research_readiness_established"]
    (output/"data/processed/features/development/uci_development.csv").write_text("fixture tampering")
    with pytest.raises(InputContractError,match="integrity_output_changed"):
        verify_integrity_receipt(output,expected_sha256=result["completion_integrity_sha256"])
