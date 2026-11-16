# UCI supplied-assignment preparation - November 1, 2026

The UCI-only preparation API is implemented and verified using synthetic fixtures.
It preserves supplied assignments and creates only the existing three-file D9
handoff. It does not allocate IDs, groups, partitions or folds, discover/read
dataset inputs, fit estimators, authenticate scientific approvals or authorize
actual-data execution. UCI D3/D6/D9 remain partial.

## Starting checkpoint and inspection

Checkout: `<user-profile>/Desktop/Projects/Thesis_Prototype_Git`.
Branch `main`; HEAD `6bded57d38e9b83ba718d7795b97e2130128c23f`;
upstream `origin/main`.

- `origin` remains `https://github.com/LichSavant/Thesis_Protoype_Test.git`.
- `se-brl` remains `https://github.com/LichSavant/CS4101-Thesis2-SE-BRL.git`.
- Initial Git status: 22 unstaged tracked paths, 22 untracked files, nothing staged.
  Existing tracked changes include nineteen materialized LFS datasets and
  Notebooks 01/03/04; these were preserved.
- A fresh baseline fingerprinted 246 existing files, including tracked/untracked
  work, all experiment/database files, Git index/config and opaque historical
  artifact bytes. No prediction or outcome rows were parsed.
- Read AGENTS.md and inspected N03 UCI construction/grouping/allocation/export
  cells, N04 branch loading/dispatch/export, notebook/input/integration contracts,
  D9 specification/consumer/tests, branch tests and the UCI readiness report.
- N04 still reads a complete selected preprocessed CSV before filtering
  development. N03 still has combined loading and partition allocation. Neither
  notebook is changed or executed here.
- The existing unavailable-state encoding and explicit D9 feature specification
  are reused. No real feature dictionary, source freeze or independent group
  relationship is inferred from historical files.

The governing requirements remain the approved proposal's Sections 4.3.3-4.3.5
and Tables 4.4/4.6/4.7: supplied conservative groups and split barriers,
Unavailable distinct from Absent, and independent technical U1-UCI. The preceding
`2026-11-01_uci_metadata_readiness.md` records the relevant paper references and
unresolved UCI evidence. Supporting drafts are not approvals or amendments.

## Exact changes

| New file | Purpose |
| --- | --- |
| `ml/uci_preparation.py` | Small in-memory UCI-only preparation entry point with strict manifest/payload joins and protected D9 export |
| `ml/tests/test_uci_preparation.py` | 81 synthetic acceptance/failure-boundary cases |
| `docs/research/2026-11-01_uci_supplied_assignment_preparation.md` | This continuation report |

No existing source module, test, notebook, dataset, manifest, decision draft or
result was edited. In particular, the existing combined Notebook 04 workflow and
historical Notebook 05 remain unchanged.

## API and reused contracts

The public function is `ml.uci_preparation.prepare_uci_handoff`:

~~~python
paths = prepare_uci_handoff(
    checkout,
    run_id,
    development_records,
    assignment_manifest=full_partition_metadata,
    expected_observation_ids=accepted_population_ids,
    specification=uci_development_specification,
)
~~~

All named inputs are required caller-supplied values, not new approved defaults.
This API accepts decoded in-memory records. It is not a CLI, corpus adapter or
CSV parser and has no automatic input discovery, historical-path fallback, or
data download. The caller remains responsible for authorized acquisition,
decoding, source hashes, original-row lineage, research acceptance and custody.
Passing reference strings does not establish those facts.

The existing schemas remain:

- Assignment records: exactly `observation_id, source_dataset, target, group_id,
  partition, cv_fold`, as exported by N03 cell `bd73bb48`.
- Development payload: the existing five D9 metadata fields plus `source_dataset,
  source_row_id, Result` and exactly the explicitly declared conventional fields.
- Existing optional audit columns `source_label` and `feature_hash` are retained
  as metadata, never predictors. Native source_label must agree with Result;
  feature_hash is checked as a nonblank string, not recomputed or authenticated.
  Unknown extra fields, including unselected engineered fields, are rejected.
- Feature specification: existing `DevelopmentSpecification` / `FeatureColumn`,
  explicitly dataset UCI, nonempty unique numeric feature list, protocol reference
  and dictionary reference. No default 30-column list or per-feature scientific
  encoding policy is invented.
- Compact output: existing five metadata fields plus eight canonical dimension
  support/availability fields.

`expected_observation_ids` is a required nonempty frozenset for the full supplied
population. Without an independent expectation, deleting an otherwise valid
reserved assignment could be indistinguishable from a smaller manifest. This
argument supplies that ordinary coverage check; it introduces no alternate row
schema, group algorithm, count default or split recipe. Its scientific provenance
must come from accepted population/lineage evidence; deriving it from the same
manifest does not independently prove completeness.

Implementation sequence:

1. Require the explicit UCI specification and fixed valid run ID. Reject
   behavioral-derived field names in the conventional dictionary, including
   indicator-level fields; known labels/provenance/compact behavioral fields
   are already rejected by the existing FeatureColumn/selector contract.
2. Copy the supplied metadata records without mutating callers. Require the exact
   existing six-column manifest, UCI source and binary integer target types.
3. Reuse `PartitionAssignment`, `validate_supplied_partitions` and the existing
   lossless nullable `_fold` decoder. Reject duplicate IDs, partition/group/fold
   crossings, invalid folds, reserved folds and missing partition roles.
   Require exact full expected-ID coverage and both classes in all three roles.
4. Validate development-only payload schema, native Result/target/source/position
   mappings and group/fold/class coverage through `validate_feature_boundary`.
   Require exactly the manifest's development IDs and an exact ID-based metadata
   join. Manifest ordering cannot misalign observations.
5. Reject invalid/nonfinite numeric values using the existing D9 numeric/null
   policy before dispatch. Preserve values and None; no imputation, recoding,
   scaling or selection occurs.
6. Invoke existing `prepare_selected_branches` with exactly `("UCI",)` and no
   Email callback. Preserve all original source fields. Use existing canonical
   unavailable indicators/dimension states.
7. Build compact vectors and prevalidate with the actual
   `build_development_dataset` / `development_folds` U1 consumer logic. A private
   validation view decodes lossless float folds to integer form for D9; exported
   records retain supplied fold representation and membership.
8. Reuse `export_selected_handoff` and `_within` with no shared-output argument.
   No read of Email/PhiUSIIL, raw/clean UCI, calibration/test predictor payloads,
   historical results or notebook cells is performed by this entry point.

Source values are retained; missing target/group/partition/fold metadata is
rejected rather than generated from a heuristic or "repaired."

### Unavailable is not a negative finding

The unchanged technical dispatcher assigns all twelve indicators support false,
availability false and audit evidence "[]"; all four dimension states are
Unavailable. In the existing compact schema, support=0 WITH availability=0
means Unavailable; Absent would require availability=1. Neither zeros nor empty
audit evidence establish known absence. No missing urls=[] or Email content is
created, and engineered indicators do not become behavioral evidence.

D9's U1 fold predictors contain only declared conventional columns. The eight
behavioral slots are validated contract metadata and are not appended to U1
predictor tuples. Native feature -1 and 0 codes remain unchanged.

The API validates numeric types/nulls/finite values, not an independently audited
per-feature domain dictionary or source authenticity. Accepted UCI domain/encoding
evidence remains a real-data gate; this task defines no new global value-domain
restriction or missingness policy.

## Fixed outputs and failure boundaries

Only these existing paths are produced under `experiments/runs/<run_id>/`:

1. `data/processed/features/development/uci_development.csv`.
2. `data/processed/features/sebrl/uci_sebrl_features.csv`.
3. `data/processed/features/development/development_input_manifest.json`.

There is no alternate branch or optional shared-summary export in this API.
Manifest entries contain only UCI, existing contract/run IDs, allowlisted
filenames and SHA-256 of exact serialized bytes.

All validation/serialization/collision checks precede directory/file creation.
Writes use exclusive `xb`, and the manifest is last. Ordinary export IO failures
reuse the existing rollback of that call's new files and empty directories.
Tests cover behavioral-file open failure, manifest open failure and partial
manifest write failure; no partial/completed bundle remains in those cases.

This is not an atomic transaction under process termination or hostile concurrent
filesystem mutation. An interrupted partial bundle must not be overwritten or
treated as completed. Existing output collisions are rejected without changing
the old files. No scientific assignments are ever exported or rewritten.

## Synthetic verification actually performed

All Python runs used `-B`, `PYTHONDONTWRITEBYTECODE=1`,
`DATABASE_URL=sqlite:///:memory:` and `-p no:cacheprovider`.
TEMP/TMP and all pytest basetemps were task-owned:

`<user-profile>/AppData/Local/Temp/sebrl-uci-supplied-7hhbcvg3`.

The fixture contains ten synthetic development observations across five supplied
mixed-target groups/folds and four reserved metadata-only assignments. It uses
two declared synthetic numeric fields, including -1 and 0, not a claimed approved
research dictionary or real source records. Temporary output checkout roots
contain no research datasets.

| Exact command, with common environment above | Actual result |
| --- | --- |
| `.venv/Scripts/python -B -m pytest ml/tests/test_uci_preparation.py -q --tb=short -p no:cacheprovider --basetemp <task-temp>/focused-first` | 78 passed, 3 failed |
| Same focused command with `--basetemp <task-temp>/focused-second` | 81 passed in 2.15 s |
| `.venv/Scripts/python -B -m pytest ml/tests/test_branch_preparation.py ml/tests/test_development_experiments.py ml/tests/test_notebook_contracts.py ml/tests/test_experiment_inputs.py ml/tests/test_experiment_integration.py ml/tests/test_preflight.py -q -p no:cacheprovider --basetemp <task-temp>/neighbors` | 301 passed in 7.02 s |
| `.venv/Scripts/python -B -m pytest ml/tests backend/tests -q -p no:cacheprovider --basetemp <task-temp>/full` | 813 passed in 20.52 s; one Starlette/httpx deprecation warning |
| `npm.cmd run test --workspaces --if-present -- --configLoader runner` | 17 extension and 8 dashboard tests passed |
| Static `ast.parse` of all six notebooks and the two new Python files | 275 notebook code cells valid; no notebook cells executed |

The first-run failures were two fixture assertions using legacy dimension names
instead of the canonical pressure_threat_cues identifiers, and a NaN error-path
assertion: NaN reached unchanged-source comparison before numeric validation.
The test identifiers were corrected and numeric validation moved before dispatch.
No shared rule semantics or existing tests were weakened or changed. All final
focused/full checks pass.

The frontend suite used the existing runner-loader workaround with task-owned
npm cache; no package/configuration/environment changes or installation. The
installed Starlette/httpx warning was recorded, not repaired by replacing packages.

Coverage establishes:

- Reversed manifest ordering joins to the correct source observation and preserves
  IDs, target, group, role, fold, native codes and source fields without input
  mutation.
- Missing/extra development AND reserved assignment IDs, duplicate/conflicting
  IDs, source/target/native mismatches, invalid schema and invalid dictionaries
  fail without creating paths.
- Supplied partition and fold/group crossings, invalid/missing/boolean/fractional
  folds, assigned reserved folds and reserved payload records are rejected.
- No unknown predictor columns or behavioral-derived fields enter U1.
  Native -1/0/1 values and explicit missing None remain unchanged.
- Canonical unavailable indicator/dimension states exist before compaction;
  the actual D9 loader accepts produced hashes/schemas and exposes only U1 fold
  plans with labels separated from predictor tuples.
- A Path.open guard permits only the canonical codebook resource and the three
  new fixed output files: no dataset input, Email or PhiUSIIL file is opened.
- A fresh subprocess rejects imports of scientific/estimator packages and Email
  rule/extraction modules while successfully running synthetic preparation.
  This entry point has no estimator object or model/preprocessing fitting path.
- Existing output collisions preserve old bytes; injected late/partial IO
  failures leave no misleading bundle or created directories.

No test read real UCI feature records, sealed-test predictions or outcomes.
Software checks are not actual-data readiness evidence.

## Remaining UCI real-data execution blockers

The preceding metadata-readiness report is preserved. Its source-identification
and historical metadata findings are not promoted to a new scientific freeze.

| Required evidence | Still needed before real preparation |
| --- | --- |
| Acquisition and native class definition | Bound source snapshot/access/license record and exact source-backed Result mapping citation; repository assertions alone do not complete this |
| Original identity and attrition | Version-bound raw-to-clean canonical-row/duplicate lineage, reason-coded exclusions and reconciled retained ID population |
| Group/split acceptance | Explicit UCI vector-only grouping limitation and accepted supplied partition/fold reuse, without claiming domain/campaign independence |
| Feature dictionary | Actual accepted ordered columns, per-field domains/types/representation/null/exclusion policy and resolvable version/reference |
| Payload access/custody | Accepted development-only delivery/decoder scope and exposure-aware claim plan; actual full ID expectation must come from independent accepted population evidence |
| Actual inputs | Authorized decoded development records and full assignment metadata bound to their real hashes, plus unused run ID and code/config/environment record |

The software entry point now avoids N03 allocation and N04's whole-population
input loader. It does not acquire/create/verify those real inputs or implement a
production CSV decoder. No complete research feature dictionary is chosen. A
reference string cannot substitute for approval. Historical test exposure cannot
be undone or resealed by this component.

Email rule/language decisions, a new Web dataset, transformer training, human
annotation and every unrelated pending H item are not prerequisites to this
software repair. They were not introduced. Scientific source, grouping, feature
and exposure decisions remain with the researchers/adviser where applicable.

## Updated D1-D16 checklist

| Task | Status | Current evidence / remaining requirement |
| --- | --- | --- |
| D1 | IN PROGRESS | Approved UCI technical role retained; source-specific acceptance/experimental controls not frozen |
| D2 | IN PROGRESS | Existing N03 repairs preserved; new UCI API bypasses allocation but does not validate real preprocessing |
| D3 | IN PROGRESS / PARTIAL | Manifest/ID/type/source coverage checks synthetic; actual lineage/screening/group acceptance incomplete |
| D4 | BLOCKED for research execution | Supplied partition/fold barriers implemented/tested; accepted real split/custody/exposure evidence pending |
| D5 | IN PROGRESS | Twelve canonical indicators preserved; no Email behavioral-specification approval inferred |
| D6 | IN PROGRESS / PARTIAL | UCI alignment/availability/native-code software boundary verified; no real dataset-to-feature verification |
| D7 | IN PROGRESS | Explicit dictionary/exclusion and reserved-payload barriers; source/group/leakage evidence still pending |
| D8 | COMPLETE within software scope | 81 focused, 301 neighboring, 813 complete Python, 25 frontend tests and 275 static cells pass |
| D9 | IN PROGRESS / PARTIAL | UCI supplied-assignment handoff passes actual D9 consumer synthetically; real accepted handoff absent |
| D10 | BLOCKED | No research models run; real UCI acceptance and frozen experiment settings still needed |
| D11 | BLOCKED / not implemented | Governing method remains deterministic SE-BRL; no transformer or annotation prerequisite introduced |
| D12 | BLOCKED | No new classification/calibration/final evaluation |
| D13 | BLOCKED | No research-data CV/ablation execution |
| D14 | IN PROGRESS | Fixed exclusive hashed UCI bundle verified synthetically; no real experiment bundle |
| D15 | IN PROGRESS | This bounded report records implementation, failure history, limitations and remaining evidence |
| D16 | BLOCKED | No final research freeze/release or researcher handoff |

## Exactly one recommended next task

Prepare a **UCI-specific acceptance packet from existing documentation** that
binds source/clean hashes and class-definition evidence to the explicit dictionary,
population lineage, supplied split and access scope. Keep missing lineage,
grouping/exposure decisions and approvals explicitly Pending. Do not execute
actual preparation or model experiments as part of that documentation task.

## Final preservation and Git state

Verified final inventory: 22 unstaged tracked paths, 25 untracked files, no staged
changes. HEAD/main/upstream/remotes remain unchanged. Final checksum comparison
against the 246-file starting baseline shows only the three additions listed
above and no changed/removed existing file. This includes historical datasets,
partitions, metrics, predictions,
plots, coefficients, thresholds, manifests, notebooks, previous research drafts,
persistent application database and Git index/config.

No research-run directory or feature bundle was created inside the checkout.
All produced CSV/JSON fixtures were under task-owned temporary roots. No
commit, push, staging, reset, clean, synchronization, environment replacement or
configuration change occurred.

Context for ChatGPT: UCI-only in-memory prepare_uci_handoff now requires decoded
development records, exact existing six-column full assignment metadata,
independent expected full ID frozenset and existing explicit numeric
DevelopmentSpecification. It validates exact supplied coverage/joins, uses
canonical unavailable technical states, rejects labels/provenance/behavioral
predictors and exclusively creates only the three fixed D9 UCI files.
81 new cases/301 neighbors/813 Python/25 frontend/275 static cells pass; one
existing deprecation warning. No real UCI preparation or notebook execution.
D3/D6/D9 remain partial; source/lineage/dictionary/group/access acceptance is
pending. Only the new module, its tests and this report were added.

