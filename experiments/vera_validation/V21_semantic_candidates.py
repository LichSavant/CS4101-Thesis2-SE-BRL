import re

from V13D_hybrid_extractor import SemanticNLI, _load_codebook
from V15_autonomous_inference import decision_labels

TEXT_MODALITIES = {
    "content_bearing_email",
    "content_bearing_webpage",
}
IDENTITY_DEPENDENT = {
    "impersonation",
    "brand_exploitation",
}
CONTEXT_FLAGS = re.compile(
    r'\b(?:never|do not|don.t|should not|must not|'
    r'training|lesson|example|hypothetical|'
    r'quoted|allegedly)\b',
    re.I,
)


def evidence_units(text):
    for match in re.finditer(r"[^.!?;\n]+[.!?;\n]?", text):
        content = match.group()
        stripped = content.strip()
        if not stripped:
            continue
        offset = len(content) - len(content.lstrip())
        start = match.start() + offset
        end = start + len(stripped)
        yield {
            "text": stripped,
            "start": start,
            "end": end,
        }


def generate_candidates(
    text,
    modality="content_bearing_email",
    semantic=None,
    identity_evidence=None,
):
    text = str(text or "")
    codebook, dimensions = _load_codebook()
    valid_modalities = {item["id"] for item in codebook["modalities"]}

    if modality not in valid_modalities:
        raise ValueError("Unsupported modality")

    units = list(evidence_units(text))
    outputs = {}

    for indicator, dimension in dimensions.items():
        item = {
            "dimension": dimension,
            "state": "abstained",
            "candidates": [],
            "reason": "candidate inference is not a validated decision",
        }

        if not text.strip() or modality not in TEXT_MODALITIES:
            item["state"] = "unavailable"
            item["reason"] = "content evidence unavailable"

        elif indicator in IDENTITY_DEPENDENT and not (
            isinstance(identity_evidence, dict)
            and identity_evidence.get("verified") is True
        ):
            item["state"] = "unavailable"
            item["reason"] = "independent identity evidence unavailable"

        else:
            if semantic is None:
                semantic = SemanticNLI()

            for unit in units:
                scores = semantic.score(unit["text"], indicator)
                if len(scores) != 3:
                    raise ValueError("Unexpected hypothesis count")

                labels = decision_labels(scores)
                if len(labels) != len(scores):
                    raise ValueError("NLI label count mismatch")

                item["candidates"].append({
                    "evidence": unit,
                    "hypothesis_labels": labels,
                    "scores": scores,
                    "requires_context_review": bool(
                        CONTEXT_FLAGS.search(unit["text"])
                        or '"' in unit["text"]
                        or "'" in unit["text"]
                        or "?" in unit["text"]
                    ),
                })

        for candidate in item["candidates"]:
            span = candidate["evidence"]
            if text[span["start"]:span["end"]] != span["text"]:
                raise ValueError("Evidence provenance mismatch")

        outputs[indicator] = item

    return {
        "mode": "v21_semantic_candidate_inference",
        "indicator_count": len(outputs),
        "behavioral_accuracy_validated": False,
        "decision_policy_approved": False,
        "approved_for_E2_E3": False,
        "indicators": outputs,
    }
