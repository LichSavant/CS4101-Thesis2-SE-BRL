from pathlib import Path
import hashlib
import json

import pytest

from ml.development_experiments import load_development_dataset
from ml.experiment_inputs import InputContractError
from ml.metadata import canonical_json
from ml.preparation_execution import run_preparation, VERSION
from ml.research_protocol import code_hashes, prospective_id
from ml.tests.test_research_protocol import fixture_packet


def packet(root):
    protocol, receipt, _, run_id, dataset, _ = fixture_packet(root)
    population=json.loads((protocol/"population.json").read_bytes())
    byid={r["observation_id"]:r for r in population["records"]}
    rows=[]
    for r in dataset.observations:
        p=byid[r.observation_id]
        rows.append(dict(observation_id=r.observation_id,source_dataset=p["source_dataset"],source_row_id=p["source_row_id"],
            target=r.target,Result=p["native_label"],group_id=r.group_id,partition="development",cv_fold=r.fold,
            **dict(zip(("URL_Length","Redirect"),r.conventional))))
    data=protocol.parent/"data/development";data.mkdir()
    (data/"uci_records.json").write_text(canonical_json(rows))
    names=("protocol/population.json","protocol/assignments.csv","protocol/dictionary.json","protocol/feature_freeze.json","data/development/uci_records.json")
    preparation={"version":VERSION,"stage":"D-features","authority":receipt["authority"],"branch":"UCI",
        "output_run_id":"synthetic-feature-output","input_sha256":{n:hashlib.sha256((protocol.parent/n).read_bytes()).hexdigest() for n in names},
        "code_sha256":code_hashes(root),"access":{"body":False,"links":False,"purpose":"Synthetic supplied technical input"}}
    path=protocol/"feature_acceptance.json";path.write_text(canonical_json(preparation))
    return protocol,preparation,hashlib.sha256(path.read_bytes()).hexdigest(),run_id, dataset


def test_no_fit_feature_stage_does_not_require_training_settings(tmp_path):
    protocol,receipt,digest,run_id,dataset=packet(tmp_path)
    # These fixture-only files are removed solely to prove stage independence.
    for name in ("acceptance.json","experiment.json","selection.json","environment.json"):
        (protocol/name).unlink()
    summary=run_preparation(tmp_path,run_id,stage="D-features",expected_authorization_sha256=digest)
    assert summary["model_fits"]==0 and summary["output_files"]==3
    loaded=load_development_dataset(tmp_path,"synthetic-feature-output",specification=dataset.specification)
    assert loaded.observations==dataset.observations
    with pytest.raises(InputContractError,match="unused"):
        run_preparation(tmp_path,run_id,stage="D-features",expected_authorization_sha256=digest)


@pytest.mark.parametrize("change",("hash","scope","code","reserved"))
def test_no_fit_invalid_scope_or_reserved_delivery_creates_no_output(tmp_path,change):
    protocol,receipt,digest,run_id,_=packet(tmp_path)
    if change=="hash":digest="0"*64
    elif change=="scope":receipt["stage"]="E-fit"
    elif change=="code":receipt["code_sha256"]={}
    elif change=="reserved":
        path=protocol.parent/"data/development/uci_records.json"
        rows=json.loads(path.read_bytes());rows[0]["partition"]="test";path.write_text(canonical_json(rows))
        receipt["input_sha256"]["data/development/uci_records.json"]=hashlib.sha256(path.read_bytes()).hexdigest()
    if change!="hash":
        path=protocol/"feature_acceptance.json";path.write_text(canonical_json(receipt));digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(InputContractError):
        run_preparation(tmp_path,run_id,stage="D-features",expected_authorization_sha256=digest)
    assert not (protocol.parent.parent/"synthetic-feature-output").exists()


def test_allocation_stage_is_metadata_only_and_independent_of_fitting(tmp_path):
    protocol,old,_,run_id,_=packet(tmp_path)
    records=[];edges=[]
    for i in range(30):
        pair=[]
        for target in (0,1):
            oid=prospective_id("UCI Phishing Websites","e"*64,"fixture.arff",2*i+target)
            pair.append(oid);records.append({"observation_id":oid,"source_dataset":"UCI Phishing Websites","target":target,
                "snapshot_sha256":"e"*64,"source_file":"fixture.arff","source_row_id":2*i+target,
                "native_label":-1 if target else 1})
        edges.append(dict(left=pair[0],right=pair[1],kind="exact_duplicate",evidence_reference="synthetic:equivalent-key"))
    (protocol/"population.json").write_text(canonical_json({"records":records}))
    (protocol/"relationships.json").write_text(canonical_json({"policy_reference":"synthetic:accepted-option","edges":edges,
        "coverage":{k:"source_verified" if k=="exact_duplicate" else "unavailable_with_accepted_limitation" for k in ("exact_duplicate","near_duplicate","template","campaign","domain")}}))
    (protocol/"allocation_settings.json").write_text(canonical_json({"fractions":[.7,.15,.15],"seed":42,"maximum_fraction_error":.08,"policy_reference":"synthetic:accepted-option"}))
    names=("protocol/population.json","protocol/relationships.json","protocol/allocation_settings.json")
    receipt={**old,"stage":"C-allocation","output_run_id":"synthetic-allocation-output",
        "input_sha256":{n:hashlib.sha256((protocol.parent/n).read_bytes()).hexdigest() for n in names}}
    path=protocol/"allocation_acceptance.json";path.write_text(canonical_json(receipt))
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    result=run_preparation(tmp_path,run_id,stage="C-allocation",expected_authorization_sha256=digest)
    assert result["model_fits"]==0 and result["observations"]==60
    output=protocol.parent.parent/"synthetic-allocation-output"
    assert {p.name for p in output.iterdir()}=={"assignments.csv","allocation_report.json","allocation_manifest.json","completion_integrity.json"}


@pytest.mark.parametrize("field", ("target", "source_dataset"))
@pytest.mark.parametrize("partition", ("development", "calibration", "test"))
def test_assignment_facts_must_match_population_even_when_rehashed(tmp_path, field, partition):
    import csv
    import io
    protocol, receipt, _, run_id, _ = packet(tmp_path)
    path = protocol/"assignments.csv"
    rows = list(csv.DictReader(io.StringIO(path.read_text())))
    row = next(r for r in rows if r["partition"] == partition)
    row[field] = str(1-int(row[field])) if field == "target" else "different source"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]))
    writer.writeheader(); writer.writerows(rows)
    path.write_text(stream.getvalue(), newline="")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt["input_sha256"]["protocol/assignments.csv"] = digest
    freeze_path = protocol/"feature_freeze.json"
    freeze = json.loads(freeze_path.read_bytes())
    freeze["assignment_sha256"] = digest
    freeze_path.write_text(canonical_json(freeze))
    receipt["input_sha256"]["protocol/feature_freeze.json"] = hashlib.sha256(freeze_path.read_bytes()).hexdigest()
    acceptance = protocol/"feature_acceptance.json"
    acceptance.write_text(canonical_json(receipt))
    with pytest.raises(InputContractError, match="assignment_source_or_target_differs_from_population"):
        run_preparation(tmp_path, run_id, stage="D-features",
            expected_authorization_sha256=hashlib.sha256(acceptance.read_bytes()).hexdigest())
    assert not (protocol.parent.parent/receipt["output_run_id"]).exists()


@pytest.mark.parametrize("field,value", (("source_row_id", 999999), ("Result", 0), ("snapshot_sha256", "f"*64)))
def test_rehashed_payload_cannot_change_original_population_locator(tmp_path, field, value):
    protocol, receipt, _, run_id, _ = packet(tmp_path)
    relative = "data/development/uci_records.json"
    path = protocol.parent/relative
    rows = json.loads(path.read_bytes())
    rows[0][field] = value
    path.write_text(canonical_json(rows))
    receipt["input_sha256"][relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    acceptance = protocol/"feature_acceptance.json"
    acceptance.write_text(canonical_json(receipt))
    with pytest.raises(InputContractError, match="development_.*changed"):
        run_preparation(tmp_path, run_id, stage="D-features",
            expected_authorization_sha256=hashlib.sha256(acceptance.read_bytes()).hexdigest())
    assert not (protocol.parent.parent/receipt["output_run_id"]).exists()
