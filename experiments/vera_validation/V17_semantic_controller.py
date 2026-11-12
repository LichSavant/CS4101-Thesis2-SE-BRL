"""Development-only contextual, constraint-governed NLI controller.

Not calibrated. Not approved for E2/E3 or sealed-test evaluation.
"""
from V13D_hybrid_extractor import SemanticNLI, _load_codebook
from V15_autonomous_inference import decision_labels
from V17_contextual_constraints import assess

TEXT_MODALITIES = {
    "content_bearing_email",
    "content_bearing_webpage",
}


def infer(text, modality="content_bearing_email", semantic=None):
    text = str(text or "")
    _, dimensions = _load_codebook()

    records = {}

    for indicator, dimension in dimensions.items():
        record = {
            "state": "abstained",
            "dimension": dimension,
            "evidence": [],
            "semantic_inference_executed": False,
            "reason": "insufficient verified evidence",
        }

        if not text.strip() or modality not in TEXT_MODALITIES:
            record["state"] = "unavailable"
            record["reason"] = "content evidence unavailable"

        elif indicator in ("impersonation", "brand_exploitation"):
            record["state"] = "unavailable"
            record["reason"] = "identity evidence contract not implemented"

        else:
            eligibility = assess(text, indicator)
            candidates = eligibility["evidence"]

            if eligibility["eligibility"] == "eligible" and candidates:
                if semantic is None:
                    semantic = SemanticNLI()

                for candidate in candidates:
                    scores = semantic.score(
                        candidate["text"], indicator
                    )
                    labels = decision_labels(scores)
                    record["semantic_inference_executed"] = True

                    # Provisional, uncalibrated decision rule.
                    if labels.count("entailment") >= 1:
                        record["state"] = "supported"
                        record["evidence"].append(candidate)

                if record["state"] != "supported":
                    record["reason"] = "semantic evidence inconclusive"
                else:
                    record["reason"] = (
                        "provisional contextual and semantic support"
                    )

        for span in record["evidence"]:
            assert text[span["start"]:span["end"]] == span["text"]

        records[indicator] = record

    return {
        "mode": "v17_contextual_semantic_development",
        "behavioral_accuracy_validated": False,
        "policy_frozen": False,
        "indicators": records,
    }
