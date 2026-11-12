import unittest
from V16_evidence_constraints import assess_evidence


class ConstraintTests(unittest.TestCase):

    def check(self, text, indicator, expected):
        result = assess_evidence(text, indicator)
        self.assertEqual(result["eligibility"], expected)
        for span in result["evidence"]:
            self.assertEqual(
                text[span["start"]:span["end"]],
                span["text"]
            )

    def test_no_deadline(self):
        self.check(
            "Please submit the document.",
            "urgency", "unresolved"
        )

    def test_explicit_deadline(self):
        self.check(
            "Submit the document before midnight.",
            "urgency", "eligible"
        )

    def test_password_warning(self):
        self.check(
            "Never share your password.",
            "credential_sensitive_data_request",
            "blocked"
        )

    def test_password_request(self):
        self.check(
            "Provide your account password.",
            "credential_sensitive_data_request",
            "eligible"
        )

    def test_educational_context(self):
        self.check(
            "This security awareness lesson discusses urgency.",
            "urgency", "unresolved"
        )

    def test_empty_evidence(self):
        self.check("", "urgency", "unavailable")

    def test_unimplemented_indicator(self):
        self.check(
            "The sender claims to be the bank.",
            "impersonation", "unresolved"
        )


if __name__ == "__main__":
    unittest.main()
