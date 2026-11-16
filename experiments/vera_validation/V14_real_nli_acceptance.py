from pathlib import Path
import hashlib
import json
import math
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from V13D_hybrid_extractor import SemanticNLI, rules_only
from V13E_review_policy import assess

CASES = [
    {
        "name": "pressure_and_action",
        "text": "Your account will be suspended unless you verify it before midnight.",
        "modality": "content_bearing_email",
        "indicators": ["urgency", "fear_threat", "call_to_action"],
    },
    {
        "name": "educational_negation",
        "text": "This security lesson says never send your password to anyone.",
        "modality": "content_bearing_email",
        "indicators": ["credential_sensitive_data_request", "call_to_action"],
    },
    {
        "name": "standalone_url_unavailable",
        "text": "https://example.invalid/login",
        "modality": "standalone_url",
        "indicators": ["urgency", "credential_sensitive_data_request"],
    },
]

def run():
    model = SemanticNLI()
    summary = []

    for case in CASES:
        original = rules_only(
            case["text"], modality=case["modality"]
        )
        reviewed = assess(
            case["text"],
            modality=case["modality"],
            semantic=model,
            indicators=case["indicators"],
        )

        assert reviewed["semantic_changes_final_labels"] is False
        assert len(reviewed["indicators"]) == 12

        for indicator, record in reviewed["indicators"].items():
            assert record["state"] == original[indicator]["state"]
            assert record["state"] in {
                "supported", "absent", "unavailable"
            }

            for span in record["evidence"]:
                assert case["text"][span["start"]:span["end"]] == span["text"]

            requested = indicator in case["indicators"]
            assessable = record["state"] != "unavailable"

            if requested and assessable:
                scores = record["nli_scores"]
                assert len(scores) == 3

                for score in scores:
                    values = [
                        float(score[k])
                        for k in ("entailment", "neutral", "contradiction")
                    ]
                    assert all(math.isfinite(x) and 0 <= x <= 1
                               for x in values)
                    assert abs(sum(values) - 1) < 0.0001
            else:
                assert "nli_scores" not in record

        summary.append({
            "case": case["name"],
            "labels_preserved": True,
            "evidence_offsets_valid": True,
            "nli_score_contract_valid": True,
            "review_required": [
                name for name, record in reviewed["indicators"].items()
                if record["needs_review"]
            ],
        })
        print("PASS:", case["name"])

    print("PASS: All semantic-review invariants")
    print("NOTE: This is an integration test, not a detection-accuracy estimate")

    report = {
        "validation_kind": "real_model_integration_smoke_test",
        "model": model.cfg["model"],
        "model_config_sha256": hashlib.sha256(
            Path(HERE / "V13_nli_hypotheses_v0.1.0.json").read_bytes()
        ).hexdigest(),
        "cases": summary,
        "human_ground_truth_validation": False,
        "classifier_improvement_established": False,
    }

    output = HERE / "V14_real_nli_integration_report.json"
    try:
        with output.open("x", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print("CREATED:", output)
    except FileExistsError:
        print("PRESERVED: Existing integration report not overwritten")

if __name__ == "__main__":
    run()
