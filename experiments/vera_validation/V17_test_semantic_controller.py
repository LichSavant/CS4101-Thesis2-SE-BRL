import unittest
from V17_semantic_controller import infer


class FakeSemantic:
    def __init__(self, label="entailment"):
        self.label = label
        self.calls = []

    def score(self, text, indicator):
        self.calls.append((text, indicator))
        return [
            {
                key: 0.90 if key == self.label else 0.05
                for key in ("entailment", "neutral", "contradiction")
            }
            for _ in range(3)
        ]


class IntegrationTests(unittest.TestCase):
    def test_real_deadline_candidate(self):
        model = FakeSemantic()
        result = infer(
            "Submit the report before midnight.",
            semantic=model
        )
        self.assertEqual(
            result["indicators"]["urgency"]["state"], "supported"
        )
        self.assertIn(
            ("Submit the report before midnight.", "urgency"),
            model.calls
        )

    def test_routine_request_does_not_run_nli(self):
        model = FakeSemantic()
        result = infer("Please submit the report.", semantic=model)
        self.assertEqual(
            result["indicators"]["urgency"]["state"], "abstained"
        )
        self.assertEqual(model.calls, [])

    def test_unrelated_clauses_do_not_run_nli(self):
        model = FakeSemantic()
        result = infer(
            "Submit the report. Your password is secure.",
            semantic=model
        )
        self.assertEqual(
            result["indicators"]["credential_sensitive_data_request"]["state"],
            "abstained"
        )
        self.assertEqual(model.calls, [])

    def test_mixed_prohibition_targets_active_clause(self):
        model = FakeSemantic()
        text = "Never share your password, but send your OTP."
        result = infer(text, semantic=model)
        self.assertEqual(
            result["indicators"]["credential_sensitive_data_request"]["state"],
            "supported"
        )
        self.assertTrue(any(
            "send your OTP" in candidate
            for candidate, indicator in model.calls
            if indicator == "credential_sensitive_data_request"
        ))

    def test_quoted_request_abstains(self):
        model = FakeSemantic()
        result = infer(
            'The poster says "Provide your password."',
            semantic=model
        )
        self.assertEqual(
            result["indicators"]["credential_sensitive_data_request"]["state"],
            "abstained"
        )
        self.assertEqual(model.calls, [])

    def test_neutral_semantics_abstains(self):
        model = FakeSemantic("neutral")
        result = infer(
            "Provide your account password.",
            semantic=model
        )
        self.assertEqual(
            result["indicators"]["credential_sensitive_data_request"]["state"],
            "abstained"
        )

    def test_unobservable_url_avoids_model(self):
        model = FakeSemantic()
        result = infer(
            "https://example.invalid",
            modality="standalone_url",
            semantic=model
        )
        self.assertEqual(model.calls, [])
        self.assertTrue(all(
            record["state"] == "unavailable"
            for record in result["indicators"].values()
        ))

    def test_unimplemented_indicator_abstains(self):
        model = FakeSemantic()
        result = infer("I am your manager.", semantic=model)
        self.assertEqual(
            result["indicators"]["authority"]["state"],
            "abstained"
        )
        self.assertEqual(model.calls, [])


if __name__ == "__main__":
    unittest.main()
