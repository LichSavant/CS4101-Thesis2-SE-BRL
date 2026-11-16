"""Run the bounded synthetic suite with research-data/network/import tripwires.

This is a regression harness, not a sandbox for hostile code. It does not run
notebooks, fit models, read corpora, or initialize real inference dependencies.
All test writes and JUnit output are confined to a fresh temporary directory.
"""
from pathlib import Path
import json
import os
import sys
import tempfile
import xml.etree.ElementTree as ET


def main():
    root = Path(__file__).resolve().parents[1]
    run = Path(tempfile.mkdtemp(prefix="sebrl-semantic-synthetic-")).resolve()
    sys.dont_write_bytecode = True
    os.environ.update(PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
                      HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", DATABASE_URL="sqlite:///:memory:",
                      TMPDIR=str(run), TEMP=str(run), TMP=str(run))
    tempfile.tempdir = str(run)
    sys.path.insert(0, str(root))
    os.chdir(root)
    blocked = []

    def within_run(path):
        return path == run or run in path.parents

    def audit(event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system"}:
            blocked.append(event)
            raise RuntimeError("synthetic_suite_network_or_subprocess_prohibited")
        if event == "import" and args[0].split(".")[0] in {"torch", "transformers", "sklearn", "xgboost"}:
            if args[0].split(".")[0] not in sys.modules:
                blocked.append("real_model_dependency_import")
                raise RuntimeError("synthetic_suite_real_model_dependency_prohibited")
        if event == "sqlite3.connect" and args[0] != ":memory:":
            path = Path(os.fsdecode(args[0])).resolve()
            if not within_run(path):
                blocked.append("database_outside_temporary_run")
                raise RuntimeError("synthetic_suite_database_scope_violation")
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            name = path.as_posix().lower()
            mode, flags = args[1], args[2]
            write = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)))
            if write and not within_run(path):
                blocked.append("write_outside_temporary_run")
                raise RuntimeError("synthetic_suite_write_scope_violation")
            if (path.suffix in {".ipynb", ".xlsx", ".parquet", ".arff", ".gzip"}
                    or any(part in name for part in ("/datasets-raw/", "/experiments/data/", "/experiments/results/",
                                                     "/vera_validation/results/", "/vera_validation/archive/"))
                    or (path.suffix == ".csv" and not within_run(path))):
                blocked.append("research_input_access")
                raise RuntimeError("synthetic_suite_research_input_prohibited")

    sys.addaudithook(audit)
    import pytest
    class Evidence:
        def __init__(self):
            self.selected = []
            self.deselected = []
        def pytest_deselected(self, items):
            self.deselected.extend(item.nodeid for item in items)
        def pytest_collection_finish(self, session):
            self.selected = [item.nodeid for item in session.items]
    evidence = Evidence()
    legacy = ["V13D_test_extractor.py", "V13E_test_policy.py", "V13F_test_ablation.py", "V15_test_autonomous_inference.py",
              "V16_test_controller.py", "V16_test_evidence_constraints.py", "V17_test_contextual_constraints.py",
              "V17_test_semantic_controller.py", "V20_test_integrity_gate.py", "V21_test_semantic_candidates.py"]
    excluded = ["test_tfidf_fit_transform_training_only", "test_tfidf_smoothed_idf_and_normalization",
                "test_empty_vocabulary_is_not_fake_data", "test_fitted_e1_reaches_missing_model_boundary_e2_e3_stay_blocked",
                "test_fitted_tfidf_signature_is_deterministic_and_changes_with_training_input"]
    protected_cases = ["experiments/vera_validation/V13F_test_ablation.py::TestAblation::" + name
                       for name in ("test_v10_all_rows", "test_v11_all_pairs", "test_semantic_does_not_override", "test_schema")]
    args = ["ml/tests", "backend/tests", *["experiments/vera_validation/" + name for name in legacy], "-q", "-p", "no:cacheprovider",
            "-o", "log_file=" + str(run / "pytest.log"),
            "--basetemp=" + str(run / "fixtures"), "--junitxml=" + str(run / "regression.xml"),
            "-k", " and ".join("not " + name for name in excluded),
            *[value for node in protected_cases for value in ("--deselect", node)]]
    code = int(pytest.main(args, plugins=[evidence]))
    counts = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    if (run / "regression.xml").is_file():
        for suite in ET.parse(run / "regression.xml").getroot().iter("testsuite"):
            for key in counts:
                counts[key] += int(suite.get(key, "0"))
    summary = {"verification_kind": "synthetic_engineering_only", "pytest_exit_code": code,
               "blocked_operations": blocked, "network_and_real_dependency_tripwires": True,
               "research_inputs_and_notebooks_prohibited": True, "all_test_writes_confined_to": str(run),
               "real_model_inference": False, "actual_data_fitting": False,
               "independent_human_validation": False, "human_annotation_study_simulated": False,
               "software_schema_fixtures_only": True, "pytest_arguments": args,
               "test_counts": {**counts, "passed": counts["tests"]-counts["failures"]-counts["errors"]-counts["skipped"]},
               "selected_node_ids": evidence.selected, "deselected_node_ids": evidence.deselected}
    (run / "verification.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("VERIFICATION_RECORD", run / "verification.json")
    return code or (1 if blocked else 0)


if __name__ == "__main__":
    raise SystemExit(main())
