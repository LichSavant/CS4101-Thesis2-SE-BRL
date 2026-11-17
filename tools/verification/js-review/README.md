# Experimental JavaScript review port — incomplete

Not approved for extension integration. Canonical Python remains authoritative.
The current differential suite deliberately exits nonzero: two accepted canonical
inputs are explicitly rejected, rather than approximated, by the draft port:

- Authorized HTML link extraction (`html_link_extraction_not_yet_ported`).
- RFC5322 sender comments (`unsupported_mailbox_syntax`).

The other 185 complete reports agree exactly, including all 12 indicators,
canonical email/webpage regression templates, score failures, context and identity
gates, code-point evidence offsets, deterministic labels, and resource budgets.
All 24 frozen cases are reused. Token-boundary guards replay previously verified
scores and unavailable states; this suite does not execute a tokenizer or model.
Passing frozen cases is not full canonical compatibility or scientific validation.

Run with existing local assets; no installation or download:

```powershell
.venv-transformer/Scripts/python.exe -B scripts/freeze_js_review_contracts.py --check
.venv-transformer/Scripts/python.exe -B scripts/verify_js_review.py
```

The second command generates Python oracle reports afresh from synthetic inputs,
then compares complete JavaScript reports, score-call counts, 13 independently
mutated invalid reports, six consent/adapter cases, and Unicode offset conversions.
Golden reports are held only in the test host, never supplied to `reviewRecord`.
The existing frozen native-score bundle must match its provenance hash. No model
loading, research dataset access, Python runtime in JavaScript, network requests,
persistence or extension imports occur in the runtime module.

`contracts.mjs` contains static rule patterns, codebook, pinned model metadata,
standard-library entity/casefold tables and source hashes. It contains no golden
labels or review outcomes. Generation never edits canonical files. Runtime
footprint is `review.mjs` plus `contracts.mjs`; no third-party runtime dependencies.

`result.json` and the full differential bundle remain in ignored
`.venv-transformer/js-review/`. Timing is Node module initialization and complete
review/validation processing, independent of ONNX. Whole-process RSS includes
fixtures and oracle reports; it is not browser incremental memory. Browser/MV3
benchmarks are deferred because compatibility failed. No arbitrary-input parity
claim is made for the draft HTML scanner, mailbox parser, JSON/URL edge semantics
or incomplete input-validation coverage.

Next work is exact source-preserving HTML/link and mailbox compatibility, then
broader preprocessing rejection/acceptance differential coverage. Keep the gate
failing until every accepted canonical case agrees; do not skip boundary cases,
weaken rules, rewrite Python, or connect this draft to production.
