# Email lineage crosswalk verification

November 5, 2026, Asia/Manila. **Overall result: BLOCKED.**

Available admissible metadata establishes **zero verified historical-to-repaired
record pairs**. It does not establish that counterpart records are absent.
There is no materialized repaired Email record inventory, source-backed
per-record identity ledger or two-sided non-content key with which to verify
the requested crosswalk. No row-level crosswalk was manufactured or exported.

The historical assignment manifest's internal isolation checks pass. Transfer
of those assignments onto repaired records remains **not verifiable**, because
identity must be established before comparing or carrying assignment fields.
Zero checked pairs is not a successful preservation test.

## Packet

- [Machine-readable evidence](crosswalk_evidence.json): aggregate source/scenario
  counts, key eligibility, unknown values, code/hash provenance and preservation.
- [Assignment compatibility](assignment_compatibility.md): three separate
  analytical scenarios and exact transfer limitations.
- [Unresolved identity cases](unresolved_identity_cases.md): evidence gaps and
  rejected matching strategies, without individual record identifiers.
- [Next acceptance gate](next_acceptance_gate.md): smallest missing input and
  design for a future restricted metadata artifact; no artifact is exported here.

## 1. Inspected evidence and audit boundary

Read the November 5 Email acceptance report, its CEAS decision matrix/evidence
register and companions; November 5 deterministic completion report; historical
N03 source at `1a45c53`; current N03 source and notebook/assignment/integration/D9
contracts; dataset/adapter/metadata/grouping schemas; historical input references;
available audit/cleaning/feature metadata schemas and candidate file inventory.
Notebook inspection selected source cells; stored output records were not
inspected and no cells ran. Filenames and explicitly safe metadata were searched;
runtime logs, credentials and content-bearing corpus files were not searched.

Raw/clean Email payloads and archives were **not opened**, including for new
hashing. Previous file fingerprints/header inventories were read as documented
evidence. Historical sealed-test predictions, metrics, outcome values and plots
were not opened. Only the six-column supplied assignment table and safe aggregate
metadata were parsed. Targets were used for assignment/class-integrity summaries
only, never as identity keys or tie-breakers. No dataset/preprocessing/model API
or test suite was executed. Existing synthetic results are not fresh evidence.

## 2. Exact identity and assignment constructions

Notebook cell numbers below are zero-based JSON indices.

| Identifier / key | Exact construction and evidence | Reconstructibility / admissibility |
| --- | --- | --- |
| Historical Email observation ID | At `1a45c53`, N03 cell 15 (`95feb561`) keeps Nazario and native-code-0 records from CEAS/Enron/SpamAssassin; cell 19 (`39163f5c`) applies per-source `cumcount()` after filtering; ID is `source_dataset + "::" + filtered_rank` | Deterministic for the exact ordered inputs/filter/run. The suffix is a filtered rank, not a retained original source locator. No run-linked per-record bridge is supplied |
| Historical `source_row_id` | The same post-filter per-source count, N03 cell 19 | Misleading if interpreted as current cleaned-file position; not present as a separate column in the saved assignment CSV |
| Repaired preprocessing ID | `ml/notebook_contracts.py:47`, `build_email_population`: enumerate each cleaned source before filtering; save `source_row_id=position`, `source_label=native`, ID `f"{source}::{position}"`; current N03 cell 19 verifies coverage | Deterministic given the exact source sequence; only positions plus an authenticated provenance chain could support linkage. No repaired output table is present. CEAS is outside this default primary builder |
| Original source identifier | Recorded CSV schemas have subject/body/label and, for three sources, sender/receiver/date/URLs; no explicit original-record-ID column is documented | No admissible populated source record key/namespace was found. Message fields are prohibited for this audit and were not inspected |
| Dataset-neutral adapter ID | `ml/experiment_inputs.py:77,122,184-209`: `DatasetIdentity(dataset_id,snapshot_id,provenance_reference)`, supplied `original_record_id`, then `dataset_id + ":" + fingerprint([snapshot_id,record_id])` | A non-content identity construction exists in code, but no real Email instance inventory provides these inputs. Generic types/tests do not instantiate research provenance |
| Metadata fingerprint | `ml/metadata.py`: SHA-256 over canonical JSON, sorted keys, compact separators, ASCII encoding, finite JSON values | A deterministic metadata hash, not a content-normalization hash. Cannot be calculated as a research identity substitute without authenticated original IDs/snapshot linkage |
| File fingerprint / run labels | Prior source inventories contain whole-file SHA-256; source_snapshot_id fields remain null. `PREPARATION_RUN_ID=paper-preparation-v1`, contract version `notebook-boundary-0.1.0` | File hashes identify a snapshot, not its rows' correspondence to an old derived table. Run/schema names are not acquisition or record identity evidence |
| Duplicate/component group | N03 cells 22-30: lowercase/trim/collapse-whitespace body and sender strings; SHA-256 normalized body; union nonempty sender/body matches; sort union-find roots and enumerate `email_group_NNNNNN` | Deterministic only for the complete ordered inputs/relationships/implementation. Group labels are many-to-one and input-dependent, so cannot identify individual messages or map roots across versions |
| Partition | N03 cells 40-43: seed 42, source/target strata, largest groups first, randomized tie ordering, greedy deficits toward development/calibration/test 70/15/15 | Existing values are supplied scientific assignments. Re-running requires exact group/input/order/library context and would allocate assignments; not performed |
| Development fold | N03 cells 49-52: development groups, source/target strata, seeded tie order, greedy row balancing over folds 1-5 | Preserve supplied values after identity verification. Seed alone is not a reproducibility certificate. Reserved folds are null/blank |

`capture_population` accepts a unique nonempty observation ID independently of a
unique source/position pair. It can retain a legacy ID with a verified current
locator if that convention is accepted; no forced renaming is needed. That
software flexibility does not supply the missing linkage. Exact source/target/
group/partition/fold joins remain required by `validate_metadata_alignment`.

## 3. Candidate-key assessment and matching attempt

The attempt stopped at key/endpoint qualification. The historical CSV contains
only `observation_id,source_dataset,target,group_id,partition,cv_fold`. It has no
source snapshot reference, stable source-record token, verified source offset,
record-level provenance event or retained original-ID hash. A repository search
found no materialized `email_preprocessed.csv`, `email_development.csv`,
`email_sebrl_features.csv`, lineage/crosswalk/record-map artifact in experiments,
and no `experiments/runs` directory. Existing feature-extraction CSVs are schema
or aggregate summaries. Historical input hashes name missing derived payloads.

No admissible key exists on both sides. Consequently, no pair candidates were
formed or tie-broken. These findings are not a claim that every historical ID
points to the wrong record, nor that rebuilding a lineage ledger is impossible.

### Per-source results

ND = not determinable from available endpoint/key evidence, represented by JSON
`null`. Historical unmatched means **without a verified counterpart**, not
proven absent in a repaired population. Ambiguity/collision ND is not zero.

| Source | Historical records | Actual repaired records | Verified unique pairs | Historical without verified match | Unmatched repaired | Ambiguous matches | Admissible-key collisions | Historical coverage |
| --- | ---: | --- | ---: | ---: | --- | --- | --- | ---: |
| Nazario | 1,565 | ND | 0 | 1,565 | ND | ND | ND | 0% |
| Enron | 15,791 | ND | 0 | 15,791 | ND | ND | ND | 0% |
| SpamAssassin | 4,091 | ND | 0 | 4,091 | ND | ND | ND | 0% |
| CEAS-08 | 17,312 | ND; no repaired auxiliary inventory; excluded from current default primary builder | 0 | 17,312 | ND | ND | ND | 0% |

No repaired count is reported as zero merely because outputs are absent. Prior
expected population counts are not measurements of a repaired table. Nazario's
all-positive historical count and similar ordinal construction do not establish
any unique matches under the required non-positional evidence standard.

Historical observation-ID duplicate counts are **zero for each source**. As a
rejected-key diagnostic, using component groups as record keys would yield the
following excess records beyond distinct group keys: Nazario 156, Enron 319,
SpamAssassin 3,167, CEAS 13,516, total 17,158. This quantifies many-to-one grouping
in historical metadata; it is not a collision measurement on an admissible
crosswalk key or evidence of duplicate message identity.

### Hash provenance and normalization

No existing row-level non-content identity hash with an authenticated two-sided
research linkage was found or used for matching. The adapter's metadata hash is
available as a formula only. Previous whole-file raw/clean SHA-256 equality is a
file-level fact; those hashes were not recomputed in this audit or promoted to
row identity evidence.

Historical/current N03 source cells 22,23,27,28,29,30 are byte-equal and AST-equal.
Thus their visible normalization/union algorithms agree at source level. The
body hash formula is SHA-256 of UTF-8 lowercase/trimmed/whitespace-collapsed body;
sender grouping uses the normalized sender string, not an independent identity
token. No persisted row-level body-hash/edge ledger is available in the inspected
metadata. Execution-equivalent historical inputs/parser/environment are not
established. No new content hash was generated. Even an existing content hash
would require separate admissibility, normalization and multiplicity review;
equivalent rules alone cannot establish a one-to-one record match.

## 4. Scenarios and acceptance classification

| Scenario | Historical records / groups | Verified pairs / historical coverage | Identity result | Assignment transfer |
| --- | --- | --- | --- | --- |
| Full historical | 38,759 / 21,601 | 0 / 0% | **BLOCKED** | Not verifiable; CEAS also differs from current default primary scope |
| Non-CEAS projection | 21,447 / 17,805 | 0 / 0% | **BLOCKED** | Internal historical isolation passes; no repaired linkage |
| CEAS-only auxiliary projection | 17,312 / 3,796 | 0 / 0% | **BLOCKED** | No repaired auxiliary identity inventory; historical slice negative-only |

None qualifies as PARTIAL because no records have a verified identity mapping.
Construction code, aggregate counts and historical isolation are verified
findings within an overall BLOCKED lineage result. No CEAS role or population
option is selected. Assignment preservation is further detailed in the companion
document; no new dataset or assignment manifest is exported.

## 5. Preservation and handoff

Checkout main, HEAD `6bded57d38e9b83ba718d7795b97e2130128c23f`, upstream
`origin/main`. `origin` remains configured to Thesis_Protoype_Test.git;
`se-brl` remains configured to CS4101-Thesis2-SE-BRL.git. No synchronization or
Git mutation occurred; optional locking was disabled and status LFS filters were
disabled. No staging, commits, pushes, reset, clean or configuration change.

Baseline: 297 pre-existing files, including prior reports and Git index/config.
213 safe metadata/code files were SHA-256 hashed; 84 protected payload/notebook/
historical-result/database paths were monitored by size and modification time,
without opening their content for preservation hashing. Initial timestamps
passed through JavaScript JSON numbers, losing sub-microsecond precision: 57
integer timestamp comparisons differed by at most 200 ns while comparing equal
at the stored floating-point precision. The first exact-integer check failed on
that bookkeeping issue. Final checks explicitly use the captured precision and
also retain exact current timestamp strings. No safe-file hash or protected
size/stored-precision timestamp change was found. Exactly five new documentation
files were created. Stat agreement is not fresh cryptographic proof of protected
byte identity; previous payload checksums remain previous evidence. No write
command targeted existing research files, code, notebooks, assignments, results
or the database.

Final Git status: 24 unstaged tracked paths, 78 untracked files, zero staged;
same branch/HEAD/upstream/remotes. The pre-existing `.pytest_cache` access warning
was left alone. Unsaved editor buffers were not inspected. No software suites,
notebook execution, package installation or network retrieval occurred.

**Next task:** request an existing source-backed, non-content identity/lineage
ledger and repaired metadata counterpart for one source's development slice.
Verify that subset independently before expanding. The restricted design and
exact acceptance checks are in [next_acceptance_gate.md](next_acceptance_gate.md).
If no admissible ledger exists, lineage reconstruction needs a separately
specified authorization; do not silently substitute a label/position join.

**Context for ChatGPT:** Nov.5 text-free lineage audit is BLOCKED: zero verified
pairs, actual repaired counts/ambiguity/key collisions unknown, no repaired
inventory or row-level provenance key. All three CEAS scenarios retain valid
historical metadata isolation but transfer to repaired observations is unverified.
Post-filter legacy rank versus pre-filter repaired position is a verified
construction difference, not evidence of any particular record match. No raw
Email payload, outcome or content-hash computation; labels never identity keys.
Only five new docs created; current code/research work preserved within the
stated hash/stat evidence limits. Request one development slice's non-content
two-sided provenance ledger; no population selection, preparation or training.
