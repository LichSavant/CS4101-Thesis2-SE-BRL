# Technical-branch admission: prioritize PhiUSIIL, no experiment yet

UCI-327 and PhiUSIIL-967 remain separate approved U1 technical branches under
proposal Table 4.7 / SRS REQ-4.4-8. Neither admits E2/E3 or establishes a behavioral
SE-BRL benefit. Deterministic indicators, unavailable technical-modality states,
review-only NLI and R22 are unchanged. UCI's exhausted label/lineage search was
not repeated.

**Priority decision: PhiUSIIL-967**, because its official repository explicitly
defines native labels, while the UCI-327 Result definition remains unresolved.
This selects the next verification task, not an admitted modeling population,
classifier, feature subset, split or winning historical percentage.

## Actual new evidence

The [official PhiUSIIL page](https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset) Class Labels section states native **0 = phishing,
1 = legitimate**. It matches the existing native-to-study target mapping 0→1,
1→0. `phiusiil/label-verification.json` binds the primary declaration to retained
publisher bytes. This resolves the branch's native-label evidence condition;
source-reported class counts were not used to infer meanings.

The official ZIP was acquired opaquely: **15,376,007 bytes**, SHA-256
`0a639fd03aea6308c5b1c10c92aa23c2ce1505447a9137271865cd0badc9a59a`, matching the
independent pre-existing original ZIP LFS pointer. Its single CSV member is
56,854,345 bytes. Only the **754-byte CSV header** was returned; all 56 ordered
fields match official metadata. No original CSV data row was returned or parsed,
no file extracted, and no LFS payload materialized. ZIP buffering may occur
internally. Complete CSV digest/record validity were not freshly checked.

`phiusiil/feature-dictionary.evidence.json` records every source field/role/type.
FILENAME is official `Other` bookkeeping, not a predictor; label is Target.
There are 54 declared features, including four categorical fields; a 50-numeric
projection is supplied for review, **not silently adopted**. Metadata does not
establish actual value ranges, original-key uniqueness or split-local generation
of precomputed reference/probability features. Those are evidence/interpretation
checks, not allegations of measured leakage. Retrieved metadata supplies no
derivation details; the linked paper endpoint was inaccessible. No mirror was
substituted and no references were invented.

## Exact next decision and delivery

**Researchers/data holder: record and authenticate one bounded PhiUSIIL no-fit
development delivery**, bound to the verified source snapshot and current code:

| Requirement | Supporting evidence | Acceptance condition / responsible actor |
| --- | --- | --- |
| Original-record identity and transformations | Original CSV/header and FILENAME metadata; identity mechanism already implemented | Researchers/data holder supply authentic original locators, transformation/attrition receipts, independent expected development ID universe and hashes. FILENAME uniqueness must be checked, not assumed. New IDs cannot transfer old assignments or erase exposure. |
| Exact data scope | Historical metadata has development/calibration/test roles; no original-row bridge or current delivery is authenticated | Named development-only predictors plus complete permitted assignment metadata; no reserved predictors/outcomes. Researchers may be their own data holders; no universal outside custodian signature is required. |
| Groups/conflicts and exposure | Prior metadata: 220,086 supplied groups, 54 mixed-target groups and zero recorded crossings | Researchers accept source-permitted URL/domain/duplicate relationships, explicit mixed-target disposition and exposure-aware claims; verify actual row-to-group correspondence. Recommend retaining distinct conflicting records together; no relabeling or silent exclusions. Joint deviation approval applies where frozen methodology/claims change. No untouched-test claim is inferred. |
| Feature freeze / leakage controls | Source-derived 56-field declaration and numeric review projection; existing FILENAME/target deny-list | Freeze exact accepted U1 dictionary, missingness/encoding and source-engineered-feature interpretation. Establish reference/statistical-feature derivation and split/exposure limitations before claiming leakage-controlled inductive performance. Do not choose features using held-out results. |
| No-fit execution | Existing D-features reader/receipt and source/locator/group/fold guards | Authenticate exact population, assignments, dictionary, feature-freeze and development JSON hashes; named actor/date/scope/code and independently trusted receipt digest. A Pending form or this packet grants nothing. |
| Subsequent fitting | Approved four-family framework and development-only experiment engine | Separately freeze exact settings, seeds, budgets, calibration/threshold/selection/uncertainty and authorize the exact E run after admission. No fitting settings are blanket prerequisites to earlier permitted metadata work. |

Researchers can record routine decisions within the approved design, as verified
directly in `../2026-11-17_uci_admission/researcher-authority-matrix.json`.
Genuinely external dependencies are source facts/third-party-controlled records
where unavailable locally, and any applicable joint/material-deviation or actual
institutional-policy process. Public access alone is not scientific authorization.

No original rows, genuine lineage/attrition receipts, assignments, classifier fits
or scientific metrics were produced. The retained UCI admission status remains
0/10; PhiUSIIL's label evidence is resolved but its overall admission is blocked.
One shared dataset does not establish the other's acceptance or performance.

## Verification limit

An exploratory test exposed that a suspected missing PhiUSIIL fold check was
already enforced by `ml.notebook_contracts.validate_feature_boundary` before
export. The temporary redundant change/test was removed. The initial test's
error-string assertion failure is retained as exploratory evidence, not a
production defect or failed experiment. No ML/gate code changes remain, no
replacement tests were added, and test totals are not scientific results.

Current exact commands/results/hashes are in `verification.json`; prior UCI
verification is reused where unchanged. Nothing is pushed or merged.

Final focused selection: **126 passed, 0 failed, 0 skipped**. Final guarded
regression: **814 passed, 0 failed, 10 skipped, 1 fitting test deselected**,
zero fitting attempts/executions; one existing Starlette warning. Counts overlap
and are not summed. Nine skips require absent trusted synthetic readback inputs;
one requires symlink permission. No production or research-gate code changed.

## Latest completion boundary

The final-completion request supplied no new authenticated development delivery
or accepted scope/policy values. At baseline commit `54fc83a`, all retained
evidence hashes matched and the existing fitting guard refused a missing verified
context. `scientific-completion-gap.json` records the exact minimum next input.
No further source/history audit or regression cycle was run: prior 814-pass
guarded results are reused, not reported as new tests. Scientific completion is
**PARTIAL - EXTERNAL EVIDENCE/AUTHORIZATION BLOCKED**. No Results/Discussion,
model table, diagnostic figure or experimental metric was fabricated.

## Six-file assembly result

`d-features-contract.json` now specifies the exact six existing-validator inputs
and their provenance constraints. `d-features-supported-decisions.json` records
only attributable existing source/mapping/U1/predictor-exclusion requirements.
`d-features-delivery-status.json` records the actual result: **partial, 0/6
admissible input files created**, zero genuine records and no dataset-specific
no-fit admission. The missing population/assignment/original-key evidence and
independently authenticated acceptance cannot be recovered from the public archive
or by hashing assistant-generated files. No placeholder protocol files were made.

## Development reconciliation executed (2026-11-18)

The subsequent explicit reconciliation request permitted source/clean development
comparison and a separate fold-representation correction. The reproducible command,
input/code/output hashes and aggregate receipt are in
`d-features-delivery-status.json` under `latest_reconciliation`. Original files
remain unchanged. Local row-level evidence is ignored, not committed.

All **165,089** development positions have source/clean correspondence and matching
native-to-target labels: **4** have identical decoded cells; **165,085** differ
only in exactly equal decimal representations in officially declared numeric
fields. No tolerance, imputation, label change or predictor choice was applied.
No selected position is missing or value/target-unmatched. This is a reconstructed
same-position correspondence, **not independently authenticated historical
lineage**; cross-position/global uniqueness was not established. Reserved source
records were traversed only for CSV framing, never decoded or feature-inspected.

The separate development assignment CSV preserves IDs, targets, groups and folds,
changing only `1.0`–`5.0` to `1`–`5`. The existing partition validator passes;
both classes occur in every fold. Group-role/fold crossings are zero, and each
selected normalized domain corresponds to one supplied group and vice versa.
The **36** mixed-target development groups remain intact. These checks do not
establish campaign/template/near-duplicate coverage. No feature rows or fits were
generated. Focused guarded regressions: **41 passed**, zero fitting attempts.

### Exact decisions still required from the researchers

1. Accept or reject the reconstructed source-bound development ledger and the
   separately normalized historical assignments. Recommended: retain all supplied
   groups, including 36 conflicts, with unchanged labels; disclose historical
   exposure and restrict claims to exploratory development. Exclusion/reallocation
   requires a separately justified, accepted policy and new frozen evidence.
2. Accept an exact ordered technical dictionary and missingness/encoding rules.
   The 50-numeric projection remains a candidate, not a freeze. Resolve or explicitly
   bound source-engineered reference-feature leakage/exposure limitations. Do not
   use FILENAME or manufacture behavioral evidence; PhiUSIIL supports U1 only.
3. Supply attributable dated scoped no-fit acceptance, an independently trusted
   digest and accepted upstream original-ID universe. A hash of this agent's own
   candidate ledger cannot authenticate independent acceptance. Historical rank IDs
   are retained here; the final prospective locator-ID contract still requires its
   accepted population/alias bridge.
4. After admission, approve the exact frozen development experiment configuration,
   budget, output namespace and fitting receipt. Until then no baseline, behavioral
   comparison, ablation, scientific metric or manuscript Results claim is authorized.

## Reported joint direction implemented

The subsequent user reports joint researcher direction to proceed conservatively;
`PHIUSIIL_DECISION_REGISTER.md` records its attribution, exact choices, alternatives
and limits. This is not independently verified signatures or exact-file acceptance.
`d-features-delivery-status.json:latest_development_delivery` records the actual
165,089-record, ten-numeric-field delivery and component checks. Five genuine
contract inputs plus a historical/prospective ID alias ledger are local and ignored
under `experiments/runs/phiusiil-development-20261118/`. All output hashes and the
existing ML code map were rechecked. Focused guarded tests: 48 passed, zero fits.

Source-native values, all 36 conflict groups and original five-fold memberships
are preserved. The subset is exploratory U1 only. The gate remains unchanged:
complete accepted three-role source-locator metadata and a genuine exact-file
no-fit receipt with independently trusted digest are still absent; separate frozen
fitting settings/authorization are also absent. No reserved source records,
acceptance receipts, signatures or scientific metrics were generated.
