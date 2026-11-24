"""Verify pinned UCI release documentation and ARFF header without reading rows."""
import hashlib
import io
import re
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from ml.uci_schema import NATIVE_DOMAINS
from ml.uci_snapshot import EXPECTED_SHA256
from ml.notebook_contracts import LABEL_MAPPINGS


MEMBERS = {".old.arff": 170897, "Training Dataset.arff": 800920,
           "Phishing Websites Features.docx": 38995}
DOC_SHA256 = "f6f9326f45659a7b5ef947fa744cec2c379dbea17de56d34436312407faca43c"


def read_header_only(stream, *, max_bytes=16384):
    """Request one byte at a time and stop at the newline ending @data.

    Never request the first data-region byte. ZIP's decompressor may buffer
    internally; no record text is returned, parsed, exported or used.
    """
    header, line = bytearray(), bytearray()
    while len(header) < max_bytes:
        byte = stream.read(1)
        if not byte:
            break
        header.extend(byte); line.extend(byte)
        if byte == b"\n":
            if line.strip().lower() == b"@data":
                return bytes(header)
            line.clear()
    raise ValueError("bounded_arff_header_boundary_required")


def compare_header(header):
    attributes = []
    for line in header.decode("utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("%"):
            continue
        match = re.fullmatch(r"\s*@attribute\s+(?:'([^']+)'|\"([^\"]+)\"|(\S+))\s+\{([^}]+)\}\s*", line, re.I)
        if match:
            name = next(x for x in match.groups()[:3] if x is not None)
            codes = tuple(x.strip() for x in match[4].split(","))
            if len(codes) != len(set(codes)):
                raise ValueError("duplicate_native_domain_code")
            attributes.append((name, set(codes)))
        elif not re.fullmatch(r"\s*@(?:relation\s+\S+|data)\s*", line, re.I):
            raise ValueError("unsupported_release_header")
    expected = [(name, {str(x) for x in domain}) for name, domain in NATIVE_DOMAINS.items()]
    expected.append(("Result", {"-1", "1"}))
    if attributes != expected:
        raise ValueError("release_dictionary_name_order_or_domain_mismatch")
    return {"ordered_predictors": 30, "target_field": "Result", "target_codes": [-1, 1],
            "native_result_meanings_established": False}


def verify_archive(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(65536), b""):
            digest.update(block)
    if digest.hexdigest() != EXPECTED_SHA256:
        raise ValueError("official_archive_digest_mismatch")
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if (len(infos) != len(MEMBERS)
                or {item.filename: item.file_size for item in infos} != MEMBERS):
            raise ValueError("unexpected_release_members")
        document = archive.read("Phishing Websites Features.docx")
        if hashlib.sha256(document).hexdigest() != DOC_SHA256:
            raise ValueError("release_document_digest_mismatch")
        with archive.open("Training Dataset.arff") as source:
            header = read_header_only(source)
    comparison = compare_header(header)
    with zipfile.ZipFile(io.BytesIO(document)) as docx:
        tree = ET.fromstring(docx.read("word/document.xml"))
    text_tags = {"{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t",
                 "{http://schemas.openxmlformats.org/officeDocument/2006/math}t"}
    text = " ".join(node.text or "" for node in tree.iter() if node.tag in text_tags)
    return {"scope": "release_document_and_source_header_only", "archive_sha256": digest.hexdigest(),
            "member_sizes": MEMBERS, "document_sha256": DOC_SHA256,
            "header_sha256": hashlib.sha256(header).hexdigest(), "header_bytes_returned": len(header),
            "header_comparison": comparison, "feature_document_contains_Result_token": bool(re.search(r"\bResult\b", text)),
            "existing_native_to_target_mapping": {str(native): target for native, target
                                                   in LABEL_MAPPINGS["UCI Phishing Websites"].items()},
            "existing_mapping_code_set_matches_header": set(LABEL_MAPPINGS["UCI Phishing Websites"]) == {-1, 1},
            "existing_target_convention": {"1": "phishing", "0": "legitimate"},
            "mapping_authoritatively_verified": False, "research_rows_returned_or_processed": 0,
            "files_extracted": 0, "scientific_admission": False}
