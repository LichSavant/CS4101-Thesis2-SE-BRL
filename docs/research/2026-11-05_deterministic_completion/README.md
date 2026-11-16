# Deterministic prototype completion checkpoint - November 5, 2026

This consolidated report separates verified software, generated-fixture results,
historical evidence, scientific acceptance and research execution. The approved
deterministic proposal governs. Transformer work is explicitly deferred.

## A. Executive summary

**Finished:** genuine Logistic Regression, Linear SVM, Random Forest and XGBoost
adapters; integration with the existing five-fold synthetic runner; per-fold
configuration/version records; stronger representation-comparison controls;
genuine generated-fixture E1/E2/E3, ablation, U1, metric and timing verification;
exclusive, hash-verified output bundles; current documentation reconciliation.

**Fresh verification:** 977 ML/backend tests, 25 frontend tests, both TypeScript
checks, extension/dashboard production builds and 275 static notebook code cells
passed. The final preflight wording/test change was additionally covered by 382
passing neighboring tests. The saved demonstration made **180 genuine estimator
fit calls on generated fixtures**, not research observations. Tests made further
fixture fits; 180 is the saved demonstration count, not a count of every test fit.

**Not finished:** accepted actual-data handoffs, empirical E1/E2/E3/U1 results,
research search/nesting, cross-fitted probability calibration, final selection,
model persistence/freeze, risk/attribution integration and confirmatory evaluation.
No research classifier or calibrator was fitted, no threshold was optimized, and
no candidate was selected. D10 research execution remains blocked. This is not a
scientifically complete thesis or a validated analytical application release.

The governing proposal was reread directly: 155 PDF pages, SHA-256
`283338c5535c5553e35266f5083a6380e014637e63d42161c659238e257ad1fe`.
References below are PDF-viewer pages. Text/font-map extraction was used; no
visual figure-layout verification is claimed.

| Approved requirement used | Governing location | Implementation/research consequence |
| --- | --- | --- |
| Deterministic SE-BRL; no supervised behavioral predictor or expert behavioral annotation | Section 1.7, p.24; Section 4.3.4, pp.66-68 | D11 explicitly deferred; no new annotation prerequisite |
| Source roles, native labels, eligibility and attrition | Tables 4.1-4.2, pp.58-60; Sections 4.3.2-4.3.3/Table 4.4, pp.63-65 | Source eligibility is not inferred from a file/hash or approval-reference string |
| Four dimensions/twelve indicators, traceable states and conformance | Tables 4.5-4.6, pp.66-68 | Candidate rules audited below; semantic discrepancies are not silently resolved |
| Matched E1/E2/E3; independent U1; LR confirmatory contrast | Section 4.3.5.1/Table 4.7, pp.69-70 | Same fixture records/folds; technical U1 never becomes E2 |
| Genuine four-family candidates and explicit controls | Table 4.8, p.71 | Genuine library adapters; no implicit SVM probability calibration |
| Development-only selection, grouped CV, PR-AUC, paired uncertainty, calibration and efficiency gates | Sections 4.3.5.2-4.3.5.3/Table 4.9, pp.72-75 | No invented tolerances, SRS limits or search/calibration/benchmark freeze |

Read before implementation: repository AGENTS.md; current Git inventory; November
4 handoff, protocol/dataset/experiment evidence and artifact inventory; approved
proposal; canonical codebook; all six notebooks' source structure and relevant
construction/extraction/modeling cells; preparation/integration/D9/runner/metric/
benchmark/model modules and tests; historical experiment/input manifests; existing
research decisions and UCI acceptance packet. Stored notebook results were not
executed or accepted as fresh results. No raw Email contents or historical
prediction/outcome rows were inspected. Unsaved editor buffers were not accessed.

## B. D1-D16 matrix and dependencies

Engineering status is bounded to the named component. A scientific Pending or
Blocked status is not removed by software tests. Historical aggregate evidence
is not new empirical validation.

| Task | Engineering | Scientific status | Empirical status / next dependency |
| --- | --- | --- | --- |
| D1 protocol/scope | Reconciliation documented | PENDING branch-specific freezes; governing deterministic architecture verified | No new research execution; resolve the specific gates in H below |
| D2 preprocessing | Existing repairs/supplied-assignment path preserved; PARTIAL end-to-end readiness | PENDING raw-to-clean lineage and screening acceptance | No real preparation in this task |
| D3 counts/labels/groups/sources | Metadata/hash checks implemented; PARTIAL | PENDING source/label/license/attrition evidence | Historical aggregates only; no new source-record audit |
| D4 isolation | Supplied-assignment/group/fold guards implemented | BLOCKED accepted relationships, reuse and exposure/custody policy | No new partitions; historical isolation does not prove scientific independence |
| D5 twelve indicators | Candidate engine/tests and trust-reference ports implemented; PARTIAL frozen conformance | PENDING operational rule/locator/language/partial-availability freeze | No behavioral ground-truth or real-source conformance claim |
| D6 alignment/availability | Shared boundary and D9 validation implemented | PENDING actual accepted dictionary/population/specification | Synthetic verified; actual dataset-to-feature check remains unexecuted |
| D7 leakage/confounding | Guards, matched controls and source-slice diagnostics implemented | PENDING source/template/campaign/exposure evidence | Synthetic safeguards; no absence-of-leakage claim on research data |
| D8 tests | ENGINEERING COMPLETE for this checkpoint | Software verification only | 977 Python + 25 JS; 275 static cells; checks/builds passed |
| D9 preparation handoff | ENGINEERING COMPLETE for current strict loader/exports | PENDING accepted real inputs/dictionary and delivery authorization | Synthetic D9 round trips; real handoff absent |
| D10 models/experiments | Genuine four-family fold adapters + matched runner verified; PARTIAL research launcher/search/selection | PENDING data and candidate settings | Genuine synthetic fits only; real D10 BLOCKED |
| D11 transformer | DEFERRED by current user direction | Outside current approved deterministic implementation | Not implemented or required for deterministic completion |
| D12 metrics/calibration | Metrics/reliability/bootstrap verified; calibrator fitting/integration NOT COMPLETE | PENDING calibration/threshold/score conventions | Synthetic/raw-probability diagnostics; zero calibrator fits |
| D13 CV/ablations | Five-fold, dimension and explicit-family omissions verified | PENDING actual comparison/nesting/sensitivity plan | Genuine synthetic execution; no empirical representation claim |
| D14 reproducibility | Versioned settings, fold records, hashes and exclusive bundles implemented; PARTIAL final model persistence/release | PENDING accepted dataset/model/environment freeze | Synthetic artifacts verified; temporary environment only |
| D15 manuscript | Methods/evidence/limitations and decision handoff prepared | Empirical conclusions pending | No fabricated thesis-performance or psychological claims |
| D16 freeze/handoff | Technical handoff prepared; final release NOT COMPLETE | BLOCKED final scientific/selection/calibration/system acceptance | No final freeze, deployment or confirmatory evaluation |

Dependency order: D1/D3/D4/D5 supply the branch-specific evidence needed by
D2/D6/D7/D9; accepted D9 and frozen search/score controls enable real D10; D10
enables real D12/D13; D14/D15 preserve/report those results; final selection,
calibration/risk/system verification precede D16. Generic code/synthetic tests can
proceed independently. D11 is outside this dependency chain.

## C. Exact files changed

Six existing on-disk files changed in this task:

| Path | Reason |
| --- | --- |
| `ml/development_runner.py` | Capture optional fold audit records; include joblib/threadpoolctl/hardware metadata; reject representation comparisons with different implementations or recorded preprocessing |
| `ml/tests/test_development_runner.py` | Three policy-mismatch regression cases, including missing recorded policy |
| `ml/preflight.py` | Replace stale 'unimplemented XGBoost' wording and clarify the legacy runtime/approved deterministic boundary; authorization remains false |
| `ml/tests/test_preflight.py` | Assert truthful candidate role without weakening execution gates |
| `ml/models.py` | Clarify legacy runtime ports versus the new offline genuine adapters |
| `ml/README.md` | Document the actual deterministic/offline path and preserve the legacy-interface distinction |

Five new source/config/test files:

| Path | Purpose |
| --- | --- |
| `ml/classifier_adapters.py` | Typed explicit settings, lazy genuine dependencies, single-use fold-local pipelines, predictor/score contracts and audit records |
| `ml/genuine_classifier_smoke.py` | Generated-fixture-only end-to-end four-family command; no research loader/search/calibrator |
| `ml/requirements-classifiers-synthetic.txt` | Six pinned packages for the separately approved isolated CPU verification environment |
| `ml/tests/test_classifier_adapters.py` | 60 contract/genuine-fit cases, including dictionary, fold-local transforms, native codes, orientation, training-only weights and failure boundaries |
| `ml/tests/test_genuine_classifier_smoke.py` | Eight end-to-end/failure/independent-metric cases |

New documentation/evidence: this report, `preflight.json`, `verification.json`,
and thirteen files under `genuine_smoke/`: `summary.json` plus each family's
`manifest.json`, `metrics.json`, and `oof_predictions.csv`. New generated
predictions describe artificial fixtures only. No historical output was replaced.

## D. Actual tests, commands, failures and warnings

Task storage shorthand:

- `<T>` = `<user-profile>/AppData/Local/Temp/sebrl-deterministic-20261105-btjhvbvt`.
- `<S>` = `<user-profile>/AppData/Local/Temp/sebrl-genuine-approved-20261105`.
- Scientific runs set `PYTHONPATH=<S>/science`, `TEMP=TMP=<S>`,
  `PYTHONDONTWRITEBYTECODE=1`, `DATABASE_URL=sqlite:///:memory:`.
- Other Python tests used `<T>` with the same bytecode/database protections.
  Every pytest invocation used `-p no:cacheprovider` and a fresh `--basetemp`.

| Executed command (repository root unless stated) | Actual result |
| --- | --- |
| `.venv/Scripts/python -B -m pytest ml/tests/test_classifier_adapters.py ml/tests/test_development_runner.py ml/tests/test_evaluation_metrics.py ml/tests/test_synthetic_demo.py -q -p no:cacheprovider --basetemp <T>/contracts-no-science` | 115 passed, 19 explicitly skipped: dependencies absent |
| Adapter/smoke files with the same options, `<T>/contracts-second` | 43 passed, 25 skipped |
| Adapter/smoke/runner files, `<T>/contracts-third` | 81 passed, 25 skipped |
| Adapter/smoke/runner/metrics/old-demo files with `--tb=short`, `<T>/genuine-first`, sandbox reading host package files | 116 passed, 26 failed, 24 metadata deprecation warnings; Windows denied package-file access, producing namespace-only imports. Not a successful genuine verification |
| Same five files, host execution with approved packages, `<S>/genuine-host-first` | **142 passed**, 0 skipped, 21.86 s |
| `.venv/Scripts/python -B -m pytest ml/tests backend/tests -q --tb=short -p no:cacheprovider --basetemp <S>/full-regression-final` | **977 passed**, 31.91 s; one installed Starlette/httpx deprecation warning |
| `.venv/Scripts/python -B -m ml.genuine_classifier_smoke --directory docs/research/2026-11-05_deterministic_completion/genuine_smoke --code-reference '6bded57 plus November 5 working-tree code hashes; synthetic only'` | Four bundles independently verified; 180 genuine synthetic fits; zero research/calibrator fits |
| `.venv/Scripts/python -B -m pytest ml/tests/test_preflight.py ml/tests/test_branch_preparation.py ml/tests/test_development_experiments.py ml/tests/test_uci_preparation.py ml/tests/test_experiment_integration.py ml/tests/test_notebook_contracts.py ml/tests/test_experiment_inputs.py -q --tb=short -p no:cacheprovider --basetemp <T>/neighbors-final` | **382 passed**, 5.36 s, after the final preflight wording/test correction |
| `npm.cmd run test --workspaces --if-present -- --configLoader runner` | **17 extension + 8 dashboard = 25 passed** |
| `node node_modules/typescript/bin/tsc -p apps/gmail-extension/tsconfig.json --noEmit --incremental false` and corresponding dashboard command | Both passed |
| From extension: `node ../../node_modules/vite/bin/vite.js build --configLoader runner --outDir <T>/build/extension`; same with `--config vite.content.config.ts` | Popup/background and content builds passed |
| From dashboard: same Vite build, `--outDir <T>/build/dashboard` | Passed; expected outside-project output-directory warning; no existing application outputs emptied |
| Read six notebook JSON files and `ast.parse` each code cell | **275 valid cells; zero executed** |
| Call existing `run_preflight(Path.cwd())` and exclusively save `preflight.json` | 16 issues, authorization false; equivalent CLI status would be 2. The function invocation itself succeeded |
| Dependency-free replay of every saved bundle's output hashes, summary manifest hashes and twelve recorded code hashes | All four passed; no refitting or corpus reads |

Installation was explicitly approved by the user during this task. The first
sandbox attempt failed on network access; a host retry downloaded packages but
failed writing into a sandbox-owned directory. A fresh host-created `<S>` target
then installed successfully. No application package was installed/replaced.
The approved installation command used `.venv/Scripts/python -B -m pip install
--target <S>/science --only-binary :all: --no-cache-dir --no-compile --no-deps
--requirement ml/requirements-classifiers-synthetic.txt
--disable-pip-version-check --retries 1`. No data was downloaded.

Pinned/import-verified packages: NumPy 2.2.6, SciPy 1.15.3, scikit-learn 1.6.1,
XGBoost 2.1.4, joblib 1.5.1, threadpoolctl 3.6.0. Python is 3.12.10; existing
pytest is 8.4.2. Host execution was needed because sandbox access to host-installed
temporary packages was denied. This is an access/environment distinction, not
an algorithm substitution. The application `.venv`, without this temporary
PYTHONPATH, still has no NumPy/SciPy/sklearn/XGBoost. Pandas/matplotlib are not
installed by this approval; full analytical notebook execution remains unavailable.

## E. Genuine model adapters and deterministic features

`ml/classifier_adapters.py:43` validates exact explicit family parameters and
uint32 seed; `:93` validates explicit preprocessing; `:134` supplies the single-use
fold pipeline; `:283` binds runner requests to those settings. No automatic
algorithm fallback, train/validation resplit, eval_set, early stopping or hidden
calibration is accepted. The library pipeline receives predictor matrices and
training targets only. Observation IDs remain alignment metadata for scoring.
This interface is not a sandbox or an authenticator of scientific permission.

| Family | Genuine estimator | Score / probability boundary | Verified on generated fixtures |
| --- | --- | --- | --- |
| Logistic Regression | `sklearn.linear_model.LogisticRegression` | `predict_proba[:,1]`, raw/uncalibrated | E1/E2/E3, U1, text/numeric fold transforms, repeatability |
| Linear SVM | `sklearn.svm.LinearSVC` | Signed `decision_function`, class 1 positive; probability remains null | Same controls; no `SVC(probability=True)` internal calibration |
| Random Forest | `sklearn.ensemble.RandomForestClassifier` | `predict_proba[:,1]`, raw/uncalibrated | Same controls, seed and explicit CPU jobs |
| XGBoost | `xgboost.XGBClassifier`, CPU `gbtree`/`hist`, binary logistic | `predict_proba[:,1]`, raw/uncalibrated | Same controls; optional declared `fold_ratio` uses only training-label counts; 3:1 test verified |

Vocabulary, IDF, median imputation and optional scaling are constructed fresh
inside each fold's sklearn Pipeline/ColumnTransformer. Validation-only words and
extreme numeric values cannot change learned training statistics. No missing
text is fabricated; missing numeric handling is explicitly reject or training
median. Entirely missing training numeric columns fail. Native UCI -1/0 values
are not interpreted as missing. Behavioral support/availability ordering remains
the existing canonical eight columns; unavailable U1 evidence stays masked and
is excluded from U1 predictors. All classes/finite scores/IDs/schema widths and
single-use fitting are checked. Convergence warnings fail a fit rather than
silently reporting a successful candidate.

Each fold records requested/resolved estimator parameters, class orientation,
seed, versions, ordered names, dictionary/protocol references, training count and
matrix fingerprint. No raw predictor text is exported. Settings/references do
not prove a completed scientific freeze. Model serialization is not performed:
no selected/frozen model or accepted persistence format exists. No pickle/joblib
loader or unsafe arbitrary-object artifact is introduced.

### Twelve-indicator specification/conformance audit

Canonical source: `ml/se_brl/codebook.v0.1.0.json`, version 0.1.0, explicitly
`pre_freeze`. Four meanings remain Pressure/Threat, Lure/Attention, Trust/Identity
Manipulation, and Requested Action/Consequence. The following rules are verified
**candidate implementation**, not a newly approved scientific specification.

Common contract for all rows: content-bearing Email/Web only when required
evidence exists; URL/engineered language evidence is unavailable. Output is
Supported/Absent/Unavailable plus evaluation status and traceable evidence;
unevaluated trust conditions remain `None/not_evaluated`, never fabricated Absent.
Runtime evidence contains original field/location/start/end/text; contextual
negation/quotation/training-example suppression is in `se_brl/context.py`.
Each Supported result must retain its qualifying span and rule/version provenance.

| Indicator; approved observable meaning | Current candidate rule / required evidence | Unavailability and test evidence | Code location |
| --- | --- | --- | --- |
| urgency; immediate-action pressure | `pressure.immediate_action`: explicit act-now or action-plus-immediacy text | Required content; positive/exact-span, negation, quote and technical cases in `test_rule_extraction.py` | `ml/se_brl/rules.py`, RULES; `extraction.py:47` |
| fear_threat; adverse consequence/loss | `pressure.adverse_consequence`: account/access suspension/termination/lock or loss/penalty text | Same required-content/state/locator tests | Same files |
| scarcity; limited availability pressuring action | `pressure.limited_action`: action plus expiry/remaining/limited-time cue | Same tests; routine dates are excluded by the codebook/context boundary | Same files |
| curiosity; induced information gap | `lure.information_gap`: click/open plus find-out/discovery/reveal cue | Same content and exact-span tests | Same files |
| reward_lure; promised benefit inducing interaction | `lure.claim_benefit`: interaction/claim plus prize/reward/gift/refund cue | Same content/context tests; routine/verified benefit distinction still needs operational freeze | Same files |
| authority; misuse of institutional power | Role plus same-sentence directive; qualifying contradiction requires linked authorization reference | Without independent authorization information, not_evaluated; authorized/contradicted/unknown synthetic boundary tests | `ml/se_brl/detectors.py:130`; `test_context_detectors.py` |
| impersonation; inconsistent claimed identity | Explicit identity claim + audited authorized-domain/delegation comparison | Missing identity/reference/delegation remains not_evaluated/unavailable; aligned/conflicting domains and forged locators tested | Same detector/test files; `_locate` at `:99` |
| brand_exploitation; misleading brand relation | Explicit brand claim + independent authorized-domain conflict | Mention alone is insufficient; missing/unknown references do not assert negative or positive evidence | Same detector/test files |
| confidentiality_isolation; concealment/avoid independent verification | `trust.prevent_verification`: explicit do-not-tell/contact/consult instruction | Runtime applies parent trust A* evidence gate, including to this lexical indicator; notebook partial availability differs and is unresolved | `rules.py`; `extraction.py:47`; both rule/context test files |
| call_to_action; requested interaction | `action.interact`: explicit click/visit/open/download/reply/submit request | Content/locator/context cases; technical records remain unavailable | `rules.py`; `test_rule_extraction.py` |
| credential_sensitive_data_request; protected-data disclosure request | `action.disclose_sensitive`: directive plus listed sensitive data | Exact spans, negated safety advice, quotations and absent content tested | Same files |
| financial_action_request; payment/transfer/account action | `action.transfer_money`: explicit transfer/send/pay/gift-card/bank-update request | Same state/context/locator boundaries | Same files |

The full taxonomy is present, but all twelve are **not scientifically frozen or
fully verified on actual sources**. Three trust indicators have conditional
reference ports, not generally available dataset evidence. Such references are
source/authorization evidence; they do not introduce expert behavioral labels or
a human-annotation requirement. Supported-state claims must await an accepted
deterministic rule/input specification.

Notebook 04 cells 25-35 contain a separate normalized lexical matcher;
`prepare_email_branch` (cell 35) still rejects a missing frozen rule reference.
Normalized evidence offsets are not established as original field offsets;
language/partial availability and notebook/runtime trust handling remain
unreconciled. A reference string alone does not establish conformance. These are
scientific/input-boundary decisions, so no rules, language scope or masks were
silently changed. No notebooks or codebook/rule files changed in this task.

## F. E1/E2/E3, metrics, calibration and ablations

Saved fixture run: ten generated development observations, five supplied pair
groups/folds, both classes in each fold. The artificial signal equals a generated
target solely to exercise plumbing. It is not observed behavioral ground truth.

Per family: 15 base fits (E1/E2/E3 x five folds), 20 dimension-omission fits,
five explicit conventional-feature omission fits and five separate UCI-shaped
technical U1 fits: **45 each, 180 total**. Each base configuration has ten OOF
rows, with identical observation/group/fold identities across configurations.
Each family bundle stores 30 base Email OOF rows, fold/pooled metrics and fold
pipeline metadata. Supplemental U1/ablation entries record smoke checks; they are
not complete archived research U1/ablation prediction/model bundles.

Metrics include precision/recall/F1/confusion, ROC-AUC, balanced accuracy, MCC,
non-interpolated average precision, Brier, ECE and reliability bins where raw
probabilities exist. Five independent tied-score fixtures matched sklearn metric
implementations. Undefined source-slice ROC remains null; class-specific
artificial source slices do not establish source independence.

Paired cluster bootstrap and dimension support+availability omissions run through
the existing primitives. The smoke uses 25 resamples/95%, five timing repetitions,
one warmup, batch one, seed 17 and small eight-tree synthetic budgets. These are
software-test settings, **not approved research settings**; the proposal's real
comparison requires 2,000 paired group resamples/95% and a separately frozen
score/interval/equivalence/benchmark policy. No candidate winner follows from
these synthetic values.

SVM margins receive no probability metrics. Other raw estimator probabilities
receive diagnostic metrics only; Brier/ECE do not prove calibration. No calibrator
was fitted. Group-disjoint inner calibration/search plans, score comparability
and threshold policy must be frozen before implementing the research procedure.
Final reserved calibration and thresholds follow selection; historical test
outcomes cannot choose any of them.

The saved timing callback predicts on a prepared numeric matrix using the fitted
classifier only; feature preparation is outside timing. Threadpoolctl limits=1
surrounds execution; RF/XGB jobs=1. Timings remain toy batch p50/p95/throughput,
not approved deployment measurements. Memory and serialized model size are null;
no resource-efficiency superiority or SRS acceptance is claimed. The existing
generic benchmark correctly marks caller thread/memory references unauthenticated.

**Research data:** zero new E1/E2/E3/U1 preparation, training, tuning, calibration,
comparison, selection or sealed evaluation. Historical LR results remain separate.

## G. Dataset readiness, provenance and attrition

This task rechecked metadata/source structure and preservation hashes. November 4
source/header/assignment records are unchanged and retained as the detailed
evidence register in `../2026-11-04_master_completion/dataset_evidence.json` and
its companion Markdown. The following aggregate counts come from those unchanged
historical metadata records; they are not a newly executed eligibility audit.

| Branch/source | Approved role and implemented mapping | Verified local evidence / missing acceptance |
| --- | --- | --- |
| Nazario | Eligible phishing positives, native 1 -> target 1 | Payload/schema fingerprints retained; source/class/access/license, original-ID screening/attrition and lineage incomplete |
| Enron | Explicit legitimate/ham only, native 0 -> target 0 | Same; organizational provenance/privacy and source shortcuts require audit |
| SpamAssassin | Explicit ham 0 -> target 0; spam excluded from this binary construction | Same; no silent spam-to-phishing mapping |
| CEAS-08 | Auxiliary original semantics unless a frozen audit supports inclusion | Historical Email manifest contains CEAS; current primary builder does not; exact reconciliation decision in H |
| Putra content-bearing Web, Zenodo 8041387 | Approved Web E1/E2/E3 source | Matching content payload not identified; source/access/schema/evidence delivery absent; BLOCKED |
| PhiUSIIL | Independent U1-Ph, native 0 -> target 1, native 1 -> target 0 | Existing engineered payload; no guaranteed behavioral evidence; dictionary/source/group acceptance incomplete |
| UCI Phishing Websites | Independent U1-UCI; implemented Result -1 -> target 1, +1 -> target 0 | Raw/archive/LFS identity and 31-column cleaned schema recorded; primary class-definition proof, original-row lineage and grouping/reuse/dictionary acceptance incomplete |
| ISCX-URL2016 | Preserved historical source outside active Table 4.7 exports | Not admitted as a replacement research branch |

| Historical assignments | Observations / groups / mixed-target groups | Development / calibration / test | Recorded group crossing |
| --- | --- | --- | --- |
| Email | 38,759 / 21,601 / 0 | 27,129 / 5,815 / 5,815 | None recorded |
| PhiUSIIL | 235,795 / 220,086 / 54 | 165,089 / 35,358 / 35,348 | None recorded |
| UCI | 5,849 / 5,785 / 64 | 4,094 / 878 / 877 | None recorded |
| ISCX | 14,823 / 14,823 / 0 | 10,375 / 2,224 / 2,224 | None recorded |

Historical Email membership: Nazario 1,565; CEAS 17,312; Enron 15,791;
SpamAssassin 4,091. Source identity determines the constructed positive/negative
class. Removing source columns cannot remove writing-style/era/format shortcuts.
Recorded groups do not prove template/campaign/domain independence.

For each source, missing evidence remains specific: source_snapshot_id,
repository/access date and license; primary native class definition; original-ID
raw-to-clean map; reason-coded exclusions and reconciled attrition; exact and
near-duplicate families and source-permitted group relationships; accepted
assignment reuse/custody; ordered predictor dictionary and extraction/version
records. Existing cleaning counts/logs are historical evidence, not an accepted
Stage 3 freeze. No new dataset was obtained; the abandoned dataset stays excluded.

The strict D9 loader and UCI supplied-assignment API remain engineering-ready
for accepted inputs. `experiments/runs` still has no current real D9 handoff.
Notebook 04's explicit U1-only branch remains intact, but its full-input loader
reads selected full preprocessed branches before development filtering; it is
not a strict reserved-payload no-read gate. Use an independently authorized
development-only delivery path when that custody constraint is required.

## H. Exact blockers and decisions

| Priority / minimum input | Responsible acceptance owner | Acceptance check / consequence |
| --- | --- | --- |
| Email population: decide auxiliary CEAS status versus audit-supported admission; specify exact eligible native classes/IDs and relationship to the CEAS-containing historical assignments | Dhanwil/Vera; adviser for any methodological change | Dated source-backed eligibility and population reconciliation, explicit no-regeneration/reuse disposition. Do not silently accept the old 38,759 population or drop CEAS and reuse incompatible assignments |
| Source/label/access/lineage and screening evidence for the selected branch | Vera/source custodian supplies evidence; researchers accept; Dhanwil validates mechanics | Immutable source manifest, native mapping documentation, original-ID lineage/attrition/duplicate records reconcile to the supplied ID universe. A signature cannot substitute for missing provenance |
| Conservative group evidence, assignment reuse and historical-exposure claim policy | Researchers/adviser and data custodian | All supplied groups/roles/folds accepted; known limitations recorded; no resealing of an exposed historical holdout or seed reshuffle as a cure |
| Deterministic rule and feature dictionary freeze for Email | Researchers/specification owner; adviser if scientific meaning changes | Canonical 12 definitions, exclusions, language policy, original-field locators, identity/reference requirements, partial availability and exact ordered conventional predictors; no invented negative evidence or human annotation requirement |
| Development delivery/authorization | Researchers/custodian; Dhanwil performs the bounded check | Named development-only files, hashes, assignment universe and accepted specifications; exact one-to-one metadata/availability validation before fitting |
| Candidate research settings | Researchers/adviser as applicable to selection policy | Table 4.8 ranges plus budgets/nesting/seeds/score and calibration procedure; AP/ECE/binning/bootstrap conventions, equivalence tolerance and actual applicable SRS requirements frozen before comparative research results |
| Final selection/resource/freeze policy | Researchers/adviser; Dhanwil implements accepted mechanics | Shared hardware/software, warmup/repetitions/batches/threads, memory and safe model persistence policy, calibration/threshold/risk/attribution/system tests; no numerical SRS limit invented |

All existing H1-H12 decision drafts remain unchanged and Pending; no new approval
is claimed. The user's approval in this session covers six temporary packages
and synthetic genuine fits only. It does not approve datasets, grouping, candidate
selection or real training. Not every H item must be closed to fix unrelated code.
Final operational threshold numbers are not prerequisites for development fits;
the procedure/data-use boundaries must be declared before using those data.

Historic test metrics/predictions and notebook evaluation demonstrate previous
exposure. No row-level outcomes were read now and no new winner was inferred.
An accepted exposure-aware scope is necessary; a historical holdout cannot be
made prospectively untouched by relabeling or resealing it.

## I. Reproducibility and integrity

`genuine_smoke/summary.json` records four independently hashed family manifests.
Each fixed three-file bundle was created exclusively, verified immediately and
replayed without scientific dependencies. Manifests contain input fingerprints,
OOF identities, requests, fold pipeline records, packages/environment and twelve
explicit code/config/codebook hashes. `verification.json` supplements this with
the full preservation baseline/current inventory and source/test hashes. These
hashes establish identity/integrity, not authenticated source approval or model
effectiveness. Exclusive files are immutable by workflow, not OS write protection.

Ordinary per-bundle IO failure rolls back that bundle's own files. No overall
summary is written until every family bundle validates; process crashes are not
an atomic multi-family transaction. A missing summary means incomplete export.
Historical outputs never serve as fallback inputs.

Reproduce fixture execution with the approved pinned target and command in D,
using a **new unused output directory**. Do not rerun into this bundle. Temporary
packages are not a permanent research environment or a long-term environment
archive. A future release needs its accepted environment/wheel/source provenance,
model/preprocessing artifact formats, accepted manifests and selected-system
hashes. No trained research model or safe persistence approval currently exists.

The software explicitly rejects forbidden predictor names, malformed inputs,
group/fold crossings, missing classes, nonfinite values, prediction-ID mismatches
and incompatible U1 behavior. Supplied metadata validation cannot discover
unrecorded campaign/template relationships, authenticate provenance, prevent a
trusted callback from reading external files, or establish absence of source
shortcuts. No annotation circularity was introduced: fixture labels/signals are
artificial and no behavioral pseudo-ground-truth or learned behavioral model was
created. Evidence and attribution remain separate; no final attribution/risk
claim is made.

## J. Manuscript readiness and remaining application boundary

Methods sections can now cite genuine estimator classes, explicit pipeline
boundaries, matched OOF identities, synthetic regression/conformance evidence,
metric definitions, ablation plumbing and reproducibility mechanisms. The
dataset/attrition tables must retain pending entries and historical-count labels.
Results/discussion cannot claim research accuracy, SE-BRL effectiveness,
source-independent generalization, calibrated risk, full twelve-rule scientific
validation, resource superiority or final-system acceptance from these fixtures.

Historical Notebook 05 remains LR-only under its old scope, including PhiUSIIL
E2/E3 proxy experiments and historical UCI/ISCX E1 naming; those are not renamed
as current approved Web or U1 evidence. Its old four-RQ interpretation is not the
current approved five-RQ methodology. Do not run it wholesale against repaired
inputs. The new adapters operate in the separate D9/synthetic runner path.

The app's rule-based/mock behavior, legacy runtime None slots and fail-closed
unavailable-model behavior remain unchanged. Genuine offline adapters do not
constitute a deployed classifier, calibrated probability, evidence-attribution
implementation or live Gmail integration validation. Integrate only a compatible
selected/frozen deterministic analytical bundle. Transformer augmentation remains
a separately deferred future item; the older amendment proposal was preserved.

Technical implementation references, not protocol amendments:
[sklearn Pipeline/ColumnTransformer](https://scikit-learn.org/1.6/modules/compose.html),
[LinearSVC scoring](https://scikit-learn.org/1.6/modules/generated/sklearn.svm.LinearSVC.html),
[XGBoost 2.1 API](https://xgboost.readthedocs.io/en/release_2.1.0/python/python_api.html).
Library persistence requires a deliberate safe-format decision; see
[sklearn persistence guidance](https://scikit-learn.org/1.6/model_persistence.html).
The pinned releases were checked against their primary PyPI package records;
they are explicit verification pins, not a claim to use newest releases.

## K. Git state and preservation

Initial branch `main`, HEAD `6bded57d38e9b83ba718d7795b97e2130128c23f`,
upstream `origin/main`; 22 unstaged tracked paths, 49 untracked files, none staged.
`origin` is configured to `LichSavant/Thesis_Protoype_Test.git`; `se-brl` points to
`LichSavant/CS4101-Thesis2-SE-BRL.git`. Do not assume a future push to upstream
targets the thesis repository. No live GitHub state was synchronized/changed.

A 273-file starting SHA-256 baseline includes existing tracked/untracked work,
all experiment/database files, and Git index/config. Final comparison found six
intentional existing-file changes listed in C, zero removals, and all remaining
267 baseline files unchanged. Existing datasets/LFS materializations, Notebook
01/03/04 repairs, historical Notebook 05, all metrics/predictions/plots/
coefficients/partitions/manifests, earlier research drafts and November 4 evidence
remain byte-identical to this task's starting baseline. The persistent database
is unchanged. Opaque preservation hashing did not parse predictions or Email
contents. Earlier unsaved buffers or changes preceding this baseline cannot be
proven preserved by this check.

Final status: **24 unstaged tracked paths, 70 untracked files, none staged**;
same branch/HEAD/upstream/remotes. Nineteen pre-existing LFS payloads still appear
modified under filter-disabled status; no LFS repair/materialization occurred.
The two additional tracked modifications are ML README/models documentation;
other changes are to previously untracked files or new task files. Full final
paths/hashes are in `verification.json` (its own hash omitted to avoid recursion).

Git reads used `GIT_OPTIONAL_LOCKS=0`, with LFS filters disabled for status. No
fetch/pull/switch/reset/clean/restore/stage/commit/push, index refresh, remote or
Git configuration mutation occurred. Existing inaccessible `.pytest_cache`
warnings were left alone. Builds/tests used task storage; no environment files,
credentials, wire contracts or application database were edited.

## L. Shortest path to completion / Context for ChatGPT

1. **Next single action:** obtain a dated Email development acceptance packet
   from Vera/researchers that resolves CEAS membership against the historical
   assignment universe and supplies the source/native-label/lineage/screening/
   group evidence, development-only delivery and explicit dictionary/rule freeze
   needed for a bounded dataset-to-feature check. Do not request the entire
   thesis or new behavioral annotations; identify the missing artifacts in H.
2. Dhanwil validates the accepted development payloads and supplied assignments
   through the existing boundaries, with no partition regeneration or model fit.
   Fix only observed mechanical discrepancies; record scientific deviations.
3. Freeze candidate budgets/nesting/score/calibration/uncertainty/efficiency
   settings before comparative research fits. Then implement that accepted
   research launch/search/calibration/selection path using the verified adapters,
   run authorized development-only E1/E2/E3, and preserve complete immutable
   candidate/ablation/OOF/model artifacts. Independent accepted U1 can progress
   separately; it cannot replace the Email behavioral question.
4. Apply Table 4.9, lock the selected family and analytical versions, fit only the
   authorized final calibration/threshold procedure, integrate/test the frozen
   deterministic risk/explanation/system bundle, and evaluate only under the
   accepted exposure-aware evaluation plan. Document empirical findings and
   limitations before final handoff. No transformer is required for this scope.

**Pasteable context:** Nov.5 main/6bded57, no Git mutation. Genuine LR/LinearSVC/
RF/XGB adapters now run through the existing matched five-fold synthetic runner.
Fresh 977 ML/backend, 25 frontend, type checks/builds and 275 static cells passed;
382 neighbors passed after final preflight wording. User explicitly approved six
pinned packages in temporary host storage only. Saved generated-fixture smoke:
180 genuine fits, four verified exclusive bundles, zero research/calibrator fits
or selections. Six existing files changed; protected baseline artifacts/DB
preserved. Actual D10 remains blocked by branch acceptance and experiment freeze;
Email CEAS/lineage/groups/rules/dictionary/custody is the next bounded research
input, not a reason to retrain on historical inputs. D11 deferred. Read this
report and verification.json; preserve all existing research work.
