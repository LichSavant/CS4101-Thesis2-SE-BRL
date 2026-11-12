"""Experimental constraint-governed semantic inference controller.

Development prototype only. Not calibrated or independently validated.
"""
from V13D_hybrid_extractor import SemanticNLI, _load_codebook
from V15_autonomous_inference import segments, decision_labels
from V16_evidence_constraints import assess_evidence


def infer(text, modality="content_bearing_email",
          semantic=None, identity_evidence=None):
    text = str(text or "")
    codebook, dimensions = _load_codebook()

    allowed = {m["id"] for m in codebook["modalities"]}
    if modality not in allowed:
        raise ValueError("Unknown modality")

    results = {}

    for indicator, dimension in dimensions.items():
        constraint = assess_evidence(text, indicator)

        record = {
            "state": "abstained",
            "dimension": dimension,
            "evidence": [],
            "constraint": constraint["eligibility"],
            "reason": constraint["reason"],
            "semantic_inference_executed": False
        }

        if modality in ("standalone_url", "engineered_technical_record") or not text.strip():
            record["state"] = "unavailable"
            record["reason"] = "required textual evidence unavailable"

        elif indicator in ("impersonation", "brand_exploitation"):
            record["state"] = "unavailable"
            record["reason"] = "identity verification not implemented"

        elif constraint["eligibility"] in ("blocked", "unavailable"):
            record["state"] = (
                "abstained"
                if constraint["eligibility"] == "blocked"
                else "unavailable"
            )

        elif constraint["eligibility"] != "eligible":
            record["reason"] = "insufficient indicator-specific evidence"

        else:
            if semantic is None:
                semantic = SemanticNLI()

            candidates = []
            for part in segments(text):
                scores = semantic.score(part["text"], indicator)
                tops = decision_labels(scores)

                candidates.append({
                    "span": part,
                    "labels": tops,
                    "entailment_votes": tops.count("entailment")
                })

            record["semantic_inference_executed"] = True

            supported = [
                candidate for candidate in candidates
                if candidate["entailment_votes"] >= 1
            ]

            if supported:
                record["state"] = "supported"
                record["evidence"] = constraint["evidence"]
                record["reason"] = "provisional semantic support and evidence eligibility"
            else:
                record["reason"] = "semantic support not established"

        for span in record["evidence"]:
            assert text[span["start"]:span["end"]] == span["text"]

        if record["state"] == "supported" and not record["evidence"]:
            raise AssertionError("Supported decision missing evidence")

        results[indicator] = record

    return {
        "mode": "constraint_governed_semantic_prototype_v16",
        "validated_behavioral_accuracy": False,
        "policy_frozen_for_evaluation": False,
        "indicators": results
    }
