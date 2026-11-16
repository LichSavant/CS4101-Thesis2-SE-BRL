# Proposed semantic review adapter 1.0.0

Status: engineering proposal with synthetic verification. No external checkout
was executed, changed or integrated. No dataset was admitted or research enabled.

## Versions inspected read-only

| Repository | Main commit |
| --- | --- |
| [Vera review](https://github.com/veramarietherese/-SE-BRL-Research-Review-Vera/tree/25677a98236895ad16c6acf6aa75499dd2552fd9) | `25677a98236895ad16c6acf6aa75499dd2552fd9` |
| [Authoritative main](https://github.com/LichSavant/CS4101-Thesis2-SE-BRL/tree/a6e849a2ee107e9f0a2330b1d05d7c8d4a4925ca) | `a6e849a2ee107e9f0a2330b1d05d7c8d4a4925ca` |
| [Dhanwil review](https://github.com/LichSavant/-SE-BRL-Research-Review/tree/6a41d94d4e4f88c77c08bf7ea20a6ca59d192136) | `6a41d94d4e4f88c77c08bf7ea20a6ca59d192136` |

All three codebook JSON documents are semantically equal: canonical schema
1.0.0, codebook 0.1.0. The behavioral hierarchy and exact IDs are unchanged.

The source comparison found one preprocessing AST difference: Vera's existing
`_PageParser.unknown_decl` and `parse_bogus_comment` additionally reject malformed
HTML declarations. Main and Dhanwil lack these overrides despite sharing
preprocessing version 0.2.0. This task does not edit any parser. New reports,
interface specifications and evaluation plans bind its UTF-8/LF-normalized source
SHA-256 as well as the version. Resolve source identity before claiming identical
preprocessing across checkouts; the new fingerprint is not a semantic-equivalence
proof or external checkout verification.

## Dhanwil's actual published seam

Inspected sources at his pinned commit:

- `ml/experiment_inputs.py`: `TextField`, `LinkField`, `EmailObservation`,
  `MappedEmailAdapter`, population/partition checks and English-language gate.
- `ml/experiment_integration.py`: `EmailEvidenceInput` and
  `evaluate_development_lexical`.
- `docs/research/adapter_integration_specification.md`: declared integration and
  unresolved research requirements.

His evidence view contains only wrapped `subject`, `body`, `sender`, and `links`.
It has no artifact ID, source ID, consent, study purpose, language or target.
The outer integration validates population/assignments and sends only eligible
development evidence to a callback. Its callback result is otherwise passed
through without independent behavioral schema validation.

`email_request_from_view` supports that exact dataclass/wrapper shape using
synthetic structural fixtures. The caller must supply opaque artifact/source
identities, a source reference, declared language and collection consent
separately. An `EmailObservation` containing labels/bookkeeping is rejected.
No Dhanwil-owned engine, adapter or frontend/backend file is modified.

## Request

`record_from_request` and `analyze_evidence` require exactly:

`schema_version`, `codebook_version`, `artifact_id`, `source_id`,
`source_reference`, `modality`, `language`, `fields`,
`body_collection_authorized`, `link_extraction_authorized`, `study_purpose`.

The modality and evidence-field allowlists are executable in `review_adapter.py`.
Unknown fields, including labels, partitions, groups and folds, are rejected.
Body presence requires explicit authorization plus study purpose; nonempty links
require opt-in. Consent is never inferred from a supplied artifact. Unknown
wrapped values are omitted; explicit empty strings/tuples stay known-empty.
Content analysis requires declared English; unknown/unsupported languages fail
without becoming ordinary negative observations. No translation occurs.

## Output and validation

`review_record` returns an immutable `ReviewReport`; `to_dict` creates a detached
JSON-compatible copy. `validate_review` recomputes canonical symbolic evidence and
checks exact identity/policy/model/preprocessing bindings without NLI execution.

Each canonically ordered indicator contains:

- Indicator and parent dimension IDs.
- Unchanged `deterministic_state` and `evaluation_status`.
- Rule evidence, original field/location/start/end/text, supporting spans and
  explicit reference IDs.
- `candidate_state`: only `abstained` or `unavailable`.
- Semantic status: `not_requested`, `unavailable`, `context_blocked`, `scored`,
  `partial` or `failed`.
- Candidate spans and three entailment/neutral/contradiction distributions.
- Stable sanitized failure codes, `needs_review`, review reasons and timed
  constraint outcomes.

The envelope includes artifact/source identity, original-input fingerprint,
canonical dimension order and strict availability mask, versions, pinned model
contract, minimized provenance metadata, four unavailable learned values, and
three false research-release flags. Identity/source truth remains explicitly
unauthenticated by software. Raw provenance dictionaries are not copied.

Offsets are half-open Python Unicode character positions in the named original
field. JavaScript UTF-16 offsets and normalized-text positions are incompatible.
Header/entity/HTML locators must retain original source linkage.

Unknown output fields, malformed distributions, duplicated/altered spans,
availability changes, removed required review signals, forged constraints,
label overrides and research-release promotion fail validation. Provider errors
never become absence or expose exception text. Semantic budgets are 64 original
units and 512 scorer calls per artifact; incomplete coverage is explicit.

## Predictor and research boundary

This is an evidence/review document, not a classifier feature vector. The
`predictor_values` entry point always refuses export. Source identities,
provenance, labels, partition/fold/group metadata must not be flattened into
predictors. No deterministic bits or NLI scores are renamed learned z values.
E2/E3 remain blocked and no dimension-absence aggregation policy is changed.

Use Dhanwil's outer join/population/group/language protections in addition to this
callback validation. This single-artifact adapter cannot prove cohort admission,
source truth, group independence or legitimate research access. Any actual-data
integration remains behind research authorization and a separately reviewed run
namespace. A structurally matching callback is not end-to-end integration proof.

## Portable fixtures and merge requirements

`ml/fixtures/semantic-review-v1/{request,response,interface}.json` are generated
solely from synthetic metadata and text with no scorer. They contain no corpus,
model execution, human judgment or evaluation outcome. The fixture roundtrip is
tested exactly.

Before integration, agree on the preprocessing source/version, deterministic
instrument and policy ownership, source/language/consent decisions, reference
protocol and evaluation exposure policy. Merge helper/resource guards first,
review adapter next, validation preparation next; keep experimental policies
isolated. Re-run synthetic cross-repository tests before any separately approved
corpus use. Do not remove readiness gates or merge automatically.
