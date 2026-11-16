"""Derive public counterpart facts and a proposed contract, never owner approval.

Writes exclusively into a new directory. No model, corpus, notebook, fitting or
research runner is invoked. Approval fields are deliberately left empty.
"""
import argparse
from dataclasses import fields
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.counterpart_checkout import COUNTERPART_COMMIT, load_counterpart
from ml.metadata import fingerprint
from ml.se_brl.joint_integration import CONTRACT_VERSION
from ml.se_brl.runtime_compatibility import runtime_declaration, compare_runtime_declaration


PROPOSED_CONTRACT = """# Proposed R22 joint integration contract 0.1.1

Status: PROPOSED_PENDING_JOINT_ACCEPTANCE. This file is a review proposal.
Neither researcher has approved it through generation or a passing test.
Authoritative Dhanwil baseline: ae20372db6014d4f83153c03ccc2cd92f445ca8c.
Vera runtime: isolated source copy of the preserved uncommitted implementation,
with the declared pin/profile and verification changes; bound by
vera-runtime-manifest.json. Its base commit is not a published-runtime claim.
Wire identifier: r22-joint-email-0.1.1-proposed. Revision 0.1.1 binds the repaired
dependency; it does not claim a new underlying 0.2.0 preprocessing version.

## 1. Scope and deterministic authority

The adapter is serial, offline and email-only. It uses the actual pinned
EmailObservation/PartitionAssignment types and actual identity join. It adds
no deployed endpoint, browser permission, production service or scientific
permission. engineering_only=True is required. All acceptance inputs are
synthetic software cases, not research observations, human reference labels,
model accuracy or evidence of deployment readiness.

Vera's existing deterministic observations remain authoritative in Vera's
review output. Peer rule states form a separately identified diagnostic channel.
Disagreement requires review; neither channel overwrites the other. Explicitly
injected software NLI scores can request review but cannot promote labels or
learned z values. No scorer is initialized by default. External typed identity
audits are outside this profile; domain/role mentions are not verified identity.

## 2. Schema and preprocessing reconciliation

This is a bounded mapping, not whole-runtime equality. The independent strict
whole-runtime comparator may correctly return INCOMPATIBLE because source,
schema and policy descriptors differ. Version-string equality is insufficient.

Both preprocessors must accept an input and return equal prepared views.
Vera runs first; the actual repaired peer parser runs second. Either rejection
or a differing view prevents acceptance. The peer now enforces a token-boundary
HTML5 DOCTYPE/comment policy and rejects malformed declarations, marked
sections, legacy doctypes, processing instructions and incomplete comments.
Vera's existing parser and stricter typed locator checks remain unchanged.
No uniform parser equivalence outside the reproduced cases is asserted.

Model text uses HTML-unescape, NFKC, casefold and whitespace collapse.
Original evidence and half-open Python Unicode source offsets remain separate.
Known-empty text/links remain distinct from unknown/missing values. HTML links
retain enclosing-tag locators; page URLs retain exact-text locators. Body
consent and link opt-in still apply. Generic webpage preprocessing intersection
is tested as a primitive; this does not extend the complete batch adapter to
webpage/URL/technical modalities. Owners must explicitly accept email-only scope.

The actual committed peer backend builds and validates a content-free lifecycle
envelope. Downstream analysis remains not_evaluated. Vera's richer report is a
separate nested offline review channel; it is not injected into a narrower API
schema or transmitted through a new endpoint. The general counterpart callback
does not supply equivalent review validation; this adapter validates its own
explicit trusted reviewer result.

## 3. Identity, missingness and privacy

The genuine counterpart evaluate_development_lexical validates the entire
population/assignment join before any processing. Its callback projects evidence
views only. IDs join back to exact original wrapper objects; callback position,
text equality and caller-supplied score order never establish identity.
Calibration and test rows never reach either preprocessor or reviewer.

Language is an explicit caller declaration. Unsupported/unknown language and
missing required evidence remain unavailable, never assessed absence. Native
labels, targets, groups, folds and partition fields are excluded from predictors.

Every eligible record needs an EvidenceAuthorization keyed by observation ID
and bound to a SHA-256 fingerprint of original evidence, source identity,
snapshot and language. Supplied body requires explicit Boolean consent and
purpose. Links require explicit opt-in. Gmail access, supplied content or an
existing observation never imply consent. These grants express caller consent
and custody declarations; the adapter is not an authentication service.

All requests are staged and validated before reviewer/scorer execution.
Mismatched/replayed grants, mutated evidence, missing/extra IDs, malformed joins,
counts and groups reject. Batches are bounded to 128 records. Every output is
copied/frozen and revalidated against its own original identity, fingerprint,
source fields, spans, schema and closed release fields. Malformed outputs fail
without a partial return and with sanitized errors. Injected callbacks remain
trusted software functions; this serial test guard is not an adversarial
sandbox and cannot undo arbitrary callback side effects.

## 4. Representation, exclusions and scientific boundaries

Actual behavioral_compatibility preserves incomplete evaluation as None/None,
unavailable as 0/0 and assessed absence as 0/1. Its structural matches never
grant research_ready. These are deterministic review slots, not a fitted or
calibrated learned z estimator. Partial assessment is not dimension absence.

SpaPhish/SpaFish aliases and registered excluded fingerprints remain denied.
No excluded corpus is materialized. All existing research gates remain closed,
including E2/E3, fitting, real-model inference, calibration and sealed tests.
Approved deterministic research methodology remains separate from this optional
semantic review engineering profile. This contract does not approve a semantic
research extension, human annotation study, model experiment or public results.

## 5. Repaired blocker and evidence limits

The old baseline's failing
ml/tests/test_preprocessing.py::test_invalid_html_parser_token_and_oversized_input
is retained in historical evidence. The new selected commit changes only
ml/preprocessing.py and ml/tests/test_preprocessing.py. Current verification
reruns the original regression and the expanded selected suite on native
CPython 3.12.16, without replacing parser modules. The exact parser-module
hashes, interpreter, selected node IDs, counts and JUnit results are bound to
the acceptance packet. The earlier parser defect is closed only for this
verified selected repair baseline; it is not relabeled passed historically.

The original 50 actual cross-runtime tests remain identifiable. Additional
parser/source-binding tests are separate. Preprocessing-only results are a
subset of the counterpart suite and must not be added to it as unique tests.
Dhanwil's reported wider 769 Python/backend and 38 frontend tests are not
independently reproduced by this bounded run and receive no acceptance credit.
No broad production, scientific or universal compatibility claim follows.

## 6. Exact owner decisions still required

Vera must review and expressly accept her source-bound runtime, deterministic
authority, consent/evidence bindings, offline richer report and bounded scope.
Dhanwil must endorse the current counterpart-runtime.json as an accurate
declaration for his exact commit, review the actual schemas/join/backend and
representation mapping, strict parsing/locator boundary, and repaired failure
disposition. His repair notice selects the baseline but does not approve this
contract or issue joint acceptance.

Both researchers must separately approve or request changes to this exact
contract and its reproduced evidence, identifying the counterpart commit,
Vera runtime-manifest file SHA-256, contract file SHA-256 and integration-
acceptance.json file SHA-256, with an attributable dated review reference.
Record those references in a new acceptance record referencing the immutable
packet. Do not edit a bound file after signing, create a circular self-hash,
or infer acceptance from a local flag, source manifest, test count or task.

Acceptance criteria: exact hashes reproduce; all required bounded cases pass
with zero errors/skips and no guard violations; each owner confirms their
listed decisions and both explicitly accept email-only scope and unchanged
scientific gates. Any source/contract/evidence change requires regenerated
bindings and fresh review. A hash mismatch or missing attributable approval
keeps R22 BLOCKED. Engineering acceptance never opens scientific gates.

Current approval_records remain null; joint_acceptance=false, R22=BLOCKED.
The unchanged 22-requirement rubric awards no R22 credit before both approvals.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counterpart-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "docs/r22-parser-repair-2026-11-16/counterpart-source-manifest.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--vera-verification", type=Path, required=True, help="Actual guarded-run verification.json")
    parser.add_argument("--counterpart-verification", type=Path, required=True, help="Actual guarded peer-run verification.json")
    parser.add_argument("--parser-verification", type=Path, required=True)
    parser.add_argument("--preprocessing-verification", type=Path, required=True)
    parser.add_argument("--safeguards-verification", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): parser.error("output must be a new directory")
    vera_evidence = json.loads(args.vera_verification.read_text())
    peer_evidence = json.loads(args.counterpart_verification.read_text())
    if (vera_evidence["pytest_exit_code"] != 0 or vera_evidence["blocked_operations"]
            or peer_evidence["commit"] != COUNTERPART_COMMIT or peer_evidence["blocked_operations"]
            or not peer_evidence["sources_unchanged"]):
        raise ValueError("genuine_completed_guarded_evidence_required")
    joint_cases = [n for n in vera_evidence["selected_node_ids"] if "ml/tests/test_joint_integration.py::" in n]
    if not joint_cases: raise ValueError("actual_cross_runtime_acceptance_cases_required")
    additional = {name: json.loads(record.read_text()) for name, record in (
        ("parser", args.parser_verification), ("preprocessing", args.preprocessing_verification),
        ("safeguards", args.safeguards_verification))}
    for record in (vera_evidence, peer_evidence, *additional.values()):
        counts = record["test_counts"]
        if (record["pytest_exit_code"] != 0 or record["blocked_operations"]
                or any(counts[k] for k in ("failures", "errors", "skipped"))
                or record["execution_environment"]["python_version"] != "3.12.16"
                or record["execution_environment"]["parser_modules_replaced"]):
            raise ValueError("passing_native_guarded_evidence_required")
    peer = load_counterpart(args.counterpart_root, args.manifest)
    manifest = json.loads(args.manifest.read_text())
    head = (peer.root / ".git/HEAD").read_text().strip()
    if head != COUNTERPART_COMMIT: raise ValueError("detached_selected_commit_required")
    hashes = peer.verify()
    cb = peer.compatibility.load_codebook()
    actual_schema = next(m for m in peer.modules if m.__name__ == "backend.app.sebrl_schemas")
    contract_document = peer.envelope.load_result_envelope_contract()
    parent = {i["id"]: d["id"] for d in cb["dimensions"] for i in d["indicators"]}
    normalized_sources = {name: hashlib.sha256((peer.root / name).read_text(encoding="utf-8").encode()).hexdigest() for name in hashes if name.endswith((".py", ".json"))}
    try: peer.preprocessing.preprocess({"kind": "webpage", "html": "<![bogus]>"})
    except peer.preprocessing.ArtifactParserError: strict_rejection = True
    else: raise ValueError("repaired_parser_regression_required")
    facts = {"declaration_version": "1.0.0", "base_commit": COUNTERPART_COMMIT, "source_state": "committed",
        "contracts": {
            "codebook": {"schema_version": cb["schema_version"], "version": cb["codebook_version"], "semantic_sha256": fingerprint(cb)},
            "preprocessing": {"version": peer.preprocessing.PREPROCESSING_VERSION,
                "source_utf8_lf_sha256": normalized_sources["ml/preprocessing.py"],
                "unsupported_declaration_rejection": strict_rejection, "observed_upstream_test_failure": None,
                "repair_commit": COUNTERPART_COMMIT, "native_verification_environment": peer_evidence["execution_environment"]},
            "admission": {"approval_inferred": False, "compatibility_research_ready": False,
                "policy_blockers": list(peer.compatibility.review_contract({}).policy_blockers)},
            "normalization": {"model_text": "HTML_unescape_then_NFKC_then_casefold_then_whitespace_collapse",
                "source_evidence": "unchanged_original_fields", "locators": "half_open_python_unicode_characters",
                "unknown": None, "known_empty_text": "", "known_empty_links": []},
            "taxonomy": {"indicator_order": list(parent), "parents": parent, "dimension_order": list(cb["vector_ordering"]["dimension_order"])},
            "input": {"adapter_version": peer.inputs.ADAPTER_CONTRACT_VERSION,
                "integration_version": peer.integration.INTEGRATION_VERSION,
                "evidence_view_fields": [f.name for f in fields(peer.integration.EmailEvidenceInput)],
                "text_wrapper_fields": [f.name for f in fields(peer.inputs.TextField)],
                "link_wrapper_fields": [f.name for f in fields(peer.inputs.LinkField)],
                "view_contains_identity_language_or_consent": False,
                "availability_states": [a.value for a in peer.inputs.Availability]},
            "output": {"envelope_contract_version": contract_document["contract_version"],
                "api_schema_sha256": fingerprint(actual_schema.SebrlResultEnvelopeResponse.model_json_schema()),
                "api_fields": list(actual_schema.SebrlResultEnvelopeResponse.model_fields),
                "generic_callback_output_validation": False, "semantic_review_schema": None},
            "representation": {"learned_feature_order": list(cb["vector_ordering"]["future_structure"]),
                "deterministic_support_availability": "nullable rule bits, not learned z",
                "partial_evaluation": "None/None", "unavailable": "0/0", "assessed_absence": "0/1",
                "structural_match_does_not_grant_research_authority": True},
            "semantic_model": {"semantic_review_runtime_declared_in_selected_interface": False},
            "reference_validation": {"independent_reference_acceptance_established": False},
            "policy": {"observation_author": "Vera-side automated source inspection; not Dhanwil approval",
                "fact_scope": "selected committed modules and recorded engineering probes",
                "dhanwil_approval": None, "joint_acceptance": False},
            "source_files_utf8_lf_sha256": normalized_sources},
        "research_release": {"approved_for_E2_E3": False, "approved_for_sealed_test": False, "publishable_as_validated_results": False}}
    vera_names = sorted({p.relative_to(ROOT).as_posix() for folder in (ROOT / "ml", ROOT / "backend", ROOT / "scripts") for p in folder.rglob("*.py")})
    vera_names += ["ml/research-inputs.v1.json", "ml/se_brl/codebook.v0.1.0.json", "ml/se_brl/semantic-model.v1.json",
                   "experiments/vera_validation/V13_nli_hypotheses_v0.1.0.json"]
    vera_manifest = {"source_state": "isolated_source_copy_with_declared_r22_pin_and_verifier_changes", "base_commit": "25677a98236895ad16c6acf6aa75499dd2552fd9",
        "published_runtime_claim": False, "source_files": {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in vera_names}}
    for evidence in (vera_evidence, peer_evidence, *additional.values()):
        if not evidence["vera_sources_unchanged"] or evidence["vera_source_files_sha256"] != vera_manifest["source_files"]:
            raise ValueError("verified_vera_sources_must_match_current_runtime")
    vera_manifest["manifest_content_sha256"] = fingerprint(vera_manifest)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, document in (("counterpart-runtime.json", facts), ("counterpart-source-manifest.json", manifest),
                           ("vera-runtime-manifest.json", vera_manifest),
                           ("whole-runtime-comparison.json", compare_runtime_declaration(runtime_declaration(), facts))):
        (args.output / name).write_text(json.dumps(document, indent=2) + "\n")
    (args.output / "agreed-integration-contract.md").write_text(PROPOSED_CONTRACT)
    failed = []
    for prefix, record in (("vera", args.vera_verification), ("counterpart", args.counterpart_verification),
                           ("parser", args.parser_verification), ("preprocessing", args.preprocessing_verification),
                           ("safeguards", args.safeguards_verification)):
        (args.output / (prefix + "-verification.json")).write_bytes(record.read_bytes())
        xml = record.parent / "regression.xml"
        (args.output / (prefix + "-regression.xml")).write_bytes(xml.read_bytes())
        counts = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
        document = ET.parse(xml)
        for suite in document.getroot().iter("testsuite"):
            for key in counts: counts[key] += int(suite.get(key, "0"))
        evidence = {"vera": vera_evidence, "counterpart": peer_evidence, **additional}[prefix]
        if any(counts[k] != evidence["test_counts"][k] for k in counts):
            raise ValueError("junit_evidence_count_mismatch")
        for case in document.getroot().iter("testcase"):
            if case.find("failure") is not None or case.find("error") is not None:
                failed.append({"runtime": prefix, "class": case.get("classname"), "name": case.get("name")})
    bound = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.output.iterdir()) if p.is_file()}
    packet = {"artifact_version": "r22-acceptance-evidence-0.1.1", "contract_version": CONTRACT_VERSION,
        "status": "ENGINEERING_EVIDENCE_READY_JOINT_ACCEPTANCE_BLOCKED", "counterpart_commit": COUNTERPART_COMMIT,
        "vera_source_state": "isolated_source_copy_with_declared_r22_pin_and_verifier_changes", "bound_artifact_sha256": bound,
        "actual_repository_facts_independently_verified": True,
        "declaration_authorship": "Vera-side automated derivation from selected source; not Dhanwil approval",
        "vera_tests": vera_evidence["test_counts"], "new_actual_cross_runtime_cases": len(joint_cases),
        "counterpart_tests": peer_evidence["test_counts"], "additional_tests": {name: record["test_counts"] for name, record in additional.items()}, "failed_cases": failed,
        "all_counterpart_tests_passed": not failed, "known_failure_disposition": "REPAIRED_AT_SELECTED_COMMIT_NATIVE_3_12_16_REGRESSION_PASSED_OWNER_CONTRACT_ACCEPTANCE_PENDING",
        "approval_records": {"vera": None, "dhanwil": None}, "joint_acceptance": False,
        "research_release": False, "R22": "BLOCKED",
        "required_attributable_approval_binding": ["counterpart commit", "Vera runtime manifest hash",
            "proposed contract file hash", "this acceptance packet file hash", "exact reproduced test evidence",
            "email integration scope", "known upstream parser failure disposition", "scientific gates remain closed"],
        "verification_commands": {
            "vera": [sys.executable, "-B", "scripts/verify_r22_joint.py", "--counterpart-root", str(peer.root)],
            "counterpart": [sys.executable, "-B", "scripts/verify_r22_counterpart.py", "--counterpart-root", str(peer.root)],
            "parser": [sys.executable, "-B", "scripts/verify_r22_joint.py", "--counterpart-root", str(peer.root), "--suite", "parser"],
            "preprocessing": [sys.executable, "-B", "scripts/verify_r22_counterpart.py", "--counterpart-root", str(peer.root), "--suite", "preprocessing"],
            "safeguards": [sys.executable, "-B", "scripts/verify_r22_joint.py", "--counterpart-root", str(peer.root), "--suite", "safeguards"]},
        "required_environment": {"PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
        "human_approval_not_inferred_from_passing_tests_or_flags": True}
    (args.output / "integration-acceptance.json").write_text(json.dumps(packet, indent=2) + "\n")
    print(json.dumps({"status": "PROPOSED_FACTS_NOT_OWNER_APPROVAL", "output": str(args.output), "source_files_verified": len(hashes), "joint_acceptance": False}))


if __name__ == "__main__": main()
