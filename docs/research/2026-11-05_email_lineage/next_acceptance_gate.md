# Next acceptance gate: source-backed development identity evidence

Date: November 5, 2026. Proposed future gate only; **not approved or executed**.

## Smallest next input and task

Request an **existing non-content ingestion/lineage ledger for one source's
development slice**, together with a metadata-only repaired endpoint inventory.
Both must link to the same authenticated original-record key and immutable
source snapshot, with evidence for each transformation into its endpoint ID.
Choose the source based on available evidence; no source is automatically deemed
verified or selected for the scientific population. A complete one-source
development slice can establish a defensible subset before expanding the audit.

Vera/source custodian supplies provenance or identifies the archived ledger.
Dhanwil checks namespaces, uniqueness, coverage and immutable assignments.
Researchers accept identity/reuse conventions; adviser resolves methodological
deviations/claims where applicable. A signature cannot invent absent evidence.

If the source has no native IDs, a compound locator can be considered only with
the immutable snapshot hash, precise CSV-record/parser convention and an
authenticated historical ingestion/transform chain linking the legacy record to
that locator. Position alone, an inferred native-label sequence, or a newly
invented UUID is insufficient. Do not create a content-derived bridge under this
task. If no admissible ledger/chain exists, document that fact and obtain a
separate bounded reconstruction authorization before any additional source work.

The immediate task remains identity verification, not feature extraction,
population selection, assignment generation or model fitting. No need to resolve
all H1-H12 items or transformer/annotation questions to inspect a valid ledger.

## Future restricted artifact design

This is a proposed metadata design, not a competing experiment schema or an
export. A custodian-controlled immutable file, stored outside public/Git-tracked
reports and restricted to the authorized researchers, can carry:

| Field group | Required meaning |
| --- | --- |
| Artifact provenance | Schema/version, provenance/custody reference, producer, source snapshot and historical/repaired input/transform versions/hashes |
| Endpoint links | Historical and repaired observation IDs or opaque endpoint tokens; source namespace; authenticated non-content original-record token |
| Record-locator evidence | Source-record locator and parser/index convention when documented; separate evidence reference linking it to the original key and each endpoint |
| Match accounting | Explicit method/version, unique/unmatched/ambiguous status and candidate multiplicity; retain unresolved cases without tie-breaking |
| Assignment payload, separate from match key | Historical assignment-manifest reference/hash, supplied group ID, partition, development fold and target; repaired values if already supplied; comparison status |

Never include subject, body, URLs, sender/recipient values, credentials, raw
personal Message-IDs or model predictions/outcomes. If a native identifier could
contain personal information, the custodian should supply an opaque consistent
token and retain the sensitive lookup separately; a keyed token design needs
documented namespace/key-version/custody. No secrets belong in a report. Token
consistency must be authenticated; tokenizing different unlinked IDs does not
create identity evidence. No new tokens or keys are generated in this audit.

Initially provide development-only rows. Calibration/test assignment metadata
already exists in the historical manifest; do not supply reserved message
payloads or predictions to establish their identity. Full-population coverage
would require separately permitted metadata evidence for those roles.

## Acceptance checks for the next audit

1. Authenticate the two endpoint inventories and key/transform provenance; check
   snapshot, parser and namespace compatibility. Reject a claimed source-only or
   row-position-only bridge.
2. Check each admissible key's cardinality independently of labels/assignments.
   Count duplicate keys, ambiguity and missing endpoints. Form only one-to-one
   pairs; never resolve duplicates by target, group, fold, position or score.
3. After identity is established, compare the supplied source/group/role/fold/
   target metadata. Record any disagreement and stop affected transfer; do not
   normalize labels or reassign groups to force agreement. Preserve null reserved
   folds and all supplied values. No identity pair is verified by its label.
4. Check cross-role/cross-fold groups over the paired population and its supplied
   historical relationships. Report omitted/unresolved records, incomplete
   relationship coverage and scenario scope. No claimed global no-leakage proof.
5. Publish aggregate counts only. Apply VERIFIED when unique identity provenance
   and assignment preservation are established for the stated scope; PARTIAL
   when some verified pairs coexist with unresolved records; BLOCKED when keys/
   endpoints cannot establish identity. A verified source slice does not make
   the full Email population verified or scientifically eligible.

For later handoff work, inspect actual fixed paths in
`ml/development_experiments.py:292`: the main CSV and input manifest are under
`data/processed/features/development/`, while `email_sebrl_features.csv` is under
`data/processed/features/sebrl/` within the named run. The previous acceptance
packet's path shorthand must not be used to relocate the behavioral file. No
D9 handoff or restricted row-level crosswalk is created by this documentation.

Any subsequent no-fit preparation still needs source/role/label/group/custody and
feature/rule acceptance for its scope. CEAS options remain Pending; lineage
verification cannot admit CEAS or reseal a historically exposed test set. Real
D10 remains blocked, and transformer work remains deferred.
