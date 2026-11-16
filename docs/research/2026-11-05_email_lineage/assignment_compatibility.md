# Assignment compatibility

Date: November 5, 2026. **Identity transfer: BLOCKED in all scenarios.**
The observations below concern the supplied historical assignment metadata only.
No repaired row was paired, no assignment was generated, and no existing value
was edited. A metadata-only scenario is not an approved scientific population.

## Fresh metadata checks

Input: `experiments/results/preprocessing/partitions/email_partition_manifest.csv`.
SHA-256 `38c87c522da47fea6f8f584c2e487af73d89502e9db3130f6298006829241ae4`.
Schema is exactly six safe assignment fields; all are nonempty where required.
Development fold strings are `1.0`-`5.0`; calibration/test fold cells are blank.

| Check | Full historical | Non-CEAS projection | CEAS-only auxiliary projection |
| --- | ---: | ---: | ---: |
| Records | 38,759 | 21,447 | 17,312 |
| Unique recorded groups | 21,601 | 17,805 | 3,796 |
| Duplicate historical observation IDs | 0 | 0 | 0 |
| Recorded group crossings between roles | 0 | 0 | 0 |
| Recorded development group crossings between folds | 0 | 0 | 0 |
| Recorded mixed-target groups | 0 | 0 | 0 |
| Recorded groups spanning sources | 0 | 0 | 0 |
| Development records | 27,129 | 15,011 | 12,118 |
| Calibration records | 5,815 | 3,218 | 2,597 |
| Test records | 5,815 | 3,218 | 2,597 |
| Five development folds present | Yes | Yes | Yes |
| Positive / negative records | 1,565 / 37,194 | 1,565 / 19,882 | 0 / 17,312 |
| Verified historical-to-repaired pairs | 0 | 0 | 0 |
| Repaired assignment comparisons performed | 0 | 0 | 0 |

Both classes appear in every historical/full and non-CEAS role/fold. The CEAS
slice has a single class. Its metadata folds exist, but it does not satisfy the
current Email binary handoff's both-class requirements and cannot support a
standalone two-class phishing claim. No label was used to identify a record.

Zero recorded crossings does not prove absence of unrecorded duplicate/template/
campaign relationships. Historical group membership is not a verified crosswalk
to repaired records. The source-disjoint groups permit a structural non-CEAS
projection without splitting a recorded component; they do not authorize reuse.

## Assignment preservation findings

| Supplied field | Verified within historical table | Historical -> repaired transfer |
| --- | --- | --- |
| `group_id` | Present; a recorded group has one role and one development fold | **Not verified**: no independently identified repaired counterparts or group-evidence bridge |
| `partition` | Exactly development/calibration/test; no recorded crossings | **Not verified**: no repaired row roles to compare; do not reallocate |
| `cv_fold` | Legal five development values; blank reserved folds | **Not verified**: no endpoint pairing; blank must remain null, never filled for reserved records |
| `target` | Binary in the supplied manifest; class summaries recorded | **Not verified** across versions: targets are payload to compare only after identity, not matching keys or tie-breakers |

There are zero checked identity pairs, so the cross-version conflict count is
**unknown**, not zero. No claim that all assignments can safely be transferred
is made. Metadata-only joins within the same historical manifest would be
circular identity evidence.

After independently verified one-to-one identity linkage, historical group/role/
fold/target values can be compared and carried as immutable attributes. If a
repaired endpoint already supplies different values, record a conflict and stop;
do not overwrite it with the historical value and call preservation verified.
For an endpoint with no assignments, carrying values would be a future explicitly
authorized operation, not evidence that a two-sided comparison already passed.

## Scenario-specific restrictions

1. **Full historical:** current primary builder admits three sources, while the
   historical manifest includes CEAS. Identity verification would not authorize
   CEAS admission. Resolve role/population separately before research use.
2. **Non-CEAS:** a subset can preserve historical values mechanically, but source
   positions/identity and group/reuse acceptance remain unresolved. Current
   default ID spelling cannot be substituted for historical IDs without proof.
3. **CEAS auxiliary:** no repaired auxiliary inventory or accepted identity
   convention is available. Preserve native-class meaning and separate any
   future source/hard-negative diagnostic from binary primary experiments.

Historical test evaluation/exposure is documented in the preceding acceptance
packet. No outcome/prediction files were read here. Reusing metadata or changing
CEAS membership cannot create an untouched test set. This audit grants no access
to reserved message payloads and performs no fit or final evaluation.
