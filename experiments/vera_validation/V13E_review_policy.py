"""V13-E conservative semantic review policy; not a calibrated behavioral classifier.

Never promotes NLI entailment alone to `supported`. Does not alter V13-D.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from V13D_hybrid_extractor import rules_only, SemanticNLI

HERE = Path(__file__).resolve().parent
INDICATORS = tuple(rules_only('Example content.'))

def _top(scores: list[dict[str, Any]]) -> list[str]:
    return [max(('entailment','neutral','contradiction'), key=lambda k:float(s[k])) for s in scores]

def assess(text: str, modality: str = 'content_bearing_email', identity_evidence=None,
           semantic=None, indicators: list[str] | None = None) -> dict[str, Any]:
    """Return audited review signals. No semantic auto-overrides or invented evidence.

    `indicators` restricts expensive transformer inference; all labels are included.
    """
    base = rules_only(text, modality=modality, identity_evidence=identity_evidence)
    chosen = list(indicators) if indicators is not None else list(base)
    unknown = set(chosen)-set(base)
    if unknown: raise ValueError(f'Unknown indicators: {sorted(unknown)}')
    if len(chosen)!=len(set(chosen)): raise ValueError('Duplicate indicators')
    result = {}
    for indicator, initial in base.items():
        record = dict(initial)
        record['decision_source'] = 'rules_only_v13d'
        record['semantic_review'] = 'not_requested'
        if record['state']=='supported':
            if not record['evidence']:
                raise AssertionError(f'Unsupported grounded explanation: {indicator}')
            for span in record['evidence']:
                assert text[span['start']:span['end']] == span['text']
        if indicator in chosen and semantic is not None and record['state']!='unavailable':
            scores = semantic.score(text, indicator)
            if len(scores)!=3: raise ValueError('Expected three candidate hypotheses')
            record['nli_scores'] = scores
            top = _top(scores)
            record['nli_top_labels'] = top
            if len(set(top))>1:
                record['needs_review'] = True
                record['semantic_review'] = 'hypothesis_disagreement'
            elif top[0]=='entailment' and record['state']=='absent':
                record['needs_review'] = True
                record['semantic_review'] = 'unverified_semantic_candidate_without_rule_evidence'
            elif top[0]!='entailment' and record['state']=='supported':
                record['needs_review'] = True
                record['semantic_review'] = 'semantic_rule_disagreement'
            else:
                record['semantic_review'] = 'agreement_not_independent_validation'
            # IMPORTANT: Do not promote/drop a label from an uncalibrated NLI score.
        elif record['state']=='unavailable':
            record['semantic_review'] = 'unavailable_not_scored'
        result[indicator] = record
    return {'mode':'conservative_semantic_review_v0.1',
            'semantic_changes_final_labels':False,
            'indicators':result}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--text',required=True)
    p.add_argument('--modality',default='content_bearing_email')
    p.add_argument('--indicators',nargs='+',default=['urgency','reward_lure','credential_sensitive_data_request'])
    p.add_argument('--cpu-nli',action='store_true',help='Load real CPU NLI model; downloads may occur')
    args=p.parse_args()
    semantic=SemanticNLI() if args.cpu_nli else None
    print(json.dumps(assess(args.text,args.modality,semantic=semantic,indicators=args.indicators),indent=2))
if __name__=='__main__': main()
