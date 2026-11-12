import unittest
from V17_contextual_constraints import assess


class ContextualTests(unittest.TestCase):
    def check(self, text, indicator, expected):
        result = assess(text, indicator)
        self.assertEqual(result["eligibility"], expected)
        for span in result["evidence"]:
            self.assertEqual(
                text[span["start"]:span["end"]],
                span["text"]
            )

    def test_routine_request(self):
        self.check("Please submit the report.", "urgency", "unresolved")

    def test_deadline(self):
        self.check("Submit the report before midnight.", "urgency", "eligible")

    def test_historical_deadline(self):
        self.check("The deadline was yesterday.", "urgency", "unresolved")

    def test_medical_urgency(self):
        self.check("The patient needs urgent care.", "urgency", "unresolved")

    def test_negated_request(self):
        self.check("Never share your password.",
                   "credential_sensitive_data_request", "unresolved")

    def test_password_request(self):
        self.check("Send your password now.",
                   "credential_sensitive_data_request", "eligible")

    def test_unrelated_clauses(self):
        self.check("Submit the report. Your password is secure.",
                   "credential_sensitive_data_request", "unresolved")

    def test_mixed_prohibition(self):
        self.check("Never share your password, but send your OTP.",
                   "credential_sensitive_data_request", "eligible")

    def test_quoted_request(self):
        self.check('The poster says "Provide your password."',
                   "credential_sensitive_data_request", "unresolved")

    def test_question(self):
        self.check("Why would anyone ask you to share a password?",
                   "credential_sensitive_data_request", "unresolved")

    def test_empty_text(self):
        self.check("", "urgency", "unavailable")

    def test_unimplemented_indicator(self):
        self.check("I am your manager.", "impersonation", "unresolved")


if __name__ == "__main__":
    unittest.main()
