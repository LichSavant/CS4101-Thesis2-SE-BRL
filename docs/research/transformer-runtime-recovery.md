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

## Remaining acquisition requirement

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
