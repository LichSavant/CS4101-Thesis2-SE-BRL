# Verified engineering completion record

November 9, 2026. All new fits use generated synthetic fixtures exclusively.
No notebook, dataset, original codebook, prior draft, prior source file or
historical result was changed. No Git mutation or application environment
installation occurred. The overall prototype remains scientifically incomplete.

## Exact added files

| Path | Reason |
| --- | --- |
| ml/feature_freeze.py | Validate Pending exact typed/order/version/codebook candidate and matched D9 value boundary |
| ml/feature_freeze_candidate.v0.1.0.json | Machine-readable proposed core E1, canonical E2 and ordered E3; no scientific approval |
| ml/experiment_engine.py | Genuine supplied-fold nested candidate search; complete training-only sigmoid and threshold cross-fits; exact OOF/audit records |
| ml/model_selection.py | Explicit expected-family/metadata/metric/SRS validity checks and Table 4.9 synthetic hierarchy; no invented settings or research winner |
| ml/model_persistence.py | Digest-bound pinned-version skops and native-XGB+preprocessor save/reload; no pickle/auto-trust |
| ml/experiment_artifacts.py | Complete exclusive synthetic result/model/calibration/threshold bundles; manifest-last completion and owned-file rollback |
| ml/requirements-persistence-synthetic.txt | Three explicitly approved pinned temporary dependencies; no application requirement changed |
| ml/tests/test_feature_freeze.py | Schema drift/forbidden fields/false approval/count alignment |
| ml/tests/test_experiment_engine.py | Genuine four-family nested fits, held-out label invariance, matched views/U1, fresh pipelines, failures and exact fit counts |
| ml/tests/test_model_selection.py | Missing/forged/mismatched evidence, hard gates, uncertainty stop, calibration/efficiency ordering and final LR-only tie preference |
| ml/tests/test_model_persistence.py | Four-family and learned TF-IDF/imputer/scaler reload identity, hashes/versions/files/resource/type/failure controls |
| ml/tests/test_experiment_artifacts.py | Complete five-model+calibrator bundle reload, coverage, tampering, exclusive output and partial-write failure |
| docs/research/2026-11-09_deterministic_finalization/{README,preflight_resolution,approval_packet,email_protocol,feature_freeze,experiment_config,engineering_completion,research_execution,manuscript_evidence,final_handoff}.md | Ten requested consolidated reports and one Pending approval form |
| Same directory / verification.json | New-file hashes, retained synthetic artifact receipt, tests and baseline-preservation evidence; its own hash omitted to avoid recursion |

No existing module was replaced. Previous Notebooks 01/03/04 repairs, D9 consumer,
historical Notebook 05 and all other working-tree changes remain intact.
The legacy simple CV runner remains a separate no-search callback path; the new
engine and complete artifact wrapper are explicit opt-in synthetic interfaces.

## Persistence policy review

The extra dependencies were missing, so the user explicitly approved isolated
installation and synthetic verification. App `.venv` remains unchanged. Packages:
skops 0.13.0, prettytable 3.16.0 and wcwidth 0.2.13, installed with `--no-deps
--only-binary :all: --no-compile --no-cache-dir` to task-owned host temporary
storage. Existing approved scientific packages and packaging 26.3 were reused.

Exact approved installation command (fresh destination existed only after this
task created it):

```powershell
.venv\Scripts\python -B -m pip install --target '<user-profile>\AppData\Local\Temp\sebrl-finalization-approved-20261109\persistence' --only-binary :all: --no-deps --no-compile --no-cache-dir --retries 1 --disable-pip-version-check --report '<user-profile>\AppData\Local\Temp\sebrl-finalization-approved-20261109\install_receipt.json' --requirement ml/requirements-persistence-synthetic.txt
```

Installation receipt SHA-256:
`7008091a3660994e79295ad8244dc6ebd01a56502256b944d85d10f6c4ff6e91`.
Wheel SHA-256: skops `55e2cccb18c86f5916e4cfe5acf55ed7b0eecddf08a151906414c092fa5926dc`;
prettytable `b5eccfabb82222f5aa46b798ff02a8452cf530a352c31bddfa29be41242863aa`;
wcwidth `3da69048e4540d84af32131829ff948f1e022c1c6bdb8d6102117aac784f6859`.

All unknown types fail except fixed reviewed `numpy.dtype`, enabled only for
numpy 2.2.6/scipy 1.15.3/sklearn 1.6.1/skops 0.13.0. The installed pinned
`skops/io/_numpy.py::DTypeNode` was inspected: it returns its child's array.dtype;
its numeric array loader uses `np.load(..., allow_pickle=False)`. The scanner's
list is never adopted as a trust list and callers cannot supply one. Recheck
this policy before any package upgrade. Hash/trusted-custody/resource constraints
still apply; this is not a general untrusted-file execution sandbox.

The reviewed design follows [sklearn persistence guidance](https://scikit-learn.org/1.6/model_persistence.html),
[skops guidance](https://skops.readthedocs.io/en/stable/persistence.html) and
[XGBoost model I/O](https://xgboost.readthedocs.io/en/release_2.1.0/tutorials/saving_model.html).
Exact implementation behavior was checked against installed pinned packages,
not assumed from newer documentation. Skops dependency metadata was verified at
[the pinned release](https://pypi.org/pypi/skops/0.13.0/json).

## Commands and actual results

Environment used for host scientific tests (sandbox could not read the earlier
host scientific install correctly; tests ran in the authorized host context):

```powershell
$env:PYTHONPATH='<user-profile>\AppData\Local\Temp\sebrl-finalization-approved-20261109\persistence;<user-profile>\AppData\Local\Temp\sebrl-genuine-approved-20261105\science'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP='<user-profile>\AppData\Local\Temp\sebrl-finalization-approved-20261109'
$env:TMP=$env:TEMP
$env:DATABASE_URL='sqlite:///:memory:'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
.venv\Scripts\python -B -m pytest ml/tests/test_experiment_engine.py ml/tests/test_feature_freeze.py ml/tests/test_model_persistence.py ml/tests/test_model_selection.py ml/tests/test_experiment_artifacts.py -q -p no:cacheprovider --basetemp "$env:TEMP\pytest-final-focused-1"
.venv\Scripts\python -B -m pytest ml/tests/test_model_persistence.py ml/tests/test_model_selection.py -q -p no:cacheprovider --basetemp "$env:TEMP\pytest-final-boundaries-2"
.venv\Scripts\python -B -m pytest ml/tests backend/tests -q -p no:cacheprovider --basetemp "$env:TEMP\pytest-final-full-2"
.venv\Scripts\python -B -m pytest ml/tests backend/tests -q -p no:cacheprovider --basetemp "$env:TEMP\pytest-final-full-3"
```

| Check | Fresh actual result |
| --- | --- |
| Initial numeric four-family persistence tests | 8 passed, 4.32 s |
| Initial engine/schema tests | 19 passed, 1 failed, 164.93 s: incorrect test expectation of 705 versus actual 625 base fits; all label-isolation assertions passed; corrected count |
| Focused engine/schema/persistence/selection/artifacts | 35 passed, 185.15 s; later boundary additions verified below/full suite |
| Added learned-text-state test + selection | 6 passed, 1 failed: unknown numpy.dtype correctly refused; fixed reviewed pinned policy after source inspection |
| Final persistence + selection | 15 passed, 6.81 s |
| Optional-memory selection boundary | Initial 6 passed/1 failed because a known contract error was wrapped as generic ValueError; preserved the specific contract error. Final focused selection: 7 passed, 0.12 s. Explicit missing-memory policy never bypasses a memory limit. |
| First full ML/backend regression | 1,016 passed, 1 warning, 251.09 s |
| Full ML/backend regression after learned-state persistence additions | 1,017 passed, 1 warning, 249.82 s |
| **Final full ML/backend regression including explicit optional-memory policy** | **1,018 passed, 1 warning, 233.67 s** |
| Notebook syntax, no execution | 275 code cells across six notebooks passed Python AST parsing; 0 failures |
| New Python source/test syntax/whitespace | 10 files passed AST parsing; 0 trailing-whitespace findings |
| Research gate CLI | Native exit 2; ten FAIL conditions; fitting disabled |
| Frontend/typecheck/build | Not rerun: no frontend/shared/API production integration changes. Prior 25 frontend result is historical, not freshly reproduced. |

The one full-suite warning is existing `StarletteDeprecationWarning` from
FastAPI's TestClient using httpx; no dependency replacement was performed.
Read-only Git status also reports the pre-existing inaccessible `.pytest_cache`
directory. It was left untouched; pytest cacheprovider and bytecode writes were
disabled, with explicit task-owned temporary bases and in-memory database.

Static command executed, using notebook source only and never stored outputs:

```powershell
@'
import ast,json,pathlib
count=0; failures=[]
for p in sorted(pathlib.Path('experiments/notebooks').glob('*.ipynb')):
 for i,c in enumerate(json.loads(p.read_bytes())['cells']):
  if c['cell_type']!='code': continue
  try: ast.parse(''.join(c.get('source',[])),filename=f'{p.name}:cell-{i+1}')
  except SyntaxError: failures.append((p.name,i+1))
  count+=1
print(count,failures)
raise SystemExit(bool(failures))
'@ | .venv\Scripts\python -B -
```

Per-notebook code cells: 01=40, 02=30, 03=100, 04=75,
05_development_preparation=4, historical 05_experiments=26. All six notebooks
remain on disk unchanged; no analytic cells were executed.

## Retained synthetic integration evidence

A separate bounded generated-fixture LR E3 run used one explicit candidate,
seed 17, reject/no-scale numeric preprocessing, identity-score sigmoid with
explicit regularized LR settings, epsilon 1e-6, fixed .5 operating threshold and
bins (0,.5,1). These are **fixture parameters, not research recommendations or
approvals**. `run_synthetic_nested_cv` performed 105 base fits + five sigmoid
fits, then `write_nested_bundle`/`load_nested_bundle` verified all five models
and exact calibrated prediction/threshold identity. No selected final model or
research outcome was generated.

Final retained task storage:
`<user-profile>\AppData\Local\Temp\sebrl-finalization-approved-20261109\verified_nested_lr_v2`.
Completion manifest SHA-256:
`042a2afd07497e13604c9fb94958262e6320f2a5f4db4f45304088ac64d1dabd`.
The earlier `verified_nested_lr` bundle with manifest
`67ea26ffbaa350eabc0d62be19d43013208262c7d9f817542a92d89a5278b047`
was preserved; v2 captures the final selector-code hash and adds explicit hashes
for the fixture-parameter source and official codebook. Each bounded bundle ran
105 base fits + five sigmoid fits; neither used research data.
Input fingerprint `a2cda5b975e8cba970054fecf95208c5bf42f50aa6b3da906355922f479f8dda`;
request fingerprint `13dd83f5c4aa0b7c2a43db2c912e23f85fb11436d8fe02b92c15cdc4e1efc8a7`.
All payload hashes and exact working-code hashes are in that complete manifest
and its result manifest. The model files stay in task storage, outside research
datasets/historical results. Temporary storage may later be removed by the OS.

The first receipt's timing callback included the validation/preprocessing
wrapper and records aggregate five-model size. It is **not** an estimator-only
or selected-model efficiency result. A separate correctly bounded smoke times
only `estimator.predict_proba` on pretransformed synthetic numeric input, excluding
preprocessing/calibration/API, after warmup=2, repetitions=5, batch=1 under
threadpool_limits(1). `verified_estimator_benchmark.json` SHA-256
`1175309839ce23474066ea02601cbe3403e17a1be60c4cd25b91e8dc80f7c720`.
Measured illustrative p50/p95: 0.1071/0.11688 ms, about 9,405.57 records/s;
one outer-model pipeline+manifest=62,425 bytes. Memory unavailable; no selection.
These tiny generated-fixture timings are verification only, **not thesis
performance, a frozen research benchmark or SRS compliance evidence**.

## Preservation and final repository state

Before changes a 311-file baseline covered all tracked/untracked project files
and existing experiments/database files plus Git index/configuration. For 227
safe code/document/control files, SHA-256 matches after the sprint. For 84
protected datasets/results/notebooks/database files, exact size and string-valued
nanosecond modification times match. No raw messages or historical prediction
rows were opened. This is strong no-observed-change evidence, **not a new
cryptographic byte-identity proof** for files deliberately checked by stat only.

Historical metrics/predictions/plots/coefficients/partitions/manifests, all prior
drafts, approved PDF, original codebook, notebooks and persistent
`database/phishing_defense.db` are preserved against that baseline. Database size
40,960 and exact mtime `1788353869239590100` are unchanged. Git index SHA-256
`32d78359bfa521d1a5ec9426267fc51d009eeb5acb5bd37addf589ee57619734` and
configuration SHA-256 `86514ae68bc6d27d646f40175b502c3dd85c65c816089961fd1fa71f1608ca14`
are unchanged. Unsaved VS Code buffers were not accessed.

Final: main/`6bded57d38e9b83ba718d7795b97e2130128c23f`, 24 unstaged tracked
paths, 110 untracked paths, 0 staged. This sprint adds 23 files; modifies/deletes
zero pre-existing files. The 19 materialized LFS payload modifications and other
pre-existing notebook/ML tracked changes remain; no LFS repair or Git refresh was
attempted. No fetch/pull/switch/stage/commit/push/reset/clean/config mutation.
`origin/main` is the different-repository upstream (`Thesis_Protoype_Test`);
`se-brl` remains the intended thesis remote. GitHub was not synchronized or
queried, so independent remote changes are unknown.

Technical limitation: the accepted-data adapter/verifier/guarded research
launcher and final selected risk/explanation/system integration remain dependent
on accepted scientific/custody/final-evaluation contracts. Independent synthetic
experiment engineering is now verified; the whole prototype/research is not
declared complete. See final_handoff.md for exact next acceptance task.
