# SE-BRL Experiment Protocol Reconciliation

**Status:** Reconciliation for researcher/adviser review; not a protocol amendment, model-selection decision, or authorization to run experiments.  
**Prepared:** 2026-10-29 (Asia/Manila).  
**Audited synchronized revision:** `87d53a39e4846771f84c66a1453363457bbf17c2`.

This document preserves the completed Logistic Regression (LR) experiments and separates three kinds of statements:

- **Approved requirement:** specified in the approved proposal, cited by section/table/figure.
- **Verified fact:** established from versioned implementation, saved aggregate artifacts, or Git metadata at the audited revision.
- **Concern / recommendation:** an interpretation or proposed future action, not an approved change or a measured research result.

No model training, notebook execution, result regeneration, raw sealed-test inspection, or additional-classifier implementation was performed for this document. Historical prediction files were checked for presence only; aggregate result tables and notebook source were sufficient for this reconciliation. Saved metrics are evidence of a historical run, not independently reproduced findings.

**Synchronization record.** The user approved using `se-brl/main` while leaving `origin` unchanged. `se-brl` was verified as `https://github.com/LichSavant/CS4101-Thesis2-SE-BRL.git` and fetched. Local `main` fast-forwarded from `9737b5a3253807928b01198cf2cd9dcc68eb31d4` to the audited revision. The existing `latest-se-brl` branch remains at `8c22d94bcec7ea7338021207f2bea06a6ca110e7`; neither remote was renamed or reconfigured. Preflight checks found no tracked changes, untracked files, or incoming-path collisions with ignored files for either the branch switch or fast-forward. File-count/size/mtime fingerprints across 12,407 existing environment, build, cache, and database files were unchanged after synchronization. The inaccessible `.pytest_cache/` directory was not traversed; neither transition introduced paths there. Git LFS automatic smudging was skipped, so newly synchronized LFS datasets remain pointers rather than downloaded corpora. This does not replace or remove any pre-existing local dataset. Notebook 05 and ordinary Git result files were synchronized without execution. No forced update, reset, clean, rebase, or push occurred.

## A. Approved Methodology Requirements

### A.1 Authoritative sources and citation convention

**P** means [the approved proposal](../../Thesis_Proposal_Documents/Alcover%20%26%20Orbello_Approved%20Document%20Proposal.pdf), repository path `Thesis_Proposal_Documents/Alcover & Orbello_Approved Document Proposal.pdf`. Printed manuscript page numbers differ from PDF viewer pages: manuscript pp. 48-68 correspond to PDF pages 63-83. The partition figure was visually inspected from the original embedded figure in memory; no PDF or figure file was created.

Notebook references below use **one-based cell numbers plus the notebook's stored cell ID**, not execution counts. All refer to the audited revision:

| Reference | Repository path |
| --- | --- |
| [N01] | `experiments/notebooks/01_data_audit.ipynb` |
| [N02] | `experiments/notebooks/02_data_cleaning.ipynb` |
| [N03] | `experiments/notebooks/03_preprocessing.ipynb` |
| [N04] | `experiments/notebooks/04_feature_extraction.ipynb` |
| [N05] | `experiments/notebooks/05_experiments.ipynb` |

### A.2 Required research boundaries and sequence

1. **Deterministic representation:** four dimensions and twelve subordinate indicators, with Supported, Absent, and Unavailable states and traceable evidence. The methodology does not train a behavioral-dimension classifier and does not require expert annotations, CVI, inter-annotator agreement, or out-of-fold behavioral predictions. Out-of-fold (OOF) predictions concern learned phishing classifiers. [P §§4.3.4, 4.3.5.1; Tables 4.5-4.6; manuscript pp. 51-54 / PDF pp. 66-69.]
2. **Audit and freeze first:** capture source provenance, licensing, labels, exclusions, attrition, content eligibility, and reconciled conservative groups. Exact duplicates, near-duplicate templates, campaigns, and domain relationships must be addressed where the source permits. Do not equate spam or all malicious material with phishing. [P §§4.3.2-4.3.3; Table 4.4; manuscript pp. 48-50 / PDF pp. 63-65.]
3. **Partition barriers:** group-aware 70% development, 15% calibration, 15% sealed test; five-fold grouped development CV with fold-local learned preprocessing. Calibration and sealed test do not select candidates. [P Figure 4.2, manuscript pp. 50-51 / PDF pp. 65-66; §4.3.5.3.]
4. **Controlled representations:** E1 conventional features, E2 deterministic support plus availability, E3 their fusion. Within each modality, E1/E2/E3 use the same eligible artifacts, groups, folds, and evaluation controls. U1 technical benchmarks are independent and do not measure SE-BRL contribution. [P Table 4.7; manuscript p. 55 / PDF p. 70.]
5. **Four genuine candidates:** LR, Linear SVM, Random Forest (RF), and XGBoost, with predeclared candidate-specific search controls. LR remains the primary confirmatory E3-versus-E1 classifier even if another family wins implementation selection. [P §4.3.5.1; Tables 4.8-4.9.]
6. **Separate selection units:** choose one family for Email-E3, one for Web-E3, and independently for each approved U1 branch. E1/E2 cannot become deployment representations opportunistically after results are observed. [P §§4.3.5-4.3.5.3; Table 4.9.]
7. **Development-only selection:** use pooled grouped-development OOF predictions, prescribed uncertainty and calibration evidence, and a frozen model-only efficiency benchmark. Freeze selected family, parameters, preprocessing, dictionaries, manifests, dependencies, environment, and hashes before final calibration/threshold completion and sealed-test access. [P §4.3.5.2; Table 4.9, orders 0-7.]
8. **One final evaluation:** freeze the calibrator, operational probability boundaries, risk/response rules, and integrated system before opening the sealed test once. Test outcomes cannot trigger reselection, feature/rule changes, or threshold retuning. [P §§4.3.6-4.3.8; Tables 4.10-4.12; manuscript pp. 64-68 / PDF pp. 79-83.]

The proposal requires software/specification verification of SE-BRL: conformance, state correctness, modality boundaries, evidence references, schema conformity, repeatability, and output consistency. These are not claims of psychological construct validity or independently annotated behavioral accuracy. [P Table 4.6; §4.9.4, Table 4.18, manuscript p. 81 / PDF p. 96.]

## B. Current Implementation vs. Approved Protocol

### B.1 Verified completed work

| Stage | Verified implementation and exact location | Reconciliation |
| --- | --- | --- |
| Audit | [N01], cell 58 `c18f9b33` hashes raw source files; cell 61 `2f24a5fd` exports inventory, label, missingness, duplicate and grouping summaries | Substantial audit infrastructure exists. A hash inventory alone does not supply the full source/license/eligibility/attrition freeze in Table 4.4. |
| Cleaning | [N02], cells 17 `be8e3d45`, 19 `f7e58383`, 28 `b1a5e1c7`, 31 `97f997c2`: label-conflict inspection, complete-row deduplication, infinity-to-missing replacement, ARFF integer conversion | Deterministic cleaning preserves conflicting predictor/label combinations rather than inventing labels. Learned numeric imputation is deferred. |
| Groups and partitions | [N03], cells 24 `4cde6e43`, 29 `88644be7`, 30 `53d001e6`, 43 `77b69f75`, 52 `0ea8a521`, 62 `1bc55f1f`, 92 `eb5cf346`, 116 `4cb6074e` | Email uses sender/exact-body connected components; PhiUSIIL exact normalized domains; UCI/ISCX exact predictor hashes. Fixed development folds exist, but comprehensive template/campaign/domain-family controls remain incomplete. |
| Behavioral extraction | [N04], cells 24 `0f71a795`, 31 `d55b15cb`, 54 `c39fad04`, 57 `88372fcf`, 65 `856e7104`, 70 `facef21a` | Deterministic lexical/structural extraction, explicit unavailable identity indicators, dimension states, support/availability encoding. It is not the same rule/schema contract as runtime `ml/`. |
| Experiment integrity | [N05], cells 5 `c1f8ad17`, 6 `c92cd1ca`, 8 `34d078c9` | One-to-one joins, matching labels/groups/partitions/folds, group isolation, five fold IDs, binary support/availability, and no supported-but-unavailable values are checked. |
| Feature handling | [N05], cells 10 `a99b87bb`, 11 `6b0fb502`, 13 `aeae4aa2` | Email E1 uses subject/body TF-IDF; numeric baselines use dtype-discovered numeric columns with exclusions. Metadata/labels/group IDs are excluded; PhiUSIIL additionally excludes `URLSimilarityIndex`, `TLDLegitimateProb`, and `URLCharProb`. Explicit schema allowlists are still needed. |
| CV | [N05], cells 13 `aeae4aa2`, 14 `d8a0e0ce`, 16 `e562e68e` | Fresh sklearn pipelines fit TF-IDF or imputer/scaler on each training fold. Validation uses only the held-out development fold. No calibration/test fit path was found in these functions. |
| Historical calibration | [N05], cells 22 `04d06166`, 23 `f37d3d2b`, 24 `dcdc47ec` | Refit on development; group-disjoint calibration-fit/threshold subsets; sigmoid on clipped probability logits; F1 threshold selection; ten-bin quantile reliability plots. This does not provide cross-fitted development calibration for family selection. |
| Historical evaluation | [N05], cells 27 `07ce0ca0`, 28 `6111595d`, 34 `24086492`, 37 `facb8909`, 40 `2719bdae` | Holdout evaluation/comparisons, development-fold ablations, LR coefficients, aggregate errors are implemented and have saved artifacts. They are historical results, not evidence of a completed four-family freeze. |

### B.2 Exact classifier/configuration coverage

[N05], cell 13 `aeae4aa2`, constructs only `LogisticRegression(solver="liblinear", max_iter=1000, class_weight="balanced", random_state=42)`, with default `C=1.0`. No search loop is implemented.

| Historical dataset key | Configurations actually run | Approved-role qualification |
| --- | --- | --- |
| `email` | E1, E2, E3 with LR | Source-confounded consolidated email; conventional feature scope is text-only |
| `phiusiil` | E1, E2, E3 with LR | Title/engineered-feature proxy experiments; not automatically the approved content-bearing Web branch |
| `iscx` | E1 with LR | Technical-only comparison, but not an approved U1 branch in Table 4.7 |
| `uci` | E1 with LR | Consistent with technical-only intent; historical naming lacks explicit `U1-UCI` |

There are eight combinations and 40 CV-fold rows; dimension ablations contribute another 40 rows. `ml/models.py`, `CandidateAlgorithm`, declares all four family IDs, but `Trainer`/`Classifier` are protocols and `UnavailableModel` is not an estimator. The two fetched live branches have the same file tree; no additional classifier result family was found there. This does not rule out unpushed or deleted work.

### B.3 Result preservation, naming, and verification limits

`experiments/results/experiments/` contains 29 non-placeholder artifacts: 17 CSVs, one JSON manifest, and 11 PNGs. Names include:

| Purpose | Historical artifact names in that directory |
| --- | --- |
| Development CV | `cross_validation_fold_metrics.csv`, `cross_validation_summary.csv` |
| Paired representation differences | `paired_cv_differences.csv`, `paired_cv_summary.csv` |
| Calibration | `calibration_summary.csv`, `calibration_reliability.png` |
| Historical holdout | `holdout_test_metrics.csv`, `holdout_comparisons.csv`, `holdout_predictions.csv` |
| Ablations | `ablation_fold_metrics.csv`, `ablation_summary.csv`, `ablation_effects.csv` |
| Explanatory summaries | `model_coefficients.csv`, `error_analysis_summary.csv`, behavioral-coefficient/confusion-matrix/precision-recall PNGs |
| Provenance and checks | `dataset_inventory.csv`, `behavioral_coverage.csv`, `split_integrity.csv`, `input_manifest.csv`, `experiment_manifest.json` |

These names lack classifier/run namespaces; `FINAL_MODELS` keys are only `(dataset, experiment)`. Reusing the notebook unchanged for another family would overwrite outputs. Keep the historical names and files unchanged. Future naming is a proposal in Section I, not an instruction to rename them now.

Saved aggregate checks show 40 CV rows, eight calibration rows, eight holdout metric rows, and 40 ablation rows. CV summary means reconcile with fold metrics; confusion totals reconcile with validation sizes; aggregate holdout sizes and thresholds match saved split/calibration summaries. These checks do not reproduce training, authenticate every historical decision, or establish predictive validity. No classifier is chosen from these values here. `experiments/results/models/` contains only a placeholder; fitted preprocessing/classifiers/calibrators are not serialized by [N05].

### B.4 Concrete gaps and documentation drift

- [N05], cell 17 `6c864305`, reports mean/std of fold metrics, not pooled OOF AP; cell 14 returns no observation-level OOF scores. Cell 19 `9ea66343` reports descriptive paired fold differences, not the specified 2,000 group bootstrap confidence intervals.
- MCC, ECE, model-only timing/throughput, inference memory/model size, hard-gate/equivalence decisions, and `model_selection_report.csv` are absent from the experiment workflow. Calibration-fit Brier is evaluated on calibrator-fitting records and must not be promoted to independent calibration evidence.
- [N01], cell 16 `69185334`, contains prose in a code cell and fails static Python parsing. [N02], cell 4 `444ebe8a`, retains a saved `FileNotFoundError`; this historical output does not prove its current path logic always fails. [N02], cell 44 `95c37a49`, reports failed validations but does not itself prevent later export cells from running.
- [N03], cells 69 `18b82f5f` and 71 `e672cd35`, contain different PhiUSIIL partition procedures; cells 72 `6913d292` and 73 `36097982` rebuild/merge the later assignments. A future refactor must preserve the actually exported manifest, not select an earlier procedure by appearance.
- `experiments/data/processed/` has no tracked preprocessed/model-feature inputs, and `experiments/results/feature_extraction/evidence/indicator_evidence.csv`, exported by [N04] cell 93 `ec7b7a6d`, is not tracked. Input filenames/hashes exist in `input_manifest.csv`, but an exact rerun needs authorized matching inputs and the environment.
- `backend/requirements*.txt` do not declare the notebook scientific stack. `experiment_manifest.json` records Python 3.9.6, pandas 2.3.3, NumPy 2.0.2, sklearn 1.6.1, and seed 42, but not a complete lockfile, workstation/thread settings, all estimator defaults, model hash, or calibration-subset membership. The local backend environment lacks the scientific packages; no packages were installed.
- `README.md`, section `Deferred research work`, says audits, partitions, CV, calibration, and final reporting are wholly unimplemented despite the notebook artifacts. Its absence-of-integrated-ML statement remains accurate. `ml/README.md`, `docs/se-brl-pretraining.md` (`Required next research work`), and [N05]'s future-work discussion contain learned-behavior/annotation assumptions that do not define the approved deterministic methodology. Older Low/Medium/High terminology also differs from P Table 4.11's Informational/Elevated/High/Review Required states. None of these existing files is changed here.
- Existing `ml/tests/` and backend tests exercise runtime contracts and safeguards; they do not execute [N05]'s sklearn experiment workflow. Static audit found 46 parseable Python modules, plus the notebook syntax issue above. No test suite, build, or training run is claimed for this documentation-only task.

## C. Dataset-Role Reconciliation

The following is the approved-role interpretation of P §4.3.5 and Table 4.7. It is not permission to relabel or regenerate historical runs.

| Dataset/artifact population | Approved role | Current use | Required reconciliation / proposed disposition |
| --- | --- | --- | --- |
| Consolidated Email | Content-bearing Email-E1/E2/E3; same eligible records across all three; E3 implementation family selection | Nazario positives plus ham negatives from three other sources; E1 subject/body text only | Resolve source confounding and freeze a defensible email pool. Approve a conventional feature dictionary covering available text, relation/header/structure and embedded-URL evidence, or explicitly record any justified restricted-feature deviation. |
| Content-bearing Webpage | Web-E1/E2/E3 with inspectable visible text, DOM/forms/links/structure, URL and brand-domain evidence; screenshots excluded from ML unless separately approved | No distinct full-content Web experiment identified; title plus engineered PhiUSIIL fields stands in for it | Identify an authorized, archived content-bearing source with auditable labels and evidence fields. A title can supply limited text, but it does not establish the complete approved Web feature/evidence scope. |
| PhiUSIIL | **U1-Ph**, independent dataset-defined engineered technical benchmark; no SE-BRL contribution claim | Treated as behaviorally evaluable `phiusiil` E1/E2/E3 | Preserve historical title/structure proxy runs with their original identity and limitations. Create a separately versioned U1-Ph specification after approval; do not rename old runs or claim they already fulfill the approved Web branch. Using PhiUSIIL in an additional behavioral role requires an explicit reviewed deviation. |
| ISCX-URL2016 | No named U1 branch in final Table 4.7 | Technical-only `iscx/E1`; no raw URLs/domains in the selected engineered file | Preserve as historical/supplementary technical work. Retention as an additional official benchmark requires approval, with separate feature space and claims. It cannot substitute silently for U1-Ph. |
| UCI Phishing Websites | **U1-UCI**, separate technical benchmark; no raw pooling with PhiUSIIL | Technical-only `uci/E1` | Retain historical baseline. Specify future U1-UCI family comparisons independently. Predictor-hash groups preserve conflicting-label duplicates together; unavailable behavioral evidence is not absence. |

Current label mappings are explicit: [N03] cell 16 `95feb561` constructs email targets; cell 59 `a56e020c` maps PhiUSIIL native `0 -> phishing target 1`, `1 -> legitimate target 0`; cell 89 `d6e0ca92` maps UCI `-1 -> 1`, `1 -> 0`; cell 113 `19beb152` maps ISCX `phishing -> 1`, `benign -> 0`. Spam/other malicious labels are not automatically relabeled as phishing. Source-supported semantics and their documentary provenance must still enter the frozen label mapping, not merely notebook prose.

**Concern:** grouping by exact feature vectors establishes only exact-vector isolation for UCI/ISCX; the missing underlying artifacts limit campaign/domain audits. PhiUSIIL lowercased exact-domain grouping is not registrable-domain-family grouping. Email normalization uses sender strings and exact bodies, not a complete sender-address/thread/template/campaign resolver. No actual near-duplicate cross-split contamination is asserted without the relevant evidence audit. [N03] cells 24, 29-30, 62, 91-92, 115-116; P §4.3.3/Table 4.4.

## D. Email Source-Confounding Assessment

### D.1 Verified mechanism and claim boundary

[N03], cell 16 `95feb561`, assigns every Nazario record `target=1` and selects only `label==0` from CEAS-08, Enron, and SpamAssassin for `target=0`. Source identity therefore determines target in the constructed pool. This is verified from construction code, without reopening any raw observation. The saved experiment inventory reports 38,759 email observations, including 1,565 positive targets; these are historical aggregate counts, not new data analysis.

[N05] excludes the explicit source field, but subject/body TF-IDF can still capture source formatting, vocabulary, collection period, or preprocessing artifacts. Sender/exact-body grouping cannot remove this confound, and stratifying sources across folds deliberately retains it. **Concern:** high discrimination could partly reflect corpus identification. The fraction attributable to that mechanism is unknown; no measured confounding effect is invented.

The existing `experiments/results/audits/meajor_suitability_review.md` acknowledges the original source-class problem and does not approve MeAJOR as a primary phishing benchmark because phishing-specific label provenance is unresolved. Preserve that finding; neither its binary column nor its multi-source composition automatically fixes label validity.

### D.2 Recommendations requiring approval

| Proposed strategy | Scientific benefit | Necessary qualification |
| --- | --- | --- |
| Prefer an independently defensible phishing/legitimate benchmark containing both classes within sources or a documented comparable collection process | Reduces deterministic source-class separation | Verify acquisition, licensing, phishing-specific semantics, artifact availability, groups and overlap before a new freeze. No dataset is selected by this document. |
| Source-only target baseline on authorized development metadata | Demonstrates the construction's shortcut ceiling | It is a diagnostic, not a phishing detector; aggregate source identity already exposes the deterministic association. |
| Source-stratified development errors and precision/recall diagnostics | Reveals which corpora contribute errors | Within single-class sources, some metrics are undefined; do not invent per-source ROC/AP comparisons requiring two classes. |
| Predeclared normalized-format and formatting-only sensitivity baselines | Tests dependence on corpus-specific representation | Freeze transformations without consulting historical test outcomes; label these new development analyses. |
| Group-preserving near-duplicate/template and appropriate domain controls | Addresses related-artifact contamination | Stronger groups can change membership/folds; treat resulting runs as a new protocol version, not directly identical replications. |
| External cross-source validation with meaningful class support | Tests generalization beyond original corpora | A naive leave-one-source-out design here is insufficient: holding out the sole positive source removes positives from training. Both-class eligibility must be designed and justified first. |

If a defensible replacement is unavailable, a proposed fallback is to retain the current pool as an explicitly source-confounded exploratory benchmark and restrict claims accordingly. Sensitivity analyses do not by themselves convert it into an unbiased confirmatory phishing benchmark. This fallback requires adviser approval and is not adopted here. [P Table 4.4 and Table 4.10, generalization/shortcuts row.]

## E. Historical Holdout and Evaluation-Integrity Plan

### E.1 Verified historical exposure

[N05], cell 5 `c1f8ad17`, reads complete preprocessed and behavioral tables before filtering partitions. Cell 27 `07ce0ca0` evaluates all eight historical LR combinations on `test`; cells 28-30 produce comparisons/figures and cell 40 `2719bdae` summarizes errors. The saved holdout metrics/prediction artifacts and executed notebook output establish prior evaluation. The experiment manifest dates the recorded run to `2026-10-28T12:07:05.592041+00:00`.

The inspected CV and calibration functions fit on development/calibration records respectively, and no explicit code path uses test scores to select family or hyperparameters. **Unknown:** whether anyone previously revised choices after reviewing test output, how many historical evaluations occurred, and which protocol version was frozen before each access. Source inspection cannot establish those facts.

Nevertheless, the four-family development-only selection hierarchy was not completed before these saved tests. Those observations cannot become an *unopened* confirmatory test for new model/feature/rule decisions simply by hiding the files, changing a seed, reshuffling the same pool, or rerunning the notebook. [P §4.3.5.3; §4.3.8; Table 4.9 order 7.]

### E.2 Proposed defensible strategy, not an approved amendment

1. Record historical run identity, known exposure, and uncertainty about earlier access. Keep every historical artifact unchanged; distinguish historical/exploratory results from future confirmatory claims. Approval of this document cannot retroactively satisfy the proposal's pre-access freeze requirement.
2. Freeze a revised development protocol and an exposure/deviation record with researcher/adviser approval. Historical holdout outputs must not rank new candidates, populate tolerances, select datasets/features/rules, or choose thresholds. This document intentionally does not recommend a winning classifier from those scores.
3. Conduct new selection only on approved development records. A separate loader should admit development data by default and keep calibration access in an explicit finalization stage; a sealed evaluator should require a frozen compatible bundle. Proposed grouped inner tuning/cross-fitting must exclude outer validation groups from every learned operation (Section G.4).
4. Prefer a genuinely unexposed independent evaluation source or separately custodied acquisition, after provenance, eligibility and group/overlap checks against all previously used populations. Newness alone does not prove independence; define sources, dates, group rules, access custody and stopping rules before inspecting outcomes. Acquisition or data inspection would require separate authorization.
5. Freeze selected family/parameters, full-development refit, features/rules, calibrator, operating boundaries, decisions, dependencies, hashes and evaluation plan before that evaluation. Execute once; report defects and limitations without test-driven reselection. Preserve LR's separately specified confirmatory representation contrast.
6. If no genuinely unexposed evaluation can be established, report the existing holdout as historical and new CV as development/exploratory evidence. A prospectively frozen nested/grouped CV study could be an approved alternative with narrower claims; it must not be described as the originally untouched sealed-system validation.

The proposal's ordinary deviation procedure requires confirmation of no sealed-test access [P §4.3.1, manuscript p. 48 / PDF p. 63]. That assurance cannot be supplied for the historical partition. An adviser-approved response to this existing exposure, rather than an undocumented ordinary pre-test amendment, is therefore necessary.

## F. Behavioral Feature Contract Alignment

### F.1 Identifiers and representations

[N04], cell 7 `73aa8e1c`, maintains a notebook-local `SEBRL_CODEBOOK`. Runtime's canonical source is `ml/se_brl/codebook.v0.1.0.json` (codebook `0.1.0`, schema `1.0.0`), loaded by `ml/se_brl/codebook.py`.

| Notebook identifier | Canonical runtime identifier | Status |
| --- | --- | --- |
| `pressure_threat` | `pressure_threat_cues` | Explicit dimension mapping required |
| `lure_attention` | `lure_attention_cues` | Explicit dimension mapping required |
| `trust_identity` | `trust_identity_manipulation` | Explicit dimension mapping required |
| `requested_action_consequence` | `requested_action_consequence` | Same ID |
| `credential_sensitive_request` | `credential_sensitive_data_request` | Explicit indicator mapping required |

Other eleven indicator IDs agree at this revision. Display names and title-cased notebook states also differ from canonical naming/lowercase state IDs; preserve display labels separately from wire identifiers.

[N04], cell 70 `facef21a`, encodes Supported as `(support=1, available=1)`, Absent as `(0,1)`, and Unavailable as `(0,0)`; compact tables preserve four support columns followed by four availability columns. This aligns conceptually with deterministic support/availability in P Figure 4.4/Table 4.7, without making them behavioral probabilities.

Runtime `ml/se_brl/representation.py`, `BrlRepresentation`, instead retains `z1-z4=None`, `z_status="not_evaluated"`; `ml/features.py`, `ExperimentFeatureBuilder.build`, blocks E2/E3 through `learned_behavioral_values_not_available`. Canonical vector metadata still calls these future confidence slots. **Concern:** runtime's older learned-slot assumption is incompatible with the approved deterministic experiment representation. Mapping names alone does not resolve this contract. Do not fill learned slots with booleans and silently call the result equivalent.

### F.2 Evidence, semantics, and modality differences

| Aspect | Notebook 04 | Runtime contract / approved requirement | Reconciliation needed |
| --- | --- | --- | --- |
| Text evidence | Cell 27 `9813807c` normalizes whitespace, deduplicates matched strings; cell 31 `d55b15cb` joins subject/body or takes title | `ml/preprocessing.py`, `TextEvidence`, keeps original field, character offsets, location and quotation status; `ml/se_brl/extraction.py`, `IndicatorEvidence`, adds rule ID/version, modality/provenance and optional supporting references. P Table 4.6 requires valid traceable locators. | A matched fragment plus observation ID is not an unambiguous original-field occurrence/span. Freeze original-field/offset and structural-field locator schemas. |
| Rule scope | Cell 24 `0f71a795` matches broad terms such as `bank`, `password`, `free`, or `payment` | `ml/se_brl/rules.py` v0.2.0 uses more specific action/consequence patterns; `context.py` suppresses quoted, educational/reported, and negated contexts | These are substantively different feature generators, not equivalent refactors. For example, a password mention alone can trigger the notebook credential indicator; the runtime request rule requires an action phrase. No corpus false-positive rate is asserted. |
| Trust/identity | Cell 54 `c39fad04` makes impersonation/brand unavailable globally; authority remains lexical | `ml/se_brl/detectors.py`, `ConservativeTrustDetector`, uses independent typed identity/authority context and can leave unreviewed claims `not_evaluated` | Decide qualifying observable relations and abstention requirements under a frozen deterministic specification. Independent reference data is not a license to introduce expert behavioral ground truth. |
| Partial availability | Cell 65 `856e7104`: if any indicator is available and none supported, the dimension becomes Absent even when other indicators are unavailable | Runtime has dimension-level conditional trust availability and distinguishes unevaluated detector status; P requires assessability-dependent evidence states | Approve what dimension-level Absent means under partial coverage. Do not retrospectively infer which unavailable indicators were absent. |
| Modality gating | Notebook's modality dictionary marks email/web dimensions assessable; record indicators use text availability, with structural availability forced true for selected PhiUSIIL fields in cell 63 `59734bd1` | Canonical modalities are `content_bearing_email`, `content_bearing_webpage`, `standalone_url`, `engineered_technical_record`; trust is A* conditional, all technical-record dimensions are U. `assessment.py` uses required-content/conditional-evidence flags. | Freeze source-kind routing and record-level missing-field rules. A column's existence or a dataset name cannot prove content/field assessability for every row. |
| Structural support | Cells 57 `88372fcf` and 59 `b5762a9c` derive requested-action support from `HasSubmitButton`, `HasExternalFormSubmit`, `HasPasswordField` | P distinguishes inspectable Web evidence from U1 engineered benchmarks; factual evidence references must retain their provenance | Do not assert live DOM/form inspection from a supplied binary feature. State that the historical evidence is a source dataset field and resolve its approved branch. |

**Recommendation:** freeze one approved deterministic specification and explicit compatibility mapping, with new version identifiers and conformance/boundary/locator/repeatability tests. Choose through reviewed evidence requirements, not whichever variant improves historical test scores. Preserve both historical implementation and artifacts. Any change to rules, preprocessing, availability semantics, features or eligible artifacts creates a separately versioned experiment; it cannot be merged numerically with old LR results as if feature-identical. Existing runtime tests are useful fixtures, but must be reconciled with the approved specification rather than assumed authoritative merely because they pass. [P §4.3.4, Table 4.6.]

## G. Four-Classifier Model-Selection Specification

### G.1 Approved family search ranges

The following transcribes P Table 4.8 (manuscript p. 56 / PDF p. 71); parameter API names in parentheses clarify implementation correspondence. It does not fill omitted budgets/defaults.

| Family | Approved search values / controls | Imbalance | Probability / attribution |
| --- | --- | --- | --- |
| Logistic Regression | `C={0.01,0.1,1,10}`; L2; `max_iter=2000` | None or balanced, selected inside grouped CV | Frozen phishing calibration; standardized coefficients and local `x_j * beta_j` contributions |
| Linear SVM | `C={0.01,0.1,1,10}` | None or balanced | Signed decision contributions; sigmoid mapping when calibrated probability is needed |
| Random Forest | Trees `{300,600}`; depth `{None,20,40}`; minimum leaf `{1,3,5}`; `max_features={sqrt,0.5}` | Balanced or balanced_subsample, frozen in CV | TreeSHAP / feature importance; calibration when selected and required |
| XGBoost | Depth `{3,6}`; eta `{0.03,0.1}`; subsample `{0.8,1}`; column subsample `{0.8,1}`; child weight `{1,5}`; lambda `{1,5}` | Fold-local `scale_pos_weight` where applicable | TreeSHAP; calibration when selected and required |

All four require p50/p95 model-only latency, throughput, and memory/model size. Exact search strategy/budget, unspecified solver/default parameters, XGBoost estimator count/early-stopping policy, threading and resource limits still need freezing. The approved value sets do not themselves prescribe undocumented random-search draws or silently authorize a reduced grid. Existing LR is one historical setting with a different iteration cap; retain it, but do not claim it completes the approved LR search.

### G.2 Approved metrics and selection hierarchy

**Metrics:** primary PR-AUC; supporting precision, recall, F1, ROC-AUC, balanced accuracy, MCC; probability quality through Brier score, ECE and fixed-binning reliability analysis. Use the positive phishing class consistently. The notebook explicitly uses sklearn non-interpolated Average Precision (AP); freeze that computational definition or obtain approval for any different PR-area estimator before comparison. Do not mix AP with trapezoidal PR area under one unlabeled metric. [P §4.3.5.2; Table 4.10; N05 cell 14 `d8a0e0ce`.]

Apply P Table 4.9 in the following order, separately within Email-E3, Web-E3, U1-Ph, and U1-UCI:

| Order | Approved decision |
| --- | --- |
| 0. Protocol validity | Exclude incomplete/unreproducible runs, unresolved leakage, incompatible schemas, unrecoverable failures, or missing required prediction/calibration/benchmark evidence. |
| 1. Hard approved requirements | Enforce applicable approved minimum recall/precision and maximum p95/memory limits before ranking. If no limit has been approved, do not invent one. |
| 2. Discrimination | Rank using PR-AUC from **pooled grouped-development OOF predictions**, not historical holdout or a replacement secondary metric. |
| 3. Uncertainty/equivalence | Use **2,000 paired group-preserving bootstrap resamples and 95% confidence intervals**, applying the approved `[delta_PR]` practical-equivalence rule. Equivalent candidates proceed instead of being separated by negligible point differences. |
| 4. Probability quality | Within the practically equivalent set, compare cross-fitted development Brier/ECE/reliability under the frozen comparison rule. Do not trade material PR-AUC loss for a small calibration gain. |
| 5. Efficiency | Among candidates still comparable, prefer lower model-only p95; then higher throughput; then lower memory/model size. p50 is descriptive. |
| 6. Interpretability/reproducibility | If still tied, prefer the simpler reproducible operational bundle considering attribution availability, dependencies and artifact size. Prefer LR only if it remains in the tied set after earlier gates. |
| 7. Lock | Record all candidates, exclusions, comparisons, uncertainty/equivalence, calibration, benchmark and tie-break reasons in `model_selection_report.csv`; freeze family, parameters, preprocessing/dictionary, training manifest, environment/dependencies and hashes. No test-driven reselection. |

LR remains the primary confirmatory E3-versus-E1 classifier independently of these implementation winners. E1/E2 do not compete as alternate implementation representations. [P §§4.3.5.1-4.3.5.3.]

### G.3 Calibration, thresholds, efficiency, and reproducibility

The existing calibration procedure [N05], cell 22 `04d06166`, uses `GroupShuffleSplit(test_size=0.5, random_state=42)` within calibration, asserts disjoint groups and both-class support, clips raw probabilities with `EPSILON=1e-6`, fits a one-dimensional LR sigmoid on logits, and maximizes F1 on the other subset. Cell 23 `f37d3d2b` fits the classifier on full development. These are **historical implementation choices**, not all specified numeric proposal parameters. The split is group-aware but not class-stratified; the both-class checks fail rather than silently accepting a one-class subset.

Future family-selection calibration must be cross-fitted using development data; the reserved calibration partition finalizes the selected phishing classifier and operational boundaries. Linear SVM does not fit the notebook's unconditional `predict_proba` interface: preserve decision-margin orientation and apply an approved sigmoid mapping without pretending margins are probabilities or passing them through a probability-logit function. For every family, calibration-fit groups and assessment groups must remain disjoint. Document whether discriminative ranking uses raw or cross-fitted calibrated scores; freeze score comparability across folds, clipping, calibration regularization and edge cases. One F1-optimal binary threshold is not the approved low/high operational boundaries or full risk logic. [P §4.3.5.2, §4.3.6; Table 4.11.]

**Model-only timing boundary:** begin after a model-compatible feature vector is ready; end when classifier prediction completes. Record p50/p95 latency, throughput in artifacts/second, inference memory where measurable, serialized model size, workstation/OS/software, batch size, threads, warm-up, repetition counts and seed/configuration. Parsing, feature construction, calibration, attribution, risk processing, API and rendering are excluded from model-only timing and measured separately for end-to-end system validation. Candidate benchmarks use one frozen environment, not different hardware or settings selected after results. [P §4.3.5.2; §4.3.5.4; Figures 4.8-4.9; Table 4.9.]

Use approved linear local contributions or tree attribution while retaining artifact evidence as a separate channel. Capture all fitted transforms, estimator parameters, class order, calibrator, thresholds, rule/schema versions, source/split/feature hashes, dependencies and model hashes in a compatible operational bundle. Repeatability and security/fail-closed validation remain required before system release; benchmark speed alone cannot establish deployment safety. [P §4.3.6, Tables 4.10/4.12/4.18.]

### G.4 Recommended development design requiring approval

Preserve the five fixed outer development folds where grouping/eligibility remains valid. Predeclare grouped inner splits for hyperparameter tuning and calibration cross-fitting using outer-training records only. Each outer-validation artifact must be unseen by vocabulary/IDF, imputation, scaling, encoding, weighting calculations, tuning and calibrator fitting. For XGBoost, any early-stopping validation must likewise remain inside training, not use outer validation, reserved calibration or test. Exact nested split counts and budgets are **not set here**.

Save one OOF row per eligible artifact/family/configuration containing observation/group/fold identity, target, score type/orientation, raw score, independently calibrated probability where required, seed, parameter/configuration identity, and provenance hashes. Pair candidate predictions on the same eligible artifacts and resample whole groups together. Predeclare bootstrap weighting, invalid/one-class-resample handling and CI/equivalence calculation. Retain fold metrics descriptively but calculate the selection statistic from pooled OOF predictions. After family/hyperparameter lock, refit on full development and finalize calibration/thresholds under the approved reserved-partition procedure.

This is a recommended design to avoid tuning/calibration optimism, not a claim that the proposal already specifies every nesting detail or that the implementation exists. New eligibility/group definitions require a new manifest/version; never force new data into old folds simply to retain numerical comparability.

## H. Open Decisions Requiring Researcher/Adviser Approval

No item below is resolved by this document. Already approved constants such as the four families, search value sets, 2,000 resamples and 95% CI are not replaced with new values.

| Decision | Why unresolved / required approval |
| --- | --- |
| H1. Dataset roles and eligibility | Approve an actual content-bearing Web source; restore PhiUSIIL's U1-Ph role in new work or explicitly approve an additional proxy role; decide whether ISCX remains supplementary. Preserve existing run labels. |
| H2. Email benchmark strategy | Choose a defensible both-class/source design, required sensitivity analyses, and claim scope. Do not automatically adopt MeAJOR or relabel spam. |
| H3. Evaluation after exposure | Record historical access, choose an unexposed independent evaluation/custody plan or explicitly approve exploratory/nested-CV limitations. Do not claim historical test resealing. |
| H4. Deterministic contract | Approve canonical IDs/mapping, rule semantics, context exclusions, conditional/partial availability, missing structural fields, locators, version migration and fixture acceptance. Learned z slots are not an approved E2 prerequisite. |
| H5. Grouping and freeze | Freeze near-duplicate algorithm/parameters, domain/path/thread/campaign reconciliation, provenance/license records, exclusions and attrition. Assess manifest changes without consulting historical test outcomes. |
| H6. `[delta_PR]` and uncertainty | Justify the practical-equivalence tolerance and exact CI/equivalence decision rule; freeze bootstrap unit/weighting, comparison construction and invalid-resample handling. No numeric tolerance is invented. |
| H7. Hard requirements | Populate `[REQ_MIN_RECALL]`, `[REQ_MIN_PRECISION]`, `[REQ_MAX_P95]`, `[REQ_MAX_MEMORY]` only from formally approved SRS/protocol limits, or explicitly record that no such hard limit applies. |
| H8. Search/defaults and nesting | Freeze complete candidate budgets/search method, solvers/defaults, XGBoost number of estimators/early stopping, inner grouped splits, repeated-seed list and execution-failure policy. Do not reduce approved ranges silently. |
| H9. Calibration/metric conventions | Approve AP/PR-area computation, OOF score scale, cross-fitting/calibration method and settings, ECE formula/bins/empty-bin handling, reliability protocol, threshold objective/ties and optional `[delta_cal]` only if a tolerance is formally approved. |
| H10. Benchmark protocol | Populate `[N_warmup]`, `[N_bench]`; freeze hardware/software, batch size, threads, time units/clock, timing scope, memory method and serialization format. Do not choose settings after comparing candidates. |
| H11. Feature and artifact release | Freeze modality-specific conventional allowlists, deterministic support/availability schema, missingness/categorical handling, data access/retention, input availability, environment lock and immutable output namespaces. |
| H12. Operational finalization | Approve numerical low/high probability boundaries, uncertainty/corroboration/severity decision rules and bounded interventions through the calibration protocol; retain Informational/Elevated/High/Review Required semantics. No personal susceptibility claim follows from artifact classification. |

A dated researcher/adviser decision record should identify the source requirement, chosen resolution, rationale, scope, exposure implications and effective protocol version for each item. Recommendations do not become approved decisions by being written here. Existing source-confounded or exposed results remain honestly labeled historical evidence even after future approval.

## I. Recommended Implementation Order

1. **Review and resolve this reconciliation first.** The single safest next development step is a researcher/adviser-approved protocol/exposure decision record covering Section H, before feature changes or more classifier runs. No such approval is asserted here.
2. **Protect the historical LR record.** Preserve the current notebook, all 29 result artifacts, their original paths and Git revision; retain `latest-se-brl`. In a later authorized task, record an immutable historical manifest/archive without moving or overwriting existing files. Do not claim this step repairs historical methodology.
3. **Freeze approved data roles, evidence specification, groups and evaluation custody.** Obtain authorized matching inputs; independently reconcile source/label/attrition and overlap. Do not open raw historical test records to optimize this work. Complete deterministic conformance and locator tests without introducing a behavioral annotation/model requirement.
4. **Create a separate development-only harness after approval.** `experiments/src/{data,features,models,evaluation,validation}/` currently contains placeholders. Extract reusable pure functions from [N05] rather than rewriting its historical record: retain one-to-one merge and group checks; replace dtype feature discovery with approved schemas; separate preprocessor/estimator factories; extend CV to save OOF rows; separate ranking scores/probabilities/labels; version calibration and threshold utilities; keep LR coefficient analysis and add approved tree attribution separately.
5. **Verify the harness with small synthetic fixtures.** Check deterministic fold identity across candidates, metadata/label exclusion, fold-local transforms/tuning/weighting/calibration, margin handling, unavailable evidence, sparse compatibility and refusal to access test. These tests must not train on research data or imply empirical performance. An unchanged-historical-pipeline compatibility fixture is useful; it does not establish equality of results after feature/protocol changes.
6. **Add the four-family registry and approved searches.** Keep historical LR unchanged; implement new LR search, Linear SVM, RF and XGBoost only in the new approved run context. Maintain sparse text without automatic dense conversion, and record resource limits/threading. Extra parameter values, defaults or stopping rules need the frozen specification.
7. **Run development-only comparison and efficiency measurements when separately authorized.** Apply the approved tuning/cross-fitting/OOF/bootstrap/benchmark controls. Proposed future paths may use `experiments/results/experiments/<protocol_version>/<run_id>/<classifier>/<dataset>/<configuration>/`; keys must include classifier/run/seed/fold/configuration. Writers should refuse existing destinations. This proposal does not rename historical artifacts or create those directories now.
8. **Apply and record the selection hierarchy, then freeze.** Produce `model_selection_report.csv` and compatible preprocessing/classifier/calibrator/rule/schema manifests with hashes, attribution, calibration/threshold and risk/response decisions. Keep LR's confirmatory representation comparison distinct from implementation-family selection.
9. **Execute the approved unexposed evaluation and integration validation once after all freezes.** Report source-stratified findings, uncertainty, limitations, model-only and separate end-to-end efficiency, security/failure checks and reproducibility. If only exploratory evidence is available, say so and do not claim completed sealed-system validation.

**Stop condition for this task:** synchronization and this document only. Existing notebooks, datasets, results, source, dependency files and model artifacts are unchanged by Phase 2. No additional classifier or next implementation action has begun.

[N01]: ../../experiments/notebooks/01_data_audit.ipynb
[N02]: ../../experiments/notebooks/02_data_cleaning.ipynb
[N03]: ../../experiments/notebooks/03_preprocessing.ipynb
[N04]: ../../experiments/notebooks/04_feature_extraction.ipynb
[N05]: ../../experiments/notebooks/05_experiments.ipynb
