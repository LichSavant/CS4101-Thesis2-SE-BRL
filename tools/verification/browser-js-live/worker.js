/* Isolated live MiniLM + JavaScript review. No Python runtime or external I/O. */
self.onmessage=async({data})=>{
  if(data.control)return;
  const violations=[];
  self.addEventListener('securitypolicyviolation',e=>violations.push({directive:e.violatedDirective,blocked:e.blockedURI}));
  const wait=name=>new Promise(resolve=>{const handler=({data})=>{if(data.control===name){self.removeEventListener('message',handler);resolve(data);}};self.addEventListener('message',handler);});
  let instrumentationMilliseconds=0;
  const progress=async(stage,detail={})=>{const start=performance.now(),pending=wait('continue');self.postMessage({type:'progress',stage,...detail});await pending;instrumentationMilliseconds+=performance.now()-start;};
  try{
    const cold=performance.now();
    const started=performance.now();
    const review=await import('/review/review.mjs');
    const reviewInitializationMilliseconds=performance.now()-started;
    const {Tokenizer}=await import('/packages/tokenizers/dist/tokenizers.mjs');
    const ort=await import('/packages/ort/dist/ort.wasm.min.mjs');
    ort.env.wasm.wasmPaths='/packages/ort/dist/';ort.env.wasm.numThreads=1;ort.env.wasm.proxy=false;
    const input=await(await fetch('/data/input.json')).json();
    const [tokJSON,tokConfig,config]=await Promise.all(['tokenizer.json','tokenizer_config.json','config.json'].map(async n=>(await fetch('/assets/'+n)).json()));
    if(JSON.stringify(config.id2label)!==JSON.stringify({0:'contradiction',1:'entailment',2:'neutral'}))throw Error('NLI label ordering');
    const tokenizerStart=performance.now(),tokenizer=new Tokenizer(tokJSON,tokConfig);
    const tokenizerMilliseconds=performance.now()-tokenizerStart;
    await progress('js-ready',{reviewInitializationMilliseconds,tokenizerMilliseconds});
    const fetchStart=performance.now();let bytes=new Uint8Array(await(await fetch('/model.onnx')).arrayBuffer());
    const modelFetchMilliseconds=performance.now()-fetchStart,hashStart=performance.now();
    const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');
    if(hash!==input.onnx_sha256||bytes.length!==input.onnx_bytes)throw Error('Pinned model integrity');
    const modelHashMilliseconds=performance.now()-hashStart,modelStart=performance.now();
    const session=await ort.InferenceSession.create(bytes,{executionProviders:['wasm'],graphOptimizationLevel:'all'});
    bytes=null;
    const modelInitializationMilliseconds=performance.now()-modelStart;
    if(JSON.stringify(session.inputNames)!==JSON.stringify(['input_ids','attention_mask'])||JSON.stringify(session.outputNames)!==JSON.stringify(['logits']))throw Error('ONNX I/O contract');
    const coldWallMilliseconds=performance.now()-cold;
    const coldInitializationMilliseconds=coldWallMilliseconds-instrumentationMilliseconds;
    await progress('ready-for-analysis',{modelInitializationMilliseconds,modelFetchMilliseconds,modelHashMilliseconds,coldInitializationMilliseconds,modelHash:hash});
    if(navigator.onLine!==false)throw Error('Network not disabled');
    const cache=new Map(),scored=[],inferenceMilliseconds=[],caseLatencyMilliseconds=[],reviewOnlyMilliseconds=[];
    let calls=0,tokenizationMilliseconds=0;
    const scorer={async score(text,indicator){
      if(navigator.onLine!==false)throw Error('Offline state lost');calls++;
      const key=JSON.stringify([text,indicator]);let result=cache.get(key);
      if(!result){
        const t=performance.now();
        const pairs=input.payload.hypotheses[indicator].map(h=>tokenizer.encode(text,{text_pair:h,add_special_tokens:true}));
        const length=Math.max(...pairs.map(p=>p.ids.length));
        result={text,indicator,input_ids:pairs.map(p=>[...p.ids,...Array(length-p.ids.length).fill(1)]),attention_mask:pairs.map(p=>[...p.attention_mask,...Array(length-p.ids.length).fill(0)]),oversized:length>512,scores:null,logits:null};
        tokenizationMilliseconds+=performance.now()-t;
        if(!result.oversized){
          const shape=[3,length],feeds={input_ids:new ort.Tensor('int64',BigInt64Array.from(result.input_ids.flat(),BigInt),shape),attention_mask:new ort.Tensor('int64',BigInt64Array.from(result.attention_mask.flat(),BigInt),shape)};
          const t=performance.now(),out=await session.run(feeds);inferenceMilliseconds.push(performance.now()-t);
          result.logits=Array.from({length:3},(_,r)=>Array.from(out.logits.data.slice(r*3,r*3+3)));
          if(result.logits.flat().some(v=>!Number.isFinite(v)))throw Error('Non-finite logits');
          result.scores=result.logits.map(row=>{const max=Math.max(...row),e=row.map(v=>Math.exp(v-max)),sum=e.reduce((a,b)=>a+b,0);return{contradiction:e[0]/sum,entailment:e[1]/sum,neutral:e[2]/sum};});
          Object.values(feeds).forEach(t=>t.dispose());out.logits.dispose();
        }
        cache.set(key,result);scored.push(result);
      }
      if(result.oversized)throw new review.SemanticInferenceUnavailable('oversized synthetic input');
      return structuredClone(result.scores);
    }};
    const normalize=report=>{const r=structuredClone(report);for(const row of r.indicators)for(const c of row.semantic_candidates)c.scores='compared_separately';return r;};
    const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
    const outcomes=[],preprocessing=[],analysisStart=performance.now();
    for(const c of input.payload.cases.concat(input.payload.extra_cases)){
      const options={detectorContext:c.context};
      const b=performance.now(),baseline=await review.reviewRecord(c.record,options);reviewOnlyMilliseconds.push(performance.now()-b);
      const t=performance.now(),value=await review.reviewRecord(c.record,{...options,scorer});caseLatencyMilliseconds.push({name:c.name,milliseconds:performance.now()-t});
      if(!value.indicators.every((r,i)=>r.deterministic_state===baseline.indicators[i].deterministic_state&&equal(r.evidence,baseline.indicators[i].evidence))||value.semantic_changes_labels||value.learned_values.some(v=>v!==null)||Object.values(value.research_release).some(Boolean))throw Error('Deterministic/scientific contract changed');
      outcomes.push({name:c.name,outcome:normalize(value)});preprocessing.push(review.preprocess(c.record.artifact_input));
    }
    const scores=await scorer.score(input.payload.boundary_text,'urgency');
    outcomes.push({name:'exact_512_tokens',outcome:{scored:true,maxima:scores.map(s=>Object.keys(s).filter(k=>s[k]===Math.max(...Object.values(s))))}});
    let oversized=false;try{await scorer.score(input.payload.boundary_text+'synthetic ','urgency');}catch(e){oversized=e instanceof review.SemanticInferenceUnavailable;}
    if(!oversized)throw Error('513-token guard');
    outcomes.push({name:'513_tokens_abstain',outcome:{abstained_without_truncation:true}});
    const budgetCase=input.payload.budget_case,before=calls;
    const budget=await review.reviewRecord(budgetCase.record,{scorer,detectorContext:budgetCase.context});
    if(calls-before!==512||!budget.indicators.some(r=>r.failure_codes.includes('semantic_budget_exhausted')))throw Error('Resource budget');
    outcomes.push({name:'64_unit_512_call_budget_replay',outcome:normalize(budget)});
    const first=input.payload.cases[0],valid=await review.reviewRecord(first.record,{scorer,detectorContext:first.context});let rejected=0;
    for(const start of [true,-1]){const bad=structuredClone(valid);bad.indicators[0].semantic_candidates[0].evidence.start=start;try{await review.validateReview(bad,first.record,{detectorContext:first.context});}catch{rejected++;}}
    const promoted=structuredClone(valid);promoted.indicators[0].candidate_state='supported';try{await review.validateReview(promoted,first.record,{detectorContext:first.context});}catch{rejected++;}
    // Deliberately malformed scorer is used only for the original negative guard.
    const bad=await review.reviewRecord(first.record,{detectorContext:first.context,scorer:{score(){return Array(3).fill({entailment:NaN,neutral:0,contradiction:0});}}});
    const nanRejected=bad.indicators.every(r=>!r.semantic_candidates.length);let blocked=false;try{review.predictorValues(valid);}catch{blocked=true;}
    if(rejected!==3||!nanRejected||!blocked)throw Error('Malformed evidence/export guard');
    outcomes.push({name:'malformed_inputs_and_export_gate',outcome:{invalid_spans_and_promotion_rejected:rejected,nan_scores_rejected:nanRejected,predictor_export_blocked:blocked}});
    const consent=input.payload.consent.map(request=>{try{review.recordFromRequest(request);return true;}catch{return false;}});
    const analysisMilliseconds=performance.now()-analysisStart;
    await progress('analysis-complete',{analysisMilliseconds});
    await session.release();
    self.postMessage({ok:true,scored,outcomes:{cases:outcomes,preprocessing},consent,inferenceMilliseconds,caseLatencyMilliseconds,reviewOnlyMilliseconds,analysisMilliseconds,reviewInitializationMilliseconds,tokenizerMilliseconds,tokenizationMilliseconds,modelInitializationMilliseconds,modelFetchMilliseconds,modelHashMilliseconds,coldInitializationMilliseconds,coldWallMilliseconds,modelHash:hash,browserOfflineDuringAnalysis:navigator.onLine===false,wasmThreads:1,ortVersion:ort.env.versions.web,pyodideLoaded:false,scorerCalls:calls,policyViolations:violations});
  }catch(e){self.postMessage({ok:false,error:String(e),stack:e.stack,policyViolations:violations});}
};
