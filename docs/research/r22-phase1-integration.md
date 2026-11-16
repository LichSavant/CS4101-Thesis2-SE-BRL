# Dhanwil R22 integration — Phase 1

Source: `ae20372db6014d4f83153c03ccc2cd92f445ca8c` from
`LichSavant/-SE-BRL-Research-Review`. Destination base:
`a6e849a2ee107e9f0a2330b1d05d7c8d4a4925ca` from original `main`.
The histories have no common ancestor; this is a selective file integration,
not a merge of unrelated histories. Line-ending-only differences were omitted.

Integrated deterministic features, guarded offline research tooling, privacy
repairs, opt-in artifact analysis, tests, source-only notebooks and supporting
research documentation. Existing schemas, datasets, historical results, proposal
documents and `experiments/vera_validation` remain unchanged. No Vera review
implementation is imported in this phase.

The new artifact API rejects non-email kinds before analysis, and the workbench
offers email only. Reusable offline modules for other modalities remain dormant;
their presence and historical proposal documents do not authorize extending the
joint integration beyond email. No model bundle or scientific acceptance is
created by this integration.

Deterministic labels remain authoritative. Transformer/NLI candidates are
review-only and receive no new connection to the authoritative label path.
Unknown, partially evaluated and assessed-absent evidence remain distinct.
Existing research acceptance, development-only access, sealed-test and fit gates
remain in force. Excluded-source checks use synthetic identifiers only; no
SpaPhish corpus files are read, changed, copied or admitted to any pipeline.

Verification used an isolated source copy and cached pinned dependencies:

- `python -B tools/verification/verify.py setup --workspace <external> --wheelhouse <cached-wheels>`: passed.
- `python -B tools/verification/verify.py run --workspace <external> --frontend`:
  Python selection passed (769 passed, 10 skipped, 1 deselected). The frontend
  subprocess initially failed on sandbox filesystem access; reruns below passed.
- Additional existing assessment, codebook, detector, envelope, rule and parser
  tests plus no-fit artifact API checks: 262 passed, 3 fitting-fixture-dependent
  tests deselected. Includes four non-email rejection checks.
- `npm.cmd test`: 37 passed (24 extension, 13 dashboard).
- `npm.cmd run typecheck`, `npm.cmd run lint`, `npm.cmd run build`: passed.

Both Python runs used `-p ml.tests.no_fit_guard`: zero fitting attempts and zero
fitting executions. Nine skips require explicitly trusted existing synthetic
readback inputs; one skip requires directory-symlink permission. No training,
scientific experiment, dataset ingestion or historical notebook execution ran.
Generated environments, databases, logs and frontend builds stayed outside Git.

Phase 1 only. Vera integration and combined R22 verification remain pending.
