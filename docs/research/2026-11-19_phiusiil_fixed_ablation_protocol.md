# SE-BRL Scientific Protocol Revision — Exploratory PhiUSIIL Technical Ablations

**Status:** Approved for preparation; separate fitting authorization pending  
**Reference comparison commit:** `c2ddb3c`  
**Reference comparison request SHA-256:** `a513d557307b7f5d73e64c543703b7d158d8b5c9635efbf7d31244189237ac84`

## 1. Research Objective

Estimate the change in development-fold predictive performance when predefined technical feature blocks are removed from the existing Random Forest configuration.

These experiments assess technical feature sensitivity only. They do not establish behavioral-indicator validity, Transformer effectiveness, or neuro-symbolic benefits.

## 2. Experimental Design

- Dataset: The existing PhiUSIIL U1 development population.
- Observations: 115,563.
- Validation: Reuse the five existing group-isolated development folds.
- Random seed: 42.
- Reference: Existing completed full-feature Random Forest out-of-fold results.
- Classifier: Random Forest, using exactly the frozen parameters, preprocessing, thresholds, and feature definitions from the approved fixed comparison.
- Hyperparameter optimization: None.
- Calibration: None.
- Protected calibration/internal evaluation populations: Not accessed.
- New model fits: Exactly 10.

## 3. Ablation A — omit_obfuscation

Exclude:

- `HasObfuscation`
- `NoOfObfuscatedChar`

Keep all other originally approved technical predictors.

Run one Random Forest fit for each of the five existing folds.

## 4. Ablation B — omit_host_structure

Exclude:

- `DomainLength`
- `IsDomainIP`
- `TLDLength`
- `NoOfSubDomain`

Keep all other originally approved technical predictors.

Run one Random Forest fit for each of the five existing folds.

## 5. Evaluation

For each ablation, report:

- Pooled average precision and individual fold average precision.
- Precision, recall, F1, and balanced accuracy.
- Confusion matrix.
- Paired descriptive performance differences against the existing full-feature Random Forest using the identical observations and folds.
- Fit counts, computation time, feature manifests, hashes, and reproducibility evidence.

Report descriptive differences without unsupported statistical significance or causal feature-importance claims.

## 6. Scientific Boundaries

The original 665-base-fit-plus-5-calibration-fit design per ablation remains preserved as a separate candidate plan.

The new fixed-configuration experiments must be labeled exploratory. They do not satisfy the original nested, calibrated ablation requirement or the formal model-selection gate.

No already completed model may be refitted merely to obtain a baseline.

## 7. Authorization and Execution Requirements

Before training, create an exact, immutable execution request identifying:

1. Source population, artifact identities, and source hashes.
2. Exact frozen Random Forest parameters and preprocessing from the completed comparison.
3. Complete retained-feature lists for both ablations.
4. Fold IDs, group-isolation rules, target definition, and random seed.
5. Exact fit budget: five fits per ablation, ten total.
6. Unique output destinations and execution-code hashes.
7. Prohibition against protected evaluation access, calibration, tuning, and unauthorized data sources.
8. Researcher-attributable acceptance referencing the exact request SHA-256.

**No training is authorized until these details are verified and separately accepted.**

## 8. Completion Criteria

The exploratory ablations are complete only when all ten authorized fits finish, saved predictions match the approved population and folds, metrics are recomputed, provenance checks pass, and aggregate results are preserved without exposing sensitive data.