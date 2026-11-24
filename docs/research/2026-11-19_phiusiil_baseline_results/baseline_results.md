# PhiUSIIL exploratory technical baseline: Results and Discussion

## Results

Five authorized, uncalibrated logistic-regression models generated exactly one
out-of-fold prediction for each of **115,563 development observations**: 66,208
legitimate (target 0) and 49,355 phishing (target 1). The five validation folds
contained 23,112, 23,112, 23,113, 23,113 and 23,113 observations. Saved predictions
have unique observation IDs and 104,570 groups; no group spans validation folds.
The accepted C-allocation isolates development groups from internal reserved
roles. No historical protected records or internal calibration/evaluation
predictors were used in this baseline.

| Metric | Pooled OOF | Fold mean | Fold population SD (percentage points) |
| --- | ---: | ---: | ---: |
| Precision | 99.9733% | 99.9733% | 0.0105 |
| Recall | 98.4581% | 98.4581% | 0.1949 |
| F1 | 99.2099% | 99.2098% | 0.0964 |
| Balanced Accuracy | 99.2192% | 99.2192% | 0.0955 |

The pooled confusion matrix, ordered [[TN, FP], [FN, TP]], was
**[[66,195, 13], [761, 48,594]]**. Thus the baseline missed 761 phishing records
and flagged 13 legitimate records. Noninterpolated average precision was
0.997640; ROC AUC was 0.997029. These ranking
statistics are secondary descriptive measures, not evidence of calibrated
probabilities. The summed final per-fold fit/scoring/metric elapsed time was
14.230 seconds, excluding admission,
loading, output serialization and earlier technical troubleshooting.

## Fixed method and reproducibility

The model used the existing ten-field technical dictionary, C=1, L2/liblinear,
intercept enabled, max_iter=2000, tolerance=0.0001 and seed 42. Each fold used a
fresh pipeline with training-fold-only StandardScaler(with_mean=False); missing
or nonfinite numeric inputs were rejected. The threshold was fixed at 0.5.
There was no hyperparameter search, probability calibration, threshold tuning,
classifier comparison or ablation. The classifier adapter treats convergence
warnings as failures. All five fits returned successfully.

`metrics.csv` and `confusion_matrices.csv` provide editable fold and aggregate
results. Private/local `oof_predictions.csv`, pipeline audits and the research
manifest remain under `experiments/runs/phiusiil-fixed-logreg-oof-v1/`.
The accompanying public manifest binds their exact hashes, actual authorization,
request, settings, source manifest and executed code/environment. Recomputing
metrics from saved predictions reproduced the saved pooled results exactly;
this verification required no additional model fits. No independent refitting
replication is claimed. Technical dispatch/validation performance repairs did
not change the frozen model parameters, data, folds or threshold; incomplete
technical attempts are distinguished in the manifest from the completed run.

## Discussion and limitations

Within this historically exposed, group-isolated development sample, the fixed
URL-structure baseline achieved high discrimination, with more false negatives
than false positives at the prespecified threshold. This is an exploratory
within-source result, not untouched holdout confirmation or evidence of deployment
performance. Historical exposure, reconstructed-lineage limitations and
unavailable near-duplicate/template/campaign coverage remain applicable. Domain
and exact-URL grouping do not establish independence of all latent source factors.
The ten-field subset does not reproduce the complete original feature benchmark.

Fold SDs are descriptive and are not independent-sample confidence intervals.
No superiority, statistical significance, or ablation conclusion is supported
because no comparison was executed. PhiUSIIL technical features provide no direct
validation of the twelve behavioral indicators or Transformer/NLI reasoning.
SE-BRL scientific validation as a whole remains incomplete. No calibration or
protected evaluation is authorized by this result.
