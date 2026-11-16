# Notebook 04 branch isolation - November 1, 2026

This continuation changes preparation mechanics only. It does not change U1,
the twelve indicators, source eligibility, partitions, scientific decisions or
historical results. D6 actual-data acceptance and D10/D11 remain incomplete.

## Initial state and verified dependency

Checkout: `<user-profile>/Desktop/Projects/Thesis_Prototype_Git`.
Branch/HEAD: `main`, `6bded57d38e9b83ba718d7795b97e2130128c23f`.
Upstream: `origin/main`. Remote configuration remains the old prototype URL for
`origin` and the thesis URL for `se-brl`; neither was changed. Initial status:
22 unstaged tracked paths, 18 untracked files, no staged changes. Nineteen of
those tracked paths are previously materialized LFS datasets. The inaccessible
`.pytest_cache` warning is unchanged. No synchronization was performed.

Inspection covered Notebook 04, `ml/notebook_contracts.py`, the integration and
input contracts, the repaired D9 consumer/tests, handoff source cells and the
previous controlled D9 continuation report. Existing rule definitions and
aggregation functions were read, not executed against research records.

The dependency was structural, not a U1 scientific requirement:

- Cells `4385ae3b`/`ef42ccf9` named and read Email, PhiUSIIL and UCI unconditionally.
- `d55b15cb` immediately constructed all three feature frames, including Email
  subject/body evidence.
- The synthetic lexical example cell `bc7bf1a9` called Email lexical routines
  without branch selection.
- `a1617aaa` unconditionally reached the Email behavioral-specification guard.
- Diagnostics, aggregation, evidence tables and compact outputs referred to
  branch-specific variables even when a caller only needed one U1 branch.
- `2361f7e7`/`a8cef068` preflighted and exported all three handoffs and created
  output directories before complete validation.

This contradicted the independence of the technical branches in approved
Section 4.3.5/Table 4.7. The repair skips irrelevant Email work; it does not waive
the selected technical branch's own audit or experiment prerequisites.

## Exact changed files

| File | Reason |
| --- | --- |
| `experiments/notebooks/04_feature_extraction.ipynb` | Explicit selection, selected loading/dispatch, guarded diagnostics, selected aggregation/export; source arrays only |
| `ml/branch_preparation.py` | Small shared branch selector, loader, dispatcher and protected exporter used by the notebook |
| `ml/tests/test_branch_preparation.py` | 34 synthetic branch-isolation and failure-boundary cases |
| `ml/tests/test_development_experiments.py` | Update the existing notebook export-wiring test to follow the delegated exporter; executable exclusivity tests now cover that exporter |
| This report | Record the verified behavior, commands, limits and status |

The D9 implementation itself is unchanged. Its 97 tests remain in the focused
run. Notebook 03, historical Notebook 05, previous reports and decision drafts
were not edited.

## Explicit selection and preserved workflow

Notebook 04 now defines:

```python
SELECTED_BRANCHES = select_branches(ALL_BRANCHES)  # combined default
RUN_ID = PREPARATION_RUN_ID
```

Examples for an authorized future run:

```python
SELECTED_BRANCHES = select_branches(("PhiUSIIL",))
SELECTED_BRANCHES = select_branches(("UCI",))
SELECTED_BRANCHES = select_branches(("PhiUSIIL", "UCI"))
```

Selection must be a nonempty tuple of unique canonical names. Unsupported names,
duplicates and malformed selections fail; file existence never selects a branch.
The combined default remains `("Email", "PhiUSIIL", "UCI")`. A different
preparation should use an unused run ID, with the same ID supplied to D9. An
existing manifest cannot be silently amended or overwritten to add branches.

`load_selected_inputs` preflights every selected source and partition-manifest
path before reading anything, then reuses the population/metadata/fold validators.
Only development observations proceed to processing. The notebook supplies its
existing pandas decoder and null conversion; the shared functions themselves
need no scientific packages. No unselected source or manifest is opened and no
output directories are created by loading or preparation.

`prepare_selected_branches` calls the Email callback only when Email is selected.
That callback retains the existing frozen-rule reference guard and unchanged
lexical implementation. The callback's original source fields and metadata must
remain unchanged. U1 adds the existing canonical unavailable indicator encoding:
support false, availability false and no evidence, with dimension state
Unavailable. It never interprets titles, links or engineered flags as behavioral
evidence. No missing Email frame, URLs or identity fields are fabricated.

The notebook's selected dictionaries drive diagnostics, state aggregation,
evidence tables and compact vectors. Optional PhiUSIIL diagnostic fields are
reported only if present; their absence does not become a new eligibility rule
or negative evidence. The previous combined Email/PhiUSIIL lexical-summary
columns are retained. Rule patterns, lexical functions, dimension aggregation,
state encoding and the five-metadata/eight-behavior compact schema are unchanged.

## Fixed handoff and failure guarantees

The exporter retains D9 filenames beneath `experiments/runs/<run_id>/`:

- `data/processed/features/development/<selected>_development.csv`
- `data/processed/features/sebrl/<selected>_sebrl_features.csv`
- `data/processed/features/development/development_input_manifest.json`

Actual canonical filenames come from the existing D9 constants, not string
guesses. The manifest contains only selected branches, existing contract/run IDs,
allowlisted filenames and hashes of the exact serialized bytes. Shared codebook,
availability, evidence and summary artifacts use the six existing fixed paths;
they derive from selected frames and do not add unselected branch handoffs.

All development metadata, compact joins/masks, payload serialization and output
collisions are checked before creation. Fixed-path resolution reuses the D9
redirection checks. Files are created exclusively with `xb`; the manifest is
last. Existing files are never truncated, removed or overwritten. On an ordinary
IO failure, cleanup removes only files and empty directories created by that
call, using no recursive deletion. Selected-input/configuration/validation and
collision failures create no output files or directories.

This is not a multi-file transaction under process termination or an adversarial
concurrent filesystem. An interrupted process may leave partial exclusive files;
their absence of a complete accepted manifest must not be treated as a valid
handoff. Do not overwrite such files on rerun. No new research output was created
in this session; all export tests used task-owned synthetic directories.

## Tests actually executed

The initial 125-test focused run passed. After additional manifest/parser/source
preservation cases, the final focused set contains 131 tests: 34 new branch tests
and the 97 D9 tests. No pre-existing assertion failure was observed.

All Python invocations used `-B`, `PYTHONDONTWRITEBYTECODE=1`,
`DATABASE_URL=sqlite:///:memory:` and `-p no:cacheprovider`. TEMP/TMP and pytest
basetemps were under:
`<user-profile>/AppData/Local/Temp/sebrl-branch-isolation-73k0w530`.
`<task-temp>` below denotes that directory.

| Command | Result |
| --- | --- |
| `.venv/Scripts/python -B -m pytest ml/tests/test_branch_preparation.py ml/tests/test_development_experiments.py -q --tb=short -p no:cacheprovider --basetemp <task-temp>/focused-verified` | 131 passed in 5.55 s, including the final notebook guard assertion |
| `.venv/Scripts/python -B -m pytest ml/tests/test_experiment_inputs.py ml/tests/test_experiment_integration.py ml/tests/test_notebook_contracts.py ml/tests/test_preflight.py -q -p no:cacheprovider --basetemp <task-temp>/neighboring` | 170 passed |
| `.venv/Scripts/python -B -m pytest ml/tests backend/tests -q -p no:cacheprovider --basetemp <task-temp>/full-verified` | 732 passed in 15.23 s; one installed Starlette/httpx deprecation warning |
| `npm.cmd run test --workspaces --if-present -- --configLoader runner` | 17 extension tests and 8 dashboard tests passed |
| Static `ast.parse` across all six notebooks | 275 code cells valid; no cells executed |

The frontend command uses the previously verified Vite runner-loader workaround
without modifying packages, configuration or execution policy. Npm cache storage
was task-owned. No installation or environment replacement occurred.

Coverage proves:

- PhiUSIIL-only, UCI-only and both-technical preparations succeed with synthetic
  inputs containing no Email files or required Email content columns.
- Only selected fixed inputs/manifests are opened; a failing Email callback is
  never invoked for U1. Notebook source guards also exclude Email examples,
  lexical functions and diagnostics from the technical path.
- Original fields, IDs, labels, groups and folds are preserved; only development
  records are prepared. Technical vectors remain unavailable even when fixture
  titles contain action/credential phrases.
- Generated handoffs load successfully through the actual D9 consumer and expose
  U1-only configurations for technical branches.
- Combined-mode dispatch calls the Email callback once and preserves the expected
  Email vectors and all three handoffs. An Email-selected freeze failure is not
  bypassed.
- Invalid selections, missing selected sources/manifests, inconsistent manifests,
  changed source fields, invalid masks and output collisions fail without output
  creation. Parser errors are sanitized.
- Only allowlisted selected/shared outputs are created; injected IO failure
  restores the prior synthetic file/directory inventory.

Synthetic CSV decoding substitutes for pandas in shared-function tests because
the scientific environment is not installed. The notebook uses its unchanged
pandas decoding path. Combined pandas/corpus execution has not been reproduced;
passing these tests is not a claim that a research notebook run is validated.

## Preservation and remaining D6 gaps

Notebook 04 cell identities, metadata, execution counts and stored outputs remain
unchanged from the initial working copy. A byte/source comparison also preserves
the existing rule definitions, lexical functions, dimension aggregation and
encoding. Its retained outputs remain marked historical/stale. This task did not
repeat the previous session's unscoped dataset whitespace diagnostic; checks were
restricted to code/report text and opaque preservation hashes.

The following still prevent D6 or research execution from being declared complete:

1. Actual source-label provenance remains pending in the existing email label
   audit. Materialized payloads alone do not establish eligibility or screening.
2. Reconciled template/campaign/domain/near-duplicate groups and accepted
   source/group/split/attrition records are incomplete. No grouping parameters
   were invented and no partition assignments changed.
3. The behavioral specification remains pre-freeze: operational rules, original
   locators, language coverage and partial-availability semantics need verified
   conformance. U1 independence does not approve the Email rules.
4. The real selected development handoff, explicit conventional dictionary and
   scientific environment are not ready. No corpus rows were validated here.
5. Historical test exposure, including the prior documented diagnostic exposure,
   remains part of the evaluation-integrity decision. No resealing claim is made.
6. No research-data E1/E2/E3 fit, calibration or transformer implementation has
   occurred. The historical Notebook 05 remains separate and unchanged.

## D1-D16 status

| Task | Status | Evidence / remaining acceptance |
| --- | --- | --- |
| D1 | IN PROGRESS | Approved branch roles retained; governing-version and outstanding experimental decisions remain |
| D2 | IN PROGRESS | Notebook 03 repairs preserved; actual eligible construction/group freeze still pending |
| D3 | IN PROGRESS | Payload identity preserved; source/label/count/screening and relationship evidence incomplete |
| D4 | BLOCKED | No new accepted group/split freeze or resolution of historical exposure |
| D5 | IN PROGRESS | Twelve canonical indicator definitions preserved; frozen operational conformance pending |
| D6 | IN PROGRESS | Branch isolation and synthetic alignment verified; actual-data masks/metadata/locators not accepted |
| D7 | IN PROGRESS | Existing exclusions/isolation checks retained; scientific leakage/confounding audit incomplete |
| D8 | COMPLETE | Available software suites and static syntax checks passed in this task |
| D9 | IN PROGRESS | D9 repairs and independently selected preparation verified synthetically; real accepted handoff pending |
| D10 | BLOCKED | Scientific eligibility, selected handoff, environment and experiment controls incomplete |
| D11 | BLOCKED | No transformer implementation or approved methodological amendment |
| D12 | BLOCKED | No repaired-pipeline final classification/calibration evidence |
| D13 | BLOCKED | New research CV/ablation execution depends on accepted data and protocol |
| D14 | IN PROGRESS | Fixed hashed selected exports and rollback verified; no real experiment bundle |
| D15 | IN PROGRESS | This report documents bounded progress; final empirical manuscript work remains |
| D16 | BLOCKED | Research freeze/final handoff depends on the earlier scientific gates |

## Exactly one recommended next task

Perform a **UCI-only metadata readiness audit for D3/D6**: reconcile the approved
source snapshot, schema/native-label evidence and supplied grouping/split/fold
records required for its first authorized dataset-to-feature verification.

Acceptance: source hashes and documentation are traceable; the exact required
preprocessed/manifest/dictionary inputs are identified; existing group/fold and
unavailable-evidence requirements are checked from permitted metadata; missing
evidence is reported explicitly. Do not infer a scientific freeze, create splits,
read Email content or reserved prediction rows, install packages or train models.

## Final Git safety and handoff

Verified final status is 22 unstaged tracked paths, 21 untracked files and no
staged changes. Notebook 04 and the existing D9 test file were already pending;
the branch module, its tests and this report are new. HEAD, branch, upstream,
remotes and Git index/config remain unchanged. Checksum comparison against the
242-file starting snapshot shows only these five intentional changes/additions,
with no removals. Historical datasets,
partitions, results, decision records, Notebook 05 and the application database
match the initial baseline. No commits, pushes, resets, cleanups of existing
work, synchronization, notebook execution, model fitting or transformer work.

Context for ChatGPT: explicit Notebook 04 branch selection now governs loading,
Email callback dispatch, diagnostics, aggregation and fixed exclusive exports.
U1-only and combined shared paths pass synthetic D9-compatible handoff tests;
the Email freeze gate/rules remain intact. D6 is IN PROGRESS, D10/D11 BLOCKED.
Next proposed task: a UCI-only metadata readiness audit, without training.
