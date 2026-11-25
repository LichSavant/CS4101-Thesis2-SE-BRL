# E2 performance sprint — continuation handoff
Research: SE-BRL: A Transformer-Augmented, Modality-Aware Neuro-Symbolic
Architecture for Constraint-Governed Social Engineering Behavior Inference and
Explainable Phishing Detection. Dhanwil Nick M. Alcover and Vera Marie Therese A.
Orbello, University of San Carlos.

## Current checkpoint
Branch: research/e2-preparation-20261125.
Preparation checkpoint: 4c3918e2dec9a0aca03f9db77a4010a1870099e0.
Provenance implementation: 8a8b736a2c52fa5da6e6a1f16f6a243357e003d3.
Base main: bb167bd6367cca574885d728f1442bc903c92d9e (cleanup merged as PR #19).
Original preparation details and primary dataset citations remain in Git at 4c3918e.
No history, frozen candidate, original result, partition or scientific gate changed.

## Substantive intervention
ml/evidence_provenance.py preserves which of the existing 35 deterministic rules
supplied qualifying evidence. Existing E2-E retained distinct-rule counts but lost
rule identity. This is one label-blind information-preserving representation,
not new regex rules, arbitrary statistics, embeddings, class proxies or NLI scores.
Its 131 predictors retain the frozen 96-feature V5.3 prefix plus 35 rule indicators.
Unevaluated/unavailable opportunities remain missing, never negative evidence.
Semantic output cannot supply these predictors or promote unsupported indicators.
Coverage is deliberately unchanged; independent truth is not inferred.

One development extraction completed: 15,011 rows, 274.63 seconds; outputs under:
experiments/e2_enrichment_20261124/provenance_representation_run01/
Bindings: run_binding.json; predictor_dictionary.json; progress.json.
Complete outputs: e2-provenance.csv; extraction_receipt.json;
representation_assessment.json (written only after complete extraction).
Every row must reproduce all 96 frozen V5.3 values before it is accepted.
Metadata are isolated from preprocessing; only existing authorized message fields
reach the unchanged rule engine. No reserved observations or new sources are used.
Rows flush every 500 observations before any target-aware diagnostic assessment.
No classifier fitting is performed. Existing delivery/scope verification is reused;
this instruction authorizes engineering exploration, not scientific admission.

## Verification and results
8 focused encoder tests passed; process-wide no-fit guard: zero fitting attempts.
These test information retention and authority/missing-state boundaries, not
authored phishing accuracy. Previous 22 preparation tests are reused.
Frozen V5.3 E2-D diagnostics: AP 0.553640 / F1 0.564326.
Frozen V5.3 E2-E diagnostics: AP 0.569835 / F1 0.568381.
Population: 15,011 development rows; 454 supported and 641 unsupported phishing;
240 supported legitimate; 224 E2-E patterns and 67 variable predictors.
New provenance outcome: diagnostic AP 0.570329 / F1 0.568738.
240 patterns (+16); AP gain 0.000494; F1 gain 0.000357; coverage gain zero.
All 96 V5.3 values matched on every row; supported phishing remains 454/1,095.
Any new AP/F1 remain explicitly optimistic target-aware in-sample diagnostics.
Actual classifier AP/F1 are unmeasured. No 0.80 or 0.90 objective is established.

## Admission and external dependencies
All ten checks in docs/research/2026-11-17_scientific_validation/research-gate.json
remain unaccepted. Do not pass authorization_verified=True based on this work.
Independent human annotations, authenticated identity/delegation references,
accepted source/label/custody decisions, matched E1/E2/E3 dictionaries and exact
evaluation settings plus applicable adviser/institutional approval remain needed.
Missing independent references leave authority/impersonation/brand unevaluated.
The existing 200-record pilot tooling remains gated; no real packets were made.
Do not relabel spam as phishing or treat exposed holdouts as untouched evaluation.
Current population is completely source–class confounded.
Previous primary-source investigation remains: MeAJOR is composite/overlapping;
IWSPA access/license/version needs acceptance; Phishing Pot lacks a comparable
legitimate class. No new corpus was ingested. Prefer a separately authorized
prospective population with comparable collection and independently justified labels.

## Exact resume instructions
Do not rerun extraction or regenerate existing outputs.
The run exited successfully. Historical progress.json is only the last batch;
extraction_receipt.json and representation_assessment.json establish completion.
The execution log contains Pandas dtype-fill FutureWarnings, not failures:

    Get-Content .local/logs/evidence-provenance-run.log -Tail 8

After completion, read the actual aggregate result:

    Get-Content experiments/e2_enrichment_20261124/provenance_representation_run01/representation_assessment.json

Only if extraction_receipt.json exists and assessment is absent, resume downstream
assessment without extraction:

    .venv/Scripts/python.exe -B -m ml.evidence_provenance --assess experiments/e2_enrichment_20261124/provenance_representation_run01

Never overwrite partial evidence after a failure. Diagnose the specific mismatch
using the persisted prefix and log. The original instruction hash and all run
bindings are retained in the output. No classifier evaluation or new rule changes
may proceed merely because an exploratory representation improves diagnostics.
Status: implementation/software-verified;
development-assessed; not independently behaviorally validated, scientifically
admitted or classifier-evaluated. Neither 0.80 nor 0.90 objective was achieved.
