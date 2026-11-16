# Independent annotation workflow — engineering interface, human study pending

No annotation source is currently approved. This document describes how the
existing utilities can be used after a separately reviewed dataset/protocol
decision. Do not populate existing independent workbooks with generated answers,
modify policy approval lists as a workaround, or treat passing checks as human
provenance verification. No real packet was generated in this sprint.

## 1. Custody and permitted artifacts

Records for `ml.annotation_validation.blinded_packet` require a unique `record_id`,
nonempty `group_id`, explicit approved `source_dataset`, `partition=development`,
canonical `modality`, original `fields`, and researcher-held `provenance`.
Calibration/test sources, excluded source aliases/hashes, mixed-modality fields,
unknown fields and unapproved sources are rejected. Group links must be retained.
Lawful research access/body authorization is a prerequisite, not inferred by this
utility. No sampling, translation, vocabulary fitting or source replacement occurs.

## 2. Blinded packet

`blinded_packet(records)` projects only original evidence and neutral annotation
IDs, canonical ordered empty indicator cells, empty evidence/uncertainty fields,
and a content hash. It does not copy source targets, previous judgments, semantic
scores or AI rationale. Deliver only the returned `items` to annotators. Retain
`researcher_only_custody_manifest` separately: it maps neutral annotation IDs and
hashed groups back to source record/group identities and provenance. This
separation must be maintained in any later UI or export.

## 3. Human-completed response

Each response must preserve the packet item's `record_id`, `modality` and
`text_hash`, and supply:

| Field | Requirement |
|---|---|
| `codebook_version` | Current canonical version, 0.1.0 |
| `annotator_id` | Distinct human identity/reference, recorded by the study |
| `role` | `independent_human`; self/AI review is not independent validation |
| `qualifications` | Nonempty study-recorded qualification description |
| `review_date` | ISO date |
| `protocol_version` | Nonempty approved protocol reference |
| `independent` | Explicit Boolean declaration; must be true |
| `model_output_visible` | Explicit Boolean declaration; must be false |
| `indicators` | Canonical ID -> supported/absent/unavailable/None |
| `evidence` | Canonical ID -> list of original-field evidence spans |
| `identity_reference_ids` | Independent references for assessable identity judgments |
| `source_provenance` | Researcher-held references where supplied; excluded inputs rejected |

Preserve uncertainty separately. Omitted/None indicator cells remain missing;
`abstained` is a candidate decision state, not a human negative label. A supported
judgment requires exact original-field evidence. Unavailable/missing judgments
cannot assert supporting spans. Empty content, technical-only modalities and
missing conditional trust evidence cannot produce ordinary support/absence.
Identity absence, as well as support, needs independent references.

Evidence format is `{field,start,end,text}` with half-open Python Unicode character
offsets and `original_fields[field][start:end] == text`. Booleans are not valid
offsets. Never substitute normalized-text or JavaScript UTF-16 indices.

Use `validate_packet_response(packet_item, response)` to verify both artifact
binding and judgment schema. `validate_judgment(response, original_fields)` checks
the judgment separately. These validate declarations and structure; they cannot
authenticate a person's identity, qualifications or actual blinding.

## 4. Coverage and disagreement

Only after response validation, use `coverage(rows)` and
`pairwise_agreement(annotator_a_rows, annotator_b_rows)`. Unknown labels, booleans,
numeric labels, duplicate record IDs and incompatible artifact hashes/modalities
are rejected instead of silently disappearing. Coverage reports supported,
absent, unavailable, abstained and missing separately.

Agreement treats supported/absent/unavailable as three categories and excludes
missing/abstained pairs. It reports comparable counts, excluded counts, unmatched
records, observed agreement and Cohen's kappa. Empty/degenerate kappa is None.
These descriptive calculations never claim independence or scientific acceptance.

## 5. Separate human adjudication

Preserve the original independent responses. An adjudication record identifies
the record/indicator, at least two distinct reference annotators, a separate
adjudicator, review date, protocol, reason, chosen state and original evidence.
It also requires `role=independent_human`, `adjudicator_qualifications`,
`independent=true`, `model_output_visible=false`, and identity references when
applicable. Reference responses must be valid, cover the selected indicator, and
refer to the same modality. Duplicate, missing or AI-visible references fail.

`validate_adjudication(record, reference_rows, original_fields)` validates the
record; it does not vote, select a label, overwrite responses or act as a human.

## 6. Scientific acceptance

All `acceptance_gate()` flags remain false. A completed software workflow does
not freeze a semantic policy, approve dataset validity, establish per-indicator
model accuracy, authorize new holdout use, or release E2/E3. Those require the
research decisions and external human evidence documented in the handoff.
