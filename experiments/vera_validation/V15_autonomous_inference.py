"""Experimental SE-BRL semantic-first autonomous inference.

Development policy only; not calibrated or independently validated.
Does not modify any historical datasets, features, or experiments.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from V13D_hybrid_extractor import SemanticNLI, _load_codebook

HERE = Path(__file__).resolve().parent
POLICY = HERE / "V15_candidate_policy.json"


def segments(text):
    result = []
    for m in re.finditer(r"[^.!?;\n]+(?:[.!?;\n]|$)", text):
        raw = m.group()
        start = m.start() + len(raw) - len(raw.lstrip())
        end = m.start() + len(raw.rstrip())
        if end > start:
            result.append({
                "text": text[start:end],
                "start": start,
                "end": end
            })
    return result


def decision_labels(scores):
    labels = ("entailment", "neutral", "contradiction")
    if len(scores) != 3:
        raise ValueError("Expected three frozen hypotheses")

    result = []
    for score in scores:
        values = [float(score[x]) for x in labels]
        if not all(math.isfinite(x) and 0 <= x <= 1 for x in values):
            raise ValueError("Invalid NLI scores")
        if abs(sum(values) - 1) > 0.001:
            raise ValueError("Invalid NLI normalization")
        result.append(labels[values.index(max(values))])
    return result


def advisory_context(text):
    return bool(re.search(
        r"\b(?:never|do not|don't|should not|must not)\s+"
        r"(?:send|share|provide|enter|disclose|give)\b|"
        r"\b(?:security awareness lesson|training example)\b",
        text, flags=re.I
    ))


def infer(text, modality="content_bearing_email",
          semantic=None, identity_evidence=None):
    text = str(text or "")
    config = json.loads(POLICY.read_text(encoding="utf-8"))
    if config["status"] != "candidate_unvalidated":
        raise ValueError("Unrecognized policy status")

    codebook, indicator_dimensions = _load_codebook()
    modalities = {x["id"] for x in codebook["modalities"]}
    if modality not in modalities:
        raise ValueError("Unknown modality")

    parts = segments(text)
    results = {}

    for indicator, dimension in indicator_dimensions.items():
        record = {
            "state": "abstained",
            "dimension": dimension,
            "evidence": [],
            "reason": "insufficient semantic evidence",
            "semantic_inference_executed": False
        }

        if modality in (
            "standalone_url", "engineered_technical_record"
        ) or not parts:
            record["state"] = "unavailable"
            record["reason"] = "required textual evidence unavailable"

        elif indicator in ("impersonation", "brand_exploitation") and not (
            isinstance(identity_evidence, dict)
            and identity_evidence.get("verified") is True
        ):
            record["state"] = "unavailable"
            record["reason"] = "verified identity evidence missing"

        else:
            if semantic is None:
                semantic = SemanticNLI()

            candidates = []
            for part in parts:
                scores = semantic.score(part["text"], indicator)
                labels = decision_labels(scores)

                candidates.append({
                    "span": part,
                    "nli_top_labels": labels,
                    "entailment_votes": labels.count("entailment"),
                    "contradiction_votes": labels.count("contradiction")
                })

            record["semantic_inference_executed"] = True
            record["candidates"] = candidates

            supported = [
                c for c in candidates
                if c["entailment_votes"] >= config["support_votes"]
            ]

            contradiction = all(
                c["contradiction_votes"] >= config["absence_votes"]
                for c in candidates
            )

            if supported and not advisory_context(text):
                record["state"] = "supported"
                record["evidence"] = [c["span"] for c in supported]
                record["reason"] = "provisional semantic support"

            elif contradiction and not supported:
                record["state"] = "absent"
                record["reason"] = "provisional semantic contradiction"

            elif advisory_context(text):
                record["reason"] = "context requires abstention"

        for span in record["evidence"]:
            assert text[span["start"]:span["end"]] == span["text"]

        if record["state"] == "supported":
            assert record["evidence"]
        else:
            assert not record["evidence"]

        results[indicator] = record

    return {
        "mode": "semantic_first_constraint_governed_v15",
        "policy_status": "candidate_unvalidated",
        "behavioral_accuracy_validated": False,
        "policy_sha256": hashlib.sha256(
            POLICY.read_bytes()
        ).hexdigest(),
        "indicators": results
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True)
    p.add_argument(
        "--modality", default="content_bearing_email"
    )
    args = p.parse_args()

    output = infer(args.text, args.modality)
    print(json.dumps(output, indent=2))
