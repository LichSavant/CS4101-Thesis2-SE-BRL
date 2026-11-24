# Exploratory PhiUSIIL technical-feature comparison

Five group-isolated development folds covered 115,563 observations (49,355 phishing; 66,208 legitimate). All models used the same ten technical fields and folds. Logistic Regression predictions were reused; the additional three families completed fifteen fixed uncalibrated fits. No fitting occurred during this verification.

| Model | AP | Precision | Recall | F1 | Balanced accuracy | Fold computation (s) |
|---|---:|---:|---:|---:|---:|---:|
| random_forest | 0.998365 | 0.998758 | 0.993719 | 0.996232 | 0.996399 | 97.933 |
| xgboost | 0.997951 | 0.993079 | 0.985513 | 0.989281 | 0.990196 | 38.654 |
| linear_svm | 0.997671 | 1.000000 | 0.988978 | 0.994458 | 0.994489 | 14.684 |
| logistic_regression | 0.997640 | 0.999733 | 0.984581 | 0.992099 | 0.992192 | 14.230 |

Under the predefined highest-pooled-noninterpolated-average-precision rule, Random Forest is the provisional descriptive winner (AP 0.998365). Ties are retained. This is not formal implementation selection: the existing calibrated nested-evidence, uncertainty and operational acceptance requirements remain unsatisfied.

Random Forest also had the highest F1 and balanced accuracy; Linear SVM had no observed false positives at its fixed zero-margin threshold. Fold variability is descriptive, not an independent-sample confidence interval or significance test. Raw SVM margins can vary in scale across folds; within-fold AP and mean AP are provided alongside pooled AP. Runtime measures saved fit/score/metric computation, excludes loading and verification, and is not an inference-latency benchmark.

The population has historical exposure and prospectively reconstructed lineage; no untouched-holdout generalization claim follows. This technical-only subset does not validate the twelve behavioral indicators or Transformer/NLI effectiveness. No calibration, search, threshold optimization, protected evaluation or new dataset access occurred. Source hashes and group isolation support reproducibility but do not imply independent source authentication.

## Planned ablations

- omit_obfuscation: remove HasObfuscation, NoOfObfuscatedChar. NOT AUTHORIZED; candidate nested search/calibration specification is not covered by fixed comparison acceptance.
- omit_host_structure: remove DomainLength, IsDomainIP, TLDLength, NoOfSubDomain. NOT AUTHORIZED; candidate nested search/calibration specification is not covered by fixed comparison acceptance.

Each ablation requires an exact separately accepted request binding feature omissions, model/settings, folds, preprocessing, fit count, output identity and code. A minimal fixed five-fold design would need acceptance before replacing the existing candidate nested search/calibration plan. Current authorization covers neither ablation; no ablation fitting was performed.
