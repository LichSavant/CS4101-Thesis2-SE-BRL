import pytest

from ml.finalization import partition_report


def test_metadata_fingerprints_preserve_order_independence_and_detect_leakage():
    rows = {"a": ("0", "g1", "development", "1.0"), "b": ("1", "g2", "test", "")}
    report = partition_report(rows)
    assert report["supplied_group_integrity"]
    assert report["partition_metadata_sha256"] == partition_report(dict(reversed(list(rows.items()))))["partition_metadata_sha256"]
    rows["b"] = ("1", "g1", "test", "")
    assert partition_report(rows)["groups_crossing_partitions"] == 1
    assert not partition_report(rows)["supplied_group_integrity"]


def test_development_fold_and_missing_group_errors_fail_closed():
    assert not partition_report({})["supplied_group_integrity"]
    assert not partition_report({"a": ("0", "", "development", "")})["supplied_group_integrity"]
    report = partition_report({"a": ("0", "g", "development", "1"), "b": ("1", "g", "development", "2")})
    assert report["groups_crossing_folds"] == 1
