"""Development-only NLI review diagnostic for fixed synthetic challenges.

NOT independent annotation, scientific validation, phishing detection accuracy,
or authorization for a protected research stage. Does not change canonical policy.
No network/model downloads; no model fitting or calibration. Never overwrite outputs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

# Force local-only huggingface usage before loading any model-related module.
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / 'experiments' / 'vera_validation'
OUTPUT = ROOT / 'docs' / 'research' / '2026-11-19_sebrl_nli_development_review'
FILES = {
    'lexical': VALIDATION / 'lexical_shortcut_challenges.csv',
    'counterfactual': VALIDATION / 'counterfactual_pairs.csv',
}
SOURCE = {
    'extractor': VALIDATION / 'V13D_hybrid_extractor.py',
    'review_policy': VALIDATION / 'V13E_review_policy.py',
    'hypotheses': VALIDATION / 'V13_nli_hypotheses_v0.1.0.json',
    'codebook': ROOT / 'ml' / 'se_brl' / 'codebook.v0.1.0.json',
}


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def main() -> int:
    # Import only from the existing canonical development implementation.
    sys.path.insert(0, str(VALIDATION))
    from V13D_hybrid_extractor import SemanticNLI, rules_only
    from V13E_review_policy import assess

    cases = []
    lexical = read_csv(FILES['lexical'])
    pairs = read_csv(FILES['counterfactual'])
    if len(lexical) != 20 or len(pairs) != 20:
        raise ValueError('Expected 20 lexical cases and 20 counterfactual pairs; stopping')
    if len({r['case_id'] for r in lexical}) != 20 or len({r['pair_id'] for r in pairs}) != 20:
        raise ValueError('Repeated case IDs')
    for r in lexical:
        cases.append(('lexical', r['case_id'], 'single', r['text'], r['target_indicator'],
                      r['expected_state_provisional']))
    for r in pairs:
        cases.append(('counterfactual', r['pair_id'], 'baseline', r['baseline_text'],
                      r['target_indicator'], r['baseline_expected_provisional']))
        cases.append(('counterfactual', r['pair_id'], 'counterfactual', r['counterfactual_text'],
                      r['target_indicator'], r['counterfactual_expected_provisional']))
    if len(cases) != 60:
        raise AssertionError('Expected 60 judgments')
    if OUTPUT.exists():
        raise FileExistsError(f'Output already exists; refusing overwrite: {OUTPUT}')

    # Loading pinned local model may fail; report that honestly, without fallback.
    try:
        semantic = SemanticNLI()
    except Exception as exc:
        print(json.dumps({'status': 'LOCAL_NLI_UNAVAILABLE', 'fits': 0,
                          'detail': f'{type(exc).__name__}: {exc}', 'output_written': False}, indent=2))
        return 2

    results = []
    for source, case_id, variant, content, indicator, provisional in cases:
        before = rules_only(content, modality='content_bearing_email')
        reviewed = assess(content, modality='content_bearing_email', semantic=semantic,
                          indicators=[indicator])
        if reviewed['semantic_changes_final_labels'] is not False or len(reviewed['indicators']) != 12:
            raise ValueError('Review-only invariants violated')
        if any(reviewed['indicators'][name]['state'] != rec['state'] for name, rec in before.items()):
            raise ValueError('NLI changed rule-based indicator state')
        record = reviewed['indicators'][indicator]
        for span in record['evidence']:
            if content[span['start']:span['end']] != span['text']:
                raise ValueError('Evidence span mismatch')
        if record['state'] == 'unavailable':
            raise ValueError('Unexpected unavailable indicator for synthetic content-bearing case')
        scores = record.get('nli_scores')
        if not isinstance(scores, list) or not scores:
            raise ValueError('NLI was not actually evaluated')
        results.append({
            'dataset': source,
            'case_id': case_id,
            'variant': variant,
            'indicator': indicator,
            'rules_state': record['state'],
            'provisional_expected': provisional,
            'matches_provisional': str(record['state'] == provisional).lower(),
            'needs_review': str(bool(record['needs_review'])).lower(),
            'semantic_review': record['semantic_review'],
            'nli_top_labels_json': json.dumps(record.get('nli_top_labels', [])),
            'nli_scores_json': json.dumps(scores),
            'rule_evidence_json': json.dumps(record['evidence']),
        })
        print(json.dumps({'event': 'case_complete', 'case_id': case_id,
                          'variant': variant, 'needs_review': bool(record['needs_review'])}), flush=True)

    # Quantifies review flags only; exploratory provisional-match breakdown is descriptive.
    counts = Counter((r['dataset'], r['needs_review']) for r in results)
    summary = {
        'status': 'DEVELOPMENT_NLI_REVIEW_COMPLETE',
        'scope': 'synthetic/development challenge diagnostic; no independent ground truth',
        'fits': 0,
        'real_pinned_local_nli_executed': True,
        'all_deterministic_labels_preserved': True,
        'cases': len(results),
        'lexical_judgments': len(lexical),
        'counterfactual_judgments': len(pairs) * 2,
        'review_flags_lexical': counts[('lexical', 'true')],
        'review_flags_counterfactual': counts[('counterfactual', 'true')],
        'l003': [r for r in results if r['case_id'] == 'L003'],
        'source_sha256': {name: sha(path) for name, path in {**FILES, **SOURCE}.items()},
        'cautions': [
            'AI-assisted/provisional expectations are not independent human ground truth',
            'Development cases were previously exposed; no held-out inference claim',
            'NLI review flags are not corrections or automatic changes to labels',
            'No test/calibration partitions accessed; scientific validation gate unchanged',
        ],
    }
    # Write only after all validations and inference have succeeded.
    OUTPUT.mkdir(parents=True, exist_ok=False)
    with (OUTPUT / 'review_cases.csv').open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    (OUTPUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: summary[k] for k in (
        'status', 'fits', 'cases', 'review_flags_lexical', 'review_flags_counterfactual')}, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, AssertionError) as exc:
        print(json.dumps({'status': 'BLOCKED_OR_FAILED', 'reason': str(exc),
                          'do_not_rerun_without_review': True}))
        raise SystemExit(2)
