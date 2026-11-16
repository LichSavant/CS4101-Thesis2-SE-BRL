import csv
import hashlib
import json

import pytest

from ml.experiment_inputs import InputContractError
from ml.web_source_audit import audit_web_snapshot
from ml.source_audit import write_source_audit


def snapshot(tmp_path):
    root = tmp_path / "snapshot"
    root.mkdir()
    columns = ["_id", "features.html", "features.text", "language", "url", "domain", "brands"]
    entries = []
    for name, count in (("phishing.csv", 2), ("not-phishing.csv", 1)):
        with (root/name).open("w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
            for i in range(count):
                writer.writerow({"_id":f"synthetic-native-{i}","features.html":json.dumps(["html","p"]),
                    "features.text":"Synthetic stored text.","language":"en" if i==0 else "xx",
                    "url":"https://example.test/","domain":"example.test","brands":"annotation-not-a-predictor"})
    (root/"brands.csv").write_text("name,website\nSynthetic,https://example.test\n")
    for name in ("phishing.csv","not-phishing.csv","brands.csv"):
        data=(root/name).read_bytes();entries.append(dict(file=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    manifest=dict(source_record=8041387,license="CC-BY-4.0",files=entries)
    (root/"source_manifest.json").write_text(json.dumps(manifest))
    return root,hashlib.sha256((root/"source_manifest.json").read_bytes()).hexdigest()


def run(root,digest,**changes):
    options=dict(expected_manifest_sha256=digest,expected_class_counts={"phishing":2,"legitimate":1},max_field_chars=10000)
    options.update(changes)
    return audit_web_snapshot(root,**options)


def test_aggregate_native_audit_does_not_export_ids_text_or_assignments(tmp_path):
    root,digest=snapshot(tmp_path);report=run(root,digest)
    assert report["source_records"]==3 and report["all_source_counts_match"]
    assert report["distinct_native_ids_across_sources"]==2 and report["repeated_native_ids_across_sources"]==1
    assert report["source_files"]["phishing.csv"]["native_language_counts"]=={"en":1,"xx":1}
    assert report["raw_html_or_dom_attributes_established"] is False
    assert report["brand_annotation_used_as_predictor"] is False
    assert report["groups_generated"]==report["assignments_generated"]==report["model_fits"]==0
    serialized=json.dumps(report)
    assert "synthetic-native-" not in serialized and "Synthetic stored text." not in serialized
    assert "annotation-not-a-predictor" not in serialized and "https://example.test/" not in serialized
    write_source_audit(tmp_path/"run",report)
    assert (tmp_path/"run/source_audit.json").exists()


def test_count_mismatch_is_reported_not_repaired(tmp_path):
    root,digest=snapshot(tmp_path)
    report=run(root,digest,expected_class_counts={"phishing":3,"legitimate":1})
    assert report["all_source_counts_match"] is False and report["source_records"]==3
    assert report["population_status"]=="not_screened_not_frozen"


@pytest.mark.parametrize("change", ({"expected_manifest_sha256":"0"*64},{"max_field_chars":True},
    {"expected_class_counts":{"phishing":True,"legitimate":1}}))
def test_invalid_expectations_fail_without_output(tmp_path,change):
    root,digest=snapshot(tmp_path)
    with pytest.raises(InputContractError):run(root,digest,**change)
    assert not (tmp_path/"run").exists()


def test_payload_tampering_fails_after_streaming_without_a_success_report(tmp_path):
    root,digest=snapshot(tmp_path)
    path=root/"phishing.csv";data=path.read_bytes();path.write_bytes(data.replace(b'Synthetic',b'SynthEtic'))
    with pytest.raises(InputContractError,match="digest_mismatch"):run(root,digest)
    assert not (tmp_path/"run").exists()
