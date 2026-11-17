# Live FP32 MiniLM + JavaScript review verification

Isolated engineering harness, never imported by the production MV3 extension.
No Pyodide or Python source is served to or executed in the browser. Python is
an external oracle only. No installation, browser download or model acquisition
is performed by these commands.

```powershell
# Existing verified environments and approved local assets are prerequisites.
.venv-transformer/onnx-tooling/Scripts/python.exe -B scripts/prepare_browser_js_live_reference.py
node tools/verification/browser-js-live/run.mjs
```

The first command verifies the Phase 6 artifact and Phase 7B runtime hashes,
checks the seven-file pinned snapshot, and runs the original `PinnedLocalNliScorer`
and Python `review_record` on synthetic inputs. An observation-only model hook
captures logits/tokens. Its process audit denies network operations, subprocesses,
research input files and writes outside the ignored ONNX tooling directory.
The unchanged frozen payload is taken from its hash-verified Phase 6 bundle.
Eight independent cases exercise authorized HTML links, Unicode, nested sender
comments, quoted and malformed headers, context gates, oversized review units,
quoted body and unaudited identity. The four original guards retain their names.

The second command verifies local Chrome/Playwright, approved tokenizer/ORT assets,
the FP32 ONNX hash and the exact Phase 7B runtime files. A dedicated browser worker
connects `reviewRecord` directly to independent JS tokenization and real ONNX
CPU/WASM inference. It receives only synthetic inputs, hypotheses and model
identity, never golden tokens, scores, logits, reports or Python modules. Identical
requests are memoized within each run; caches start empty and all scores originate
from that run's real model. The original budget guard's name contains `replay`,
but its scores now come from this live run, not a prerecorded score bundle.
NaN scores occur only in the explicitly negative malformed-score guard.

The host compares every token ID/mask exactly, NLI maxima/decisions exactly and
complete review/preprocessing structures exactly. Candidate probability matrices
are compared separately for every distinct request under the unchanged FP32
tolerances: logits atol 1e-4 / rtol 1e-3; probabilities maximum absolute 1e-4.
Score matrices are the only report fields normalized for structural comparison.
Deterministic labels/evidence are checked against symbolic-only results in both
runtimes; accepted labels never come from NLI. Consent rejection is checked
separately without inference. No rules, hypotheses, thresholds or gates change.

Only allowlisted local GET assets are served. External requests are blocked,
Chrome's sandbox and strict self-only CSP remain enabled, and the browser context
is switched fully offline before any analysis. Zero local or external requests
during analysis is required. Pyodide assets are excluded from the server map.
This is strict-CSP loopback browser verification, not loaded-MV3 verification.

Results and native oracle assets stay in ignored
`.venv-transformer/onnx-tooling/browser-js-live/`. The committed summary contains
hashes, tolerances, per-case parity, latency and memory scope. Cold initialization
includes tokenizer/runtime imports, local model fetch/hash and WASM initialization,
subtracting explicitly measured host memory-observation pauses. Warm latency is
actual `session.run`, excluding the first forward, tokenization and memoized hits.
Per-review latency is a mixed synthetic workload with shared-request caching and
context/unavailable cases; it is not a representative mailbox performance claim.

Memory snapshots compare the same isolated Chrome instance before worker creation,
after JS/tokenizer load, at model readiness and after analysis. Process lifetime
peak sums are upper bounds, not an exact simultaneous aggregate peak. No claim of
lightweight production memory usage follows from removing Pyodide.

## Minimal subsequent extension work

1. Add an isolated, disabled-by-default local mode and consent screen. Gate every
   analysis, tracking and feedback upload path; never silently fall back to FastAPI.
2. Package these exact JS/WASM assets in an extension-origin worker/context. Add
   only the MV3 CSP/permissions needed after testing, without weakening privacy.
3. Implement a user-approved, hash-pinned model installer with quota checks,
   atomic cache activation, corruption recovery, explicit removal and offline use.
4. Re-run this live suite in the loaded MV3 extension, including worker restart,
   disabled-AI, adapter authorization, cache failures and no-outbound-content tests.
   Set explicit resource budgets: FP32 storage and resident memory remain large.

No production extension edits, deployment or research release are part of this task.
