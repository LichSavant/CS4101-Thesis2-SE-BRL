# UCI scientific admission — BLOCKED

Updated 18 November 2026, Asia/Manila. Current technical-admission baseline `d0f44c482375547a3bfa71524e625795a9c10227`;
same workspace/branch. **0/10 complete admission conditions passed.**
This continuation checked original-author publications, contradictory independent
papers, the approved proposal and signed supervision agreement. It corrects the
prior blanket custodian/adviser-approval interpretation. Result mapping remains
**UNRESOLVED**; genuine records processed **0**, experiments **0**. No labels,
research gates, reserved data, R22 or Transformer contracts were changed.

## New evidence and completed work

1. **Current source/license documentation retained:** official UCI 327 page
   identifies DOI `10.24432/C51W2X`, 11,055 instances/30 features and CC BY 4.0.
   `source-retrieval.json` records exact HTTPS URLs, retrieval timestamps, sizes
   and SHA-256 values. This establishes access to documentation today, not the
   original dataset acquisition date, immutable release identity or custody.
2. **Feature-document identity authenticated against the current publisher:**
   retrieved DOCX SHA-256
   `f6f9326f45659a7b5ef947fa744cec2c379dbea17de56d34436312407faca43c`
   equals the existing Git document bytes. That prior documentation-only step downloaded no archive. `.gitattributes` preserves exact retrieved
   document bytes against checkout line-ending conversion.
   The official API describes `result` as Target but supplies no class definition.
   Feature-rule prose does not establish Result's numeric class mapping.
3. **Exact machine-readable source schema materialized:**
   `ml/uci-native-schema.v1.json` contains all 30 ordered original field names,
   native domains from the retained native-value audit, explicit API aliases and
   zero-based direct-body-paragraph locators into the authenticated DOCX.
   It excludes Result and explicitly has no scientific acceptance. Request_URL
   and Redirect have three qualitative states in the prose but two recorded
   native codes; their state-to-code meanings remain unresolved. No recoding,
   universal zero/missing assumption or semantic label was invented.

**Software repair:** `ml/uci_preparation.py` now checks selected fields against
native domains before any export. Previously finite but invalid codes such as
`Redirect=-1`, fractional `URL_Length`, and invented source fields could pass.
Native values, source spellings/order and existing explicit-null representation
are preserved. Null eligibility and model encoding still require acceptance.
The new schema/code are included by the existing research code-hash mechanism;
no admission gate, approval requirement or research authorization was changed.

## UCI-S01–S10 requirement-to-evidence matrix

`admission-status.json` is the current machine-readable status authority.
VERIFIED applies to complete evidence items; PARTIAL denotes incomplete compound
conditions; BLOCKED_EXTERNAL needs custodian facts or accepted decisions;
BLOCKED_TECHNICAL denotes a failing/missing necessary software check. No whole
condition is fully satisfied. The table below states the exact remaining criteria.

| Condition | Evidence-backed progress | Minimum remaining evidence / authority / acceptance condition |
| --- | --- | --- |
| S01 Source/acquisition | Official source/DOI/license and feature document verified; newly acquired archive matches the pinned original SHA-256. Actual prospective acquisition is recorded in source-snapshot.json. | Historical acquisition remains unestablished. Researchers must accept the prospective source/reconstruction scope; current acquisition is not a backdated historical attestation. |
| S02 Result classes | Official API target description is null; retained feature document has no release-specific Result numeric definition. Existing code/CSV mapping is an assertion, not independent evidence. | Custodian supplies original UCI-327/creator documentation explicitly mapping Result -1/1 to classes for the actual release; researchers verify it. Another dataset's mapping, counts, features or model outcomes cannot substitute. |
| S03 Lineage/attrition | Retained N02 source and cleaning log specify full-row duplicate removal, index reset and byte-to-int conversion: 11,055→5,849, 5,206 removed. N03 cell `d6e0ca92` assigns cleaned-position IDs. | Custodian provides authenticated raw-original-locator→retained-clean-position→existing observation-ID ledger, retained/deleted duplicate-family membership, reasons and transform/code hashes. Verify uniqueness, exact development coverage and preserved order/targets. Recipe/counts do not authenticate correspondence. |
| S04 Grouping | Prior vector-hash recipe `eb5cf346`; metadata confirms 64 mixed-target groups, each size two; 44 development, 10 calibration, 10 test. | Researchers accept source-permitted vector-only scope, unavailable domain/campaign limits and explicit conflicting-label disposition. Custodian proves original-record/vector→supplied-group correspondence. No relabeling, splitting conflicts or fabricated relationships. |
| S05 Split reuse | Reuse prior zero-crossing/five-fold findings. Exact Git manifest hash `304bb9446748e27bd4d1a7521513b1b2e31e0bab3be4f6fac0c8a0673ca7e6fd`; 4,094 development IDs / 4,050 development groups. | Joint researchers accept reuse of this exact manifest after S03/S04/S08. No new split, ID or seed repairs prior exposure. |
| S06 Dictionary | All 30 names/order/native domains are executable and checked; official aliases and definition locators are explicit. Result is excluded. | Researchers freeze exact dictionary hash, null eligibility, numeric/nominal training-local encoding and resolve/limit the prose-versus-code discrepancies. Audited schema is not an accepted semantic dictionary or actual-row conformance report. |
| S07 Custody | Existing in-memory reader and development-only boundary preserved; no authenticated real delivery was found. | Custodian names producer, allowed reader/files/fields and delivery hashes; supplies only development predictors plus independent accepted population/lineage and full assignment metadata. Acceptance requires exact ID coverage and exclusion of reserved payloads before access. |
| S08 Exposure | Reuse documented historical UCI holdout evaluation and diagnostic-exposure uncertainty; no outcomes reread. | Researchers/adviser explicitly accept bounded exploratory/development claim scope and access restrictions, or supply authentic unexposed-scope evidence. Do not call the old holdout untouched. |
| S09 No-fit admission | Source/schema documentary check passes; synthetic supplied-assignment and real verifier tests pass. **Actual-data admission not executed.** | After the applicable evidence is accepted, researchers/custodian bind one D-features authorization to exact code, source/population/assignment/dictionary/freeze/development hashes and exclusive outputs. Independent trusted receipt digest is required; no draft receipt was created. |
| S10 Experiment | Existing four-family, grouped development, training-local preprocessing and uncertainty requirements preserved. | Researchers freeze exact U1 settings, seeds, search/fit/time budgets, nested calibration/threshold/selection/uncertainty and benchmark rules; authenticate one exact development run. These fit settings do not block the earlier authorized no-fit D boundary. Final calibration/test require separate authority. |

## Executed checks and reproduction

- `python -B -m tools.verify_uci_admission_evidence`: **PASS** on retained-source
  digests, publisher/retained-DOCX identity, API source/role/order/aliases and all
  30 recorded native domains. `documentary-checks.json` explicitly retains
  `scientific_admission=BLOCKED`. This command has no network or corpus loader.
- Focused no-fit pytest selection: **130 passed, 0 failed, 0 skipped**; see
  `verification.json`, `focused-tests.txt`.
  Synthetic tests include invalid finite codes, invented fields, all-domain
  coverage and all-30-feature save/load without recoding. No-fit process guard
  reports zero attempted and executed fits.
- Reuse the previous report's six pointer identities, full manifest integrity,
  source/exposure findings and broad regression; do not claim fresh payload hashes.
- `development-metadata.json` adds only conflict-size/role and development-group
  aggregates from the fixed historical assignment Git blob. It does not verify
  source-vector correspondence or grant split reuse.

The interpreter is the pre-existing
`%LOCALAPPDATA%/Temp/sebrl-submission-20261117/venv/Scripts/python.exe`;
run from this workspace with `PYTHONDONTWRITEBYTECODE=1`,
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `DATABASE_URL=sqlite:///:memory:`,
`OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, task-owned TEMP/TMP, and:

```text
python -B -m pytest -p ml.tests.no_fit_guard -p no:cacheprovider -q -rs --basetemp .u/b ml/tests/test_uci_preparation.py ml/tests/test_preparation_execution.py ml/tests/test_research_protocol.py ml/tests/test_preparation_integrity.py
```

Use an unused short test scratch path. Sources compile in memory; Git whitespace
checks and artifact hashes are recorded. No frontend changes/checks are claimed.

Bounded repository/history searches inspected the named UCI paths and prospective
source/label/lineage/receipt/dictionary artifacts, plus source-only N02/N03 cells
and their relevant commits (`cf4f677`, `3ae39fa`, `abfe2f4`). They found recipes and
aggregate assertions, not an authenticated original-record ledger, acquisition
receipt, accepted split/dictionary/custody dossier or run authorization. This
does not assert that custodian-held records outside Git do not exist. Investigation
stops at that external evidence boundary; no speculative crosswalk was made.

## Current official acquisition and reconstruction

`source-snapshot.json` records a genuine acquisition from the official UCI 327
archive URL under the latest Phase A request: **1,011,184 bytes**, SHA-256
`514f582cb44cba17251baf1d59f64cddff16efa2b644d091ce8d2a1e8d492940`, exactly matching
the independently retained original archive identity. The manifest records the
actual current acquisition timestamp, source DOI/provider metadata, CC BY 4.0,
request reference and all three ZIP directory entries. The payload is retained
locally under its explicitly ignored path, not Git/LFS. No ZIP member was opened
or extracted, no genuine ARFF record processed, and no historical acquisition
date invented. Fresh official acquisition authenticates the source archive;
it does not authenticate a development-only subset or admit the study population.

`ml/uci_snapshot.py` reproduces bounded, exclusive acquisition with official-host
redirect restrictions, a 2 MB ceiling, network timeout and pinned digest checking.
Wrong bytes/hosts/oversized responses abort and roll back only new output.

`ml/uci_reconstruction.py` provides an in-memory exact-schema ARFF parser and
prospective candidate constructor: snapshot hash checked before decoding; exact
30 fields/domains plus native Result; original ordinal IDs before filtering;
canonical complete-record/predictor digests; first-occurrence duplicate receipts;
retained original locators/order; native-only retained feature mappings and
ledger consistency checks. Invalid input aborts without partial outputs. No
class meanings, target labels, groups, splits or approvals are generated. The
only executions used generated fixtures, including conflicting native labels;
these are software results, not a reconstructed scientific population. Focused
checks: **119 passed**. Final guarded regression: **804 passed, 0 failed,
10 skipped, 1 fitting test deselected**, zero fitting attempts/executions. The
prior 790-test result remains a historical checkpoint, not an additional count.

`label-source-checks.json` records the remaining authoritative-source boundary.
UCI's API target description is null; its authenticated feature document supplies
no numeric Result definition. The author-deposited Huddersfield dataset page
links UCI and feature documentation but supplies no release-specific Result
mapping; alternate ARFF datasets were neither opened nor substituted. Searches
stop here rather than infer labels from mirrors, feature states or class counts.

**Actual-data execution remains blocked:** there is no verified Result mapping,
accepted reconstruction/conflict/exposure policy or authenticated development-only
source scope. The full original archive includes observations historically used
in reserved partitions. Downloading it anew cannot erase that history or authorize
opening those records. No genuine record-level lineage/attrition ledger or new
assignment receipt is claimed. The current source acquisition is real; the
prospective preprocessing implementation is tested and ready for separately
scoped authorized inputs.

## Historical recovery and prospective fallback

`lineage-recovery.json` records the bounded historical search: zero authenticated
mapping pairs, no identified external backup, and authorized local candidates
exhausted. **Historical lineage remains INCOMPLETE**, not proven globally
unrecoverable. No raw/clean payload comparison or speculative rank bridge occurred.

`prospective-protocol.json` is **READY FOR APPROVAL, UNAPPROVED**. It pins the
original ARFF snapshot, existing pre-filter original-position ID algorithm,
strict parser convention, complete-duplicate first-occurrence policy and
attrition ledger, exact-vector grouping with conflicting native labels retained,
explicit exposure restrictions and separately accepted group-disjoint allocation.
It freezes no seed, grants no source access and creates no real IDs or assignments.
The authorized data holder may be a researcher; this agent receives
only an accepted development-only delivery and permitted metadata. Prospective
IDs/folds establish neither historical continuity nor a fresh holdout.

`ml/uci_lineage.py` checks a future supplied metadata ledger for original-position
coverage, snapshot-bound IDs, declared full-record/predictor digest consistency,
first-occurrence duplicate representatives, retained order/counts and preserved
mixed-native-label groups. It loads no source files, produces aggregate checks
only, recomputes no source-record digests, and cannot authenticate custody. Generated
fixtures exercise these mechanics; no purported research ledger was created.
Focused checks: **118 passed**. Completion guarded regression: **790 passed,
0 failed, 10 skipped, 1 genuine-fitting test deselected**, with zero fitting
attempts/executions. Nine skips require absent trusted synthetic readback inputs;
one requires Windows symlink permission. One existing Starlette warning remains.
Counts overlap and are not summed. Logs retain UTF-8 text with trailing whitespace
trimmed. The prior verification.json is historical evidence bound to its prior
commit; recovery-verification.json binds this updated dossier.

## Current Result semantics: UNRESOLVED

`result-semantics-evidence.json` records exact citations, dates, authority,
PDF pages, retrieved-paper digests, release limitations and contradictions.
The [original authors' 2012 paper](https://eprints.hud.ac.uk/id/eprint/16229/)
and [2014 paper](https://eprints.hud.ac.uk/id/eprint/17994/) concern earlier
feature studies/populations and supply no authenticated numeric Result codebook
for this pinned release. The 2015 creator record, official API and bundled
feature documentation likewise do not establish the missing definition.

[Al-diabat (August 2016), Section 4, PDF p.4](https://www.ijcaonline.org/archives/volume147/number5/aldiabat-2016-ijca-911061.pdf)
assigns legitimate to +1 and phishy to -1.
[Hutchinson, Zhang and Liu (2018), Section 3.1, PDF p.3](https://eudl.eu/pdf/10.1007/978-3-030-00557-3_46)
explicitly assigns the opposite mapping. Both are secondary evidence for the
original dataset's semantics, neither is bound to this archive by an original
codebook receipt, and their contradiction is not resolved by counting papers,
class frequencies, feature correlations or model scores. The existing mapping
is preserved as an unverified implementation assertion. Searches stop at this
source-evidence boundary; no arbitrary mirror is promoted to authority.

## Current researcher-versus-external authority

The approved proposal was read directly (SHA-256 unchanged): Stage 2, PDF p.63,
assigns source acquisition, hashes and provenance capture to the researchers;
Stage 3/Table 4.4, pp.63-65, assigns audit and requires documented semantics,
original IDs, reason-coded attrition and groups before partitioning. The proposal
requires a dated technical deviation and **joint approval for later changes to
a frozen protocol** (p.63). It does not impose a separate custodian signature or
universal adviser signoff for routine technical audit. Its institutional-review
qualification is conditional on actual university policy (p.57), not evidence
that an unnamed external approval is always required. The signed supervision
agreement was checked; no blanket technical-audit signoff clause was identified.

`researcher-authority-matrix.json` is the precise A/B/C distinction:

- **A ? already permitted:** named-source acquisition, provenance/schema/header
  checks, publication review, metadata checks and generated-input regressions.
  The factual `source_manifest.csv` is now materialized from actual existing
  acquisition evidence; its missing class definition is explicitly UNRESOLVED.
- **B ? researcher decisions:** record a consistent prospective preparation,
  native dictionary, grouping/conflict limitations and bounded no-fit scope within
  the approved design. Researchers can be their own data holders; a third-party
  custodian is required only when that party actually controls missing facts or
  access. In-principle P3 agreement does not specify actual original-row membership.
- **C ? explicit joint/external requirements:** later frozen-protocol changes
  and exposure-dependent departures need the prescribed joint deviation process;
  institutional review only where actual policy requires it; third-party source
  facts/access only where those are genuinely held externally. No adviser
  amendment is invented for ordinary schema/hash/join mechanics.

This distinction does not authorize treating the full source as development-only.
The 4,094 legacy cleaned-position IDs have no authenticated original-row bridge;
no permitted original-record slice or accepted prospective scope has been supplied.
Missing class semantics block target construction/partition/admission, not all
label-neutral metadata review. Genuine row processing remains unperformed because
exact allowed row scope and source facts are unresolved, not because every routine
choice needs an outside signature. Existing no-fit/fitting receipt gates remain
unchanged. No research models or genuine lineage/attrition outcomes are claimed.

## Single current authorization request

See **execution-authorization-request.md** for the one actionable request,
minimum required delivery, exact existing D-features receipt boundary, and
controlling evidence. It replaces the older multi-item decision packet in this
live dossier. No request was sent to another person, no approval was presumed,
and no receipt or genuine lineage/attrition ledger was generated.

Current execution commands, test results and artifact digests are in
`reconstruction-verification.json`. Earlier verification receipts retain their
historical commit-bound meaning; they do not bind this updated dossier.

Latest readiness evidence and exact commands are in `execution-readiness-verification.json`;
all older verification files retain their historical commit-bound meaning.

Current source-review and regression evidence is in `semantics-authority-verification.json`.
No application or scientific dependencies were modified; a task-local PDF reader
was used for read-only document verification and removed after use.

Current focused regression: **41 passed, 0 failed, 0 skipped**, with zero fitting
attempts/executions. No code defects were identified or code changes made in this
continuation; no new tests or scaffolding were added. Counts are not summed with
prior runs. No genuine row lineage, attrition or model metrics were produced.

## Current two-branch execution priority

PhiUSIIL-967 now has primary-source label evidence and a matching official ZIP/
56-field header. It is the next no-fit admission priority, independently of UCI-327.
UCI remains 0/10 and its exhausted label/lineage investigations were not repeated.
The single current two-branch decision packet and receipts are under
`../2026-11-18_technical_admission/`; no technical data were pooled, no genuine
rows processed and no fits authorized by that priority decision.

Latest scientific-completion gap and the precise PhiUSIIL delivery boundary are
recorded in `../2026-11-18_technical_admission/scientific-completion-gap.json`.
No new input scope or acceptance was supplied; the existing fitting guard refused
execution. Prior source evidence and test results were reused without another audit.

The latest PhiUSIIL six-file contract/assembly result is recorded in
`../2026-11-18_technical_admission/d-features-delivery-status.json`: independent
population membership and acceptance remain missing; no placeholder delivery
files, original-row inference or scientific results were generated.
