"""SE-BRL V17 contextual evidence eligibility.

Development-only necessary-condition checks.
Not a validated semantic classifier or independent ground truth.
"""
import re

ACTION = re.compile(
    r"\b(?:send|share|provide|enter|submit|disclose|give|type)\b",
    re.I
)
CREDENTIAL = re.compile(
    r"\b(?:password|passcode|otp|pin|verification code|"
    r"login credentials|recovery code)\b",
    re.I
)
TIME = re.compile(
    r"\b(?:before|by|within|until)\s+"
    r"(?:midnight|tonight|tomorrow|today|"
    r"\d+\s*(?:minutes?|hours?|days?))\b|"
    r"\b(?:immediately|asap|right away)\b",
    re.I
)
PROHIBITION = re.compile(
    r"\b(?:never|do not|don't|must not|should not)\s+"
    r"(?:(?:\w+)\s+){0,2}"
    r"(?:send|share|provide|enter|submit|disclose|give|type)\b",
    re.I
)
META = re.compile(
    r"\b(?:security awareness|training example|educational example|"
    r"classroom exercise|hypothetical example)\b",
    re.I
)


def clauses(text):
    """Return original-text offsets, splitting simple contrast clauses."""
    for match in re.finditer(r"[^.!?;\n]+[.!?;]?", text):
        raw = match.group()
        pieces = list(re.finditer(
            r".+?(?=\s*,?\s+but\s+|$)", raw, re.I
        ))
        if not pieces:
            continue

        for piece in pieces:
            content = piece.group()
            start = match.start() + piece.start()
            content = re.sub(r"^\s*,?\s*but\s+", "", content, flags=re.I)
            start = match.start() + piece.end() - len(content)
            content = content.strip()
            start += len(text[start:match.start() + piece.end()]) - len(
                text[start:match.start() + piece.end()].lstrip()
            )
            if content:
                end = start + len(content)
                if text[start:end] == content:
                    yield {"text": content, "start": start, "end": end}


def assess(text, indicator):
    text = str(text or "")

    if not text.strip():
        return {"eligibility": "unavailable", "evidence": []}

    if indicator not in (
        "urgency", "credential_sensitive_data_request"
    ):
        return {"eligibility": "unresolved", "evidence": []}

    eligible = []
    for clause in clauses(text):
        sentence = clause["text"]

        # Conservative scope: quoted, interrogative, and instructional
        # examples require additional semantic/contextual evaluation.
        if '"' in sentence or "'" in sentence:
            continue
        if "?" in sentence or META.search(sentence):
            continue
        if PROHIBITION.search(sentence):
            continue

        if indicator == "urgency":
            # A temporal cue alone is insufficient; there must also
            # be an explicit addressed action cue in the same clause.
            ok = bool(TIME.search(sentence) and ACTION.search(sentence))
        else:
            # These are necessary lexical conditions, NOT proof that
            # the requested action semantically targets the credential.
            ok = bool(ACTION.search(sentence) and CREDENTIAL.search(sentence))

        if ok:
            eligible.append(clause)

    for span in eligible:
        if text[span["start"]:span["end"]] != span["text"]:
            raise ValueError("Evidence offset mismatch")

    return {
        "eligibility": "eligible" if eligible else "unresolved",
        "evidence": eligible
    }
