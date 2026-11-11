"""Exploratory V13-F paired audit: rules baseline vs NLI review, not a validated classifier.

Only writes an explicitly chosen, previously nonexistent output path.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
from V13D_hybrid_extractor import rules_only, SemanticNLI
from V13E_review_policy import assess

HERE = Path(__file__).resolve().parent
CODEBOOK_INDICATORS = set(rules_only('Test message.'))

def candidate_top_labels(scores):
    return [max(('entailment','neutral','contradiction'), key=lambda k:float(s[k])) for s in scores]

def summarize_semantic(scores):
    """Not a label predictor: report candidate vote and raw-score range only."""
    tops = candidate_top_labels(scores)
    return {'top_labels': tops,
            'entailment_votes':tops.count('entailment'),
            'entailment_min':min(float(s['entailment']) for s in scores),
            'entailment_max':max(float(s['entailment']) for s in scores),
            'entailment_spread':max(float(s['entailment']) for s in scores)-min(float(s['entailment']) for s in scores)}

def load_cases(path, kind, limit=None):
    with path.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    if kind=='v10':
        required = {'case_id','text','target_indicator','expected_state_provisional'}
    else:
        required = {'pair_id','baseline_text','counterfactual_text','target_indicator','baseline_expected_provisional','counterfactual_expected_provisional'}
    if not rows or not required <= set(rows[0]):
        raise ValueError(f'Invalid {kind} input schema')
    if any(r['target_indicator'] not in CODEBOOK_INDICATORS for r in rows):
        raise ValueError('Unknown target indicator')
    if limit is not None: rows=rows[:limit]
    return rows

def audit_record(text, indicator, semantic):
    reviewed=assess(text, semantic=semantic, indicators=[indicator])
    item=reviewed['indicators'][indicator]
    result={'state':item['state'], 'evidence':item['evidence'],
            'needs_review':item['needs_review'], 'semantic_review':item['semantic_review']}
    if 'nli_scores' in item:
        result['nli_scores']=item['nli_scores']
        result['semantic_diagnostic']=summarize_semantic(item['nli_scores'])
    else:
        result['semantic_diagnostic']=None
    return result

def run(kind, semantic=None, limit=None, input_path=None):
    path = Path(input_path) if input_path else HERE/('lexical_shortcut_challenges.csv' if kind=='v10' else 'counterfactual_pairs.csv')
    cases=load_cases(path,kind,limit)
    results=[]
    for row in cases:
        indicator=row['target_indicator']
        if kind=='v10':
            decision=audit_record(row['text'],indicator,semantic)
            results.append({'case_id':row['case_id'],'indicator':indicator,
                'expected_provisional':row['expected_state_provisional'],
                'rules_match_provisional':decision['state']==row['expected_state_provisional'],
                'decision':decision})
        else:
            baseline=audit_record(row['baseline_text'],indicator,semantic)
            modified=audit_record(row['counterfactual_text'],indicator,semantic)
            results.append({'pair_id':row['pair_id'],'indicator':indicator,
                'rules_directional_success':baseline['state']=='absent' and modified['state']=='supported',
                'baseline':baseline,'counterfactual':modified})
    return {'dataset':kind,'mode':'nli_review' if semantic else 'rules_only',
        'nli_changes_labels':False,'provisional_labels_not_human_validated':True,
        'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'v13d_sha256':hashlib.sha256((HERE/'V13D_hybrid_extractor.py').read_bytes()).hexdigest(),
        'v13e_sha256':hashlib.sha256((HERE/'V13E_review_policy.py').read_bytes()).hexdigest(),
        'count':len(results), 'rules_successes':sum(bool(x['rules_match_provisional'] if kind=='v10' else x['rules_directional_success']) for x in results),
        'results':results}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',choices=['v10','v11'],required=True)
    p.add_argument('--cpu-nli',action='store_true')
    p.add_argument('--max-cases',type=int,default=3,help='Default 3 for a low-cost smoke test; 0 means all')
    p.add_argument('--output',type=Path,required=True,help='Fresh .json file inside experiments/vera_validation')
    args=p.parse_args()
    if args.max_cases < 0: p.error('--max-cases cannot be negative')
    destination=args.output.resolve()
    if destination.parent != HERE.resolve() or destination.suffix!='.json':
        p.error('Output must be a .json file directly inside experiments/vera_validation/')
    if destination.exists():
        p.error('Refusing to overwrite existing file: '+str(destination))
    semantic=SemanticNLI() if args.cpu_nli else None
    result=run(args.dataset,semantic=semantic,limit=args.max_cases or None)
    with destination.open('x',encoding='utf-8') as file:
        json.dump(result,file,indent=2,ensure_ascii=False)
    print(f"V13-F {args.dataset}: {result['rules_successes']}/{result['count']} rule-only regression matches; NLI review={'on' if args.cpu_nli else 'off'}")
    print('NLI changes final decisions: NO; semantic scores are diagnostic only')
    print('Saved:',destination)

if __name__=='__main__':main()
