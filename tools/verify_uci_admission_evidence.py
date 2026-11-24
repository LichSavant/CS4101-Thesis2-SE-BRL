"""Verify retained UCI documentation/schema; never load research payloads or fit.

Run from repository root: python -B -m tools.verify_uci_admission_evidence
An integrity PASS does not authorize ingestion, allocation or experiments.
"""
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile


EVIDENCE = Path("docs/research/2026-11-17_uci_admission")
SCHEMA = Path("ml/uci-native-schema.v1.json")
DOCUMENT = "experiments/datasets-raw/webpage/uci/phishing+websites/Phishing Websites Features.docx"
SOURCE_URLS = {
    "uci-page.html": "https://archive.ics.uci.edu/dataset/327/phishing+websites",
    "uci-metadata.json": "https://archive.ics.uci.edu/api/dataset?id=327",
    "uci-feature-document.docx": "https://archive.ics.uci.edu/ml/machine-learning-databases/00327/Phishing%20Websites%20Features.docx",
}


def git_blob(commit, path):
    return subprocess.run(["git", "show", f"{commit}:{path}"], check=True, capture_output=True).stdout


def require(condition):
    if not condition:
        raise ValueError("uci_documentary_evidence_mismatch")


def verify():
    retrieval = json.loads((EVIDENCE / "source-retrieval.json").read_bytes())
    require(len(retrieval) == len(SOURCE_URLS))
    require({entry["artifact"] for entry in retrieval} == set(SOURCE_URLS))
    identities = {}
    for entry in retrieval:
        require(entry["requested_url"] == SOURCE_URLS[entry["artifact"]])
        body = (EVIDENCE / entry["artifact"]).read_bytes()
        require(hashlib.sha256(body).hexdigest() == entry["sha256"])
        require(len(body) == entry["bytes"])
        require(entry["requested_url"] == entry["effective_url"])
        require(entry["effective_url"].startswith("https://archive.ics.uci.edu/"))
        identities[entry["artifact"]] = entry["sha256"]
    schema = json.loads(SCHEMA.read_bytes())
    require(schema["status"] == "evidence_only_not_scientific_acceptance")
    audit = schema["native_audit"]
    require(audit["path"] == "experiments/results/audits/uci_native_value_audit.csv")
    require(audit["git_commit"] == "cee80d97c8454e726d55a97abb98fda74a8e2b7f")
    body = git_blob(audit["git_commit"], audit["path"])
    require(hashlib.sha256(body).hexdigest() == audit["sha256"])
    native_rows = list(csv.DictReader(io.StringIO(body.decode("utf-8"))))
    metadata = json.loads((EVIDENCE / "uci-metadata.json").read_bytes())
    require(metadata["status"] == 200 and metadata["data"]["uci_id"] == 327)
    metadata = metadata["data"]
    require(metadata["dataset_doi"] == "10.24432/C51W2X")
    require(metadata["num_features"] == 30 and metadata["num_instances"] == 11055)
    require(b"CC BY 4.0" in (EVIDENCE / "uci-page.html").read_bytes())
    original_document = git_blob(audit["git_commit"], DOCUMENT)
    require(hashlib.sha256(original_document).hexdigest() == identities["uci-feature-document.docx"])
    with zipfile.ZipFile(io.BytesIO(original_document)) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
    paragraphs = document.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body/"
                                   "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p")
    features = schema["features"]
    variables = metadata["variables"]
    require(len(features) == len(native_rows) - 1 == len(variables) - 1 == 30)
    require(native_rows[-1]["feature"] == "Result" and variables[-1]["role"] == "Target")
    # Explicit API spelling aliases; never silently lowercase source field names.
    aliases = {"Domain_registeration_length": "domain_registration_length", "popUpWidnow": "popupwindow"}
    for order, (feature, native, variable) in enumerate(zip(features, native_rows, variables), 1):
        require(feature["order"] == order and feature["name"] == native["feature"])
        require(feature["native_domain"] == [int(v) for v in re.findall(r"b'(-?\d+)'", native["native_values"])])
        require(feature["uci_api_name"] == variable["name"] == aliases.get(feature["name"], feature["name"].lower()))
        require(variable["role"] == "Feature")
        definition = feature["source_definition"]
        require(definition["artifact_sha256"] == identities["uci-feature-document.docx"])
        require("".join(paragraphs[definition["zero_based_body_paragraph"]].itertext()).strip())
    return {
        "scope": "documentation_and_native_schema_only_no_payload_access",
        "documentation_integrity": "PASS", "ordered_feature_domains_verified": len(features),
        "official_feature_document_matches_retained_git_bytes": True,
        "official_api_target_description": variables[-1]["description"],
        "current_license": "CC BY 4.0", "original_acquisition_date_established": False,
        "scientific_admission": "BLOCKED", "actual_data_no_fit_admission_executed": False,
        "scientific_experiments_executed": 0,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
