# C1. Deterministic codebook audit and freeze candidate

**Candidate audit, not an approved rule freeze.** Approved definitions are in
proposal Section 4.3.4/Tables 4.5-4.6, PDF pp.66-68. Canonical IDs/dimension order
come from `ml/se_brl/codebook.v0.1.0.json` (pre_freeze). Runtime candidate rules
are version 0.2.0; no file, definition or rule semantics was changed here.

Evidence output for the rows below: `IndicatorResult` in
`ml/se_brl/extraction.py`, state Supported/Absent/Unavailable, evaluation status,
and evidence with original field/location/start/end/text, rule/version and
supporting references. A conditional detector can remain None/not_evaluated;
that must never be converted to Absent. `context.py` suppresses quoted,
educational, reported, negated and counterexample uses conservatively.

Content-bearing Email/Web are potentially assessable. Bare URL/engineered U1
language evidence stays Unavailable. Trust/identity is conditional A* under the
current canonical resolver. Eligibility/language and partial opportunity must
be frozen; unknown language does not become English by dataset name.

| Official indicator / dimension | Definition and current deterministic candidate | Evidence condition / code | Synthetic coverage | Pending scientific interpretation |
| --- | --- | --- | --- | --- |
| `urgency` / pressure_threat_cues | Immediate-action pressure; action-now or action plus immediate/right-now phrase | Original qualifying text span; `rules.py` pressure.immediate_action | `test_rule_extraction.py::test_each_rule_family_has_exact_evidence`, context negatives | N04 accepts standalone deadline/urgent words; runtime requires narrower action coupling; exclusions/bounds/language must be frozen |
| `fear_threat` / pressure_threat_cues | Adverse consequence/loss; account/access suspension/termination/lock or loss/penalty phrase | pressure.adverse_consequence span | Same positive/negative/unavailable tests | N04 broad security-alert/unauthorized tokens differ; legitimate security information exclusion |
| `scarcity` / pressure_threat_cues | Action induced by limited availability/expiry | pressure.limited_action span | Same tests | N04 limited/exclusive-offer tokens versus runtime action coupling; routine availability exclusion |
| `curiosity` / lure_attention_cues | Interaction induced by an information gap | lure.information_gap span | Same tests | N04 important/private-message tokens versus explicit gap; informative content boundary |
| `reward_lure` / lure_attention_cues | Promised incentive inducing interaction | lure.claim_benefit span | Same tests | Verified promotions/routine benefits and deceptive inducement cannot be silently inferred from keyword presence |
| `authority` / trust_identity_manipulation | Misuse of institutional power, rather than mere role mention | `detectors.py::ConservativeTrustDetector`: role + directive, linked authorization contradiction; otherwise not_evaluated | `test_context_detectors.py::test_authority_independent_review`, role-alone/unknown/bad locator cases | N04 authority lexical matches versus runtime independent evidence; choose deterministic observable input/reference criteria; no human behavioral annotation prerequisite |
| `impersonation` / trust_identity_manipulation | Inconsistent explicit claimed identity | Explicit claim + independently audited authorized-domain/delegation evidence; exact conflict; `IdentityReference` | `test_explicit_claim_with_independent_domain_conflict`, aligned/unknown/partial references | Missing identity/delegation is unassessable. Dataset reference acquisition/opportunity coverage not established |
| `brand_exploitation` / trust_identity_manipulation | Misleading brand relation | Same detector with canonical brand indicator; brand mention alone insufficient | Same parameterized conflict/mention/partial tests | Valid domain/reference coverage and aligned-use exclusions; no brand-name-only positive |
| `confidentiality_isolation` / trust_identity_manipulation | Concealment or avoidance of independent verification | trust.prevent_verification directive; special negative-instruction exception | Rule/context positive, educational/negated cases | Runtime parent A* blocks it when identity fields missing; N04 lexical partial availability differs. Researcher decision needed |
| `call_to_action` / requested_action_consequence | Requested interaction: click/reply/download/visit/submit | action.interact text span | Rule exact-span/overlap/context/unavailable tests | Structural link/button/form requests versus lexical-only coverage; do not fabricate missing links |
| `credential_sensitive_data_request` / requested_action_consequence | Request to disclose protected information | action.disclose_sensitive directive + specified data span | Exact spans, safety advice/quotation and technical boundary tests | Data-type lexicon/exclusions and source-field coverage remain pre-freeze |
| `financial_action_request` / requested_action_consequence | Payment/transfer/purchase/account-change request | action.transfer_money span | Positive, negation/context, unavailable tests | Requested-action scope and verified-transaction exclusion; no inferred intent or severity model |

Common tests also cover forged evidence, deterministic schemas, modality masks,
overlap retention, reference alignment and source-preserving locators. Fresh
focused rule/adapter/preflight run: 131 passing tests; full suite details in
README. Test conformance to candidate rules is not psychological ground truth or
accepted dataset coverage. Three trust ports require independent observable
reference metadata; this does not add expert behavioral annotation to the paper.

## Dimension encoding candidate already implemented at D9

Use the existing ordered four support bits followed by four availability bits.
Supported -> (1,1), Absent -> (0,1), Unavailable -> (0,0); support > availability
is invalid. These are evidence states, not confidence, intent, phishing labels
or calibrated probability. Keep indicator evidence separately from predictor
bits and from model attribution. Technical U1 excludes those predictor columns.

## Unresolved aggregation and notebook alignment

N04 cell 23 has ten broad lexical indicators (including authority), two identity
placeholders; runtime has nine narrower lexical rules plus three conditional
trust detectors. Cell 26 collapses whitespace and returns deduplicated matched
snippets, not original-field offset evidence; cell 30 concatenates subject/body.
Cell 35 still blocks without a frozen specification. Cell 64 calls a dimension
Absent when any subindicator is available and none is supported. Runtime
assessment may mark the same dimension Absent despite unevaluated trust ports
when its parent A* opportunity is supplied. Neither path establishes that all
required negative evidence has been assessed.

**Decision-ready clarification, not adopted:** choose either the documented
current partial-opportunity aggregation with explicit claim limits, or a
conservative rule where Supported requires qualifying evidence and Absent
requires all frozen required opportunities evaluated; otherwise Unavailable/
review. Define how supported partial evidence affects the dimension mask.
Do not choose between these by observed model performance. Once accepted,
reconcile both paths and test exact original-field locators before extraction.

The twelve canonical definitions/modality boundaries are approved. Rule
operational details, exclusions, context windows, language support, reference
opportunity and partial aggregation need the dated specification acceptance.
The candidate package consists of this traceability, existing rule/version
hashes and tests, and the decisions above. No new scientific rule or final
codebook version was invented. Legacy runtime learned-z/readiness placeholders
are not a supervised-behavioral prerequisite for the deterministic D9 study.
