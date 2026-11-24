"""Reusable conservative context guards with source-preserving character positions."""

import re
from bisect import bisect_left, bisect_right
from collections import defaultdict

from ml.preprocessing import PreparedArtifact, TextEvidence

CONTEXT_CHARS = 320
NEGATION = re.compile(r"\b(?:not|never|don['’]t|shouldn['’]t|mustn['’]t|cannot|can['’]t|no need to|avoid|without)\b", re.I)
EDUCATIONAL = re.compile(r"\b(?:examples?|scamm?ers?|scams?|phishing|training|beware|warning|fraud|security awareness)\b", re.I)
REPORTED = re.compile(r"\b(?:says?|said|told|claims|claimed|they claim|reads?|wrote|writes?|reported|according to|pretend(?:s|ing)?)\b", re.I)
COUNTEREXAMPLE = re.compile(r"\b(?:not true|false|ignore|disregard)\b", re.I)
QUOTATION = re.compile(r'''"[^"\n]*"|“[^”]*”|‘[^’]*’|(?<!\w)'[^'\n]*'(?!\w)''')
PUNCTUATION = re.compile(r"[.!?]")


class ContextIndex:
    """Join each field once; index punctuation/quotes once, not for every match."""

    def __init__(self, artifact: PreparedArtifact) -> None:
        chunks: dict[str, list[str]] = defaultdict(list)
        lengths: dict[str, int] = defaultdict(int)
        self.positions: dict[TextEvidence, int] = {}
        for segment in artifact.segments:
            if segment.quoted or segment in self.positions:
                continue
            self.positions[segment] = lengths[segment.field]
            chunks[segment.field].append(segment.text + "\n")
            lengths[segment.field] += len(segment.text) + 1
        self.fields = {field: "".join(parts) for field, parts in chunks.items()}
        self.punctuation = {field: tuple(m.start() for m in PUNCTUATION.finditer(text))
                            for field, text in self.fields.items()}
        self.quotes = {field: tuple((m.start(), m.end()) for m in QUOTATION.finditer(text))
                       for field, text in self.fields.items()}
        self.quote_starts = {field: tuple(start for start, _ in ranges) for field, ranges in self.quotes.items()}

    def suppressed(self, segment: TextEvidence, start: int, end: int,
                   *, allow_negative_instruction: bool = False) -> bool:
        if segment.quoted or segment not in self.positions:
            return True
        offset = self.positions[segment]
        start, end = offset + start, offset + end
        text = self.fields[segment.field]
        punctuation = self.punctuation[segment.field]
        before = bisect_left(punctuation, start)
        after = bisect_left(punctuation, end)
        left = punctuation[before - 1] + 1 if before else 0
        right = punctuation[after] if after < len(punctuation) else len(text)
        context = text[max(left, start - CONTEXT_CHARS):min(right, end + CONTEXT_CHARS)]
        quote_index = bisect_right(self.quote_starts[segment.field], end - 1) - 1
        if quote_index >= 0 and self.quotes[segment.field][quote_index][1] > start:
            return True
        # Unclosed double quotes are ambiguous and must not expose quoted cues.
        if text[max(left, start - CONTEXT_CHARS):start].count('"') % 2:
            return True
        # Educational or reported framing applies only to the matched
        # sentence and its immediately adjacent sentences.
        nearby_start = max(0, start - CONTEXT_CHARS)
        nearby_end = min(len(text), end + CONTEXT_CHARS)
        framing_start = max(
            nearby_start,
            punctuation[before - 2] + 1 if before >= 2 else 0,
        )
        framing_end = min(
            nearby_end,
            punctuation[after + 1] + 1 if after + 1 < len(punctuation) else len(text),
        )
        framing = text[framing_start:framing_end]
        # Scope contextual suppression to the sentence containing the match.
        # Adjacent sentences must not suppress independent behavioral evidence.

        previous = text[framing_start:left].strip()
        following = text[right:framing_end].strip(" .!?\r\n")

        if re.fullmatch(
            r"security awareness[.!:]?",
            previous,
            re.I
        ):
            return True

        if re.fullmatch(
            r"this is (?:a|an) (?:phishing|scam|training) example",
            following,
            re.I
        ):
            return True


        sentence = text[left:right]
        if EDUCATIONAL.search(sentence) or REPORTED.search(sentence):
            return True
        return bool(
            (COUNTEREXAMPLE if allow_negative_instruction else NEGATION).search(sentence)
        )
