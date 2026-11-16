# D5. Fail-closed Email research admission

**Overall FAIL. research_fitting_enabled=false.** This is not a source approval,
new population, executable experiment configuration or authorization receipt.

`ml/preflight.py` now provides `research_fit_gate()`,
`require_research_fitting()` and `--research-gate-only`. The normal metadata
preflight also includes this gate. The gate-only command performs no corpus,
manifest, dataset, notebook or credential reads. It reports all ten obligations;
the guard raises the stable `research_fitting_not_authorized` error.

| Requirement | Research PASS/FAIL now | Verified software/evidence and exact shortfall |
| --- | --- | --- |
| 1. Approved Email population | **FAIL** | Proposal default/CEAS exception understood; no accepted prospective population/version/eligible ID universe |
| 2. Verified source/label semantics | **FAIL** | Source fingerprints/aggregate schemas previously recorded; acquisition/license and native CSV class meanings still incomplete |
| 3. Accepted identity/lineage | **FAIL** | Historical recovery closed BLOCKED; prospective identity/ingestion proposal unaccepted and unexecuted |
| 4. Accepted grouping/partitions | **FAIL** | Supplied historical isolation and validators exist; prospective relationship/allocation/exposure protocol Pending |
| 5. Authorized development custody | **FAIL** | Strict development-only consumer exists; no named real delivery or custody approval |
| 6. Approved deterministic definitions | **FAIL** | Canonical taxonomy and candidate rules/tests exist; operational semantics/language/locators/partial aggregation not frozen |
| 7. Approved matched dictionaries | **FAIL** | Ordered core/E2/E3 candidate prepared; actual E1 scope/materialization and rule dictionary acceptance missing |
| 8. Approved candidate/evaluation settings | **FAIL** | Families/ranges/hierarchy specified by paper; nesting/budgets/calibration/score/tolerance/benchmark choices Pending |
| 9. Research leakage safeguards verified | **FAIL** | Synthetic gates and historical recorded groups pass; no accepted-data relationship/source/transform isolation audit for the prospective version |
| 10. Research reproducibility configured | **FAIL** | Exclusive hashed synthetic bundles exist; accepted real run/input/model/environment/persistence outputs are not frozen or complete |

FAIL means applicable accepted-branch evidence has not been verified. It does
not mean all software or earlier work is absent. In particular, source role
requirements and current software tests do not themselves supply a frozen
dataset, and deterministic features need no supervised behavioral ground truth.

## Deliberately limited admission implementation

There is currently no trusted accepted-evidence verifier or real-data research
launcher. Therefore the gate has no public approval switches, JSON override,
automatic document-discovery route or synthetic-test-based promotion. All ten
checks remain closed. The guard also stays closed; changing a returned report
dictionary does not enable fitting. This avoids treating a reference string or
new Markdown proposal as a scientific freeze.

After researchers accept concrete artifacts/procedure, implement the minimal
accepted-bundle verifier and guarded research entry point, including exact
versions/hashes/scope/custody/assignment/features. A signed-looking string alone
cannot authenticate the facts. This work must precede research fits; it is not
claimed complete or immediately runnable merely after document sign-off.

The guard is an explicit research entry port, not an interception of every
possible Python estimator call. Existing synthetic runner/adapters remain
available for authorized generated fixtures; arbitrary caller code remains
trusted and is not sandboxed. There is no newly enabled real-data training path.

## Invocation and verification

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.venv\Scripts\python -B -m ml.preflight --research-gate-only
```

Expected native Python exit code **2**, status FAIL, ten FAIL checks, fitting
false. Default `--root` has no effect on this gate-only inspection. Tests prove
no filesystem access, a fresh report despite caller mutation, no self-declared
approval switch, and a read-only CLI even with a nonexistent corpus root.

The original broader preflight still checks metadata prerequisites and never
authenticates scientific authorization. It can inspect raw schemas, so the
gate-only command is used for this sprint's actual workspace check. No analytical
notebook, real preparation or fitting is executed. Full test commands/results
and the expected nonzero gate exit are distinguished in README.
