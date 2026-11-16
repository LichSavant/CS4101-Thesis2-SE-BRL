"""Internal bounded-worker entry point; no defaults, source discovery or approval."""
import hashlib
import json
from pathlib import Path
import sys

from ml.experiment_inputs import InputContractError
from ml.research_protocol import verify_accepted_run
from ml.source_controls import _execute_verified_controls


def run_worker(request):
    contexts, controls, specifications = {}, {}, []
    if set(request) != {"root", "output_directory", "receipt", "controls"}:
        raise InputContractError("exact_diagnostic_worker_request_required")
    for name, entry in request["controls"].items():
        context, dataset, specification = verify_accepted_run(request["root"], entry["input_run_id"],
            expected_authorization_sha256=entry["authorization_sha256"], purpose="diagnostic")
        contexts[name], controls[name] = context, dataset
        specifications.append(specification)
    if not specifications or any(s != specifications[0] for s in specifications):
        raise InputContractError("matched_diagnostic_settings_required")
    _execute_verified_controls(controls, request["receipt"], specification=specifications[0],
        contexts=contexts, output_directory=request["output_directory"])
    return {"completion_sha256": hashlib.sha256((Path(request["output_directory"])/"diagnostic_completion.json").read_bytes()).hexdigest()}


def main():
    try:
        body = sys.stdin.read(1_000_001)
        if len(body) > 1_000_000:
            raise InputContractError("diagnostic_request_oversized")
        result = run_worker(json.loads(body))
    except (InputContractError, ValueError, KeyError, TypeError):
        print(json.dumps({"status":"diagnostic_worker_failed"})); return 2
    print(json.dumps(result)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
