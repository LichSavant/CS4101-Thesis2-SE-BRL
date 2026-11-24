# Scientific validation execution — 17 November 2026

No dataset is admitted. **Zero scientific experiments, model fits, tuning runs,
calibration fits or final evaluations were executed. No new predictive metrics
or uncertainty estimates exist.** The results below are metadata integrity and
synthetic software verification, not model-generated research findings.

## Baseline and authority

Verified existing workspace `.scientific-validation-20261117`, branch
`research/scientific-validation-20261117`, clean starting HEAD
`ee7976ef04aa6060b0c7a5e18e5a6529e0af695e`.
No branch/worktree creation, remote operation or change to another worktree occurred.

The approved proposal's Git blob SHA-256 matches
`283338c5535c5553e35266f5083a6380e014637e63d42161c659238e257ad1fe`.
Method requirements were read through the repository's proposal traceability,
protocol reconciliation, Tables 4.7–4.9 configuration reconciliation and scientific
acceptance records; no new interpretation supersedes the approved proposal.

Read authorities:

- `docs/methodology-review/SEBRL_METHODOLOGY_TRACEABILITY.md` and
  `SEBRL_APPROVED_VS_EXTENSION_MATRIX.md`;
- `docs/research/experiment_protocol_reconciliation.md`;
- `docs/research/2026-11-09_deterministic_finalization/` approval packet,
  experiment configuration, feature freeze, Email protocol and preflight resolution;
- `docs/research/2026-11-05_scientific_unblocking/` acceptance register,
  replacement protocol and real-data preflight;
- Email acceptance/lineage records and UCI scientific acceptance packet;
- `docs/r22-parser-repair-2026-11-16/agreed-integration-contract.md`,
  `integration-acceptance.json`, R22 Phase 2 integration record and V22 protocol.

R22 owner approvals remain null, `joint_acceptance=false`, `research_release=false`.
V22 is proposed, not an adopted human-reference prerequisite for the approved
deterministic classifier study. Transformer engineering remains preserved;
NLI remains review-only and cannot change deterministic labels or enter E2/E3.
All twelve indicators, evidence states and modality/context constraints are unchanged.

## Dataset readiness matrix

BLOCKED means necessary factual evidence or accepted execution scope is absent;
CONDITIONALLY BLOCKED would require sufficient authentic inputs with only a
specified, executable remaining check. None qualifies for that lesser status.

| Modality / actual branch | Status | Supported evidence | Exact admission gaps |
| --- | --- | --- | --- |
| Email E1/E2/E3 | **BLOCKED** | Four source pointer identities match the registered cleaned snapshots. Historical manifest: 38,759 unique IDs; 21,601 supplied groups; five development folds; no recorded group crossings. | Source-backed class/access/license facts; accepted primary population/CEAS role; authenticated original-record lineage or accepted prospective protocol and actual receipts; accepted duplicate/group/exposure rules and assignments; restricted development delivery; accepted deterministic rule and matched feature freeze; accepted experiment settings and exact launch authorization. |
| Content-bearing Webpage E1/E2/E3 (Putra) | **BLOCKED** | Approved source role is documented; software supports a distinct content-bearing branch. | No identified immutable content-bearing payload/snapshot, original IDs, native label mapping, class/attrition counts, duplicate relationships or supplied partitions. Need custodian source/release/license/access/schema/content evidence and scoped ingestion authorization before those checks. PhiUSIIL/UCI engineered tables cannot replace this dataset. |
| URL/technical U1-UCI and U1-PhiUSIIL, separately | **BLOCKED** | Registered pointer identities agree. UCI: 5,849 IDs/5,785 groups; PhiUSIIL: 235,795 IDs/220,086 groups. Five development folds and no recorded crossings for each. | UCI-S01–S10 evidence remains incomplete: original-source class definition/access/license, raw-to-clean original-record ledger, accepted duplicate/group/split reuse, exact audited feature dictionary, development custody, exposure disposition and bounded run settings/authority. PhiUSIIL separately requires equivalent source/label/lineage/group/dictionary/custody evidence, including FILENAME exclusion and a mixed-target conflict policy. No pooled U1 raw feature space. ISCX remains historical, outside active Table 4.7. |

No rejected or unavailable dataset was substituted. No LFS payload was materialized.
Missing working files are intentional sparse exclusions, not deleted user data.

## Actual checks and findings

`tools/scientific_validation_snapshot.py` reads only three fixed Git assignment
metadata blobs at one pinned commit, emits aggregate counts and fails on malformed
schemas, duplicate IDs, invalid roles/targets/folds, populated reserved folds,
group crossings or missing classes/folds. It never reads source content,
features, predictions or sealed-test payloads and never creates assignments.
Reserved-role membership metadata is aggregated solely for isolation checks.
No row IDs are exported. Admission is explicitly false even when integrity passes.

| Historical metadata | Target 0 / target 1 | Development / calibration / test | Mixed-target groups | Role / fold crossings |
| --- | --- | --- | --- | --- |
| Email | 37,194 / 1,565 | 27,129 / 5,815 / 5,815 | 0 | 0 / 0 |
| UCI | 2,830 / 3,019 | 4,094 / 878 / 877 | 64 | 0 / 0 |
| PhiUSIIL | 134,850 / 100,945 | 165,089 / 35,358 / 35,348 | 54 | 0 / 0 |

Every recorded development fold contains both targets. These are historical
target assertions, **not independently verified native-label semantics**.
Group disjointness does not prove that duplicate/domain/campaign relationships
were correctly identified. Mixed-target groups require an accepted disposition;
they were neither relabeled nor split here.

Email source/target separation is complete in this manifest: Nazario supplies all
1,565 positives; CEAS-08 17,312, Enron 15,791 and SpamAssassin 4,091 supply only
negatives. This establishes a source-confounding risk, not a measured fitted
source-only classifier result. The 17,312 CEAS negatives conflict with automatic
reuse as the proposal's default primary population. Removing CEAS does not repair
lineage, erase historical exposure or eliminate source/target separation.

`input-identities.json` verifies six LFS **pointer** OID/size pairs against
`ml/research-inputs.v1.json`, plus the proposal blob hash. It does not verify local
payload availability, authenticity, class meaning or scientific approval.
Manifest digests in this sprint hash Git blob bytes; older reports sometimes
hash CRLF working files. Different serialization digests alone do not establish
changed records. This sprint neither normalizes nor replaces those artifacts.

## Work completed and validation

- Resolved the sparse-checkout verification obstacle with a fixed-path,
  standard-library Git metadata checker; no data restoration required.
- Added eight synthetic regressions for integrity/admission separation,
  group leakage, duplicate IDs, reserved folds, schema/LFS rejection,
  single-class folds and source/target separation.
- Research gate returns expected native exit **2**: ten FAIL conditions,
  fitting disabled. This is a refusal, not a failed experiment.
- Existing reviewed no-fit selection: **766 passed, 10 skipped, 1 deselected**,
  one existing Starlette deprecation warning; **zero attempted/executed fits**.
  Nine skips concern absent trusted synthetic readback inputs; one concerns an
  unavailable directory-symlink permission. No skip substitutes for a pass.
- Initial same selection: 765 passed, 10 skipped, one deselected, one filesystem
  export failure. Shortening only the task-owned pytest base path from
  `.validation-scratch/pytest` to `.v/t` made the failing test and full selection
  pass, consistent with Windows path length constraints. No production behavior,
  test assertion or gate was relaxed. Both logs are retained as UTF-8 text with trailing whitespace trimmed.
- No JS changes were made; frontend tests/build/typecheck were not rerun.
  Python source compilation and metadata regressions are recorded separately.

The pre-existing Python 3.12 environment under
`%LOCALAPPDATA%/Temp/sebrl-submission-20261117/venv` supplied dependencies only.
Tests imported **this workspace's code**, with bytecode/plugin autoload disabled,
in-memory SQLite and task-owned scratch paths. No environment installation,
other source workspace execution or model download occurred. Test selection is
exactly `tools/verification/selection.json`; its genuine-fitting node is excluded.
Source-denial tests use synthetic identifiers; no excluded corpus records enter
tests or reports. Existing trusted-model readback is not claimed.

Reproduction: `python -B tools/scientific_validation_snapshot.py`;
`python -B -m unittest tools.test_scientific_validation_snapshot -v`;
`python -B -m ml.preflight --research-gate-only` (expected exit 2).
For pytest, use the dependency interpreter above with
`-B -m pytest -p ml.tests.no_fit_guard -p no:cacheprovider -q --basetemp .v/t`,
append `tests` from `selection.json` and its exact `--deselect` value. Use an
unused short basetemp for repetition. Logs and `commands.json` preserve results.

## Highest-priority next action

Obtain one authenticated **UCI development-only admission dossier** from the
source custodian, using the existing UCI-S01–S10 packet: immutable source/release
and access/license evidence; exact original Result class-definition citation;
original-record-to-cleaned-development ledger with transformation/attrition
receipts; accepted group/split/mixed-target and prior-exposure dispositions;
30-feature ordered/domain-audited dictionary; named development delivery hashes
and bounded no-fit authorization. UCI avoids waiting on Email's CEAS decision,
behavioral rule freeze or missing Web content. Its 4,094 historical development
records are a scope candidate, not automatically accepted observations.

This is the smallest coherent path to an accepted-data no-fit check; no single
signature or missing file alone opens training. Only after that check and exact
frozen settings/run authorization can a separate U1 experiment proceed. Final
calibration and sealed evaluation remain separately controlled. No historical
holdout can be called untouched merely by assigning new IDs or splits.
