# B. Prospective identity, grouping and partition protocol candidate

**Proposal for researcher/adviser review, version rp-candidate-0.1. All choices
below remain Pending. No identities, groups, partitions or folds were generated.**
This is a new version of the approved-source data workflow, not a replacement
dataset or an assertion that old records can be relinked. Governing provisions:
proposal Section 4.2.1/Tables 4.1-4.2, PDF pp.57-60; Sections 4.3.1-4.3.3/Table
4.4, pp.63-65; matched development evaluation in Section 4.3.5, pp.69-75.

## B1. Population decision

| Alternative | Review decision and consequence |
| --- | --- |
| P-A: default primary | Audited Nazario phishing positives plus Enron legitimate/explicit SpamAssassin ham. CEAS remains auxiliary. Follows the proposal default; final counts await screening. The historical non-CEAS 21,447 is contextual, not a new frozen size |
| P-B: CEAS admitted | Specify exact native classes and scientific purpose; source-backed labels and a frozen audit admission record required. The proposal allows an audit-supported different role; adviser determines whether this particular change fits that clause or needs amendment. Explicit amendment route requires its own approval; none adopted |
| P-C: CEAS separate | Specify source/negative-only/sensitivity estimand and permitted roles independently. The historical CEAS slice is negative-only and previously evaluated; neither the slice nor native ham/spam becomes a fresh phishing benchmark |

No option is selected. Keep native spam/other classes distinct. No numerical
mapping is accepted merely because current code implements it. Source custodian
must provide acquisition/license/schema/class definitions linked to snapshots.
The [existing CEAS matrix](../2026-11-05_email_acceptance/README.md) supplies
historical membership consequences; those tables are not repeated here.

## B2. Prospective identity and audit receipts

Recommended construction for review:

1. Retain each immutable source snapshot and SHA-256, source locator/terms/access
   record, parser version/encoding/options and acquisition/import receipt.
2. Preserve the native source-record identifier if supplied and trustworthy. If
   absent, record the CSV record index at ingestion **before filtering**, with
   the immutable snapshot/parser and ingestion event. Quoted multiline CSV
   records are not physical lines. These are prospective provenance locators,
   not retrospective proof of a legacy match.
3. Form a versioned canonical ID from SHA-256 of canonical JSON containing the
   source namespace, snapshot identity, locator-kind/version and original record
   token/verified record locator. Use the full digest; exclude labels, groups,
   partition roles, content, and eventual model output from this identity key.
4. Persist raw -> cleaned -> screened -> feature-row linkage at each transform,
   including unchanged records and exclusion reasons. Never renumber retained
   records after filtering. Equal canonical IDs with differing provenance are
   collisions and stop the affected export; repeated import of the exact same
   provenance is an explicit duplicate ingestion event, not a second identity.
5. Keep content-normalization hashes separate as duplicate relationships. They
   may intentionally identify several originals and are not unique record IDs.

Required metadata outputs: source manifest; parser/transform versions; immutable
per-record ingestion/lineage and screening records; counts/attrition; relationship
edges and group membership; supplied assignments and provenance hashes. Use
restricted metadata storage for sensitive native IDs; public reports contain
aggregate evidence. Do not invent missing upstream identifiers or backdate a
new receipt as historical evidence. Existing paired raw/clean byte identity can
be documented as a current transform fact after authorized verification, but
does not recover old post-filter ranks.

## B3. Group relationship policy candidate

Compute relationships without target/model outputs. Proposed policy:

- Exact normalized subject/body artifact hash plus nonempty normalized-body
  hash as a conservative relationship; reuse the existing N03 lowercase/trim/
  collapsed-whitespace normalization as `dup-normalization-candidate-v1`.
  Propose canonical JSON of `[normalized_subject_or_null,
  normalized_body_or_null]` for the exact artifact, preserving null versus known
  empty. Hash that UTF-8 canonical JSON together with the normalization version;
  the nonempty body relationship uses its separate versioned hash. Reject
  ineligible empty-content records before grouping; empty fields never form a
  universal family. These concrete field/null choices need acceptance.
- For complete exact duplicates with consistent source-backed classes, propose
  one canonical record chosen by smallest canonical ID, preserving all aliases
  and reason-coded attrition. Conflicting classes on indistinguishable artifacts
  stop for source-label audit; do not majority-vote or relabel. An unresolved
  conflict-family exclusion must be predeclared and logged, not outcome-driven.
- Near-duplicate candidate from the existing Pending H5 recommendation: five-word
  shingles, 128-permutation MinHash, candidate Jaccard threshold .90, seed 42.
  This is a **provisional configuration for review**, not an approved/validated
  similarity threshold. Propose consecutive five-token shingles from whitespace-
  separated normalized body tokens; fewer than five tokens bypass near matching
  with an explicit short-text limitation while exact/other accepted edges remain.
  Propose 32 bands x 4 rows for deterministic LSH retrieval, then verify exact
  shingle Jaccard >= .90 for retrieved pairs before adding an edge. Pin the
  implementation/signature/hash ordering and seed before execution. LSH retrieval
  has false negatives: report this limitation, do not claim exhaustive near-
  duplicate detection, and do not tune the index/threshold from model outcomes.
- Add independently available thread/campaign identifiers and source-permitted
  domain/identity relationships with documented provenance. Existing sender
  equality is a reviewable conservative edge, not a campaign label. Missing
  campaign evidence stays missing. Source name is an audit/stratification field;
  putting an entire corpus in one group solely by source can make binary CV
  infeasible and is not proposed as an automatic rule.
- Reconcile all accepted edges by connected components; preserve the edge types,
  uncertainty and aliases. Keep near duplicates as separate observations inside
  their common group unless a distinct exclusion rule is approved. Hash sorted
  canonical members plus policy version for a stable component ID, rather than
  numbering union-find roots. Verify collisions and one-to-one membership.

Mixed-target groups can be legitimate related artifacts and must retain their
full source-by-target composition. Distinguish them from a contradictory exact
duplicate label. Report group sizes/giant components, source overlap, missing
relationships and limits. No campaign/source independence claim follows merely
from successful graph construction. Specification owner and researchers accept
each edge/normalization/threshold choice before implementation/data execution.

## B4. Prospective partition/fold recipe candidate

Propose 70/15/15 development/calibration/final-evaluation allocation, retaining
the historical ratio convention and the paper's 70% development scope. The
new allocation itself needs approval. Never alter existing assignments.

Use whole accepted groups and source-by-target **count vectors**, not the old
first-source/first-target reduction. A concrete deterministic candidate is:
order groups by descending record count, then stable hash of proposed seed 42
and group ID; greedily choose the role minimizing the sum of squared normalized
source-by-target count deviations from its target allocation across all roles,
with equal stratum weights and fixed role-order tie-break. Use each stratum's
total count (at least 1) as denominator. Apply the same policy within development
with five target fractions of 1/5 and fixed fold order 1-5. Log the objective,
tie ordering, group composition and resulting deviations. This algorithm and
seed are recommendations, not adopted code or a promise of exact balance.

Check feasibility before accepting any manifest: both classes in every required
partition, every development fold and training complement; no group crosses
roles/folds; no missing/duplicate/unexpected IDs; all admitted records covered;
null reserved folds; source composition/giant components documented. If the
fixed recipe is infeasible, stop for a documented protocol decision. Do not
shuffle repeatedly, split a group, change labels or choose a seed to improve
class/model results. Allocation can use labels for stratification only, never
to establish identity or duplicate relationships.

Reserve calibration from candidate selection. Before its use, specify a fixed
group-disjoint probability-fit/threshold policy with class-feasibility checks;
the historical half/half convention is only a candidate. Development probability
assessment requires nested group-disjoint cross-fitting of the complete training/
tuning pipeline. No preprocessing/feature selection/calibrator learns from its
outer validation or reserved records. Record source-only/format/source-stratified
sensitivity plans to expose source-class confounding, not claim its removal.

## B5. Exposure and final-evaluation alternatives

**Critical:** new IDs/splits on these same corpora cannot create an untouched
holdout. With historical linkage unavailable, do not certify absence of prior
exposure for any newly allocated component solely from its new assignment.

| Evaluation route | Required disposition |
| --- | --- |
| E-A: development/exploratory continuation on currently available sources | Adviser/researchers explicitly accept exposure uncertainty and scope. New split results are internal/repeated evaluation, not an untouched confirmatory test. A first authorized development experiment can be a milestone without claiming final thesis validation |
| E-B: independently documented unexposed archived subset within approved scope | Feasible only if such material actually exists, with acquisition/identity/group/custody/non-access evidence and both classes. None has been identified or obtained. Lock before selection. Do not assume availability or download anything |
| Neither can support the required final claim | Keep confirmatory evaluation blocked and ask adviser for a prospective evaluation/claim decision. No external source, replacement study, relabeling, resealing or methodological amendment is adopted here |

Section 4.3.1's ordinary change process requires a non-access assurance that
cannot truthfully be supplied retroactively for historically evaluated data.
Record that limitation explicitly in a dated deviation/claim-scope decision.
Prohibit use of old outcomes to choose groups, thresholds, candidate settings or
the preferred route. Keep old notebooks/results/assignments immutable and clearly
separate from the prospective version.

## B6. Approval and later implementation gate

Researchers choose P-A/B/C, identity/duplicate/group details, allocation and
exposure route. Adviser approves actual methodology/claim deviations; custodian
supplies source facts/custody, which approval alone cannot create. All are
Pending. Once accepted, Dhanwil implements/tests the exact identity receipt,
composition-aware supplied-assignment preparation and accepted allocation
policy with synthetic fixtures before any newly authorized data execution.
No replacement assignment exists now. Old first-source stratification must not
be reused for mixed groups, and no actual-data fit is authorized by this proposal.
