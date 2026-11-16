# Transformer feasibility and proposed amendment - November 4, 2026

Status: PENDING SCIENTIFIC APPROVAL. No option is adopted, no model downloaded,
no independent annotation corpus assumed, and no transformer trained.

The master prompt's Transformer-Augmented title conflicts with the governing
approved proposal. Section 1.7 (PDF p.24) excludes supervised behavioral learning;
Sections 4.1/4.3.4-4.3.5 specify deterministic SE-BRL and four phishing-classifier
families. Behavioral ground-truth annotation is not a requirement of that approved
baseline. Existing runtime learned-slot language and old README references do not
amend the paper. This proposal preserves the completed deterministic work.

| Option | What it would mean | Data/evaluation requirements | Computational implications / limitations |
| --- | --- | --- | --- |
| A: Keep approved deterministic design and align the title | No new behavioral model; E2 is deterministic support/availability | Complete existing source/rule/partition/model-selection gates | Fastest path consistent with paper; selected phishing classifiers still require real evaluation |
| B: Frozen encoder for conventional features | Add a separately named encoder-derived representation; it does not become a behavioral detector by naming | Explicit amendment: source/model/license/version/tokenization/truncation/language/modality policy; cache/split boundaries; matched baseline/augmentation comparisons; phishing labels accepted independently | Weight/download/storage/RAM/CPU requirements not measured; encoder feature extraction timing separate from classifier-only timing; freeze model hash and feature cache provenance |
| C: Supervised behavioral transformer | Predict specified indicator/dimension labels | Major amendment: defensible independently labeled artifacts, train/evaluation separation, label definition/provenance and source/group controls; availability/locator semantics; appropriately scoped validation | No independent behavioral annotation corpus found in repository inventory. Typed labels/synthetic fixtures/rule outputs are not ground truth. No feasibility/accuracy claim or training authorization |

Recommendation for adviser review: A is the shortest route within the existing
approved study. B or C needs a dated explicit amendment before any design-specific
implementation or acquisition. Do not silently combine title B/C with method A.

Draft amendment language for B, if chosen: retain deterministic SE-BRL and its
E2 control, add an explicitly named frozen-encoder conventional augmentation,
and compare its matched baseline/fusion conditions on the same accepted records,
groups and folds. Encoder embeddings are conventional features, not behavioral
ground truth. Amend the representation/configuration and efficiency sections;
list actual encoder/tokenizer/cache policies as Pending until selected and frozen.

Draft amendment language for C, if chosen: introduce a separate supervised
behavioral prediction question and independently evidenced label/evaluation
protocol while preserving deterministic E2 as a control. Amend scope, research
instruments, eligible sources, target definitions, annotation/administrative
requirements where applicable, split/availability policies and validation claims.
No such corpus, protocol or institutional approval is established by this draft.
Both drafts require explicit acceptance; neither edits the approved proposal.

For B, a pretrained encoder is not automatically source-independent or leakage-free.
Pretraining overlap/provenance may be uncertain; freeze language coverage,
truncation, upstream normalization, batching and fit-free extraction boundaries.
Any fitted dimensionality reduction, resampling, fine-tuning or normalization
belongs inside training folds. Use explicit modality availability and no content
features for technical U1. Compare against deterministic E2 and matched E1/E3 only
under newly approved representation names; preserve historical results.

For C, training on rule-generated labels is weak supervision/distillation. It
cannot support independent behavioral prediction accuracy or validation claims
against the same rules. It would require a separately defensible evaluation
target and uncertainty/availability policy. Do not create a human-annotation
prerequisite for the current deterministic study merely because C is proposed.

No model family/size, tokenizer, epoch count, label taxonomy change, annotation
scheme, data source, hardware budget or latency target is selected here.
Measurements needed before any cost claim: encoder loading and peak memory,
feature-extraction p50/p95 and throughput, batch/token lengths, cache/model bytes,
threads/device/hardware/software and end-to-end impact. The synthetic callback
benchmark does not estimate transformer performance.

Safe architecture-independent work completed: feature dictionaries, score/OOF
alignment, fresh fold pipeline callback, metrics and immutable synthetic result
ports. The runner rejects transformer as an unapproved classifier family and
never imports torch/transformers. It does not commit to encoder or supervised
behavioral architecture.

Required decision record: chosen option, title/method changes, affected RQs and
representations, actual source/label/access eligibility, protected-group and test
exposure plan, comparison/search/metric/resource protocol, versions/hashes,
approver role/date/rationale and permitted claims. Leave all fields Pending until
evidenced. If B/C is deferred, approved deterministic development may advance once
its own source/experimental gates are satisfied.

