# Email acceptance and CEAS-08 reconciliation packet

Date: November 5, 2026, Asia/Manila. **Metadata audit and decision packet only.**
No option is selected or newly approved. No dataset preparation, assignment
generation, notebook execution, classifier fitting, tuning, calibration or sealed
evaluation was performed. The only new repository files are this report and its
two JSON evidence/preservation supplements.

## 1. Executive determination and authority

**CEAS-08 is an approved named source with a default auxiliary role, not an
automatically approved primary Email member.** Section 4.2.1 expressly permits a
different role when supported by a frozen audit decision. Tables 4.1-4.2 preserve
its native ham/spam semantics and exclude an unapproved primary-pool mapping.
No completed audit/admission approval was found in the inspected repository.

The historical 38,759-record Email manifest includes 17,312 CEAS negative records.
It therefore does not match the default Nazario-positive plus Enron/SpamAssassin
legitimate construction. It cannot be reused unchanged as that default primary
population. A metadata-only non-CEAS projection is mechanically feasible, with
21,447 records, 17,805 supplied groups, intact five-fold coverage and no recorded
crossings. **That is a scenario calculation, not an approved or exported split.**

Two further findings materially narrow the next work:

- All four existing Email raw/clean file pairs are byte-identical and match
  registered/tracked LFS hashes. Current file-level raw-to-clean ordering/value
  identity is stronger evidence than the previous general lineage warning.
- Historical IDs encode rank **after** label filtering; the repaired builder
  encodes cleaned-source position **before** filtering. String equality alone is
  not an identity crosswalk. The assignment manifest has neither native labels
  nor source positions/content hashes with which to resolve this itself.

Authoritative sources, in order:

| Evidence | Authority / precise role |
| --- | --- |
| Approved proposal, `Thesis_Proposal_Documents/Alcover & Orbello_Approved Document Proposal.pdf` | Governs dataset roles and research procedure; SHA-256 `283338c5535c5553e35266f5083a6380e014637e63d42161c659238e257ad1fe`; 155 pages, freshly read in memory |
| Section 4.2.1, PDF p.57; Table 4.1, pp.58-59; Table 4.2, p.60 | Nazario positives after audit; Enron legitimate and explicit SpamAssassin ham; CEAS auxiliary unless frozen audit supports another role; final counts prospective |
| Sections 4.3.1-4.3.3/Table 4.4, pp.63-65 | Provenance, class definitions, screening/attrition, conservative groups, source-confounding analysis, freeze and controlled deviations |
| Section 4.3.4/Tables 4.5-4.6, pp.66-68; Section 4.3.5/Table 4.7, pp.69-70 | Deterministic evidence states and matched Email E1/E2/E3; no learned behavioral or annotation prerequisite |
| `experiments/results/preprocessing/partitions/email_partition_manifest.csv` | Authoritative evidence of the assignments actually recorded, not of source eligibility or scientific approval |
| Historical Notebook 03 source at Git `1a45c53`, cells 15/19 | Explains the legacy four-source construction and filtered-rank identifiers; code existence does not establish approval or exact run lineage |
| Current `ml/notebook_contracts.py:47` and Notebook 03 cells 15/19 | Implements the default three-source construction and cleaned-position IDs; not a completed source/label/group freeze |
| Earlier research decisions/reports and saved experiment manifest | Supporting/historical evidence; do not amend the proposal or approve admission |

Notebook cell numbers in this packet are zero-based JSON indices. Relevant
stable IDs: N03 cell 15 `95feb561`, cell 19 `39163f5c`, cell 40 `407edb97`;
N04 cell 35 `a1617aaa`; D9 config cell `d9-required-config`.

**Qualification to earlier wording:** N03 cell 15's comment says
"paper-required CEAS exclusion." The paper establishes a default auxiliary role
with an audit-supported exception, not an unconditional lifetime ban. The comment
and earlier blanket amendment/exclusion interpretations are not governing
authority. They are preserved, not edited in this documentation-only task.

## 2. Governing population versus historical construction

| Source | Approved default use | Historical implementation | Current implementation |
| --- | --- | --- | --- |
| Nazario | Audited phishing-positive content | All supplied Nazario rows -> target 1 | Requires native label 1, maps to target 1, subject/body schema validated |
| Enron | Audited legitimate content | Native label 0 -> target 0 | Same numeric assumption, pending primary class-definition evidence |
| SpamAssassin | Explicit ham may support legitimate pool; spam separate | Native label 0 -> target 0 | Same numeric assumption; native 1 excluded, not relabeled phishing |
| CEAS-08 | Original semantics; auxiliary hard-negative/source analysis unless frozen audit supports another role | Native label 0 -> target 0 in the primary pool | Not consumed by the default primary builder |

The approved source family is the Zenodo curated Email release, repository
8339691. A DOI/repository reference in the paper is not proof of local acquisition
date, applicable license/access conditions or the numerical class definition of
the particular CSV snapshot. `verified_label_semantics.csv` explicitly leaves all
four Email source meanings **pending provenance verification / do not map yet**.
This conflicts with treating the numeric assumptions in historical/current code
as already scientifically verified. No labels were changed here.

### Current payload and historical attrition evidence

All eight Email files were opaquely hashed; no source CSV records were parsed.
Each raw/clean pair has the same SHA-256, also matching the historical inventory
and each index LFS object. Full fingerprints are in `metadata_evidence.json`.

| Source | Historical raw count = recorded cleaned count | Native-0 / native-1 audit counts | Historical selected records | Native-1 records outside ham selection |
| --- | ---: | --- | ---: | ---: |
| CEAS-08 | 39,154 | 17,312 / 21,842 | 17,312 target 0 | 21,842 |
| Enron | 29,767 | 15,791 / 13,976 | 15,791 target 0 | 13,976 |
| Nazario | 1,565 | 0 / 1,565 | 1,565 target 1 | Not a ham source |
| SpamAssassin | 5,809 | 4,091 / 1,718 | 4,091 target 0 | 1,718 |

Recorded arithmetic reconciles: 76,295 raw Email rows minus 37,536 unselected
native-1 rows from CEAS/Enron/SpamAssassin = 38,759 historical members. Under the
default non-CEAS scenario, 37,141 source rows minus 15,694 non-ham code-1 rows
from Enron/SpamAssassin = 21,447. These are **historical counts and scenario
arithmetic**, not final Stage 3 eligible counts or verification of code meanings.

The cleaning log records zero Email removals, filling missing subject/body cells
with empty strings (CEAS 28, Enron 198, Nazario 4, SpamAssassin 17), retaining
extreme-length observations and preserving native labels. The exact-duplicate
audit reports zero complete-row duplicates for these sources. Notebook 02's
`drop_duplicates` cell 18 targets technical datasets, not Email; its Email
validation checks missing cells/nonempty datasets, not a complete eligibility
audit. Empty-string serialization does not establish evidence availability.

**What lineage is established:** byte-identical raw/clean files imply identical
record values/order when decoded with the same CSV rules; no filtering/reordering
is visible between those paired current files. This can support a documented
identity-by-record-position transform for these exact snapshots. It does not
recover upstream message IDs, source acquisition history, historical filtered-rank
positions or a source-backed eligibility decision. A CSV record index is not a
physical text-line number because quoted fields can contain newlines. Preserve
source-native identifiers where available; otherwise document frozen-file
record locators without fabricating identifiers.

No per-original-ID screening log, exclusion reasons, duplicate families,
raw/clean/legacy-ID crosswalk, reconciled Stage 3 attrition table or scientific
freeze was found. Existing aggregate logs are useful partial evidence and should
be retained rather than replaced or described as nonexistent work.

## 3. Fresh historical assignment audit

Input schema is exactly `observation_id,source_dataset,target,group_id,partition,
cv_fold`. File SHA-256:
`38c87c522da47fea6f8f584c2e487af73d89502e9db3130f6298006829241ae4`.
Only these metadata fields were parsed. Targets here are supplied assignment
labels, not test predictions or outcomes. Detailed aggregate results and ID-set
hash conventions are in `metadata_evidence.json`; no individual assignments are
exported.

| Source | Records | Groups | Recorded target | Recorded ID range |
| --- | ---: | ---: | --- | --- |
| CEAS-08 | 17,312 | 3,796 | All 0 | `CEAS-08::0` through `CEAS-08::17311` |
| Enron | 15,791 | 15,472 | All 0 | `Enron::0` through `Enron::15790` |
| Nazario | 1,565 | 1,409 | All 1 | `Nazario::0` through `Nazario::1564` |
| SpamAssassin | 4,091 | 924 | All 0 | `SpamAssassin::0` through `SpamAssassin::4090` |
| Total | **38,759** | **21,601** | 1,565 positive / 37,194 negative | Unique, contiguous within each source |

Fresh metadata checks found:

- 38,759 unique IDs; zero duplicated IDs or identical assignment rows.
- Zero group crossings between development/calibration/test, zero development
  group crossings between folds, zero groups shared by sources, zero mixed-target
  groups. Zero group IDs shared between the CEAS and non-CEAS slices.
- All five development folds present, both classes in every fold and every
  partition. CSV fold values are `1.0` through `5.0`; reserved roles have blank
  folds. No invalid/missing development folds or nonnull reserved folds found.
- 2,729 multirow groups contain 19,887 records; largest group has 462 records.
  CEAS accounts for 1,940 multirow groups / 15,456 such records. These are group
  sizes, not counts of proven exact duplicate messages.

### Source, role and fold composition

| Source | Development | Calibration | Test |
| --- | ---: | ---: | ---: |
| Nazario | 1,095 | 235 | 235 |
| CEAS-08 | 12,118 | 2,597 | 2,597 |
| Enron | 11,053 | 2,369 | 2,369 |
| SpamAssassin | 2,863 | 614 | 614 |
| Historical total | **27,129** | **5,815** | **5,815** |
| Non-CEAS projection | **15,011** | **3,218** | **3,218** |

| Development fold | Nazario positive | CEAS negative | Enron negative | SpamAssassin negative | Historical total | Non-CEAS total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 219 | 2,424 | 2,211 | 573 | 5,427 | 3,003 |
| 2 | 219 | 2,424 | 2,211 | 573 | 5,427 | 3,003 |
| 3 | 219 | 2,424 | 2,211 | 573 | 5,427 | 3,003 |
| 4 | 219 | 2,423 | 2,210 | 572 | 5,424 | 3,001 |
| 5 | 219 | 2,423 | 2,210 | 572 | 5,424 | 3,001 |

The non-CEAS scenario has 21,447 records / 17,805 groups, 1,565 positive /
19,882 negative (7.2971% positive, versus 4.0378% historically). Development has
1,095 positive / 13,916 negative; each reserved partition has 235 / 2,983.
Both classes remain in every validation fold and its four-fold training
complement. No assignment value was changed, regenerated or saved.

### Implemented historical grouping and its limits

N03 cells 22-30 normalize lowercase/trimmed/collapsed-whitespace body text and
sender strings; union records sharing a nonempty normalized sender or a
normalized-body SHA-256; reconcile transitive components; number sorted
union-find roots as `email_group_NNNNNN`. Empty bodies/senders do not create a
common empty-value group. These rules are present in historical and current
source. They do not implement documented near-duplicate MinHash/SimHash,
template/campaign relationships or complete source-permitted domain controls.
The assignment CSV contains group labels only, without edges, body hashes,
sender availability or a versioned accepted policy. The exact historical
execution/source version cannot be authenticated from the group labels alone.

Cells 41-42 allocate whole groups within source/target strata toward 70/15/15
with largest-group-first deficit allocation and seeded tie ordering. Cell 51
balances source/target group rows over five development folds, seed 42. This is
a custom group allocation recipe, not a call to sklearn StratifiedGroupKFold.
The historical first-source/first-target reduction is safe from composition
loss only for the observed single-source/single-target groups; current cell 41
rejects mixed composition. Current cell 40 separately stops without a documented
group freeze. Merely filling its reference string would not establish one.

No recorded crossings is verified. **No unrecorded duplicate/campaign leakage**
is not verified. Zero cross-source group labels cannot establish that no
cross-source near duplicates exist. Complete-row duplicate counts do not replace
normalized-content families or a reconciled relationship manifest.

### Historical exposure

Historical N05 cell 26 (`07ce0ca0`) explicitly predicts/evaluates its test role;
saved holdout metrics, comparisons, predictions and plots exist. These files
were checked for existence/opaque preservation identity only; their contents or
performance values were not used. Prior outcome access means the historical
holdout cannot be called prospectively untouched. Dropping CEAS, changing an ID
or reusing the remaining membership does not reseal it or erase researcher
knowledge. Exact human exposure/influence needs a custody/deviation record.

## 4. Assignment compatibility and identity decision

**Full historical manifest as-is:** incompatible with the default primary
population because it includes CEAS. `capture_population` permits the current
three primary sources; `validate_metadata_alignment` at
`ml/notebook_contracts.py:165` requires exact IDs and source/target/group/role/fold
agreement. Filtering is a new documented population version, not permission to
pass a mismatched full manifest or silently relax an exact-join check.

**Frozen projection with original values:** mathematically compatible with
recorded isolation and five-fold class coverage. Because recorded groups are
source-disjoint, excluding CEAS removes 3,796 whole groups and does not split a
recorded retained component. Retained legacy IDs, group names, roles and folds
can remain unchanged if that reuse is accepted. The original manifest must
remain immutable; a future versioned selection/crosswalk would refer back to it.
Scientific reuse is still conditional on identity, source/label, relationship
coverage and exposure acceptance. This packet does not authorize that export.

**Reconstructing through current N03:** not a safe substitute for projection.
At `1a45c53`, cell 15 filters source label 0 before cell 19 applies
`groupby(source_dataset).cumcount()`. Current `build_email_population` enumerates
all cleaned-source rows before filtering and constructs the same-looking
`source::position` string. For Enron/SpamAssassin, filtered rank and source
position need not identify the same record. Nazario ranks coincide only under
the same unchanged all-positive ordering. No actual conflicting record was
located here because payload rows were not read; the convention conflict itself
is verified and requires a crosswalk, not an assertion that every ID is wrong.

The shared `capture_population` validator checks a unique nonempty observation
ID and a unique source/position pair independently; it does not require the ID
string to equal `source::position`. A documented, verified legacy ID alongside
its actual cleaned-source position can therefore be a mechanically viable
preservation route without renaming historical IDs. That convention still needs
acceptance and consistent handoff metadata; the default builder's freshly
generated strings cannot be assumed to supply the crosswalk.

Changing group input membership/order can also renumber root-based group IDs.
Replaying the legacy allocator consumes different random sequences when strata
are removed and may change roles/folds, even with seed 42. No such replay was
performed. Retaining explicit supplied values avoids these mechanical changes
only after identity/reuse acceptance; it cannot repair missing group evidence.

**Historical LR:** preserve all original metrics, coefficients, predictions,
thresholds and manifests as the original population/version. A new primary pool
changes training examples, prevalence, weights, vocabulary and interpretation;
old aggregate results cannot simply be relabeled, scaled or claimed as the new
study. E1/E2/E3 must be matched within each future accepted population. No-fit
projection statistics are not new classifier results.

## 5. CEAS decision matrix - all options Pending

| Option | Protocol/approval route | Size, grouping and folds | Comparability/leakage/claim consequence |
| --- | --- | --- | --- |
| **A. Keep CEAS outside primary experiments** | Follows the proposal's default role; document researcher choice and eligibility/assignment reuse. This does not itself require a replacement study or methodological amendment. No choice is made here | Historical non-CEAS scenario: 21,447 rows, 17,805 groups; dev/cal/test 15,011/3,218/3,218; five folds retained by projection. No new final eligible count guaranteed | Preserves supplied values if identity crosswalk/group reuse accepted. Prevalence becomes 7.2971%; historical 38,759-row LR is a separate analysis. Source-target confounding remains. Test remains historically exposed |
| **B. Retain CEAS through the explicitly approved amendment route requested for review** | Requires dated rationale, precise admissible native classes, primary class-definition evidence and explicit researcher/adviser decision. The paper already allows an audit-supported different role; CEAS admission alone does not prove an amendment is mandatory. Adviser determines whether the proposed role fits that clause or changes methodology. An amendment is not adopted by this packet | If exactly the historical native-0 cohort is accepted: 38,759 rows, 21,601 groups; 27,129/5,815/5,815 and existing five folds. Different screening/inclusion changes these numbers and needs separate compatibility assessment | No mapping spam to phishing. Full manifest could be a candidate for reuse only after provenance, ID, group and exposure acceptance. Historical counts/results do not validate admission; retrospective approval cannot establish prospective sealing |
| **C. Separate CEAS sensitivity/source or external evaluation** | Auxiliary source/hard-negative analysis is already contemplated; exact estimand, source classes, independent-use/overlap controls and timing need a frozen protocol. A new external evaluation claim or changed label role needs applicable adviser approval | Default-primary scenario as A, plus a separate CEAS analysis. Existing assigned CEAS slice is 17,312 negative-only, split 12,118/2,597/2,597; the remaining 21,842 native-1 records have no rows in this Email assignment manifest | Negative-only data can support declared false-positive/specificity diagnostics after label verification, not a standalone two-class phishing AP/ROC/recall comparison. Entire CEAS native ham/spam is not phishing/legitimate. Adding verified ham as a sensitivity pool changes prevalence/population; preserve matched E1/E2/E3 within each pool. Already used CEAS records are not fresh external data |

For B, Section 4.3.1's ordinary deviation procedure includes confirming sealed
test non-access. That assurance cannot truthfully be supplied retroactively for
these historical artifacts. Researchers/adviser must define any prospective
development/exploratory use and claim limitations explicitly; an approval
signature cannot repair missing provenance or erase exposure.

For C, no CEAS-only binary handoff is proposed: current Email contracts require
both classes. Do not weaken them to admit the negative-only slice or repurpose
native code 1 as phishing. No extra CEAS records are assumed eligible/available
for a new purpose merely because the source file exists. Cross-source content
overlap and pre-exposure must be assessed before any external-generalization
claim. A separate source file is not proof of an independent evaluation set.

## 6. Scientific evidence register

VERIFIED = bounded checked fact; PARTIAL = some supporting evidence but an
acceptance element is absent; MISSING = no matching record found in the searched
repository; CONFLICTING = incompatible claims/contracts. No claim is made about
documents that may exist with the researchers outside this checkout.

| Requirement | Evidence path / location | Status | Minimum missing item / owner |
| --- | --- | --- | --- |
| Governing source roles | Approved Section 4.2.1/Tables 4.1-4.2 | VERIFIED default and conditional exception | Researchers record A/B/C disposition; no automatic selection |
| Current source and cleaned payload identities | Eight paths and hashes in `metadata_evidence.json`; audit inventory and index LFS pointers | VERIFIED bytes/identity | Source custodian supplies acquisition/access/license and schema provenance; hashes do not prove those |
| Acquisition/access/license/snapshot record | `experiments/results/audits/dataset_inventory.csv`; Nov.4 `dataset_evidence.json` has null access/license/snapshot fields | PARTIAL hashes/counts; MISSING acquisition/license evidence | Vera/source custodian: repository/release locator, actual acquisition date, applicable terms and accepted snapshot identifier. File mtime or experiment `created_utc` is not an access date |
| Numerical native label semantics | `verified_label_semantics.csv` versus current/historical mappings | CONFLICTING readiness assertions; Email entries explicitly pending | Source-backed CSV class definitions and accepted mapping preserving spam/other classes; researchers verify |
| Raw-to-clean current lineage | All four pairs byte-identical | VERIFIED file identity; PARTIAL original-ID/run lineage | Document same-parser positional identity and source-native IDs if present; obtain legacy rank-to-source-position crosswalk |
| Screening and attrition | `cleaning_log.csv`, `validation_results.csv`, `label_distribution.csv`, `exact_duplicates.csv` | PARTIAL aggregate evidence | Original-ID exclusions/reasons and reconciled source/cleaned/eligible/split counts; custodian supplies, Dhanwil checks |
| Duplicate/conservative group coverage | N03 cells 22-30; supplied `email_partition_manifest.csv`; audit sender summaries | PARTIAL exact sender/body recipe and recorded isolation | Accepted normalized-content/near-duplicate/template/campaign/source-permitted relationship records and limitations; no invented thresholds |
| Group/partition/fold integrity | Supplied manifest metadata and fresh aggregate checks | VERIFIED on recorded groups | Researcher acceptance of reuse/coverage/custody and new version linkage; no assignment generation |
| Historical assignment/current ID linkage | `1a45c53` N03 cell 19 versus `ml/notebook_contracts.py:47` | CONFLICTING identifier semantics | Explicit one-to-one legacy/current/source-row map with metadata-only checks; do not join by ID string alone |
| Source-label confounding | Manifest source-by-target table | VERIFIED source determines supplied target | Declare source-only, normalized-format and source-stratified plan; later authorized development analyses; no source-independent claim |
| Historical test exposure | N05 cell 26 and existence of saved holdout artifacts | VERIFIED historical evaluation path/artifacts; PARTIAL custody history | Researchers/adviser define exposure-aware use/claims; no resealing |
| Deterministic rule/codebook freeze | `ml/se_brl/codebook.v0.1.0.json:7` pre_freeze; N04 cell 35 guard | PARTIAL candidate rule/test infrastructure; no accepted freeze | Vera/specification owner + researchers: twelve rules/exclusions, original-field locators, language, trust/reference and partial availability; no human annotation requirement |
| Availability provenance | `email_grouping_summary.csv`, schemas, `email_evidence_availability` at `ml/notebook_contracts.py:186` | PARTIAL; Enron has no sender field; missing link/identity evidence remains unavailable | Per-record evidence opportunity/availability metadata; document empty versus unavailable without fabricating URL lists |
| Ordered conventional feature dictionary | Historical experiment manifest lists only `model_text`; current D9 config has all three required settings None | PARTIAL historical lexical choice; MISSING current accepted dictionary | Dhanwil formalizes accepted names/types/order/derivations; researchers accept feature eligibility and preprocessing; exclude labels/provenance/group/role/fold |
| Development-only delivery boundary | `ml/development_experiments.py:292`; `ml/experiment_integration.py:61`; `ml/branch_preparation.py:53` | VERIFIED software guards; MISSING real delivery | Custodian supplies named hashed development-only inputs/assignment linkage. Generic branch loader reads full selected payloads before filtering and is not a strict no-read barrier |
| Research experiment settings | Table 4.8/4.9, historical `experiment_manifest.json`, current decision drafts | PARTIAL approved families/ranges; budgets/nesting/calibration/selection freeze unresolved | Researchers freeze settings before comparative research fits. Historical seed 42/LR balanced/sigmoid/F1 and synthetic seed 17/eight trees are not accepted new settings |

Searched `experiments/`, `docs/` and `ml/` for the Table 4.2/4.4 records and
equivalent supporting evidence. Exact named `source_manifest.csv`,
`label_mapping.yaml`, `screening_log.csv`, `dataset_attrition.csv`,
`duplicate_groups.csv`, `group_manifest.csv`, `availability_matrix.csv` and
`split_manifest.csv` were absent. The existing partition manifest and aggregate
logs partially cover some of those roles; filename absence alone is not proof
that all corresponding work is missing. No completed approval/equivalent
acceptance record was identified in the inspected material.

The historical Email preprocessed and feature hashes are recorded in
`experiments/results/experiments/input_manifest.csv`, but matching historical
payloads/current versioned handoffs are absent. `experiments/runs` does not
exist. Those reference strings cannot authenticate the currently repaired input
population or establish a completed feature dictionary/rule freeze.

## 7. Decision/approval register

All entries below are **Pending**. These are concrete acceptance requests, not
newly imposed scientific requirements or edits to existing H1-H12 decisions.

| Decision | Researcher/adviser action | Completion evidence |
| --- | --- | --- |
| E-POP | Researchers select A/B/C scope using the approved default/exception; adviser determines amendment/deviation route for changed methodology or new claims | Dated role and native-class/eligibility decision, intended population version, rationale and sign-off; no chosen option prefilled |
| E-LABEL/SOURCE | Custodian supplies source evidence; researchers verify numeric classes/access terms | Source cards/release documentation, native label mapping and license/access record linked to exact hashes; evidence cannot be invented by approval |
| E-ID | Dhanwil validates supplied positional/rank crosswalk; researchers accept identity convention and historical reuse | One-to-one original/cleaned/legacy/current identifiers, exact snapshot/parser linkage and coverage/mismatch report; retain both ID conventions explicitly |
| E-GROUP/REUSE | Researchers accept reconciled relationships/limitations and supplied-assignment reuse; adviser for scientific deviation | Frozen policy and relationship/group evidence; approved immutable full-manifest reference or versioned projection; no regenerated assignments |
| E-ACCESS/EXPOSURE | Custodian/researchers specify development-only custody; adviser resolves confirmatory/exploratory scope | Named allowed files/fields/hashes, prohibited reserved-payload access, prior-exposure disclosure and claim scope |
| E-FEATURE/RULE | Specification owner/researchers freeze the existing deterministic interpretation and predictor eligibility; adviser only if meaning/scope changes | Ordered dictionary plus twelve-rule/language/locator/availability version and conformance criteria; no ground-truth annotation or transformer prerequisite |
| E-EXPERIMENT | Researchers/adviser as applicable freeze comparative training/selection/calibration/benchmark settings | Versioned ranges/budgets/nesting/seeds/metrics/score/calibration/equivalence/efficiency policy before research fits; not necessary to invent now for a metadata-only no-fit check |

Record naming, hashing, strict joins, immutable writers and validation mechanics
are implementation details within an unchanged approved protocol. Adviser
approval is not a substitute for missing facts and is not automatically required
for every routine metadata check. All earlier decision drafts are preserved.

## 8. Minimum authorization gates for no-fit Email preparation

**Gate 0 - lineage-only metadata reconciliation (smallest next step).** Supply a
text-free development crosswalk for the existing four-source historical IDs,
including source snapshot/hash, source CSV record position, native label,
historical filtered rank/ID and supplied group/role/fold. Investigate source
meaning from documentation. Report missing/ambiguous/duplicate links; do not
change assignments or derive new roles. This investigation can proceed without
choosing A/B/C or freezing model search/calibration and does not itself approve
CEAS for primary use. Body text and reserved prediction files are unnecessary.
No such crosswalk was produced or source rows parsed in the present audit.

**Gate 1 - source/population/assignment validation without feature extraction.**
Before future real preparation, researchers accept the selected role/population,
source terms/native labels, current file/record lineage, conservative groups and
reuse/exposure policy. Custodian provides the explicitly permitted development
metadata/payload delivery and authoritative expected ID universe. Dhanwil then
checks exact cardinality, coverage, targets, one-to-one source positions/groups,
supplied roles/folds, missing/extra/conflicting records and hashes. Resolve any
identity/group discrepancy before proceeding; no automatic regroup/repartition.

**Gate 2 - no-fit dataset-to-feature verification.** Add the accepted ordered
predictor dictionary and deterministic behavioral rule/language/original-field
locator/availability specification. Run only the authorized development delivery
through pure transformations and shared validators. Missing sender/identity/link
evidence stays unavailable; no synthetic negative evidence. Do not fit a
vectorizer, imputer, scaler, classifier or calibrator. Verify exact observation
alignment, feature types/order, support/availability consistency, evidence
traceability, both classes and five existing folds. A reference string is not an
acceptance record. N04's Email freeze guard and D9's required settings are not
bypassed.

For a later authorized export, preserve fixed existing handoff paths beneath a
fresh accepted `experiments/runs/<run_id>/data/processed/features/development/`:
`email_development.csv`, `email_sebrl_features.csv`,
`development_input_manifest.json`. Exclusive creation, hash verification and
complete-bundle checks remain mandatory. This packet creates no run directory
or handoff. The UCI supplied-assignment API is not an Email implementation and
must not be misused. A development-only Email consumer may need a bounded
mechanical addition after input/identity acceptance; the generic full-payload
notebook loader must not violate a development-only no-read authorization.

**Gate 3 - model experiments, later and separate.** Freeze remaining model/search/
calibration/selection settings and obtain research-fit authorization. Then use
the verified genuine adapters. Final numeric risk thresholds or all pending H
items are not blanket prerequisites for Gate 0/1. No-fit authorization does not
permit fitting learned preprocessing. This task authorizes documentation only.

Acceptance for the first future no-fit check: a dated authorization names its
gate and immutable inputs; zero ID/label/group/role/fold disagreements; no
unapproved source/class or reserved payload; unchanged supplied assignments;
all failures produce no misleading complete output; expected masks/evidence and
feature ordering agree with the accepted specification when Gate 2 is included;
all historical artifacts stay byte-identical. Stop on an unresolved scientific
or identity conflict rather than weakening checks.

## 9. Updated D1-D16 position

No software implementation status is promoted by this audit. Previous 977 Python,
25 frontend and 275 static-cell results are historical checkpoint evidence,
**not rerun here**. No tests that fit even synthetic models were executed.

| Task | Engineering/scientific/empirical position after this audit |
| --- | --- |
| D1 | PARTIAL: default CEAS role/conditional exception now precisely reconciled; option/reuse decisions Pending |
| D2 | PARTIAL: current raw/clean Email byte identity verified; legacy rank/source-position bridge and accepted no-fit delivery missing |
| D3 | PARTIAL: fresh source/role/fold/ID/group metadata and scenario counts verified; native semantic/access/eligibility/attrition acceptance incomplete |
| D4 | BLOCKED scientifically: recorded isolation verified; full relationship coverage, reuse/custody and exposure claims unresolved |
| D5 | PARTIAL: canonical candidate rules unchanged; operational freeze/language/locator/availability decisions Pending |
| D6 | PARTIAL: metadata feasibility established for a non-CEAS projection; no actual dataset-to-feature check or approved crosswalk |
| D7 | PARTIAL: source-target determinism, ID convention conflict and exposure documented; unrecorded duplicate/source shortcut controls unresolved |
| D8 | Prior engineering verification retained; no software suite rerun for this documentation audit |
| D9 | Existing strict handoff/loader engineering retained; real Email handoff absent and acceptance blocked |
| D10 | Genuine adapters synthetically verified previously; research fits remain BLOCKED; none run here |
| D11 | DEFERRED; no transformer or behavioral annotation requirement introduced |
| D12 | Metrics infrastructure retained; real calibration/predictions/threshold evaluation blocked |
| D13 | Synthetic CV/ablations retained; new research comparisons blocked; metadata projection is not an ablation result |
| D14 | Audit hashes/scenario/evidence packet reproducible; final accepted source/model/environment freeze incomplete |
| D15 | Decision-ready methodology/limitations evidence improved; no new classifier-performance or source-independence claims |
| D16 | Final scientific/system freeze BLOCKED; historical work preserved and technical handoff updated |

## 10. Exact next technical task

**Reconcile the historical development IDs against source-record positions using
a custodian-supplied, text-free lineage crosswalk, with all four source roles
retained as audit metadata and no A/B/C selection implied.**

Vera/source custodian provides snapshot/hash, source record position, native
label and legacy ID linkage. Dhanwil validates unique/exhaustive ID joins and
unchanged supplied groups/roles/folds, reports disagreements and separates the
three-source and CEAS membership views in memory. If the crosswalk does not
exist, request exactly this metadata export/lineage reconstruction authorization;
do not guess positions from filtered IDs or request the entire thesis. No raw
email body or test outcome is needed. This is a proposed future task, not
executed by this packet.

## 11. Verification, preservation and handoff

Initial checkout main/`6bded57d38e9b83ba718d7795b97e2130128c23f`, upstream
`origin/main`; 24 unstaged tracked paths, 70 untracked files, none staged.
`origin` remains `https://github.com/LichSavant/Thesis_Protoype_Test.git` and
`se-brl` remains `https://github.com/LichSavant/CS4101-Thesis2-SE-BRL.git`.
No live GitHub state was queried or synchronized.

Read-only Git used `GIT_OPTIONAL_LOCKS=0`; status disabled LFS filters. Fresh
294-file SHA-256 baseline includes current tracked/untracked research/software,
all experiments/database files, Git index/config, and the preceding completion
packet. Final comparison is recorded in `preservation.json`: no pre-existing file
changed or disappeared; only the three new documentation files were added.
Historical datasets, partitions, metrics, predictions, plots, coefficients,
manifests, notebooks, source code, decision drafts and application database are
unchanged. Final status is 24 unstaged tracked / 73 untracked / zero staged;
same branch/HEAD/upstream/remotes. The existing `.pytest_cache` permission warning
and dataset LFS status are left unchanged. Unsaved editor buffers were not read.

Audit operations: pure-Python metadata CSV counters/schema/ID/fold/group checks;
in-memory non-CEAS/CEAS scenario summaries; opaque SHA-256/LFS comparisons;
JSON/source inspection of notebooks (never cell execution); direct proposal text
extraction; read-only Git history/status; scoped artifact/schema searches. No
dataframe/scientific environment, dependency installation, feature/preprocessing
API execution, training, tests, web retrieval, staging or repository sync was
needed. Opaque preservation hashes are not interpretation of held-out outcomes.

Companions: `metadata_evidence.json` contains only aggregate assignment/scenario,
source fingerprint and evidence facts; `preservation.json` contains baseline and
final hashes/change accounting. Neither is an accepted source or split manifest.

**Context for ChatGPT:** Nov.5 Email audit only, main/6bded57, no Git mutation.
CEAS default auxiliary with an explicit frozen-audit exception; no option chosen.
Historical manifest 38,759 includes 17,312 CEAS negative records/3,796 groups.
Non-CEAS scenario 21,447/17,805 groups, dev/cal/test 15,011/3,218/3,218;
both classes/five folds intact, no recorded cross-source/group crossings.
Current four Email raw/clean pairs are byte-identical and LFS-matched. Legacy
IDs were post-filter ranks; repaired IDs are pre-filter source positions, so a
crosswalk is required before joining assignments. Source semantics/license/
screening/group/rule/dictionary/custody acceptance remains incomplete. CEAS-only
legacy slice is negative-only and previously evaluated; do not call it a fresh
external phishing benchmark. Next: text-free development lineage crosswalk
verification, not training or partition regeneration. All 294 baseline files
preserved; this packet creates documentation only. D10 remains blocked, D11
deferred; previous test pass counts were not reproduced in this audit.
