"""Run exactly the actual joint cases under the existing no-fit/network guard."""
from pathlib import Path
import argparse
import json
import os
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r22_execution_environment import execution_environment, runtime_source_hashes

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counterpart-root", type=Path, required=True)
    parser.add_argument("--suite", choices=("joint", "parser", "safeguards"), default="joint")
    args = parser.parse_args()
    vera_before = runtime_source_hashes(ROOT)
    os.environ.update(PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", SEBRL_R22_COUNTERPART_ROOT=str(args.counterpart_root.resolve()))
    import pytest
    original = pytest.main
    captured = {}
    def joint_scope(arguments, plugins):
        suffix = arguments[arguments.index("-q"):]
        suffix = suffix[:suffix.index("-k")]
        suites = {"joint": ["ml/tests/test_joint_integration.py"],
                  "parser": ["ml/tests/test_joint_parser_repair.py"],
                  "safeguards": ["ml/tests/test_counterpart_sources.py", "ml/tests/test_runtime_compatibility.py",
                      "ml/tests/test_review_adapter.py", "ml/tests/test_finalization_policy.py",
                      "ml/tests/test_finalization_preflight.py"]}
        effective = [*suites[args.suite], *suffix]
        captured["arguments"] = effective
        captured["run"] = Path(next(v.split("=",1)[1] for v in effective if v.startswith("--basetemp="))).parent
        return original(effective, plugins=plugins)
    pytest.main = joint_scope
    try:
        import verify_semantic_review
        code = verify_semantic_review.main()
    finally:
        pytest.main = original
    record = captured["run"] / "verification.json"
    document = json.loads(record.read_text())
    document["guard_harness_original_arguments"] = document.pop("pytest_arguments")
    document["pytest_arguments"] = captured["arguments"]
    document["execution_environment"] = execution_environment()
    document["counterpart_root"] = str(args.counterpart_root.resolve())
    document["verification_kind"] = "actual_pinned_cross_runtime_synthetic_engineering"
    document["vera_source_files_sha256"] = vera_before
    document["vera_sources_unchanged"] = vera_before == runtime_source_hashes(ROOT)
    record.write_text(json.dumps(document,indent=2)+"\n")
    return code or int(not document["vera_sources_unchanged"])

if __name__ == "__main__": raise SystemExit(main())
