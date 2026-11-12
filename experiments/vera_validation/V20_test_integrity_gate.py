import pytest
from V20_inference_integrity_gate import run, assert_research_ready


class FakeSemantic:
    def score(self, text, indicator):
        return [
            {
                "entailment": 0.9,
                "neutral": 0.05,
                "contradiction": 0.05,
            }
            for _ in range(3)
        ]


def test_all_twelve_returned():
    report = run(
        "Submit your report before midnight.",
        semantic=FakeSemantic(),
    )
    assert report["indicator_count"] == 12
    assert report["implemented_indicator_count"] == 2
    assert len(report["pending_indicators"]) == 10


def test_positive_evidence_is_grounded():
    text = "Submit your report before midnight."
    report = run(text, semantic=FakeSemantic())
    result = report["indicators"]["urgency"]
    assert result["state"] == "supported"
    assert result["semantic_inference_executed"]
    for span in result["evidence"]:
        assert text[span["start"]:span["end"]] == span["text"]


def test_url_must_remain_unavailable():
    report = run(
        "https://example.invalid",
        modality="standalone_url",
        semantic=FakeSemantic(),
    )
    assert all(
        r["state"] == "unavailable"
        for r in report["indicators"].values()
    )


def test_gate_rejects_unvalidated_results():
    report = run(
        "Please submit the report.",
        semantic=FakeSemantic(),
    )
    with pytest.raises(RuntimeError):
        assert_research_ready(report)


def test_unknown_modality_rejected():
    with pytest.raises(ValueError):
        run("Example", modality="unknown")
