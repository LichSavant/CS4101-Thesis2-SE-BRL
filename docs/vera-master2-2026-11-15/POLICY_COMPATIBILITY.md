# Semantic policy compatibility — 15 November 2026

Engineering reconciliation only. No methodological approval, human reference
judgment, empirical accuracy, or permission to execute research is created here.

## Policy distinctions

| Policy | Inputs / outputs | Label authority | Review / abstention | Confidence and provenance | Scientific status |
| --- | --- | --- | --- | --- | --- |
| V13D `rules_only` / `extract` | Anonymous original text, modality, optional legacy identity argument; deterministic states/spans and optional scores | V13D regex decisions remain authoritative within that legacy instrument | Optional NLI can raise review flags; unavailable modalities not scored | Rule-based spans; NLI uncalibrated; anonymous text does not establish custody | Development instrument, not accepted independent inference |
| V13E `assess` | V13D observations, explicitly requested indicators, optional injected scorer | Preserves every V13D supported/absent/unavailable state | Hypothesis disagreement, entailment without rule evidence, or disagreement with rule support requests review | Scores are diagnostic; agreement is not validation | Current conservative review default; not calibrated fusion |
| V14 `V14_real_nli_acceptance.py` | Explicit model smoke-test script using fixed integration examples | Asserts V13E label preservation and span/score invariants | Tests integration, not behavioral correctness | A historical execution record cannot validate current code/model or human references | Script inspected; not executed; its real-model report was not generated or rewritten |
| V15 `infer` | Text, modality, explicit injected semantic scorer; segmented provisional states | Experimental majority-vote policy may assert support/absence | Advisory context abstains; missing scorer now abstains without loading weights | Original spans and uncalibrated votes; no independent judgments | Experimental; never the default authority |
| V16 `infer` | Text, explicit scorer, necessary evidence constraints | Experimental one-entailment-vote support after eligibility | Unresolved constraints abstain; missing scorer now abstains | Grounded necessary conditions do not prove semantic truth | Experimental, not accepted E2/E3 |
| V17 `assess` / `infer` | Clause evidence plus explicit scorer | Provisional contextual decisions for urgency and credential requests | Quotation/prohibition/context checks; unresolved indicators abstain | Evidence offsets; uncalibrated semantic votes | Two engineering decision paths; independent quality unvalidated |
| V20 `run` | V17 output plus V19 coverage contracts | Historical gate recognizes exactly two implemented paths | Ten pending indicators and independent-validation/research gates stay closed | Checks coverage and evidence, not accuracy | Unchanged: two implemented paths; no release |
| V21 `generate_candidates` | Text/modality and explicit scorer; twelve candidate records | No final label authority; candidates abstained/unavailable | Context flags request review | Original units, uncalibrated scores; anonymous legacy source | Candidate-only; no scientific release |
| V22 protocol | Codebook, blinding, provenance, independent judgments, evaluation requirements | Independent humans would provide references after approval | Missing/uncertain evidence stays explicit; adjudication separate | Qualification/blinding declarations need external authentication | Proposed, not evidence of an executed study |
| Canonical `generate_candidates` | `DatasetRecord`, explicit scorer, typed `DetectorContext`; original-field candidates | No final label authority | A/A*/U restrictions, identity evidence, failure/token-limit abstention | Pinned model/hypotheses contract, exact spans, uncalibrated scores | Engineering candidates only |
| New `review_record` | Canonical artifact, optional explicit scorer and typed context; validated immutable review document | Preserves canonical runtime `RuleEngine` observations exactly | Context prefilters, disagreement/ties, provider errors, budgets, missing identity; candidates never become final labels | Version/source bindings, original-field locators, explicit unauthenticated-provenance flags | Proposed engineering adapter; not a replacement frozen research policy |

V13D and canonical `RuleEngine` are different deterministic instruments. The new
controller preserves the latter; V13E continues to preserve the former. Shared
indicator IDs do not establish rule equivalence. No existing production pipeline,
dimension aggregation, learned-vector contract, or API route was replaced.

## Why V20 remains at two

`V17_contextual_constraints.assess` explicitly returns unresolved for indicators
other than `urgency` and `credential_sensitive_data_request`. V20's `IMPLEMENTED`
set reflects that executable limitation. Adding IDs would not implement missing
decision policies. This task leaves V20 and V19 unchanged and tests that V20
still reports two implemented and ten pending indicators.

The new twelve-indicator engineering claim is narrower: deterministic
observations, constrained semantic review/candidates, and source-linked identity
interfaces can execute under synthetic acceptance cases. It is not twelve
validated semantic decision policies or twelve scientific predictions.

## Focused resource and identity repairs

V15/V16/V17/V21 no longer instantiate a model when a caller omits its scorer.
Eligible cases remain abstained with an explicit reason. Injected experimental
vote policies otherwise remain unchanged and separate from the review default.

V15/V21 no longer accept `identity_evidence={verified: true}` as sufficient.
Those anonymous-text paths leave identity indicators unavailable and direct
callers to canonical artifact-linked references. V13D deterministic decisions
were not changed, including its limited legacy identity handling; they are not
an identity-validation interface.

Explicit legacy `SemanticNLI` construction delegates to the canonical pinned,
local-only scorer, validates the frozen hypotheses, and retains its legacy
score shape. It cannot download a moving model revision or silently truncate.
This is a documented resource/reproducibility repair, not new scientific
evidence. No real model was initialized during this task.

## Constraint timing

| Constraint | Before scoring | After scoring / export |
| --- | --- | --- |
| Canonical record, source exclusion, modality/content opportunity | Required | Recomputed against original record |
| Independent identity/brand references and artifact linkage | Typed audit-linked references required; anonymous flags rejected | Source/reference bindings retained; no claim software authenticated the audit |
| Quotation, education, warnings, reports, hypotheticals, negation | Ineligible units skipped; isolation directives retain their special meaning | Candidate spans must still be eligible original units |
| Source offsets | Exact field/location/Python-character offsets | Exact original substring and symbolic evidence revalidated |
| NLI distribution | No model/scorer implicitly created | Three finite normalized distributions; label mapping, logits/token shape and failure handling checked |
| Uncertainty / disagreement | Missing opportunity stays unavailable | Ties, disagreement, failures and incomplete budgets require review |
| Label authority | Deterministic baseline retained | Exact equality enforced; no supported/absent promotion from NLI |
| Research use | Explicitly closed stage boundaries | No predictor export, learned values, accepted features, or release |

The context heuristics are conservative candidate filters, not validated semantic
understanding. A previously broad deterministic match is retained as an
observation and flagged for review; this task does not silently revise the frozen
methodology or present that observation as a validated final conclusion.
