# Isolated FP32 browser compatibility harness

Experimental verification only. Pyodide preserves the existing Python review
implementation for comparison; it is not a proposed production extension dependency.

Prerequisites: the existing verified local model snapshot and FP32 ONNX artifact,
the pinned ONNX tooling environment, installed Chrome matching `packages.v1.json`,
and local Playwright Core 1.62.1. No browser/model auto-downloads are implemented.
If the agent runtime does not supply Playwright, set `SEBRL_PLAYWRIGHT_CORE` to an
existing exact-version package directory. All executable files must match the pins.

1. Verify approved cached package archives with
   `python scripts/acquire_browser_verification_assets.py`.
   Use `--acquire` only after explicit approval for the three pinned archives.
2. Run `.venv-transformer/onnx-tooling/Scripts/python -B scripts/prepare_browser_minilm_reference.py`.
3. Copy `reference.json` and `preparation.json` from
   `.venv-transformer/onnx-tooling/browser-reference/` into
   `.venv-transformer/browser-harness/data/`.
4. Run `node tools/verification/browser-fp32/run.mjs`.

The native reference is never supplied to the model/review worker. The worker
gets only frozen inputs and unchanged framework source. Its independent tokenizer
output is checked before model loading; final review reports use actual WASM model
outputs. Neutral discovery placeholders are discarded. Resource-budget tests replay
actual model scores, matching the prior 24-case suite.

The loopback server accepts only allowlisted GETs. CSP permits local scripts and
WASM but no `unsafe-eval` or remote connections. Chrome's sandbox is retained.
Chrome is fully offline during analysis; one terminated-worker restart is tested.
A deliberate post-analysis remote fetch must be rejected by CSP. Generated weights,
packages, profiles, references and results stay under ignored `.venv-transformer/`.

Memory snapshots cover only this isolated Chrome instance. Sum of process lifetime
peaks is an upper bound for observed live processes, not a simultaneous total peak.
Pyodide linear-heap measurements do not represent all of its resident overhead.
