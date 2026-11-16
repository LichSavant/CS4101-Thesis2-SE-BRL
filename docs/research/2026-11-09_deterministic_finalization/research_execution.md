# Research execution — BLOCKED, no research runs

Fresh invocation of `.venv\Scripts\python -B -m ml.preflight
--research-gate-only` returns native Python exit **2**, ten FAIL checks,
`research_fitting_enabled=false`, `scientific_authorization_verified=false`.
No filesystem/data reads are made by that gate-only function. See
preflight_resolution.md for independent evidence obligations. The PowerShell
tool initially represented the nonzero command as shell exit 1; a separate
explicit `$LASTEXITCODE` check confirmed native exit 2. This is expected refusal,
not a failed research experiment or a passed readiness test.

| Execution category | This sprint |
| --- | --- |
| Source/development payload inspection, screening or real feature preparation | Not performed |
| Group/partition/fold generation or assignment transfer | Not performed |
| Research candidate fits/tuning/calibration/threshold selection | **Zero** |
| Historical sealed-test outcomes/prediction rows read | **Zero** |
| Final calibration, selected-system freeze or final evaluation | Not performed |
| Genuine synthetic classifier/calibrator fits | Performed in tests and one bounded synthetic save/reload smoke; explicitly SYNTHETIC RESULT |
| Scientific approvals/population/rule/assignment changes | **None** |

No accepted development D9 handoff or authentic run authorization was found.
The always-closed guard is not relaxed. The general Python estimator interfaces
are trusted engineering ports, not a system-wide sandbox capable of preventing
arbitrary code from reading files; no research loader/launcher was added.

Next authorization boundary: complete the factual source records and accept the
population, prospective identity/assignment/exposure, operational rules,
dictionaries and restricted development custody in approval_packet.md. Then
implement/verify that accepted no-fit path and its authenticated artifact
verifier. Freeze experiment settings and authorize an exact bounded development
run only after actual-data checks. The reserved calibration/test scopes remain
separately controlled; historical exposure cannot be reset by new IDs or splits.

The first genuine E1/E2/E3 experiment is **not runnable on research data now**.
No unapproved new dataset, behavioral supervised model or transformer is needed
to explain this block. Do not execute historical Notebook 05 wholesale against
repaired/prospective inputs.
