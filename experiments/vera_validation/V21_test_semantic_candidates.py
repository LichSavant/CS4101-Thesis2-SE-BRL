from V21_semantic_candidates import generate_candidates


class FakeSemantic:
    def __init__(self):
        self.calls = []

    def score(self, text, indicator):
        self.calls.append((text, indicator))
        return [
            {
                "entailment": 0.1,
                "neutral": 0.8,
                "contradiction": 0.1,
            }
            for _ in range(3)
        ]


def test_all_indicators_represented():
    model = FakeSemantic()
    report = generate_candidates("Review the notice.", semantic=model)
    assert report["indicator_count"] == 12
    assert len(report["indicators"]) == 12
    assert len(model.calls) == 10
    assert all(
        record["state"] != "supported"
        for record in report["indicators"].values()
    )


def test_evidence_offsets():
    text = "  Submit the report. Send your password."
    report = generate_candidates(text, semantic=FakeSemantic())
    for item in report["indicators"].values():
        for candidate in item["candidates"]:
            span = candidate["evidence"]
            assert text[span["start"]:span["end"]] == span["text"]


def test_url_does_not_run_model():
    model = FakeSemantic()
    report = generate_candidates(
        "https://example.invalid",
        modality="standalone_url",
        semantic=model,
    )
    assert model.calls == []
    assert all(
        item["state"] == "unavailable"
        for item in report["indicators"].values()
    )


def test_identity_requires_independent_evidence():
    report = generate_candidates(
        "I represent your bank.",
        semantic=FakeSemantic(),
    )
    for indicator in ("impersonation", "brand_exploitation"):
        assert report["indicators"][indicator]["state"] == "unavailable"


def test_negation_requires_review():
    report = generate_candidates(
        "Never share your password.",
        semantic=FakeSemantic(),
    )
    candidates = report["indicators"][
        "credential_sensitive_data_request"
    ]["candidates"]
    assert candidates
    assert candidates[0]["requires_context_review"]
    assert report["indicators"][
        "credential_sensitive_data_request"
    ]["state"] == "abstained"


def test_unknown_modality_rejected():
    import pytest
    with pytest.raises(ValueError):
        generate_candidates(
            "Example",
            modality="unknown",
            semantic=FakeSemantic(),
        )
