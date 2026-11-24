# Narrow authentication revision — PROPOSED, NOT ACCEPTED

## Determination and controlling evidence

The approved proposal assigns source hashing and record audits to the researchers
(PDF pp.63–65, Table 4.4). Page 63 permits a later change only through a dated
deviation, technical justification, joint approval and confirmation that the
sealed test was not accessed. The retained primary extraction is
`../2026-11-17_uci_admission/research-authority-primary-evidence.json`, especially
`findings` and `key_text.page_63_deviation`. No blanket external custodian or
external receipt-digest authenticator is specified in this inspected methodology.

External receipt authentication is an additional implementation requirement:
`ml/preparation_execution.py:3` and `run_preparation`; trusted operator acceptance
is enforced by `ml/research_protocol.py:verify_accepted_run`, with typed fitting
contexts enforced by `ml/preflight.py:require_research_fitting`. This does not
make it optional under the current implementation. Moreover,
`PHIUSIIL_C_PERSONAL_ACCEPTANCE_RECORD.json:response_text_verbatim` expressly makes
the actual personal C acceptance conditional on independent verification and
excludes fitting. General prior agreement does not revoke that condition.

## Exact proposed change for researcher acceptance

For this exploratory PhiUSIIL scope only, replace **externally authenticated
receipt provenance/digest as a prerequisite** with **a directly attributable,
dated researcher exact-file acceptance plus reproducible automated integrity and
source/record checks**. The accepting researchers must expressly supersede the
independent-verification condition in the prior personal C response and record
joint acceptance of this dated protocol deviation. No outside institution or
fabricated independent signature is substituted. Existing recorded scope and
technical verification support this proposal, not its acceptance.

Retain all other checks: immutable original source and historical artifacts;
165,089 source-bound former-development positions; exclusion of all 70,706
historical protected observations; exact labels/locators/input/code/environment
bindings; unchanged conflict observations; verified relationship components;
group-disjoint folds and train-only preprocessing; explicit historical exposure
and reconstructed-lineage limitations; exclusive reproducible outputs. Keep the
accepted-scope 70/15/15 plan distinct from the historical folds until allocation
is actually executed and accepted. No new internal test becomes an untouched
holdout. Reproduction must be possible by an independent person, but a prior
independent person's signature is not proposed as the execution prerequisite.

After explicit acceptance, implement and test this **narrow, versioned**
authority-policy revision in the existing verifier and C/D gates. Do not accept a
boolean bypass, arbitrary self-supplied hash or unverified context. Retain exact
input/code hashes as integrity checks rather than claims of external authority;
retain typed verified fitting contexts and separate exact fitting permission.
No gate code is changed or exercised by this proposal.

## Smallest proposed experiment — separately unapproved

After C/D admission and a separate exact fitting decision, run only the existing
`logistic_regression-004` candidate from
`../2026-11-18_phiusiil_descriptive/candidate_experiment_configuration.json`:
ten frozen technical fields; C=1; class_weight=null; L2/liblinear; intercept=true;
max_iter=2000; tolerance=0.0001; seed=42; missing values rejected; training-fold
standardization. Use the existing nested engine's five accepted grouped outer
folds, training-only sigmoid calibration and fixed probability threshold 0.5.
One candidate means no hyperparameter search; existing calibration cross-fits
still require multiple estimator fits, not one literal fit. Predeclare precision,
recall, F1 and balanced accuracy from genuine out-of-fold predictions. No 152-grid
launch, behavioral comparison, feature selection, ablation or protected evaluation
is authorized here. Technical-only inputs cannot support a valid SE-BRL behavioral
contribution comparison.

**Current status:** proposal only. Actual C acceptance remains conditional; the
proposed authority revision and this fixed-baseline fitting run have not been
accepted. No new packet, receipt, signature, trusted digest, allocation or model
result is generated. Proceed only after actual researcher acceptance of the
revision and separate admission/fitting authority; otherwise preserve all gates.
