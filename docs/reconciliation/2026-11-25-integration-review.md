# SE-BRL reconciliation — local integration review

**Follow-up status:** targeted assessment cleared normal publication of the
source-only reconciliation branch. The original publication hold described
below is superseded by the follow-up assessment at the end of this report.
Main merge still requires final researcher approval.

Research: **SE-BRL: A Transformer-Augmented, Modality-Aware Neuro-Symbolic
Architecture for Constraint-Governed Social Engineering Behavior Inference and
Explainable Phishing Detection**. Researchers: Dhanwil Nick M. Alcover and Vera
Marie Therese A. Orbello, University of San Carlos.

## Outcome and publication boundary

The canonical workspace now contains canonical main's approved R22 and verified
Transformer/browser runtime, the scientific branch's committed implementation,
the complete local E2 candidate/extraction directory and Chapter 5 artifacts.
No model fitting, research extraction, approval fabrication, history rewrite,
force push or main merge occurred. V4.2 remains experimental.

**Publication is blocked, not complete.** Fetched canonical main already tracks
raw/cleaned email datasets through Git LFS pointers. Their reachable history and
LFS publication boundary require repository-owner review under the execution
directive. Ignore rules do not remove tracked files or historical LFS references.
Dataset and build-cache tracking is removed from the candidate index while all
local files remain intact; historical LFS references still exist. No dataset was
staged by this reconciliation and no push was attempted. Do not
merge this candidate before resolving publication review and obtaining final
researcher merge approval. No visibility or permissions were changed.

Integration branch: `reconciliation/canonical-20261125`, based on fetched main
`ee7976ef04aa6060b0c7a5e18e5a6529e0af695e`. Imported scientific source:
`e95492ef13039782b43e55dcad42f2421b5aee85`. Original engineering branch:
`6bded57d38e9b83ba718d7795b97e2130128c23f`. Final commit references are available
from `git log -2 reconciliation/canonical-20261125` and the local state file.
Implementation commit: `2a94d5c43bfae6d5c1462bee94ec53829374cd0b`.

## Workspace inventory and dispositions

| Source | Disposition |
|---|---|
| Canonical root, engineering branch | Original dirty state recorded; code/doc variants preserved by SHA-256 before assembly; original branch retained |
| `.scientific-validation-20261117`, `e95492e` | Committed sources selectively integrated; complete E2 and Chapter 5 copied locally; uncommitted production rule variants isolated as experimental snapshots |
| `.sprint-transformer-release-readiness`, `ee7976e` | Clean canonical duplicate; verified runtime, privacy safeguards and model pins retained |
| `.r22-phase1-integration`, `6e699b2` | Historical ancestor; source/status recorded, verified browser assets reused with hash checks |
| `.r22-review`, `ae20372` | Dhanwil public R22 repair source, already reflected in canonical integration; historical source retained |
| `.r22-vera`, `25677a9` | No-checkout Git source preserved; current remote independently fetched |
| `.r22-audit/vera-source` | Standalone historical source export, not an independent Git repository; hashes and recovery retained |
| Sibling `Thesis_Prototype` | Standalone legacy prototype; preserved source variants, no production replacement |
| Sibling `SE-BRL-Research-Review-Export`, `6a41d94` | Clean historical review export; unique content preserved, current remote `ae20372` already represented |
| Vera current remote, `337c3c4f23c1aeff7b16f5d6924eb377a52393af` | All 88 changed files classified: 81 canonical duplicates, seven exact variants retained in `research/historical/vera-review-337c3c4` |
| Temp `sebrl-final-int`, `6e699b2` | Clean detached historical worktree; ancestor already integrated |
| `.venv-transformer/integration-final`, `27e19d1` | Locked/initializing historical worktree metadata recorded; ancestor retained |
| Desktop `SEBRL_Recovery_20261120` | Existing Git metadata recovery retained; no redundant repository backup |

Parent Projects and relevant Desktop directory names were inspected without
scanning unrelated projects. Known local branches, remote refs, worktrees and
stashes are recorded. Canonical and legacy remotes were fetched; their main tips
match. `origin/data-preprocessing` has no commits outside canonical main. No
separately named R1–R22 local branch series was discovered; recoverable R22
sources and approved integration commits were inspected instead. Vera's original
device and unpublished workspaces were inaccessible; remote review reconciliation
does not certify their completeness. Some historical pytest cache directories
were inaccessible and excluded. No inaccessible cache is treated as a research
contribution.

Local recovery: `.reconciliation-local/inventory.json`, content-addressed
`objects/`, tracked patches and `source-dispositions.json`. Initial inventory has
3,201 file dispositions across nine source directories; assembly has 1,010
decisions. Thirty-two differing root variants were preserved before selecting
committed sources (including generated build metadata and historical notebooks).
No original source workspace was deleted. Large/restricted datasets and 614 MB
of scientific run artifacts remain in their original controlled local locations
with hashes; they were not duplicated or staged. The nested scientific directory
remains inside the canonical workspace. Complete E2 continuation inputs are also
available directly at the canonical experiment path.

## Implementation and methodological decisions

Preserved four dimensions, twelve indicators and email/webpage/URL research
contracts. Approved deterministic evidence remains authoritative; semantic review
cannot promote unsupported indicators. The approved email-only Phase 1 UI/API
scope, selected-message tracking, consent gates, on-device semantic inference and
no-content-telemetry protections remain intact. Historical source copies do not
become production imports. Existing production/model pins were not substituted.

Browser packaging now resolves existing verified assets through
`SEBRL_LOCAL_ASSET_ROOT`, or the existing local cache locations, without copying
weights into Git or weakening byte verification. The canonical build packages
the local runtime successfully without downloading a model. On a fresh machine,
verified assets must be prepared separately; this is an explicit local prerequisite.

Existing scientific gate records retain their original scope and exact bytes.
The supplementary E2 gate is closed. The frozen 35-rule candidate and historical
30/30 authored-case receipt were preserved; 30/30 was not freshly re-executed.
The E2 README explains diagnostic limitations and the scientific continuation
requirements. Four-family synthetic readiness is preserved as reported evidence,
not newly executed fitting or a predictive-performance claim.

## Verification

| Command/check | Actual result |
|---|---|
| `npm.cmd test` | Extension 37 tests/11 files; dashboard 13 tests/2 files; all passed |
| `npm.cmd run typecheck` | Passed |
| `npm.cmd run lint` | Passed (repository's strict TypeScript check) |
| `npm.cmd run build` | Both builds passed; approved assets hash-checked; no model weights packaged |
| Pinned Python safe regression selection + portability, process-wide no-fit plugin | 775 passed, 10 skipped, 1 deselected, 1 portability temp-location failure; 1 Starlette deprecation warning |
| Portability checks repeated with an external temp directory | 3 passed; previous failure was repository-isolation guard working correctly |
| Twelve scientific-branch changed test modules, no-fit plugin | 189 passed |
| `verify_e2_local.py` | 36 integrity/schema/group-fold checks passed; 14 candidate modules parsed; five aligned 15,011-row matrices |
| `verify_e2_local.py --staged` | 58 checks passed, including exact Git-index bytes for 22 frozen references |
| Source/staging credential-pattern and size audit | No candidate matches in reviewed allowlist; raw/row-level artifacts excluded; not a certification of all pre-existing history |
| Python syntax and notebook parsing | Canonical Python source parsed; eight local notebooks parsed without execution |

Test counts above overlap and must not be added into a unique total. Nine skips
require explicitly supplied existing synthetic bundles; one requires Windows
symlink permission. A genuine-fitting case was deliberately deselected. Both
Python runs reported zero blocked fitting attempts and zero fitting executions.
This is the repository's safe verification selection, not unrestricted research
fitting tests. Initial sandbox frontend access and missing Python dependencies
were resolved; pinned verification dependencies are installed in canonical `.venv`.
React review found no integration change requiring component restructuring.
`git diff --cached --check` reports whitespace in preserved historical sources
(including authored Markdown hard breaks and frozen candidate context bytes).
These were retained rather than cosmetically changing evidence-bound files.

## Remaining decisions and continuation

Resolve existing dataset/LFS publication exposure with the repository owner; do
not automatically rewrite history. Review the exact local commit and staged paths
before any authorized branch push. After a safe push, request one final main-merge
approval, then synchronize this same workspace without dropping restricted local
artifacts. No main-merge approval is requested while publication remains blocked.

For E2, reuse the verified matched inputs, preserve historical results and source
snapshots, resolve source/label/grouping limitations, freeze the dictionary and
nested evaluation settings, and obtain applicable exact-run scientific admission.
Then perform one authorized baseline evaluation before proposing improvements.
AP/F1 0.80 minimum and 0.90 stretch remain aspirational objectives. No uncontrolled
optimization or reserved-test tuning is authorized by consolidation.

## Follow-up: targeted LFS publication assessment

The canonical remote was fetched again and remains at
`ee7976ef04aa6060b0c7a5e18e5a6529e0af695e`. GitHub repository metadata confirms
public visibility and authenticated push access. No visibility or access settings
were changed.

Canonical main already references 19 LFS paths representing 15 unique objects.
Eight email paths represent four shared objects: each raw file below has the same
object as its cleaned-path counterpart. All eight pointers already exist in
canonical remote history.

| Raw email path under `experiments/datasets-raw/email/` | Corresponding path under `experiments/data/interim/email/` |
|---|---|
| `ceas_08/CEAS_08.csv` | `ceas_08_clean.csv` |
| `enron/Enron.csv` | `enron_clean.csv` |
| `nazario/Nazario.csv` | `nazario_clean.csv` |
| `spamassasin/SpamAssasin.csv` | `spamassassin_clean.csv` |

GitHub's anonymous LFS download-batch metadata API confirmed all 15 objects,
including all four email objects, available from the existing remote. Only
existence metadata was requested; no email data or signed download URLs were
printed, retained or followed. This establishes inherited public availability,
not permission to redistribute personal information.

The two implementation/report commits introduced 216 new Git blobs, zero new
LFS pointer blobs and no restricted-path, credential-pattern or JSON row/payload
candidates in the targeted scan. The newly added CSV tables were already reviewed
as aggregate metrics or source manifests, not record-level data. Dataset pointers
are deleted from the candidate tip. `git lfs push --dry-run origin
reconciliation/canonical-20261125` selected zero uploads. A normal branch push
therefore adds source/configuration, aggregate historical evidence and provenance;
it does not upload additional restricted LFS content. The additional follow-up
commit changes only this report and is inspected before publication.

The publisher's live metadata for [Zenodo record 8339691](https://zenodo.org/records/8339691)
identifies open access and CC BY 4.0. Existing attribution/provenance is retained.
That dataset license does not establish subject consent, complete historical
custody, or institutional permission for individual email contents. Those matters
remain a separate inherited-exposure review. Publication clearance here applies
only to the non-sensitive reconciliation changes expressly authorized by the
researcher; it does not grant dataset redistribution or scientific-fitting authority.

Least disruptive inherited-exposure response: the owner should review custody,
privacy and third-party rights and decide whether historical public availability
requires restriction or removal. Changing visibility/access, removing remote LFS
objects or coordinated history cleanup requires separate approval; none occurred.
No history rewrite or new source-only orphan repository is necessary for this push.

Continuity check: original E2 baseline, all five frozen matched matrices, nested
engine, admission records, extension/Transformer implementation, dashboard,
historical aggregate results and Chapter 5 notebook are present directly in the
canonical workspace. Chapter 5 retains 16 figure files. Local restricted data
remain ignored and intact. Vera's accessible contributions remain preserved;
unpublished work on her original device remains inaccessible and is not certified.
Scientific fitting remains false. Existing regressions were not repeated because
this follow-up changes documentation only.

Recommendation: publish the reconciliation branch normally, verify its remote
SHA, then review the final compare diff and obtain one main-merge approval.
Until that approval, the canonical workspace stays on the synchronized integration
branch. Preserve ignored research inputs when subsequently updating main.
