# Adapter integration checkpoint

Status: synthetic software integration at baseline `6bded57`; not research
approval, corpus adoption, or an amendment to H1-H12. Existing drafts and
historical notebooks/results are preserved.

## Implemented path

Explicitly mapped email adapter -> typed observations -> population validation ->
exact partition-ID coverage and supplied-group isolation -> development-only
language/text gate -> evidence-only callback -> results keyed by observation ID.

`ml/experiment_integration.py` performs this path entirely in memory. Callers
supply the identity, expected total, target counts, and existing assignments.
Integration requires a nonnegative integer total (excluding booleans) and a
mapping containing both target labels with nonnegative integer counts whose
sum equals that total; count booleans are also rejected. Neither expectation
may be `None`. The standalone
`validate_population` retains its intentionally optional expectations.
No counts, labels, groups, folds, splits, language detection, or permissions are
inferred. Calibration and test records never reach the lexical callback. All
batch validation finishes before the first callback. A source label is retained
for population checks, but is not included in `EmailEvidenceInput`.

The view supplies original subject/body, sender and supplied links using the
existing availability wrappers. Unknown links remain unknown. No text or an
unsupported/unknown language returns unavailable, never an absent vector.
Explicit English is a caller assertion, not verified language coverage.

The integration tests exercise the existing runtime `preprocess` and `RuleEngine`
with synthetic English text and explicit synthetic body authorization. They
verify original-field spans and rule-based provenance. This does not select the
runtime rules as the approved experimental instrument. There is no default
runtime callback, corpus loader, file writer, model fit, or holdout evaluator.
Callbacks must be trusted pure functions. Validation is a software boundary,
not an adversarial sandbox: caller code can access external state. Sanitized
callback exceptions abort without returning partial results; they cannot undo
side effects performed by a callback.

The generic callback may return an arbitrary result. The wrapper passes that
result through without independently validating an evidence schema, field
locators, offsets, or behavioral semantics. `evaluated` means that the callback
returned, not that its output is valid behavioral evidence. The runtime-rule
test verifies spans for that specific callback; it establishes no new generic
behavioral-output contract.

## Acceptance checks

| Boundary | Required outcome |
| --- | --- |
| Missing, extra, duplicate partition identifiers | Reject before evaluation |
| Mixed snapshot or inconsistent population/class counts | Reject before evaluation |
| Missing (`None`), malformed or contradictory expectations | Reject before evaluation |
| Supplied groups crossing partitions or development folds | Reject before evaluation |
| Reordered assignments | Join by ID, retain observation order |
| Calibration/test observations | No lexical callback |
| Spanish/unknown language | Unavailable, no callback |
| Empty/unavailable text | Unavailable, preserve field distinction |
| Callback input | No native label, target, provenance or partition |
| Existing runtime synthetic extraction | Distinct records retain their own original-field spans and offsets |
| Arbitrary callback result | Passed through; no independent evidence-schema validation |
| Evaluator exception | Stable sanitized error, no partial return |

These checks do not establish near-duplicate/campaign independence, correct
source labels, lawful data use, or scientific validity. The integration does not
require every partition/fold to be populated or both classes within every fold;
those are future experiment-protocol checks, separate from this join boundary.

## Notebook/runtime alignment specification

The proposed integration seam is before Notebook 04's lexical extraction and
before Notebook 05's feature merge. Neither notebook is changed in this phase.
Future integration requires explicit source decoding and an approved contract:

1. Keep original text and source locators separate from normalized model text.
2. Use canonical codebook IDs; provide a versioned legacy-name adapter for the
   four notebook dimension names and `credential_sensitive_request`. A name
   mapping alone must not assert rule equivalence.
3. Freeze qualifying rules, negation/quoted/educational exclusions, language
   coverage and per-indicator version identity. Do not choose these from test
   performance.
4. Decide whether partial indicator availability can establish dimension-level
   Absent. Until resolved, do not replace current runtime aggregation behavior.
5. Define source-faithful locators for supplied engineered fields separately from
   directly observed text/DOM evidence.
6. Specify deterministic support/availability E2 and E3 under a new version.
   Do not repurpose learned z slots or remove existing readiness blockers as a
   side effect of the adapter integration.
7. Require exactly matched observation IDs and metadata for E1/E2/E3 and explicit
   feature allowlists. Keep native labels, targets and provenance separate.
8. Use a new run namespace after approval; never overwrite historical results.

## Verification

Run from the repository root with the existing Python environment:

```powershell
.venv\Scripts\python -B -m pytest ml/tests/test_experiment_inputs.py ml/tests/test_experiment_integration.py ml/tests/test_preflight.py -q -p no:cacheprovider
```

Use a writable task-specific TEMP/TMP directory if Windows denies pytest's
standard temporary directory. No scientific dependencies are needed for these
synthetic checks. They do not execute analytical notebooks or inspect research
holdout rows.

## Next research gate

Resolve the dataset/language/evidence decisions, source provenance and evaluation
exposure plan before corpus integration or training. Prepare source-specific
schema and grouping fixtures after those decisions; do not interpret a passing
synthetic test as permission to adopt a research dataset. Model selection and operational
finalization remain later milestones.


## Current source-selection checkpoint

No primary email benchmark is selected. The notebook loader is disabled and
preflight reports the missing selection; the historical source-confounded
population is not automatically reactivated. `MappedEmailAdapter` uses caller-
supplied source-column names and an explicit identity/label mapping. Synthetic
fixtures use a fictitious source and do not endorse any corpus.
