"""Run rules-only development regressions; requires only Python stdlib."""
import csv
import hashlib
import json
from pathlib import Path
from V13D_hybrid_extractor import rules_only
HERE=Path(__file__).resolve().parent

def prediction(message,indicator):
    return rules_only(message)[indicator]['state']

def run():
    v10=[];v11=[]
    with (HERE/'lexical_shortcut_challenges.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            pred=prediction(r['text'],r['target_indicator'])
            v10.append({**r,'proposed_prediction':pred,'matches_provisional':str(pred==r['expected_state_provisional']).lower()})
    with (HERE/'counterfactual_pairs.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            base=prediction(r['baseline_text'],r['target_indicator'])
            cf=prediction(r['counterfactual_text'],r['target_indicator'])
            v11.append({**r,'baseline_prediction':base,'counterfactual_prediction':cf,'directional_success':str(base=='absent' and cf=='supported').lower()})
    digest=hashlib.sha256((HERE/'V13D_hybrid_extractor.py').read_bytes()).hexdigest()
    prefix='V13D_rules_only_dev_'+digest[:12]
    outputs=[HERE/(prefix+'_v10.csv'),HERE/(prefix+'_v11.csv'),HERE/(prefix+'_summary.json')]
    if any(p.exists() for p in outputs):raise FileExistsError('Output already exists; refusing overwrite')
    for path,rows in zip(outputs[:2],[v10,v11]):
        with path.open('x',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    s={'implementation_sha256':digest,'evaluation_kind':'known development regression; not held-out','mode':'rules_only','nli_inference_executed':False,'v10_correct':sum(r['matches_provisional']=='true' for r in v10),'v10_total':len(v10),'v11_success':sum(r['directional_success']=='true' for r in v11),'v11_total':len(v11),'v10_mismatches':[r['case_id'] for r in v10 if r['matches_provisional']=='false'],'v11_failures':[r['pair_id'] for r in v11 if r['directional_success']=='false']}
    outputs[2].write_text(json.dumps(s,indent=2))
    print(json.dumps(s,indent=2));print('Saved:',*[str(x) for x in outputs],sep='\n')
if __name__=='__main__':run()
