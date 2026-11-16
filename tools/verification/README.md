# Portable synthetic/no-fit verification

Use Python **3.12** (verified on Windows x64 with Python 3.12.10), Node >=20
and npm. `requirements.txt` pins the observed scientific/backend/test versions;
it does not change the application requirements or approve research settings.

Run from any working directory with the absolute path to `verify.py`. All generated
files go to a new **external** workspace: environment, wheel downloads, source
copy, tests, logs, SQLite fixtures and frontend builds. Existing workspaces are
rejected. No historical verification JSON or installed temporary packages are used.

PowerShell example from the repository root:

```powershell
$repoRoot = (Get-Location).Path
$verificationRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('sebrl-portable-' + [guid]::NewGuid())
py -3.12 -B "$repoRoot/tools/verification/verify.py" setup --workspace "$verificationRoot" --allow-download
py -3.12 -B "$repoRoot/tools/verification/verify.py" run --workspace "$verificationRoot" --frontend
```

`--allow-download` requires researcher permission before use. It downloads only
the declared pins from PyPI; installation uses the resulting wheelhouse with
`--no-index --no-deps --require-hashes`, followed by `pip check`. The downloaded
wheel SHA-256 values and installation report are retained outside the repository.
Hashes record retrieved wheel identity; they are not independent supply-chain
attestation. Original scientific pins and model-persistence trust checks remain.

Offline repetition into another new workspace:

```powershell
$secondRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('sebrl-offline-' + [guid]::NewGuid())
py -3.12 -B "$repoRoot/tools/verification/verify.py" setup --workspace "$secondRoot" --wheelhouse "$verificationRoot/wheels"
py -3.12 -B "$repoRoot/tools/verification/verify.py" run --workspace "$secondRoot"
```

Frontend installation uses `npm ci --offline --ignore-scripts` and the supplied
package lock, installing into the copied tree. An already populated npm cache is
necessary for that optional step. Missing cache entries fail without downloading;
they do not silently skip or pass frontend checks. A future online npm installation
requires separate authorization. Python verification has no npm dependency.

## Existing synthetic model readback (optional, explicit)

No fitting is permitted. Without an explicitly supplied synthetic root and its
independently trusted receipt digest, existing-model tests report skips. To verify
readback, provide both options on `run`:

```powershell
py -3.12 -B "$repoRoot/tools/verification/verify.py" run --workspace "$verificationRoot" --readback-root '<explicit-synthetic-fixture-directory>' --receipt-sha256 '<independently-trusted-sha256>' --frontend
```

Only the receipt and four named synthetic model directories are copied. Original
fixtures are not modified. Their exact component/dependency hashes remain checked
by existing loaders. Fixture custody remains a declared external test input; no
machine path, model download or replacement training fallback is inferred.

`selection.json` explicitly lists the reviewed no-fit selection and the one
excluded genuine-fitting node. The no-fit plugin loads before collection; any
attempted supported fit fails the session, including an attempt caught by a test.
Source-denial regressions use identifiers only, never excluded corpus records.
No original dataset, research run, .env, .git, application venv or dependency tree
is copied. Two explicitly named notebook sources are copied with stored outputs
removed for aggregation-helper and companion-source checks; notebooks are not executed.

Evidence is in `*-command.json`, `*-result.json`, `*.txt`, `installation.json`,
`wheel-integrity.json`, `requirements-hashed.txt`, `setup.json` and `run.json`.
`run.json` appears only after all requested checks pass. Python test output includes
passes, skips, deselections and no-fit status. A Python-only pass does not claim
frontend verification; a pass without readback inputs does not claim model reload.
