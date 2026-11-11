"""Experimental SE-BRL prototype. Not a production detector or validated ground truth.
CPU-only, no model downloads unless --semantic is explicitly requested.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODEBOOK = HERE.parents[1] / 'ml/se_brl/codebook.v0.1.0.json'
CONFIG = HERE / 'V13_nli_hypotheses_v0.1.0.json'

# Patterns are intentionally broad development heuristics, not validated operating rules.
RULES = {
 'urgency':[r'\b(?:urgent|immediately|asap|act now|right away|deadline|expires?)\b',r'\b(?:before|by|within|until)\s+(?:midnight|sunrise|tonight|tomorrow|today|your next login|the office closes|\d+\s*(?:minutes?|hours?|days?))\b',r'\bwithin (?:the )?next \w+ (?:minutes?|hours?|days?)\b',r'\bmust\b.{0,90}\b(?:today|before|within)\b'],
 'fear_threat':[r'\b(?:suspended|terminated|blocked|compromised|penalty|legal action|account closure|disabled|permanently removed|locked|loss of access|loss of your|will be removed)\b',r'\b(?:failure to|unless|if you (?:do not|don.t|refuse))\b.{0,110}\b(?:lose|removed|closed|disabled|locked|suspended|terminated|result in|deleted)\b'],
 'scarcity':[r'\b(?:limited (?:time|offer|availability)|while supplies last|last chance|exclusive offer)\b',r'\bonly\s+(?:\d+|one|two|three|four|five)\s+(?:\w+\s+){0,2}(?:left|remain|available|places|seats)\b',r'\b(?:remaining|last)\s+(?:invitations?|places?|seats?|spots?)\b',r'\b(?:no additional|once the remaining|last available seat)\b'],
 'curiosity':[r'\b(?:see what happened|check this out|you won.t believe|mystery|surprise|find out what|hidden information)\b'],
 'reward_lure':[r'\b(?:won|winner|prize|reward|bonus|gift|cashback|free|voucher|complimentary|discount|incentive)\b',r'\b(?:receive|collect|get)\b.{0,50}\b(?:subscription|membership|ticket|entry|voucher)\b'],
 'authority':[r'\b(?:as your|i am your|by order of the|from the)\s+(?:administrator|manager|ceo|security team|director|government|bank)\b'],
 'confidentiality_isolation':[r'\b(?:keep this private|do not share|do not tell|between us|keep (?:this|it) secret|do not consult)\b'],
 'call_to_action':[r'\b(?:please\s+)?(?:click|open|visit|download|verify|confirm|update|sign in|log in|reply|submit|provide|send|enter|complete|register|fill out|review|transfer|pay|share)\b'],
 'credential_sensitive_data_request':[r'\b(?:password|passcode|pin|otp|verification code|secret code|recovery (?:questions?|answers?)|account recovery answers|login credentials|banking credentials|account credentials|social security number)\b',r'\b(?:secret code (?:you use|used) to access|answers to your account recovery)\b'],
 'financial_action_request':[r'\b(?:send|transfer|pay|deposit|wire|submit|provide|make)\b.{0,70}\b(?:money|payment|funds|bank transfer|fee|deposit|invoice|credit card|debit card)\b'],
}
# Context excludes descriptions of attack tactics and negated directives; intentionally conservative.
META = re.compile(r'\b(?:training|workshop|handbook|lecture|textbook|tutorial|article|manual|dictionary|class|lesson|awareness|marketing class|discuss(?:es|ing)?|explain(?:s|ing)?|defines?|examples?|phrase|word|says never|never share|never send)\b',re.I)
NEGATION = re.compile(r'\b(?:never|do not|don.t|should not|must not)\s+(?:send|provide|share|enter|disclose|give)\b',re.I)
REQUEST = re.compile(r'\b(?:send|provide|submit|enter|share|disclose|give|type|supply|fill|complete|register|collect|receive|transfer|pay)\b',re.I)


def _load_codebook():
    cb=json.loads(CODEBOOK.read_text())
    return cb,{i['id']:d['id'] for d in cb['dimensions'] for i in d['indicators']}


def _spans(text, patterns):
    spans=[]; seen=set()
    for pattern in patterns:
        for match in re.finditer(pattern,text,re.I):
            key=(match.start(),match.end())
            if key not in seen:
                seen.add(key);spans.append({'text':text[slice(*key)],'start':key[0],'end':key[1]})
    return sorted(spans,key=lambda s:(s['start'],s['end']))


def _assessable(indicator,modality,text,identity_evidence):
    if modality in ('standalone_url','engineered_technical_record') or not text.strip():return False
    if indicator in ('impersonation','brand_exploitation'):return bool(identity_evidence)
    # Authority and confidentiality cues can be textually observable, but verify provenance separately.
    return True


def rules_only(text,modality='content_bearing_email',identity_evidence=None):
    cb, ids=_load_codebook(); text=str(text or '')
    if modality not in {m['id'] for m in cb['modalities']}:raise ValueError('Unsupported modality')
    output={}
    for indicator in ids:
        if not _assessable(indicator,modality,text,identity_evidence):
            output[indicator]={'state':'unavailable','evidence':[],'needs_review':False,'reason':'required modality or evidence missing'}
            continue
        spans=_spans(text,RULES.get(indicator,[]))
        if META.search(text):
            # Blanket conservative guard: will miss mixed messages containing both education and instructions.
            spans=[]
        if indicator in ('credential_sensitive_data_request','financial_action_request'):
            if not REQUEST.search(text) or NEGATION.search(text):spans=[]
        if indicator=='call_to_action' and NEGATION.search(text):spans=[]
        if indicator=='reward_lure' and not re.search(r'\b(?:receive|collect|get|claim|offered?|promis(?:e|ed)|complimentary|free|discount|bonus|voucher|gift)\b',text,re.I):spans=[]
        if indicator=='authority' and not identity_evidence: # claimed authority is observable but unverified
            pass
        if indicator in ('impersonation','brand_exploitation'):
            # Identity metadata alone never establishes inconsistency or misleading brand use.
            output[indicator]={'state':'absent','evidence':[],'needs_review':True,'reason':'identity claim requires external verification'}
            continue
        output[indicator]={'state':'supported' if spans else 'absent','evidence':spans,'needs_review':False,'reason':'development regex context rules'}
    return output


class SemanticNLI:
    def __init__(self,config=CONFIG):
        from transformers import AutoTokenizer,AutoModelForSequenceClassification
        import torch
        self.torch=torch
        self.cfg=json.loads(Path(config).read_text())
        self.model=AutoModelForSequenceClassification.from_pretrained(self.cfg['model']).to('cpu').eval()
        self.tokenizer=AutoTokenizer.from_pretrained(self.cfg['model'])
        self.indices={str(v).lower():int(k) for k,v in self.model.config.id2label.items()}
        if not {'entailment','neutral','contradiction'}<=self.indices.keys():raise ValueError('Unexpected NLI labels')
    def score(self,text,indicator):
        h=self.cfg['hypotheses'][indicator]
        inputs=self.tokenizer([text]*len(h),h,padding=True,truncation=True,max_length=512,return_tensors='pt')
        with self.torch.inference_mode():p=self.torch.softmax(self.model(**inputs).logits,dim=-1).cpu().tolist()
        return [{'hypothesis':x,**{k:round(float(y[self.indices[k]]),6) for k in ('entailment','neutral','contradiction')}} for x,y in zip(h,p)]


def extract(text,modality='content_bearing_email',identity_evidence=None,semantic=None):
    labels=rules_only(text,modality,identity_evidence)
    if semantic is None:return {'indicators':labels,'mode':'rules_only'}
    for indicator,result in labels.items():
        if result['state']=='unavailable':continue
        scores=semantic.score(text,indicator)
        result['nli_scores']=scores
        # No calibrated fusion policy exists. Preserve rules decision and surface conflicts.
        top=[max(('entailment','neutral','contradiction'),key=lambda k:s[k]) for s in scores]
        if len(set(top))>1 or ('entailment' in top and result['state']=='absent'):
            result['needs_review']=True
            result['reason']+='; NLI disagreement or candidate support without grounded rule evidence'
    return {'indicators':labels,'mode':'hybrid_review_only','semantic_contributes_to_review_flags':True}


def main():
    p=argparse.ArgumentParser();p.add_argument('--text',required=True);p.add_argument('--modality',default='content_bearing_email');p.add_argument('--semantic',action='store_true');args=p.parse_args()
    model=SemanticNLI() if args.semantic else None
    print(json.dumps(extract(args.text,args.modality,semantic=model),indent=2))
if __name__=='__main__':main()
