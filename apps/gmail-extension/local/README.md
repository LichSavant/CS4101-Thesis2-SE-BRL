# Local-only development integration

Default processing is local-only. The popup opens one visible extension-origin
workspace; an origin-wide Web Lock permits one dedicated model worker. No
offscreen permission, all-sites permission, `tabs`, `unlimitedStorage`, Pyodide,
remote code or server is required. Closing the workspace or pressing Unload
terminates its worker. Model initialization is lazy, rule-first and occurs only
when canonical review actually requests an eligible NLI score. Analysis queues
are bounded to one operation; each artifact's memoized scores are discarded after
its operation. Canonical 64-unit / 512-call budgets and 512-token abstention stay
unchanged. A failed model never falls back to FastAPI or becomes negative evidence.

`scripting` is the sole added permission: it is used only after an explicit click,
under the existing temporary `activeTab` grant, to capture a selected ordinary
webpage. Forms, inputs, editable areas and scripts are excluded. Gmail continues
to use its selected-message adapter and centralized selectors; bodies remain
disabled. URLs remain a separate non-content modality. Identity truth is never
inferred: independent audited references are unavailable during ordinary user
capture, and those gates stay unavailable.

Local analysis consent and model-install approval are separate. The development
installer explicitly imports an existing approved local FP32 ONNX file; there is
no network acquisition strategy or model downloader. Bytes, SHA-256 and revision
must match the trusted packaged manifest. One atomic IndexedDB record activates
the complete verified Blob; interrupted/failed transactions cannot activate a
partial model. Quota checks precede writes. Every new model session rechecks all
bytes; corruption removes the bad cache and returns explicit semantic unavailable
states, preserving basic rules. Removal and reinstallation are supported.

Only settings/consent flags persist in chrome.storage.local; model bytes persist
in origin IndexedDB. Artifacts, bodies, URL parameters, scores and reports stay
in memory. There is no sync storage or analytics. Legacy research mode remains
explicitly selectable, with a metadata-upload warning. Local mode blocks all
backend API, feedback, tracking, dashboard and persisted-result paths; in-flight
legacy requests are aborted on a mode change. It cannot retroactively retract
content previously sent under an explicit legacy-mode selection.

Build using existing approved local dependencies/assets:

```powershell
npm.cmd run build:local --workspace @phishing-defense/gmail-extension
npm.cmd test --workspace @phishing-defense/gmail-extension
node scripts/verify_loaded_mv3.mjs
node scripts/verify_mv3_acquisition.mjs
node scripts/verify_mv3_install_recovery.mjs
```

The packaging step verifies the approved assets and copies executable JS/WASM and
tokenizer data into ignored `dist/local`. Model weights are never packaged or
committed. Load `apps/gmail-extension/dist` as an unpacked development extension.
Import `.venv-transformer/onnx-tooling/minilm-fp32.onnx` explicitly in its workspace.
Keep source license notices with those packaged assets.

Verification uses isolated Chrome profiles and Chrome's documented unpacked
extension debugging interface (`--enable-unsafe-extension-debugging` over a local
debugging pipe), not security-policy bypasses. Sandbox/CSP remain enabled; normal
packaged code is tested against the CSP, avoiding debugger eval privileges.
Gmail/web pages are synthetic route fulfillments, never actual account content.
Quota exhaustion is simulated, not induced by filling a real disk. Corruption,
worker interruption, import interruption, removal and reinstall are real local
operations. Results, profiles and model caches stay under ignored
`.venv-transformer/mv3-verification/`.

This is verified development functionality, not production deployment, scientific
validation or Chrome Web Store approval. There is no public model distribution
endpoint. FP32 storage and memory remain substantial; no lightweight claim is made.
Gmail layout compatibility is verified only against synthetic selected-message DOM.
