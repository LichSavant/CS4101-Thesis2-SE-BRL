"""Scoped C-allocation/D-feature commands; no model-fitting prerequisites.

Only an independently authenticated researcher's dated exact-scope receipt opens
these stages. No approved=True flag, original-source discovery or test predictors.
Receipts record an existing human decision; this command never creates approval.
"""
import argparse
import csv
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import re

from ml.branch_preparation import export_selected_handoff, prepare_selected_branches
from ml.content_preparation import extract_content_handoff
from ml.development_experiments import DevelopmentSpecification, FeatureColumn, METADATA, behavioral_columns, build_development_dataset
from ml.experiment_inputs import InputContractError
from ml.metadata import canonical_json
from ml.prospective_allocation import connected_groups, allocate, export_allocation
from ml.research_protocol import _read, _json, code_hashes
from ml.preparation_integrity import (validate_prospective_population, validate_population_assignments,
    validate_preparation_sources, validate_development_locators)
from ml.execution_identity import execution_identity, write_integrity_receipt
from ml.development_experiments import _within

VERSION = "scoped-no-fit-preparation-1"
PAYLOAD = {"Email": "email_records.json", "Web": "web_records.json", "UCI": "uci_records.json", "PhiUSIIL": "phiusiil_records.json"}


def _completion(root, output, receipt, authorization_sha256):
    identity = execution_identity(root, code_sha256=receipt["code_sha256"],
        settings_sha256=hashlib.sha256(canonical_json(receipt["input_sha256"]).encode()).hexdigest())
    return write_integrity_receipt(output, identity=identity,
        input_sha256={**receipt["input_sha256"], "external_authorization_receipt":authorization_sha256},
        category="no_fit_preparation")


def _assignments(body):
    rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig")), strict=True))
    for row in rows:
        if set(row) != {*METADATA, "source_dataset"} or row["target"] not in {"0", "1"} or not re.fullmatch(r"[1-5]?", row["cv_fold"]):
            raise InputContractError("strict_supplied_assignment_schema_required")
        row["target"] = int(row["target"])
        row["cv_fold"] = int(row["cv_fold"]) if row["cv_fold"] else None
    return rows


def run_preparation(root, input_run_id, *, stage, expected_authorization_sha256):
    if stage not in {"C-allocation", "D-features"} or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", input_run_id):
        raise InputContractError("explicit_preparation_stage_required")
    root = Path(root).resolve()
    run = _within(root, "experiments/runs/"+input_run_id)
    receipt_path = _within(run, "protocol/"+("allocation_acceptance.json" if stage == "C-allocation" else "feature_acceptance.json"))
    receipt = _json(_read(receipt_path, expected_authorization_sha256, 1_000_000))
    try:
        authority = receipt["authority"]
        output_run_id, branch = receipt["output_run_id"], receipt["branch"]
        if (set(receipt) != {"version", "stage", "authority", "branch", "output_run_id", "input_sha256", "code_sha256", "access"}
                or receipt["version"] != VERSION or receipt["stage"] != stage or branch not in PAYLOAD
                or set(authority) != {"name", "role", "date", "response_reference", "response_text"}
                or any(type(v) is not str or not v.strip() for v in authority.values())
                or authority["role"] not in {"researcher", "adviser"} or date.fromisoformat(authority["date"]) > date.today()
                or len(authority["response_text"]) < 40
                or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", output_run_id)
                or output_run_id == input_run_id):
            raise InputContractError("dated_exact_no_fit_acceptance_required")
        output = _within(root, "experiments/runs/"+output_run_id)
        if output.exists():
            raise InputContractError("unused_preparation_output_required")
        code = code_hashes(root)
        if not code or code != code_hashes(Path(__file__).resolve().parents[1]) or receipt["code_sha256"] != code:
            raise InputContractError("accepted_preparation_code_changed")
        names = ({"protocol/population.json", "protocol/relationships.json", "protocol/allocation_settings.json"} if stage == "C-allocation" else
                 {"protocol/population.json", "protocol/assignments.csv", "protocol/dictionary.json", "protocol/feature_freeze.json", "data/development/"+PAYLOAD[branch]})
        if set(receipt["input_sha256"]) != names:
            raise InputContractError("exact_scoped_preparation_inputs_required")
        content = {name: _read(_within(run, name), receipt["input_sha256"][name], 100_000_000) for name in names}
        population = _json(content["protocol/population.json"])
        records = population["records"]
        validate_prospective_population(records)
        validate_preparation_sources(records, branch)
        ids = frozenset(r["observation_id"] for r in records)
        if len(ids) != len(records) or not records:
            raise InputContractError("unique_accepted_population_required")
        if stage == "C-allocation":
            relationships = _json(content["protocol/relationships.json"])
            settings = _json(content["protocol/allocation_settings.json"])
            if (set(settings) != {"fractions", "seed", "maximum_fraction_error", "policy_reference"}
                    or not relationships["policy_reference"] == settings["policy_reference"]
                    or set(relationships["coverage"]) != {"exact_duplicate", "near_duplicate", "template", "campaign", "domain"}
                    or any(v not in {"source_verified", "unavailable_with_accepted_limitation"} for v in relationships["coverage"].values())):
                raise InputContractError("explicit_relationship_coverage_and_allocation_policy_required")
            groups = connected_groups(tuple(r["observation_id"] for r in records), tuple(relationships["edges"]), policy_reference=settings["policy_reference"])
            assigned, report = allocate({r["observation_id"]: r["target"] for r in records}, groups,
                fractions=tuple(settings["fractions"]), seed=settings["seed"], maximum_fraction_error=settings["maximum_fraction_error"],
                policy_reference=settings["policy_reference"])
            digest = export_allocation(output, assigned, report, targets_by_id={r["observation_id"]:r["target"] for r in records},
                sources_by_id={r["observation_id"]:r["source_dataset"] for r in records})
            completion = _completion(root, output, receipt, expected_authorization_sha256)
            return {"status": "accepted_metadata_allocated", "stage": stage, "output_run_id": output_run_id,
                    "allocation_manifest_sha256": digest, "observations": len(assigned), "model_fits": 0,
                    "completion_integrity_sha256":completion}
        assignments = _assignments(content["protocol/assignments.csv"])
        validate_population_assignments(records, assignments)
        dictionary = _json(content["protocol/dictionary.json"])
        specification = DevelopmentSpecification(dictionary["dataset"], tuple(FeatureColumn(c["name"],c["kind"]) for c in dictionary["conventional"]),
            dictionary["protocol_reference"],dictionary["feature_dictionary_reference"])
        if specification.dataset != branch:
            raise InputContractError("preparation_branch_dictionary_mismatch")
        freeze = _json(content["protocol/feature_freeze.json"])
        if (freeze["code_sha256"] != code or freeze["assignment_sha256"] != receipt["input_sha256"]["protocol/assignments.csv"]
                or freeze["dictionary_sha256"] != receipt["input_sha256"]["protocol/dictionary.json"]
                or freeze["data_scope"] != "development_only"):
            raise InputContractError("exact_accepted_feature_freeze_required")
        rows = _json(content["data/development/"+PAYLOAD[branch]])
        validate_development_locators(records, rows, branch)
        if branch in {"Email", "Web"}:
            access = receipt["access"]
            main, vectors, evidence, summary = extract_content_handoff(rows, assignment_manifest=assignments,
                expected_observation_ids=ids, specification=specification,
                body_access_authorized=access["body"], link_access_authorized=access["links"], study_purpose=access["purpose"])
            # Shared writer's existing evidence path. No raw message snippets.
            stream = io.StringIO(newline="")
            writer = csv.DictWriter(stream, fieldnames=("observation_id","indicator_id","state","evaluation_status","locators_json"))
            writer.writeheader()
            writer.writerows({"observation_id":e["observation_id"],"indicator_id":i["id"],"state":i["state"],
                "evaluation_status":i["status"],"locators_json":canonical_json(i["locators"])} for e in evidence for i in e["indicators"])
            paths = export_selected_handoff(output,(branch,),{branch:main},{branch:vectors},
                shared_outputs={"results/feature_extraction/evidence/indicator_evidence.csv":stream.getvalue().encode()})
        elif branch == "UCI":
            from ml.uci_preparation import prepare_uci_handoff
            paths = prepare_uci_handoff(root,output_run_id,rows,assignment_manifest=assignments,
                expected_observation_ids=ids,specification=specification)
        else:
            # Existing technical dispatcher supplies unavailable behavioral bits.
            # Validate assignments/population with the same strict U1 checks by
            # source metadata, not by positional zipping or regenerated splits.
            from ml.notebook_contracts import validate_feature_boundary
            validate_feature_boundary(rows,dataset="PhiUSIIL",development_only=True)
            index = {a["observation_id"]:a for a in assignments}
            if len(index)!=len(assignments) or set(index)!=ids:
                raise InputContractError("exact_assignment_population_required")
            from ml.experiment_inputs import PartitionAssignment, validate_supplied_partitions
            counts = validate_supplied_partitions(tuple(PartitionAssignment(a["observation_id"],a["group_id"],a["partition"],a["cv_fold"]) for a in assignments))
            if not all(counts.values()):
                raise InputContractError("three_partition_roles_required")
            if any({a["target"] for a in assignments if a["partition"] == role} != {0, 1} for role in counts):
                raise InputContractError("two_class_partition_required")
            if ({r["observation_id"] for r in rows}!={i for i,a in index.items() if a["partition"]=="development"}
                    or any(any(r[k]!=index[r["observation_id"]][k] for k in (*METADATA,"source_dataset")) for r in rows)):
                raise InputContractError("development_assignment_metadata_changed")
            prepared=prepare_selected_branches({branch:rows},(branch,))[branch]
            vectors=tuple({k:r[k] for k in (*METADATA,*behavioral_columns())} for r in prepared)
            build_development_dataset(rows,vectors,specification=specification)
            paths=export_selected_handoff(output,(branch,),{branch:rows},{branch:vectors})
        completion = _completion(root, output, receipt, expected_authorization_sha256)
        return {"status":"accepted_no_fit_handoff_created","stage":stage,"branch":branch,"output_run_id":output_run_id,
            "completion_integrity_sha256":completion,
            "output_files":len(paths),"model_fits":0,"development_manifest_sha256":hashlib.sha256(paths[-1].read_bytes()).hexdigest()}
    except InputContractError:
        raise
    except Exception:
        raise InputContractError("no_fit_preparation_evidence_or_input_invalid") from None


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",required=True);p.add_argument("--input-run-id",required=True)
    p.add_argument("--stage",required=True,choices=("C-allocation","D-features"))
    p.add_argument("--authorization-sha256",required=True)
    args=p.parse_args(argv)
    try: result=run_preparation(args.root,args.input_run_id,stage=args.stage,expected_authorization_sha256=args.authorization_sha256)
    except InputContractError as error:
        print(json.dumps({"status":"BLOCKED","code":str(error),"model_fits":0}));return 2
    print(json.dumps(result));return 0


if __name__=="__main__":
    raise SystemExit(main())
