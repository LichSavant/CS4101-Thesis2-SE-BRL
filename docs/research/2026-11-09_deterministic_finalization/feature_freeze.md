# Candidate deterministic feature freeze

**Technically validated candidate; scientific status Pending.** Official
`ml/se_brl/codebook.v0.1.0.json` remains `pre_freeze` and unchanged. The new
`ml/feature_freeze_candidate.v0.1.0.json` binds its exact SHA-256 and canonical
order; `ml/feature_freeze.py` rejects drift, invented approvals, forbidden E1
predictors, changed masks/order/types and inconsistent observed-text counts.
No real features were materialized. Specification references are not approvals.

Proposal §4.3.4/Tables 4.5–4.6 define dimensions, observable qualifying evidence,
exclusions and Supported/Absent/Unavailable, not psychological ground truth.
Use the [existing full indicator audit](../2026-11-05_scientific_unblocking/deterministic_codebook_audit.md)
for detailed exclusions and verified code/test traceability.

| Indicator / dimension | Current candidate rule and code | Evidence / applicability / unresolved decision |
| --- | --- | --- |
| urgency / pressure_threat_cues | rules.py pressure.immediate_action; action coupled to immediacy | Original qualifying content span; N04 broader deadline/urgent tokens differ; routine dates excluded |
| fear_threat / pressure_threat_cues | pressure.adverse_consequence | Account/access loss, penalty/suspension consequence span; distinguish neutral security information |
| scarcity / pressure_threat_cues | pressure.limited_action | Action coupled to limited availability; N04 broader offer tokens differ |
| curiosity / lure_attention_cues | lure.information_gap | Explicit information-gap inducement; ordinary informative content excluded |
| reward_lure / lure_attention_cues | lure.reward_action | Benefit/reward coupled to action; legitimate promotion/routine compensation boundaries require freeze |
| authority / trust_identity_manipulation | detectors.py ConservativeTrustDetector | Role/directive plus independent observable authorization contradiction; role word alone insufficient; N04 lexical authority differs |
| impersonation / trust_identity_manipulation | Conditional trust detector/IdentityReference | Explicit claim plus independent authorized-domain/delegation contradiction; missing reference means unassessable |
| brand_exploitation / trust_identity_manipulation | Same conditional trust detector | Misleading brand relationship, not brand mention; aligned use excluded |
| confidentiality_isolation / trust_identity_manipulation | trust.prevent_verification | Directive to conceal/avoid verification; runtime parent availability versus N04 partial aggregation unresolved |
| call_to_action / requested_action_consequence | action.interact | Observed click/reply/download/visit/submit request; structural/link coverage must be declared |
| credential_sensitive_data_request / requested_action_consequence | action.disclose_sensitive | Requested disclosure plus specified protected data; safety/educational/quoted text exclusions |
| financial_action_request / requested_action_consequence | action.transfer_money | Explicit consequential payment/transfer/purchase/account request; neutral transaction notices excluded |

Paths in the table are under `ml/se_brl/`. `extraction.py`, `assessment.py`,
`context.py`, `representation.py` supply structured states, original-field
evidence, context suppression and canonical aggregation. Existing
`test_rule_extraction.py` and `test_context_detectors.py` cover positives,
counterexamples, quotation/negation, exact spans, unavailable evidence and
independent-reference conflicts. New schema tests validate structural
traceability, not scientific validity of each detector.

Runtime has nine narrower lexical indicators plus three conditional trust ports;
N04 has ten broader lexical indicators and two placeholders. N04 normalized
snippets are not original-field offset evidence. Its specification guard remains
in place. This task changes neither implementation's meanings. A recorded
English lexical gate is not a corpus language audit; unknown language cannot be
assumed English. Do not invent translation/annotation prerequisites.

## Exact ordered predictor candidate

E1 is currently a **core candidate**, not the full approved Table 4.7 baseline:

1. `model_text`: observed normalized subject/body model view, nonempty string.
2. `conventional:text_char_count`: integer length of that exact model view.
3. `conventional:text_word_count`: integer whitespace-token count of that view.

`preprocessing.py::normalize_text` and `features.py::structural_features` are
existing derivation references. A future accepted pure dataset adapter must
preserve original evidence separately; runtime transport/privacy limits do not
become corpus eligibility by accident. Actual source-field coverage, original
boundaries and model-view assembly remain to be frozen.

E2: `pressure_threat_cues_supported`, `lure_attention_cues_supported`,
`trust_identity_manipulation_supported`, `requested_action_consequence_supported`,
then the corresponding four `_available` columns in the same dimension order.
E3: the three E1 columns followed by the eight E2 columns (eleven raw columns
before TF-IDF expansion). Every mask/support cell is an integer bit; missing
cells fail. Pair encodings: supported (1,1), assessable absent (0,1), unavailable
(0,0); (1,0) fails. No unavailable indicator becomes zero-confidence, negative
evidence or a learned behavioral z vector. Partial dimension availability remains
a scientific choice. Support/mask columns are not phishing targets.

E1 core omits relation/header/embedded-URL families listed by Table 4.7. Accept
fuller audited fields or document a scoped pilot/deviation before research claims.
Missing sender/identity/link fields remain unavailable; do not fabricate empty
URL lists or adopt current runtime zero defaults as absence evidence.

Forbidden: target/native/annotation labels, observation/original/source IDs,
hashes/locators, group/partition/fold, source/provenance/snapshot fields, language,
collection/authorization flags and source-revealing bookkeeping. Explicit
allowlists replace dtype discovery. Text/length may still carry source-era/style
shortcuts, so source-confounding diagnostics and claim limits remain required.

`validate_candidate_dataset` validates the exact core dictionary and D9 input
population plus count derivations. D9 forms E1/E2/E3 from the **same** observation
objects and supplied folds. Synthetic tests check these boundaries; no real
one-to-one alignment or eligibility is established here. PhiUSIIL and UCI retain
separate U1 dictionaries and unavailable behavioral evidence; this Email schema
does not define their technical predictors or a content-bearing Web branch.

Pending acceptance: complete versus core E1 scope, observed-field derivations,
language/locator/trust inputs, all twelve operational rules/exclusions, partial
aggregation/missingness, text dtype/TF-IDF/numeric settings and actual-data
conformance. Approval fields exist only in approval_packet.md P6–P7.
