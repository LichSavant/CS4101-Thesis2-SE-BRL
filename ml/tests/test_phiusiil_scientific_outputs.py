"""No-fit tests of descriptive definitions and exact candidate specifications."""
from pathlib import Path
import json

import pytest

from scripts.phiusiil_scientific_outputs import quality, configuration
from ml.experiment_inputs import InputContractError
from ml.research_protocol import parse_specification
from scripts.phiusiil_development_delivery import FEATURES


def test_missingness_nonfinite_and_predeclared_statistics_are_distinct():
    result=quality([0,2,None,float('inf')],[0,1,0,1])
    assert result['missing']==1 and result['nonfinite_nonmissing']==1
    assert result['finite']==2 and result['mean']==1 and result['std_population']==1
    assert result['median']==1 and result['unique_finite']==2
    assert not result['exact_target_copy'] and not result['constant']


def test_obvious_target_shortcut_and_near_constant_are_diagnostics_only():
    assert quality([0,1],[0,1])['exact_target_copy']
    assert quality([1,0],[0,1])['exact_target_complement']
    result=quality([0]*99+[1],[0]*50+[1]*50)
    assert result['near_constant_99pct'] and not result['constant']


def test_full_existing_candidate_grids_validate_without_fitting():
    root=Path(__file__).resolve().parents[2]
    settings=json.loads((root/'ml/research_settings_candidate.v0.1.0.json').read_bytes())
    dictionary={'dataset':'PhiUSIIL','conventional':[{'name':name,'kind':'numeric'} for name in FEATURES]}
    result=configuration(settings,dictionary)
    assert result['status']=='CANDIDATE - NOT FITTING AUTHORIZATION'
    assert [p['candidate_count'] for p in result['plans']]==[8,8,72,64]
    assert len(result['technical_ablations'])==2
    for plan in (*result['plans'],*result['technical_ablations']):
        spec=parse_specification(plan['runner_specification'])
        assert spec.configurations==('U1',) and spec.candidates[0].model.seed==42
    assert result['model_fits']==0 and result['predictive_results'] is None


def test_forbidden_metadata_cannot_become_a_candidate_predictor():
    with pytest.raises(InputContractError):
        configuration({}, {'dataset':'PhiUSIIL','conventional':[{'name':'FILENAME','kind':'numeric'}]})
