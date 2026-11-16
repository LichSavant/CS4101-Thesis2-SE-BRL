# D9 — Development experiment consumer preparation

Date: 2026-11-01 (Asia/Manila). Baseline: `6bded57` plus existing local repairs.
Scope: Dhanwil D9, preparing the repaired Notebook 03/04 outputs for experiments.
This is not dataset approval, a completed model comparison or a new result.
The approved proposal remains the governing specification; see the verified
section/table references in `notebook_03_04_repair.md`.

## Implemented connection

Notebook 03 versioned preprocessing -> Notebook 04 validated development rows ->
exclusive development-input exports and hashed handoff ->
`05_development_preparation.ipynb` -> matched five-fold input plans.

Historical `05_experiments.ipynb` is unchanged. Its old schemas, technical roles,
reserved-partition procedures and generic result writers are not redirected.
The companion notebook contains only preparation, not research-data fitting.

### Notebook 04 handoff

Source-only additions to cells `2361f7e7` and `a8cef068` add:

- `data/processed/features/development/email_development.csv`
- `data/processed/features/development/phiusiil_development.csv`
- `data/processed/features/development/uci_development.csv`
- `data/processed/features/development/development_input_manifest.json`

These paths are under `experiments/runs/<run_id>/`. Conventional-input views
contain the already filtered development records, with original metadata kept
for validation. They are not model predictor matrices. The consumer selects
only an explicit conventional dictionary; it never discovers features by dtype.
Compact canonical behavior tables remain in the sibling `sebrl/` directory.

Both complete destination sets are checked before file writing. CSV/JSON writes
use exclusive creation. The manifest records the existing boundary version,
run identity, allowlisted filenames and SHA-256 values for paired inputs.
Partial exports after interruption are not rolled back; exclusive files must be
inspected rather than overwritten on rerun. This implementation task did not
execute exports, create a research run, or regenerate any existing artifact.
Stored outputs, execution counts and metadata are retained as historical/stale.

### Consumer and fold contracts

`ml/development_experiments.py` uses the standard library and existing validators.

- Fixed filenames under a validated run ID; no historical-path fallback.
- Resolved paths cannot escape the checkout/run through traversal or symlinks.
- File contents are parsed from the same bytes used for checksum validation.
- Every supplied row must be development; malformed/duplicate headers, invalid
  metadata and mismatched hashes are rejected.
- Exact one-to-one IDs, targets, group, partition and fold agreement are required
  between conventional inputs and canonical support/availability tables.
- All five supplied development folds require both classes. Group crossing is
  rejected. This validates supplied group assignments, not campaign independence.
- Support/availability are binary; support without availability is invalid.
- PhiUSIIL/UCI are U1-only and must have unavailable behavioral values.
- Email E1/E2/E3 use identical observation identities, labels and fold allocation.
- Predictor tuples contain only declared conventional features and/or canonical
  behavioral columns. Labels, identifiers and provenance remain control metadata.
- Numeric missing values stay explicit; no imputation/scaling/vocabulary fitting
  occurs. CSV's small default field limit does not become a text-length exclusion.
- Fold inputs keep training labels separate from predictors. Fresh fold-local
  transforms, tuning and calibration must be implemented by later estimator code.

The typed representation is an ordinary software interface, not an adversarial
sandbox. Callers must not bypass the validated builder. Protocol references and
hashes establish traceability, not independent source authenticity or approval.
A handoff labelled development does not prove historical reserved records were
never accessed upstream; loader/custody and Stage 3 freeze evidence remain needed.

## Companion notebook use

After authorized Notebook 03/04 runs and the appropriate scientific freezes:

1. Open `experiments/notebooks/05_development_preparation.ipynb`.
2. Supply the actual frozen protocol and feature-dictionary references.
3. Supply explicit `FeatureColumn` entries; no scientific feature choices are
   guessed or defaulted by this task.
4. Load the hashed handoff and inspect aggregate preparation counts.
5. Construct matched five-fold inputs for the branch's allowed configurations.

This preparation notebook creates no files, scores or predictions. It stops
before data consumption when configuration references/dictionary are missing.
No calibration/test loader or automatic model execution exists in this module.

## Remaining work and assignment checkpoints

D2-D8: the previous paper-aligned repairs and synthetic checks are preserved;
actual-data screening/grouping and verified behavioral evidence remain required.
D9: the compatible consumer/companion notebook is implemented and synthetically
tested. Corpus acceptance and a full runnable experiment are not claimed.
D10-D14: estimator factories for LR/Linear SVM/RF/XGBoost, approved search/nesting,
OOF scores, uncertainty, efficiency, metrics and immutable result bundles remain
later work. Do not equate declared family names with implemented classifiers.
D11's transformer stage is not introduced: the governing methodology is
currently deterministic SE-BRL.

Coordinate source/evidence validation with Vera while Dhanwil completes the
experimental implementation. Existing H1-H12 statuses are unchanged. Missing
payloads/environment, Stage 3 screening/grouping, frozen behavioral language/
locators/partial availability, feature dictionaries and the exposure-aware
selection/evaluation settings still gate research runs. Final operational
requirements are later checkpoints, not prerequisites to every coding repair.

## Verification scope

Tests use synthetic Email and technical records only. They check matched folds,
reserved-data rejection, label exclusion, metadata/state mismatches, technical
scope, fixed paths/checksums, read-only loading, long text and absence of model
or scientific-package execution. Notebook code cells are syntax-parsed only.
No analytical notebook, classifier or calibrator is executed during this task.
