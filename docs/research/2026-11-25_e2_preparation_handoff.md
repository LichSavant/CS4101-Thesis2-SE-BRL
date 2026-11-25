# E2 preparation sprint — recoverable handoff

Research: SE-BRL: A Transformer-Augmented, Modality-Aware Neuro-Symbolic
Architecture for Constraint-Governed Social Engineering Behavior Inference and
Explainable Phishing Detection. Dhanwil Nick M. Alcover and Vera Marie Therese A.
Orbello, University of San Carlos.

Branch: `research/e2-preparation-20261125`, based on clean canonical main
`bb167bd6367cca574885d728f1442bc903c92d9e` (merged cleanup PR #19).
The prior cleanup branch is no longer advertised on the remote; its published
commit remains preserved through the merged history. Do not republish or redo it.
This sprint's source/test/handoff changes form a local Git checkpoint; no main
merge, force push or new restricted publication is part of this sprint.

## Implemented and software-verified

Files: `ml/e2_research_preparation.py`,
`ml/tests/test_e2_research_preparation.py`, and this handoff.

- Reproducible, input-order-independent pilot sampling with exact 75/25/75/25
  diagnostic quotas. Bipartite matching allocates one member per established
  group across all strata; inconsistent exact-duplicate groups and shortages
  fail explicitly. No automatic quota adjustment or repartitioning occurs.
  `content_sha256` binds the sorted, Unicode-preserving JSON of original fields,
  using the same convention as the existing blinded-packet helper. Delivery
  cross-checks that digest, source/group identity and partition against custody.
- Annotation delivery reuses `ml.annotation_validation.blinded_packet`; ingestion
  reuses prospective identities and connected groups. Both entrypoints invoke
  the **existing closed stage policy before consuming inputs**. The global policy
  and approved-source lists were not changed. These interfaces cannot currently
  generate real packets or ingest a new population.
- Reviewer delivery projects original evidence fields and neutral IDs only,
  omitting class/source/group metadata and previous judgments. Separate custody
  and sampling manifests remain researcher-only. Blank responses cover all twelve
  indicators and do not prefill independence or any human judgment.
- An independent-reference adapter requires externally trusted document hashes,
  artifact hashes, HTTPS provenance, custodian/date, and original-field spans.
  It produces the existing `DetectorContext`, never new detector rules. Authentic
  audit truth must be established outside the adapter. No references were imported;
  missing trust evidence stays unevaluated. Downstream detectors retain their
  segment, claim, delegation and authorized-domain checks.
- Matched E1/E2/E3 validation enforces explicit disjoint dictionaries, exact E3
  concatenation and values, identical IDs/targets/groups/folds, development-only
  partitions, finite values or explicit missingness, group isolation and both
  classes per outer fold. It rejects metadata predictors and reports complete
  source–class confounding. Feature semantics still require independent acceptance.
- One aggregate-only preparation packet binds V5.3 metadata, the existing feature
  hashes, the 96-column E2-E header, supporting evidence for all ten gate checks,
  blank response materials and outstanding decisions. It reads no email rows or
  predictions and runs no extraction, inference, calibration or classifier.

Focused command actually run:

```powershell
.venv\Scripts\python.exe -B -m pytest -p ml.tests.no_fit_guard ml/tests/test_e2_research_preparation.py -q -p no:cacheprovider --basetemp .local/pytest-e2-preparation-checkpoint
```

Result: **22 passed; zero blocked fitting attempts; zero fitting executions**.
Earlier focused runs preceded input-validation/source-URI/custody-binding changes; the final
run validates the finished implementation. Existing broad regression/extraction
and benchmark results were not rerun.

## Latest actual development results, unchanged

Read from the existing V5.3 extraction receipt/assessment, not recomputed:

| Representation | Diagnostic AP | Diagnostic F1 |
|---|---:|---:|
| V5.3 E2-D (44 predictors) | 0.553640 | 0.564326 |
| V5.3 E2-E (96 predictors) | 0.569835 | 0.568381 |

15,011 development observations; 454 supported and 641 unsupported phishing
observations; 240 supported legitimate observations; 224 E2-E patterns and
67 variable predictors. These remain optimistic target-aware in-sample pattern
diagnostics. Actual classifier AP/F1 and generalization are **unmeasured**.
No new improvement, independent behavioral accuracy or achieved target is claimed.

Candidate: `experiments/e2_enrichment_20261124/candidate_context_v6.py`, SHA-256
`74414ff27be3963ba089c75a4a04bf2ee8975ff74e9e45e68bd25343b2f1ae21`.
Outputs: `experiments/e2_enrichment_20261124/primary_v53_features_run01/`.
Original E2 and V4.2/V5.3 candidates and outputs were not overwritten.

## Dataset remediation findings and proposed decision

Only primary documentation/license metadata was accessed; no new email samples,
corpora or reserved records were downloaded. No excluded source was selected.

| Candidate | Primary evidence and readiness finding |
|---|---|
| MeAJOR v2.0 | [Publisher record](https://zenodo.org/records/18471483): 108,685 anonymized content-bearing records with source metadata and declared benign/phishing labels; live API identifies open CC BY 4.0. TREC/Nazario/Nigerian-Fraud composition creates overlap and label-semantics questions. Anonymization changes identity evidence. Not a verified cure for source confounding; exact release, native-label construction, overlap and class-collection comparability require acceptance. The [earlier author paper](https://arxiv.org/abs/2507.17978) describes a different population size, reinforcing version pinning. |
| IWSPA-AP | [Organizer documentation](https://dasavisha.github.io/IWSPA-sharedtask/): content/header and body-only tasks; submission labels use **1 legitimate / 0 phishing**, opposite the canonical target convention. Current full-corpus access, licensing, exact release and collection/label provenance were not established. Do not treat sample links or historical registration as present access authorization. |
| Phishing Pot | [Maintainer card](https://raw.githubusercontent.com/rf-peixoto/phishing_pot/main/DATASET_CARD.md) and [license](https://raw.githubusercontent.com/rf-peixoto/phishing_pot/main/LICENSE): real received malicious/unsolicited mail, CC BY-NC 4.0. No comparable legitimate class is established; campaign repetition, spam/fraud mixing and personal metadata need review. It cannot independently replace the matched two-class population. No source data was fetched. |

Strongest proposal: a **separate prospective supplementary population** with
phishing and legitimate observations collected under comparable channels/time
windows and independently justified phishing-specific labels. Preserve historical
15,011 observations as exposed development data; do not merge or repartition them
silently. Existing spam labels cannot become phishing labels by convention.

Before ingestion: obtain source/access/privacy and institutional decisions; pin
release/file digests, document native labels and inclusion/exclusion criteria,
use existing `prospective_id`, and admit exact/near-duplicate/campaign grouping
rules through `ml.prospective_allocation`. Freeze groups/partitions before any
optimization; check authorized overlaps with historical corpora. Existing source
acquisition and identity/grouping implementations are reused, not replaced.

## Annotation and trust readiness

The 200-record allocation is a diagnostic pilot, not a prevalence estimate.
Established-group diversity is not proof of campaign/near-duplicate independence.
Lawful content access, source approval and protocol acceptance precede real
sampling/delivery. Two independently identified human reviewers work separately;
disagreement requires separately recorded adjudication. Source clues inherent in
message content may limit blinding and must be reported.

Use `None` plus an uncertainty explanation for an unfilled/uncertain judgment;
do not introduce unsupported human-label states. Original-field spans use Python
Unicode character offsets. Preserve unavailable/not-evaluated states when content
or independent identity evidence is missing. Validate completed responses with
`validate_packet_response`, then use existing agreement and adjudication helpers.
Existing AI annotations and researcher filenames do not establish blinded human
provenance. No independent response or adjudication was created here.

Independent authority/identity/brand/delegation documents must be authenticated
and bound to the exact artifact through a separate trusted document registry.
Never populate that registry from the submitted manifest, class labels, suspicious
vocabulary, model scores or domain unfamiliarity. No admissible registry was
available to this sprint; trust-rule changes are deferred.

## Admission and matched evaluation

Local packet: `.local/e2-preparation-20261125/exact-run-acceptance.json`.
It is a preparation record, **not an accepted authorization**. All ten existing
gate checks remain formally unaccepted: population, source/labels, identity,
assignments, custody, behavior, dictionaries, evaluation, leakage and reproducibility.
Supporting evidence and SHA-256 bindings are grouped by those check IDs; their
presence does not grant admission. The canonical gate and every approval record
remain unchanged. Independent annotation, authentic references and applicable
adviser/institutional approvals remain external dependencies.

The packet proposes reuse of the existing nested engine/calibration/statistical
modules and four classifier families. E1 and E3 dictionaries/matrices are still
missing from an admitted matched run; their fields are explicitly null. Existing
E2-E names are a header-derived proposal, not semantic acceptance. Freeze exact
outer/inner grouping, grids, fold-local imputation/preprocessing, cross-fitted
calibration and training-only threshold selection before an authorized run.
Report all valid configurations, AP/F1/precision/recall/ROC-AUC/Brier as applicable,
group-aware intervals, folds, coverage, ablations and errors. Do not tune on exposed
holdouts or report representation diagnostics as classifier performance.

Do not set the legacy coordinator's `authorization_verified=True` based on this
packet or passing tests. Real fitting must use the legitimate existing admission
and exact-run verification requirements. Researcher-level engineering agreement
does not substitute for any independent or institutional prerequisite.

## Exact continuation checkpoint

Start in the canonical root on `research/e2-preparation-20261125`. Read this file
and the existing local packet; do not redo extraction or prior checks.

Next executable command (metadata-only, no data or fitting):

```powershell
.venv\Scripts\python.exe -B -m ml.e2_research_preparation --inspect .local/e2-preparation-20261125/exact-run-acceptance.json
```

Next substantive dependency: obtain the dataset/protocol decisions and independent
human/reference evidence described above. Then bind them into a newly reviewed
exact-run proposal; retain the prepared packet unchanged. The delivery/ingestion
interfaces intentionally remain blocked by the existing policy until a legitimate
reviewed authorization implementation exists. No data-bearing CLI bypass exists.

Status distinctions: **implemented/software-verified** preparation; pre-existing
**development-assessed** V5.3; **not independently behaviorally validated**, **not
scientifically admitted**, and **not classifier-evaluated**. Targets remain
aspirational. Defer evidence-dependent rule changes rather than start another
regex/feature micro-candidate cycle.
