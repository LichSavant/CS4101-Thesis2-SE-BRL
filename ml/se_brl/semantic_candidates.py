"""Grounded twelve-indicator NLI candidates; no automatic accepted decisions.

The scorer is injected. Model loading is optional, pinned and local-only. The
candidate path never trains, calibrates, rewrites rules, or fills learned slots.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Protocol

from ml.datasets import DatasetRecord, prepare_record
from ml.research_policy import reject_excluded
from .codebook import load_codebook
from .detectors import ConservativeTrustDetector, DetectorContext
from .context import ContextIndex
from .representation_contract import CONTRACT_VERSION


ROOT = Path(__file__).resolve().parents[2]
HYPOTHESES = ROOT / "experiments/vera_validation/V13_nli_hypotheses_v0.1.0.json"
LOCK = Path(__file__).with_name("semantic-model.v1.json")
LABELS = ("entailment", "neutral", "contradiction")
MODEL_ID = "cross-encoder/nli-MiniLM2-L6-H768"
MODEL_REVISION = "b95119ce93d3e065de6214e38cd4a97b0f2f2c6d"
REVIEW_CONTEXT = re.compile(r"\b(?:never|not|no|without|don.t|training|example|hypothetical|allegedly|quoted|educational)\b|[\"'?]", re.I)


class SemanticInferenceUnavailable(RuntimeError):
    """Missing local model or oversized evidence requires abstention."""


class SemanticScorer(Protocol):
    def score(self, text: str, indicator: str) -> list[dict]: ...


def semantic_configuration() -> tuple[dict, dict]:
    """Check declared identity and parse the very bytes whose hash is checked."""
    import hashlib

    try:
        spec = json.loads(LOCK.read_text())
        payload = HYPOTHESES.read_bytes()
        document = json.loads(payload)
    except (OSError, ValueError):
        raise SemanticInferenceUnavailable("Pinned semantic configuration unavailable") from None
    expected = {"lock_version": "1.0.0", "model": MODEL_ID, "tokenizer": MODEL_ID,
                "revision": MODEL_REVISION, "local_files_only": True, "device": "cpu",
                "max_tokens": 512, "oversized_evidence_policy": "abstain_without_truncation",
                "confidence_calibrated": False, "scientifically_accepted": False}
    if not isinstance(spec, dict) or any(type(spec.get(key)) is not type(value) or spec[key] != value for key, value in expected.items()):
        raise SemanticInferenceUnavailable("Pinned model/tokenizer configuration mismatch")
    if hashlib.sha256(payload).hexdigest() != spec.get("hypotheses_sha256"):
        raise SemanticInferenceUnavailable("Hypotheses differ from the model lock")
    codebook = load_codebook()
    parents = {dim["id"]: [item["id"] for item in dim["indicators"]] for dim in codebook["dimensions"]}
    hypotheses = document.get("hypotheses") if isinstance(document, dict) else None
    if (not isinstance(document, dict) or document.get("model") != MODEL_ID or document.get("dimensions") != parents
            or not isinstance(hypotheses, dict) or set(hypotheses) != {i for items in parents.values() for i in items}
            or any(not isinstance(items, list) or len(items) != 3 or any(type(text) is not str or not text.strip() for text in items) for items in hypotheses.values())):
        raise SemanticInferenceUnavailable("Hypotheses do not match the canonical indicator contract")
    reject_excluded((spec, document))
    return spec, hypotheses


def validate_scores(scores: object) -> list[dict[str, float]]:
    if not isinstance(scores, list) or len(scores) != 3:
        raise ValueError("Exactly three hypothesis score records are required")
    result = []
    for item in scores:
        if not isinstance(item, dict):
            raise ValueError("Malformed NLI score record")
        values = {label: item.get(label) for label in LABELS}
        if any(type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1 for value in values.values()):
            raise ValueError("NLI values must be finite probabilities, not calibrated confidence")
        if abs(sum(values.values()) - 1) > 0.001:
            raise ValueError("NLI distribution is not normalized")
        result.append(values)
    return result


class PinnedLocalNliScorer:
    """Explicit opt-in initialization; never downloads or silently truncates."""

    def __init__(self) -> None:
        spec, hypotheses = semantic_configuration()
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            import torch
        except (ImportError, OSError, RuntimeError):
            raise SemanticInferenceUnavailable("Optional local inference dependencies unavailable") from None

        self.torch = torch
        self.spec = spec
        self.hypotheses = hypotheses
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(spec["tokenizer"], revision=spec["revision"], local_files_only=True)
            self.model = AutoModelForSequenceClassification.from_pretrained(spec["model"], revision=spec["revision"], local_files_only=True).to("cpu").eval()
        except (OSError, ValueError, RuntimeError, TypeError, AttributeError):
            raise SemanticInferenceUnavailable("Pinned local model is unavailable") from None
        try:
            self.indices = {str(value).lower(): int(key) for key, value in self.model.config.id2label.items()}
        except (AttributeError, TypeError, ValueError):
            raise SemanticInferenceUnavailable("Unexpected model labels") from None
        if (set(self.indices) != set(LABELS) or set(self.indices.values()) != {0, 1, 2}
                or len(self.model.config.id2label) != 3
                or type(getattr(self.model.config, "num_labels", 3)) is not int
                or getattr(self.model.config, "num_labels", 3) != 3
                or any(type(key) not in (int, str) or (type(key) is str and key not in {"0", "1", "2"})
                       for key in self.model.config.id2label)):
            raise SemanticInferenceUnavailable("Unexpected model labels")

    def score(self, text: str, indicator: str) -> list[dict]:
        try:
            hypotheses = self.hypotheses[indicator]
            tokens = self.tokenizer([text] * 3, hypotheses, truncation=False, padding=True, return_tensors="pt")
            shape = tokens["input_ids"].shape
            if len(shape) != 2 or shape[0] != 3 or shape[1] < 1:
                raise ValueError("Unexpected token shape")
            if shape[1] > self.spec["max_tokens"]:
                raise SemanticInferenceUnavailable("Evidence exceeds token limit; abstain without truncation")
        except SemanticInferenceUnavailable:
            raise
        except (KeyError, RuntimeError, ValueError, TypeError, IndexError, AttributeError):
            raise SemanticInferenceUnavailable("Pinned semantic tokenization failed") from None
        try:
            with self.torch.inference_mode():
                values = self.torch.softmax(self.model(**tokens).logits, dim=-1).cpu().tolist()
            if len(values) != 3 or any(len(row) != 3 for row in values):
                raise ValueError("Unexpected logits shape")
            return validate_scores([{label: float(row[index]) for label, index in self.indices.items()} for row in values])
        except (RuntimeError, ValueError, TypeError, IndexError, AttributeError):
            raise SemanticInferenceUnavailable("Pinned semantic inference failed") from None


def generate_candidates(record: DatasetRecord, scorer: SemanticScorer,
                        detector_context: DetectorContext | None = None) -> dict:
    if not isinstance(record, DatasetRecord):
        raise TypeError("Candidates require a canonical record with provenance")
    if not callable(getattr(scorer, "score", None)):
        raise TypeError("Candidate inference requires an explicit scorer")
    reject_excluded((record.source_dataset, record.record_id, record.provenance, record.source_metadata))
    artifact = prepare_record(record).artifact
    codebook = load_codebook()
    _, hypotheses = semantic_configuration()
    parents = {item["id"]: dim["id"] for dim in codebook["dimensions"] for item in dim["indicators"]}
    if set(hypotheses) != set(parents) or any(len(items) != 3 for items in hypotheses.values()):
        raise ValueError("Hypotheses do not match the canonical twelve-indicator contract")
    support = next(m for m in codebook["modalities"] if m["id"] == artifact.modality_id)["support_by_dimension"]
    context = detector_context if detector_context is not None else DetectorContext()
    if not isinstance(context, DetectorContext):
        raise TypeError("Independent identity evidence requires typed detector context")
    # Existing detector validates the field/offset linkage of supplied references.
    identity_reports = {report.indicator_id: report for report in
                        ConservativeTrustDetector().detect(artifact, context, ContextIndex(artifact))}
    records = {}
    for indicator, dimension in parents.items():
        item = {"dimension": dimension, "state": "abstained", "candidates": [],
                "semantic_inference_executed": False, "reason": "candidate_only_requires_independent_validation"}
        code = support[dimension]
        if code == "U" or not artifact.required_content_available or (code == "A*" and not artifact.conditional_evidence_available):
            item.update(state="unavailable", reason="required_modality_or_evidence_missing")
        elif indicator in {"impersonation", "brand_exploitation"} and (
            not identity_reports[indicator].evaluated or not any(
                ref.indicator_id == indicator and ref.delegation_audited for ref in context.identities)):
            item.update(state="unavailable", reason="independent_identity_reference_missing")
        else:
            for segment in artifact.segments:
                if not segment.text.strip() or segment.quoted:
                    continue
                # Evidence is the exact original field unit, never normalized offsets.
                original = record.artifact_input.get(segment.field)
                if (not isinstance(original, str) or type(segment.start) is not int
                        or type(segment.end) is not int or not 0 <= segment.start < segment.end <= len(original)
                        or original[segment.start:segment.end] != segment.text):
                    raise ValueError("Evidence does not belong to the original field")
                try:
                    scores = validate_scores(scorer.score(segment.text, indicator))
                except SemanticInferenceUnavailable:
                    item["reason"] = "semantic_inference_unavailable_or_token_limit"
                    continue
                item["semantic_inference_executed"] = True
                item["candidates"].append({
                    "evidence": {"field": segment.field, "location": segment.location,
                                 "start": segment.start, "end": segment.end, "text": segment.text},
                    "scores": scores, "requires_context_review": bool(REVIEW_CONTEXT.search(segment.text)),
                    "decision": "candidate_only", "confidence_calibrated": False,
                })
        records[indicator] = item
    return {"contract_version": CONTRACT_VERSION, "codebook_version": codebook["codebook_version"],
            "modality": artifact.modality_id,
            "dimension_availability": {dim: int(code != "U" and artifact.required_content_available
                and (code != "A*" or artifact.conditional_evidence_available)) for dim, code in support.items()},
            "representation_type": "semantic_candidate_v1", "indicator_count": len(records),
            "indicators": records, "learned_values": [None] * 4,
            "behavioral_accuracy_validated": False, "approved_for_E2_E3": False,
            "approved_for_sealed_test": False, "publishable_as_validated_results": False}
