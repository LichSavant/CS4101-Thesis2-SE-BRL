"""SE-BRL inference integrity and coverage gate.

Development-only. Never interprets unimplemented indicators as validated.
"""
import json
from pathlib import Path

from V13D_hybrid_extractor import _load_codebook
from V17_semantic_controller import infer as infer_v17

HERE = Path(__file__).resolve().parent
CONTRACTS = HERE / "V19_twelve_indicator_contracts.json"
IMPLEMENTED = {
    "urgency",
    "credential_sensitive_data_request",
}


def run(text, modality="content_bearing_email", semantic=None):
    text = str(text or "")
    cb, dimensions = _load_codebook()
    spec = json.loads(CONTRACTS.read_text(encoding="utf-8"))

    if set(spec["indicators"]) != set(dimensions):
        raise ValueError("Contract/codebook indicator mismatch")

    valid_modalities = {m["id"] for m in cb["modalities"]}
    if modality not in valid_modalities:
        raise ValueError("Unknown modality")

    provisional = infer_v17(text, modality=modality, semantic=semantic)
    records = provisional["indicators"]

    if set(records) != set(dimensions):
        raise ValueError("Inference output missing indicators")

    unsupported = []
    for indicator, record in records.items():
        if record["dimension"] != dimensions[indicator]:
            raise ValueError("Incorrect indicator dimension")

        if indicator not in IMPLEMENTED:
            if record["state"] == "supported":
                raise ValueError(
                    "Unimplemented indicator asserted support: " + indicator
                )
            unsupported.append(indicator)

        if record["state"] == "supported":
            if not record["semantic_inference_executed"]:
                raise ValueError("Positive inference without transformer")
            if not record["evidence"]:
                raise ValueError("Positive inference without evidence")

        for span in record["evidence"]:
            start = span["start"]
            end = span["end"]
            if (
                not isinstance(start, int)
                or not isinstance(end, int)
                or isinstance(start, bool)
                or isinstance(end, bool)
                or start < 0
                or end <= start
                or end > len(text)
                or text[start:end] != span["text"]
            ):
                raise ValueError("Invalid evidence provenance")

    return {
        "schema": "sebrl_v20_development",
        "codebook_version": cb["codebook_version"],
        "modality": modality,
        "indicator_count": len(records),
        "implemented_indicator_count": len(IMPLEMENTED),
        "pending_indicators": unsupported,
        "behavioral_accuracy_validated": False,
        "approved_for_E2_E3": False,
        "approved_for_sealed_test": False,
        "publishable_as_validated_results": False,
        "indicators": records,
    }


def assert_research_ready(report):
    if report["pending_indicators"]:
        raise RuntimeError("Research gate closed: indicator coverage incomplete")
    if not report["behavioral_accuracy_validated"]:
        raise RuntimeError("Research gate closed: independent accuracy unverified")
    if not report["approved_for_E2_E3"]:
        raise RuntimeError("Research gate closed: experimental policy unapproved")
