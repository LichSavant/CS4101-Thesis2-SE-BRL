# C2. E1/E2/E3 predictor-freeze candidate

Version `email-predictor-candidate-0.1`; **Pending research acceptance**. Exact
columns below are a reviewable proposal, not an adopted study configuration.
Table 4.7 permits modality-specific conventional fields finalized from audit;
the full baseline's relation/header/embedded-URL coverage must be explicitly
accepted or its limitations/deviation documented. No data was extracted here.

## Conventional core candidate

| Order | Predictor | Type and explicit candidate meaning | Existing implementation |
| --- | --- | --- | --- |
| 1 | `model_text` | Nonempty string; candidate source-preserving subject/body segments used to form the model view, then existing HTML-unescape/NFKC/casefold/whitespace normalization; preserve original evidence separately | `ml/preprocessing.py::normalize_text` / PreparedArtifact model view; historical N05 also uses model_text, with a separately reviewed derivation |
| 2 | `conventional:text_char_count` | Finite nonnegative numeric; length of that exact normalized observed model view | `ml/features.py::structural_features` |
| 3 | `conventional:text_word_count` | Finite nonnegative numeric; whitespace token count of the same view | Same function |

These names/types/order are compatible with `FeatureColumn` and all four genuine
adapters. They are not already materialized by repaired N03 into a real D9 file.
Do not run the privacy-bounded runtime transport API over a research corpus
wholesale: its length/body/link-authorization constraints are not automatically
research eligibility criteria. A later accepted pure dataset adapter must retain
raw-field evidence and produce precisely the accepted model view.

The core supplies lexical plus observed-text size metadata, not the complete
relation/header/URL conventional baseline. A researcher must accept this scoped
first experiment under Table 4.7 or require the fuller baseline before fits.
The historical text-only dictionary is not automatically the new frozen baseline.

Fuller existing feature candidates for separate review include
`conventional:header_count`, `conventional:quoted_segment_count`,
`conventional:sender_reply_domain_differ` and the `conventional:url_*` values.
Current runtime structural/URL functions can emit zero when evidence is missing;
that cannot be adopted as known absence. Freeze per-feature required opportunity,
None/availability semantics and observable derivation first. No new relational
feature, empty URL list or negative evidence is fabricated in this sprint.

Exclude source identity, addresses/domains as raw categorical IDs, corpus names,
row numbers and collection/authorization flags from this proposed core.
`sender_available`, `body_supplied`, `html_supplied`, `links_authorized` and source
format can reveal corpus membership; do not silently add them as predictors.
Text and length may still encode era/style/source shortcuts: predeclare source-
only, normalized-format and source-stratified diagnostics and limit claims.

## Exact E2 order already supported by D9

All are integer bits 0/1; missing mask/support cells fail validation. The order
comes from `ml/development_experiments.py::behavioral_columns`:

```json
[
  "pressure_threat_cues_supported",
  "lure_attention_cues_supported",
  "trust_identity_manipulation_supported",
  "requested_action_consequence_supported",
  "pressure_threat_cues_available",
  "lure_attention_cues_available",
  "trust_identity_manipulation_available",
  "requested_action_consequence_available"
]
```

E1 = the three proposed conventional columns in order. E2 = the eight canonical
columns above. E3 = E1 followed by E2, eleven raw columns before fold-local text
expansion. Vocabulary/IDF may differ by training fold; its learned ordering/state
must be saved in the eventual selected bundle. Raw dictionary ordering and
fold-specific expanded estimator columns are distinct reproducibility records.
No labels or source annotations generate behavioral evidence.

Encoding: supported (1,1), assessable absent (0,1), unavailable (0,0). Support
without availability fails. Missing/unsupported-language/identity/link evidence
does not become a negative behavioral observation. Partial availability remains
the unresolved scientific decision in the codebook audit. Do not average or
replace unavailable bits with calibrated probabilities or learned z values.

## Preprocessing candidate and forbidden columns

Proposed lexical settings reuse historical choices where supported: word
TF-IDF, ngrams (1,2), max_features 20,000, min_df 3, max_df 1.0, sublinear_tf
true, norm L2, no stop-word list or accent stripping, word token regex
`(?u)\b\w\w+\b`, lowercase true. Pinned sklearn 1.6.1 supplies float64 TF-IDF
under the current adapter; the legacy notebook's explicit float32 is different.
Type/configuration and actual library dtype were inspected without fitting.
These are recommendations, not accepted values.
Numeric core policy: reject missing/nonfinite values, no scaling initially;
standardization is a separately declared train-fold transform if accepted.
Tree/linear differences, dtype and missing-text eligibility must be frozen before
comparative fits. No silent family-specific densification or changed row set.

Never allow `target`, `label`, `Result`, `source_label`, native labels,
`observation_id`, `source_row_id`, original-record IDs/hashes, `group_id`,
`partition`, `cv_fold`, source/dataset/snapshot/provenance fields, language,
evidence references, paths or audit status as predictors. Existing
`select_predictors` also rejects source_/provenance_ prefixes. ID and assignment
metadata are control columns only. Do not discover predictors by numeric dtype.

Matched E1/E2/E3 must use the same accepted IDs, targets, groups and folds.
Screening occurs once under the accepted source/content policy, not separately
after seeing representation performance. A missing text row cannot disappear
only from E1/E3. Unsupported language is not automatically excluded or assumed
English; freeze eligibility versus unavailable-evidence handling prospectively.

PhiUSIIL/UCI retain their separate U1 technical dictionaries; no behavioral
E2/E3 or raw pooling. Current dataset-neutral schema does not establish a full
Web content branch. Screenshots remain audit-only unless separately approved.

## Freeze acceptance

Researchers must choose core-versus-complete E1 scope, exact derivation/types/
missingness, text/numeric settings and codebook aggregation/language/locator
version. Dhanwil then materializes/validates named development fields without
fitting preprocessing and verifies one-to-one alignment. Current references
remain assertions, not approval. This Markdown candidate is not a frozen source
dictionary, a data handoff or evidence of actual-data feature conformance.
