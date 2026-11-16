import hashlib
import json

import pytest

from ml.csv_source_audit import audit_csv
from ml.experiment_inputs import InputContractError


def invoke(tmp_path, text, **changes):
    path = tmp_path / "source.csv"
    path.write_text(text, encoding="utf-8")
    values = dict(dataset="SpamAssassin", expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        expected_md5=hashlib.md5(path.read_bytes()).hexdigest(), max_bytes=10000, max_field_chars=10000,
        source_reference="synthetic:source", license_reference="synthetic:license", authorization_reference="synthetic:no-fit")
    return audit_csv(path, **dict(values, **changes))


def test_native_labels_empty_fields_duplicates_and_conflicts_without_relabeling(tmp_path):
    result = invoke(tmp_path, 'subject,body,label\nPrivate subject,Private body,0\nPrivate subject,Private body,1\n,,0\n')
    assert result["source_records"] == 3
    assert result["native_label_counts"] == {"0": 2, "1": 1}
    assert result["mixed_native_label_exact_content_keys"] == 1
    assert result["repeated_exact_content_records"] == 1
    assert result["empty_or_whitespace_field_counts"] == {"subject": 1, "body": 1}
    assert result["groups_generated"] == result["assignments_generated"] == result["model_fits"] == 0
    assert "Private" not in json.dumps(result)
    assert "target_counts" not in result


def test_phiusiil_remains_native_and_filename_is_only_opaque_diagnostic(tmp_path):
    result = invoke(tmp_path, 'FILENAME,URL,Domain,TLD,Title,label\nsecret.htm,https://example.test/,example.test,test,Title,1\nsecret.htm,https://example.test/,example.test,test,Title,0\n', dataset="PhiUSIIL")
    assert result["duplicate_native_filename_records"] == 1
    assert result["native_label_counts"] == {"0": 1, "1": 1}
    assert result["mixed_native_label_exact_content_keys"] == 1
    assert "secret.htm" not in json.dumps(result)
    assert "https://example.test/" not in json.dumps(result)


@pytest.mark.parametrize("changes", ({"expected_sha256": "0"*64}, {"expected_md5": "0"*32}, {"max_bytes": 1},
    {"dataset": "abandoned"}, {"max_field_chars": 2}, {"source_reference": ""}))
def test_bad_hash_source_budget_or_reference_rejected(tmp_path, changes):
    with pytest.raises(InputContractError):
        invoke(tmp_path, 'subject,body,label\nPrivate,Private,0\n', **changes)


def test_duplicate_header_and_literal_nan_are_not_silently_fixed(tmp_path):
    with pytest.raises(InputContractError):
        invoke(tmp_path, 'subject,body,label,label\nS,B,0,0\n')
    result = invoke(tmp_path, 'subject,body,label\nnan,null,0\n')
    assert result["literal_missing_token_counts_not_converted"] == {"subject": 1, "body": 1}
    assert result["empty_or_whitespace_field_counts"] == {}
