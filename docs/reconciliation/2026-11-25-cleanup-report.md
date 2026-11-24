# Canonical workspace cleanup — 25 November 2026

## Outcome and Git state

The active root was reduced from **53 to 26 entries**. Cleanup is based on the
published reconciliation commit `43ea1e6d4fc8a22ab3630ee9532b886f567aa15e`, on branch
`cleanup/canonical-organization-20261125`. No main merge occurred. Automatic
approval review rejected the attempted main fast-forward because an explicit
approval of that exact merge was not present in a trusted user message. The
cleanup branch includes the reconciliation and will require one final main-merge
approval. Remote main remained `ee7976ef04aa6060b0c7a5e18e5a6529e0af695e`.

Actual Git evidence showed the original canonical root on the reconciliation
branch, not `engineering/dhanwil-completion-20261115`. Local VS Code Git refresh
was disabled and the old saved workspace selected a separate Transformer
worktree. `SE-BRL.code-workspace` now opens the canonical root, enables Git refresh
and avoids automatic discovery of historical repositories. Local editor settings
were repaired; the old saved configuration is archived. No live VS Code status
bar refresh is claimed.

## Physical organization and preservation

One local-only archive holds historical evidence at
`../SE-BRL-Local-Archive/canonical-20261125/`:

| Action | Actual result |
|---|---|
| Recorded relocations | 49 operations: 25 directories and 24 individual files; dependency file trees were not enumerated for a misleading leaf-file total |
| Historical root directories archived | Scientific-validation and Transformer-release worktrees, R22 integration repository/audit, reconciliation recovery, five engineering evidence directories |
| Exact duplicate copies removed | 497 files; each deletion rechecked SHA-256 against its retained canonical artifact or existing content-addressed recovery object |
| Disposable files removed | 469 Python/pytest-cache files and empty logs |
| Logical file bytes removed | 70,974,388 duplicate bytes plus 6,628,830 disposable bytes: **77,603,218 bytes**; physical allocated disk recovery was not measured |
| Logs | 17 root logs relocated; three empty logs removed; useful logs retained under ignored `.local/logs/`; 16 previously tracked root logs removed from the Git tree |
| Active research consolidated | Nine scientific run directories, two source-snapshot directories, six annotation CSVs and the selective-review directory moved into canonical experiment paths |
| Verified Transformer environment | Moved, without duplication, from the old R22 checkout to canonical `.venv-transformer/`; canonical `.venv/` and `node_modules/` retained |

Registered worktrees were moved through Git. The historical R22 repository's
linked worktree pointers were repaired after its main directory moved. Its
incomplete initializing worktree retains the original staged-deletion state and
lock; it was not silently reset or treated as a valid production checkout.
Windows long-path support was enabled in that archived repository's local Git
configuration; all checkpoint refs and commit histories remain intact.

The root now focuses on `apps`, `backend`, `database`, `docs`, `experiments`, `ml`,
`packages`, `research`, `scripts`, `tools`, original proposal documents, essential
configuration, canonical dependencies and ignored local state. Scientific run
outputs and frozen E2 matrices are available directly through `experiments/`.
Necessary local-only directories are excluded from editor searches/watchers.
This follows physical relocation and deduplication, rather than substituting for it.

**Remaining local restrictions:** Windows denied relocating `.r22-review` and
`.r22-vera` and denied access to the root `.pytest_cache` and several historical
pytest caches. Those items are preserved in place or in archive quarantine;
no ACL, ownership, repository visibility or access permissions were changed.
These are unresolved local housekeeping items, not missing scientific inputs.

## Archive index and recovery

The single cleanup index is ignored `.local/cleanup-state.json`, with its archive
alias at `../SE-BRL-Local-Archive/canonical-20261125/cleanup-state.json`. It records
original/destination paths, categories, hashes, retained duplicate copies,
disposable counts, access limitations and verification. Original reconciliation
inventories, patches and content-addressed objects remain under archive
`recovery/reconciliation/`. Original engineering reports/manifests and source
variants remain archived; historical manifests were not rewritten.

Resolve an old path without opening its contents:

```powershell
.venv\Scripts\python.exe tools/reconciliation/resolve_local_path.py .scientific-validation-20261117/experiments/e2_enrichment_20261124/v42_matched_execution_inputs/e2-c.csv
```

The resolver applies the longest relocation prefix and then exact deduplication
mappings. A recovery-object destination contains the original bytes; copy it to
the desired historical filename only when restoration is needed, without
overwriting current work. The index and existing Git histories avoid another
full-project backup. Archived maintenance scripts document the operations.

## Targeted verification

| Check | Result |
|---|---|
| Archived Git heads, original incomplete index, pinned FP32 hash, scientific gate, notebooks and Chapter 5 paths | 9/9 checks passed; 34 Chapter 5 path literals resolve |
| Canonical and archived R22 Git connectivity | Both passed; archived Git long-path support repaired the initial path-length diagnostic without changing refs |
| Historical research artifact hashes | 84/84 original run, source-snapshot and Chapter 5 files match the prior reconciliation inventory |
| Frozen E2 verification after organization | 58 checks passed; all five 15,011-row matrices, original baseline and receipts accessible; 14 candidate modules parsed |
| Review/context safety selection | 38 Python tests passed; process-wide no-fit guard recorded zero attempts and zero fitting executions |
| Local browser worker/privacy selection | 8 tests passed across two files |
| Browser packaging | Passed approved byte/hash checks; 12,892,761 asset bytes packaged, no model weights included |
| Transformer and ONNX environments | Imports passed at their new canonical paths |
| Backend health smoke | HTTP 200 / status `ok`; existing Starlette/httpx deprecation warning retained |
| Notebook documents | Eight structurally parsed without execution; one pre-existing code-cell syntax issue in `01_data_audit.ipynb` remains unchanged |

A frozen-contract check initially exposed CRLF/LF working-byte differences from
reconciliation. Fourteen files were restored from the archived verified checkout
only after checking exact approved hashes, newline-equivalent content and
unchanged normalized Git source. The frozen contract check then passed. Neither
approved contracts nor model pins were regenerated or relaxed.

The prior 775 Python, 189 scientific, 50 frontend, typecheck/lint/build results
were reused. Broad regressions, extraction, historical benchmarks and fitting
were not repeated. No application component or behavioral rule semantics changed.

## Research and publication boundaries

Both researchers' accessible contributions, approved R22 implementation, four
dimensions, twelve indicators, modality contracts, deterministic evidence and
review-only local Transformer constraints remain preserved. Vera's inaccessible
unpublished device work is still outside the verified scope.

Frozen V4.2 retains its 35-rule registry, context guards, dictionaries, classifier
configurations, nested engine, calibration/statistical implementations,
coordinator, restricted development inputs, original baseline, all five matched
matrices, freeze/extraction receipts, representation assessment and exact-run
packet. AP 0.551002 and F1 0.560748 remain exploratory in-sample representation
diagnostics. Actual V4.2 classifier fitting has not occurred; scientific gate and
authorization records remain unchanged.

Only code, documentation, ignore/editor configuration and removal of tracked
logs belong to this cleanup commit. Archives, environments, model caches,
restricted snapshots, row-level records and local logs remain excluded. The
existing inherited public LFS concern is unchanged; cleanup adds no LFS objects.
The final commit and publication SHA are recorded in the local index and final
response. Main synchronization remains pending explicit final merge approval.
