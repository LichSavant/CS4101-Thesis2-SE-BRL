"""Experimental, label-blind retention of authoritative deterministic rule identity.

No rule changes, inference models, new detections, fitting or scientific admission.
The existing count-based E2-E representation is preserved as a frozen prefix.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'experiments/e2_enrichment_20261124'
CONTEXT_SHA = '74414ff27be3963ba089c75a4a04bf2ee8975ff74e9e45e68bd25343b2f1ae21'


def rule_provenance(result, rules):
    """Known qualifying rule identity, not raw vocabulary or class-derived features."""
    by_id = {rule.rule_id: rule for rule in rules}
    indicators = {item.indicator_id: item for item in result.indicators}
    if not by_id or len(by_id) != len(rules) or len(indicators) != len(result.indicators):
        raise ValueError('Unique explicit rules and indicators required')
    features = {}
    for rule in rules:
        item = indicators[rule.indicator_id]
        name = 'rule_evidence__' + rule.rule_id
        if item.evaluation_status != 'rule_evaluated':
            features[name] = None
            continue
        hits = [e for e in item.evidence if e.rule_id == rule.rule_id]
        if hits and item.evidence_state != 'supported':
            raise ValueError('Evidence cannot promote an absent indicator')
        if any(e.provenance != 'rule-based' or e.indicator_id != rule.indicator_id
               or e.ruleset_version != result.ruleset_version for e in hits):
            raise ValueError('Only matching authoritative deterministic evidence is admissible')
        features[name] = int(bool(hits))
    return features


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def run(instruction_path):
    """One persisted development extraction, then one explicitly optimistic diagnostic.

    Access uses the existing exact delivery/crosswalk boundary and reported
    development-extraction scope. This is not fitting admission. No new source,
    reserved observation or remote service is used.
    """
    import pandas as pd
    from ml.se_brl import extraction

    sys.path.insert(0, str(HERE))
    from restricted_delivery_adapter import validate_delivery, iter_preprocessing_inputs, METADATA
    from research_preprocessing_adapter import preprocess_research_email
    from v42_evidence_adapter import V42EvidenceAdapter
    from supplementary_exporter import build_representations
    from evidence_enrichment_v1 import evidence_features

    output = HERE / 'provenance_representation_run01'
    if output.exists():
        raise FileExistsError('Existing run preserved; do not repeat or overwrite extraction')
    scope = json.loads((HERE / 'e2e_development_scope.json').read_text())
    if (scope['scope']['development_extraction_authorized_reported'] is not True
            or scope['scope']['reserved_test_access'] is not False
            or scope['research_fitting_authorized'] is not False):
        raise PermissionError('Existing development-only access scope required; no fitting permitted')
    receipt = json.loads((HERE / 'primary_v53_features_run01/extraction_receipt.json').read_text())
    if receipt['candidate_sha256'] != CONTEXT_SHA or digest(HERE / 'candidate_context_v6.py') != CONTEXT_SHA:
        raise ValueError('Frozen V5.3 context differs')
    context_path = HERE / 'candidate_context_v6.py'
    spec = importlib.util.spec_from_file_location('ml.se_brl._provenance_v53_context', context_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    adapter = V42EvidenceAdapter()
    rules = adapter.engine.rules
    if len(rules) != 35:
        raise ValueError('Expected frozen 35-rule registry')
    baseline_path = HERE / 'primary_v53_features_run01/e2-e.csv'
    if digest(baseline_path) != receipt['feature_hashes']['e2-e.csv']:
        raise ValueError('Frozen V5.3 matrix differs')
    baseline = pd.read_csv(baseline_path, float_precision='round_trip')
    base_features = [c for c in baseline if c not in METADATA]
    lookup = baseline.set_index('observation_id')
    payload = HERE / 'restricted_delivery/primary_development_payload.csv'
    payload_fields = [c for c in pd.read_csv(payload, nrows=0).columns if c not in METADATA]
    frame = validate_delivery(payload,
                              HERE / 'primary_development_crosswalk.csv', receipt['payload_sha256'],
                              receipt['crosswalk_sha256'], payload_fields)
    if len(frame) != 15011 or len(lookup) != len(frame) or not lookup.index.is_unique:
        raise ValueError('Exact frozen development population required')
    output.mkdir(exist_ok=False)
    binding = {'candidate': 'V5.3 authoritative-rule provenance', 'context_sha256': CONTEXT_SHA,
               'source_sha256': digest(__file__), 'baseline_sha256': receipt['feature_hashes']['e2-e.csv'],
               'payload_sha256': receipt['payload_sha256'], 'crosswalk_sha256': receipt['crosswalk_sha256'],
               'researcher_instruction_sha256': digest(instruction_path),
               'scope': 'exploratory development representation only; existing local delivery',
               'new_representation_predictors': 35, 'classifier_fitting_performed': False,
               'scientific_admission_granted': False, 'transformer_policy': 'review_only',
               'reserved_test_accessed': False}
    (output / 'run_binding.json').write_text(json.dumps(binding, indent=2))
    definitions = [{'name': 'rule_evidence__' + r.rule_id, 'rule_id': r.rule_id,
                    'indicator_id': r.indicator_id, 'missing': 'None when indicator not evaluated',
                    'meaning': 'matching qualifying deterministic rule evidence present'} for r in rules]
    (output / 'predictor_dictionary.json').write_text(json.dumps({'frozen_prefix': base_features,
                                                                 'additional_predictors': definitions}, indent=2))
    path = output / 'e2-provenance.csv'
    fields = METADATA + base_features + [d['name'] for d in definitions]
    started = time.perf_counter()
    seen = set()
    with path.open('x', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for index, (metadata, raw) in enumerate(iter_preprocessing_inputs(frame), 1):
            identity = metadata['observation_id']
            if identity in seen or identity not in lookup.index:
                raise ValueError('Duplicate or unmatched identity')
            reference = lookup.loc[identity]
            for key in METADATA[1:]:
                if metadata[key] != reference[key]:
                    raise ValueError('Frozen assignment mismatch')
            seen.add(identity)
            artifact = preprocess_research_email(raw)  # only original allowed fields, no target/source
            original = extraction.ContextIndex
            try:
                extraction.ContextIndex = module.ContextIndex
                result = adapter.engine.extract(artifact)
            finally:
                extraction.ContextIndex = original
            legacy = {**build_representations(result)['E2-D'], **evidence_features(result, adapter.rule_ids)}
            if set(legacy) != set(base_features):
                raise ValueError('V5.3 schema parity failure')
            for key, value in legacy.items():
                previous = reference[key]
                if not ((value is None and pd.isna(previous)) or value == previous):
                    raise ValueError('V5.3 parity failure in ' + key + '; persisted prefix retained for diagnosis')
            writer.writerow({**metadata, **legacy, **rule_provenance(result, rules)})
            if index % 500 == 0:
                stream.flush()
                (output / 'progress.json').write_text(json.dumps({'persisted_rows': index, 'complete': False}))
                print('Persisted', index, '/ 15011; frozen 96-feature parity PASS', flush=True)
    if seen != set(lookup.index):
        raise ValueError('Incomplete population; no downstream assessment')
    binding.update(observations=len(seen), feature_hash=digest(path),
                   elapsed_seconds=time.perf_counter() - started, extraction_complete=True)
    (output / 'extraction_receipt.json').write_text(json.dumps(binding, indent=2))
    assess(output)


def assess(output):
    """Resume downstream diagnostics from persisted extraction, never re-extract."""
    import pandas as pd
    import numpy as np
    output = Path(output)
    if (output / 'representation_assessment.json').exists():
        raise FileExistsError('Existing assessment preserved; do not repeatedly optimize diagnostics')
    receipt = json.loads((output / 'extraction_receipt.json').read_text())
    path = output / 'e2-provenance.csv'
    if not receipt.get('extraction_complete') or digest(path) != receipt['feature_hash']:
        raise ValueError('Complete persisted extraction with matching digest required')
    definition = json.loads((output / 'predictor_dictionary.json').read_text())
    base_features = definition['frozen_prefix']
    features = base_features + [r['name'] for r in definition['additional_predictors']]
    # Only after persistence: one frozen, target-aware diagnostic, not a trained model.
    full = pd.read_csv(path, float_precision='round_trip')
    def patterns(columns):
        return full[columns].fillna('__MISSING__').astype(str).agg('|'.join, axis=1)
    old_pattern, new_pattern = patterns(base_features), patterns(features)
    refinement = pd.DataFrame({'old': old_pattern, 'new': new_pattern}).groupby('old')['new'].nunique()
    from sklearn.metrics import average_precision_score, f1_score
    def diagnostic(pattern):
        rates = pd.DataFrame({'pattern': pattern, 'target': full['target']}).groupby('pattern')['target'].mean()
        scores = pattern.map(rates).to_numpy()
        # Preserve a clearly optimistic threshold diagnostic; never call this CV performance.
        thresholds = np.unique(scores)
        f1 = max(f1_score(full['target'], scores >= t) for t in thresholds)
        return {'optimistic_ap': average_precision_score(full['target'], scores),
                'optimistic_best_f1': f1, 'patterns': int(pattern.nunique())}
    report = {'scope': 'target-aware in-sample diagnostic; no classifier fitting or independent validation',
              'baseline': diagnostic(old_pattern), 'candidate': diagnostic(new_pattern),
              'baseline_patterns_refined': int((refinement > 1).sum()),
              'changed_supported_indicators': 0, 'changed_availability_states': 0,
              'classifier_performance': None, 'complete_source_class_confounding': True}
    (output / 'representation_assessment.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--run', action='store_true')
    mode.add_argument('--assess', type=Path)
    parser.add_argument('--instruction', type=Path)
    args = parser.parse_args()
    if args.assess:
        assess(args.assess)
    elif not args.instruction:
        parser.error('Bind the explicit researcher instruction file; no scope is inferred')
    else:
        run(args.instruction)
