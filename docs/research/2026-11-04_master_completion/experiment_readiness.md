# Experiment, metric, ablation and reproducibility readiness

Result category: VERIFIED SOFTWARE RESULT. Demonstration outputs are separately
labeled SYNTHETIC RESULT. All real research preparation/training/selection remains
BLOCKED. No historical outcome values were inspected.

## Exact engineering changes

- `ml/evaluation_metrics.py`: explicit positive=1/higher-score-is-phishing;
  confusion/precision/recall/F1/specificity/balanced accuracy/MCC; tie-grouped
  non-interpolated average precision and ROC-AUC; PR curve points; Brier,
  caller-edged reliability/ECE; paired whole-group AP-difference bootstrap.
  Undefined one-class/zero-denominator statistics remain null, not fabricated 0.
- `ml/development_runner.py`: validated D9-only synthetic input, explicit
  family/config/seed/parameters/reference, one fresh pipeline per fold, labels
  separate from predictors, no validation labels passed to score, strict score
  orientation and one-to-one OOF IDs, fold/pooled reports, dimension/family
  omissions, fixed-classifier representation contrasts, source slices, exclusive
  hashed bundle writer and verifier.
- `ml/inference_benchmark.py`: trusted model-only prediction callback on an
  already numeric compatible batch, explicit warmup/repetitions/batch/thread
  reference, p50/p95 batch latency and throughput. Resource/model size remain
  unavailable unless measured/supplied. No selection occurs.
- `ml/synthetic_demo.py`: standalone fixture-only demonstration/replay command.
  Artificial feature signal equals constructed target to exercise plumbing;
  these scores have no thesis-performance interpretation.
- `ml/development_experiments.py`: shared numeric validator converts unrepresentable
  integer overflow into existing invalid_numeric_predictor contract error.
- `ml/uci_preparation.py`: reuses that validator before technical dispatch. No
  target mapping, source eligibility, native code, grouping, fold or rule change.
- Five new test files cover these modules and numeric failure boundaries.

`run_synthetic_cv` is intentionally labeled synthetic and is not an actual-data
experiment launch path. Family names are slots; the test/demo factories are
deterministic stubs, not LR/SVM/RF/XGBoost implementations. There is no actual
estimator/search/calibrator/threshold or selected-model integration in these new
files. Existing legacy model ports/guards remain unchanged.

## Callback and scientific boundaries

A factory supplies a fresh complete fold-local pipeline. Its fit sees training
predictors and training labels only; score sees validation predictors plus
observation IDs as control metadata, never validation labels. The caller must not
put IDs/provenance in predictor columns or let the callback read external data.
The runner cannot sandbox a malicious callback, authenticate approval references,
or prove that arbitrary callback preprocessing was fitted correctly.

Exact supplied development assignments remain D9's source of truth; no partitions
or folds are generated. OOF population/IDs/group/fold/target metadata must match.
Representation/ablation contrasts require fixed family/parameters and matched
seed/score-policy reference; candidate comparisons retain matched IDs. No winner,
practical-equivalence tolerance or approved search budget is inferred.

Raw margins are not probabilities. Probability metrics require explicit supplied
unit-interval values and edges, and do not prove calibration. No calibrator is
fitted. The classification threshold applies to the supplied score units.
AP means non-interpolated average precision, not trapezoidal PR area. Actual
H9 metric/score conventions remain pending. Paired bootstrap resamples entire
supplied groups with identical multiplicities for both candidates; one-class
draws are counted as undefined rather than replaced. Actual research must use
the approved 2,000/95% protocol and its accepted estimand/interval rules.

U1 excludes all behavioral predictors. Behavioral ablation is rejected for
technical branches. Missing values remain explicit; no global imputation/scaling
or synthetic negative evidence is introduced.

## Tests and commands actually run

Common Python environment:
`PYTHONDONTWRITEBYTECODE=1`, `DATABASE_URL=sqlite:///:memory:`,
`TEMP/TMP=<task-temp>`; pytest uses `-p no:cacheprovider` and unique basetemps.
Task temporary directory:
`<user-profile>/AppData/Local/Temp/sebrl-master-20261104-xiwva8k4`.
Existing .venv Python 3.12.10 / pytest 8.4.2; scientific packages absent. No install.

| Command | Result |
| --- | --- |
| `.venv/Scripts/python -B -m pytest ml/tests/test_evaluation_metrics.py ml/tests/test_development_runner.py -q --tb=short -p no:cacheprovider --basetemp <task-temp>/wave3-first` | 66 passed, 2 failed |
| Add numeric tests, same focused options under `wave3-second` | 71 passed |
| Four focused files including benchmark, basetemp `focused-final` | 87 passed |
| Strengthened pairing/comparison tests, basetemp `focused-controls` | 92 passed |
| `.venv/Scripts/python -B -m pytest ml/tests/test_evaluation_metrics.py ml/tests/test_development_runner.py ml/tests/test_numeric_boundaries.py ml/tests/test_inference_benchmark.py ml/tests/test_synthetic_demo.py -q --tb=short -p no:cacheprovider --basetemp <task-temp>/focused-demo` | 93 passed in 1.16 s |
| `.venv/Scripts/python -B -m pytest ml/tests/test_uci_preparation.py ml/tests/test_branch_preparation.py ml/tests/test_development_experiments.py ml/tests/test_notebook_contracts.py ml/tests/test_experiment_inputs.py ml/tests/test_experiment_integration.py ml/tests/test_preflight.py -q -p no:cacheprovider --basetemp <task-temp>/neighbors-final` | 382 passed in 6.60 s |
| `.venv/Scripts/python -B -m pytest ml/tests backend/tests -q -p no:cacheprovider --basetemp <task-temp>/full-release-check` | 906 passed in 11.14 s; one installed Starlette/httpx deprecation warning |
| `npm.cmd run test --workspaces --if-present -- --configLoader runner` | 17 extension + 8 dashboard tests passed |
| `node node_modules/typescript/bin/tsc -p apps/gmail-extension/tsconfig.json --noEmit --incremental false` | Passed |
| `node node_modules/typescript/bin/tsc -p apps/web-dashboard/tsconfig.json --noEmit --incremental false` | Passed |
| From extension: `node ../../node_modules/vite/bin/vite.js build --configLoader runner --outDir <task-temp>/build/extension` | Passed popup/background build |
| From extension: same build with `--config vite.content.config.ts` and same outDir | Passed content build |
| From dashboard: `node ../../node_modules/vite/bin/vite.js build --configLoader runner --outDir <task-temp>/build/dashboard` | Passed; outside-root outDir will not be emptied warning |
| Static JSON/`ast.parse` on all six notebooks | 275 code cells valid; 0 executed |
| `.venv/Scripts/python -B -m ml.preflight --root .` | Exit 2, 18 reported issues; scientific/input/environment gates remain blocked |

The first two failures were hand-fixture expectations: reversing a symmetric
three-item ranking leaves AP unchanged, and AP(perfect)-AP(reversed two-item)
equals .5 rather than 1. Tests were corrected to the independent hand arithmetic.
The implementation was not weakened to meet those expectations. All final checks
pass. Intermediate complete runs also passed 884/905 tests as new tests were added.

Timing tests use deterministic injected clocks (10/20/30 ms batches -> p50 20,
p95 29, throughput 100 artifacts/s for batch size 2). These are SYNTHETIC RESULT,
not measured workstation performance. No dependency warning was "fixed" by
installing/replacing environments. Vite output paths were checked unused and
confined to task temporary storage; user dist directories were preserved.

## Reproduce the synthetic demonstration

The saved [synthetic manifest](synthetic_smoke/manifest.json) identifies
code hashes, environment, input fingerprint, seed 7, stub parameters, explicit
threshold/bins, score policy, omitted dimensions and output hashes. Its feature
signal and scores are constructed. It records 40 no-optimization stub fit calls,
zero real research model fits, 30 Email E1/E2/E3 OOF rows, four dimension checks
and 10 synthetic UCI U1 observations. No real dataset is loaded.

From checkout root, use an unused leaf directory with an existing parent:

~~~powershell
.venv\Scripts\python -B -m ml.synthetic_demo --directory <unused-directory> --code-reference <HEAD-plus-dirty-code-reference>
~~~

Actual command used the directory
`docs/research/2026-11-04_master_completion/synthetic_smoke` and code reference
`6bded57d38e9b83ba718d7795b97e2130128c23f+uncommitted-2026-11-04-sprint`.
Do not rerun against that existing directory. A fresh replay produces new timing
and environment metadata, so byte equality of timing files is not promised;
deterministic assignments/scores and semantic checks are the reproducibility target.

`verify_synthetic_bundle(directory)` checks only fixed files and their hashes.
Existing directories refuse writes. Ordinary IO failure rolls back that call's
new files/leaf directory, with manifest last; process termination is not atomic.
No raw conventional text/values are exported. This is traceability, not source
authentication or a signature.

## What still blocks research experiments

Actual accepted source/label/lineage/group/dictionary/access evidence; a legitimate
exposure/evaluation plan; approved candidate budgets, nested tuning/scoring,
practical-equivalence/calibration conventions and efficiency settings; an isolated
scientific environment; genuine model factories; selected calibrated/model-attribution/
risk integration and release validation. No real handoff, classifier fit, OOF
research score, ablation, final threshold or empirical thesis metric was produced.

