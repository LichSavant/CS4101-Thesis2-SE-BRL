# PhiUSIIL C-allocation exact-file acceptance form

**UNATTESTED REVIEW FORM ? not an execution acceptance receipt.**
Dhanwil's 2026-11-18 methodological acceptance is directly recorded. Joint
agreement is reported, subject to Vera confirmation; no independent signatures
are asserted. No fitting is authorized.

## Exact files to review

Input root: `experiments/runs/phiusiil-former-development-input-v1/`.

| Relative input path | Actual SHA-256 |
| --- | --- |
| `protocol/allocation_settings.json` | `12ba404731616f8cc6bd0062b8d2fe9f67389147a0d06ede5a16ef5f8279824c` |
| `protocol/population.json` | `a56fe920af493aff1238c9a30b5db14a5d0bc371a92e9ac85966531d45eded16` |
| `protocol/relationships.json` | `93c18fcc240cf852f1e8e609d2a45bd66e6c274a2eb5f0e9dbfaf663db2adbb3` |

ML code: copy the complete `/code_sha256` map from
`experiments/runs/phiusiil-former-development-input-v1/preparation_checks.json`,
whose exact SHA-256 is
`39f32d2aaeda459c1817d627da61fd844d919584c918ff91712b7e8c8cb07e0b`.
It must still equal `code_hashes(current checkout)` when launched.

Source-bound verification report:
`docs/research/2026-11-18_technical_admission/PHIUSIIL_C_SOURCE_VERIFICATION.json`
(SHA-256 `cd78b369cf6fa8cf51b1ae88fdee3a04c6228876db8749d799e51637f0f1bbf4`).
It checks all 165,089 original positions, native labels/targets and edges against
the authenticated source; 154,096 components, 36 mixed-label components, no
historical group splitting or protected-source decoding. This is a separate
**automated comparison by the same agent**, not independent human verification,
historical custody proof or signed acceptance.

## Method and limits requiring personal acceptance

Population: only 165,089 verified former-development positions; exclude all
70,706 historical protected positions. Accept source-bound reconstructed IDs
and the upstream membership ledger, without claiming independently authenticated
historical execution. Retain mixed-label groups without relabeling. Connected
components use literal Domain `strip().lower()` and exact URL equality only;
near-duplicate/template/campaign coverage is unavailable with explicit limitations.
New internal roles: 70/15/15 development/calibration/test, seed 42, five development
folds, maximum absolute per-class fraction error 0.05. Abort unmet constraints;
no seed search, group splitting or fallback. Exploratory previously exposed U1
technical subset only; no untouched holdout, behavioral or Transformer claim.

## Personal review and actual attestation ? not yet supplied

1. Each reviewing researcher personally checks the method and attribution above.
   Record Vera's actual confirmation where required for joint deviation acceptance;
   do not substitute Dhanwil's reported agreement for her own confirmation.
2. In an independently controlled review session, verify the exact three input
   hashes, source digest, upstream historical-development membership, locator/label
   correspondence and actual code map. Inspect the verifier's permitted-position
   restriction before running it; never open protected records in a spreadsheet.
   The original source SHA-256 is
   `a236549cd369cd80bd478ff8e1779cbf44c58d5c3f79f7a51a1adbed7d06d1c6`.
   For a repeatable read-only comparison that preserves the first report:

```powershell
python -B -c "import json; from pathlib import Path; from scripts.verify_phiusiil_c_acceptance import verify; print(json.dumps(verify(Path.cwd(), Path('..')), indent=2))"
```

3. Supply an actual dated personal review response identifying the exact three
   input hashes, code map, allowed population, reconstructed-lineage limitations,
   grouping coverage and exploratory exposure scope. Include the real review
   reference. No personal response, date or signature is filled in by this form.
4. The accepting researcher/adviser supplies
   `experiments/runs/phiusiil-former-development-input-v1/protocol/allocation_acceptance.json`.
   Its root keys must be **exactly** `version`, `stage`, `authority`, `branch`,
   `output_run_id`, `input_sha256`, `code_sha256`, `access`. Fixed values are
   `scoped-no-fit-preparation-1`, `C-allocation`, `PhiUSIIL`, and
   `phiusiil-former-development-allocation-v1`, respectively. `input_sha256` must
   contain exactly the three relative input paths/hashes above; `code_sha256` must
   be the complete bound map. `access` truthfully records metadata-only scope,
   no historical protected access and no fitting. Authority keys are exactly
   `name`, `role`, `date`, `response_reference`, `response_text`: actual nonempty
   values, role `researcher` or `adviser`, genuine ISO date not future, response
   at least 40 characters. Do not add signature keys outside the exact schema.
5. A trusted operator independently authenticates the provenance of that real
   human response/receipt and computes its SHA-256, for example with
   `Get-FileHash -Algorithm SHA256 -LiteralPath 'experiments/runs/phiusiil-former-development-input-v1/protocol/allocation_acceptance.json'`.
   Send the actual digest through that trusted review channel. Hash computation
   alone does not establish authority; this form or an agent-created hash is not
   a substitute. No mandatory outside institution is presumed.

## Execute only after genuine acceptance and trusted digest

The output namespace must not exist. With `$receiptSha256` set to the actual
independently trusted digest, run from the existing checkout:

```powershell
python -B -m ml.preparation_execution --root . --input-run-id phiusiil-former-development-input-v1 --stage C-allocation --authorization-sha256 $receiptSha256
```

D-features admission and fitting still require their own scoped acceptance and
frozen settings. Current C status: **NOT EXECUTED ? human exact-file acceptance
and independently trusted receipt digest absent**.

## Final personal review procedure

1. Dhanwil and Vera personally review the exact three input hashes above plus
   the fourth file, `preparation_checks.json`, and its complete code map. Record
   actual name/role/date/review-reference/response text; Vera must supply her own
   confirmation rather than an assistant inferring it from reported agreement.
2. The accepting researcher/adviser supplies the real exact-schema receipt at
   the path above. A trusted reviewer authenticates the personal response's
   provenance, computes the receipt hash independently and communicates the actual
   digest through the trusted review channel. No receipt is created by this form.
3. With `$receiptSha256` containing that independently trusted digest, run the
   read-only verifier below. It writes no files and performs no allocation/fitting.
   It checks original permitted population/relationship evidence and exact receipt
   bytes/schema/input/code identity. It cannot authenticate human identity or the
   digest's trust-channel provenance; those remain the reviewer's responsibility.

```powershell
python -B -m scripts.review_phiusiil_c_acceptance --source-root .. --receipt-sha256 $receiptSha256
```

4. After successful technical review **and** genuine personal/trusted-channel
   acceptance, use the C-allocation launch command above. D-feature rebinding and
   its scoped acceptance follow successful C allocation; fitting remains separate.
