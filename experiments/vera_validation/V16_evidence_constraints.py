"""Development-only evidence eligibility checks for SE-BRL.

These checks are necessary-condition guards, not semantic ground truth.
Do not use them as independent labels or final E2/E3 features.
"""
import re

TIME_PRESSURE = re.compile(
    r"\b(?:before|by|within|until)\s+"
    r"(?:midnight|tonight|tomorrow|today|"
    r"\d+\s*(?:minutes?|hours?|days?))\b"
    r"|\b(?:urgent|immediately|asap|right away)\b",
    re.I
)

CREDENTIAL = re.compile(
    r"\b(?:password|passcode|otp|pin|"
    r"verification code|login credentials|"
    r"account recovery answers)\b",
    re.I
)

REQUEST = re.compile(
    r"\b(?:provide|send|share|enter|submit|"
    r"disclose|give|supply|type)\b",
    re.I
)

PROHIBITION = re.compile(
    r"\b(?:never|do not|don't|should not|must not)\s+"
    r"(?:send|share|provide|enter|submit|disclose|give)\b",
    re.I
)

EDUCATIONAL = re.compile(
    r"\b(?:security awareness lesson|training example|"
    r"educational example|classroom exercise)\b",
    re.I
)


def assess_evidence(text, indicator):
    text = str(text or "")

    if not text.strip():
        return {
            "eligibility": "unavailable",
            "evidence": [],
            "reason": "empty text"
        }

    if EDUCATIONAL.search(text):
        return {
            "eligibility": "unresolved",
            "evidence": [],
            "reason": "educational context requires semantic review"
        }

    if indicator == "urgency":
        match = TIME_PRESSURE.search(text)

        if match:
            return {
                "eligibility": "eligible",
                "evidence": [{
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end()
                }],
                "reason": "observable time-pressure cue"
            }

        return {
            "eligibility": "unresolved",
            "evidence": [],
            "reason": "no recognized time-pressure cue"
        }

    if indicator == "credential_sensitive_data_request":
        if PROHIBITION.search(text):
            return {
                "eligibility": "blocked",
                "evidence": [],
                "reason": "explicit prohibition; mixed contexts need review"
            }

        credential = CREDENTIAL.search(text)
        request = REQUEST.search(text)

        if credential and request:
            return {
                "eligibility": "eligible",
                "evidence": [{
                    "text": text,
                    "start": 0,
                    "end": len(text)
                }],
                "reason": "request and sensitive-data cues coexist"
            }

        return {
            "eligibility": "unresolved",
            "evidence": [],
            "reason": "required request context not established"
        }

    return {
        "eligibility": "unresolved",
        "evidence": [],
        "reason": "indicator-specific constraint not yet implemented"
    }
