# Experiment configuration: requirements versus executable options

Proposal §4.3.5/Tables 4.7–4.9 governs: LR, Linear SVM, RF and XGBoost;
matched Email E1/E2/E3 and separately evaluated U1 branches; grouped development
CV; train-fold preprocessing; primary pooled OOF PR-AUC; LR confirmatory E3–E1;
implementation family selection within E3/U1, never E1/E2 deployment shopping;
2,000 paired whole-group bootstrap resamples and 95% CI; frozen criteria before
final calibration/threshold/system lock and any permitted final evaluation.

| Family | Governing Table 4.8 space | Still requires a research configuration |
| --- | --- | --- |
| LR | C .01/.1/1/10 × None/balanced, L2, max_iter 2000: eight combinations | Solver, tolerance/intercept/dtype/seeds, exact search budget/failure policy |
| Linear SVM | C .01/.1/1/10 × None/balanced: eight | LinearSVC loss/dual/tolerance/max_iter/intercept and score mapping |
| RF | trees 300/600 × depth None/20/40 × leaf 1/3/5 × features sqrt/.5 × balanced/balanced_subsample: 72 | Criterion/bootstrap/thread/seed/budget and interpretation/attribution protocol |
| XGBoost | depth 3/6 × eta .03/.1 × subsample .8/1 × columns .8/1 × child 1/5 × lambda 1/5: 64 | Tree count, other complete settings/budget/seeds; training-only imbalance ratio |

These are paper spaces, not permission to run them. New tests use tiny explicit
fixture parameters and seed 17; they are not research freeze defaults. Existing
approved temporary scientific environment is NumPy 2.2.6, SciPy 1.15.3,
scikit-learn 1.6.1, XGBoost 2.1.4, joblib 1.5.1, threadpoolctl 3.6.0.

## Newly implemented optional nested procedure

`ml/experiment_engine.py` requires typed explicit candidates, their exact
preprocessing and seeds, configurations, sigmoid parameters/score transform/
clip epsilon, calibration bins, threshold policy and `synthetic:` reference.
No grids, numeric research settings or new group/fold assignments are generated.

For each of the five supplied outer folds:

1. Tune explicit candidates on remaining supplied folds using fresh complete
   preprocessing+classifier fits. Pool inner raw-score AP; equal AP uses the
   declared candidate tuple order. This precise search/tie rule is an option.
2. Refit the selected base pipeline on outer training only.
3. Generate calibration scores on outer-training cross-fits. Each held-out
   calibration fold is excluded from **both** base training and that base's
   parameter search, which is repeated inside the remaining folds. Fit the
   explicitly configured regularized logistic sigmoid on these scores/targets.
4. Use either an explicit fixed probability threshold, or generate additional
   outer-training cross-fits of the **complete tuned and calibrated pipeline**,
   maximize training F1 and resolve equal maxima by smallest observed probability.
5. Score outer validation only after all learned choices; aggregate exactly one
   calibrated OOF prediction per ID/configuration. Report fold thresholds and
   pooled confusion counts from those actual fold decisions; do not apply an
   artificial common threshold when thresholds differ.

Every nonempty supplied fold must have both classes; no automatic replacement
split/resampling is made. Groups remain indivisible. Convergence/candidate
failure aborts, with no silent family/config fallback or completed bundle.
Tests alter one outer fold's targets and verify that fold's selected parameters,
preprocessor audit, calibrator, threshold, traces and prediction scores do not
change. Test labels still determine its evaluation metrics, as expected.

This is nested **development** calibration for candidate assessment. It never
opens the reserved calibration partition or determines final operational risk
thresholds. Its pooled sigmoid-score AP versus raw-score primary convention
must be accepted before research outcomes. Raw SVM margins are not probabilities;
logit-probability calibration transform is rejected for SVM. No behavioral
predictor is trained. Brier/ECE/reliability analysis uses explicit bins.

For c candidates and m supplied training folds, a calibrated pipeline requires
`c*m*m + m + 1` base fits. One outer fold with four training folds, two candidates
and nested F1 thresholding needs `37 + 4*22 = 125` base fits: 625 over five outer
folds, plus 25 sigmoid fits. The genuine tests exercise that boundary. Budget
feasibility on the research corpus is unverified and must be frozen prospectively.

## Selection, ablations and efficiency

`ml/model_selection.py` implements a synthetic Table 4.9 option: require the
explicit family roster and matched five-fold OOF metadata; recompute AP and
calibration/operating summaries; enforce explicit SRS dispositions; compare
paired group-bootstrap differences to caller-supplied delta_PR; stop when
inconclusive. Only practically equivalent contenders reach declared Brier/ECE
then p95/throughput/memory/size and explicit simplicity ranking. LR preference
applies only to a final tied set. No default delta_PR or hard SRS number exists.
An explicit None limit means caller-declared non-applicability; it is not evidence
that researchers have accepted no limit. Missing benchmark/measurement or required
candidate evidence fails. The exact bootstrap interval/undefined-draw and tie
conventions are options requiring acceptance, not implications of Table 4.9.

Existing `dimension_ablations` omits each dimension's support+availability pair;
the new engine accepts explicit predictor omissions and preserves the same
population/folds. Existing matched comparison, source-stratum metrics and paired
group-bootstrap functions remain usable. Source strata alone cannot establish
source-independent performance. Fitted source-only/normalized-format diagnostics
await accepted features/data/experimental authorization; no such research was run.

Existing `inference_benchmark.py` times a trusted model-only callback with explicit
warmups/repetitions/batch/thread description, p50/p95, throughput, optional memory
probe and serialized size. A thread reference does not configure/authenticate
threads; a caller probe does not establish process-wide peak memory. A future
accepted benchmark must freeze actual hardware/runtime/thread/batch/sample/memory
scope. Model-only measurements are separate from feature/API/application latency.
The selector requires an explicit memory-evidence policy. It either requires a
numerical measurement or allows unavailable memory only when no memory limit
applies; if any tied contender lacks a measurement, the memory tie-break is
explicitly skipped. A declared memory limit can never be bypassed. This supports
the paper's “where available” clause without inventing a memory/SRS number or
treating a missing measurement as zero. The scientific benchmark policy is still
Pending; no option is automatically accepted for research.

## Safe complete artifacts

`model_persistence.py`: sklearn pipeline in skops; XGB native JSON **plus** skops
preprocessor. No pickle/joblib execution format; no automatically trusted unknown
types. Independent manifest digest, fixed paths/files, hashes, exact package/
adapter versions and encoded/decompressed resource caps are checked before load.
The digest must come from trusted custody, not the same untrusted download.

`experiment_artifacts.py` saves every returned outer model, exact sigmoid JSON
state/threshold, ordered dictionaries, candidate settings/search audits, folds,
OOF metadata, input/request/code hashes and environment records. A completion
manifest is written last; exclusive creation rejects existing destinations and
ordinary IO failure removes only this call's created files. Process death may
leave an incomplete directory, which must not be treated as a complete run.
Learned vocabularies can disclose tokens: future research models require
restricted custody. This format currently labels output SYNTHETIC RESULT only;
it is not a final selected/refitted system or research launch authorization.

Pending P9/P10/P11: solver/dtype/config/budgets, nesting/score/calibration/
threshold policies, bins/seeds, bootstrap conventions/tolerance/multiplicity,
SRS applicability, benchmark and simplicity/attribution criteria, trusted
accepted-data launcher and final operational calibration/evaluation protocol.
