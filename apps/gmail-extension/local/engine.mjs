import {reviewRecord,recordFromRequest,SemanticInferenceUnavailable} from './review/review.mjs';
import {readVerifiedModel} from './store.mjs';
let session=null,tokenizer=null,ort=null,initializing=null,trace=[],sessionCount=0,lastLoad={};
export async function unloadModel(){if(session)await session.release();session=null;tokenizer=null;ort=null;trace=[];}
async function initialize(){
  if(session)return;if(initializing)return initializing;
  initializing=(async()=>{
    lastLoad={};const bytes=await readVerifiedModel(lastLoad);let stage=performance.now();
    ort=await import('./runtime/ort.wasm.min.mjs');ort.env.wasm.wasmPaths=new URL('./runtime/',import.meta.url).href;ort.env.wasm.numThreads=crossOriginIsolated?(navigator.hardwareConcurrency>=4?4:navigator.hardwareConcurrency>1?2:1):1;ort.env.wasm.proxy=false;
    const {Tokenizer}=await import('./runtime/tokenizers.mjs');
    const assets=await Promise.all(['tokenizer.json','tokenizer_config.json','config.json','hypotheses.json'].map(async n=>(await fetch(new URL('./runtime/'+n,import.meta.url))).json()));
    if(JSON.stringify(assets[2].id2label)!==JSON.stringify({0:'contradiction',1:'entailment',2:'neutral'}))throw Error('NLI class order mismatch');
    tokenizer=new Tokenizer(assets[0],assets[1]);initialize.hypotheses=assets[3].hypotheses;
    lastLoad.runtimeAndTokenizerMs=performance.now()-stage;stage=performance.now();session=await ort.InferenceSession.create(bytes,{executionProviders:['wasm'],graphOptimizationLevel:'all'});sessionCount++;lastLoad.sessionCreateMs=performance.now()-stage;
    if(JSON.stringify(session.inputNames)!==JSON.stringify(['input_ids','attention_mask'])||JSON.stringify(session.outputNames)!==JSON.stringify(['logits'])){await unloadModel();throw Error('Model input contract mismatch');}
  })();try{await initializing;}finally{initializing=null;}
}
export async function inferEvidence(text,indicator){
  if(typeof text!=='string'||Array.from(text).length>200000||typeof indicator!=='string')throw new SemanticInferenceUnavailable();
  await initialize();
  if(!initialize.hypotheses[indicator])throw new SemanticInferenceUnavailable();
    let stage=performance.now();const pairs=initialize.hypotheses[indicator].map(h=>tokenizer.encode(text,{text_pair:h,add_special_tokens:true}));const length=Math.max(...pairs.map(p=>p.ids.length));
    const item={text,indicator,input_ids:pairs.map(p=>[...p.ids,...Array(length-p.ids.length).fill(1)]),attention_mask:pairs.map(p=>[...p.attention_mask,...Array(length-p.ids.length).fill(0)]),oversized:length>512,logits:null,scores:null};
    item.tokenizationMs=performance.now()-stage;stage=performance.now();
    if(!item.oversized){const shape=[3,length],feeds={input_ids:new ort.Tensor('int64',BigInt64Array.from(item.input_ids.flat(),BigInt),shape),attention_mask:new ort.Tensor('int64',BigInt64Array.from(item.attention_mask.flat(),BigInt),shape)};let output;
      try{item.tensorPreparationMs=performance.now()-stage;const t=performance.now();output=await session.run(feeds);item.ms=performance.now()-t;item.logits=Array.from({length:3},(_,r)=>Array.from(output.logits.data.slice(r*3,r*3+3)));item.scores=item.logits.map(row=>{const max=Math.max(...row),e=row.map(v=>Math.exp(v-max)),sum=e.reduce((a,b)=>a+b,0);return{contradiction:e[0]/sum,entailment:e[1]/sum,neutral:e[2]/sum};});}finally{Object.values(feeds).forEach(t=>t.dispose());output?.logits.dispose();}
    }
  return item;
}
export async function analyzeRecord(record,context,{ai=false,consent=false,diagnostics=false,progress=()=>{}}={}){
  if(consent!==true)throw Error('Explicit local analysis consent required');
  const start=performance.now();trace=[];let initMs=0,warning=null,initFailed=false,requests=0,cacheHits=0,tokenizationMs=0,tensorPreparationMs=0,inferenceMs=0;
  // Symbolic validation/extraction always precedes optional model initialization.
  const baseline=await reviewRecord(record,{detectorContext:context});const symbolicPassMs=performance.now()-start;
  const cache=new Map();let forwards=0;
  const scorer={async score(text,indicator){
    requests++;
    if(initFailed)throw new SemanticInferenceUnavailable();
    if(!session){progress({stage:'Verifying and loading local AI'});const t=performance.now();try{await initialize();}catch{initFailed=true;warning='Local AI unavailable. Deterministic evidence is preserved; semantic review abstains. Reinstall or free resources.';throw new SemanticInferenceUnavailable();}finally{initMs+=performance.now()-t;}}
    const key=JSON.stringify([text,indicator]);if(cache.has(key)){cacheHits++;const c=cache.get(key);if(c.oversized)throw new SemanticInferenceUnavailable();return c.scores;}
    const item=await inferEvidence(text,indicator);if(!item.oversized){forwards++;progress({stage:'Local semantic review',hypothesisEvaluations:forwards*3});}tokenizationMs+=item.tokenizationMs??0;tensorPreparationMs+=item.tensorPreparationMs??0;inferenceMs+=item.ms??0;
    cache.set(key,item);if(diagnostics)trace.push(item);if(item.oversized)throw new SemanticInferenceUnavailable();return item.scores;
  }};
  const report=ai?await reviewRecord(record,{detectorContext:context,scorer}):baseline;
  const milliseconds=performance.now()-start;
  return{report,warning,ai:ai&&!!session,metrics:{milliseconds,initMs,forwards,sessionCount,requests,cacheHits,hypothesisEvaluations:forwards*3,symbolicPassMs,tokenizationMs,tensorPreparationMs,inferenceMs,reviewAndConstraintsMs:Math.max(0,milliseconds-symbolicPassMs-initMs-tokenizationMs-tensorPreparationMs-inferenceMs),sessionLoad:initMs>0?{...lastLoad}:null,threads:ort?.env.wasm.numThreads??0,isolated:crossOriginIsolated,hardwareConcurrency:navigator.hardwareConcurrency},...(diagnostics?{trace}: {})};
}
export async function analyzeRequest(request,options){return analyzeRecord(recordFromRequest(request),null,options);}
