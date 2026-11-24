"""Synthetic metadata integrity regressions; no estimators or corpus access."""
import unittest

from tools.scientific_validation_snapshot import FIELDS, summarize


def fixture(extra=""):
    rows = [f"s::{i},source,{i % 2},g{i},development,{i % 5 + 1}.0" for i in range(10)]
    return (",".join(FIELDS) + "\n" + "\n".join(rows) + "\n" + extra).encode()


class MetadataTests(unittest.TestCase):
    def test_integrity_never_implies_admission(self):
        report = summarize(fixture())
        self.assertTrue(report["metadata_integrity_pass"])
        self.assertFalse(report["scientific_admission"])

    def test_cross_role_group_rejected(self):
        report = summarize(fixture("reserved,source,0,g0,test,\n"))
        self.assertFalse(report["metadata_integrity_pass"])
        self.assertEqual(report["role_crossing_groups"], 1)

    def test_duplicate_id_and_fold_crossing_rejected(self):
        report = summarize(fixture("s::0,source,1,g0,development,2\n"))
        self.assertEqual(report["duplicate_ids"], 1)
        self.assertEqual(report["fold_crossing_groups"], 1)
        self.assertFalse(report["metadata_integrity_pass"])

    def test_reserved_fold_rejected(self):
        self.assertFalse(summarize(fixture("reserved,source,0,reserved,test,1\n"))["checks"]["reserved_folds_empty"])

    def test_lfs_pointer_not_treated_as_metadata(self):
        with self.assertRaises(ValueError):
            summarize(b"version https://git-lfs.github.com/spec/v1\n")

    def test_malformed_row_rejected(self):
        with self.assertRaises(ValueError):
            summarize(fixture("short,row\n"))

    def test_single_class_fold_rejected_even_with_two_classes_overall(self):
        payload = fixture().replace(b"s::5,source,1,", b"s::5,source,0,")
        report = summarize(payload)
        self.assertTrue(report["checks"]["both_targets"])
        self.assertFalse(report["checks"]["both_targets_per_development_fold"])

    def test_source_target_confounding_reported(self):
        payload = fixture().decode().splitlines()
        rows = [payload[0]]
        for row in payload[1:]:
            values = row.split(",")
            values[1] = "source" + values[2]
            rows.append(",".join(values))
        report = summarize(("\n".join(rows) + "\n").encode())
        self.assertTrue(report["each_source_has_only_one_historical_target"])
        self.assertFalse(report["scientific_admission"])


if __name__ == "__main__":
    unittest.main()
