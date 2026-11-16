# UCI scientific acceptance packet - November 1, 2026

Checkpoint/filename date: November 1, 2026. Review completed November 2, 2026
(Asia/Manila). Neither date is a scientific approval or acquisition date.

**Review packet only. No new scientific decision is approved.**

UCI local source/cleaned identities, schema agreement, historical assignment
consistency and the supplied-assignment software path are supported by existing
evidence. The exact source basis for Result class meanings, acquisition/access
record, original-row lineage, accepted grouping/split reuse, audited dictionary
and exposure-aware access authorization are incomplete. Actual-data preparation,
real D9 handoff generation, U1 training and confirmatory evaluation remain blocked.

UCI is the approved **U1-UCI technical benchmark**, not an Email/Web E1-E3 branch.
No replacement dataset, supervised behavioral predictor or human-annotation
requirement is introduced.

## 1. Scope, repository state and evidence rules

Checkout: `<user-profile>/Desktop/Projects/Thesis_Prototype_Git`.
Branch `main`; HEAD `6bded57d38e9b83ba718d7795b97e2130128c23f`;
configured upstream `origin/main`.

- `origin` remains `https://github.com/LichSavant/Thesis_Protoype_Test.git`.
- `se-brl` remains `https://github.com/LichSavant/CS4101-Thesis2-SE-BRL.git`.
- Starting status: 22 unstaged tracked paths, 25 untracked files, none staged.
  Existing LFS materializations and Notebook 01/03/04 edits are pre-existing work.
- A fresh 249-file preservation baseline covers existing tracked/untracked work,
  all experiment/database files, Git index/config and historical artifact hashes.
  Prediction/outcome files were only opaque preservation bytes; no rows or
  performance values were parsed or displayed.
- Git reads used `GIT_OPTIONAL_LOCKS=0`; status disabled LFS filters. No refresh,
  synchronization or Git/configuration mutation. The pre-existing inaccessible
  `.pytest_cache` warning remains.
- This task uses **existing local evidence only**. No internet retrieval, source
  download, package installation, tests, notebook execution, preparation API call,
  feature verification, partition generation or training occurred.
- Only saved on-disk files were reviewed; unsaved editor buffers were not accessed.

**VERIFIED** below describes a checked, bounded fact; **PENDING** is an unresolved
decision/acceptance; **BLOCKED** means a decision or execution gate lacks necessary
evidence/dependencies. A verified fact does not imply approval of its scientific
use. Missing facts cannot be made true by a signature.

The preceding reports record 81 focused, 301 neighboring, 813 complete Python,
25 frontend tests and 275 syntax-valid notebook cells. These are **previous
checkpoint results, not freshly reproduced results here**. Current test source
contains 81 cases by static AST/decorator counting. The UCI module/tests and shared
branch/D9/notebook-contract hashes match the preceding checkpoint. Test source
includes actual synthetic D9-loader round trips; it is not a real-data acceptance
record.

## 2. Governing sources and citation key

### Approved source [P]

[Alcover & Orbello approved proposal](../../Thesis_Proposal_Documents/Alcover%20%26%20Orbello_Approved%20Document%20Proposal.pdf),
SHA-256 `283338c5535c5553e35266f5083a6380e014637e63d42161c659238e257ad1fe`.

Its 155-page PDF was read directly using in-memory text/font-map extraction; no
PDF/text artifact was created. Page references are PDF viewer pages, not execution
counts or extracted-file line numbers. No visual figure/layout review is claimed.

| Paper provision | Governing acceptance requirement |
| --- | --- |
| Section 4.2.1; Tables 4.1-4.2, PDF pp. 58-60 | UCI repository 327, source-reported 11,055 records/30 engineered features; U1-UCI independent of PhiUSIIL. Counts are pre-audit. |
| Sections 4.3.1-4.3.2, PDF p. 63 | Source_snapshot_id, source/DOI/URL, license, access date, immutable source/hash, original filename, schema/class definition; controlled changes and approvals. |
| Section 4.3.3; Table 4.4, PDF pp. 63-65 | Original IDs, reason-coded screening/attrition, canonical duplicate families and reconciled groups before partitioning; technical domain/path relationships where source permits. |
| Section 4.3.4; Tables 4.5-4.6, PDF pp. 66-68 | Supported/Absent/Unavailable separation, modality boundaries, schema/evidence/repeatability checks; deterministic SE-BRL. |
| Section 4.3.5; Table 4.7, PDF pp. 69-70 | Dataset-specific U1 technical feature space; no SE-BRL contribution claim or raw pooling with PhiUSIIL. |
| Sections 4.3.5.2-4.3.5.3; Tables 4.8-4.10 | Four classifier families, development-only grouped comparison, training-local learned transforms, frozen features/settings and efficiency evidence; test cannot select winners. |
| SRS appendix REQ-4.4-8, PDF p. 135 | PhiUSIIL and UCI technical benchmarks remain independent, not one universal raw feature space. |

**Original-source bibliographic locator recovered from existing evidence:**
[P], bibliography PDF p. 101 / manuscript p. 86, lists Mohammad, R., &
McCluskey, L. (2012), *Phishing websites* [Data set], UCI Machine Learning
Repository, [DOI 10.24432/C51W2X](https://doi.org/10.24432/C51W2X).
This is a **proposal-listed citation**, not a freshly retrieved source page or
proof of the local acquisition date/license/Result mapping. The external source
was not accessed in this existing-evidence-only task.

### Repository evidence key

| Key | Existing path / location |
| --- | --- |
| [N01] | `experiments/notebooks/01_data_audit.ipynb`; cells 6 `31080e7c` (raw selection), 43 `b2406143` (label assertions), 57 `c18f9b33` (inventory) |
| [N02] | `experiments/notebooks/02_data_cleaning.ipynb`; cells 16 `be8e3d45`, 18 `f7e58383`, 30 `97f997c2`, 46 `dce0b430` |
| [N03] | `experiments/notebooks/03_preprocessing.ipynb`; cells 88 `d6e0ca92` (IDs/targets), 90 `989a40c0` / 91 `eb5cf346` (vector grouping), 96 `be257cb1` / 105 `a830d120` (allocation), 145 `bd73bb48` (manifest schema) |
| [N04] | `experiments/notebooks/04_feature_extraction.ipynb`; cell 14 `ef42ccf9` and `ml/branch_preparation.py:53-76` (full read then development filter) |
| [N05H] | Historical `experiments/notebooks/05_experiments.ipynb`; cell 26 `07ce0ca0` (holdout evaluation/writers); later cells 28/29/39 (comparisons/plots/errors) |
| [N05D] | `experiments/notebooks/05_development_preparation.ipynb`; `d9-required-config` still has None protocol/dictionary/features |
| [API] | `ml/uci_preparation.py:45-138`, supplied-assignment preparation |
| [D9] | `ml/development_experiments.py:37-63,107-177,207-301`, specification/build/folds/fixed loader |
| [Contracts] | `ml/notebook_contracts.py:19-25,81-183,216-228`; `ml/experiment_inputs.py:259-315` |
| [Tests] | `ml/tests/test_uci_preparation.py:55-354`; prior results in `docs/research/2026-11-01_uci_supplied_assignment_preparation.md` |
| [Decisions] | `docs/research/experiment_protocol_decisions.md`, especially H3/H5/H11; all twelve resolutions remain Pending |
| [Exposure] | `docs/research/2026-11-01_controlled_d9_continuation.md`, Diagnostic exposure incident |
| [Audit] | `experiments/results/audits/dataset_inventory.csv:7`, `verified_label_semantics.csv:4-5`, `uci_native_value_audit.csv`, `missing_values.csv`, `exact_duplicates.csv` |
| [Cleaning] | `experiments/results/cleaning/cleaning_log.csv:2,11,21` and `validation_results.csv` |
| [Assignment] | `experiments/results/preprocessing/partitions/uci_partition_manifest.csv` |
| [History] | `experiments/results/experiments/experiment_manifest.json` and `input_manifest.csv:8-9` |

Notebook indices here are **zero-based JSON positions with stable cell IDs**.
The older decision register uses one-based numbering; its historical descriptions
are not silently treated as current source. Code/record assertions and research
recommendations are distinguished throughout.

## 3. Acceptance evidence matrix

| Area / requirement | Evidence directly supported | Missing evidence / limitation | Scientific disposition |
| --- | --- | --- | --- |
| A: Original source identification | [P] identifies repository 327 and supplies a DOI citation; [N01]/[N02] explicitly select Training Dataset.arff | No locally retained acquisition receipt/source-page snapshot establishing actual download/access date and license | PENDING, UCI-S01 |
| A: Local archive/raw identity | Selected raw hash matches [Audit], HEAD LFS OID/size and ZIP member bytes | Byte equality is not independent source authenticity | VERIFIED local identity; acceptance PENDING |
| A: Clean identity | Clean CSV matches HEAD LFS OID/size and raw attribute names/order | No source-to-derived manifest binds raw/clean/code/row correspondence | VERIFIED bytes/schema; lineage BLOCKED |
| B: Label codes | ARFF declares Result {-1,1}; code and saved audit agree on the stated mapping | Exact authoritative Result class-meaning passage not found locally; feature-rule meanings cannot establish the target definition | Acceptance PENDING; target-dependent execution blocked, UCI-S02 |
| C: Recorded transformations | [N02]/[Cleaning] document full duplicate removal, reset index, byte-to-integer conversion | No raw canonical-row map, reason-coded retained IDs or reproduced raw-to-clean join | BLOCKED, UCI-S03 |
| C: Stable observations | [N03] creates UCI::cleaned-position IDs; [Assignment] IDs unique and contiguous | IDs are not original raw IDs; row reordering/recleaning can change identity; independent full expected-ID provenance absent | VERIFIED historical IDs; acceptance BLOCKED |
| D: Supplied grouping | [Assignment] has 5,785 groups and 64 mixed-target groups; [N03] defines predictor-vector hashing | Actual predictor-to-hash-to-group relation not reproduced; no URL/domain/campaign identities; no group-scope acceptance found | PENDING, UCI-S04 |
| D: Partitions/folds | Fresh metadata aggregation establishes exact membership counts, five folds and zero supplied group crossings | Metadata consistency does not approve reuse or prove broader independence/custody | VERIFIED internally; reuse BLOCKED, UCI-S05 |
| E: Engineered schema | Raw header, clean header and [History]'s ordered 30-feature list agree | No current audited dictionary with accepted meanings/domains/encoding/null/exclusion policy, version/hash and review record | PENDING, UCI-S06 |
| E: Native codes and unavailable evidence | Source domains include valid -1/0 where declared; current U1 dispatcher keeps behavioral states unavailable; D9 omits behavioral predictors from U1 | Actual-row/domain conformance has not been checked; API finite-numeric validation is not per-feature domain validation | VERIFIED software/schema facts; actual acceptance PENDING |
| F: Development boundary | [API] accepts supplied development records and complete metadata, checks exact IDs/joins, exports only development; no input-file loader | Cannot authenticate upstream reader/custodian or prove delivered records were never exposed elsewhere | PENDING access scope, UCI-S07 |
| F: Historical exposure | [N05H]/[History]/existing reports document historical holdout evaluation; [Exposure] records a raw diagnostic incident | Earlier human access/influence and incident-specific partition membership are unknown | Untouched-test claim unsupported; PENDING, UCI-S08 |
| Reproducible D9 compatibility | [API] calls existing builder/fold validation and fixed exclusive exporter; [Tests] exercise actual synthetic D9 loading | Current real handoff/input pair and accepted source/dictionary/access packet absent | VERIFIED code/prior synthetic evidence; real execution BLOCKED, UCI-S09 |
| Model-selection controls | [P] fixes families and hierarchy; [Decisions] records remaining settings | No accepted current UCI candidate-search/selection/calibration/benchmark bundle found | PENDING before comparative fits, UCI-S10 |

No row above approves a new policy. Missing evidence may have an owner, but is not
assumed to exist outside this checkout.

## 4. A-C: Source, labels and raw-to-clean lineage

### Fingerprints and authority

| Existing artifact | Fresh SHA-256 |
| --- | --- |
| `experiments/datasets-raw/webpage/uci/phishing+websites.zip` | `514f582cb44cba17251baf1d59f64cddff16efa2b644d091ce8d2a1e8d492940` |
| `experiments/datasets-raw/webpage/uci/phishing+websites/Training Dataset.arff` | `3bcf93b1612306537ee2737751f1bac185b2a77886ab376644c3bf0c7f7cb3e6` |
| `experiments/data/interim/webpage/uci_phishing_websites_clean.csv` | `5bdf3b3429f31b4c31d137f3872eede81fe45f9473ad033afb425dd50e62ba92` |
| `experiments/datasets-raw/webpage/uci/phishing+websites/.old.arff` | `18841a0b7f3bd1e63e2897dca7ae7e75c6ed9ebcc1d9925cbbb3964754c19b51` |
| `experiments/datasets-raw/webpage/uci/phishing+websites/Phishing Websites Features.docx` | `f6f9326f45659a7b5ef947fa744cec2c379dbea17de56d34436312407faca43c` |
| [Assignment] | `371c0b29d19772c0061db824aff2c77ec5e9bf126568b2e63ce7e755845aa84f` |

The four LFS payloads match tracked HEAD OIDs and declared sizes. The ZIP contains
exactly Training Dataset.arff, .old.arff and the feature DOCX; each member matches
the corresponding local file. There is no license/acquisition record among those
three members. Training Dataset.arff is selected by code and the saved inventory,
not merely because it exists. The alternate .old.arff has different domains and
is not selected; its relation name test is not an SE-BRL partition declaration.

**Missing source fields:** actual acquisition/access date, source_snapshot_id,
retained source/license/access evidence and a precise class-definition reference.
The proposal bibliography establishes an intended locator, not those facts.
Git commits, ZIP/DOCX timestamps and LFS materialization dates must not be
substituted for acquisition dates. No source field is backfilled by assumption.

### Exact label basis: not established

| Native Result | Existing repository interpretation | Existing standardized target |
| --- | --- | --- |
| -1 | phishing / phishy | 1 |
| 1 | legitimate | 0 |

Evidence: [N01] cell 43 hardcodes its "verified from source documentation" text;
`verified_label_semantics.csv:4-5` exports those assertions; [N03] cell 88 and
`ml/notebook_contracts.py:23-25` implement the mapping. These sources agree
internally but are not independent citations to the original target definition.

The complete raw ARFF header has relation phishing and attribute declarations,
including Result {-1,1}; it has no class-meaning comment establishing which value
means phishing. The local feature DOCX was inspected through ordinary text and
151 readable Office Math text nodes across 176 paragraphs; no exact
target-Result class definition was established. Feature equations describing
phishing/legitimate conditions are not a target-label codebook.

[P] Table 4.1 defers UCI class semantics to the audited repository definition; it
does not independently state the numeric mapping. The proposal-listed DOI's
source content is not retained here with an exact supporting passage. Therefore
**scientific acceptance of the mapping remains PENDING**, with target-dependent
execution blocked by missing evidence, not
approved and not reversed. Class proportions or historical metrics cannot resolve
orientation. Current source code and historical labels remain unchanged.

### Lineage: recorded recipe, not record-level proof

[Cleaning] records 11,055 -> 5,849 after removal of 5,206 complete duplicates.
[N02] removes full-row duplicates, retains predictor-identical rows with different
labels, resets the index, converts nominal byte codes to integers and writes
31 native columns. Its conversion is intended to preserve -1/0/1 values; no
statistical imputation/scaling is part of that recipe.

However:

- No raw-row -> retained canonical-row -> cleaned-position table was found.
- No complete original-ID screening/exclusion/duplicate-family artifact or
  independently accepted full ID population was found.
- The equality 11,055 - 5,206 = 5,849 is a consistent historical aggregate, not a
  proof that specific present rows underwent those operations.
- No numeric raw/clean observation rows were parsed or transformations rerun in
  this task, so actual per-row feature-code preservation is not newly verified.
- [N03] assigns source_row_id only after cleaning and observation_id=UCI::position.
  These are cleaned-file locators, not recovered original identifiers.
  Stability requires binding the clean hash, row order and lineage. The current
  API preserves supplied IDs; it cannot reconstruct or authenticate them.

Historical experiment input hashes are recorded in [History]:
preprocessed `e5558bced50e80b3133ea3c60ac7f062c5c02fa0bb3ce9df24d5ddba557bfadf`;
behavioral `c7f039c60910d2d026692305aed238a127839cfd8e37d9f92445a0452714a1c4`.
Those input files are absent. The saved raw audit matches today's raw hash,
but the complete raw -> clean -> historical experiment chain cannot be proven.
No historical-result equivalence is inferred.

## 5. D: Grouping and supplied assignments

Fresh read-only aggregation of the six metadata columns gives:

| Partition | Observations | target 0 | target 1 |
| --- | ---: | ---: | ---: |
| development | 4,094 | 1,969 | 2,125 |
| calibration | 878 | 420 | 458 |
| test | 877 | 441 | 436 |
| Total | 5,849 | 2,830 | 3,019 |

| Development fold | Observations | target 0 | target 1 |
| --- | ---: | ---: | ---: |
| 1 | 820 | 382 | 438 |
| 2 | 820 | 371 | 449 |
| 3 | 817 | 423 | 394 |
| 4 | 818 | 407 | 411 |
| 5 | 819 | 386 | 433 |

Verified: 5,849 unique IDs spanning UCI::0 through UCI::5848; one expected
source name; 5,785 distinct supplied groups; 64 mixed-target groups; zero supplied
group crossings between partitions or development folds; both target codes in
each partition/fold; no reserved fold values. Lossless 1.0-style development folds
are compatible with the existing decoder. Target codes are reported without
promoting their unverified semantic citation to approval.

[N03] hashes the ordered complete predictor vector excluding Result and listed
metadata, then maps sorted hashes to ordinal group IDs. It does not use raw
URL/domain/campaign/template identity because those fields are absent from this
schema. Group labels can change with altered population/order/serialization.
The metadata manifest lacks feature hashes, native Result, raw locators and source
snapshot linkage. Its correspondence to the actual predictor-hash recipe has not
been reproduced here.

Scientifically defensible statements are limited to **recorded group isolation**.
No domain/campaign independence, complete near-duplicate control or accepted
split freeze follows automatically. The proposal permits source-dependent
technical relationships where observable; neither inventing URLs nor importing
Email MinHash defaults is justified for UCI.

The old assignment file remains immutable. Acceptance for a new run requires
source/lineage/group/exposure review. Declining reuse is distinct from silently
rewriting it. No assignment, group, partition or fold was regenerated.

## 6. E: Candidate feature dictionary and U1 semantics

The raw ARFF header, clean CSV header and [History]'s 30-predictor list agree
exactly in name and order. The following is **verified source schema**, not an
accepted new scientific dictionary. All raw attributes are nominal codes; the
cleaning recipe represents them as integers. Per-field meanings, model encoding,
null/eligibility policy, exclusions, dictionary version/hash and approval remain
Pending.

| Order | Source feature name | Declared native domain |
| ---: | --- | --- |
| 1 | having_IP_Address | {-1,1} |
| 2 | URL_Length | {-1,0,1} |
| 3 | Shortining_Service | {-1,1} |
| 4 | having_At_Symbol | {-1,1} |
| 5 | double_slash_redirecting | {-1,1} |
| 6 | Prefix_Suffix | {-1,1} |
| 7 | having_Sub_Domain | {-1,0,1} |
| 8 | SSLfinal_State | {-1,0,1} |
| 9 | Domain_registeration_length | {-1,1} |
| 10 | Favicon | {-1,1} |
| 11 | port | {-1,1} |
| 12 | HTTPS_token | {-1,1} |
| 13 | Request_URL | {-1,1} |
| 14 | URL_of_Anchor | {-1,0,1} |
| 15 | Links_in_tags | {-1,0,1} |
| 16 | SFH | {-1,0,1} |
| 17 | Submitting_to_email | {-1,1} |
| 18 | Abnormal_URL | {-1,1} |
| 19 | Redirect | {0,1} |
| 20 | on_mouseover | {-1,1} |
| 21 | RightClick | {-1,1} |
| 22 | popUpWidnow | {-1,1} |
| 23 | Iframe | {-1,1} |
| 24 | age_of_domain | {-1,1} |
| 25 | DNSRecord | {-1,1} |
| 26 | web_traffic | {-1,0,1} |
| 27 | Page_Rank | {-1,1} |
| 28 | Google_Index | {-1,1} |
| 29 | Links_pointing_to_page | {-1,0,1} |
| 30 | Statistical_report | {-1,1} |

Result {-1,1} is the target source field, never predictor 31. Preserve spellings.
-1 and 0 are native values **where that feature's domain permits**; zero is not a
universal valid value or missing sentinel. No feature is removed or recoded here.

[D9] requires explicit FeatureColumn entries and nonempty references, not dtype
discovery. It does not resolve/authenticate a scientific dictionary. [API] rejects
missing/extra payload fields, labels/bookkeeping/behavioral predictors and
nonnumeric/nonfinite values; it permits None as an explicit missing value. It
does not enforce each ARFF domain or decide which missing rows are eligible.
Those scientific requirements must be documented before actual ingestion.
The generic `ml/feature_schema.py` E1/E2/E3 version mechanism is not a completed
UCI dictionary or an alternative U1 handoff contract.

Current U1 behavior:

- All twelve behavioral indicators remain unsupported/unavailable; audit evidence
  is empty with availability false.
- All four dimension states are Unavailable. Compact support=0 and availability=0
  encode Unavailable; Absent would require availability=1.
- D9's U1 predictor tuple includes only declared conventional features, not the
  eight behavioral contract slots. Technical indicators do not substitute for
  missing behavioral evidence.
- No missing urls=[], Email content, identity or language evidence is fabricated.
- Historic summaries use legacy dimension names and report unavailable for all
  5,849 UCI observations. They are historical aggregates, not current canonical
  per-record features.
- Historical UCI experiments use the name E1 for their conventional run. Keep
  that history unchanged; new UCI scope remains U1-UCI under [P] Table 4.7.

## 7. F: Current access boundary and exposure truthfulness

[API] is an in-memory function, not a CSV loader or access-control sandbox.
It requires:

1. Decoded development records with the existing source/native/assignment fields.
2. Exactly the existing six-column full-population assignment metadata.
3. A full expected ID frozenset from an independent accepted population record.
4. Existing DevelopmentSpecification for UCI with explicit numeric features and
   actual protocol/dictionary references, plus an unused run ID.

It validates exact development IDs and manifest joins without generating missing
assignments. Full metadata includes reserved role/group/target/fold information,
but reserved predictor payloads are not required or accepted for export.

**Boundary limitation:** the function materializes caller-provided iterables
before validating them. Rejection of reserved records does not establish that
the caller never read/delivered them. Path guards and synthetic tests show no
input dataset-file discovery/read by this API; they do not authenticate upstream
delivery, provenance or authorization. A trusted, approved development-only
delivery/decoding procedure is still needed.

[N04]'s older loader reads full selected preprocessed data before filtering.
[N03] still globally loads other branches and allocates splits. Neither is a
development-only source-access procedure to run wholesale. [D9] reads fixed named
development exports and rejects reserved rows, but filenames/reference strings
also cannot prove custody upstream.

Only three exclusive outputs are allowed by [API], under an unused run:

- `data/processed/features/development/uci_development.csv`.
- `data/processed/features/sebrl/uci_sebrl_features.csv`.
- `data/processed/features/development/development_input_manifest.json`.

The existing exporter checks collisions and exact-byte hashes, writes manifest
last and rolls back ordinary IO failures. No such real outputs exist here;
`experiments/runs/` is absent. Process termination is not an atomic transaction.

### Exposure record and claims

[History] identifies historical LR and UCI conventional evaluation. [N05H] cell
26 evaluates test and writes holdout artifacts; UCI-named plots and prior audit
reports document historical UCI evaluation. No prediction/outcome row or plot
performance was inspected for this packet.

[Exposure] separately records an unscoped diagnostic that emitted raw dataset
lines. Its record says affected partition membership was not examined. Do not
claim that specific UCI sealed rows were necessarily in those diagnostics, or
that no reserved material was exposed. Historical UCI holdout use is documented
independently of that uncertainty.

| Truthful supported statement | Unsupported stronger claim |
| --- | --- |
| Supplied groups do not cross recorded partitions/folds | Domain/campaign or complete duplicate independence |
| The new API validates development-only output and fits nothing | Proof the caller never accessed reserved predictors |
| Historical holdout evaluation is documented | An untouched historical holdout for newly chosen candidates |
| Current code/test sources match the preceding checkpoint | Fresh test reproduction or actual-data conformance in this task |
| No outcomes were used for decisions in this packet | Proof no earlier human post-test tuning/influence occurred |

No automatic resealing, new-seed reshuffle, retroactive pre-access freeze or
confirmatory claim is supported. The existing H3 decision remains Pending.
No independently unexposed evaluation source/pool is assumed to exist.

## 8. Decision register for researcher/adviser review

These are UCI-specific questions mapped to existing H decisions, not replacements
for that register. Recommendations remain unchosen. Authority descriptions follow
the existing draft's distinction between evidence verification, implementation
details and scientific claim/deviation decisions; no institutional delegation or
signature is invented. An approval must identify option/settings, evidence,
versions/hashes, decision-maker role, date, rationale and permitted scope.

### UCI-S01 - Source snapshot/acquisition acceptance

1. **Question:** Is the pinned local archive/raw/clean source sufficiently
   documented for the approved U1 source/access requirements, and which retained
   acquisition/license records establish it?
2. **Evidence:** [P] source/DOI locator; matching local/LFS/archive/inventory bytes;
   missing access date, source_snapshot_id and retained license/access proof.
3. **Options:** Recover and bind existing custodian records; or defer source
   acceptance while facts remain unavailable. Treat a genuinely unavailable
   required field through the formal research-deviation process, never backdating.
4. **Recommendation:** Recover existing evidence and keep acceptance pending;
   hash equality alone cannot prove provenance/access.
5. **Authority:** Source custodian/Vera provides facts; researchers verify;
   adviser/joint authority for any required-method deviation.
6. **Consequences:** Populate a versioned source record before actual ingestion;
   no dataset changes/download or historical hash replacement.
7. **Links:** H5/H11; [P] Section 4.3.2/Table 4.4.
8. **Status:** PENDING.

### UCI-S02 - Exact Result class definition

1. **Question:** What retained authoritative passage explicitly establishes
   Result -1=phishing and Result 1=legitimate for this pinned release?
2. **Evidence:** Consistent code/CSV assertions and ARFF categories; no exact
   supporting target-definition passage found in retained documentation.
3. **Options:** Supply the original definition tied to this version; or defer
   target-dependent research when it cannot be established. Any discovered
   contradiction requires a separately versioned correction/review, not guessing.
4. **Recommendation:** Obtain the exact source citation before accepting the
   mapping; retain current code/history without claiming scientific acceptance.
5. **Authority:** Source custodian supplies documentation; researchers verify;
   adviser/joint review if meaning or approved claims must change.
6. **Consequences:** Record accepted label mapping/version or explicit unresolved
   status; do not invert labels from counts or model outcomes.
7. **Links:** H5/H11; [P] Table 4.4.
8. **Status:** PENDING authoritative evidence; target-dependent execution blocked.

### UCI-S03 - Raw-to-clean lineage and eligibility evidence

1. **Question:** Which raw records/canonical duplicate families produced each
   retained cleaned position, and what complete exclusion/transform log proves it?
2. **Evidence:** [N02]/[Cleaning] recipe and counts; no original-ID correspondence
   or completed reason-coded retained-population record.
3. **Options:** Recover existing row/duplicate logs; separately authorize a bounded
   custodian-led lineage reconciliation if needed; or defer claims requiring
   irrecoverable identity. This task performs none of that row-level work.
4. **Recommendation:** Recover existing records first; if absent, specify the
   narrow reconciliation/access scope before any protected-data inspection.
   Aggregate counts do not establish identity.
5. **Authority:** Dhanwil handles technical reconciliation; custodian provides
   provenance; researchers/adviser approve eligibility-policy changes/limitations.
6. **Consequences:** Bind raw and clean hashes, canonical original IDs, retained
   order, reasons and expected full ID set. Never generate replacement IDs to
   make an old manifest appear aligned.
7. **Links:** H5/H11; [P] Section 4.3.3/Table 4.4.
8. **Status:** BLOCKED on lineage/acceptance evidence.

### UCI-S04 - Permitted grouping scope

1. **Question:** Is predictor-vector-only grouping acceptable for this independent
   technical benchmark, with domain/campaign/template identity unavailable?
2. **Evidence:** [N03] vector hash recipe, absent identity fields, 5,785 recorded
   groups/64 mixed-target groups; no broader relationship audit/acceptance.
3. **Options:** Accept narrowly documented exact-vector controls where the source
   permits; reconcile additional relationships only if real evidence is supplied;
   or exclude/defer claims requiring unsupported independence.
4. **Recommendation:** Consider the narrow U1 limitation, preserving conflicting
   pairs; do not invent identity or adopt unrelated MinHash parameters. This
   recommendation is not acceptance of existing group-to-record correctness.
5. **Authority:** Researchers document source-permitted controls; adviser/joint
   approval for changed eligibility or scientific claim scope.
6. **Consequences:** Freeze accepted relationship scope/version and check supplied
   record-to-group correspondence after authorized lineage work. No group IDs
   or relationships are regenerated by this packet.
7. **Links:** H5; [P] Section 4.3.3/Table 4.4.
8. **Status:** PENDING.

### UCI-S05 - Historical split/fold reuse

1. **Question:** May this exact historical manifest be reused for a new
   development-only technical run after lineage, group and exposure review?
2. **Evidence:** Internally consistent metadata and hash; no accepted source-bound
   group/split freeze, and historical holdout exposure.
3. **Options:** Preserve/reuse the exact accepted assignments if prerequisites
   reconcile; or decline reuse/defer execution if they do not. Neither option
   permits editing the old file or calling a reshuffle an untouched test.
4. **Recommendation:** Keep reuse conditional on UCI-S03/S04/S08. Integrity checks
   are necessary, not sufficient.
5. **Authority:** Joint researchers; adviser where protocol/evaluation claims
   require approval; Dhanwil verifies mechanical membership.
6. **Consequences:** Pin the old manifest hash, keep exact role/fold membership,
   and use a separate run namespace only after acceptance. Any incompatible
   scientific change needs its own decision/version, not silent repair.
7. **Links:** H3/H5; [P] Figures 4.1-4.2 and Table 4.4.
8. **Status:** BLOCKED on prerequisites.

### UCI-S06 - Audited dictionary and preparation representation

1. **Question:** Which exact ordered technical fields/domains, missingness/
   eligibility rules, representation and exclusions form the UCI dictionary?
2. **Evidence:** Thirty matching names and source domains; feature DOCX; historical
   list; current numeric D9 interface, but no accepted scientific dictionary.
3. **Options:** Review all thirty source fields with native codes preserved;
   or justify a predeclared source-backed subset/encoding policy. Do not choose
   features from historical test outcomes or assume finite-numeric checks prove
   nominal-domain membership.
4. **Recommendation:** Review the complete source schema first, preserve codes at
   preparation, and explicitly freeze null/domain/exclusion policy and later
   training-local encoding before relevant research use. Do not assign a final
   version/approval merely because this table is printed.
5. **Authority:** Dhanwil prepares technical dictionary; researchers freeze it;
   adviser/joint review for feature eligibility/representation scope changes.
6. **Consequences:** Populate actual FeatureColumn/configuration references and
   source-domain acceptance checks as separately authorized work; no zero fill
   or behavioral substitution.
7. **Links:** H11 and relevant H8/H9 encoding controls; [P] Tables 4.2/4.7.
8. **Status:** PENDING.

### UCI-S07 - Development delivery, reader and access scope

1. **Question:** Who may supply/decode which payloads, and what accepted independent
   population record supplies the API's expected ID set?
2. **Evidence:** In-memory development API, complete metadata schema and synthetic
   no-input-file guards; no authenticated real delivery/custody record or decoder.
3. **Options:** Approved custodian supplies development-only payload plus complete
   metadata/lineage IDs; or separately scope a broader technical audit under an
   exposure policy. The latter is not permission to feed reserved payloads to
   the current API or run combined notebooks.
4. **Recommendation:** Prefer the restricted delivery boundary, Pending approval.
   Validate delivery hashes/lineage before passing records; code cannot unread
   data obtained upstream.
5. **Authority:** Researchers/custodian define access; adviser for policy/claim
   deviations; Dhanwil implements the specified reader/guards.
6. **Consequences:** Record exact allowed files/roles/hashes, custodian, decoder
   contract, logging/output limits and independent IDs. Do not infer authorization
   from filenames/reference strings.
7. **Links:** H3/H11; [P] Sections 4.3.2/4.3.5.
8. **Status:** PENDING.

### UCI-S08 - Historical exposure and permissible evaluation claims

1. **Question:** Which future development/evaluation claims remain defensible after
   historical UCI holdout use and the documented diagnostic exposure uncertainty?
2. **Evidence:** [N05H]/[History]/[Exposure]; unknown prior human influence and
   incident-specific partition membership; no established unexposed pool.
3. **Options:** Approve bounded development/exploratory use with explicit historical
   limitations; defer confirmatory claims; or separately specify a genuinely
   independent prospective evaluation if later authorized and evidenced. No new
   source is selected or assumed obtained here.
4. **Recommendation:** Consider bounded development use plus deferral of untouched-
   test/confirmatory claims until evidence supports them. A new seed or software
   access gate does not restore the old seal.
5. **Authority:** Joint researchers/adviser for exposure response and claim scope;
   technical custody mechanics implement that decision.
6. **Consequences:** Version an exposure/claim/access record before new research
   comparison; preserve historical results, and forbid their use to tune/select.
   Ordinary pre-access freeze assurances cannot be supplied retroactively.
7. **Links:** H3; [P] Sections 4.3.1/4.3.5-4.3.8.
8. **Status:** PENDING.

### UCI-S09 - Actual-data preparation/handoff authorization

1. **Question:** After the above evidence is accepted, is one named no-fit UCI
   development preparation and D9 verification run authorized, with what inputs
   and three exclusive outputs?
2. **Evidence:** Implemented API and prior synthetic round trips; required real
   records/references/acceptances not present; this task authorizes documentation.
3. **Options:** Defer actual execution now; after prerequisites, issue bounded
   authorization for specified no-fit inputs/outputs. No blanket model/training/
   sealed-test authorization follows.
4. **Recommendation:** Defer now. Reassess only against completed evidence and
   an explicit execution instruction, not packet creation or API success.
5. **Authority:** User/research execution owner within accepted institutional
   authority; adviser/joint review for unresolved methodological deviations.
6. **Consequences:** If later authorized, use unused run ID, exact accepted IDs/
   assignments/dictionary, D9 hash checks, preservation baseline and zero fits.
   Current file paths stay absent; no real bundle is created.
7. **Links:** UCI-S01-S08; H5/H11.
8. **Status:** BLOCKED.

### UCI-S10 - U1 model-selection settings, later gate

1. **Question:** Which frozen UCI-only search, metrics/calibration, practical-
   equivalence and efficiency configuration will govern comparative fits?
2. **Evidence:** [P] four families/Table 4.8 ranges/Table 4.9 hierarchy;
   existing H6-H10 settings remain Pending, not approved by old LR results.
3. **Options:** Freeze a complete U1-specific protocol within approved requirements
   before comparative research fits; or defer model experiments while continuing
   independent software/documentation work.
4. **Recommendation:** Defer research fits pending the versioned protocol. Do not
   invent SRS limits, equivalence tolerances or benchmark parameters.
5. **Authority:** Researchers for documented implementation settings; adviser/
   requirements owner for scientific tolerances, changed policies and SRS limits.
6. **Consequences:** Later implement/run approved candidate comparison separately.
   This gate does not demand every H item before metadata review/no-fit repairs.
7. **Links:** H6-H10; [P] Sections 4.3.5.1-4.3.5.4.
8. **Status:** PENDING; pre-comparison gate, not a new requirement to this packet.

## 9. Explicit review/approval checklist

Completed factual checks, **not scientific sign-offs**:

- [x] Selected raw/archive/clean identities and source-schema correspondence checked.
- [x] Historical six-column assignments aggregated without predictors/outcomes.
- [x] Current API/D9 contracts and synthetic round-trip test source inspected.
- [x] Prior test counts identified as prior, not rerun.
- [x] Existing H1-H12 decisions remain Pending; known exposure documented.

Unresolved acceptance/authorization items; none checked or signed by this packet:

- [ ] UCI-S01: acquisition/source/access/license record and actual source_snapshot_id.
- [ ] UCI-S02: exact authoritative Result meaning citation tied to this snapshot.
- [ ] UCI-S03: raw/canonical/clean ID correspondence, reasons and reconciled attrition.
- [ ] UCI-S04: accepted source-permitted grouping scope and its limitations.
- [ ] UCI-S05: accepted exact manifest/hash reuse after record/group/exposure review.
- [ ] UCI-S06: reviewed dictionary with field meanings/domains, representation,
      null/eligibility/exclusion policy, order, version/hash and permitted use.
- [ ] UCI-S07: approved development delivery/decoding/custodian scope and independent IDs.
- [ ] UCI-S08: dated exposure/custody/claim decision, with no resealing assertion.
- [ ] UCI-S09: explicit named real no-fit execution authorization after prerequisites.
- [ ] UCI-S10: later candidate-comparison protocol/settings before comparative fits;
      not a blanket prerequisite for unrelated no-fit technical work.

For each eventual decision record, supply **chosen option and exact settings;
approver identity/role and authority/delegation; date; rationale; evidence path/
passage; source/manifest/dictionary/protocol hashes and versions; dependencies;
permitted inputs/outputs/claim scope; acceptance checks**. Leave unknown fields
unknown; do not backdate, infer a signature, or turn "reviewed" into "approved."

Factual acquisition/label/lineage evidence is first supplied by its owner, not
invented by Dhanwil or approved into existence. Researcher/adviser governance is
needed for scientific acceptance/limitations and policy deviations. Merely
preserving existing schemas/writers is an implementation detail already completed.

## 10. Readiness and D1-D16 position

| Activity | Software/evidence capability | Research authorization/readiness |
| --- | --- | --- |
| Read-only metadata verification | Available; bounded checks performed here | Within this task; does not permit raw-row transformation/feature execution |
| Synthetic preparation | Implemented; prior 81 focused/813 total Python results; current source unchanged | Established software scope; not executed again in this documentation task |
| Actual-data development preparation | In-memory consumer exists; source delivery/acceptance incomplete | BLOCKED, UCI-S01-S09 |
| D9 handoff generation | Synthetic round trip implemented/tested; fixed three-file output | Real handoff BLOCKED; none created |
| E1-E3 training on UCI | Not applicable under Table 4.7 | UCI is U1; Email/Web readiness not established by this packet |
| U1-UCI training/comparison | Family names/contracts exist; no research training performed here | BLOCKED on accepted data and UCI-S10 settings/authorization |
| Sealed-test evaluation | Historical evaluation already documented; no established fresh seal | BLOCKED; no untouched-test claim or evaluation unlock |

Updated assigned checklist:

| Task | Position |
| --- | --- |
| D1 | IN PROGRESS: approved U1 role clear; UCI-specific acceptances/settings unresolved |
| D2 | IN PROGRESS: existing repairs/API preserved; no real preprocessing verification |
| D3 | PARTIAL: identity/schema/metadata facts verified; original-row/label/source eligibility evidence incomplete |
| D4 | BLOCKED for research use: supplied isolation verified, scientific grouping/split/custody/exposure acceptance pending |
| D5 | IN PROGRESS: canonical indicators preserved; no behavioral freeze inferred |
| D6 | PARTIAL: software alignment/unavailable semantics supported; no actual-data feature conformance |
| D7 | IN PROGRESS: exclusion/isolation safeguards; scientific leakage/group evidence incomplete |
| D8 | COMPLETE in prior software-check scope: no fresh test claim in this task |
| D9 | PARTIAL: synthetic compatible handoff exists as capability; accepted real inputs/bundle absent |
| D10 | BLOCKED: no actual candidate training/comparison authorization/evidence |
| D11 | BLOCKED/not implemented: no transformer prerequisite introduced under deterministic methodology |
| D12 | BLOCKED: no new final metrics/calibration/evaluation |
| D13 | BLOCKED: no new research CV/ablation |
| D14 | IN PROGRESS: source hashes/write-once contracts; accepted research bundle incomplete |
| D15 | IN PROGRESS: this packet documents evidence, limitations and pending decisions |
| D16 | BLOCKED: no final research freeze/release/handoff |

**Exactly one recommended next task:** resolve **UCI-S02's evidence request** with
Vera/the source custodian: obtain the retained authoritative passage defining the
Result classes for this release and bind its citation to the pinned source.
If no such retained evidence is available, explicitly record that fact, keep
acceptance Pending and target-dependent execution blocked. Do not change labels,
acquire a replacement dataset or run
preparation as part of that narrow task.

## 11. Preservation and stop record

Only `docs/research/2026-11-01_uci_scientific_acceptance_packet.md` is added.
The final checksum comparison verified all 249 prior files unchanged, including code,
tests, notebooks, datasets, assignments, results, research decisions, database and
Git index/config, with no removals. Verified final Git status: 22 unstaged tracked paths, 26
untracked files, none staged; main/HEAD/upstream/remotes unchanged.

No tests, notebooks, model/preprocessing fits, real preparation, partition/group/
fold generation, handoff creation, raw-row reconciliation, historical outcome
inspection, installation, download, commit, push or Git repair occurred.
Raw/clean bodies were used only for opaque fingerprints; ARFF/CSV inspection
stopped at headers. ZIP comparisons were in-memory byte hashes, not extraction
to new files. Only existing UCI assignment metadata and saved aggregate audits
were parsed. Document/table/whitespace checks concern this report alone.

Context for ChatGPT: New packet separates verified UCI bytes/schema/internal
assignment consistency and existing synthetic API capability from scientific
acceptance. Source DOI is present in proposal bibliography, but exact Result
class-meaning passage is absent from retained evidence. UCI-S01-S10 are
Pending/Blocked; no new approval. IDs lack raw-to-clean lineage, grouping is
vector-only, real dictionary/delivery/custody and exposure-aware claims remain
unaccepted. E1-E3 are not applicable to UCI; U1 training and real handoffs remain
blocked. Next task is the single UCI-S02 source-evidence request. Only this
packet was added; no experiments or data transformations ran.

