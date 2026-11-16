# UCI-only D3/D6 metadata readiness - November 1, 2026

**Outcome: PARTIAL; not ready to execute the first dataset-to-feature verification.** The intended local UCI raw input is identifiable and matches the historical audit fingerprint. Historical partition metadata is internally consistent. Source/class provenance, original-row lineage, accepted grouping/split records, an audited feature dictionary and the current preparation inputs remain incomplete.

Only this report is created. No dataset-to-feature check, notebook, test, transform, model or calibrator was executed. No pending decision is approved here.

## 1. Scope and independently verified starting state

Checkout: `<user-profile>/Desktop/Projects/Thesis_Prototype_Git`.
Branch `main`; HEAD `6bded57d38e9b83ba718d7795b97e2130128c23f`; upstream `origin/main`.

- `origin`: `https://github.com/LichSavant/Thesis_Protoype_Test.git`.
- `se-brl`: `https://github.com/LichSavant/CS4101-Thesis2-SE-BRL.git`.
- Starting inventory: 22 unstaged tracked paths, 21 untracked files, nothing staged. Nineteen tracked modifications are existing materialized LFS datasets.
- Git reads used `GIT_OPTIONAL_LOCKS=0`; status disabled LFS filters. No synchronization, index refresh or configuration changes.
- The existing `.pytest_cache` permission warning remains. It was not repaired or inspected.
- A fresh SHA-256 baseline covers 245 existing tracked/untracked files, all files under `experiments/` and `database/`, and Git index/config. Historical prediction/result files were hashed only as opaque preservation bytes, not parsed or displayed.
- Saved files were reviewed; unsaved editor buffers were not accessed.

The preceding `docs/research/2026-11-01_notebook04_branch_isolation.md` records 34 branch tests, 732 Python tests, 25 frontend tests and 275 syntax-valid notebook cells. These are **previously reported results, not fresh results from this audit**. Relevant test source and notebook wiring were inspected; no tests were rerun.

Status meanings: **VERIFIED** is a directly checked, bounded fact; **PARTIAL** means relevant but incomplete evidence; **MISSING** means required current evidence was not found in this checkout; **CONFLICTING** identifies an incompatible assertion/convention. None alone demonstrates actual unknown row contamination. File existence, an LFS match, a reference string and synthetic tests are not scientific approval.

## 2. Governing paper and code references

The [approved proposal](../../Thesis_Proposal_Documents/Alcover%20%26%20Orbello_Approved%20Document%20Proposal.pdf) remains governing. SHA-256:
`283338c5535c5553e35266f5083a6380e014637e63d42161c659238e257ad1fe`.

The 155-page PDF was read directly using in-memory standard-library stream/font-map extraction. Relevant complete page text was inspected; no extracted-text file was created. No PDF figure/layout verification is claimed.

| Provision | Applicable requirement |
| --- | --- |
| Section 4.2.1, Tables 4.1-4.2, PDF pp. 58-60 | UCI repository 327, 11,055 source-reported instances, 30 engineered features; independent U1-UCI. Counts are pre-audit. |
| Section 4.2.2, Table 4.3, PDF p. 61 | Versioned source, screening, label, group, split and experiment evidence. |
| Sections 4.3.1-4.3.2, PDF p. 63 | Immutable source, SHA-256, source_snapshot_id, repository/DOI/URL, license, access date, schema and class definition. |
| Section 4.3.3, Table 4.4, PDF pp. 63-65 | Original IDs, reason-coded screening/attrition, duplicate families and reconciled conservative groups before partitioning; technical domain/path grouping where the source permits. |
| Section 4.3.4, Tables 4.5-4.6, PDF pp. 66-68 | Unsupported evidence stays Unavailable; state, modality, schema and repeatability verification. No trained behavioral classifier or human-annotation prerequisite. |
| Section 4.3.5, Table 4.7, PDF pp. 69-70 | UCI uses its own approved technical feature space; no raw pooling with PhiUSIIL or SE-BRL contribution claim. |
| Sections 4.3.5.2-4.3.5.3, Tables 4.9-4.10 | Development-only selection, grouped folds, fold-local learned operations and frozen feature/environment versions; sealed outcomes cannot select candidates. |

Notebook references use **zero-based cell index and stored cell ID**, never execution count:
`N01` = `experiments/notebooks/01_data_audit.ipynb`;
`N02` = `experiments/notebooks/02_data_cleaning.ipynb`;
`N03` = `experiments/notebooks/03_preprocessing.ipynb`;
`N04` = `experiments/notebooks/04_feature_extraction.ipynb`;
`N05H` = historical `experiments/notebooks/05_experiments.ipynb`;
`N05D` = `experiments/notebooks/05_development_preparation.ipynb`.

In code citations, D9 means `ml/development_experiments.py`; it is distinct from the N05D companion notebook.

Research drafts support analysis, not amendments. `docs/research/experiment_protocol_decisions.md:5` leaves every H1-H12 resolution Pending; this audit changes none.

## 3. Source and artifact inventory

### Existing source candidates

| Path | Observed role and authority |
| --- | --- |
| `experiments/datasets-raw/webpage/uci/phishing+websites.zip` | Materialized LFS archive, 1,011,184 bytes; contains exactly the three members below. Local source container, not independent acquisition/license proof. |
| `experiments/datasets-raw/webpage/uci/phishing+websites/Training Dataset.arff` | **Intended primary local raw input**, 800,920 bytes. Explicitly selected by N01 cell 6 `31080e7c` and N02 cell 10 `62eaeb75`. Matches archive member and saved raw audit hash. |
| `experiments/datasets-raw/webpage/uci/phishing+websites/.old.arff` | Legacy member, 170,897 bytes; relation test and different attribute domains. Not selected by N01/N02. Do not substitute or concatenate. Its name/relation does not make it the SE-BRL sealed-test partition. |
| `experiments/datasets-raw/webpage/uci/phishing+websites/Phishing Websites Features.docx` | Supplied feature descriptions, 38,995 bytes; 176 text paragraphs inspected. Matches archive member. Not a completed project dictionary or acquisition manifest. |
| `experiments/data/interim/webpage/uci_phishing_websites_clean.csv` | Intended cleaned input selected by N03 cell 6 `6b7c4909`; 420,700 bytes. Header matches all 31 ARFF attributes in order. Record-level transformation lineage remains unverified. |

All four LFS payloads match HEAD pointer OIDs **and declared sizes**. The ZIP member bytes match all three extracted files. Fresh fingerprints:

| File | SHA-256 |
| --- | --- |
| ZIP | `514f582cb44cba17251baf1d59f64cddff16efa2b644d091ce8d2a1e8d492940` |
| Training Dataset.arff | `3bcf93b1612306537ee2737751f1bac185b2a77886ab376644c3bf0c7f7cb3e6` |
| .old.arff | `18841a0b7f3bd1e63e2897dca7ae7e75c6ed9ebcc1d9925cbbb3964754c19b51` |
| Cleaned CSV | `5bdf3b3429f31b4c31d137f3872eede81fe45f9473ad033afb425dd50e62ba92` |
| Feature DOCX | `f6f9326f45659a7b5ef947fa744cec2c379dbea17de56d34436312407faca43c` |
| Historical UCI partition manifest | `371c0b29d19772c0061db824aff2c77ec5e9bf126568b2e63ce7e755845aa84f` |

`experiments/results/audits/dataset_inventory.csv:7` records the same Training Dataset.arff hash, 11,055 rows and 31 columns. The fingerprint matches present bytes. The row count is **saved audit evidence**, not a freshly parsed raw-data count.

### Existing derived and historical evidence

| Evidence path | What exists / what it proves |
| --- | --- |
| `experiments/results/audits/dataset_inventory.csv`, `label_distribution.csv`, `uci_native_value_audit.csv`, `missing_values.csv`, `exact_duplicates.csv`, `verified_label_semantics.csv` | Historical source/schema/class/missingness/duplicate summaries. No complete source/license/snapshot freeze. |
| `experiments/results/cleaning/cleaning_log.csv` and `validation_results.csv` | Recorded duplicate removal, integer conversion and validation; no original-row canonicalization map. |
| `experiments/results/preprocessing/partitions/uci_partition_manifest.csv` | Saved historical ID/source/target/group/partition/fold assignments. Fresh metadata aggregates are in section 5. |
| `experiments/results/preprocessing/preprocessing_policy.csv` | Declares learned transforms training-local; deterministic mapping/identity construction may be global. A policy is not execution provenance. |
| `experiments/results/feature_extraction/evidence_availability.csv` and `summaries/dimension_state_summary.csv` / `vector_summary.csv` | Historical UCI unavailable-state aggregates. No current per-record behavioral/evidence file. |
| `experiments/results/experiments/experiment_manifest.json` and `input_manifest.csv` | Historical LR configuration, 30 UCI predictor names and historical input hashes. |
| `experiments/results/experiments/uci_confusion_matrices.png`, `uci_precision_recall.png`, coefficient/holdout artifacts | Exist and were preservation-hashed. No performance interpretation, prediction-row inspection or selection use. |

`experiments/data/processed/` contains only `.gitkeep`. `experiments/runs/` does not exist. Current fixed inputs below are absent, as are current D9 outputs:

- `experiments/runs/paper-preparation-v1/data/processed/preprocessed/uci_phishing_websites_preprocessed.csv`.
- `experiments/runs/paper-preparation-v1/results/preprocessing/partitions/uci_partition_manifest.csv`.
- `experiments/runs/paper-preparation-v1/data/processed/features/development/uci_development.csv`.
- `experiments/runs/paper-preparation-v1/data/processed/features/sebrl/uci_sebrl_features.csv`.
- `experiments/runs/paper-preparation-v1/data/processed/features/development/development_input_manifest.json`.

The historical unversioned preprocessed/compact files are also absent. Historical `input_manifest.csv:8-9` preserves:
preprocessed SHA `e5558bced50e80b3133ea3c60ac7f062c5c02fa0bb3ce9df24d5ddba557bfadf`;
behavioral SHA `c7f039c60910d2d026692305aed238a127839cfd8e37d9f92445a0452714a1c4`.

The raw audit fingerprint matches today's raw bytes and historical counts/configuration are compatible. Nevertheless, absent experiment inputs and source-to-derived lineage prevent proving that every historical result corresponds to the exact present raw/cleaned version. No historical-result equivalence is claimed.

Git history records UCI manifest addition at `abfe2f4` (October 4), raw/cleaned LFS files at `10ccb9d` (October 28), and results at `6d1dae0` (October 29). Commit dates are not acquisition dates, execution evidence or approval.

## 4. Metadata evidence matrix

Paths identify the best existing evidence, not automatic scientific authority. Execution blocking is distinguished from later modeling/evaluation gates.

| Requirement | Evidence path / code location | Status | Exact reason | Blocks? | Minimum next action |
| --- | --- | --- | --- | --- | --- |
| Approved source role | Proposal Tables 4.1/4.7; `ml/notebook_contracts.py:21`; `ml/development_experiments.py:82` | VERIFIED | Independent U1-UCI; D9 permits only U1 | No | Retain scope; no pooling/E2/E3. |
| Intended raw identity | N01 cell 6 `31080e7c`; N02 cell 10 `62eaeb75`; audit `dataset_inventory.csv:7` | VERIFIED | Explicit selected filename, matching inventory/archive/LFS bytes | No for local identity | Bind to source snapshot record. |
| Acquisition/access provenance | Proposal Section 4.3.2; raw inventory above | PARTIAL | Hash/file/count/docs exist; no completed UCI source_manifest with snapshot ID, access date, license and exact class-definition citation found | Yes | Recover existing source/access evidence; do not infer from Git dates. |
| Alternate file exclusion | `.old.arff` header; N01/N02 source paths | VERIFIED | Different schema, not the selected input | No | Keep immutable and outside modeling pool. |
| Schema/header compatibility | ARFF header through @data; clean CSV header; `experiment_manifest.json:188` | VERIFIED | 31 names/order agree; historical predictor list is exactly 30 attributes excluding Result | Not for header; row checks pending | Later check authorized development values against per-field domains. |
| Native label meaning/mapping | `verified_label_semantics.csv:4-5`; N01 cell 43 `b2406143`; N03 cell 88 `d6e0ca92`; `ml/notebook_contracts.py:23` | PARTIAL | Internally agrees: Result -1 -> target 1; Result 1 -> target 0. Saved "verified" assertion lacks precise source passage/freeze evidence | Yes | Pin source class definition and accepted mapping without changing native Result. |
| Observation/source identity | N03 cell 88; `ml/notebook_contracts.py:81`; historical UCI manifest | PARTIAL | Positional UCI IDs explicit/unique, but refer to cleaned rows; no preserved raw-to-clean original-ID map | Yes for complete traceability | Recover version-bound row lineage and duplicate canonicalization; never assume arbitrary row order. |
| Screening/attrition | `cleaning_log.csv:2,11,21`; `validation_results.csv`; Proposal Table 4.4 | PARTIAL | Historical 11,055 - 5,206 = 5,849 reconciles; no complete reason-coded original-ID eligibility freeze | Yes | Reconcile source, exclusions, canonical records, retained IDs and split. |
| Exact duplicate families | N02 cells 16-18 `be8e3d45`/`f7e58383`; N03 cell 91 `eb5cf346` | PARTIAL | Complete duplicates removed; conflicting feature/label pairs retained. No raw duplicate-family map found | Yes for full audit | Document canonical families; no relabeling. |
| Grouping sufficiency | Proposal Section 4.3.3/Table 4.4; N03 cells 87-96 | PARTIAL | Exact-vector grouping exists; no raw URL/domain/campaign/template identity in schema | Yes, narrow UCI scope | Record accepted vector-only limitation and unavailable relationships; no invented domain/MinHash rules. |
| Historical ID coverage | `results/preprocessing/partitions/uci_partition_manifest.csv` | VERIFIED | 5,849 unique IDs; exactly UCI::0..5848; one expected source | No within this file | Reconcile to accepted retained-row lineage before adoption. |
| Historical partition isolation | Same manifest; `ml/experiment_inputs.py:259` | VERIFIED | 4,094/878/877 rows; zero supplied group crossings; both target codes in each partition | No for recorded assignments | Preserve exact supplied assignments if accepted; no regeneration. |
| Historical development folds | Same manifest; N03 cell 105 `a830d120`; `ml/notebook_contracts.py:131` | VERIFIED | Five folds, both classes; zero group crossings; reserved folds blank | No within metadata | Preserve membership; check actual aligned inputs later. |
| Source-bound group/split acceptance | N03 cell 3 `4992e9f8` / cell 40 `407edb97`; decision draft H5 | MISSING | GROUPING_PROTOCOL_REFERENCE=None; historical manifest has no source hashes, version or approval linkage | Yes | Document UCI-specific acceptance/reuse tied to provenance; a reference string alone is insufficient. |
| Approved feature dictionary | Raw schema/DOCX; `experiment_manifest.json:188`; N05D `d9-required-config` | PARTIAL | Historical 30-name list exists; no current frozen types/domains/null/encoding/version record. D9 dictionary configuration is None | Yes | Freeze explicit ordered UCI dictionary/exclusions, source-backed. |
| Predictor exclusion safeguards | `ml/experiment_inputs.py:290-315`; `ml/development_experiments.py:37-63,137-148` | VERIFIED | Explicit allowlist; known labels/IDs/group/fold/hash/source/provenance rejected; no D9 dtype discovery | No for code; actual matrix pending | Verify accepted dictionary/emitted predictor names later. |
| U1 state/mask semantics | `ml/notebook_contracts.py:216`; `ml/branch_preparation.py:89`; D9 `:134-136`; saved UCI summaries | VERIFIED | Technical indicators unavailable/unsupported; eight compact zeros; U1 omits behavioral predictor slots | No for contract | Later verify each emitted state/mask/evidence record; Email rule freeze is unrelated. |
| Missingness / native feature codes | ARFF domains; saved missing/native audits; D9 `:137-147,258-270` | PARTIAL | -1/0 are declared feature values, not nulls. Historical missingness zero; present development rows unparsed | Yes for actual-row acceptance | Preserve codes; validate finite/allowed values without fitting/imputation. |
| Current N03 -> N04 handoff | N03 cells 144-145; N04 cell 14 `ef42ccf9`; `ml/notebook_contracts.py:165` | MISSING | Versioned preprocessed/manifest pair absent; alignment validator has no current pair to check | Yes | Supply traceable accepted inputs; do not blindly copy a historical manifest. |
| Reserved payload access boundary | `ml/branch_preparation.py:67-76`; N04 cell 14 | PARTIAL | Full selected preprocessed CSV read before development filtering; processing isolation is not input-read isolation | Yes for strict development-payload-only gate | Specify access scope and a reviewed development-only reader/path; do not misdescribe current loader. |
| No test-derived learned transforms | Historical policy; N03 cells 135-136; D9 `:153-177`; N05H cell 12 `aeae4aa2` | PARTIAL | Preparation/D9 fit nothing; historical Pipeline source fits locally, but current execution lineage absent | Not a no-fit check once other gates pass; yes before modeling claims | Keep unfitted now; verify future trainer fold-local behavior separately. |
| Untouched holdout / no test-driven selection | N05H holdout source; saved manifest/artifact presence; decision draft H3 | CONFLICTING | An untouched-test claim conflicts with historical evaluation. D9 lacks a test loader but cannot prove absence of prior researcher influence | Not blanket block on documented no-fit development checks; blocks confirmatory claims without a plan | Record UCI exposure/custody and permitted claims; no resealing or selection from historical outcomes. |
| Reproducibility/protected exports | `ml/branch_preparation.py:128-196`; D9 `:181-301`; historical input manifest | PARTIAL | Fixed paths, exclusive writes, hashes/strict reads implemented; current inputs/provenance/dictionary absent | Yes for complete replay | Bind source/derived/code/config/dictionary/environment versions in unused namespace. |

## 5. Labels, lineage, groups and partition findings

The saved implementation interprets native Result -1 as phishing/target 1 and native Result 1 as legitimate/target 0. This reports existing semantics, **not a new approved mapping**. The proposal requires source-backed repository class definitions. N01 hardcodes the "verified from source documentation" wording without an exact passage/reference in the exported CSV. The feature document's per-feature rules are not automatically proof of the target Result definition. No label reversal is proposed or inferred from class balance/outcomes.

N02 cell 18 `f7e58383` drops complete duplicates and resets the index; cell 30 `97f997c2` converts byte codes to integers. Its export retains only 31 native columns. Original raw row identities and duplicate canonicalization are not retained. N03 subsequently creates source_row_id and UCI::position IDs from this cleaned order. A reordered/recleaned input can assign the same ID to another observation unless the cleaned hash/order and raw correspondence are bound externally.

Saved cleaning records report 11,055 -> 5,849 after removing 5,206 full duplicates; native values preserved. These are historical aggregates, not a new cleaning run. Saved audits report zero missing fields. No numeric raw/clean observation rows were parsed here.

N03 cell 90 `989a40c0` dynamically selects predictors by exclusion. Cell 91 `eb5cf346` stringifies in column order, joins with a vertical bar, SHA-256 hashes, sorts unique hashes and assigns ordinal group IDs. Result/target/source/observation metadata are excluded from that hash. With today's header, these are the 30 technical features. However, dynamic selection is not an approved dictionary, and order/serialization/population changes may change hashes or ordinal group IDs.

Identical feature vectors with different labels remain together. This controls exact-vector overlap, **not domain/campaign independence**. UCI lacks underlying URL/domain/path/content IDs in the inspected schema. The paper conditions technical domain/path grouping on availability; do not invent those fields or require HTML for U1. A narrow documented UCI grouping limitation is needed, rather than reopening every thesis decision.

Freshly aggregated historical metadata:

| Partition | Rows | target 0 | target 1 |
| --- | ---: | ---: | ---: |
| development | 4,094 | 1,969 | 2,125 |
| calibration | 878 | 420 | 458 |
| test | 877 | 441 | 436 |
| Total | 5,849 | 2,830 | 3,019 |

| Development fold | Rows | target 0 | target 1 |
| --- | ---: | ---: | ---: |
| 1 | 820 | 382 | 438 |
| 2 | 820 | 371 | 449 |
| 3 | 817 | 423 | 394 |
| 4 | 818 | 407 | 411 |
| 5 | 819 | 386 | 433 |

Verified within the supplied manifest: 5,849 unique IDs, exactly UCI::0 through UCI::5848; one expected source; 5,785 groups; 64 mixed-target groups; zero partition-group crossings; zero development-fold group crossings; five valid folds; both target codes in every partition/fold; no reserved fold values. Development folds use lossless 1.0-style CSV encodings supported by shared decoding.

The manifest contains only observation_id, source_dataset, target, group_id, partition and cv_fold. It lacks native Result, source/raw-row locators, source hashes, feature hashes and grouping-version linkage. Therefore its internal consistency cannot prove its own alignment to a particular payload. Predictor-to-hash-to-group identity was not recomputed.

## 6. Feature dictionary, U1 and reproducibility boundaries

The following is the **schema-backed candidate list to review**, not a newly approved dictionary. Raw attributes, clean header and historical predictor order agree exactly:

~~~text
having_IP_Address, URL_Length, Shortining_Service, having_At_Symbol,
double_slash_redirecting, Prefix_Suffix, having_Sub_Domain, SSLfinal_State,
Domain_registeration_length, Favicon, port, HTTPS_token, Request_URL,
URL_of_Anchor, Links_in_tags, SFH, Submitting_to_email, Abnormal_URL,
Redirect, on_mouseover, RightClick, popUpWidnow, Iframe, age_of_domain,
DNSRecord, web_traffic, Page_Rank, Google_Index, Links_pointing_to_page,
Statistical_report
~~~

Preserve source spellings. Domains are discrete; many are {-1,1}, several {-1,0,1}, and Redirect {0,1}. The dictionary must specify ordered names, per-field native meaning/domains, machine types/representation, null policy, inclusion/exclusion, source references and version/hash. Preserving integer codes in preparation does not preapprove every later classifier encoding choice. No field is selected/excluded from outcomes.

Forbidden predictors include Result/target/source_label/native_label; observation/original/source-row IDs; feature_hash/group_id/partition/cv_fold; source_dataset and provenance/snapshot fields. D9's allowlist checks known case-folded names and source_/provenance_ prefixes. It cannot prove semantic safety of arbitrarily renamed/precomputed features without the audited dictionary.

For UCI, all twelve indicators remain unsupported/unavailable, evidence arrays empty with availability false, and all four dimensions Unavailable rather than Absent. Eight zero-valued support/availability fields are retained in the compact contract but **not included in U1 predictor tuples**. No urls=[] or missing Email substitute is created. SFH, Submitting_to_email or popUpWidnow do not become behavioral evidence. Native -1/0 values are not missing-value sentinels.

Historical summaries report four unavailable dimensions over all 5,849 UCI records. Current per-record feature tables are absent. Historical experiments name their conventional UCI run E1; the repaired protocol calls the branch U1-UCI. Preserve historical names/results rather than relabeling them as newly validated U1 runs.

Material boundaries:

1. `validate_feature_boundary` and `validate_metadata_alignment` enforce types, source/native mappings, one-to-one IDs, supplied groups/folds and class coverage. They do not authenticate acquisition or an external original-ID/population freeze.
2. `load_selected_inputs` reads the full preprocessed CSV and complete manifest before development filtering. It requires all three partition roles. Supplying development-only rows to that loader is not a compatible workaround.
3. `prepare_selected_branches` can handle development-only UCI records independently. A strict development-only reader/staging path can reuse it, but actual-data access/wiring is not implemented or approved by this audit.
4. N03 still reads all six interim sources (cell 7 `99bc2e45`), reaches an unfrozen grouping guard before UCI (cell 40 `407edb97`), allocates UCI partitions/folds (cells 96/105), and exports all three branches (cells 144/145). Running it wholesale would read unrelated inputs and regenerate assignments. N04 isolation does not solve this upstream limitation.
5. D9 checks output hashes/fixed paths/strict CSV/alignment, but starts downstream: original raw/clean hashes and source authenticity are not established by that handoff.
6. Deterministic preparation/D9 learn no preprocessing parameters. Historical LR source contains training-fold imputer/scaler Pipelines; source and saved PASS summaries do not prove a current reproducible execution or upstream feature-generation provenance.
7. Historical holdout evaluation exists. No outcome values were inspected here. Software cannot make that history untouched or reseal it. No new candidate, dictionary or scientific decision may be justified from those outcomes.

Available .venv module discovery found no numpy, pandas or sklearn. This blocks the current pandas notebook path in that environment, not standard-library metadata work or a narrowly implemented no-fit driver. No installation or environment change occurred.

## 7. Minimum UCI-specific evidence and responsibility

| Needed item | Responsible contribution | Approval / acceptance distinction |
| --- | --- | --- |
| Source/access/class definition | Vera/source custodian supplies existing acquisition/license/class records; Dhanwil binds names/hashes | Recover evidence, not a new dataset. Any class-definition mismatch must be resolved before ingestion. |
| Raw-to-clean lineage and attrition | Dhanwil traces existing N02 procedure; source custodian confirms existing original IDs | No guessed IDs, new duplicate policy or relabeling. Later actual-data lineage reconciliation requires bounded authorization. |
| Grouping limitation/split reuse | Joint researchers document UCI scope; adviser where claim/deviation decisions require it | Explicitly accept/reject vector-only limitations and historical assignments; never invent broader independence or new splits. |
| Ordered UCI dictionary | Dhanwil prepares source-backed fields/domains/types/null/exclusion metadata; researchers freeze it | The present 30-name list is a recommendation, not recorded approval. |
| Access/custody and exposure | Joint researchers/adviser for scientific claims; Dhanwil implements accepted boundaries | Prefer development-payload-only access. Broader reserved-payload access must be explicitly scoped; no resealing claim. |
| Named inputs and safe entry point | Dhanwil after contract specification | Reuse supplied assignments and fixed outputs; do not execute combined N03 or disguise full CSV reads as development-only access. |

H3/H5/H11 matter only in this UCI-specific scope. Email benchmark/rule/language decisions, a new Web dataset, transformer work, human annotation, every H1-H12 item and unknown SRS limits are not blanket prerequisites to a no-fit UCI metadata/preparation check. No new decision is Approved.

## 8. First future UCI-only verification gate

**Plan only: not executed or authorized here.**

Before real-data preparation, require a versioned UCI acceptance packet binding the pinned source/archive/clean hashes; source_snapshot_id/acquisition/license/class references; accepted screening/attrition and original-to-clean canonical IDs; accepted grouping limitation and exact group/split/fold metadata/hash; explicit dictionary/representation/null policy; exposure-aware access scope; actual code/configuration/environment identities and unused run ID.

**Recommended access default, Pending:** a custodian-provided development-only payload plus complete partition metadata. This permits overlap checks without opening reserved predictor payloads. Its reader/staging boundary must be separately implemented/reviewed; current N04 full-population loading does not provide that guarantee. If researchers instead accept a whole-population technical-input check, record broader access explicitly before execution. Neither choice restores a historical seal.

Required future payload fields: declared technical predictors, native Result, source_dataset, source_row_id, observation_id, target, group_id, partition and cv_fold. Expected retained/development IDs must come from accepted lineage, not historical hardcoded totals. Full partition metadata is used for group barriers; reserved predictions and predictor payloads are unnecessary under the recommended scope.

Input staging is a separate documented precursor. Do not simply copy a historical manifest or run N03 to generate another split. No missing source or rule meaning may be fabricated.

### Allowed future outputs

After separate execution authorization, use an unused `experiments/runs/<run_id>/` and existing D9 fixed names:

- `data/processed/features/development/uci_development.csv`.
- `data/processed/features/sebrl/uci_sebrl_features.csv`.
- `data/processed/features/development/development_input_manifest.json`.

The manifest contains only UCI, existing compatible contract/run identifiers and SHA-256 of exact bytes. Aggregate diagnostics may go to stdout without records, IDs, predictions or content. The minimal check need not create six optional shared diagnostic artifacts. Any broader output set must be explicitly named/preflighted. No metrics, plots, fitted transforms, model files or historical-directory writes.

### Checks, failures and acceptance criteria

Pass only when all criteria hold:

1. Required records resolve and have their stated acceptance; Pending entries are not treated as approved. Authorized input hashes/schemas/versions match.
2. Acquired -> excluded/duplicate -> retained -> partition counts and exact IDs reconcile. Original/native labels and raw-to-clean canonical lineage remain traceable.
3. Valid source/native/target/position types and unique canonical IDs; exact expected population coverage. No label mapping is guessed.
4. Only the accepted supplied groups/partitions/folds are used. Zero supplied group crossings, development folds 1-5 with both classes, null reserved folds. Unavailable broader relationships are disclosed.
5. The implemented reader demonstrates the accepted access scope: recommended development payload only plus complete metadata; no Email or reserved predictor access. No dependency on file-existence-based branch selection.
6. Technical dispatcher/compact output preserve each observation and source field, target/group/role/fold exactly. All UCI indicators/dimensions remain unavailable; eight compact bits zero; predictor names/order equal the explicit dictionary and contain no labels/bookkeeping.
7. Missing numeric values retain their documented meaning; native -1/0 remain native values. No fit/fit_transform, imputation, scaling, feature removal, tuning, calibration, scoring, thresholds or model selection.
8. The actual D9 consumer accepts output hashes/schema and only U1 fold plans without fitting. Existing source/behavior join metadata is one-to-one.
9. Only the three selected fixed outputs are created exclusively, manifest last. Output collisions/redirected paths are rejected before writes. Invalid inputs cause no output-path creation.
10. Before/after hashes confirm unchanged historical data, partitions, notebooks, results, decisions, persistent database and Git index/config. Diagnostics use task-owned temporary storage and suppress caches/bytecode where practical.
11. A future verification report separates actual-data aggregates from synthetic evidence, records zero fits, names versions/limitations/exposure and claims only the checks performed. Passing advances UCI D3/D6, not D10 or whole-thesis completion.

Expected failures include missing/ambiguous provenance, unsupported class codes, malformed/duplicate columns, unexpected predictors, invalid/nonfinite values, ID/source-position/population/manifest mismatch, group/fold crossing, reserved development-input rows, fabricated evidence, unselected reads, redirected paths, collisions and mismatched hashes. Fail rather than repair/allocate/fill to pass.

The exporter has ordinary IO rollback for its own newly created files/empty directories. It is not atomic under process termination; interrupted bundles must not be overwritten or presumed complete.

## 9. Updated D3/D6 and exactly one next task

| Responsibility | Status after this audit |
| --- | --- |
| D3 UCI | PARTIAL. Local identities/schema and historical metadata coverage/barriers verified; acquisition/class provenance, original-row lineage, screening/group acceptance and current payload alignment incomplete. |
| D6 UCI | PARTIAL. Implemented safeguards and prior synthetic coverage exist; no actual dataset-to-feature check or current D9 handoff. Dictionary and access/staging contract unresolved. |
| D3/D6 thesis-wide | Not complete. No readiness promotion for other branches. |
| D10-D13 | Remain blocked/not executed. Metadata checks do not establish model-selection/final-evaluation evidence. No transformer prerequisite introduced. |

**One recommended next technical task:** implement and synthetically test a **UCI-only supplied-assignment preparation entry point** that consumes an explicitly scoped development payload plus complete partition metadata, preserves observation/source IDs, never allocates groups/splits/folds, and reuses the existing technical dispatcher and fixed exclusive D9 exports. Keep actual-data execution gated on the UCI acceptance packet. This is an incremental upstream access/contract repair, not a notebook rebuild or scientific-setting choice.

## 10. Preservation and stop record

Operations performed: read-only Git status/rev-parse/branch/remote/log and selected LFS pointer show; path inventory; streaming SHA-256; ZIP member metadata/opaque hashes; ARFF header reads stopping at @data; CSV headers and existing aggregates; UCI partition metadata aggregation; notebook-source JSON reads; module/test/document inspection; package discovery; in-memory approved-PDF extraction.

No numeric raw/clean UCI observations were parsed/displayed. No dataset URLs were opened. No historical prediction/performance rows were inspected for analysis or selection. No notebooks/tests/preflight pipeline/trainers were executed. No download, package installation, split generation, source alteration or Git mutation occurred.

Final checksum comparison against the 245-file start verified no changed or removed existing file, including datasets/results, partitions, N03/N04/N05, previous drafts, persistent database and Git index/config. The only addition is this report. Final Git inventory verified: 22 unstaged tracked paths, 22 untracked files, no staged changes; main/HEAD/upstream/remotes unchanged.

Context for ChatGPT: Intended raw/archive/interim UCI bytes match LFS; raw audit SHA matches Training Dataset.arff. Historical metadata: 5,849 unique IDs, 5,785 groups, 64 mixed-label groups, 4,094/878/877 partitions, five intact development folds and zero supplied group overlap. These do not establish source/group approval or feature verification. Current versioned UCI inputs/handoff are absent. Source/license/class evidence, raw-to-clean lineage, accepted vector-only grouping/split reuse, explicit dictionary and access scope remain pending. N04 reads full selected data before filtering; N03 remains combined and allocates splits. Next engineering task is a synthetic-tested UCI-only supplied-assignment entry point; actual data remains gated. Only this report was added.

