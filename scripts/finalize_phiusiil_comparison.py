"""Verify saved predictions and export aggregate-only results; never load features or fit."""
import csv
import json
import math
from pathlib import Path
import statistics

from ml.comparison_batch import (REQUEST,REQUEST_SHA256,AUTHORIZATION,PERSONAL,OUTPUT,
    METRICS,digest,compact_metrics,validate_request,VerifiedComparison,completed_model,_TOKEN)
from ml.evaluation_metrics import binary_metrics
from ml.research_protocol import code_hashes

PUBLIC='docs/research/2026-11-19_phiusiil_comparison_results'


def require(condition,reason):
    if not condition:raise ValueError(reason)


def equal(actual,expected):
    if isinstance(expected,dict):
        return isinstance(actual,dict) and set(actual)==set(expected) and all(equal(actual[k],v) for k,v in expected.items())
    if isinstance(expected,list):return isinstance(actual,list) and len(actual)==len(expected) and all(equal(a,b) for a,b in zip(actual,expected))
    if type(expected) is float:return type(actual) in (float,int) and math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-12)
    return actual==expected


def metrics(rows,threshold):
    return compact_metrics(binary_metrics(tuple(r['target'] for r in rows),tuple(r['score'] for r in rows),positive_label=1,threshold=threshold))


def predictions(path,threshold):
    with path.open(newline='') as stream:rows=list(csv.DictReader(stream))
    groups={};identities={}
    for row in rows:
        row.update(target=int(row['target']),fold=int(row['fold']),score=float(row['score'] if 'score' in row else row['raw_probability']),decision=int(row['decision']))
        require(row['target'] in (0,1) and row['fold'] in range(1,6) and math.isfinite(row['score']),'invalid prediction')
        require(row['decision']==int(row['score']>=threshold),'decision threshold mismatch')
        oid=row['observation_id'];group=row['group_id']
        require(oid not in identities,'duplicate OOF ID')
        require(group not in groups or groups[group]==row['fold'],'OOF group crosses folds')
        groups[group]=row['fold'];identities[oid]=(row['target'],group,row['fold'])
    require(len(rows)==115563,'OOF population mismatch')
    require(all({r['target'] for r in rows if r['fold']==fold}=={0,1} for fold in range(1,6)),'fold class coverage')
    return rows,identities,len(groups)


def main():
    root=Path(__file__).resolve().parents[1]
    read=lambda p:json.loads((root/p).read_bytes())
    request=read(REQUEST);require(digest(root/REQUEST)==REQUEST_SHA256,'request hash');validate_request(request)
    auth=read(AUTHORIZATION);personal=read(PERSONAL)
    require(auth['request_sha256']==REQUEST_SHA256 and auth['authority']==personal['authority']
        and personal['decision']=='ACCEPT_FIXED_THREE_FAMILY_COMPARISON','attributable acceptance')
    require(auth['code_sha256']==code_hashes(root),'executed code changed')
    context=VerifiedComparison(root,digest(root/AUTHORIZATION),request,auth['code_sha256'],_TOKEN)
    baseline=read(request['baseline']['manifest_path'])
    require(digest(root/request['baseline']['manifest_path'])==request['baseline']['manifest_sha256'],'LR manifest hash')
    baseline_path=root/request['baseline']['run']/'oof_predictions.csv'
    require(digest(baseline_path)==request['baseline']['prediction_sha256'],'LR predictions hash')
    baseline_rows,universe,group_count=predictions(baseline_path,.5)
    models=[('logistic_regression',baseline_rows,baseline['pooled_metrics'],baseline['fold_results'],baseline['pipeline_audits'],baseline['executed_identity'])]
    source_files={REQUEST,AUTHORIZATION,PERSONAL,request['baseline']['manifest_path'],baseline_path.relative_to(root).as_posix()}
    for model in request['models']:
        directory=root/OUTPUT/model['family']
        result=completed_model(directory,model,context)
        require(result is not None,'completed family missing')
        rows,ids,groups=predictions(directory/'oof_predictions.csv',model['decision_threshold'])
        require(ids==universe and groups==group_count,'model ID/group/target/fold mismatch')
        marker=read((directory/'completed.json').relative_to(root))
        require(marker['identity']['settings_sha256']==__import__('ml.metadata',fromlist=['fingerprint']).fingerprint(result['settings']),'settings identity')
        require(result['base_fits']==5 and result['calibration_fits']==0,'fit counts')
        for metric in METRICS:
            values=[f['metrics'][metric] for f in result['fold_reports']]
            require(equal(result['fold_variability'][metric],{'mean':statistics.mean(values),'population_sd':statistics.pstdev(values)}),'fold variability')
        with (directory/'metrics.csv').open(newline='') as stream:table=list(csv.DictReader(stream))
        require(len(table)==6,'saved metrics table length')
        expected=[('fold-'+str(f['fold']),f['metrics']) for f in result['fold_reports']]+[('pooled',result['pooled_metrics'])]
        for row,(scope,values) in zip(table,expected):
            require(row['scope']==scope and all(equal(float(row[m]),values[m]) for m in METRICS),'saved metrics CSV mismatch')
        models.append((model['family'],rows,result['pooled_metrics'],result['fold_reports'],result['pipeline_audits'],marker['identity']))
        source_files.update(p.relative_to(root).as_posix() for p in directory.iterdir() if p.is_file())
    comparison=[];fold_table=[];verified=[]
    for family,rows,pooled,reports,audits,identity in models:
        threshold=0. if family=='linear_svm' else .5
        require(equal(metrics(rows,threshold),pooled),'pooled metrics fail recomputation: '+family)
        require(len(reports)==5 and {r['fold'] for r in reports}==set(range(1,6)) and len(audits)==5,'five folds/audits')
        for report,audit in zip(reports,audits):
            fold=report['fold'];subset=[r for r in rows if r['fold']==fold]
            require(equal(metrics(subset,threshold),report['metrics']),'fold metrics fail recomputation')
            require(report['validation_rows']==len(subset) and report['training_rows']==115563-len(subset),'fold row counts')
            require(audit['training_rows']==report['training_rows'] and audit['family']==family
                and audit['feature_names']==request['feature_columns'] and audit['seed']==42,'training audit mismatch')
            require(math.isfinite(report['seconds']) and report['seconds']>=0,'invalid runtime')
            fold_table.append(dict(family=family,fold=fold,training_rows=report['training_rows'],validation_rows=len(subset),seconds=report['seconds'],**{m:report['metrics'][m] for m in METRICS}))
        confusion=pooled['confusion_matrix']
        comparison.append(dict(family=family,**{m:pooled[m] for m in METRICS},fold_mean_AP=statistics.mean(r['metrics']['average_precision'] for r in reports),fold_AP_population_sd=statistics.pstdev(r['metrics']['average_precision'] for r in reports),fold_F1_population_sd=statistics.pstdev(r['metrics']['f1'] for r in reports),fold_computation_seconds=sum(r['seconds'] for r in reports),TN=confusion[0][0],FP=confusion[0][1],FN=confusion[1][0],TP=confusion[1][1]))
        verified.append(dict(family=family,rows=len(rows),folds=5,OOF_groups=group_count,group_crossings=0,pooled_and_fold_metrics_recomputed=True,identity=identity))
    # Existing batch summary is evidence too: compare, do not overwrite.
    with (root/OUTPUT/'comparison.csv').open(newline='') as stream:old=list(csv.DictReader(stream))
    require(len(old)==4,'batch summary count')
    for row in old:
        value=next(r for r in comparison if r['family']==row['family'])
        require(all(equal(float(row[k]),value[k]) for k in row if k!='family'),'batch summary mismatch')
    source_files.update((OUTPUT+'/comparison.csv',OUTPUT+'/comparison_results.md'))
    ranked=sorted(comparison,key=lambda r:r['average_precision'],reverse=True)
    for row in ranked:row['rank']=1+sum(r['average_precision']>row['average_precision'] for r in ranked)
    out=root/PUBLIC;out.mkdir(exist_ok=False)
    def table(name,rows):
        with (out/name).open('x',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,list(rows[0]));writer.writeheader();writer.writerows(rows)
    table('comparison.csv',ranked);table('fold_metrics.csv',fold_table)
    source=read(request['configuration_source']['path'])
    ablations=[{'name':a['name'],'omitted_features':a['runner_specification']['omitted_features'],'status':'NOT AUTHORIZED; candidate nested search/calibration specification is not covered by fixed comparison acceptance'} for a in source['technical_ablations']]
    winner=ranked[0]
    text='# Exploratory PhiUSIIL technical-feature comparison\n\n'
    text+='Five group-isolated development folds covered 115,563 observations (49,355 phishing; 66,208 legitimate). All models used the same ten technical fields and folds. Logistic Regression predictions were reused; the additional three families completed fifteen fixed uncalibrated fits. No fitting occurred during this verification.\n\n'
    text+='| Model | AP | Precision | Recall | F1 | Balanced accuracy | Fold computation (s) |\n|---|---:|---:|---:|---:|---:|---:|\n'
    for r in ranked:text+=f"| {r['family']} | {r['average_precision']:.6f} | {r['precision']:.6f} | {r['recall']:.6f} | {r['f1']:.6f} | {r['balanced_accuracy']:.6f} | {r['fold_computation_seconds']:.3f} |\n"
    text+='\nUnder the predefined highest-pooled-noninterpolated-average-precision rule, Random Forest is the provisional descriptive winner (AP '+f"{winner['average_precision']:.6f}"+'). Ties are retained. This is not formal implementation selection: the existing calibrated nested-evidence, uncertainty and operational acceptance requirements remain unsatisfied.\n\n'
    text+='Random Forest also had the highest F1 and balanced accuracy; Linear SVM had no observed false positives at its fixed zero-margin threshold. Fold variability is descriptive, not an independent-sample confidence interval or significance test. Raw SVM margins can vary in scale across folds; within-fold AP and mean AP are provided alongside pooled AP. Runtime measures saved fit/score/metric computation, excludes loading and verification, and is not an inference-latency benchmark.\n\n'
    text+='The population has historical exposure and prospectively reconstructed lineage; no untouched-holdout generalization claim follows. This technical-only subset does not validate the twelve behavioral indicators or Transformer/NLI effectiveness. No calibration, search, threshold optimization, protected evaluation or new dataset access occurred. Source hashes and group isolation support reproducibility but do not imply independent source authentication.\n\n'
    text+='## Planned ablations\n\n'
    for a in ablations:text+='- '+a['name']+': remove '+', '.join(a['omitted_features'])+'. '+a['status']+'.\n'
    text+='\nEach ablation requires an exact separately accepted request binding feature omissions, model/settings, folds, preprocessing, fit count, output identity and code. A minimal fixed five-fold design would need acceptance before replacing the existing candidate nested search/calibration plan. Current authorization covers neither ablation; no ablation fitting was performed.\n'
    (out/'results.md').write_text(text,encoding='utf-8')
    manifest=dict(category='saved-prediction verification and aggregate exploratory results',fits_during_finalization=0,new_protected_access=False,request_sha256=REQUEST_SHA256,selection_policy=request['selection_policy'],ranking=[r['family'] for r in ranked],provisional_winner=winner['family'],formal_implementation_selection=False,verification=verified,ablations=ablations,command='python -B -m scripts.finalize_phiusiil_comparison',verification_script_sha256=digest(Path(__file__)),source_sha256={p:digest(root/p) for p in sorted(source_files)},public_output_sha256={p.name:digest(p) for p in out.iterdir() if p.is_file()})
    (out/'reproducibility_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='PASS',records_per_model=115563,ranking=manifest['ranking'],fits=0,output=PUBLIC)))


if __name__=='__main__':main()
