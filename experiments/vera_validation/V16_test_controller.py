
import unittest
from V16_constraint_governed_controller import infer


class FakeSemantic:
    def __init__(self, label):
        self.label = label
        self.calls = 0

    def score(self, text, indicator):
        self.calls += 1
        return [
            {
                key: 0.9 if key == self.label else 0.05
                for key in ("entailment", "neutral", "contradiction")
            }
            for _ in range(3)
        ]


class ControllerTests(unittest.TestCase):

    def test_eligible_semantic_support(self):
        result = infer(
            "Submit the document before midnight.",
            semantic=FakeSemantic("entailment")
        )
        self.assertEqual(result["indicators"]["urgency"]["state"], "supported")

    def test_no_deadline_abstains(self):
        result = infer(
            "Please submit the document.",
            semantic=FakeSemantic("entailment")
        )
        self.assertEqual(result["indicators"]["urgency"]["state"], "abstained")

    def test_negated_password_abstains(self):
        result = infer(
            "Never share your password.",
            semantic=FakeSemantic("entailment")
        )
        self.assertEqual(
            result["indicators"]["credential_sensitive_data_request"]["state"],
            "abstained"
        )

    def test_password_request(self):
        result = infer(
            "Provide your account password.",
            semantic=FakeSemantic("entailment")
        )
        self.assertEqual(
            result["indicators"]["credential_sensitive_data_request"]["state"],
            "supported"
        )

    def test_unobservable_url(self):
        model = FakeSemantic("entailment")
        result = infer(
            "https://example.invalid",
            modality="standalone_url",
            semantic=model
        )
        self.assertEqual(model.calls, 0)
        self.assertTrue(all(
            item["state"] == "unavailable"
            for item in result["indicators"].values()
        ))

    def test_unimplemented_indicator_abstains(self):
        result = infer(
            "The director ordered an immediate response.",
            semantic=FakeSemantic("entailment")
        )
        self.assertEqual(
            result["indicators"]["authority"]["state"],
            "abstained"
        )


if __name__ == "__main__":
    unittest.main()
