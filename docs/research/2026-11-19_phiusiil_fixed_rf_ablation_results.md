# PhiUSIIL U1 — Exploratory Fixed Random Forest Technical Ablations

**Reporting status:** Descriptive development-fold comparison; local run reported `ABLATIONS_COMPLETE` with 10 new fits. Recorded hashes for the six ablation output files were subsequently checked against `completed.json`. The manuscript-level comparison below has been compiled from the reported metrics; independent row-level paired checks against both saved prediction files have not yet been performed for this report.

**Design:** 115,563 observations; the same five group-isolated development folds (1–5); Random Forest with 300 trees, `class_weight=balanced`, Gini, `max_features=sqrt`, `min_samples_leaf=1`, `bootstrap=True`, `max_depth=None`, `n_jobs=1`, seed 42; reject missing numeric values; no scaling; fixed threshold 0.5. No search, calibration, protected evaluation, or full-feature refitting. The completed full-feature Random Forest predictions are reused as the reference.

## Pooled out-of-fold results

| Metric | Full-feature Random Forest | Omit obfuscation | Omit host structure |
|---|---:|---:|---:|
| Average precision | 0.9983646303 | 0.9983804939 | 0.9964512666 |
| Precision | 0.9987577893 | 0.9986968827 | 0.9923654722 |
| Recall | 0.9937189748 | 0.9938000203 | 0.9797183669 |
| F1 | 0.9962320106 | 0.9962424341 | 0.9860013662 |
| Balanced accuracy | 0.9963988180 | 0.9964166849 | 0.9870498553 |
| True negatives | 66,147 | 66,144 | 65,836 |
| False positives | 61 | 64 | 372 |
| False negatives | 310 | 306 | 1,001 |
| True positives | 49,045 | 49,049 | 48,354 |

## Descriptive changes from full-feature Random Forest

Values below are **percentage-point** changes, not relative percentage changes.

| Metric | Omit obfuscation | Omit host structure |
|---|---:|---:|
| Average precision | +0.001586 pp | −0.191336 pp |
| F1 | +0.001042 pp | −1.023064 pp |
| Recall | +0.008105 pp | −1.400061 pp |
| Balanced accuracy | +0.001787 pp | −0.934896 pp |
| Additional false positives | +3 | +311 |
| Additional false negatives | −4 | +691 |

## Interpretation suitable for Results and Discussion

Within the five-fold, group-isolated PhiUSIIL U1 development experiment, the fixed Random Forest classifier showed minimal change when the `HasObfuscation` and `NoOfObfuscatedChar` technical predictors were excluded: pooled average precision increased from 0.99836463 to 0.99838049 and F1 changed from 0.99623201 to 0.99624243. These very small observed differences do not justify a claim that obfuscation-related technical information is generally redundant.

Excluding the host-structure predictors (`DomainLength`, `IsDomainIP`, `TLDLength`, and `NoOfSubDomain`) yielded lower pooled average precision (0.99645127), F1 (0.98600137), and recall (0.97971837). At the fixed threshold, the number of false negatives increased from 310 to 1,001 and false positives from 61 to 372. This supports a descriptive finding that the omitted host-structure block contributes more strongly to performance **for this fixed model and development population**, under these specific feature-removal conditions.

The experiments do not establish causal individual-feature importance, statistically significant differences, expected performance on unseen sources or independently untouched holdouts, or performance of SE-BRL's twelve social-engineering behavioral indicators or Transformer/NLI component. These fixed-point exploratory ablations do not replace the original candidate nested-search and calibrated ablation plan, and they do not satisfy the formal model-selection gate. The development population has documented historical-exposure limitations. Per-fold estimates, and paired per-observation change analysis where useful, should be taken from the original saved output artifacts rather than inferred from the pooled confusion matrices.

## Research provenance

- Repository worktree: `research/scientific-validation-20261117`
- Reference four-family results commit: `c2ddb3c`
- Protocol, request, authorization and runner commit: `983f7c7`
- Fixed ablation request SHA-256: `3f29d2d60abd479b84fa50d7845ce423d7d6ff08411821a50125e569839dd887`
- Ablation run root: `experiments/runs/phiusiil-fixed-rf-ablations-v1/`
- Full-feature results source: `docs/research/2026-11-19_phiusiil_comparison_results/comparison.csv`
- Recorded integrity check: `ABLATION_OUTPUT_HASHES_VERIFIED`
- Training completed: 10 new Random Forest fits (5 per ablation), no calibration fits.

**Note:** The report is an editable draft assembled from values presented in the conversation. Check its row values against the committed files before incorporating into a submitted manuscript. Raw predictions and local experiment outputs should remain in their original protected/ignored locations rather than being copied into publication artifacts.
