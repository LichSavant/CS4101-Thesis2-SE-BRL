// Dedicated extension-origin CPU worker; no server, telemetry, or remote assets.
const nativeFetch=self.fetch.bind(self);
self.fetch=(input,init={})=>{const url=new URL(typeof input==='string'?input:input.url??input,location.href);if(url.origin!==location.origin||!url.pathname.startsWith('/local/')||(init.method??'GET')!=='GET')return Promise.reject(Error('Local worker blocks network transmission'));return nativeFetch(input,init);};
for(const name of ['XMLHttpRequest','WebSocket','EventSource'])self[name]=class{constructor(){throw Error('Local worker blocks external I/O');}};
let owner=false;const acquired=new Promise(resolve=>navigator.locks.request('sebrl-model-owner',{ifAvailable:true},async lock=>{owner=!!lock;resolve(owner);if(lock)await new Promise(()=>{});}));
let busy=false;
self.onmessage=async({data})=>{
  const operationStart=performance.now();
  if(busy){self.postMessage({id:data.id,ok:false,error:'Local operation already active'});return;}busy=true;
  try{
    if(!await acquired)throw Error('Another local workspace owns the model. Close it first.');
    // Dedicated workers have no extension storage API. The trusted extension
    // page projects current preferences per call and terminates us on revocation.
    const {operation,value={},policy:settings}=data;
    if(!settings||typeof settings!=='object')throw Error('Missing local policy');
    if(settings.processingMode==='legacy')throw Error('Local worker disabled while legacy research mode is selected');
    const store=await import('./store.mjs');const progress=value=>self.postMessage({id:data.id,progress:value});let result;
    if(operation==='status')result=await store.modelStatus();
    else if(operation==='install'){if(value.approved!==true)throw Error('Installation approval required');const engine=await import('./engine.mjs');await engine.unloadModel();result=await store.installModel(value.file,true,progress);}
    else if(operation==='remove'){const engine=await import('./engine.mjs');await engine.unloadModel();await store.removeModel();result={installed:false};}
    else if(operation==='analyze'||operation==='record'||operation==='infer'){
      if(settings.localConsent!==true||value.consent!==true)throw Error('Explicit local consent required');
      const engine=await import('./engine.mjs');
      const options={consent:true,ai:settings.localAIEnabled===true,diagnostics:value.diagnostics===true,progress};
      if(operation==='infer'){if(settings.localAIEnabled!==true)throw Error('Local AI disabled');result=await engine.inferEvidence(value.text,value.indicator);}
      else result=operation==='record'?await engine.analyzeRecord(value.record,value.context,options):await engine.analyzeRequest(value.request,options);
    }else throw Error('Unknown local operation');
    self.postMessage({id:data.id,ok:true,result,workerMs:performance.now()-operationStart});
  }catch(e){const safe=new Set(['Explicit model installation approval required','Installation approval required','Only the exact approved FP32 ONNX file is accepted','Insufficient storage quota; free space before installing','Model integrity verification failed. Existing model preserved.','Another local workspace owns the model. Close it first.','Explicit local consent required','Local worker disabled while legacy research mode is selected','Model storage operation failed; check quota']);self.postMessage({id:data.id,ok:false,error:(safe.has(e.message)?e.message:'Local operation unavailable. Check consent, declared English language, model integrity, quota, or another open workspace.')+' No backend fallback.'});}
  finally{busy=false;}
};
