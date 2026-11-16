# Controlled D9 continuation - November 1, 2026

This is a technical continuation report, not a protocol amendment, scientific
freeze, dataset acceptance or new model result. Only the D9 consumer, its tests
and this new report changed. All other work remains preserved.

## Repository state and scope

Checkout: `<user-profile>/Desktop/Projects/Thesis_Prototype_Git`.
Branch/HEAD: `main`, `6bded57d38e9b83ba718d7795b97e2130128c23f`.
Upstream remains `origin/main`. Configured remotes remain:

- `origin`: `https://github.com/LichSavant/Thesis_Protoype_Test.git`
- `se-brl`: `https://github.com/LichSavant/CS4101-Thesis2-SE-BRL.git`

The initial filter-disabled status had 22 unstaged tracked paths (19 materialized
LFS datasets and three previously repaired notebooks), 17 untracked files and no
staged files. Verified final status is the same 22 tracked paths and 18
untracked files: the two edited D9 files were already untracked; this report is
new. A read-only GitHub reference query independently returned the same thesis
`main` SHA. No synchronization or remote/upstream reconfiguration occurred.
The prior checkpoint established that the old origin URL redirects to the thesis
repository, while its local tracking ref is stale; do not infer the destination
of a future push from the tracking name alone.

The governing PDF is
[`Thesis_Proposal_Documents/Alcover & Orbello_Approved Document Proposal.pdf`](../../Thesis_Proposal_Documents/Alcover%20%26%20Orbello_Approved%20Document%20Proposal.pdf).
Its cover and approval sheet (PDF pp. 1-2) use the modality-aware machine-learning
title without **Transformer-Augmented**. Section 4.3.4 and Tables 4.5-4.6 specify
deterministic SE-BRL. This conflicts with the continuation prompt's title; neither
the title nor the methodology was changed to hide that discrepancy.

## D9 defects, fixes and compatibility

Changed files:

1. `ml/development_experiments.py`: strict CSV/header/schema checks and fixed
   resolved-path validation; unambiguous manifest parsing.
2. `ml/tests/test_development_experiments.py`: 59 additional synthetic cases.
3. This report: independently verified progress, limitations and next task.

### CSV boundary

The old `csv.DictReader` accepted an unterminated final quoted field even when
the malformed bytes had a matching manifest hash. Hashing proves identity, not
CSV validity. Blank headers and unexpected compact behavioral columns were also
accepted.

The consumer now uses `strict=True`, rejects blank/duplicate headers, checks
required columns before row consumption, and requires exactly the existing five
metadata plus eight canonical behavioral columns in compact behavior CSVs.
Malformed row widths, values, duplicate IDs, reserved records and inconsistent
metadata continue to fail closed through the existing validators. Exceptions
remain sanitized and the global CSV field-size limit is restored on failure.

Conventional handoffs intentionally retain additional source/audit columns for
compatibility with Notebook 04's existing full development-input export. Their
required native-label/source/position/partition fields and declared predictors
are checked, but unselected columns are not automatically treated as predictors.
Only the explicit `DevelopmentSpecification.conventional` dictionary can select
model inputs. A new closed source-field dictionary was not invented.

Valid UTF-8 BOM input, quoted commas/quotes, multiline text, long text, nullable
numeric predictors and unselected source fields remain supported. No evidence
semantics, label mapping, predictor default, rule or scientific threshold changed.

### Fixed locations and manifest boundary

Previously, containment within a run permitted a named development file,
manifest, directory or entire run path to resolve elsewhere inside that run or
checkout. The code now canonicalizes the explicitly supplied checkout, then
requires every fixed descendant path to retain its expected lexical location.
Redirected symlink/junction resolution and paths outside the run are rejected
before opening the redirected file. Unresolvable paths produce a sanitized
contract error. Invalid run IDs and mismatched manifest filenames remain rejected.

The manifest parser also rejects duplicate JSON object keys, so a later valid
filename/hash/version cannot silently replace an earlier conflicting declaration.
The existing valid manifest format and fixed filenames are unchanged.

These are ordinary local-file integrity checks, not an authentication system or
an adversarial concurrent-filesystem sandbox. They cannot prove scientific
approval, source authenticity, historical custody, or that a correctly named file
was never copied from another population. Hashes and references remain traceability
assertions. Dynamic path replacement after validation and hard-link provenance
are not solved by this bounded repair.

## Verification actually executed

Python: existing `.venv`, Python 3.12.10, pytest 8.4.2. All Python commands used
`-B`, `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider` and distinct task-owned
`--basetemp` directories beneath the session's `sebrl-d9-hardening-*` temporary
root. TEMP/TMP pointed there. `DATABASE_URL=sqlite:///:memory:` was set before
test imports, keeping the persistent application database out of the test path.
The task root was
`<user-profile>/AppData/Local/Temp/sebrl-d9-hardening-rqrdx_qi`;
`<task-temp>` in the commands below denotes that exact directory.

| Check | Command, with common options above | Actual result |
| --- | --- | --- |
| Original D9 baseline | `.venv/Scripts/python -B -m pytest ml/tests/test_development_experiments.py -q -p no:cacheprovider --basetemp <task-temp>/d9-before` | 38 passed |
| New regression cases against old code | Same suite with `--tb=short`, basetemp `d9-reproductions` | 16 failed, 81 passed; intentional reproductions of existing acceptance gaps |
| Repaired D9 | Same suite, basetemp `d9-after` | 97 passed |
| Neighboring contracts | `.venv/Scripts/python -B -m pytest ml/tests/test_experiment_inputs.py ml/tests/test_experiment_integration.py ml/tests/test_notebook_contracts.py ml/tests/test_preflight.py -q -p no:cacheprovider --basetemp <task-temp>/neighboring` | 170 passed |
| Complete Python ML/backend suite | `.venv/Scripts/python -B -m pytest ml/tests backend/tests -q -p no:cacheprovider --basetemp <task-temp>/full-regression` | 698 passed, one Starlette/httpx deprecation warning |
| Standard frontend launch | `npm test`, then `npm.cmd test` | PowerShell script policy blocked the first; default esbuild config loading hit a parent-directory access error in the second; no assertion results |
| Available frontend suites with supported loader | `npm.cmd run test --workspaces --if-present -- --configLoader runner` | Extension: 17 passed; dashboard: 8 passed |
| Notebook syntax only | `ast.parse` on code sources in all six notebooks | 275 valid code cells; none executed |

Installed Vite 6.4.3/Vitest 3.2.7 support the alternate loader. It was selected
only on the command line; no configuration, execution policy, dependency or
environment installation was changed. Npm cache output used task-owned storage.
No remaining test assertion failures were observed after the repairs. The launch
errors are environment/config-loader limitations, not evidence of a Python D9
regression; no claim is made that the default frontend launcher itself was fixed.

Path tests simulate resolved symlink/junction locations, covering same-run and
outside-run redirection without requiring Windows symlink privileges. They verify
that redirected targets are not opened. They are not a newly measured Windows
filesystem stress test. Existing valid per-branch handoffs and fold tests pass.

## Diagnostic exposure incident

An unscoped `git diff --check` with LFS filters disabled treated materialized
payloads as additions and emitted raw dataset lines in whitespace diagnostics.
This was an avoidable diagnostic mistake; further content checks were restricted
to the D9 source files. No dataset bytes or partitions were changed, and no
row-level historical holdout prediction file was opened for analysis.

Those diagnostics were not used to tune rules, choose features/models, compute
research metrics or validate records. Nevertheless, this session cannot claim
that raw dataset contents remained unseen. The affected record partition
membership was not examined, so no fresh sealed-test-integrity claim is made.
This incident must be included in the researchers' exposure/custody assessment.

## Read-only D2-D8 and E1-E3 readiness findings

| Area | Verified evidence | Remaining gate / smallest correction | Ownership / approval |
| --- | --- | --- | --- |
| Source roles and labels | `ml/notebook_contracts.py` uses Nazario positives plus Enron/SpamAssassin ham; CEAS-08 is auxiliary. PhiUSIIL/UCI are U1. This matches Section 4.2.1/Tables 4.1-4.2/4.7. | Email native-label provenance is still pending in `experiments/results/audits/verified_label_semantics.csv`; do not promote code mappings to source verification. | Vera supplies existing source/class documentation; Dhanwil reconciles metadata. Scope-changing mappings require joint/adviser approval. |
| Payloads and provenance | All 19 working LFS payload hashes are preserved against the checkpoint; the materialization prerequisite is now met. No abandoned dataset is reintroduced. | No completed `source_manifest.csv`, `label_mapping.yaml`, `screening_log.csv`, `dataset_attrition.csv` or equivalent frozen evidence package was found in the inspected research paths. Raw/clean lineage and reasons must reconcile under Table 4.4. | Dhanwil performs technical checks against source evidence; no replacement study or invented exclusion rules. |
| Observation identity | Pre-filter cleaned-source positions and exact population/metadata validators exist and have synthetic coverage. | Actual retained-population counts/identity/duplicate checks were not run. Cleaned positions are not reconstructed raw-corpus IDs. | Dhanwil; requires matching source/screening records. |
| Grouping and isolation | Supplied group/partition/fold checks exist. Historical manifests were preserved; earlier metadata checks reported no crossings. | Historical sender/exact-body, exact-domain/vector recipes do not establish complete template/campaign/near-duplicate independence. No new `group_manifest.csv`/`split_manifest.csv` or documented reconciled parameters was found. Notebook 03 retains the specific grouping guard. | Researchers document source-permitted relationships/configuration; Dhanwil implements and validates. Scientific parameter/claim decisions need research agreement, not guessed constants. |
| Behavioral states and evidence | Canonical four dimensions/twelve IDs, unavailable optional evidence, English gating and technical U1 masking exist. Codebook status remains `pre_freeze`. | Notebook 04 still has draft broad patterns, normalized evidence fragments without original-field offsets, and any-available aggregation. A reference string cannot replace a versioned verified rule/locator/language/partial-availability specification (Tables 4.5-4.6). | Vera/researchers specify operational meaning; Dhanwil implements conformance/locator tests. No human-annotation prerequisite is added to the deterministic study. |
| E1/E2/E3 controls | D9 builds identical Email IDs/labels/folds for E1/E2/E3; explicit predictors exclude known bookkeeping; canonical support/availability is separate. | No actual conventional feature dictionary or `development_input_manifest.json` exists; `experiments/runs/` is absent. Consumer references remain unfilled in `05_development_preparation.ipynb`. | Dhanwil completes the audited-schema dictionary and handoff after relevant source/rule gates. |
| Technical branches | D9 independently supports PhiUSIIL/UCI U1 and rejects behavioral values for them. | Notebook 04 still loads/exports all branches and reaches the Email rule guard before U1 export. This is mechanical coupling, not a scientific requirement that U1 wait for Email behavior rules. | Dhanwil may propose branch-scoped preparation; retain U1 roles and each branch's own audit gates. |
| Source confounding / exposure | Historical Email target is correlated with source; old Notebook 05 and result manifest identify historical LR experiments. No new research fit occurred. | Table 4.4 requires source-only, format and source-stratified analysis. Historical exposure plus the diagnostic incident require an accepted evaluation/custody plan; no historical holdout can be resealed by software. | Joint researcher/adviser decision for evaluation claims; Dhanwil supplies technical evidence. |
| Scientific environment | Current environment lacks NumPy, pandas, SciPy, sklearn, matplotlib, XGBoost, torch and transformers. | An authorized, pinned scientific environment is needed for later research execution. No packages were installed. | Dhanwil coordinates environment provisioning separately. |
| Model experiments | Four families are declared; historical Notebook 05 implements LR. New D9 exposes fold inputs only. | No new estimator factory, nested-search/OOF scorer, uncertainty/efficiency benchmark, calibrated final model or immutable model-result bundle exists. Freeze branch-specific settings under Sections 4.3.5.1-4.3.5.3/Tables 4.8-4.10 before comparative fits. | Dhanwil implements the agreed experiment mechanics; unresolved statistical choices require researcher/adviser decision. |

**E1-E3 research execution is not ready.** Payload availability and passing
software tests do not satisfy the remaining scientific gates. Historical
`05_experiments.ipynb` must not be run wholesale against the new namespace.
It still has historical roles, identifiers, reserved procedures and generic
writers. The repaired consumer has no writer or reserved-data loader; future
result generation needs a separate immutable namespace. U1 may progress
independently once its own evidence is complete; Web data is not a prerequisite
to unrelated Email/U1 repairs.

## D11 transformer feasibility - proposal only

### Verified current implementation

No transformer inference, fine-tuning code, tokenizer/model dependency or model
weight artifact was found in the inspected implementation. `ml/models.py` has
future classifier ports; `ml/se_brl/representation.py` explicitly keeps learned
z values null. Notebook/runtime indicators are deterministic candidate rules,
not transformer predictions. `BehavioralAnnotation`/`BehavioralGroundTruth` in
`ml/datasets.py` are types exercised by synthetic tests, not an independently
annotated research dataset. No dedicated independent behavioral-label corpus or
annotation artifact was located. This does not establish that none exists
outside the checkout.

The current architecture therefore does not support an implemented
Transformer-Augmented claim. Moreover, the supplied approved PDF's cover and
approval sheet omit that title phrase, and Section 4.3.4 expressly specifies no
behavioral-dimension model or annotation stage. The researchers/adviser must
reconcile the intended title and governing approved version before D11 changes.

### Smallest proposed augmentation

If an amendment is approved, prefer a **frozen compact text encoder as an
explicit conventional feature extractor**, with the deterministic BRL retained
as E2 and fused into E3. This avoids pretending that a text embedding is an
independent behavioral ground-truth label. Keep the four approved downstream
classifier families, and explicitly version the amended E1/E3 feature dictionary
so the representation comparison still uses matched records and folds. Retain a
historical conventional baseline rather than relabel its results.

An illustrative resource-constrained candidate is Google's English uncased
two-layer, 128-hidden BERT-Tiny; the [official model card](https://huggingface.co/google/bert_uncased_L-2_H-128_A-2)
documents that architecture and its language scope. This is a proposal, not a
selected model, approved feature, package installation or weight download.
Language, maximum length/chunking, pooling, normalization, tokenizer/version,
pretrained revision/license, hashes and missing-content behavior must be frozen.
No model-derived output may overwrite deterministic evidence or original locators.

With a frozen public encoder and immutable label-independent settings, encode
only eligible development records; fit any learned scaling/projection and the
classifier only within training folds. If the encoder or pooling is tuned on
study labels, that tuning must also be nested/fold-local. Audit pretrained-data
overlap and source/style shortcuts; measure local model-only and complete-feature
pipeline efficiency separately. No calibration/test record selects the encoder.

For planning only, not observed data/performance: N=20,000 records at L=256 tokens
would require about 5.12 million token positions in one frozen encoding pass;
128-dimensional float32 vectors use N*128*4 = 10,240,000 bytes (about 9.8 MiB).
There are zero encoder training epochs in this option. Wall time is N/r for
measured records/second r: hypothetical rates of 10 or 100 imply about 33 or
3.3 minutes, respectively, excluding tokenization, IO and classifier work.
These are arithmetic scenarios, not measured or guaranteed throughput. Actual
peak RAM, batching and CPU/GPU suitability require an approved synthetic
benchmark; no GPU allocation or latency limit is assumed here.

A transformer that **predicts the twelve indicators** is a different and larger
amendment. It needs a legitimate independent target and validation protocol,
group-safe train/validation/evaluation, evidence-reference and uncertainty
semantics, and justified sample/class coverage. Native phishing labels are not
behavioral labels. Training on the current rules and evaluating against those
same rules would measure rule imitation, not independent behavioral accuracy.
Do not generate pseudo-ground-truth or add human annotation to the approved
deterministic methodology by implication. No defensible supervised-training
workload can be estimated until that amended task and its data are defined.

Both options require adviser/researcher approval of the affected methodology,
title/claim scope, feature comparisons and evaluation-exposure response, plus
separate permission for environment/model acquisition. No D11 implementation is
authorized or performed by this report.

## D1-D16 progress register

COMPLETE means supported within the named scope, not scientific validation by
file presence. D9-A/B/C are complete bounded software repairs; the full D9
research handoff remains IN PROGRESS.

| ID | Status | Existing implementation / exact evidence | Remaining work | Dependencies / owner | Acceptance criterion |
| --- | --- | --- | --- | --- | --- |
| D1 | IN PROGRESS | Approved PDF Sections 4.2.1, 4.3.3-4.3.5; this title audit | Reconcile title/version and branch-specific frozen settings | Joint researchers/adviser | Governing version and actual protocol choices are traceable; no inferred amendment |
| D2 | IN PROGRESS | `03_preprocessing.ipynb` cells `95feb561`, `39163f5c`, `407edb97`; `ml/notebook_contracts.py` | Validate actual eligible construction/grouping; execute only after gates | Dhanwil, with source/group evidence | Audited population/IDs/attrition and feasible unchanged groups reconcile |
| D3 | IN PROGRESS | Preserved LFS payload hashes; `verified_label_semantics.csv`; population validators | Verify source/native labels, counts, screening and duplicates | Vera/source documentation; Dhanwil checks | Frozen source/label/screening/attrition evidence matches actual inputs |
| D4 | BLOCKED | Supplied isolation validators; preserved historical partition manifests | New reconciled group/split manifest and exposure assessment | Group freeze and joint evaluation decision | No relationship/group crossings; accepted custody/exposure plan, no resealing claim |
| D5 | IN PROGRESS | `04_feature_extraction.ipynb` canonical IDs and deterministic drafts; `ml/se_brl/` | Freeze/verify twelve-indicator rules, language, exclusions and locators | Operational specification, then Dhanwil implementation | Table 4.6 conformance/state/modality/reference tests pass |
| D6 | IN PROGRESS | `ml/notebook_contracts.py`, matching tests; Notebook 04 metadata checks | Verify actual masks, null semantics, input/output identity | Eligible inputs and specified BRL semantics | Exact joined IDs/metadata; unsupported evidence never becomes negative evidence |
| D7 | IN PROGRESS | Predictor exclusions, group checks, documented historical confounding | Actual relationship audit and required shortcut/generalization analyses | Frozen groups/features; joint exposure response | Traceable leakage controls and source-only/stratified evidence without test-driven choices |
| D8 | COMPLETE | 698 Python tests, 25 frontend tests, 275 static notebook checks in this session | Recheck when relevant code changes; maintain honest environment notes | Dhanwil | Available suites pass; limitations/warnings recorded; no research fits |
| D9 | IN PROGRESS | `ml/development_experiments.py`, matching 97-test suite, `05_development_preparation.ipynb`; D9-A/B/C fixed | Produce/accept real development handoff and dictionary after upstream gates | Dhanwil plus source/rule evidence | Exact hashed development-only handoff, matched E1/E2/E3 folds and safe exclusive outputs |
| D10 | BLOCKED | Fold preparation only; historical LR source remains separate | Implement and run approved candidate experiments | D3-D7, environment and frozen experimental controls | New grouped development OOF results for approved matched configurations; no reserved-data selection |
| D11 | BLOCKED | No transformer/weights/corpus; null z slots; feasibility proposal above | Adviser decision before any amended architecture | Title/protocol reconciliation and legitimate data objective | Approved amended claim, leakage-safe comparison and measured implementation evidence |
| D12 | BLOCKED | Historical metrics preserved; no repaired-pipeline fit | New classification/calibration evidence | Selected/frozen model and prescribed procedures | Versioned metrics from the accepted protocol; distinguish development and final evidence |
| D13 | BLOCKED | D9 matched folds; historical CV/ablation source | New approved CV, uncertainty and ablation analysis | Frozen data/groups/model controls | Same folds, paired group-preserving analysis and no test-based adjustment |
| D14 | IN PROGRESS | LFS identities, exclusive Notebook 03/04 writers, hashed handoff design | Complete environment/config/model/result bundle | Actual accepted run; Dhanwil | Immutable hashes, seeds, dictionaries, fits and operational settings reconcile |
| D15 | IN PROGRESS | This report plus preserved research drafts | Reconcile final manuscript with actual empirical findings/title | Joint scientific decisions and later results | All claims traceable; failures, exposure and limitations disclosed |
| D16 | BLOCKED | No new research freeze or final bundle | Validate/freeze accepted artifacts and researcher handoff | Earlier research gates | Reproducible accepted bundle, approvals and final summary; no unapproved push |

## Next single technical task

Make Notebook 04 preparation **branch-selective** using the existing D9 branch
contracts, so an approved technical U1 handoff does not require Email inputs or
the Email behavioral-rule gate. This is a proposed mechanical correction to
Table 4.7 independence, not permission to skip any selected branch's own audit.

Acceptance: a synthetic PhiUSIIL-only or UCI-only preparation never reads Email
files or invokes Email rules; roles remain U1-only; IDs/folds and unavailable
behavioral values are validated; only selected fixed filenames/hashes are
exported through exclusive creation; historical artifacts remain unchanged.
Do not train, select new scientific defaults or acquire new data for that task.

Smallest research dependencies in parallel: ask Vera for the existing source
class/provenance documents and agreed operational BRL specification; Dhanwil
handles mechanical validation. Ask the adviser to reconcile the title/protocol
version and evaluation-exposure response. Do not ask Dhanwil to replace the
study or resolve every H1-H12 item before unrelated implementation can continue.

## Preservation and handoff

Before/after SHA-256 comparison covers all tracked/untracked research/software
files, the materialized datasets, the persistent database and Git index/config.
The final comparison covered 242 files: only the two D9 source/test files changed
and this report was added; no files were removed. No notebooks,
raw/cleaned datasets, partition files, historical metrics/predictions/plots,
thresholds, coefficients, manifests or existing decision drafts were rewritten.
No staging, commit, push, branch change, remote/upstream edit, synchronization,
installation or model/calibrator training occurred.

Context for ChatGPT: bounded D9 parsing/fixed-path repairs pass 97 focused,
170 neighboring and 698 full Python tests; 25 frontend tests pass with the runner
config loader; 275 notebook cells parse without execution. The three changed
files are the D9 module, its tests and this new report. Payloads are present but
scientific eligibility/grouping/rule/dictionary/environment gates still block
D10. No transformer is implemented; the approved PDF title/methodology differs
from the continuation prompt's transformer claim. A diagnostic accidentally
emitted raw dataset lines; record this in the exposure assessment. Next proposed
task: independent branch-selective Notebook 04 preparation, with synthetic tests.
