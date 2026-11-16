# D. Research experiment decision sheet

**Pending settings, not an executable research configuration.** The approved
paper fixes the four families, matched grouped development comparisons, LR
confirmatory E3-v-E1 contrast, E3 implementation representation, primary PR-AUC
and the Table 4.9 hierarchy. See Sections 4.3.5.1-4.3.5.3, PDF pp.69-75. Explicit
paper requirements are not reopened; implementation recommendations below are
not automatically adopted. No real candidate fit or selection was performed.

## Candidate spaces and budgets

| Family | Approved Table 4.8 search space | Specific remaining setting / recommendation for review |
| --- | --- | --- |
| LR | C .01/.1/1/10; L2; max_iter 2000; class_weight None/balanced | Eight combinations. Propose liblinear, tol 1e-4, intercept true, seed 42; confirm solver/dtype and compare convergence fairly |
| Linear SVM | C .01/.1/1/10; class_weight None/balanced | Eight combinations. Propose LinearSVC L2/squared_hinge, dual false, max_iter 2000, tol 1e-4, intercept true, seed 42; fail rather than silently accept nonconvergence |
| RF | 300/600 trees; depth None/20/40; leaf 1/3/5; max_features sqrt/.5; balanced/balanced_subsample | 72 combinations if fully crossed. Propose Gini, bootstrap true, CPU n_jobs 1 and seed 42; exact complete parameter record required |
| XGBoost | depth 3/6; eta .03/.1; subsample .8/1; colsample .8/1; child weight 1/5; lambda 1/5; fold-local scale_pos_weight where applicable | 64 combinations before extra approved choices. Tree count is not fixed by this table: propose fixed 300 for review, CPU hist/gbtree, binary:logistic/logloss, n_jobs 1, seed 42, training-only negative/positive ratio. No eval_set/early-stopping shortcut |

Budget options for a dated researcher decision: full grids (8/8/72/64), or
predeclared fixed parameter subsets, e.g. 8/8/24/24 with deterministic sampling
without replacement before any outcome. Full grids are a transparent reference
recommendation, **not an authorized computational budget**. Freeze parameter
enumeration, sampler/seed if used, tie rules, failure/convergence policy, fit/time
limits and identical representation budgets. Do not adapt budgets after seeing
which family looks strongest. No budget pilot on research data is authorized.

Proposed nested assessment: five supplied outer development folds; use the
remaining four supplied fold labels as inner tuning folds, preserving groups
without generating a new partition manifest. For full grids this is 3,040 inner
candidate fits per representation (5 x 4 x 152), or 9,120 over E1/E2/E3 before
outer refits/calibration. Thus budget feasibility needs an explicit decision;
the small synthetic tests do not establish resource feasibility on the corpus.
Initial LR confirmatory execution may be separately bounded if approved, but
does not complete four-family implementation selection.

## Decision register

| Item | Approved requirement / current software | Recommendation or exact decision needed | Status |
| --- | --- | --- | --- |
| Population/features | Same accepted IDs/groups/folds for E1/E2/E3; D9 guards exist | Accept the prospective population and predictor candidate; do not use historical CEAS membership or a reference string as approval | Pending |
| Outer/inner CV | Five grouped development folds; runner consumes supplied folds | Freeze nested tuning design and exact inner group plans; recommendation above requires both-class feasibility and no outer-validation fit | Pending |
| Selection metric | Pooled development OOF PR-AUC primary | Freeze non-interpolated AP versus PR integration convention. Recommend existing AP implementation, not trapezoidal PR area | Pending convention; paper primary metric governs |
| Score comparability | SVM margins are not probabilities; calibration assessment is required where probabilities drive risk | Recommend pooled group-cross-fitted sigmoid probabilities for comparable primary scoring, raw-score AP as descriptive. Accept/reject before fits; do not compare arbitrary margin/probability scales opportunistically | Pending |
| Calibration | No fitted calibrator exists; Brier/ECE/reliability primitives exist | Freeze train-only nested/cross-fitted sigmoid procedure, regularization/class-weight and score transform. Each calibration-held-out score must come from the complete tuning pipeline without that record's labels; tuning must also nest inside that boundary | Pending |
| Thresholds | No test selection; runner receives explicit threshold in supplied units | Propose development-training-only cross-fitted F1 operating threshold for descriptive metrics; deterministic smallest-maximizer tie rule. Final operational thresholds follow selected-model calibration/risk protocol separately | Pending |
| Seeds | Explicit adapter/runner seeds verified | Propose 42 for research split/search/bootstrap schedules, record each independently; fixed order and versions. Synthetic seed 17 is not a research freeze | Pending |
| Uncertainty | Paper: 2,000 paired whole-group bootstrap resamples, 95% CI | Freeze paired estimand/multiplicities, percentile/quantile rule, required valid-draw handling and comparison multiplicity. Existing one-class draws are counted undefined, not silently redrawn | Pending conventions; 2,000/95% already specified |
| Practical equivalence | Table 4.9 uses justified delta_PR; no numeric value supplied | Researchers/adviser justify tolerance before candidate outputs; define inconclusive outcomes and optional calibration tolerance only if needed. No invented number or automatic tie from CI crossing zero | Pending |
| Reliability | Brier/ECE fixed binning/reliability required | Propose ten equal-width bins on [0,1], absolute artifact-weighted ECE, empty bins explicit, p=1 in last bin. Existing code [left,right) differs from some library conventions; freeze this exact convention | Pending |
| Ablations | Matched folds and fixed family for representation contrasts | LR principal E3-v-E1; four dimension support+mask pairs omitted together; explicit conventional-family omissions; source-only, normalized-format and source strata. Separate confirmatory versus exploratory comparisons | Pending execution plan |
| Efficiency | Common environment, p50/p95 model-only latency, throughput, memory/model size | Prior H10 recommendation: CPU single thread, warmup 100, 1,000 timed calls; latency batch 1, separate throughput batch 32. Freeze hardware/software/dtypes/sample schedule/memory method before comparison; these counts are unapproved recommendations | Pending |
| Hard SRS gates | Apply only actually approved recall/precision/p95/memory limits | Record each real requirement or accepted non-applicability; unknown is not no-limit. No limits are invented | Pending |
| Final selection | Table 4.9 hierarchy for Email-E3, Web-E3 and separate U1 | Validity -> approved hard gates -> primary AP -> paired uncertainty/equivalence -> calibration -> p95/throughput/memory/size -> simplicity; LR tie preference only at final tied stage -> freeze. No sealed reselection | Approved hierarchy; settings/implementation Pending |
| Persistence/release | No safe model serialization or selected-system bundle implemented | Select safe pipeline/model format, trusted type policy and reload/version/hash verification; XGB native JSON alone omits preprocessing. Do not introduce pickle/untrusted loading or install persistence tools without approval | Pending |

Calibrator cross-fitting adds substantial nested tuning/refitting beyond the
fit-count illustration. A calibrator trained on a score that used its own
label during hyperparameter selection is not a clean full-pipeline held-out
score. Freeze the exact nesting and computational envelope before building it.
The current runner does not implement research search, calibration fitting,
selection, research model persistence or final refit. Approval alone therefore
does not launch experiments: accepted mechanics must still be implemented/tested.

## Independently verified engineering

Current adapters call genuine sklearn LR, LinearSVC, RandomForestClassifier and
XGBClassifier. Fresh tests cover fold-local vocabulary/IDF/imputation/scaling,
finite typed predictors, binary orientation, SVM margin/null probability, raw
uncalibrated probabilities for other families, training-only XGB class ratio,
single-use pipelines, deterministic reruns, exact OOF identities and immutable
synthetic bundle checks. Data-facing metadata is excluded from predictors.
These are trusted in-memory interfaces, not a sandbox against arbitrary code.

Fresh 131 focused and 980 ML/backend tests passed; no research fits/calibrators,
new large simulation bundle or candidate winner. Existing 180-fit smoke artifacts
remain historical immutable fixture evidence. Safe serialization is a remaining
engineering task after format acceptance, not falsely claimed verified here.
