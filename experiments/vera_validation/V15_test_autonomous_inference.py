import unittest

from V15_autonomous_inference import infer


class FakeSemantic:
    def __init__(self, label):
        self.label = label
        self.calls = 0

    def score(self, text, indicator):
        self.calls += 1
        return [
            {
                key: 0.9 if key == self.label else 0.05
                for key in (
                    "entailment", "neutral", "contradiction"
                )
            }
            for _ in range(3)
        ]


class TestV15(unittest.TestCase):

    def test_semantic_support(self):
        result = infer(
            "Please submit the document.",
            semantic=FakeSemantic("entailment")
        )
        self.assertEqual(
            result["indicators"]["urgency"]["state"],
            "supported"
        )
        self.assertFalse(
            result["behavioral_accuracy_validated"]
        )

    def test_neutral_abstention(self):
        result = infer(
            "Please submit the document.",
            semantic=FakeSemantic("neutral")
        )
        self.assertEqual(
            result["indicators"]["urgency"]["state"],
            "abstained"
        )

    def test_semantic_contradiction(self):
        result = infer(
            "Please submit the document.",
            semantic=FakeSemantic("contradiction")
        )
        self.assertEqual(
            result["indicators"]["urgency"]["state"],
            "absent"
        )

    def test_missing_modality_evidence(self):
        model = FakeSemantic("entailment")
        result = infer(
            "https://example.invalid",
            modality="standalone_url",
            semantic=model
        )
        self.assertEqual(model.calls, 0)
        self.assertTrue(all(
            r["state"] == "unavailable"
            for r in result["indicators"].values()
        ))

    def test_identity_evidence(self):
        result = infer(
            "Your bank requests a response.",
            semantic=FakeSemantic("entailment")
        )
        self.assertEqual(
            result["indicators"]["impersonation"]["state"],
            "unavailable"
        )

    def test_contextual_abstention(self):
        result = infer(
            "Never share your password.",
            semantic=FakeSemantic("entailment")
        )
        self.assertEqual(
            result["indicators"][
                "credential_sensitive_data_request"
            ]["state"],
            "abstained"
        )


if __name__ == "__main__":
    unittest.main()
