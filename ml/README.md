# Social Engineering Behavior Representation Layer

## Portable engineering verification

Use [`tools/verification/README.md`](../tools/verification/README.md) for the
standalone Python 3.12 environment and reviewed no-fit test selection. It creates
an external verification workspace with explicit dependency pins and copied
software sources, without using historical temporary installations or modifying
the application environment. Existing synthetic model readback requires an
explicit named fixture directory and independently trusted receipt digest.
Historical reproduction commands below are retained as prior evidence.

## Current continuation — 2026-11-12

Engineering continuation evidence is recorded in
[`engineering_completion_20261112/REPORT.md`](../engineering_completion_20261112/REPORT.md).
The shared selector now explicitly rejects native PhiUSIIL `FILENAME`, including
case variants, at dictionary construction and final matrix selection. Predictor
lookup otherwise remains case-sensitive. C/D additionally recomputes prospective
IDs from source snapshot/file/original position and rejects conflicting locators
and native-label assertions before allocation or export. New no-fit preparation
outputs include an exclusive `completion_integrity.json` sidecar with actual code,
configuration, environment, Git dirty-state and output digests. Unknown Git state
is recorded as unknown; hashes do not authenticate custody or scientific approval.

`ml.source_controls.prepare_source_controls` validates matched development-only
baseline/normalized/source-only controls without fitting. Normalization is supplied
under an explicit protocol reference; no default policy is selected. Future
`execute_source_controls` fits models and writes new diagnostic bundles: **do not
call it under the current authorization**. It requires separate exact contexts
verified with `verify_accepted_run(..., purpose="diagnostic")`, whose receipt
boundary is `E-development-diagnostic-only`. Principal experiment receipts still
require complete E1/E2/E3 and cannot be reused as E1-only diagnostic authority.
Source-stratified reporting remains descriptive of performance, never proof of
causal behavioral learning. Diagnostic fitting/persistence is not verified by a
synthetic fit in this continuation because all fitting remains prohibited.

Notebook 04 is preserved. Source-only tests compile its two pure aggregation
functions without executing cells or reading stored outputs. Fully assessed and
wholly unavailable aggregation cases can be checked mechanically; lexical trust
rules and incomplete aggregation remain pending P6/P7, not declared equivalent.

Artifact request capacity is reserved before thread scheduling. Timeouts and
client cancellation retain a slot until computation exits; excess requests receive
503. Threads are not forcefully cancelled, and timed-out workers cannot persist
metadata. Two non-returning workers make this service busy until they exit or the
process restarts; the timeout is a response deadline, not a hard compute kill.

For focused no-fit checks, use the existing environment below and run the new
`test_engineering_leakage.py`, `test_behavioral_path_conformance.py`,
`test_preparation_integrity.py`, `test_source_controls.py`, `test_execution_identity.py`
and `backend/tests/test_artifact_worker_bounds.py` with
`-p ml.tests.no_fit_guard -p no:cacheprovider` and a fresh scratch `--basetemp`.
Do not run fitting suites indiscriminately: the Web genuine-adapter test must be
excluded by its exact pytest node ID (its `genuine` decorator is a conditional
skip, not a pytest marker). Existing synthetic bundle readback performs inference
only; it never creates replacement fitted state.

Use [the single completion tracker](../docs/research/completion_tracker.md) and
[the existing decision packet](../docs/research/2026-11-09_deterministic_finalization/approval_packet.md).
The researcher's latest direction permits non-destructive verification, **not
additional model fitting, hyperparameter search, final evaluation or sealed-test
access**. P3 is accepted in principle; P4/P6/P7 directions are conditional. The
candidate JSON remains Pending. Do not execute older fitting smoke commands
below under this current scope.

The runtime now accepts explicit Email, Webpage Content and source-specific
UCI/PhiUSIIL engineered inputs through `/api/v1/artifact-analysis`. Bare URLs
are never converted into fabricated native U1 values. The versioned DecisionObject
separates deterministic evidence, calibrated classifier output, model attribution
and SRS precedence-based advisory response. Missing, incomplete, stale or
incompatible analysis yields Review Required. Only synthetic compatible bundles
are currently admitted for demonstration; none is a validated research model.
No trained behavioral predictor, transformer or human-annotation stage is required.

### Existing-state verification without fitting

Existing checksum-verified synthetic state is retained locally, excluded from Git:
`experiments/runs/system-validation-synthetic-20261112-01/`.
Its `fixture_receipt.json` SHA-256 is
`abf6556e08c4fe80d6c090afd72a8e5ef1ea9f6591e37aea8e674e9a22873dd4`.
It contains pre-existing fixture models/calibrators, not research-data fits.
Use the independently recorded digest; do not trust a digest supplied by an
untrusted download. The runtime verifies all component code hashes and state
versions, and refuses stale packages. This directory is local custody, not OS
access-control configuration or permission to publish models.
The same directory's `software_validation_manifest.json` records the executed
checks, package/code/state hashes and limits; it is not research-result evidence.

PowerShell setup for this checkout's existing isolated packages (no installation):

```powershell
$taskStorage = Join-Path $env:LOCALAPPDATA 'Temp\sebrl-completion-20261111'
$env:PYTHONPATH = "$taskStorage\grouping;$env:LOCALAPPDATA\Temp\sebrl-finalization-approved-20261109\persistence;$env:LOCALAPPDATA\Temp\sebrl-genuine-approved-20261105\science"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:TEMP = $taskStorage
$env:TMP = $taskStorage
$env:DATABASE_URL = 'sqlite:///:memory:'
$env:SEBRL_READBACK_ROOT = Join-Path (Get-Location) 'experiments\runs\system-validation-synthetic-20261112-01'
$env:SEBRL_READBACK_RECEIPT_SHA256 = 'abf6556e08c4fe80d6c090afd72a8e5ef1ea9f6591e37aea8e674e9a22873dd4'
.venv\Scripts\python -B -m pytest -p ml.tests.no_fit_guard ml/tests/test_existing_bundle_integration.py -q -p no:cacheprovider --basetemp "$taskStorage\pytest-readback-new-unused-name"
npm.cmd test
npm.cmd run typecheck
npm.cmd run build
```

The no-fit plugin is installed before collection and globally rejects supported
classifier, calibrator and learned-transform fits. Any attempted fit fails the
session, even if a test catches the exception. Use a fresh task-owned basetemp.
Do not run the complete fitting suite under the current no-fitting direction.
`requirements-grouping.txt` pins the separately isolated MinHash implementation;
the application environment was not changed.

### Local application with existing synthetic state

After the setup above, configure only the server's trusted bundle paths/digests:

```powershell
$bundleStorage = $env:SEBRL_READBACK_ROOT
$env:ARTIFACT_EMAIL_BUNDLE = "$bundleStorage\email"
$env:ARTIFACT_EMAIL_BUNDLE_SHA256 = 'df64bae81499cd1134275acede39a7583d680702762a819ca851adae9dc342f6'
$env:ARTIFACT_WEB_BUNDLE = "$bundleStorage\web"
$env:ARTIFACT_WEB_BUNDLE_SHA256 = 'f537691e1bc3721a1366c7de41d580a498a9171449bb0192cfa62cad5b3f0ab3'
$env:ARTIFACT_UCI_BUNDLE = "$bundleStorage\uci"
$env:ARTIFACT_UCI_BUNDLE_SHA256 = 'ed10b5ed4aca7e31f2e66a66cc1bb3bf7c1088ae01a3d2c837b657138008b45e'
$env:ARTIFACT_PHIUSIIL_BUNDLE = "$bundleStorage\phiusiil"
$env:ARTIFACT_PHIUSIIL_BUNDLE_SHA256 = 'c77045c553af973dbb149aa003134cf1369dd6fbd7191035de22d1a4d2cf76de'
$env:ALLOWED_ORIGINS = 'http://127.0.0.1:5187'
$env:DATABASE_URL = 'sqlite:///:memory:'
.venv\Scripts\python -B -c "import ml.tests.no_fit_guard; import uvicorn; uvicorn.run('backend.app.main:app', host='127.0.0.1', port=8017, access_log=False)"
```

In another terminal, use the same setup for Node and run:

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8017'
npm.cmd run dev --workspace @phishing-defense/web-dashboard -- --host 127.0.0.1 --port 5187 --strictPort
```

Submit generated, non-personal artifacts only for software validation. Leave
body and link extraction off unless explicitly authorized for that artifact.
Unknown language produces Review Required for content rules. UCI/PhiUSIIL do
not apply English behavioral rules; the supplied vector must match its exact
configured dictionary. The included U1 fixture dictionaries contain two fields
and **are not complete research benchmark dictionaries**. The extension's manual
artifact action never collects a body, increments visit count or automatically
reports a message. Legacy mock/tracking functionality remains separate.

### Source, preparation and research boundaries

- A/B: `python -B -m ml.source_audit --help`,
  `python -B -m ml.csv_source_audit --help`,
  `python -B -m ml.web_source_audit --help`; exact named snapshots, expected
  hashes and explicit budgets, aggregate outputs only. Existing actual source
  audits under `experiments/runs/*-source-audit-20261111-01/` remain immutable;
  do not rerun into them or interpret native codes without source evidence.
- C/D: `python -B -m ml.preparation_execution --root . --input-run-id
  <accepted-input-run> --stage C-allocation --authorization-sha256 <independent-digest>`;
  use `--stage D-features` for the separate accepted no-fit feature boundary.
  Receipts and fixed file requirements are specified in that module. Missing
  custody, mappings, policy acceptance or input files blocks the command. No
  training settings are prerequisites for these earlier boundaries. None of
  these commands has been run on real research populations in this task.
- E: `python -B -m ml.research_execution --root . --input-run-id
  <accepted-development-run> --authorization-sha256 <independent-digest>` is
  verification only. Its separate `--execute` option performs genuine fitting
  and **is not authorized now**. The public CLI enforces the accepted worker
  wall-time cap, and the shared engine enforces fit/row budgets. Completed runs
  are exclusive; incomplete/interrupted state is not silently resumed or mixed
  with a completed result. A matching readback context is required to reload
  research artifacts; it cannot start another fit. Synthetic results never open E.
- F: final calibration/thresholds, selected research analytical-bundle promotion,
  exposure-aware final evaluation and release remain unperformed and unapproved.

No actual eligible population, partition/fold allocation, feature extraction,
development training, candidate selection or final evaluation was completed on
research data. Source-only/normalized-format comparisons require the affected
frozen diagnostic settings and future authorized execution; the current source
contingency and source-stratified helpers do not substitute for those experiments.
The persisted application database, historical notebooks/results and approved
documents are preserved. Visual browser testing was unavailable because the
installed automation runtime could not start; component and localhost API checks
are recorded separately in the tracker.

## Earlier synthetic experiment path (historical instructions)

The approved proposal uses deterministic behavioral support/availability values;
it does not require a learned behavioral predictor or human behavioral annotation.
The D9 path in `development_experiments.py` is separate from the legacy runtime
representation described below. `classifier_adapters.py` supplies genuine
Logistic Regression, Linear SVM, Random Forest and XGBoost pipelines to the
synthetic development runner. Each learned transform is fitted inside its
supplied training fold. Raw classifier probabilities are uncalibrated, and SVM
margins remain margins. No validated research model is integrated into the app.

`requirements-classifiers-synthetic.txt` pins an isolated CPU verification
environment; installation requires approval. With those packages available,
`python -B -m ml.genuine_classifier_smoke --directory <unused-directory>
--code-reference <reviewed-code-reference>` fits generated fixtures only. It
cannot load research corpora. Existing directories are rejected, each exported
bundle uses the existing three synthetic artifact names, and `summary.json` is
written only after every family bundle validates. No summary means the
multi-family export is incomplete. These are software checks, not thesis metrics
or an approved research protocol. The consolidated November 5 report under
`docs/research/2026-11-05_deterministic_completion/` records the current boundaries.

The following pre-training/runtime notes describe the existing legacy interface.
Its `None` slots do not add a supervised behavioral-learning requirement to the
approved deterministic study. Research eligibility, dictionaries, rule freeze,
search/calibration/selection settings and exposure-aware evaluation still need
their own acceptance evidence before real experiments.

This directory contains the versioned, machine-readable SE-BRL codebook, its dependency-free Python loader and structural validator, and an internal pre-training analytical pipeline. The codebook implements the hierarchy in Section 3.3.1, the evidence states and future encoding metadata in Section 3.3.2, the modality-support matrix in Table 4.4, and the processing boundaries in Sections 4.5.2-4.5.3 of the thesis manuscript.

`se_brl/codebook.v0.1.0.json` is the sole canonical runtime source for dimension and indicator IDs and names, parent mappings, dimension-level evidence boundaries and exclusions, evidence-state definitions, modality definitions and support codes, required-evidence rules, deterministic dimension order, vector-slot metadata, and the schema and codebook versions. Python code loads and validates that document rather than maintaining a second taxonomy.

Codebook version `0.1.0` is pre-1.0 and is not the final validated or fully frozen codebook. Candidate rule definitions, synthetic examples, overlap handling, and evidence locators now exist as versioned implementation infrastructure; their scientific validation and protocol freeze remain deferred.

SE-BRL is an instrument and pre-training pipeline, not a trained model. No behavior-identification model, calibrator, confidence, probability, performance result, learned vector value, final risk mechanism, or phishing classification is produced here. Existing extension results remain explicitly rule-based and are not generated by this package.

See [pre-training architecture and research boundaries](../docs/se-brl-pretraining.md) for preprocessing, conventional features, candidate rules, evidence records, BRL placeholders, E1/E2/E3 boundaries, model interfaces, and usage. Dataset provenance and availability audits, annotation and reviewer validation, learned E2/E3 values, model training, calibration, controlled evaluation, and sealed-test work remain deferred.

The pre-training infrastructure now also includes independent-evidence trust detector interfaces, stronger context guards, typed dataset/provenance records with distinct phishing and behavioral labels, supplied-group split validation, feature configuration fingerprints, a sparse-compatible storage boundary, and a programmatic readiness report. No datasets are acquired or models trained by these components.

## Modality assessment foundation

`se_brl/assessment.py` resolves caller-supplied Boolean observations into the canonical `supported`, `absent`, and `unavailable` evidence states. It reads modality mappings, support-code semantics, dimension ordering, evidence-state IDs, and versions from the canonical JSON. `A` requires content, `A*` requires both content and the conditional identity/brand or visual/structural evidence opportunity, and `U` always remains unavailable regardless of caller flags.

The resolver also returns the immutable four-value availability mask `[a1, a2, a3, a4]` in canonical dimension order. `supported` and `absent` map to availability `1`; `unavailable` maps to `0`. The mask records whether behavioral evidence could be assessed. It does not encode behavioral presence, confidence, probability, phishing likelihood, or risk.

Callers provide only the modality ID, two strict availability Booleans, and exactly one strict Boolean observation for each canonical dimension. The assessment module itself does not inspect text, HTML, URLs, raw evidence, or confidence values. The new rule engine supplies its observations through this unchanged interface. The representation exposes `[None, None, None, None, a1, a2, a3, a4]`; learned `z1`-`z4` values remain unavailable.

## Fail-closed result envelope

`se_brl/result-envelope.v0.1.0.json` is the separate canonical lifecycle contract for the immutable analytical result envelope. Contract version `0.1.0` records compatible SE-BRL versions, the ordered analytical components, lifecycle statuses, and stable non-sensitive reason codes without duplicating the behavioral taxonomy.

The envelope is infrastructure, not a model or prediction. The current safe factory returns `not_evaluated`: modality assessment is `completed` only when a compatible `AssessmentResult` exists, while behavior identification, phishing classification, calibration, and risk decision remain `not_evaluated` with explicit deferred-component reasons. The `completed` state is reserved for future use and is rejected unless every required component is completed, a compatible assessment exists, and no failure or missing-component reason is present.

`review_required` and `failed` results fail closed. Review conditions use approved codes for unsupported modalities, missing evidence, invalid schemas, incompatible versions, or parser failure. Failed processing uses only `component_failure`, requires a failed component, and never exposes exception text. Neither lifecycle state contains a definitive classification, probability, confidence, risk tier, or intervention.

Serialization returns a fresh primitive snake_case dictionary while preserving canonical component and dimension order. Raw artifacts, sensitive data, evidence locators, model attribution, and user susceptibility are excluded. The existing backend adapter revalidates this envelope for the API. The internal pipeline retains evidence separately and never adds it to that API contract. Dataset processing, validated behavioral identification, model training, calibration, risk rules, analytical persistence, and final UI integration remain deferred; the SE-BRL model is not complete.
