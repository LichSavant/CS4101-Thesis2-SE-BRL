import {reviewRecord,validateReview,predictorValues,recordFromRequest,preprocess,SemanticInferenceUnavailable,utf16ToCodePoint,codePointToUtf16} from './review.mjs';
import {parseAddress} from './mailbox.mjs';
const equal=(a,b)=>JSON.stringify(sort(a))===JSON.stringify(sort(b));
const sort=x=>Array.isArray(x)?x.map(sort):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,sort(x[k])])):x;
export function makeScorer(mode,requests) {
  if(mode==='none')return null;
  const lookup=new Map(requests.map(r=>[JSON.stringify([r.text,r.indicator]),r]));
  return {count:0,score(text,indicator){
    this.count++;
    if(mode==='replay'){
      const r=lookup.get(JSON.stringify([text,indicator]));if(!r)throw Error('missing frozen score');
      if(r.oversized)throw new SemanticInferenceUnavailable();return structuredClone(r.scores);
    }
    if(mode==='unavailable')throw new SemanticInferenceUnavailable('private-path');
    if(mode==='failure'||mode==='partial'&&this.count%2)throw Error('private-error');
    if(mode==='bad_empty')return [];
    if(mode==='bad_boolean')return Array(3).fill({entailment:true,neutral:0,contradiction:0});
    if(mode==='bad_nan')return Array(3).fill({entailment:NaN,neutral:0,contradiction:0});
    if(mode==='bad_sum')return Array(3).fill({entailment:.9,neutral:.9,contradiction:.9});
    if(mode==='tie')return Array(3).fill({entailment:.5,neutral:.5,contradiction:0});
    const labels=['entailment','neutral','contradiction'];
    return [0,1,2].map(i=>({...Object.fromEntries(labels.map(k=>[k,k===(mode==='mixed'?labels[i]:labels.includes(mode)?mode:'entailment')?.9:.05])),...(mode==='extra_score_key'?{untrusted:1}:{})}));
  }};
}
function firstDiff(a,b,path='') {
  if(equal(a,b))return null;
  if(a&&b&&typeof a==='object'&&typeof b==='object'){
    for(const k of new Set([...Object.keys(a),...Object.keys(b)])){const diff=firstDiff(a[k],b[k],path+'/'+k);if(diff)return diff;}
  }
  return {path,python:a,javascript:b};
}
export async function run(bundle) {
  const failures=[],reports=[],times=[];let passed=0;
  let mailboxPassed=0,preprocessingPassed=0;
  for(const [i,c]of bundle.mailbox.entries()){
    const value=parseAddress(c.value),diff=firstDiff(c.expected,value);
    if(diff)failures.push({name:'mailbox-direct:'+i,...diff});else mailboxPassed++;
  }
  for(const c of bundle.preprocessing){
    let ok=false,value=null;try{value=preprocess(c.raw);ok=true;}catch{}
    const diff=firstDiff({ok:c.ok,value:c.expected},{ok,value});
    if(diff)failures.push({name:c.name,...diff});else preprocessingPassed++;
  }
  for(let i=0;i<bundle.cases.length;i++){
    const c=bundle.cases[i],s=makeScorer(c.mode,bundle.requests),start=performance.now();
    try{
      const report=await reviewRecord(c.record,{scorer:s,detectorContext:c.context});
      times.push(performance.now()-start);reports.push(report);
      const diff=firstDiff(bundle.expected[i].report,report);
      if(diff)failures.push({name:c.name,...diff});
      else if((s?.count??0)!==bundle.expected[i].calls)failures.push({name:c.name,call_count:[bundle.expected[i].calls,s?.count??0]});
      else passed++;
    }catch(e){reports.push(null);failures.push({name:c.name,error:e.message});}
  }
  let validationPassed=0;
  for(let i=0;i<bundle.mutations.length;i++){
    const [path,value]=bundle.mutations[i],changed=structuredClone(bundle.expected[0].report);let target=changed;
    for(const k of path.slice(0,-1))target=target[k];target[path.at(-1)]=value;
    try{await validateReview(changed,bundle.cases[0].record,{detectorContext:bundle.cases[0].context});failures.push({name:'mutation:'+path.join('/'),accepted:true});}
    catch{validationPassed++;}
  }
  let adapterPassed=0;
  for(const [i,c]of bundle.adapter.entries()){
    let value=null,ok=false;try{value=recordFromRequest(c.request).artifact_input;ok=true;}catch{}
    if(ok===c.ok&&equal(value,c.artifact))adapterPassed++;else failures.push({name:'adapter:'+i,python:c,javascript:{ok,value}});
  }
  let exportBlocked=false;try{predictorValues();}catch{exportBlocked=true;}
  if(!exportBlocked)failures.push({name:'predictor_export'});
  const unicode='🧪 e\u0301 𝟙 Act now.';
  let offsetChecks=0;
  for(let i=0;i<=Array.from(unicode).length;i++)if(utf16ToCodePoint(unicode,codePointToUtf16(unicode,i))===i)offsetChecks++;else failures.push({name:'offset-roundtrip:'+i});
  try{utf16ToCodePoint(unicode,1);failures.push({name:'split_surrogate_accepted'});}catch{offsetChecks++;}
  // Four original frozen guard cases: token-boundary states are replayed from
  // the unchanged tokenizer/model oracle, not newly claimed tokenizer execution.
  const boundary=makeScorer('replay',bundle.requests);let frozenGuards=0;
  try{boundary.score(bundle.payload.boundary_text,'urgency');frozenGuards++;}catch{failures.push({name:'exact_512_replay'});}
  try{boundary.score(bundle.payload.boundary_text+'synthetic ','urgency');failures.push({name:'513_replay'});}catch(e){if(e instanceof SemanticInferenceUnavailable)frozenGuards++;else failures.push({name:'513_missing_score'});}
  const budgetIndex=bundle.cases.findIndex(c=>c.name==='64_unit_512_call_budget_replay');
  if(reports[budgetIndex]&&equal(reports[budgetIndex],bundle.expected[budgetIndex].report))frozenGuards++;
  if(validationPassed===bundle.mutations.length&&exportBlocked)frozenGuards++;
  const sorted=[...times].sort((a,b)=>a-b);
  return {status:failures.length?'FAIL':'PASS',original_187:{passed:reports.slice(0,187).filter((r,i)=>equal(r,bundle.expected[i].report)).length,total:187},differential:{passed,failed:bundle.cases.length-passed,total:bundle.cases.length},mailbox:{passed:mailboxPassed,total:bundle.mailbox.length},html_preprocessing:{passed:preprocessingPassed,total:bundle.preprocessing.length},frozen_24:{passed:reports.slice(0,20).filter((r,i)=>equal(r,bundle.expected[i].report)).length+frozenGuards,total:24},validation_rejections:validationPassed,adapter_cases:adapterPassed,unicode_roundtrips:offsetChecks,failures,timing_ms:{median:sorted[Math.floor(sorted.length/2)],p95:sorted[Math.ceil(sorted.length*.95)-1],total:times.reduce((a,b)=>a+b,0)},reports};
}
