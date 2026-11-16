# A. Bounded lineage recovery - final outcome

November 5, 2026. **BLOCKED; recovery effort closed for this sprint.**

The previous [lineage audit](../2026-11-05_email_lineage/README.md) established
zero authenticated pairs. This sprint added one systematic current-evidence and
Git-history check, rather than reconstructing another speculative crosswalk.
Read-only `git log --all --format= --name-only --` covered `experiments/src`,
`experiments/results/preprocessing`, `experiments/results/audits`,
`experiments/results/cleaning`, and `experiments/data/processed`. There were 28
distinct historical paths: aggregate audit/cleaning tables, supplied assignment
manifests, preprocessing policy and scaffolding. No lineage/identity/source-ID/
screening/attrition bridge candidate was present. No corpus blobs were retrieved.

Current metadata inventories, historical transformation source, recorded native
filtering, generic original-record-ID types, historical input references and the
prior source inventories were checked against the preceding evidence. No new
authenticated per-record ledger, repaired Email table or non-content two-sided
key was found. `experiments/runs` remains absent. No labels, ordinal coincidence,
group assignments or whole-file hashes were used as identity proof.

| Scenario | Historical denominator | Verified pairs | Historical coverage | Repaired denominator / ambiguity | Transfer |
| --- | ---: | ---: | ---: | --- | --- |
| Full historical | 38,759 | 0 | 0% | Unknown | BLOCKED |
| Non-CEAS projection | 21,447 | 0 | 0% | Unknown | BLOCKED |
| CEAS auxiliary projection | 17,312 | 0 | 0% | Unknown | BLOCKED |

The exact construction difference remains: historical N03 cells 15/19 at
`1a45c53` filter before per-source ranking; repaired
`ml/notebook_contracts.py:47` enumerates cleaned-source positions before
filtering. Source-backed metadata links are missing even where the counts or
ordinals could coincide. No claim that a particular historical record is wrong
or absent is made. Unknown ambiguity/key-collision counts remain unknown.

The recorded assignment groups/folds and prior raw/clean file-identity findings
retain their original scope; neither supplies row-level provenance. Existing
metadata hashes are not behavioral evidence or scientific approval. No message
contents, new content hashes, runtime logs, credentials or historical prediction/
outcome values were read. Notebook inspection used source cells, not evaluation
outputs. The abandoned dataset was not accessed or revived.

**Disposition:** use the [replacement protocol proposal](replacement_protocol.md)
as the decision-ready contingency. Do not repeat this missing-ledger search or
make historical recovery a prerequisite for an independently approved prospective
dataset version. A genuinely new authenticated ledger would be new evidence;
none is assumed to exist. Historical assignments/results remain immutable.
