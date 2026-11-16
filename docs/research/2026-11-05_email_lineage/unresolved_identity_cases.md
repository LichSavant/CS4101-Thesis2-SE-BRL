# Unresolved identity cases

Date: November 5, 2026. Aggregate cases only; no row-level crosswalk, message
content, native personal identifiers or ambiguous pair candidates are exported.

| Case | Affected historical records | Verified issue | Evidence required |
| --- | ---: | --- | --- |
| U1: Enron rank/position | 15,791 unresolved | Legacy suffix is post-filter rank; repaired suffix is pre-filter cleaned position. No source-backed bridge | Historical ingestion/lineage event or original-record token linked to the exact snapshot and both endpoint IDs |
| U2: SpamAssassin rank/position | 4,091 unresolved | Same construction gap; identical-looking IDs are insufficient | Same two-sided non-content evidence; no label/order inference |
| U3: Nazario ordinal coincidence | 1,565 unresolved | All historical records are positive and ordinal conventions may coincide under identical input/order; no authenticated per-record run linkage or repaired endpoint exists | Existing source-record identity plus snapshot/transform provenance, not a count or ordinal assumption |
| U4: CEAS role and missing endpoint | 17,312 unresolved | Legacy negative slice exists; current primary builder excludes CEAS and no repaired auxiliary identity table exists | Separate auxiliary endpoint/identity ledger if that role is later accepted. Identity audit does not select the role |
| U5: Original source-key absence | All 38,759 unresolved; overlaps U1-U4 | Recorded schemas/assignment table do not provide a populated original-record key; generic adapter types are infrastructure | Existing acquisition/import ledger; document any source-native-ID namespace or fully evidenced source-record locator chain |
| U6: Two-sided inventory absence | All sources; actual repaired count unknown | No repaired Email metadata inventory or existing row-level crosswalk was located | Named, immutable metadata-only endpoint delivery; no preparation API is authorized to generate it here |

U5/U6 overlap the source cases and must not be added to them as extra records.
Unresolved counts mean no verified counterpart; they are not proven missing rows.
Ambiguous matches and duplicate collisions for an admissible identity key are
not measurable because no such two-sided key exists. JSON uses null for those
unknown values. Historical observation-ID duplicate counts are independently
measurable and zero.

## Strategies rejected without attempting row pairing

- Same source and same ordinal suffix: the two ID definitions differ and row
  position alone is disallowed. No padding, renumbering or nearest-position join.
- Source checksum plus equal counts: binds a file, without the legacy per-record
  transform/run link. Prior raw/clean byte equality does not fill that gap.
- Source and target/native-label combinations: labels are forbidden identity
  keys. No class-based matching or label-driven tie-breaking was performed.
- Group/role/fold combinations: assigned scientific attributes are not independent
  record identity. Groups deliberately contain many records; using them as keys
  yields 17,158 excess historical records beyond distinct groups.
- Sender, recipient, subject, body, date or URLs: no message-field values were
  read or compared. These fields are also not established unique source keys.
- Body/content hashes: none generated. Matching normalization source code is not
  a persisted provenance ledger; normalization can merge distinct source records.
- Synthetic `original_record_id` examples or hashes: cannot establish actual
  corpus provenance. No synthetic identity was attached to a research record.
- Historical model predictions, errors, coefficients or outcomes: not admissible
  identity evidence and not inspected.

An unresolved case is not silently assigned to a candidate. A future evidence
delivery may establish unique pairs, multiple candidates or missing endpoints;
only then can those quantities be measured. Existing snapshots/assignments and
scientific decisions remain unchanged.
