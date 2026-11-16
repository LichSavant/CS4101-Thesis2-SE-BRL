"""Run only selected no-fit counterpart suites, with offline IO tripwires."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
VERA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VERA))
from ml.counterpart_checkout import verify_source_manifest
from r22_execution_environment import execution_environment, runtime_source_hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counterpart-root", type=Path, required=True)
    parser.add_argument("--suite", choices=("contract", "preprocessing"), default="contract")
    args = parser.parse_args()
    vera_before = runtime_source_hashes(VERA)
    root = args.counterpart_root.resolve()
    manifest = json.loads((VERA / "docs/r22-parser-repair-2026-11-16/counterpart-source-manifest.json").read_text())
    before = verify_source_manifest(root, manifest)
    run = Path(tempfile.mkdtemp(prefix="sebrl-r22-counterpart-tests-")).resolve()
    os.environ.update(PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", HF_HUB_OFFLINE="1",
                      TRANSFORMERS_OFFLINE="1", DATABASE_URL="sqlite:///:memory:", TMPDIR=str(run), TEMP=str(run), TMP=str(run))
    tempfile.tempdir = str(run)
    blocked = []
    def audit(event, values):
        if event in {"socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system"}:
            blocked.append(event); raise RuntimeError("r22_external_execution_prohibited")
        if event == "import" and values[0].split(".")[0] in {"torch", "transformers", "sklearn", "xgboost"}:
            blocked.append("model_import"); raise RuntimeError("r22_real_model_import_prohibited")
        if event == "sqlite3.connect" and values[0] != ":memory:":
            blocked.append("persistent_database"); raise RuntimeError("r22_persistent_database_prohibited")
        if event == "open" and isinstance(values[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(values[0])).resolve()
            mode, flags = values[1], values[2]
            write = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)))
            if ((write and path != run and run not in path.parents) or path.suffix in {".ipynb", ".xlsx", ".arff", ".parquet"}
                    or (path.suffix == ".csv" and run not in path.parents)
                    or any(part in path.as_posix().lower() for part in ("/datasets-raw/", "/experiments/data/", "/experiments/results/"))):
                blocked.append("file_scope"); raise RuntimeError("r22_research_or_write_scope_violation")
    sys.addaudithook(audit)
    for name in list(sys.modules):
        if name == "ml" or name.startswith("ml.") or name == "backend" or name.startswith("backend."):
            del sys.modules[name]
    sys.path.insert(0, str(root))
    os.chdir(root)
    import pytest
    class Evidence:
        def __init__(self): self.selected = []; self.deselected = []
        def pytest_collection_finish(self, session): self.selected = [item.nodeid for item in session.items]
        def pytest_deselected(self, items): self.deselected.extend(item.nodeid for item in items)
    evidence = Evidence()
    suites = ["ml/tests/" + n for n in (
        "test_behavioral_compatibility.py", "test_experiment_inputs.py", "test_experiment_integration.py",
        "test_preprocessing.py", "test_rule_extraction.py", "test_context_detectors.py", "test_result_envelope.py",
        "test_deterministic_representation.py")]
    suites += ["backend/tests/" + n for n in ("test_sebrl_contract.py", "test_sebrl_pipeline.py", "test_sebrl_service.py")]
    if args.suite == "preprocessing": suites = ["ml/tests/test_preprocessing.py"]
    arguments = [*suites, "-q", "-p", "no:cacheprovider", "-o", "log_file=" + str(run / "pytest.log"),
                 "--basetemp=" + str(run / "fixtures"), "--junitxml=" + str(run / "regression.xml")]
    code = int(pytest.main(arguments, plugins=[evidence]))
    counts = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
    for suite in ET.parse(run / "regression.xml").getroot().iter("testsuite"):
        for key in counts: counts[key] += int(suite.get(key, "0"))
    after = verify_source_manifest(root, manifest)
    summary = {"scope": "actual_selected_counterpart_no_fit_suites", "suite": args.suite, "execution_environment": execution_environment(), "commit": manifest["commit"],
        "pytest_exit_code": code, "pytest_arguments": arguments, "test_counts": counts,
        "passed": counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"],
        "selected_node_ids": evidence.selected, "deselected_node_ids": evidence.deselected,
        "blocked_operations": blocked, "vera_source_files_sha256": vera_before, "vera_sources_unchanged": vera_before == runtime_source_hashes(VERA), "verified_source_files": len(before), "sources_unchanged": before == after,
        "real_model_inference": False, "fitting": False, "research_release": False, "joint_acceptance": False,
        "not_selected": "All other suites, including existing model-bundle inference, classifier/fitting, experiments and corpus operations."}
    (run / "verification.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("VERIFICATION_RECORD", run / "verification.json")
    return code or int(bool(blocked) or before != after or not summary["vera_sources_unchanged"])


if __name__ == "__main__":
    raise SystemExit(main())
