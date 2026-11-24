"""SE-BRL fixed-configuration exploratory PhiUSIIL ablations.

Preparation never trains. Execution requires an independently recorded, attributable
researcher acceptance of the exact generated request SHA-256. This is NOT the
original nested/calibrated ablation design or formal implementation selection.

Put this file at scripts/phiusiil_fixed_ablation.py in the existing worktree.
Usage: python -B -m scripts.phiusiil_fixed_ablation --prepare
       python -B -m scripts.phiusiil_fixed_ablation --execute
"""
import argparse
import csv
from datetime import date
import hashlib
import json
from pathlib import Path
import statistics
import time

from ml.classifier_adapters import ClassifierSpecification, PreprocessingSpecification, FoldClassifier
from ml.comparison_batch import (
    REQUEST as COMPARISON_REQUEST, REQUEST_SHA256 as COMPARISON_SHA,
    OUTPUT as COMPARISON_OUTPUT, digest, compact_metrics,
    verify_authorization as verify_original_comparison,
    completed_model,
)
from ml.development_experiments import (
    DevelopmentSpecification, DevelopmentObservation, DevelopmentDataset,
    development_folds,
)
from ml.development_runner import dataset_fingerprint
from ml.evaluation_metrics import binary_metrics
from ml.experiment_inputs import InputContractError
from ml.metadata import fingerprint

ROOT = Path(__file__).resolve().parents[1]
REQUEST = 'docs/research/2026-11-19_phiusiil_fixed_ablation_request.json'
AUTH = 'docs/research/2026-11-19_phiusiil_fixed_ablation_authorization.json'
PROTOCOL = 'docs/research/2026-11-19_phiusiil_fixed_ablation_protocol.md'
OUTPUT = 'experiments/runs/phiusiil-fixed-rf-ablations-v1'
ABLATIONS = {
    'omit_obfuscation': ('HasObfuscation', 'NoOfObfuscatedChar'),
    'omit_host_structure': ('DomainLength', 'IsDomainIP', 'TLDLength', 'NoOfSubDomain'),
}
METRICS = ('precision', 'recall', 'f1', 'balanced_accuracy', 'average_precision')


def require(test, message):
    if not test:
        raise InputContractError(message)


def bytes_json(obj):
    return (json.dumps(obj, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def sha_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def frozen_request():
    original_path = ROOT / COMPARISON_REQUEST
    require(digest(original_path) == COMPARISON_SHA, 'comparison request changed')
    original = read_json(original_path)
    rf = next(m for m in original['models'] if m['family'] == 'random_forest')
    require(rf['id'] == 'random_forest-000' and rf['base_fits'] == 5
            and rf['calibration_fits'] == 0 and rf['seed'] == 42
            and rf['decision_threshold'] == .5 and rf['score_kind'] == 'probability',
            'unexpected comparison RF settings')
    require(rf['preprocessing']['numeric_scaling'] == 'none'
            and rf['preprocessing']['numeric_missing'] == 'reject', 'unexpected preprocessing')
    names = original['feature_columns']
    require(len(names) == 10 and len(set(names)) == 10, 'unexpected feature set')
    marker = ROOT / COMPARISON_OUTPUT / 'random_forest' / 'completed.json'
    require(marker.is_file(), 'existing RF completion missing')
    for omitted in ABLATIONS.values():
        require(set(omitted) <= set(names), 'ablation feature not in baseline')
    require((ROOT / PROTOCOL).is_file(), 'saved ablation protocol missing')
    return {
        'schema': 'sebrl-phiusiil-fixed-rf-exploratory-ablation-request-v1',
        'status': 'PROPOSED_NOT_AUTHORIZED',
        'scientific_scope': 'exploratory technical sensitivity, not original nested calibrated design',
        'comparison_request_sha256': COMPARISON_SHA,
        'original_comparison_authorization_sha256': digest(ROOT / 'docs/research/2026-11-19_phiusiil_comparison_fitting_authorization.json'),
        'protocol_sha256': digest(ROOT / PROTOCOL),
        'runner_sha256': digest(Path(__file__)),
        'full_feature_rf_completion_sha256': digest(marker),
        'full_feature_rf_predictions_sha256': digest(ROOT / COMPARISON_OUTPUT / 'random_forest' / 'oof_predictions.csv'),
        'input_fingerprint': original['input_fingerprint'],
        'D_manifest_sha256': original['D_manifest_sha256'],
        'C_completion_sha256': original['C_completion_sha256'],
        'D_completion_sha256': original['D_completion_sha256'],
        'eligible_observations': 115563,
        'config': 'U1', 'development_folds': [1, 2, 3, 4, 5],
        'full_feature_names': names,
        'model': rf,
        'ablations': [{'name': name, 'omitted_features': list(omitted),
                       'retained_features': [n for n in names if n not in omitted],
                       'base_fits': 5} for name, omitted in ABLATIONS.items()],
        'fit_budget': {'base_fits': 10, 'calibration_fits': 0,
                       'hyperparameter_search': False, 'threshold_optimization': False},
        'output': OUTPUT,
        'prohibited': ['protected calibration and evaluation populations', 'additional datasets',
                       'new baseline fitting', 'calibration', 'tuning', 'source/target leakage',
                       'original protocol alteration', 'model selection claims'],
    }


def prepare():
    expected = bytes_json(frozen_request())
    target = ROOT / REQUEST
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        require(target.read_bytes() == expected, 'existing request differs; do not overwrite')
    else:
        target.write_bytes(expected)
    print(json.dumps({'status': 'REQUEST_PREPARED_NOT_AUTHORIZED',
                      'request_path': REQUEST, 'request_sha256': sha_bytes(expected),
                      'fits': 0, 'authorization_path': AUTH}, indent=2))


def verify_acceptance(request_bytes):
    path = ROOT / AUTH
    require(path.is_file(), 'separate researcher authorization missing; no fits allowed')
    decision = read_json(path)
    require(set(decision) == {'schema', 'request_sha256', 'decision', 'researcher',
                              'role', 'date', 'response_text'}, 'authorization schema differs')
    require(decision['schema'] == 'sebrl-phiusiil-fixed-rf-ablation-acceptance-v1'
            and decision['request_sha256'] == sha_bytes(request_bytes)
            and decision['decision'] == 'ACCEPT_EXACT_TEN_FIXED_RF_ABLATION_FITS',
            'exact separate fitting authorization not established')
    require(decision['role'] in ('researcher', 'adviser')
            and isinstance(decision['researcher'], str) and decision['researcher'].strip()
            and isinstance(decision['response_text'], str)
            and len(decision['response_text'].strip()) >= 40
            and '10' in decision['response_text']
            and 'exploratory' in decision['response_text'].lower(),
            'specific, attributable acceptance required')
    require(date.fromisoformat(decision['date']) <= date.today(), 'future-dated authorization')
    return digest(path)


def reduced_dataset(dataset, retained):
    full_names = tuple(f.name for f in dataset.specification.conventional)
    indices = tuple(full_names.index(name) for name in retained)
    spec = DevelopmentSpecification(dataset.specification.dataset,
            tuple(dataset.specification.conventional[i] for i in indices),
            dataset.specification.protocol_reference,
            dataset.specification.feature_dictionary_reference)
    rows = tuple(DevelopmentObservation(o.observation_id, o.target, o.group_id, o.fold,
                 tuple(o.conventional[i] for i in indices), o.behavioral)
                 for o in dataset.observations)
    return DevelopmentDataset(spec, rows)


def verify_rf_baseline(original, context):
    model = original['model']
    directory = ROOT / COMPARISON_OUTPUT / 'random_forest'
    completed = completed_model(directory, model, context)
    require(completed is not None, 'baseline RF not valid')
    require(digest(directory / 'completed.json') == original['full_feature_rf_completion_sha256'],
            'baseline RF marker changed')
    require(digest(directory / 'oof_predictions.csv') == original['full_feature_rf_predictions_sha256'],
            'baseline RF predictions changed')
    return completed


def write_csv_exclusive(path, rows, fields):
    with path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_one(dataset, ablation, model, request_sha, auth_sha):
    name = ablation['name']
    directory = ROOT / OUTPUT / name
    require(not directory.exists(), 'output already exists; do not overwrite or refit: ' + name)
    reduced = reduced_dataset(dataset, ablation['retained_features'])
    classifier_spec = ClassifierSpecification('random_forest', model['parameters'], 42)
    preprocessing = PreprocessingSpecification(**model['preprocessing'])
    predictions, reports, audits = [], [], []
    group_lookup = {o.observation_id: o.group_id for o in dataset.observations}
    for plan in development_folds(reduced, 'U1'):
        require(plan.feature_names == tuple(ablation['retained_features']), 'incorrect feature projection')
        pipe = FoldClassifier(reduced.specification, classifier_spec, preprocessing, 'U1')
        start = time.perf_counter()
        pipe.fit(plan.x_train, plan.y_train, feature_names=plan.feature_names, seed=42)
        scores = pipe.score(plan.x_validation, observation_ids=plan.validation_ids)
        require(scores.observation_ids == plan.validation_ids and scores.score_kind == 'probability',
                'unexpected prediction identity or score kind')
        metric = compact_metrics(binary_metrics(plan.y_validation, scores.scores,
                                                 positive_label=1, threshold=.5))
        reports.append({'fold': plan.validation_fold, 'training_rows': len(plan.training_ids),
                        'validation_rows': len(plan.validation_ids),
                        'seconds': time.perf_counter() - start, 'metrics': metric})
        audits.append(pipe.audit_record())
        predictions.extend({'observation_id': oid, 'group_id': group_lookup[oid],
                            'fold': plan.validation_fold, 'target': y,
                            'score': score, 'decision': int(score >= .5)}
                           for oid, y, score in zip(plan.validation_ids, plan.y_validation, scores.scores))
        print(json.dumps({'event': 'fold_complete', 'ablation': name, 'fold': plan.validation_fold}), flush=True)
    require(len(predictions) == 115563 and len({p['observation_id'] for p in predictions}) == 115563,
            'out-of-fold coverage mismatch')
    pooled = compact_metrics(binary_metrics(tuple(p['target'] for p in predictions),
                                            tuple(p['score'] for p in predictions),
                                            positive_label=1, threshold=.5))
    directory.mkdir(parents=True, exist_ok=False)
    write_csv_exclusive(directory / 'oof_predictions.csv', predictions,
                        ('observation_id', 'group_id', 'fold', 'target', 'score', 'decision'))
    write_csv_exclusive(directory / 'metrics.csv',
        [{'scope': f"fold-{r['fold']}", **{m: r['metrics'][m] for m in METRICS}} for r in reports]
        + [{'scope': 'pooled', **{m: pooled[m] for m in METRICS}}], ('scope', *METRICS))
    result = {'schema': 'sebrl-fixed-rf-exploratory-ablation-result-v1',
              'ablation': name, 'omitted_features': ablation['omitted_features'],
              'retained_features': ablation['retained_features'], 'base_fits': 5,
              'calibration_fits': 0, 'settings': model, 'pooled_metrics': pooled,
              'fold_reports': reports, 'pipeline_audits': audits}
    (directory / 'result.json').write_bytes(bytes_json(result))
    with (directory / 'oof_predictions.csv').open(newline='', encoding='utf-8') as stream:
        saved = list(csv.DictReader(stream))
    recalc = compact_metrics(binary_metrics(tuple(int(r['target']) for r in saved),
                             tuple(float(r['score']) for r in saved), positive_label=1,
                             threshold=.5))
    require(recalc == pooled, 'saved results do not reproduce')
    files = {p.name: digest(p) for p in directory.iterdir() if p.is_file()}
    marker = {'request_sha256': request_sha, 'authorization_sha256': auth_sha,
              'runner_sha256': digest(Path(__file__)),
              'ablation': name, 'base_fits': 5, 'calibration_fits': 0,
              'output_sha256': files}
    # Completion marker LAST. A partial output is never silently re-run.
    (directory / 'completed.json').write_bytes(bytes_json(marker))
    return result


def execute():
    expected = bytes_json(frozen_request())
    req_path = ROOT / REQUEST
    require(req_path.is_file() and req_path.read_bytes() == expected,
            'request absent or mutated; prepare and authorize first')
    auth_sha = verify_acceptance(expected)
    original = read_json(req_path)
    # This existing guard verifies the ORIGINAL independently accepted comparison,
    # its scientific C/D source boundaries, and loads development only.
    context, dataset = verify_original_comparison(ROOT)
    require(dataset_fingerprint(dataset) == original['input_fingerprint']
            and len(dataset.observations) == 115563, 'source population changed')
    verify_rf_baseline(original, context)
    require(not (ROOT / OUTPUT).exists(), 'ablation output already exists; no automatic overwrite')
    results = []
    for ablation in original['ablations']:
        results.append(run_one(dataset, ablation, original['model'],
                               sha_bytes(expected), auth_sha))
    print(json.dumps({'status': 'ABLATIONS_COMPLETE', 'fits': 10,
                      'output': OUTPUT,
                      'results': {r['ablation']: r['pooled_metrics'] for r in results}}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--prepare', action='store_true')
    modes.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    try:
        if args.prepare:
            prepare()
        else:
            execute()
    except (InputContractError, KeyError, ValueError, OSError, TypeError) as error:
        print(json.dumps({'status': 'BLOCKED_OR_FAILED', 'reason': str(error),
                          'no_unverified_completion_claim': True}))
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
