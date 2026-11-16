# Transformer runtime recovery

Branch: `research/transformer-validation`. Synthetic engineering verification only.

- Restored the hypothesis working file to LF bytes matching the unchanged approved
  SHA-256 `e4ccfdbb799d064c13ccccedf50be1a49818e910b9e9c0f9b3557b7da1ecfb2d`.
  Git already stored these bytes; the file-specific `eol=lf` rule prevents recurrence.
- Isolated `.venv-transformer`: Python 3.12.10, PyTorch 2.6.0+cpu,
  Transformers 4.49.0, pytest 8.4.2, NumPy 2.2.6. All installed dependencies
  are pinned in `tools/verification/requirements-transformer.txt`; production
  requirements and other environments are unchanged. `pip check` passes.
- Native imports were verified outside the execution sandbox. Initially resolved
  NumPy 2.5.5 failed Windows Application Control; the repository's established
  NumPy 2.2.6 imports successfully. No host security settings were changed.
- 681 selected existing synthetic tests passed, zero failures/errors/skips and
  zero guard violations. See `transformer-runtime-verification.json` for suites.
  The existing `verify_semantic_review` harness enforced offline/no-dataset/no-fit
  tripwires. Windows platform metadata was collected before enabling its guard
  so JUnit reporting did not attempt a prohibited subprocess.
- Verified disagreement/ties, abstention, context/identity constraints, grounded
  offsets, tamper rejection, missing-model behavior, unchanged deterministic
  labels, legacy autonomous controllers, and closed finalization gates using
  injected synthetic scorers. This does not establish behavioral accuracy.

## Recreate the isolated runtime

```powershell
python -m venv .venv-transformer
.venv-transformer/Scripts/python -m pip install -r tools/verification/requirements-transformer.txt
.venv-transformer/Scripts/python -m pip check
```

## Original acquisition requirement (resolved)

The follow-up acquisition was explicitly approved. All seven allowlisted files
from the exact pinned revision passed upstream size/digest checks before loading.
See `tools/verification/pinned-minilm-files.json` for upstream metadata and
`pinned-minilm-offline-verification.json` for the complete synthetic verification
record. The model lock and scientific contracts remain unchanged.

Reproduce with the already acquired, ignored local cache:

```powershell
.venv-transformer/Scripts/python -B scripts/verify_pinned_minilm.py --cache .venv-transformer/model-cache/hub --output .venv-transformer/pinned-minilm-offline-results.json
```

This verifier never downloads. It verifies the exact seven files before loading,
blocks network/subprocess operations and research-file reads, and runs on CPU with
two inference threads. urllib3's local IPv6 capability probe is denied and recorded;
all unexpected blocked operations fail verification. On this Windows host, native
dependency imports require execution outside the agent sandbox; network remains
blocked by the verifier's process audit throughout model loading and inference.

Results: 681 guarded regressions passed; 20 real-model synthetic review cases
passed, including all twelve behavioral indicators, with 312 real scorer calls.
Evidence tampering and predictor export were rejected; oversized input abstained
before model execution. Unknown content, unsupported modalities and unaudited
identity evidence remained unavailable. Deterministic labels/evidence stayed
unchanged, candidates stayed abstained/unavailable, learned slots stayed empty,
and scientific gates stayed closed. All twelve target indicator cases raised
review disagreements; this is engineering integration evidence, not accuracy.

Observed loading time was 2.97 seconds after integrity hashing (OS cache may be
warm; dependency imports excluded). Three-hypothesis scorer calls had median
75.2 ms, mean 75.3 ms and p95 95.0 ms on two CPU threads. Whole-process peak
resident memory was 487.7 MiB and peak committed memory was 1.32 GiB; these
include native allocations and dependencies, not just model memory. The seven
files and local cache occupy 331,111,701 logical file bytes (315.8 MiB), including
328,499,560 weight bytes. No runtime blocker remains. Semantic accuracy,
calibration, independent identity truth and scientific release remain unvalidated.

### Historical pre-acquisition state

Known Hugging Face and sentence-transformer cache directories were absent; no
cache environment overrides were configured. The installed runtime's effective
cache is `%USERPROFILE%/.cache/huggingface/hub`. Explicit initialization with
`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1` and the existing local-only loader
returned `Pinned local model is unavailable`.

An explicitly authorized acquisition must provision tokenizer/configuration and
PyTorch-compatible weights for **only** `cross-encoder/nli-MiniLM2-L6-H768`,
revision **`b95119ce93d3e065de6214e38cd4a97b0f2f2c6d`**, into the Hugging Face
cache snapshot for that exact revision. The revision's upstream provenance is
still not independently authenticated, as recorded in the unchanged model lock.
No weights were downloaded or substituted here.

Once that snapshot is available, run a bounded offline synthetic comparison:
symbolic-only versus explicitly injected `PinnedLocalNliScorer`, checking
executed scores, original evidence offsets, review/abstention signals, unchanged
deterministic labels, empty learned slots and closed scientific release flags.
Real inference remains unverified until then. R22 safeguards, SpaPhish exclusion,
sealed tests, hypotheses, rules, hashes and scientific contracts are unchanged.
