# Scientific unblocking and experiment-readiness sprint

November 5, 2026, Asia/Manila. Governing scope: approved deterministic SE-BRL.
**No scientific approval, replacement assignment or research fit was created.**

## A. Completed work and navigation

All four workstreams were pursued. The bounded lineage search is closed with
BLOCKED outcome; the contingency is a prospective approved-source protocol for
review. A twelve-indicator traceability audit, exact ordered predictor candidate,
research decision sheet and acceptance register are complete as proposals.
The existing preflight now explicitly enumerates ten failed admission conditions
and supplies a closed research-entry guard; it cannot turn documentation or
synthetic results into authorization.

| Deliverable | Location |
| --- | --- |
| A: final bounded recovery evidence | [lineage_recovery.md](lineage_recovery.md) |
| B: prospective identity/group/partition/exposure contingency | [replacement_protocol.md](replacement_protocol.md) |
| C1: twelve indicators, code/tests/ambiguities | [deterministic_codebook_audit.md](deterministic_codebook_audit.md) |
| C2: candidate E1/E2/E3 order/types/missingness | [predictor_freeze_candidate.md](predictor_freeze_candidate.md) |
| D: candidate/budget/calibration/selection decisions | [experiment_settings_decisions.md](experiment_settings_decisions.md) |
| D5: ten FAIL requirements and guarded entry | [real_data_preflight.md](real_data_preflight.md) |
| Evidence, authority and Pending approvals | [acceptance_register.md](acceptance_register.md) |
| Minimum evidence/implementation path | [next_actions.md](next_actions.md) |

Prior packets are retained and referenced, rather than republished:
[Email acceptance](../2026-11-05_email_acceptance/README.md),
[lineage audit](../2026-11-05_email_lineage/README.md),
[deterministic checkpoint](../2026-11-05_deterministic_completion/README.md),
[November 4 handoff](../2026-11-04_master_completion/README.md).
Those documents are evidence of prior work and decisions, not automatic approval.

The approved 155-page proposal was freshly read in memory; SHA-256
`283338c5535c5553e35266f5083a6380e014637e63d42161c659238e257ad1fe`.
Key provisions: Section 4.2.1/Tables 4.1-4.2 (PDF pp.57-60), Sections 4.3.1-4.3.3/
Table 4.4 (pp.63-65), Section 4.3.4/Tables 4.5-4.6 (pp.66-68), Section 4.3.5/
Tables 4.7-4.9 (pp.69-75). PDF references are viewer page numbers. Text extraction,
not figure/layout rendering, was used. No amendment to the approved file.

## B. Email lineage result

**BLOCKED: zero authenticated historical-to-repaired record pairs.** One bounded
metadata/source/history search found no bridge candidate. Repaired endpoint
counts/ambiguity remain unknown; no reconstruction from labels, ordinal
coincidence or file hashes. The historical 38,759/full, 21,447/non-CEAS and
17,312/CEAS scenario denominators remain previous metadata evidence, not new
eligible populations. Recovery is closed for this sprint; the independent
prospective route does not depend on inventing a legacy crosswalk.

## C. Replacement assignment protocol

The reviewable proposal specifies population alternatives, forward-only stable
identity/ingestion receipts, separate duplicate semantics, conservative relation
reconciliation, collision/conflict handling, composition-aware group allocation,
five development folds, calibration isolation, reproducibility and exposure
alternatives. Exact technical recommendations are labeled Pending.

No CEAS option, grouping threshold, source or evaluation route was adopted. No
group/partition/fold was generated. A new split of historically used corpora
cannot be called untouched. Without independently evidenced unexposed material,
final confirmatory validation remains blocked; an explicitly approved
development/exploratory milestone does not establish full thesis completion.

## D. Deterministic feature-freeze candidate

Canonical taxonomy/state boundaries are traceable to the approved paper. Runtime
candidate rule v0.2.0 and pre_freeze codebook v0.1.0 are unchanged. The proposal
does not require expert behavioral annotation or a supervised behavioral model.
All twelve indicators have a code/evidence/test/ambiguity row in the audit.

Mechanical candidate E1 is ordered `model_text`, `conventional:text_char_count`,
`conventional:text_word_count`; E2 is the existing canonical eight support/mask
bits; E3 concatenates them (3/8/11 raw columns). Schema/order and all four adapter
configuration widths were checked without fitting. The candidate text-parameter
types and pinned vectorizer float64 dtype were inspected without fitting.
This is not a real feature table or scientific acceptance of the proposed E1
scope. Fuller relation/header/URL features require accepted opportunity/missingness.

Notebook/runtime lexical criteria, original-field locators, trust inputs,
language and partial-availability aggregation require researcher decisions.
Those are not unambiguous coding repairs. No notebook or rule semantics changed;
their guards remain. Core E1 versus full Table 4.7 coverage must be accepted
explicitly. Legacy runtime learned-z placeholders do not govern deterministic
offline experimentation or introduce a new training/annotation prerequisite.

## E. Experiment engineering readiness

Genuine LR/LinearSVC/RandomForest/XGB adapters and existing D9/runner/metric/
reproducibility boundaries were inspected and freshly regression-tested. Tests
exercise fresh training-fold transforms, explicit parameters/seeds, correct
positive class, SVM margin handling, raw uncalibrated probabilities, training-only
class weighting, matched OOF identities, technical-only U1 and output integrity.

The current software is not a complete real-data experiment launcher: research
search/nesting, cross-fitted calibrators, Table 4.9 decision execution, accepted
bundle verification and safe selected-model/pipeline persistence still need
implementation against accepted settings. No pickle loader or persistence
dependency was introduced. Approval alone cannot make those missing mechanics
exist. Tests of supplied/trusted interfaces do not sandbox arbitrary Python or
authenticate upstream scientific evidence.

## F. Research authorization

**All ten research requirements FAIL.** See the preflight report for each reason:
population; source/class evidence; identity; group/partition protocol; development
custody; deterministic rule freeze; matched dictionaries; candidate/evaluation
settings; actual-data leakage evidence; accepted research reproducibility.
Existing software checks are not themselves accepted branch evidence.

`research_fit_gate()` has no approval flag/JSON/reference-string override.
`require_research_fitting()` raises `research_fitting_not_authorized`.
`--research-gate-only` reports the closed gate without opening corpus files.
This is deliberate admission closure pending a trusted verifier and research
entry point; it does not falsely authenticate researcher/adviser sign-off.
No real-data fitting path was enabled by this sprint.

## G. Exact tests and limitations

Existing application Python 3.12.10 / pytest 8.4.2 was used. Previously approved
temporary packages were reused, not installed: NumPy 2.2.6, SciPy 1.15.3,
scikit-learn 1.6.1, XGBoost 2.1.4, joblib 1.5.1, threadpoolctl 3.6.0.
Scientific imports were independently verified. Host execution was needed for
read access to these host-owned temporary packages, as recorded previously.

`<T>` = `<user-profile>/AppData/Local/Temp/sebrl-scientific-unblocking-20261105-x12hng8_`.
Python tests set `TEMP=TMP=<T>`, `PYTHONDONTWRITEBYTECODE=1`,
`DATABASE_URL=sqlite:///:memory:` and
`PYTHONPATH=<user-profile>/AppData/Local/Temp/sebrl-genuine-approved-20261105/science`.
No application environment replacement or database write.

| Executed check | Result |
| --- | --- |
| `.venv/Scripts/python -B -m pytest ml/tests/test_preflight.py ml/tests/test_classifier_adapters.py ml/tests/test_rule_extraction.py ml/tests/test_context_detectors.py -q --tb=short -p no:cacheprovider --basetemp <T>/focused` | **131 passed**, 12.10 s |
| `.venv/Scripts/python -B -m pytest ml/tests backend/tests -q --tb=short -p no:cacheprovider --basetemp <T>/full` | **980 passed**, 31.91 s; one existing installed Starlette/httpx deprecation warning |
| `.venv/Scripts/python -B -m ml.preflight --research-gate-only` | Native exit **2** (expected closed admission), ten FAIL checks; fitting false |
| JSON-read six notebooks and `ast.parse` all code cells | **275 syntax-valid cells**, zero executed |
| Candidate dictionary JSON order/schema + four factories' E1/E2/E3 widths | Passed 3/8/11 raw-column checks, seven forbidden names rejected; **zero model fits** in this check |
| Candidate explicit TF-IDF parameter object and pinned library dtype inspection | Valid types, float64 observed; **zero fits** |
| New documentation links/whitespace, source syntax, scoped preservation/Git checks | Passed in final review |

The complete-test-plus-gate PowerShell command returned a nonzero wrapper result
after all tests passed because the gate intentionally denies admission. A direct
Python subprocess probe independently verified native gate exit 2. No test
failure was hidden as authorization failure. Three focused tests were added for
the new gate (ten obligations/no reads, self-declared approval rejection and
read-only CLI); no redundant model tests were added to inflate counts.

The existing full suite includes genuine synthetic fits and its fixture smoke
test. Those outputs stay in task-owned test storage; no new large synthetic
research bundle was generated in the checkout. Prior saved 180-fit smoke bundles
are preserved as previous evidence, not relabeled as a new standalone run.
No actual research observation was used to fit any estimator or calibrator.

Frontend code did not change; frontend checks were not rerun. Prior 25 frontend
passes remain historical. No datasets downloaded, new packages installed,
analytical notebooks executed, historical outcomes inspected or empirical model
performance/latency claim made.

## H. D1-D16 position

| Task | Engineering readiness | Scientific acceptance | Empirical research completion |
| --- | --- | --- | --- |
| D1 protocol/scope | Reconciled, concrete contingency/settings decisions prepared | Pending role/version/exposure decisions; approved deterministic architecture retained | No new research execution |
| D2 preprocessing | Contracts retained; forward recipe proposed | Pending source/identity/screening specification | No actual preparation |
| D3 data/source/labels | Existing evidence checked, recovery closed | Source/native-label/terms/attrition evidence incomplete | Prior aggregates only |
| D4 isolation | Validators verified; composition-aware recipe proposed, not implemented | Pending prospective group/partition/exposure policy | No replacement assignments |
| D5 deterministic indicators | Candidate twelve-row traceability/tests ready; implementation preserved | Pending rule/locator/language/partial-mask freeze | No source-level conformance run |
| D6 alignment/availability | Schema 3/8/11 and contract tests verified | Pending real accepted dictionary/data/rules | No dataset-to-feature verification |
| D7 leakage/confounding | Safeguards/tests and planned sensitivities available | Actual-data relationship/source/exposure evidence incomplete | No absence-of-leakage claim |
| D8 software checks | **Verified checkpoint: 980 Python / 275 static cells** | Software result only | No empirical classifier finding |
| D9 handoff | Strict existing loader/exports verified | Real input/custody/acceptance absent | No research handoff generated |
| D10 models | Four genuine adapters verified; research orchestrator/search/selection incomplete | Settings/data/fit authorization Pending | Synthetic fits only; real training blocked |
| D11 transformer | Deferred | Outside current authorized deterministic implementation | None required for deterministic milestone |
| D12 evaluation | Metrics primitives verified; calibration fitting not implemented | Score/calibration/threshold choices Pending | Zero research calibrator fits |
| D13 CV/ablations | Matched supplied-fold/ablation controls verified | Accepted real nesting/budgets/sensitivity plan Pending | Fixtures only |
| D14 reproducibility | Exclusive synthetic hashes and package/config records available | Accepted source/model/persistence/environment freeze incomplete | No complete real-model bundle |
| D15 manuscript | Decision-ready methods/limitations package prepared | Empirical conclusions and prospective scope Pending | No fabricated effectiveness/generalization claim |
| D16 freeze/handoff | Technical handoff prepared | Final selection/calibration/risk/system/evaluation blocked | No final release or confirmatory evaluation |

## I. Files, Git and preservation

Existing files modified: `ml/preflight.py` (ten-condition closed admission report,
entry guard and gate-only CLI), `ml/tests/test_preflight.py` (three targeted
regressions plus normal-report assertion). Nine new Markdown documents are this
directory's requested deliverables. No other existing file is intentionally
changed. No notebook, codebook, rule, predictor derivation, dataset, assignment,
historical result or decision draft was modified.

Initial branch main, HEAD `6bded57d38e9b83ba718d7795b97e2130128c23f`, upstream
origin/main, 24 unstaged tracked / 78 untracked / zero staged. Final status is
24 unstaged tracked / 87 untracked / zero staged; same branch/HEAD/upstream.
`origin` remains configured to `LichSavant/Thesis_Protoype_Test.git`, and `se-brl`
to `LichSavant/CS4101-Thesis2-SE-BRL.git`. Future pushes must not assume origin is
the thesis target. No GitHub state was synchronized/changed.

A 302-file starting baseline records safe source/metadata hashes and protected
data/notebook/historical-result/database size+mtime metadata. Timestamps are
stored as exact decimal strings, avoiding the preceding audit's JSON precision
issue. Final review finds only the two intended existing-source changes, no
removals, and nine new documents. Safe hashes and protected size/mtime records
otherwise agree. Protected contents were not opened for preservation hashing;
this is not a new cryptographic proof of payload byte identity. No command
targeted those files for writing. Previous source/model artifact hashes remain
their documented historical integrity evidence. Unsaved buffers were not read.

Git reads used GIT_OPTIONAL_LOCKS=0 and filter-disabled status. No fetch, pull,
branch switch, index refresh, stage, commit, push, reset, clean, remote/config
change or historical overwrite. The existing inaccessible .pytest_cache warning
and LFS-materialized dataset status were left alone. The persistent application
database's protected metadata is unchanged; tests used in-memory SQLite.

## J. Minimum next actions / Context for ChatGPT

The next action is **joint review of the prospective protocol/exposure scope**,
alongside the deterministic feature and experiment decision sheets. Custodian
source facts, researcher/adviser choices and Dhanwil's later implementation are
separated in the acceptance register. Do not keep re-auditing the absent bridge.

The minimum path is three substantive packets: source/role/prospective lineage/
groups/exposure; deterministic rule/dictionary semantics; development evaluation/
custody/run settings. Then implement/test accepted prospective preparation and
guarded research mechanics, execute an explicitly authorized no-fit development
check, and obtain explicit fit authorization after ten conditions are verified.
No final operational threshold numbers, new dataset, transformer or annotation
requirement is introduced as a blanket prerequisite. Exact order/owners and the
remaining implementation are in next_actions.md.

**Pasteable context:** Nov.5 main/6bded57. One bounded Email recovery search
closed BLOCKED; no speculative pairs. A complete prospective identity/group/
partition/exposure proposal and twelve-indicator/E1-E2-E3/settings candidates
are ready for review, all proposed choices Pending. Only ml/preflight.py and its
test changed; nine new docs. Ten-condition research gate always fails closed,
with no approval-string/JSON bypass; accepted-bundle verifier and research
launcher/search/calibrator/persistence still need accepted-setting implementation.
Fresh 131 focused, 980 ML/backend, 275 static cells passed; no new frontend run,
install, data preparation/assignment generation or research fit. Prior artifacts
preserved under stated hash/stat limits. Next: researcher/adviser protocol and
exposure review plus custodian source facts, not another empty lineage search
or an immediate training run. D11 remains deferred; thesis not declared complete.
