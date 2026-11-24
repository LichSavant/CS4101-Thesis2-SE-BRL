"""Generated metadata only; never source records or an authenticated ledger."""
from copy import deepcopy
import pytest

from ml.experiment_inputs import InputContractError
from ml.research_protocol import prospective_id
from ml.uci_lineage import validate_prospective_uci_ledger


def fixture():
    rows = []
    for position, (native, digest, predictor, representative, cleaned) in enumerate([
        (-1, "b", "e", 0, 0), (-1, "b", "e", 0, None),
        (1, "c", "e", 2, 1), (1, "d", "f", 3, 2),
    ]):
        oid = lambda p: prospective_id("UCI Phishing Websites", "a" * 64, "Training Dataset.arff", p)
        rows.append(dict(source_row_id=position, observation_id=oid(position), native_label=native,
                         record_sha256=digest * 64, predictor_sha256=predictor * 64,
                         action="duplicate" if cleaned is None else "retain",
                         representative_id=oid(representative), cleaned_position=cleaned))
    return rows


def check(rows, **options):
    return validate_prospective_uci_ledger(rows, snapshot_sha256=options.get("snapshot", "a" * 64),
                                         original_count=4, retained_count=options.get("retained", 3))


def test_complete_metadata_preserves_conflicts_and_never_claims_custody():
    rows = fixture(); before = deepcopy(rows)
    result = check(rows)
    assert result == check(rows[::-1]) and rows == before
    assert result["removed_complete_duplicates"] == 1
    assert result["predictor_groups"] == 2 and result["mixed_native_label_groups"] == 1
    assert not result["scientific_admission"] and not result["source_custody_established"]
    assert not result["historical_identity_bridge_established"]


@pytest.mark.parametrize("change", ["missing", "position", "bool_position", "identifier", "snapshot",
                                   "representative", "action", "removed_position", "order", "native",
                                   "bool_native", "digest", "extra", "count", "digest_conflict",
                                   "unremoved_duplicate"])
def test_inconsistent_ledger_rejected(change):
    rows = fixture(); options = {}
    if change == "missing": rows.pop()
    elif change == "position": rows[1]["source_row_id"] = 0
    elif change == "bool_position": rows[0]["source_row_id"] = False
    elif change == "identifier": rows[0]["observation_id"] = "UCI::0"
    elif change == "snapshot": options["snapshot"] = "b" * 64
    elif change == "representative": rows[1]["representative_id"] = rows[2]["observation_id"]
    elif change == "action": rows[1]["action"] = "retain"
    elif change == "removed_position": rows[1]["cleaned_position"] = 0
    elif change == "order": rows[2]["cleaned_position"] = 0
    elif change == "native": rows[0]["native_label"] = 0
    elif change == "bool_native": rows[0]["native_label"] = True
    elif change == "digest": rows[0]["record_sha256"] = "not-a-digest"
    elif change == "extra": rows[0]["invented_approval"] = True
    elif change == "count": options["retained"] = 4
    elif change == "digest_conflict": rows[1]["native_label"] = 1
    else:
        rows[3].update(predictor_sha256=rows[2]["predictor_sha256"])
    before = deepcopy(rows)
    with pytest.raises(InputContractError): check(rows, **options)
    assert rows == before
