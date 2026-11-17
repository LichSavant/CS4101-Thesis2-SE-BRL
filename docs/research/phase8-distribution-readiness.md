# Phase 8 distribution assessment — not a release approval

The working installer remains explicit local-file import of the approved FP32
ONNX bytes. No download code, new model, executable asset or external service was
introduced in Phase 8.

A future hosted installer needs approval for an exact HTTPS origin and the exact
derived ONNX artifact. Keep runtime JS/WASM and tokenizer assets packaged; install
model data only, with pinned revision, size, SHA-256 and provenance in the signed
extension. Any artifact change must require a reviewed extension/manifest update,
not an unsigned mutable "latest model" configuration. Keep the existing local-file
fallback. Consider a separately scoped installer context with a fixed URL, optional
host grant, explicit per-install consent, omitted credentials/referrer, bounded
size, atomic activation, cancellation, integrity checking, removal and rollback.
The analysis worker must retain self-only networking regardless of installation
permissions. None of that network acquisition is implemented or authorized here.

Before Web Store submission, verify redistribution rights/notices for the exact
model export and packaged dependencies, publish a privacy policy and accurate data
disclosures, justify permissions, and decide whether a public-only build should
omit the isolated legacy research backend and localhost permissions. Test supported
hardware/browser combinations and real Gmail layout compatibility with separately
authorized non-research fixtures. Document the large model/RAM requirements and
review-only semantics; do not describe the prototype as scientifically validated.

Chrome's [remote-hosted-code guidance](https://developer.chrome.com/docs/extensions/develop/migrate/remote-hosted-code)
distinguishes data from remote executable JavaScript/WASM; this is not an approval
of a specific ONNX distribution scheme. Its [disclosure requirements](https://developer.chrome.com/docs/webstore/program-policies/disclosure-requirements)
and [Limited Use policy](https://developer.chrome.com/docs/webstore/program-policies/limited-use)
require a release review of actual behavior and disclosures, including optional
legacy uploads. No Web Store approval or legal compliance determination is claimed.

The performance change uses Chrome's documented
[cross-origin isolation](https://developer.chrome.com/docs/extensions/develop/concepts/cross-origin-isolation)
and ONNX Runtime's [CPU/WASM thread configuration](https://onnxruntime.ai/docs/tutorials/web/env-flags-and-session-options.html).
COOP/COEP become stricter; existing script/worker/connect CSP and permissions are
unchanged. Only packaged same-origin worker modules are used. Thread counts are
bounded to the tested four on capable hardware, two on smaller devices, and one
when isolation/threading is unavailable. This is not a guarantee of fastest
performance on every device.
