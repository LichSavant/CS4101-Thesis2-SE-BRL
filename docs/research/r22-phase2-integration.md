# Vera R22 integration — Phase 2

Destination branch: `integration/vera-dhanwil-r22`.
Status: **VERIFIED — engineering integration ready for the integration branch.**
Existing Phase 1 parent: `85f6105ef2c520f98304c68b5d30f3cf657c04ae`.
Vera approved source: `337c3c4f23c1aeff7b16f5d6924eb377a52393af` from
`veramarietherese/-SE-BRL-Research-Review-Vera`.
Dhanwil approved source: `ae20372db6014d4f83153c03ccc2cd92f445ca8c` from
`LichSavant/-SE-BRL-Research-Review`, already selectively integrated in Phase 1.

This is a selective source integration onto the existing branch, with no merge
of unrelated histories. No existing source, test, schema, dataset, historical
result, proposal, or notebook is deleted. Main and both review repositories are
unchanged. The original working checkout and its uncommitted work are untouched;
integration and verification use separate temporary directories.

## Integrated contributions and overlaps

Vera adds the source-verified offline joint adapter, evidence/consent bindings,
bounded semantic review, independent annotation/evaluation contracts, explicit
representation semantics, closed research admission, source-only notebook
projections, runtime comparison tooling, tests, and review documentation.

| Overlap | Combined behavior |
| --- | --- |
| Preprocessing | Preserve Dhanwil's repaired token-boundary parser and expanded tests unchanged. Vera's joint adapter checks both prepared views and rejects differences. |
| Canonical codebook bytes | Restore the exact CRLF serialization from Dhanwil's approved commit, matching the existing candidate's byte hash. All JSON values, definitions, ordering, and versions equal the destination and Vera codebooks. Pin this file against Git text normalization. |
| Representation, features, readiness, backend/API, shared wire schema and dashboard | Preserve Dhanwil's implementation unchanged. Vera's review schema is a separate offline report, with no new endpoint or authoritative predictor connection. |
| Dataset records | Add Vera's early excluded-source/provenance/fingerprint rejection to the existing record type. |
| Independent evidence locators | Add Vera's strict span field, integer offset, and Boolean quote validation to the existing detector. |
| Extension privacy | Existing Phase 1 implementation already provides the metadata projection, body prohibition and link opt-in. Retain it, including artifact submission, UI disclosures and race protection; add Vera's API and selected/hidden-message regression coverage. No permissions change. |
| Legacy validation modules | Apply Vera's pinned local-only NLI loader, score validation, review/abstention and closed corpus-entry gates; preserve existing corpus files. |
| Runtime fixtures | Rebind the new synthetic fixtures to the combined source and Phase 1 parent. Original source-bound review packets remain unchanged under their historical documentation paths. |
| Notebooks | Add Vera's five source-only guarded projections alongside the existing notebooks. They describe Vera's review snapshot, not equality with Dhanwil's notebooks. No notebook is overwritten or executed. |

There are no unresolved Git conflicts. Unchanged or semantically equivalent
overlaps are retained without duplicate implementation. The review snapshot's
omissions of destination files are not applied as deletions.

## Safeguards and approval boundaries

The complete joint adapter accepts only the actual pinned email observation
types. Generic preprocessing/review primitives retain their existing modality
contracts; they do not extend the joint batch adapter's scope. Body collection
requires explicit consent and study purpose; links require opt-in. All batch
identity, partition, evidence and output checks remain fail-closed.

Deterministic labels remain authoritative. NLI is explicitly injected and
review-only; no scorer is initialized by default. Unknown, known-empty,
unavailable, partially evaluated, and assessed-absent evidence retain separate
semantics. Dhanwil's deterministic slots and Vera's learned-value placeholders
remain separate contracts; neither is silently substituted for the other.

SpaPhish/SpaFish aliases and registered excluded fingerprints remain denied.
No excluded corpus is read, copied, modified or admitted. Existing protected
datasets/results are unchanged. Sealed tests, calibration, scientific fitting,
E2/E3 release, and scientific experiment approval gates remain closed.

The imported R22 acceptance packet remains historical evidence with pending
owner approvals. Source integration and synthetic software tests do not change
`joint_acceptance=false`, authorize a semantic methodology extension, or claim
scientific R22 acceptance. No model training, scientific experiment, actual
model inference or independent human study is performed by this integration.

## Verification

The initial expanded regression selection exposed ten failures in
`ml/tests/test_feature_freeze.py`, all raising
`ml.experiment_inputs.InputContractError: invalid_feature_candidate`.
The candidate binds the codebook byte hash
`36ad77a3f06a962003f8383b4390f2410f93cd7f38eeee3f4d30cad20d839021`, while
the destination codebook hashes to
`5360a30f8d8781179db3dbd3def76c6b718d74521ea82522e0df35e518dabd94`.
Investigation of the approved Dhanwil commit, Vera commit, destination, and
original canonical-codebook commit `e483018` proves that the only difference is
196 CRLF versus LF line endings: replacing CRLF with LF makes every byte equal.
The original Phase 1 validator, candidate, and failing tests remain unchanged.

The authorized continuation restores the exact codebook blob from Dhanwil's
approved commit, whose SHA-256 is the existing expected `36ad77...` hash above.
No hash value is replaced. `.gitattributes` sets `-text` for this specific file
to preserve those bytes on commit and checkout; its whitespace rule recognizes
CRLF while retaining the normal trailing-space, blank-EOF and indentation
checks. No scientific validation is disabled, new codebook version invented,
or feature meaning changed. The codebook remains the same `pre_freeze` version.

The ten originally failing tests pass first after the repair. Fresh reruns then
pass: joint 50, parser 34, safeguards 145, expanded Vera/legacy/preprocessing 881,
pinned broader regression 770 (9 trusted-readback skips, 1 fitting deselection),
and supplemental ML/backend 521 (9 fitting-dependent deselections). Frontend
tests pass 28 extension and 13 dashboard cases; typecheck, lint and build pass.
The process-wide no-fit runs report zero fitting attempts and zero executions.
These are software checks, not scientific results or joint owner acceptance.

Fresh combined-branch results and the complete file inventory are recorded in
[r22-phase2-verification.json](r22-phase2-verification.json). Test selections
overlap; their counts must not be summed as unique tests. Historical Vera and
Phase 1 test results are not substituted for fresh combined verification.

Vera's guarded runs prohibit network/subprocess access, real-model dependency
loading, corpus reads and writes outside their temporary run. Dhanwil's broader
selection uses his process-wide no-fit plugin, pinned Python 3.12 dependencies,
synthetic fixtures, and an external source copy. Fitting-dependent cases and
model readback lacking independently trusted synthetic receipts remain excluded
or skipped as explicitly recorded. No verification gate is bypassed.
