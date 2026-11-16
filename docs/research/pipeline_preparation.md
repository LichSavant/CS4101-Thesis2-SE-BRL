# Pipeline preparation and behavioral contract boundary

Technical preparation at repository baseline `6bded57`. This note does not approve
a dataset, alter H1-H12, validate historical performance, or complete the research
pipeline. The two existing reconciliation/decision drafts remain unchanged.

## Read-only preflight

From the checkout root, using the available Python environment:

```powershell
.venv\Scripts\python -B -m ml.preflight --root .
```

`-B` is part of the read-only command: it prevents Python import bytecode writes.
The command emits JSON to stdout only. Exit `2` means blockers were reported;
exit `0` means no blockers were reported, never permission to run research.
There is no output-file, overwrite, download, execution, or training option.
Diagnostics therefore cannot overwrite historical results. Do not redirect stdout
over an existing result. No diagnostic files or output directories are created.

`ml/preflight.py` uses only the standard library. It reports missing files, LFS
pointers versus headers, candidate header compatibility, notebook syntax and
stored-error metadata, population assertions, historical manifest source counts,
allowlisted processed-input SHA-256 matches, installed distribution versions, and
per-stage blockers. Header compatibility is not row validity, verified label
semantics, licensing, source authenticity, or scientific eligibility.

Only fixed historical partition metadata is aggregated. Raw CSV data rows are
not parsed; ARFF inspection stops at `@data`. Processed inputs are hashed as
opaque bytes, never used for analysis. Historical row-level prediction files
are not opened. Recorded filenames cannot redirect checksum reads to arbitrary
files. No Git command, pandas import, notebook execution, or network call is used.

Stage flags concern metadata prerequisites, not experiment authorization. The
current report conservatively retains explicit protocol and contract blockers;
it does not interpret a recommendation or an `Approved` word as authorization.
Absent evidence is reported as unestablished, not silently promoted to ready.

Notebook 03 cell `95feb561` now explicitly stops because no primary email
benchmark is selected. Its historical counts and saved partitions are retained
as historical evidence, not adopted as a replacement. The preflight reports
`primary_email_benchmark_not_selected`. Notebook 04's direct email `urls` access
still needs a source-specific schema decision before integration.

## Offline input contracts

`ml/experiment_inputs.py` defines `EmailDatasetAdapter`, `EmailObservation`,
`DatasetIdentity`, and `DocumentedLabelMapping`, version `0.1.0`.
`MappedEmailAdapter` accepts explicit `EmailFieldMapping` column names for any
source; no dataset, schema, label meaning or language is selected by default.
Callers supply a snapshot identity, provenance reference, documented native-label
mapping, language and unique field mapping. References are caller assertions,
not authenticated approvals. Optional unmapped or missing evidence is unavailable.

The observation preserves the original record ID; its deterministic observation
ID hashes the snapshot/original-ID tuple to avoid separator collisions. Subject
and body are preserved, not translated or silently normalized. `TextField` and
`LinkField` distinguish unavailable (`None`), known-empty (`""`/whitespace or an
explicit empty link tuple), and available evidence. No synthetic `urls=[]` is
inserted when links are unknown. Stringified CSV link lists are rejected rather
than parsed by guesswork; a future documented source decoder is separate work.

This is an in-memory offline contract, not an automatic corpus loader or runtime
bridge. Callers must already have lawful, authorized data access. Constructing a
record does not authorize body collection, link extraction, transport, or logging.
Existing runtime body authorization/study-purpose and URL validation gates remain
mandatory before any future runtime use. No credentials should be supplied.

`validate_population` checks supplied identity, unique original/observation IDs,
explicit target counts and contradictory totals. `validate_supplied_partitions`
checks supplied group/partition/fold isolation without making or repairing groups
or partitions. Neither function establishes campaign/template independence.
`select_predictors` requires an explicit allowlist and rejects native labels,
targets, provenance and bookkeeping (including `Label` and `original_hash`);
additional source-specific label fields must be declared as extra bookkeeping.
It does not choose scientific features or infer predictors from data types.

`gate_english_lexical` is the required language boundary for the **new preparation
path**. Explicit Spanish or unknown-language input returns `unavailable` with no
extractor call and no fabricated absent/support vector. Explicit `en`/`en-*`
permits a caller-supplied evaluator. This is a language assertion, not automatic
language detection or proof that every English artifact is assessable. The old
notebook/runtime extractors remain unchanged; they are not automatically guarded
by this new API. Future callers must use the gate before lexical evaluation.

## Notebook 04 versus runtime ml/: verified gap

Proposal Chapter 4, section 4.3.4 and Tables 4.6-4.7 specify deterministic SE-BRL
support/availability and evidence verification. A learned behavioral predictor
or human annotation is not a new prerequisite introduced by this preparation.
The proposal remains at `Thesis_Proposal_Documents/Alcover & Orbello_Approved
Document Proposal.pdf`; refer to the existing reconciliation for page locators.

| Notebook 04 ID | Canonical runtime ID | Mechanical fact only |
| --- | --- | --- |
| `pressure_threat` | `pressure_threat_cues` | Dimension ID mapping |
| `lure_attention` | `lure_attention_cues` | Dimension ID mapping |
| `trust_identity` | `trust_identity_manipulation` | Dimension ID mapping |
| `requested_action_consequence` | `requested_action_consequence` | Same ID |
| `credential_sensitive_request` | `credential_sensitive_data_request` | Indicator ID mapping |

These mappings can be checked against Notebook 04 cell `73aa8e1c` and
`ml/se_brl/codebook.v0.1.0.json`. Other eleven indicator IDs match. Name mapping
does not prove rule equivalence and is not applied to historical artifacts here.

| Boundary | Notebook 04 | Runtime / pending alignment |
| --- | --- | --- |
| Rules/version | Cell `0f71a795` has notebook-local English word patterns with no exported per-rule version | `ml/se_brl/rules.py` v0.2.0 uses narrower action/consequence patterns; `context.py` suppresses negated, quoted, reported and educational contexts. Rule meaning must be reviewed, not selected from test performance. |
| Evidence | `9813807c` stores normalized matched fragments; `905013fc` exports fragments by observation/indicator | `preprocessing.TextEvidence` and `extraction.IndicatorEvidence` retain original-field character offsets, locators, rule version and provenance. Freeze a source-faithful locator schema before integration. |
| State encoding | `facef21a`: Supported `(1,1)`, Absent `(0,1)`, Unavailable `(0,0)` | Support and availability are deterministic evidence, not calibrated probabilities or phishing risk. |
| Partial availability | `856e7104`: any available indicator can make a dimension assessable; no support then gives Absent | Canonical trust is conditional A*; runtime detector status also distinguishes unevaluated. Whether partial evidence suffices for dimension-level Absent remains H4, not silently resolved here. |
| Identity/structure | `c39fad04` makes impersonation/brand unavailable; `88372fcf` uses supplied binary form fields | Runtime trust detectors require independent typed references. A dataset field is not a newly observed DOM element. Evidence opportunity and modality policies remain pending. |
| E2/E3 | Deterministic support plus availability tables | `representation.BrlRepresentation` retains null learned z slots; `features.ExperimentFeatureBuilder` blocks E2/E3 on missing learned values. This older runtime contract needs a separately approved deterministic alignment. No blocker is removed here. |

Proposed alignment: a versioned deterministic specification, explicit legacy-ID
adapter, reviewed qualifying/exclusion/partial-availability rules, faithful
locators, and synthetic conformance/boundary tests before a new experiment
version. Do not repurpose null learned slots or overwrite the historical LR
features/results. Existing runtime APIs/tests keep their current contracts.

## Verification and remaining work

Run preparation tests without installing scientific/model packages:

```powershell
.venv\Scripts\python -B -m pytest ml/tests/test_experiment_inputs.py ml/tests/test_preflight.py -q -p no:cacheprovider
```

These synthetic tests validate software boundaries, not source-label truth,
language adequacy, grouping science, or historical performance. In-memory
notebook syntax checks never execute cells. Notebook 01 cell `69185334` is
converted to Markdown with its wording preserved; other cells/outputs remain.

Missing payloads/processed inputs and scientific dependencies are separate from
pending H1-H12 decisions. Later work includes an approved source decoder,
language/evidence contract integration, immutable run persistence, selection
settings, four-family experiments and the exposure-aware evaluation plan.
The next milestone is an approved dataset/language/evidence and evaluation
decision record plus a source-specific fixture plan after those decisions.
This phase does not obtain a dataset, create a training run, or validate a model.
