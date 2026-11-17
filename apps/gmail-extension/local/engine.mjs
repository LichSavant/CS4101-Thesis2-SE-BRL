import {reviewRecord,recordFromRequest,SemanticInferenceUnavailable} from './review/review.mjs';
import {readVerifiedModel} from './store.mjs';
let session=null,tokenizer=null,ort=null,initializing=null,trace=[],sessionCount=0;
export async function unloadModel(){if(session)await session.release();session=null;tokenizer=null;ort=null;trace=[];}
async function initialize(){
  if(session)return;if(initializing)return initializing;
  initializing=(async()=>{
    const bytes=await readVerifiedModel();
    ort=await import('./runtime/ort.wasm.min.mjs');ort.env.wasm.wasmPaths=new URL('./runtime/',import.meta.url).href;ort.env.wasm.numThreads=1;ort.env.wasm.proxy=false;
    const {Tokenizer}=await import('./runtime/tokenizers.mjs');
    const assets=await Promise.all(['tokenizer.json','tokenizer_config.json','config.json','hypotheses.json'].map(async n=>(await fetch(new URL('./runtime/'+n,import.meta.url))).json()));
    if(JSON.stringify(assets[2].id2label)!==JSON.stringify({0:'contradiction',1:'entailment',2:'neutral'}))throw Error('NLI class order mismatch');
    tokenizer=new Tokenizer(assets[0],assets[1]);initialize.hypotheses=assets[3].hypotheses;
    session=await ort.InferenceSession.create(bytes,{executionProviders:['wasm'],graphOptimizationLevel:'all'});sessionCount++;
    if(JSON.stringify(session.inputNames)!==JSON.stringify(['input_ids','attention_mask'])||JSON.stringify(session.outputNames)!==JSON.stringify(['logits'])){await unloadModel();throw Error('Model input contract mismatch');}
  })();try{await initializing;}finally{initializing=null;}
}
export async function inferEvidence(text,indicator){
  if(typeof text!=='string'||Array.from(text).length>200000||typeof indicator!=='string')throw new SemanticInferenceUnavailable();
  await initialize();
  if(!initialize.hypotheses[indicator])throw new SemanticInferenceUnavailable();
    const pairs=initialize.hypotheses[indicator].map(h=>tokenizer.encode(text,{text_pair:h,add_special_tokens:true}));const length=Math.max(...pairs.map(p=>p.ids.length));
    const item={text,indicator,input_ids:pairs.map(p=>[...p.ids,...Array(length-p.ids.length).fill(1)]),attention_mask:pairs.map(p=>[...p.attention_mask,...Array(length-p.ids.length).fill(0)]),oversized:length>512,logits:null,scores:null};
    if(!item.oversized){const shape=[3,length],feeds={input_ids:new ort.Tensor('int64',BigInt64Array.from(item.input_ids.flat(),BigInt),shape),attention_mask:new ort.Tensor('int64',BigInt64Array.from(item.attention_mask.flat(),BigInt),shape)};let output;
      try{const t=performance.now();output=await session.run(feeds);item.ms=performance.now()-t;item.logits=Array.from({length:3},(_,r)=>Array.from(output.logits.data.slice(r*3,r*3+3)));item.scores=item.logits.map(row=>{const max=Math.max(...row),e=row.map(v=>Math.exp(v-max)),sum=e.reduce((a,b)=>a+b,0);return{contradiction:e[0]/sum,entailment:e[1]/sum,neutral:e[2]/sum};});}finally{Object.values(feeds).forEach(t=>t.dispose());output?.logits.dispose();}
    }
  return item;
}
export async function analyzeRecord(record,context,{ai=false,consent=false,diagnostics=false}={}){
  if(consent!==true)throw Error('Explicit local analysis consent required');
  const start=performance.now();trace=[];let initMs=0,warning=null,initFailed=false;
  // Symbolic validation/extraction always precedes optional model initialization.
  const baseline=await reviewRecord(record,{detectorContext:context});
  const cache=new Map();let forwards=0;
  const scorer={async score(text,indicator){
    if(initFailed)throw new SemanticInferenceUnavailable();
    if(!session){const t=performance.now();try{await initialize();}catch{initFailed=true;warning='Local AI unavailable. Deterministic evidence is preserved; semantic review abstains. Reinstall or free resources.';throw new SemanticInferenceUnavailable();}finally{initMs+=performance.now()-t;}}
    const key=JSON.stringify([text,indicator]);if(cache.has(key)){const c=cache.get(key);if(c.oversized)throw new SemanticInferenceUnavailable();return c.scores;}
    const item=await inferEvidence(text,indicator);if(!item.oversized)forwards++;
    cache.set(key,item);if(diagnostics)trace.push(item);if(item.oversized)throw new SemanticInferenceUnavailable();return item.scores;
  }};
  const report=ai?await reviewRecord(record,{detectorContext:context,scorer}):baseline;
  return{report,warning,ai:ai&&!!session,metrics:{milliseconds:performance.now()-start,initMs,forwards,sessionCount},...(diagnostics?{trace}: {})};
}
export async function analyzeRequest(request,options){return analyzeRecord(recordFromRequest(request),null,options);}
