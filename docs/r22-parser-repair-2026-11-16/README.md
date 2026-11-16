# R22 public implementation and approval evidence

**READY FOR HUMAN R22 APPROVAL. R22 remains BLOCKED; 21/22 (95.45%).**
Both approvals are null. The filename agreed-integration-contract.md remains a
proposal, not agreement. Review-only policy is proposed for R22; no formal
researcher approval has been supplied. Scientific methodology remains the
approved deterministic baseline, with optional semantic tooling outside it.

This public packet is a new privacy projection of actual software verification.
The original immutable local packet is preserved unchanged; its digest and the
scope of historical 420/145-result reuse are explicit. Historical runs are not
claimed freshly executed. Fresh results: 1067 owned checks (including the 50
joint and 34 parser/source-binding cases), 52 actual counterpart preprocessing
checks, 29 JS tests, typecheck/build and seven supplemental Gmail privacy checks.
All current Python scopes have zero failures/errors/skips/guard violations.

## Reproduction

Use a separate checkout of Dhanwil's exact commit
ae20372db6014d4f83153c03ccc2cd92f445ca8c, with only the manifest-approved public
source files materialized. Verify SHA-256 and Git blob identities before import.
Native Python 3.12.16 is required for the recorded exact environment; dependencies
and parser-module hashes are recorded in each public result. No real model,
corpus operation, notebook or research experiment is permitted.

```sh
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
python -B scripts/verify_r22_joint.py --counterpart-root "$PEER"
python -B scripts/verify_r22_joint.py --counterpart-root "$PEER" --suite parser
python -B scripts/verify_r22_counterpart.py --counterpart-root "$PEER" --suite preprocessing
python -B tools/review_verification/run_safe_owned.py --vera-root . --counterpart-root "$PEER"
npm ci
npm test
npm run typecheck
npm run build
node scripts/verify_gmail_privacy.cjs "$PWD/node_modules/typescript/lib/typescript.js"
```

Expected Python counts are 50, 34, 52 and 1067; the 50/34 are subsets of 1067.
The owned runner explicitly omits fitted-feature cases and corpus-alias
parameterized cases before selection. Defense deny rules remain intact. All
writes are temporary/isolated, real model imports and external calls are denied.
npm audit reports 9 advisories (2 critical, 4 high, 3 moderate); this is not
production security clearance.

## Required acceptance

Dhanwil endorses his source-derived declaration, actual schema/join/backend and
nullable representation mapping, repaired parser/locator boundary and email-only
scope. Vera accepts her manifest-bound runtime, deterministic authority, consent
and evidence bindings, richer offline review report and semantic non-promotion.
Both provide attributable dated approval references naming the full published
Vera commit, exact peer commit, runtime-manifest, contract and acceptance-packet
hashes, and reproduced evidence. The enclosing commit supplies Vera's identity;
a file cannot contain its own enclosing commit SHA. No approval is inferred
from generated files, source equality, synthetic checks or assistant output.

All scientific gates remain closed. URL/technical records do not become
behavioral evidence. The complete joint batch profile is email-only; standalone
webpage preprocessing checks do not authorize a webpage production adapter.
Experimental semantic-first V15/V17/V20 paths remain separate and unapproved.
