"""No-fit matched source-control preparation and rejection checks."""
from dataclasses import replace
import pytest

from ml.development_experiments import build_development_dataset, development_folds
from ml.experiment_inputs import InputContractError
from ml.source_controls import prepare_source_controls, execute_source_controls
from ml.tests.test_development_experiments import fixture_rows, spec
from ml.tests.test_experiment_engine import spec as experiment_spec
from ml.tests.test_research_protocol import fixture_packet
from ml.research_protocol import verify_accepted_run
from ml.metadata import canonical_json
import hashlib


def fixture():
    rows,vectors=fixture_rows()
    dataset=build_development_dataset(rows,vectors,specification=spec())
    normalized=replace(dataset,observations=tuple(replace(r,conventional=("normalized fixture",r.conventional[1])) for r in dataset.observations))
    return dataset, normalized, {r["observation_id"]:r["source_dataset"] for r in rows}


def test_matched_source_control_is_separate_deterministic_and_fold_local():
    original,normalized,sources=fixture()
    controls,receipt=prepare_source_controls(original,normalized,sources_by_id=sources,normalization_reference="synthetic:policy-only")
    again,other=prepare_source_controls(replace(original,observations=original.observations[::-1]),normalized,
        sources_by_id=sources,normalization_reference="synthetic:policy-only")
    assert receipt==other and controls==again
    assert receipt["model_fits"]==0 and not receipt["source_independent_performance_established"]
    assert controls["source_only"].specification.conventional[0].name=="diagnostic_source_token"
    for name,dataset in controls.items():
        for a,b in zip(development_folds(controls["baseline"],"E1"),development_folds(dataset,"E1")):
            assert (a.training_ids,a.validation_ids,a.y_train,a.y_validation)==(b.training_ids,b.validation_ids,b.y_train,b.y_validation)
    assert all(r.behavioral==(0,)*8 for r in controls["source_only"].observations)
    assert all("diagnostic_source_token" not in p.feature_names for p in development_folds(controls["baseline"],"E1"))


@pytest.mark.parametrize("change", ["population","target","group","fold","availability","sources","protocol"])
def test_invalid_matched_controls_rejected(change):
    original,normalized,sources=fixture();reference="synthetic:policy"
    first=normalized.observations[0]
    if change=="population":normalized=replace(normalized,observations=normalized.observations[:-1])
    elif change=="sources":sources.pop(first.observation_id)
    elif change=="protocol":reference=""
    else:
        values={"target":{"target":1-first.target},"group":{"group_id":"changed"},"fold":{"fold":2},
            "availability":{"behavioral":(0,)*8}}[change]
        normalized=replace(normalized,observations=(replace(first,**values),)+normalized.observations[1:])
    with pytest.raises(InputContractError):
        prepare_source_controls(original,normalized,sources_by_id=sources,normalization_reference=reference)


def test_execution_requires_three_exact_authorizations_before_any_output(tmp_path):
    original,normalized,sources=fixture()
    controls,receipt=prepare_source_controls(original,normalized,sources_by_id=sources,normalization_reference="synthetic:policy")
    with pytest.raises(InputContractError,match="authorization"):
        execute_source_controls(controls,receipt,specification=experiment_spec(configs=("E1",)),
            contexts={n:{"approved":True} for n in controls},output_directory=tmp_path/"must-not-exist")
    assert not (tmp_path/"must-not-exist").exists()


def test_diagnostic_authority_cannot_be_reused_for_principal_fitting(tmp_path):
    protocol,receipt,_,run_id,_,_=fixture_packet(tmp_path)
    receipt["boundary"]="E-development-diagnostic-only"
    path=protocol/"acceptance.json";path.write_text(canonical_json(receipt))
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(InputContractError):
        verify_accepted_run(tmp_path,run_id,expected_authorization_sha256=digest)
    with pytest.raises(InputContractError,match="content_branch"):
        verify_accepted_run(tmp_path,run_id,expected_authorization_sha256=digest,purpose="diagnostic")
