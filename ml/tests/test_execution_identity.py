"""Synthetic integrity receipts; never model or source-custody evidence."""
import json
import pytest

from ml.execution_identity import execution_identity, write_integrity_receipt, verify_integrity_receipt
from ml.experiment_inputs import InputContractError


def identity(root):
    return execution_identity(root,code_sha256={"synthetic.py":"a"*64},settings_sha256="b"*64)


def test_unknown_git_is_explicit_and_exact_code_settings_retained(tmp_path,monkeypatch):
    def unavailable(*args,**kwargs):
        raise OSError("git unavailable")
    monkeypatch.setattr("ml.execution_identity.subprocess.check_output",unavailable)
    state=identity(tmp_path)
    assert state["git"]["dirty"] is None and state["git"]["state"]=="unavailable"
    assert state["code_sha256"]=={"synthetic.py":"a"*64}
    assert not state["reproducible_from_head_alone"] and not state["source_custody_established"]


@pytest.mark.parametrize("change", ["payload","added","removed","receipt"])
def test_receipt_reloads_and_detects_changes_without_overwriting(tmp_path,change):
    (tmp_path/"synthetic.txt").write_text("fixture")
    digest=write_integrity_receipt(tmp_path,identity=identity(tmp_path),input_sha256={"fixture":"c"*64},category="software_validation")
    record=verify_integrity_receipt(tmp_path,expected_sha256=digest)
    assert record["category"]=="software_validation" and not record["research_readiness_established"]
    before=(tmp_path/"completion_integrity.json").read_bytes()
    with pytest.raises(InputContractError,match="already_exists"):
        write_integrity_receipt(tmp_path,identity=identity(tmp_path),input_sha256={"fixture":"c"*64},category="software_validation")
    assert (tmp_path/"completion_integrity.json").read_bytes()==before
    if change=="payload":(tmp_path/"synthetic.txt").write_text("tampered")
    elif change=="added":(tmp_path/"extra.txt").write_text("extra")
    elif change=="removed":(tmp_path/"synthetic.txt").unlink()
    else:(tmp_path/"completion_integrity.json").write_text("{}")
    with pytest.raises(InputContractError,match="integrity"):
        verify_integrity_receipt(tmp_path,expected_sha256=digest)


def test_no_research_category_or_empty_success_receipt(tmp_path):
    with pytest.raises(InputContractError,match="category"):
        write_integrity_receipt(tmp_path,identity=identity(tmp_path),input_sha256={"fixture":"c"*64},category="research")
    with pytest.raises(InputContractError,match="nonempty"):
        write_integrity_receipt(tmp_path,identity=identity(tmp_path),input_sha256={"fixture":"c"*64},category="software_validation")
