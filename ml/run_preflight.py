"""No-fit budget/alignment reports. No engine calls or research-source discovery."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

from ml.development_experiments import development_folds, _within
from ml.experiment_inputs import InputContractError
from ml.metadata import fingerprint
from ml.research_protocol import fit_estimate, specification_record


def verified_run_report(root, context, dataset, specification):
    """Recheck exact admitted scope/alignment before even an inert engine seam."""
    from ml.development_runner import dataset_fingerprint
    context.require_verified()
    if (str(Path(root).resolve()) != context._state.get("checkout_root")
            or dataset.specification.dataset != context.branch
            or dataset_fingerprint(dataset) != context.input_fingerprint
            or fingerprint(specification_record(specification)) != context.specification_fingerprint
            or set(context.sources_by_id) != {r.observation_id for r in dataset.observations}
            or context._state.get("readback_only") or context._state.get("bound")):
        raise InputContractError("preflight_run_identity_or_scope_changed")
    output = _within(Path(root), 'experiments/runs/'+context.output_run_id)
    if output.exists():
        raise InputContractError("preflight_output_collision")
    alignment, dictionaries = {}, {}
    indexed = {r.observation_id:r for r in dataset.observations}
    for configuration in specification.configurations:
        plans = development_folds(dataset, configuration)
        names = plans[0].feature_names
        omissions = set(specification.omitted_features)
        if not omissions <= set(names) or set(names) <= omissions:
            raise InputContractError("preflight_invalid_omissions")
        dictionaries[configuration] = [n for n in names if n not in omissions]
        from ml.classifier_adapters import FoldClassifier
        for candidate in specification.candidates:
            FoldClassifier(dataset.specification,candidate.model,candidate.preprocessing,configuration)
            if any(c.kind=='text' and c.name in dictionaries[configuration] for c in dataset.specification.conventional) and candidate.preprocessing.text_parameters is None:
                raise InputContractError('preflight_text_parameters_required')
        for plan in plans:
            for position,column in enumerate(dataset.specification.conventional):
                if column.name in dictionaries[configuration] and column.kind=='numeric' and all(indexed[i].conventional[position] is None for i in plan.training_ids):
                    raise InputContractError('preflight_training_column_entirely_missing')
        alignment[configuration] = fingerprint([
            (p.validation_fold, p.training_ids, p.validation_ids,
             tuple((i,indexed[i].target,indexed[i].group_id,indexed[i].fold,context.sources_by_id[i])
                   for i in (*p.training_ids,*p.validation_ids))) for p in plans])
    if len(set(alignment.values())) != 1:
        raise InputContractError("preflight_matched_representation_required")
    estimate = fit_estimate(specification)
    if estimate != dict(context.expected_fits):
        raise InputContractError("preflight_fit_estimate_changed")
    return {'category':'VERIFIED DRY RUN; NO FITTING', 'execution_scope':context._state['boundary'],
        'authorization_sha256':context.authorization_sha256, 'input_sha256':context.input_fingerprint,
        'configuration_sha256':context.specification_fingerprint, 'configurations':list(specification.configurations),
        'code_map_sha256':fingerprint(context.code_sha256),
        'environment_sha256':context._state['environment_sha256'],
        'source_population_sha256':context._state['source_population_sha256'],
        'source_audit_sha256':context._state['source_audit_sha256'],
        'family':specification.candidates[0].model.family, 'candidates':len(specification.candidates),
        'outer_folds':5, 'inner_folds':4, 'calibration_retuning':True,
        'expected_fits':estimate, 'omitted_features':list(specification.omitted_features),
        'alignment_sha256':alignment, 'feature_dictionaries':dictionaries,
        'development_rows':len(indexed), 'reserved_predictors_accessed':False,
        'output_directory':str(output), 'output_collision':False, 'accepted_resources':dict(context.budget),
        'measured_runtime_seconds':None,'estimated_storage_bytes':None,
        'unknown_costs':['row-dependent fitting time','sparse vocabulary/matrix memory','serialized model storage','bootstrap and diagnostic overhead'],
        'model_fits':0,'final_evaluation_authorized':False}


def candidate_budget_report(root):
    """Read only candidate JSON; never turn a proposed grid into authorization."""
    path = Path(root)/'ml/research_settings_candidate.v0.1.0.json'
    body = path.read_bytes(); candidate = json.loads(body); settings = candidate['experiment']
    mode = settings['threshold']['mode']
    if mode not in {'fixed','training_crossfit_f1'}:
        raise InputContractError('unsupported_candidate_threshold_budget')
    families = {}
    for family in ('logistic_regression','linear_svm','random_forest','xgboost'):
        axes = settings[family]['axes']
        if not axes or any(type(v) is not list or not v for v in axes.values()):
            raise InputContractError('nonempty_candidate_axes_required')
        combinations = list(itertools.product(*axes.values()))
        if len({fingerprint(c) for c in combinations}) != len(combinations):
            raise InputContractError('duplicate_candidate_grid_entries')
        count = math.prod(len(v) for v in axes.values())
        # Delegate to exactly the estimator used by accepted-run admission.
        from types import SimpleNamespace
        estimate = fit_estimate(SimpleNamespace(candidates=(None,)*count,
            configurations=('budget-only',),threshold=SimpleNamespace(mode=mode)))
        families[family] = {'candidates':count,'axis_sizes':{k:len(v) for k,v in axes.items()},'per_configuration':estimate}
    branches={'Email':['E1','E2','E3'],'Web':['E1','E2','E3'],'PhiUSIIL':['U1'],'UCI':['U1']}
    configurations=sum(map(len,branches.values()))
    base=sum(v['per_configuration']['base_fits'] for v in families.values())*configurations
    calibration=sum(v['per_configuration']['calibration_fits'] for v in families.values())*configurations
    return {'category':'CANDIDATE BUDGET; NOT APPROVAL','settings_sha256':hashlib.sha256(body).hexdigest(),
        'candidate_status':candidate['status'],'families':families,'family_count':len(families),'branches':branches,
        'outer_folds':5,'inner_folds':4,'expected_fits':{'base_fits':base,'calibration_fits':calibration},
        'recorded_estimate_matches':base==settings['full_principal_matrix_base_fits'] and calibration==settings['full_principal_matrix_calibrator_fits'],
        'diagnostics_and_ablations':'excluded; separately authorized exact specifications required',
        'output_directory':None,'output_collision':None,'runtime_seconds':None,'storage_bytes':None,
        'resource_measurement':'unknown until accepted population and bounded timing evidence; no fitting performed',
        'research_execution_authorized':False,'model_fits':0}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True)
    args=parser.parse_args(argv)
    try: result=candidate_budget_report(args.root)
    except (KeyError,TypeError,ValueError,InputContractError):
        print(json.dumps({'status':'BLOCKED','model_fits':0}));return 2
    print(json.dumps(result,sort_keys=True));return 0


if __name__=='__main__':
    raise SystemExit(main())
