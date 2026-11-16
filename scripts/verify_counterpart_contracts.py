"""Bounded probes against hash-pinned actual counterpart source, never acceptance.

No downloads, corpus reads, notebook execution, fitting or model dependencies.
The supplied source-only mirror must match the recorded public Git blobs.
"""
import argparse
import ast
from dataclasses import asdict, fields
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def verify_sources(root, manifest):
    for name, expected in manifest["source_files"].items():
        path = root / name
        if path.is_symlink() or root.resolve() not in path.resolve().parents:
            raise ValueError("counterpart_source_path_rejected")
        raw = path.read_bytes()
        if (hashlib.sha256(raw).hexdigest() != expected["sha256"]
                or hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != expected["git_blob_sha1"]):
            raise ValueError("counterpart_source_hash_mismatch:" + name)
    return len(manifest["source_files"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counterpart-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "docs/vera-outstanding-2026-11-15/counterpart-sources.json")
    args = parser.parse_args()
    mirror = args.counterpart_root.resolve()
    manifest = json.loads(args.manifest.read_text())
    verified = verify_sources(mirror, manifest)
    run = Path(tempfile.mkdtemp(prefix="sebrl-counterpart-contracts-")).resolve()
    blocked = []
    def audit(event, values):
        if event in {"socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system"}:
            blocked.append(event)
            raise RuntimeError("counterpart_probe_external_execution_prohibited")
        if event == "import" and values[0].split(".")[0] in {"torch", "transformers", "sklearn", "xgboost"}:
            blocked.append("model_import")
            raise RuntimeError("counterpart_probe_model_import_prohibited")
        if event == "open" and isinstance(values[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(values[0])).resolve()
            mode, flags = values[1], values[2]
            write = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)))
            if ((write and run not in path.parents)
                    or path.suffix.lower() in {".ipynb", ".csv", ".xlsx", ".parquet", ".arff"}
                    or any(part in path.as_posix().lower() for part in ("/experiments/data/", "/experiments/results/", "/datasets-raw/", "/vera_validation/results/"))):
                blocked.append("file_scope")
                raise RuntimeError("counterpart_probe_research_io_prohibited")
    sys.addaudithook(audit)
    from ml import preprocessing as local_pre
    from ml.se_brl.extraction import RuleEngine as LocalEngine
    from ml.se_brl.review_adapter import email_request_from_view, analyze_evidence
    from ml.se_brl.semantic_review import validate_review
    from ml.se_brl.review_adapter import record_from_request
    from ml.se_brl.runtime_compatibility import runtime_declaration, compare_runtime_declaration
    # Isolate genuine modules; do not stub dependencies or substitute local code.
    local_modules = {k: v for k, v in sys.modules.items() if k == "ml" or k.startswith("ml.")}
    for key in local_modules:
        del sys.modules[key]
    package = ModuleType("ml")
    package.__path__ = [str(mirror / "ml")]
    sys.modules["ml"] = package
    try:
        peer_pre = importlib.import_module("ml.preprocessing")
        peer_inputs = importlib.import_module("ml.experiment_inputs")
        peer_integration = importlib.import_module("ml.experiment_integration")
        peer_extraction = importlib.import_module("ml.se_brl.extraction")
        peer_datasets = importlib.import_module("ml.datasets")
        peer_codebook = importlib.import_module("ml.se_brl.codebook")
        assert all(mirror in Path(module.__file__).resolve().parents for module in
                   (peer_pre, peer_inputs, peer_integration, peer_extraction, peer_datasets, peer_codebook))
    finally:
        for key in list(sys.modules):
            if key == "ml" or key.startswith("ml."):
                del sys.modules[key]
        sys.modules.update(local_modules)
    checks = []
    def check(name, condition):
        if not condition:
            raise AssertionError("counterpart_contract_probe_failed:" + name)
        checks.append({"name": name, "status": "PASS"})
    def outcome(preprocessor, raw):
        try:
            return {"artifact": asdict(preprocessor.preprocess(raw))}
        except (ValueError, AssertionError) as exc:
            return {"error_type": type(exc).__name__}
    def observations(engine, prepared):
        extraction = engine.extract(prepared)
        return [{"id": r.indicator_id, "state": r.evidence_state, "evaluation_status": r.evaluation_status,
                 "evidence": [(e.span.field, e.span.start, e.span.end, e.span.text, e.provenance) for e in r.evidence]}
                for r in extraction.indicators]
    check("published_view_exact_fields", [f.name for f in fields(peer_integration.EmailEvidenceInput)] == ["subject", "body", "sender", "links"])
    for text in (" ＶＥＲＩＦＹ &amp; pay\nNOW ", "Straße\tK", "A\u0301 &lt;B&gt;"):
        check("normalization_order_" + str(len(checks)), local_pre.normalize_text(text) == peer_pre.normalize_text(text))
    cases = {
        "metadata_only": {"kind": "email", "subject": "Act now!"},
        "missing_text": {"kind": "email"},
        "known_empty": {"kind": "email", "subject": ""},
        "unicode_original_offsets": {"kind": "email", "subject": "🙂 Ａ Act now!"},
        "quoted_body": {"kind": "email", "body": "> Act now!\nOrdinary notice.", "body_collection_authorized": True, "study_purpose": "software contract test"},
        "unauthorized_body": {"kind": "email", "body": "Act now!"},
        "unauthorized_links": {"kind": "email", "urls": ["https://example.invalid/"]},
        "authorized_links": {"kind": "email", "subject": "See https://example.invalid/", "link_extraction_authorized": True},
        "credential_url": {"kind": "url", "url": "https://name:password@example.invalid/"},
        "ordinary_html": {"kind": "webpage", "html": "<p>Act now!</p><script>Pay this fee.</script>"},
        "warning_context": {"kind": "email", "subject": "Phishing warning: never submit your password."},
        "isolation_directive": {"kind": "email", "subject": "Do not contact your bank."},
    }
    for name, raw in cases.items():
        a, b = outcome(local_pre, raw), outcome(peer_pre, raw)
        check("preprocessing_" + name, a == b)
        if "artifact" in a:
            check("deterministic_observations_" + name,
                  observations(LocalEngine(), local_pre.preprocess(raw)) == observations(peer_extraction.RuleEngine(), peer_pre.preprocess(raw)))
    malformed = {"kind": "webpage", "html": "<![CDATA[hidden]]><p>Act now.</p>"}
    local_result, peer_result = outcome(local_pre, malformed), outcome(peer_pre, malformed)
    check("equal_version_actual_parser_divergence", local_pre.PREPROCESSING_VERSION == peer_pre.PREPROCESSING_VERSION
          and local_result == {"error_type": "ArtifactParserError"} and "artifact" in peer_result)
    bridge_options = dict(artifact_id="software-probe:1", source_id="software-probe", source_reference="software-only",
                          language="en")
    for name, text, links, expected_fields in (
        ("unknown", None, None, {}), ("known_empty", "", (), {"subject": "", "urls": []}),
        ("metadata_subject", "Act now!", None, {"subject": "Act now!"})):
        view = peer_integration.EmailEvidenceInput(peer_inputs.TextField(text), peer_inputs.TextField(), peer_inputs.TextField(), peer_inputs.LinkField(links))
        request = email_request_from_view(view, **bridge_options)
        check("actual_peer_view_bridge_" + name, request["fields"] == expected_fields)
        response = analyze_evidence(request)
        validate_review(response, record_from_request(request))
        check("actual_peer_view_validated_response_" + name, response["schema_version"] == "1.0.0")
    for name, view, options in (
        ("body_without_consent", peer_integration.EmailEvidenceInput(peer_inputs.TextField(), peer_inputs.TextField("Act now!"), peer_inputs.TextField(), peer_inputs.LinkField()), {}),
        ("links_without_opt_in", peer_integration.EmailEvidenceInput(peer_inputs.TextField(), peer_inputs.TextField(), peer_inputs.TextField(), peer_inputs.LinkField(("https://example.invalid/",))), {}),
        ("unsupported_language", peer_integration.EmailEvidenceInput(peer_inputs.TextField("Act now!"), peer_inputs.TextField(), peer_inputs.TextField(), peer_inputs.LinkField()), {"language": "es"}),
    ):
        try:
            email_request_from_view(view, **{**bridge_options, **options})
        except ValueError:
            check("actual_peer_view_rejects_" + name, True)
        else:
            raise AssertionError("unsafe_bridge_request_accepted:" + name)
    authorized = peer_integration.EmailEvidenceInput(peer_inputs.TextField("Notice"), peer_inputs.TextField("Submit your password."), peer_inputs.TextField(), peer_inputs.LinkField(("https://example.invalid/",)))
    request = email_request_from_view(authorized, **bridge_options, body_collection_authorized=True,
                                      link_extraction_authorized=True, study_purpose="software contract test")
    response = analyze_evidence(request)
    from ml.datasets import prepare_record
    deterministic = {row.indicator_id: row.evidence_state for row in LocalEngine().extract(prepare_record(record_from_request(request)).artifact).indicators}
    check("actual_peer_authorized_input_preserves_deterministic_observations",
          {row["indicator_id"]: row["deterministic_state"] for row in response["indicators"]} == deterministic)
    # Run actual counterpart join/gate with explicitly synthetic in-memory rows.
    identity = peer_inputs.DatasetIdentity("software-probe", "no-corpus", "software-only")
    label = peer_datasets.PhishingLabel
    rows = tuple(peer_inputs.EmailObservation(f"probe:{i}", f"native:{i}", identity, language, i % 2,
                 label.LEGITIMATE if i % 2 == 0 else label.PHISHING, "software-only",
                 peer_inputs.TextField("Act now!"), peer_inputs.TextField())
                 for i, language in enumerate(("en", "es", "und", "en", "en")))
    assignments = tuple(peer_inputs.PartitionAssignment(r.observation_id, f"group:{i}", partition, 1 if partition == "development" else None)
                        for i, (r, partition) in enumerate(zip(rows, ("development", "development", "development", "calibration", "test"))))
    options = dict(identity=identity, expected_total=5, expected_targets={label.LEGITIMATE: 3, label.PHISHING: 2})
    try:
        email_request_from_view(rows[0], **bridge_options)
    except ValueError:
        check("actual_peer_full_observation_rejected_at_evidence_bridge", True)
    else:
        raise AssertionError("full_observation_accepted")
    calls = []
    def callback(view):
        calls.append(view)
        return analyze_evidence(email_request_from_view(view, **bridge_options))
    result = peer_integration.evaluate_development_lexical(rows, tuple(reversed(assignments)), evaluate=callback, **options)
    check("actual_peer_join_language_partition_gate", [r.observation_id for r in result] == [r.observation_id for r in rows[:3]]
          and [r.evaluation.status for r in result] == ["evaluated", "unavailable", "unavailable"] and len(calls) == 1)
    arbitrary = peer_integration.evaluate_development_lexical(rows, assignments, evaluate=lambda _: {"invalid_behavioral_output": True}, **options)
    check("actual_peer_does_not_validate_callback_output", arbitrary[0].evaluation.result == {"invalid_behavioral_output": True})
    for name, selected in (("missing_id", assignments[:-1]), ("duplicate_id", assignments + (assignments[0],))):
        calls.clear()
        try:
            peer_integration.evaluate_development_lexical(rows, selected, evaluate=callback, **options)
        except peer_inputs.InputContractError:
            check("actual_peer_rejects_" + name + "_before_callback", calls == [])
        else:
            raise AssertionError("invalid_join_accepted")
    pending = compare_runtime_declaration(runtime_declaration(), None)
    check("missing_declaration_remains_pending", pending["status"] == "PENDING_COUNTERPART_DECLARATION" and pending["integration_accepted"] is False)
    from ml.se_brl.codebook import load_codebook
    check("actual_codebook_content_match", dict(load_codebook()) == dict(peer_codebook.load_codebook()))
    static = {}
    for name in ("ml/preprocessing.py", "ml/se_brl/context.py", "ml/se_brl/rules.py", "ml/se_brl/extraction.py", "ml/se_brl/detectors.py"):
        left, right = (ROOT / name).read_text(), (mirror / name).read_text()
        static[name] = {"local_utf8_sha256": hashlib.sha256(left.encode()).hexdigest(),
                        "peer_utf8_sha256": hashlib.sha256(right.encode()).hexdigest(),
                        "ast_equal": ast.dump(ast.parse(left)) == ast.dump(ast.parse(right))}
    check("no_prohibited_operations", not blocked)
    output = {"status": "PASS_COMPONENT_PROBES_ONLY", "counterpart_commit": manifest["commit"],
              "verified_actual_source_files": verified, "checks": checks, "passed_checks": len(checks),
              "source_comparison": static,
              "parser_divergence": {"version_equal": True, "local": local_result, "peer": "accepts_CDATA_declaration"},
              "blocked_operations": blocked, "runtime_comparison": pending,
              "inputs": "explicitly_synthetic_software_cases_no_research_rows",
              "cross_repository_compatibility_proven": False, "formal_acceptance_obtained": False,
              "R22": "BLOCKED", "research_release": False}
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
