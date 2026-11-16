# SE-BRL methodology traceability

**Phase 1 — 16 November 2026. Source-to-method map, not scientific results.**

The governing source is the approved proposal identified in
`verification/approved-methodology-evidence.json`. References use **physical PDF
pages**. Software files below are preserved under `source/vera/` (V) or the
separate pinned `source/dhanwil-baseline/` (D). No source/evidence was rewritten.
All research gates remain closed. The original engineering rubric remains
21/22 (95.45%), with R22 blocked; this is not a scientific completion percentage.

## 1. Approved objectives → method → implementation → evidence → allowed claim

Exact objectives from PDF pp. 22–23:

**O1.** Develop and software-verify a frozen, modality-aware SE-BRL rule specification and evidence schema that operationalizes four behavioral dimensions through twelve subordinate indicators, distinguishes Supported, Absent, and Unavailable states, preserves traceable evidence references, and enforces modality boundaries.

**O2.** Audit, screen, group, and freeze the eligible datasets; construct E1, E2, E3, and U1 representations; comparatively evaluate Logistic Regression, Linear SVM, Random Forest, and XGBoost under identical leakage-controlled development conditions; and finalize the implementation classifier using predeclared predictive, calibration, inference-latency, throughput, resource-efficiency, and reproducibility criteria before sealed-test access.

**O3.** Integrate and verify explainability components that separately present observable behavioral and technical artifact evidence and model-based feature attribution associated with phishing-classification decisions.

**O4.** Design and verify a context-induced artifact-risk and decision mechanism that maps calibrated phishing likelihood, evidence coverage, requested-outcome severity, corroboration, and uncertainty into Informational, Elevated, High, or Review Required states and predefined risk-adaptive defensive responses.

**O5.** Implement and functionally validate a proof-of-concept browser extension, FastAPI backend, and supporting dashboard that integrate artifact processing, phishing detection, deterministic SE-BRL representation, evidence presentation, model attribution, risk assessment, decision processing, performance measurement, failure handling, and bounded intervention generation within an end-to-end workflow.

| Approved objective | Approved method | Actual source implementation | Available verification | Missing scientific evidence / acceptance | Acceptable current claim |
| --- | --- | --- | --- | --- | --- |
| O1 — rule/evidence specification | Four dimensions/twelve subordinate indicators, frozen deterministic definitions, modality boundaries, S/A/U and exact evidence; conformance not expert-ground-truth validity (pp. 20, 68, 86) | V `ml/se_brl/{codebook,rules,context,detectors,extraction,assessment}.py`; D nullable `representation.py` | Canonical source/unit/context/negative/unavailable checks; audit's 645 safe passes include broad conformance and 50 actual joint cases | Accepted exact operational rule/context/identity/locator/language/partial-availability specification; conformance to that frozen version on authorized inputs | Code operationalizes a twelve-ID evidence interface with bounded synthetic conformance tests; no psychological/implicit-meaning validity claimed |
| O2 — datasets/configurations/classifiers | Provenance/label/leakage/group audit; matched E1/E2/E3, separate U1; LR confirmatory E3–E1 and independent four-family implementation selection under frozen controls (pp. 20, 50–51, 69–83, 86) | V `datasets.py`, `preprocessing.py`, `features.py`, `grouping.py`, `feature_schema.py`; D `experiment_inputs.py`, `development_experiments.py`, `experiment_engine.py`, `classifier_adapters.py`, `model_selection.py`, `research_protocol.py` | Source/schema/fold/metadata/typed-run machinery and software fixtures; no accepted current actual-data comparative results established | Source-backed eligible labels/population/license/custody; actual group/exposure acceptance; matched dictionaries; exact settings/run authorization; controlled research results | Research infrastructure and leakage constraints are implemented; no E3 improvement, winning classifier, final accuracy or accepted source independence is asserted |
| O3 — explainability | Artifact fact/evidence separate from predictive attribution; neither implies the other (pp. 51, 87) | V source spans/rule IDs and `semantic_review.py`; D `attribution.py`, `artifact_analysis.py` and source/evidence envelope | Exact Unicode/span/provenance checks, malformed output rejection; peer attribution paths inspected but not executed on real models here | Accepted selected-model attribution method, fidelity/consistency checks and lawful artifacts/results under approved scope | Rule findings are traceable to source; optional NLI is a separate diagnostic channel, not validated causal or behavioral truth |
| O4 — artifact-risk/decision mechanism | Calibrated phishing likelihood + coverage/severity/corroboration/uncertainty with frozen precedence and bounded states/templates (pp. 21, 79–81, 87) | D `decision.py`, `experiment_engine.py::FittedSigmoid`, `artifact_analysis.py`; V legacy `backend/app/analyzers.py` is a different weighted demo | Software boundary/decision infrastructure and rule-based demo tests; no accepted final calibrated classifier/risk freeze supplied | Actual approved calibration/threshold/precedence specification and selected-system evidence; tested failure/review behavior and accepted final evaluation | A prototype heuristic and a separate guarded decision architecture exist. Hardcoded strengths/weights and NLI softmax are not calibrated risk |
| O5 — proof-of-concept integration | Bounded explicit-invocation extension/backend/dashboard; selected per-modality frozen classifier and evidence/attribution joined; failure/security/performance tests, no user susceptibility/effectiveness claim (pp. 21–24, 81–83, 87) | V `apps/*`, `backend/app/main.py`, `ml/se_brl/joint_integration.py`; D backend adapters, artifact service and source-level system infrastructure | Historical frontend and Python/backend records; audit's 50 joint cases; newly relocated same 50 pass. No live Gmail or model execution in Phase 1 | Parser disposition and attributable R22 acceptance; approved selected-system deployment seam, privacy/security/performance/end-to-end verification; durable release evidence | Source and proposed Email integration are preserved and software-tested. No deployed multimodal transformer service or production/security certification is claimed |

## 2. All twelve indicators: approved construction and current instrument

Common path: `preprocess` preserves original fields; `RuleEngine.extract` applies
English patterns plus `ContextIndex`; typed trust ports validate audit-linked
claims. `review_record` optionally calls a scorer but preserves the exact rule
observations. `validate_review` checks the final document against those original
fields and observations. Schema/identity/source truth are different questions.

| Indicator / parent | Deterministic approved-method mapping and actual source | Available verification | Missing scientific/specification evidence | Acceptable current statement |
| --- | --- | --- | --- | --- |
| Urgency / Pressure–Threat | `rules.py::pressure.immediate_action`, contextual action/immediacy | Positive/negative/context and span tests; V20 recognizes this as one of two legacy decision paths | Freeze urgency operational patterns/exclusions and authorized conformance; implicit urgency efficacy unvalidated | Explicit qualifying urgency-pattern observation; optional semantic review candidate is not an accepted label |
| Fear/threat / Pressure–Threat | `pressure.adverse_consequence` plus local context | Rule/context/missingness tests | Freeze consequence/benign-warning boundaries; no independently validated psychological fear claim | Source-linked specified adverse-consequence cue |
| Scarcity / Pressure–Threat | `pressure.limited_action` | Rule/context/negative cases | Define action/limited-opportunity semantics and false-support boundaries | Specified action/expiry/inventory cue, not proof of manipulation |
| Curiosity / Lure–Attention | `lure.information_gap` | Positive/negative/context cases | Freeze information-gap/action construct; broad implicit meaning not evaluated | Specified click/open/reveal cue with eligible evidence |
| Reward/lure / Lure–Attention | `lure.claim_benefit` | Positive/negative/context cases | Freeze benefit-request versus benign promotion semantics | Qualifying benefit/action cue, not independently proven deception |
| Authority / Trust–Identity | `ConservativeTrustDetector`: explicit role + same-sentence following directive + typed authorization relation | Artifact-linked positive/negative/unresolved examples; no bare verified flag promotion | Freeze allowed reference/custody and authorization relation under deterministic spec; no subjective legitimacy inference from NLI alone | Conditional typed rule finding; unknown legitimacy remains unresolved |
| Impersonation / Trust–Identity | Typed explicit identity claim + audited authorized-domain relation and exact observed conflict | Exact-host/span, missing-reference and malformed locator cases | Authentic external identity/delegation facts and accepted qualifying rule; reference type is not proof of truth | Conditional claim/domain evidence, not general identity verification |
| Brand exploitation / Trust–Identity | Typed brand/identity claim plus authorized-domain relation | Conditional and unavailable cases | Accepted brand relation/opportunity rules; no visual logo model or brand-intent validation demonstrated | Conditional artifact-linked brand/domain cue only |
| Confidentiality/isolation / Trust–Identity | `trust.prevent_verification`; specific negative directive allowance | Negation/context/double-negation review tests | Freeze source-opportunity and double-negation semantics; heuristic grammar is limited | Specified isolation instruction observation; reversed/uncertain units remain review-only |
| Call-to-action / Action–Consequence | `action.interact` | Positive/negative/context/modality cases | Freeze directive/exclusion boundaries; benign instructions are not automatically phishing | Qualifying action cue with source locator |
| Credential/sensitive request / Action–Consequence | `action.disclose_sensitive` | Positive/negative/span/context; V20 second legacy path | Freeze sensitive item/action and unavailable-field rules; no automatic semantic promotion | Specified disclosure request cue, not probability of phishing |
| Financial action / Action–Consequence | `action.transfer_money` | Positive/negative/context/missingness cases | Freeze payment/invoice/gift-card semantics; legitimate versus deceptive context needs bounded claims | Specified financial action observation, not independently established malicious intent |

All twelve have review/candidate interfaces, but the registry has nine lexical
families plus three conditional trust ports. V20's two legacy provisional
semantic decision paths do not become twelve validated decision policies.
Never add names to V20 merely to manufacture completeness. Baseline conformance
must name its actual frozen deterministic instrument, not silently mix V13D,
V17/V20, canonical rules and the product keyword analyzer.

Optional scorer tests use injected software values. They establish that eligible
implicit text can be offered for review and that constraints preserve labels;
they do not demonstrate real-world implicit tactic recognition. No per-indicator
scientific precision, recall, F1, agreement or calibrated confidence is generated.

## 3. E1/E2/E3/U1: fixed research boundaries

| Configuration | Approved input and control | Implementation | Verification / exact missing step | Permissible claim now |
| --- | --- | --- | --- | --- |
| Email/Web E1 | Conventional source-appropriate features; same eligible IDs/groups/folds/search conditions as E2/E3; learned transforms fit only in development training folds | V conventional/schema builders; D `features.py`, `feature_freeze.py`, `experiment_engine.py` | Software schemas/fold guards exist. Candidate E1 core versus full Table 4.7 scope, types/derivations and real accepted-data coverage remain pending | Conventional-feature infrastructure, not an accepted empirical baseline result |
| Email/Web E2 | Four deterministic support and four availability values; evidence locators are audit-only; no predicted behavioral confidence or dimension-OOF model | D `BrlRepresentation.deterministic_names/deterministic_slots`; V `representation_contract.py` preserves legacy types but rejects unapproved export | Nullable partial assessment/Absent policy, aliases and exact frozen eight-value dictionary need agreement. None must not be coerced into absent; unavailable remains distinct | Deterministic representation candidate and safeguard logic; no learned z estimator is required by approved study |
| Email/Web E3 | Exact E1 + exact E2 on matched observations, groups and folds; not a different population or extra unapproved neural predictor | D fusion/development engine and matched views; typed observation/assignment contracts | Accepted merged dictionary and actual one-to-one population/mask conformance missing; no data operation authorized here | Fusion/join infrastructure; no measured added value or selected system claim |
| U1 technical branches | Standalone URL and engineered technical benchmarks remain separate; no content-dependent behavioral scores from unavailable modalities | Codebook U masks, technical extraction/pipeline support | Source-specific feature dictionaries/label/custody and accepted technical evaluation required; do not infer original HTML/screenshots/intent from engineered fields | Technical-only route with behavioral unavailability, not cross-modal semantic equivalence |
| Comparison and selection | LR confirmatory E3–E1; all four classifier families under frozen controls; separate per-modality deployment selection, group-aware uncertainty, model/efficiency/calibration criteria | D candidate/nested/selection/calibration/persistence infrastructure | Authentic data/control/authorization and measured research results; no best model/threshold/positive improvement preselected | Executable research architecture; not a demonstrated research finding |

Approved 2,000-resample/95% paired group uncertainty is a methodological design
reference, not a confidence interval measured in Phase 1. Still-pending numeric
settings/tolerances are not invented. Existing classifier thresholds, candidate
JSON recommendations and prototype weighted scores are not silently adopted as
accepted scientific settings. No fresh split or label correction is performed.

## 4. Keep six output layers separate

| Layer | Actual owner/interface | What current verification establishes | Missing evidence / acceptable wording |
| --- | --- | --- | --- |
| Rule observation | Canonical `RuleEngine` or explicitly identified legacy instrument | Repeatable source-linked condition under that rule/context/opportunity contract | “Rule-derived supported/absent/unavailable/not-evaluated observation”; not expert truth or intent |
| Semantic review candidate | `semantic_candidates.py`, `semantic_review.py`, explicit optional scorer | Interface, pinning, score shape, eligibility, ties/errors/budgets and abstention; software-score cases only | “Uncalibrated optional review diagnostic”; no rule override, accepted label, predictor export or scientific efficacy |
| Phishing prediction | Genuine downstream classifier adapters/selected pipeline, distinct from legacy demo classification | Implementation and synthetic machinery; no accepted current comparative research result supplied | Actual authorized held-out measurements needed; do not call rule-demo classification a trained prediction |
| Calibrated probability | Selected phishing classifier/calibration object | Calibration/threshold infrastructure exists; no accepted final calibration run here | Calibrated classifier likelihood only after accepted data/procedure/results; no calibration of deterministic BRL or NLI implied |
| Risk/response decision | Frozen precedence over probability/coverage/severity/corroboration/uncertainty and bounded templates | Software decision architecture plus a separate simple weighted demo | Accepted selected-system freeze needed; demo percent/strength is heuristic, not official risk calibration or recipient susceptibility |
| Explanation | Long-form artifact evidence and separate classifier attribution | Exact original spans/IDs/version linkage; source/identity authenticity not automatically authenticated | Traceable deterministic evidence is not causal/psychological validity, SHAP truth or proven human warning effectiveness |

## 5. Current verification versus scientific evidence

- Historical full engineering records: Vera 1,199 passes/10 explicit research
  exclusions; selected peer 391 passes/one parser failure. These are not fresh
  Phase 1 totals or scientific metrics.
- November 16 audit: 645 safe Vera passes (including all 50 joint cases) and
  187 peer passes/one failure. No installations/models/corpora were used.
- **New Phase 1 preservation test:** all 50 joint cases passed from the relocated
  copied source trees, with the original code and actual pinned peer types.
  This is preservation/usability evidence, not NLI/classifier research accuracy.
- Source SHA-256/runtime-manifest coverage and all 144 peer Git blob identities
  were checked. No source was repaired, merged, committed or pushed.
- The known `<![bogus]>` peer parser discrepancy remains in the exact pinned
  source. Vera's strict intersection rejects it; direct peer behavior is not
  repaired by a source export. R22 approvals remain null and its whole-runtime
  comparison remains non-equivalent.

## 6. Minimum scientific prerequisite sequence (both options remain closed)

1. Establish the governing option and exact claim scope. Baseline A is already
   deterministic; B needs explicit revised questions/reference methods if studied.
2. Obtain source-backed provenance/access/license/native label semantics and
   eligible population roles. Historical source–class confounding is not cured
   by removing a source column. No replacement dataset or label map is chosen.
3. Accept duplicate/conflict/group relationships and exposure disposition. Do not
   imply historical holdout labels become sealed by creating a new split.
4. Freeze operational rule/language/locator/partial-state conformance and the
   exact matched E1/E2/E3/U1 dictionaries; keep targets/provenance audit-only.
5. Freeze candidate budgets/ranges/seeds, nested isolation, confirmatory and
   selection procedures, calibration/threshold custody, ECE/uncertainty and
   efficiency measurement rules before reading outcomes for selection.
6. Obtain named, hashed, authorized development delivery; perform an approved
   no-fit conformance check under its own boundary. Then request exact bounded
   research execution separately. Source hashes/task permission do not authorize it.
7. Accept actual controlled results and limitations, selected-system freeze,
   exposure-valid final evaluation and reproducibility evidence before manuscript
   performance claims. Null/negative outcomes must be retained, not rewritten.

No protected data, annotations, model weights, sealed labels or outcomes were
read or generated to create this traceability. Sources, gates and prior evidence
remain unchanged. The recommendations are decision materials, not execution.
