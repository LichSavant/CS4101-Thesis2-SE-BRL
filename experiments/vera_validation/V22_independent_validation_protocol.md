# SE-BRL V22 — Independent Behavioral Validation Protocol

Status: PROPOSED / NOT YET EXECUTED
Scope: Behavioral indicator validation only.
No sealed-test access or experiment fitting is authorized.

## 1. Annotation instrument

Use the repository's existing codebook:
`ml/se_brl/codebook.v0.1.0.json`

Assess all twelve indicators individually using the original
artifact and permitted provenance information.

## 2. Blinding

Independent annotators must not inspect:
- SE-BRL semantic scores or predicted indicator states
- V13–V21 inference outputs
- AI-reviewed annotation decisions
- Previously completed reference labels for assigned items

Do not automatically copy AI-reviewed annotations into the
independent annotation workbook.

## 3. Allowed reference judgments

- supported: qualifying behavioral evidence is observed
- absent: required evidence is assessable but the behavior is absent
- unavailable: required content or provenance makes assessment impossible

Record uncertainty separately rather than inventing a definitive label.
Preserve the evidence span, reasoning, and modality for decisions.

A bare URL or technical-only record does not provide evidence for
content-dependent behavioral conclusions.

Impersonation and brand exploitation require appropriate independent
identity or brand provenance; suspicious wording alone is insufficient.

## 4. Independence and provenance

Record the annotator's role, qualifications, review date,
codebook version, and whether model output was visible.

Record disagreements and adjudication separately.
Do not label an AI-assisted review as independent human ground truth.

## 5. Coverage

Report observed annotation coverage per indicator.
Missing cells must remain missing.
Do not infer accuracy for indicators without evaluable references.

Use group-aware separation where artifacts have shared origins,
near-duplicates, or matched counterfactual relationships.

## 6. Evaluation

Only after independent reference judgments and an approved
decision policy exist:

- Freeze the model, policy, prompts, and threshold configuration.
- Compare predictions to independent reference judgments.
- Report confusion matrices, precision, recall, and F1 by indicator.
- Report abstention and unavailable rates separately.
- Include support counts and uncertainty intervals.
- Distinguish development, calibration, and sealed-test data.
- Never use sealed-test results for model or policy selection.

Do not score abstentions as ordinary negative predictions without
an explicitly justified evaluation protocol.

## 7. Research-release conditions

E2/E3 integration remains blocked until:
- scientific semantics are approved;
- inference decisions have independently supported validation;
- artifacts, datasets, and policies have verified lineage;
- the appropriate research authorization is recorded.

Passing software tests does not substitute for empirical validation.
