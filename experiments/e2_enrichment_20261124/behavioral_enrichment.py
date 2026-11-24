
from ml.se_brl.representation import BrlRepresentation

def behavioral_features(extraction):
    rep = BrlRepresentation(extraction)
    baseline = rep.deterministic_slots

    indicators = {}
    evidence = {}

    for item in extraction.indicators:
        key = item.indicator_id
        evaluated = item.evaluation_status == "rule_evaluated"

        indicators[key + "_supported"] = (
            int(item.evidence_state == "supported")
            if evaluated else None
        )

        indicators[key + "_available"] = (
            0 if item.evidence_state == "unavailable"
            else 1 if evaluated else None
        )

        evidence[key + "_evidence_count"] = (
            len({
                (e.span.field, e.span.start, e.span.end)
                for e in item.evidence
            })
            if evaluated else None
        )

    return {
        "baseline": dict(zip(
            rep.deterministic_names, baseline, strict=True
        )),
        "indicator": indicators,
        "evidence": evidence,
    }
