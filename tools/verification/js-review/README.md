# Isolated JavaScript review compatibility implementation

Phase 7B passes the original 187 reports plus targeted synthetic regressions:
371 complete reports, 93 HTML preprocessing cases, and 102 strict mailbox parser
cases agree exactly with the immutable CPython 3.12.10 oracle. All 24 frozen cases,
13 independently mutated report rejections, six consent/adapter cases and Unicode
offset conversions also pass. Compatibility is bounded by these synthetic cases;
this is not scientific validation or approval for extension integration.

Run with existing local assets; no installation or download:

```powershell
.venv-transformer/Scripts/python.exe -B scripts/freeze_js_review_contracts.py --check
.venv-transformer/Scripts/python.exe -B scripts/verify_js_review.py
```

The runner generates Python oracle reports afresh, then compares complete JS
reports and scorer-call counts. Golden reports remain in the test host and are
never passed into `reviewRecord`. Model/tokenizer boundary cases replay the
previously verified native scores and oversized-input states; this task does not
load a model or claim new tokenizer/WASM inference verification.

`review.mjs`, `contracts.mjs`, `mailbox.mjs` and `python-url.mjs` form the browser-safe
runtime, with no third-party dependency, Python interpreter, network, storage or
extension imports. Static contracts contain patterns, codebook, pinned model
metadata, entity/casefold tables and source hashes, never inferred labels.
Canonical sources, hypotheses, thresholds, model weights and research gates are
unchanged. All semantic evidence remains candidate-only; deterministic labels
are authoritative, learned values remain null, and predictor export is blocked.

HTML links require explicit authorization. Only visible start-tag href/action/src
attributes are collected, in canonical attribute-priority order. The implementation
retains original enclosing-tag code-point offsets, source spelling, relative-URL
joining, entity decoding, duplicate ordering, quota checks and URL validation.
URLs are never fetched. Text URL scanning and quoted/hidden content follow the
existing Python rules rather than imposing a new extraction policy.

The mailbox parser translates CPython's strict pre-validation, address-list state
machine and post-validation. Tests cover nested/escaped comments, quoted names
and local parts, folding, obsolete routes/groups, multiple addresses and malformed
syntax. Invalid parsing yields the same empty pair, never invented identity proof.
Identity evidence still requires independently supplied audited references.
See `PYTHON-NOTICE.txt` for the source license and translation attribution.

The full oracle bundle and result stay in ignored `.venv-transformer/js-review/`.
Results include fixture, runtime, stdlib and tool hashes. A compact committed
summary is in `docs/research/js-review-parity.json`. Timing covers Node module
initialization and complete review plus validation, independently of ONNX. Whole
verifier RSS includes fixtures and golden reports; it is not incremental browser
memory. Browser/MV3 integration and resource verification remain separate work.
