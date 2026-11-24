"""Read-only metadata preflight. Run: python -B -m ml.preflight --root .

No network, notebook execution, dataframe/model imports, output files, or output
directories. Raw CSVs are inspected for headers only; processed files may be
hashed opaquely. Historical row-level prediction files are never opened.
"""

from __future__ import annotations

import argparse
import ast
import csv
from dataclasses import asdict, dataclass
import hashlib
from importlib import metadata
import io
import json
from pathlib import Path
import re
import sys
from typing import Callable

REPORT_VERSION = "0.1.0"
RESEARCH_GATE_VERSION = "email-research-admission-0.1.0"
# These are evidence obligations, never caller-supplied approval switches.
EMAIL_RESEARCH_REQUIREMENTS = (
    ("population", "Approved Email population", "Dated population/CEAS role and exact eligible ID-universe acceptance"),
    ("source_labels", "Verified source and label semantics", "Source snapshot/access/license records and source-backed native class definitions"),
    ("identity", "Accepted identity and lineage", "Authenticated record lineage, or an accepted prospective identity/ingestion protocol"),
    ("assignments", "Accepted grouping and partitions", "Accepted relationship policy and versioned supplied group/role/fold manifest; exposure disposition"),
    ("custody", "Authorized development custody", "Named hashed development-only delivery and access authorization"),
    ("behavior", "Approved deterministic feature definitions", "Accepted twelve-rule/language/locator/availability specification and conformance evidence"),
    ("dictionaries", "Approved matched E1/E2/E3 dictionaries", "Ordered typed predictors, forbidden-field controls and matched population/fold validation"),
    ("evaluation", "Approved candidate and evaluation settings", "Predeclared ranges/budgets/nesting/seeds/score/calibration/selection settings"),
    ("leakage", "Verified research leakage safeguards", "Accepted-data duplicate/group/target/source/preprocessing isolation evidence, beyond synthetic checks"),
    ("reproducibility", "Configured research reproducibility outputs", "Accepted run/code/environment/input/model provenance and exclusive complete research-output plan"),
)


def research_fit_gate(verified_run=None) -> dict:
    """Current Email admission gate; no filesystem reads or approval inference.

    A verified context comes only from the trusted operator's scoped artifact
    verifier. No argument remains closed and performs no data discovery.
    """
    if verified_run is not None:
        require_research_fitting(verified_run)
        return {"gate_version": RESEARCH_GATE_VERSION, "scope": "exact accepted development run",
                "status": "PASS", "research_fitting_enabled": True,
                "scientific_authorization_verified": True, "authorization_sha256": verified_run.authorization_sha256,
                "final_evaluation_authorized": False}
    return {"gate_version": RESEARCH_GATE_VERSION, "scope": "accepted development research fitting",
            "status": "FAIL", "research_fitting_enabled": False,
            "scientific_authorization_verified": False,
            "reason": "accepted_exact_run_evidence_not_supplied",
            "checks": [{"id": key, "requirement": title, "status": "FAIL",
                        "required_evidence": evidence, "reason": "accepted_branch_evidence_not_verified"}
                       for key, title, evidence in EMAIL_RESEARCH_REQUIREMENTS],
            "synthetic_success_authorizes_research": False,
            "reference_strings_authorize_research": False}


def require_research_fitting(verified_run=None) -> None:
    """Typed verified context required; never accepts an approved=True flag."""
    from ml.experiment_inputs import InputContractError
    from ml.research_protocol import VerifiedResearchRun
    from ml.fixed_baseline import VerifiedFixedBaseline
    from ml.comparison_batch import VerifiedComparison
    if isinstance(verified_run, VerifiedComparison):
        verified_run.require_verified()
        return
    if isinstance(verified_run, VerifiedFixedBaseline):
        verified_run.require_verified()
        return
    if not isinstance(verified_run, VerifiedResearchRun):
        raise InputContractError("research_fitting_not_authorized")
    verified_run.require_verified()


BASE = "experiments/"
INPUT_NAMES = {
    "email": ("email_preprocessed.csv", "email_sebrl_features.csv"),
    "phiusiil": ("phiusiil_preprocessed.csv", "phiusiil_sebrl_features.csv"),
    "iscx": ("iscx_url2016_preprocessed.csv", "iscx_sebrl_features.csv"),
    "uci": ("uci_phishing_websites_preprocessed.csv", "uci_sebrl_features.csv"),
}
RAW_INPUTS = (
    ("email/ceas_08/CEAS_08.csv", ("subject", "body", "label")),
    ("email/enron/Enron.csv", ("subject", "body", "label")),
    ("email/nazario/Nazario.csv", ("subject", "body", "label")),
    ("email/spamassasin/SpamAssasin.csv", ("subject", "body", "label")),
    ("webpage/PhiUSIL/PhiUSIIL_Phishing_URL_Dataset.csv", ("URL", "Domain", "Title", "label")),
    ("webpage/uci/phishing+websites/Training Dataset.arff", ("Result",)),
    ("url/iscx-url-2016/All.csv", ("URL_Type_obf_Type",)),
    ("url/iscx-url-2016/Phishing.csv", ("URL_Type_obf_Type",)),
)
CLEAN_NAMES = (
    "email/ceas_08_clean.csv", "email/enron_clean.csv", "email/nazario_clean.csv",
    "email/spamassassin_clean.csv", "webpage/phiusiil_clean.csv",
    "webpage/uci_phishing_websites_clean.csv", "url/iscx_url2016_all_clean.csv",
    "url/iscx_url2016_phishing_clean.csv",
)
NOTEBOOKS = ("01_data_audit", "02_data_cleaning", "03_preprocessing", "04_feature_extraction", "05_experiments")


def _safe_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("path_outside_checkout")
    return candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_input(root: Path, relative: str, required: tuple[str, ...] = ()) -> dict[str, object]:
    """Bounded header inspection. Does not read CSV rows or ARFF @data values."""
    result: dict[str, object] = {"path": relative, "required_fields": list(required)}
    # This inspector is for inputs, never arbitrary historical test predictions.
    if "holdout" in relative.casefold() or "prediction" in relative.casefold():
        return {**result, "status": "forbidden_prediction_path"}
    try:
        path = _safe_path(root, relative)
        if not path.is_file():
            return {**result, "status": "missing"}
        with path.open("rb") as stream:
            prefix = stream.read(256)
        if prefix.startswith(b"version https://git-lfs.github.com/spec/v1"):
            oid = re.search(rb"oid sha256:([a-f0-9]{64})", prefix)
            size = re.search(rb"(?:\n|\r)size (\d+)", prefix)
            return {**result, "status": "lfs_pointer", "oid_sha256": oid[1].decode() if oid else None,
                    "declared_payload_bytes": int(size[1]) if size else None}
        with path.open(encoding="utf-8-sig", newline="") as stream:
            if path.suffix.casefold() == ".arff":
                fields = []
                for _ in range(512):
                    line = stream.readline(65537)
                    if len(line) > 65536:
                        raise ValueError("header_limit")
                    if line.lstrip().casefold().startswith("@data"):
                        break
                    match = re.match(r"\s*@attribute\s+(?:'([^']+)'|\"([^\"]+)\"|(\S+))", line, re.I)
                    if match:
                        fields.append(next(v for v in match.groups() if v is not None))
                    if not line:
                        raise ValueError("missing_arff_data_boundary")
                else:
                    raise ValueError("header_limit")
            else:
                line = stream.readline(65537)
                if not line or len(line) > 65536:
                    raise ValueError("header_limit")
                fields = next(csv.reader(io.StringIO(line), strict=True))
        if (not fields or len(fields) > 512 or len(set(fields)) != len(fields)
                or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_ .()/-]{0,127}", f) for f in fields)):
            raise ValueError("invalid_header")
        missing = sorted(set(required) - set(fields))
        return {**result, "status": "incompatible_schema" if missing else "header_compatible",
                "schema": fields, "missing_required_fields": missing,
                "schema_only": True, "row_validity": "not_inspected"}
    except (OSError, UnicodeError, ValueError, csv.Error):
        # Do not echo parser errors, source lines, filenames supplied in data, or rows.
        return {**result, "status": "unreadable_or_invalid_metadata"}


@dataclass(frozen=True, slots=True)
class Issue:
    code: str
    stage: str
    detail: str
    path: str | None = None
    cell_id: str | None = None
    blocking: bool = True


def _is_column(node: ast.AST, frame: str, column: str) -> bool:
    return (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
            and node.value.id == frame and isinstance(node.slice, ast.Constant) and node.slice.value == column)


def _read_notebooks(root: Path, issues: list[Issue]) -> tuple[list[dict], list[dict], set[str]]:
    reports = []
    assumptions = []
    email_identities = set()
    for name in NOTEBOOKS:
        stage = name[:2]
        relative = f"{BASE}notebooks/{name}.ipynb"
        report = {"stage": stage, "path": relative, "syntax": "valid", "stored_exceptions": []}
        try:
            notebook = json.loads(_safe_path(root, relative).read_text(encoding="utf-8"))
            cells = notebook["cells"]
            if not isinstance(cells, list):
                raise ValueError("invalid_cells")
            report["cells"] = len(cells)
            for position, cell in enumerate(cells, 1):
                if cell.get("cell_type") != "code":
                    continue
                cell_id = cell.get("id")
                source = "".join(cell["source"])
                try:
                    tree = ast.parse(source)
                except SyntaxError as error:
                    report["syntax"] = "invalid"
                    issues.append(Issue("notebook_syntax_error", stage, f"Code cell {position}, source line {error.lineno} does not parse.", relative, cell_id))
                    continue
                for output in cell.get("outputs", []):
                    if output.get("output_type") == "error":
                        report["stored_exceptions"].append({"cell": position, "cell_id": cell_id})
                for node in ast.walk(tree):
                    if (stage == "03" and isinstance(node, ast.Raise)
                            and isinstance(node.exc, ast.Call) and node.exc.args
                            and isinstance(node.exc.args[0], ast.Constant)
                            and isinstance(node.exc.args[0].value, str)
                            and node.exc.args[0].value.startswith("primary_email_benchmark_not_selected")):
                        issues.append(Issue("primary_email_benchmark_not_selected", "03",
                                            "No primary email benchmark has been selected; historical results are not a replacement approval.",
                                            relative, cell_id))
                    if isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare):
                        test = node.test
                        if (len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)
                                and isinstance(test.left, ast.Call) and isinstance(test.left.func, ast.Name)
                                and test.left.func.id == "len" and len(test.left.args) == 1
                                and isinstance(test.left.args[0], ast.Name)
                                and test.left.args[0].id in {"email_binary", "email_dev"}
                                and isinstance(test.comparators[0], ast.Constant)
                                and type(test.comparators[0].value) is int):
                            assumptions.append({"frame": test.left.args[0].id, "rows": test.comparators[0].value,
                                                "path": relative, "cell_id": cell_id, "cell": position})
                    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and type(node.value.value) is str:
                        if any(_is_column(target, "email_binary", "source_dataset") for target in node.targets):
                            email_identities.add(node.value.value)
                    if stage == "04" and _is_column(node, "email_features", "urls"):
                        marker = ("requires_email_urls", cell_id)
                        if not any((x.code, x.cell_id) == marker for x in issues):
                            issues.append(Issue(marker[0], "04", "Direct urls access requires a supplied field; missing links cannot be invented as negative evidence.", relative, cell_id))
            if report["stored_exceptions"]:
                issues.append(Issue("stored_execution_errors", stage, "Historical exceptions are retained; this is not a fresh-run failure diagnosis.", relative, blocking=False))
        except (OSError, UnicodeError, ValueError, KeyError, TypeError):
            report["syntax"] = "unavailable"
            issues.append(Issue("notebook_unavailable", stage, "Notebook metadata could not be inspected.", relative))
        reports.append(report)
    for frame in ("email_binary", "email_dev"):
        if len({a["rows"] for a in assumptions if a["frame"] == frame}) > 1:
            issues.append(Issue("conflicting_population_assumptions", "03", f"Different row-count assertions remain for {frame}; no count was adopted or changed."))
    totals = [a["rows"] for a in assumptions if a["frame"] == "email_binary"]
    development = [a["rows"] for a in assumptions if a["frame"] == "email_dev"]
    if totals and development and max(development) > min(totals):
        issues.append(Issue("development_population_conflict", "03", "A development-size assertion exceeds a total-population assertion; no partition was changed."))
    return reports, assumptions, email_identities


def _historical_email_summary(root: Path, issues: list[Issue]) -> dict:
    relative = f"{BASE}results/preprocessing/partitions/email_partition_manifest.csv"
    try:
        counts: dict[str, int] = {}
        total = 0
        with _safe_path(root, relative).open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not {"source_dataset", "partition", "target", "group_id", "cv_fold", "observation_id"}.issubset(reader.fieldnames or ()):
                raise ValueError("invalid_manifest_schema")
            for row in reader:
                source = row["source_dataset"]
                if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", source):
                    raise ValueError("invalid_dataset_identifier")
                counts[source] = counts.get(source, 0) + 1
                total += 1
        return {"path": relative, "rows": total, "source_counts": counts,
                "scope": "supplied_historical_partition_metadata_only"}
    except (OSError, UnicodeError, ValueError, csv.Error, KeyError, TypeError):
        issues.append(Issue("historical_manifest_unavailable", "03", "Historical population identity cannot be reconciled from the manifest.", relative))
        return {"path": relative, "status": "unavailable"}


def check_environment(recorded: dict, lookup: Callable[[str], str] = metadata.version) -> list[dict]:
    result = []
    for package, field in (("numpy", "numpy_version"), ("pandas", "pandas_version"),
                           ("scikit-learn", "scikit_learn_version"), ("scipy", "scipy_version"),
                           ("matplotlib", "matplotlib_version")):
        expected = recorded.get(field)
        try:
            current = lookup(package)
        except metadata.PackageNotFoundError:
            current = None
        result.append({"package": package, "installed": current, "recorded": expected,
                       "status": "missing" if current is None else (
                           "recorded_version_mismatch" if expected is not None and expected != current else "available"),
                       "compatibility": "not_established"})
    return result


def run_preflight(root: Path, *, version_lookup: Callable[[str], str] = metadata.version) -> dict:
    root = root.resolve()
    issues: list[Issue] = []
    inputs = []
    for name, required in RAW_INPUTS:
        inputs.append({**inspect_input(root, BASE + "datasets-raw/" + name, required), "stage": "01", "role": "historical_source"})
    for name in CLEAN_NAMES:
        inputs.append({**inspect_input(root, BASE + "data/interim/" + name), "stage": "03", "role": "historical_cleaned"})
    for item in inputs:
        if item["status"] != "header_compatible":
            issues.append(Issue("input_" + item["status"], item["stage"], "Input unavailable or header incompatible; payload rows were not inspected.", item["path"]))
    notebooks, assumptions, identities = _read_notebooks(root, issues)
    historical = _historical_email_summary(root, issues)
    if identities and set(historical.get("source_counts", {})) != identities:
        issues.append(Issue("dataset_identity_conflict", "03", "Notebook email source assignment differs from the historical partition manifest."))
    if any(a["frame"] == "email_binary" and a["rows"] != historical.get("rows") for a in assumptions) and "rows" in historical:
        issues.append(Issue("recorded_population_conflict", "03", "Notebook population assertion differs from the historical manifest."))

    manifest_path = BASE + "results/experiments/experiment_manifest.json"
    try:
        recorded = json.loads(_safe_path(root, manifest_path).read_text(encoding="utf-8"))
        if not isinstance(recorded, dict):
            raise ValueError("invalid_manifest")
    except (OSError, UnicodeError, ValueError):
        recorded = {}
        issues.append(Issue("experiment_manifest_unavailable", "05", "Recorded experiment/environment metadata is unavailable.", manifest_path))
    environment = check_environment(recorded, version_lookup)
    if sys.version_info < (3, 11):
        issues.append(Issue("runtime_python_incompatible", "environment", "Runtime ml/ requires Python 3.11+; the historical notebook interpreter is a separate environment record."))
    for package in environment:
        if package["status"] == "missing":
            issues.append(Issue("dependency_missing", "environment", f"Required notebook distribution is missing: {package['package']}."))
        elif package["status"] == "recorded_version_mismatch":
            issues.append(Issue("environment_differs_from_historical", "environment", f"Installed {package['package']} differs from the recorded historical version; compatibility/replay is not established."))

    expected_hashes: dict[tuple[str, str], str] = {}
    relative = BASE + "results/experiments/input_manifest.csv"
    try:
        with _safe_path(root, relative).open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                dataset, kind = row["dataset"], row["input_type"]
                index = {"preprocessed": 0, "behavioral": 1}.get(kind)
                if (dataset not in INPUT_NAMES or index is None or row["filename"] != INPUT_NAMES[dataset][index]
                        or not re.fullmatch(r"[a-f0-9]{64}", row["sha256"]) or (dataset, kind) in expected_hashes):
                    raise ValueError("invalid_input_manifest")
                expected_hashes[dataset, kind] = row["sha256"]
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, csv.Error):
        expected_hashes = {}
        issues.append(Issue("input_manifest_invalid_or_missing", "05", "Only allowlisted processed-input names are accepted; no arbitrary manifest path is opened.", relative))
    for dataset, names in INPUT_NAMES.items():
        for index, kind in enumerate(("preprocessed", "behavioral")):
            directory = "data/processed/preprocessed/" if index == 0 else "data/processed/features/sebrl/"
            path = BASE + directory + names[index]
            item = {**inspect_input(root, path, ("observation_id", "target", "group_id", "partition", "cv_fold")),
                    "stage": "04" if index == 0 else "05", "role": kind, "dataset": dataset}
            expected = expected_hashes.get((dataset, kind))
            item["recorded_sha256"] = expected
            if item["status"] == "header_compatible":
                try:
                    item["actual_sha256"] = _sha256(_safe_path(root, path))
                    item["hash_status"] = "match" if item["actual_sha256"] == expected else ("mismatch" if expected else "unrecorded")
                except OSError:
                    item["hash_status"] = "unreadable"
                if item["hash_status"] != "match":
                    issues.append(Issue("processed_hash_" + item["hash_status"], item["stage"], "Processed input identity does not match a recorded snapshot.", path))
            else:
                issues.append(Issue("processed_" + item["status"], item["stage"], "Processed input unavailable/incompatible; no regeneration attempted.", path))
            inputs.append(item)
    issues.extend((
        Issue("protocol_authorization_not_established", "research", "This tool cannot approve H1-H12, dataset eligibility, language/rule semantics, grouping or research execution."),
        Issue("behavioral_contract_unresolved", "04", "Runtime/notebook rule, locator and availability conformance is not frozen together. Legacy runtime learned-z slots do not replace the approved deterministic classifier representation."),
    ))
    if any(_safe_path(root, BASE + "results/experiments/" + name).is_file()
           for name in ("holdout_test_metrics.csv", "holdout_predictions.csv")):
        issues.append(Issue("historical_holdout_already_exposed", "05", "Historical holdout artifacts are present; no prediction rows were opened. New selection requires an accepted evaluation-integrity plan."))
    else:
        issues.append(Issue("sealed_evaluation_plan_unresolved", "05", "No accepted evaluation-integrity plan has been established by this metadata check."))
    stages = []
    inherited: list[str] = []
    for stage in ("01", "02", "03", "04", "05"):
        direct = [x.code for x in issues if x.blocking and x.stage in {stage, "environment", "research"}]
        if stage == "02":
            direct.extend(x.code for x in issues if x.blocking and x.stage == "01")
        blockers = sorted(set(inherited + direct))
        stages.append({"stage": stage, "can_run": not blockers, "blockers": blockers,
                       "meaning": "metadata_prerequisites_only_not_execution_authorization"})
        inherited = blockers
    optional_dependencies = []
    for package in ("xgboost", "pytest"):
        try:
            version = version_lookup(package)
        except metadata.PackageNotFoundError:
            version = None
        optional_dependencies.append({"package": package, "installed": version,
                                      "role": "genuine_offline_candidate; research_execution_not_authorized" if package == "xgboost" else "synthetic_test_runner",
                                      "required_for_preflight": False})
    return {"report_version": REPORT_VERSION, "scope": "read_only_metadata_preparation_not_scientific_validation",
            "research_execution_authorized": False, "real_data_fit_gate": research_fit_gate(),
            "python": {"current": sys.version.split()[0], "historical": recorded.get("python_version")},
            "inputs": inputs, "notebooks": notebooks, "population_assumptions": assumptions,
            "historical_email": historical, "environment": environment, "optional_dependencies": optional_dependencies,
            "issues": [asdict(issue) for issue in issues], "stages": stages,
            "synthetic_contract_checks": "available_without_scientific_stack; run pytest separately"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Existing checkout; never created or modified")
    parser.add_argument("--research-gate-only", action="store_true",
                        help="Report current closed Email research admission without opening corpus/metadata files")
    args = parser.parse_args()
    if args.research_gate_only:
        print(json.dumps(research_fit_gate(), indent=2, ensure_ascii=True))
        return 2
    report = run_preflight(args.root)
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 2 if any(issue["blocking"] for issue in report["issues"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
