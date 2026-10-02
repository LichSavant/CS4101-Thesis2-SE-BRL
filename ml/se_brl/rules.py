"""Versioned English candidate rules; not validated behavioral detectors.

Definitions reference canonical IDs, never define or rename the taxonomy.
Identity/brand/authority adjudication is deliberately deferred.
"""

from dataclasses import dataclass

RULESET_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class Rule:
    rule_id: str
    indicator_id: str
    pattern: str
    allow_negative_instruction: bool = False


RULES = (
    Rule("pressure.immediate_action", "urgency",
         r"\b(?:act now|(?:click|reply|respond|verify|pay|submit)\b.{0,40}?\b(?:immediately|right now))\b"),
    Rule("pressure.adverse_consequence", "fear_threat",
         r"\b(?:your (?:account|access) will be (?:suspended|terminated|locked)|you will (?:lose access|face penalties))\b"),
    Rule("pressure.limited_action", "scarcity",
         r"\b(?:act|claim|buy|order)\b.{0,60}?\b(?:before (?:it|they) (?:expires?|runs? out)|only \d+ (?:left|remaining)|limited time)\b"),
    Rule("lure.information_gap", "curiosity",
         r"\b(?:click|open)\b.{0,40}?\b(?:find out|see who|discover (?:who|what)|reveal)\b"),
    Rule("lure.claim_benefit", "reward_lure",
         r"\b(?:click|reply|claim)\b.{0,45}?\b(?:your|a) (?:prize|reward|free gift|refund)\b"),
    Rule("trust.prevent_verification", "confidentiality_isolation",
         r"\b(?:do not|don't|never) (?:tell|contact|consult) (?:anyone|your (?:bank|manager|IT department))\b",
         allow_negative_instruction=True),
    Rule("action.interact", "call_to_action",
         r"\b(?:click (?:here|the link|this link)|(?:visit|open) (?:this|the) (?:website|link)|download (?:the|this) (?:file|attachment)|reply (?:to this|with)|submit (?:your|the) (?:details|password|information))\b"),
    Rule("action.disclose_sensitive", "credential_sensitive_data_request",
         r"\b(?:send|share|provide|submit|enter|confirm)\s+(?:(?:us|me)\s+)?(?:your|the)\s+(?:password|login credentials|verification code|credit card number|social security number)\b"),
    Rule("action.transfer_money", "financial_action_request",
         r"\b(?:transfer (?:the |your )?(?:funds|money)|send (?:us |me )?(?:money|payment)|pay (?:the|this) (?:fee|invoice)|purchase (?:a |the )?gift cards?|update your bank account)\b"),
)

DEFERRED_INDICATORS = frozenset({"authority", "impersonation", "brand_exploitation"})
