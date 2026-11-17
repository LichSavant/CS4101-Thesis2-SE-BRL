let worker=null,nextId=0,busy=false,generation=0;
const pending=new Map();
export function unload(){
  generation++;worker?.terminate();worker=null;busy=false;
  for(const [,p]of pending){clearTimeout(p.timer);p.reject(Error('Local worker stopped; retry explicitly'));}
  pending.clear();
}
export async function call(operation,value={},onProgress=()=>{}){
  if(busy)throw Error('Local operation already active; wait or unload before retrying');
  busy=true;const current=generation;
  if(!worker){
    try{worker=new Worker(new URL('./worker.mjs',import.meta.url),{type:'module'});}catch{busy=false;throw Error('Local worker unavailable; retry explicitly. No backend fallback.');}
    const created=worker;
    worker.onmessage=({data})=>{
      if(worker!==created)return;
      const p=pending.get(data.id);if(!p)return;
      if(data.progress){p.onProgress(data.progress);return;}
      pending.delete(data.id);clearTimeout(p.timer);busy=false;
      if(data.result?.metrics){data.result.metrics.workerRoundTripMs=performance.now()-p.sent;data.result.metrics.messagingMs=Math.max(0,data.result.metrics.workerRoundTripMs-data.workerMs);data.result.metrics.preferenceReadMs=p.preferenceReadMs;}
      data.ok?p.resolve(data.result):p.reject(Error(data.error));
    };
    worker.onerror=()=>{if(worker===created)unload();};
    worker.onmessageerror=()=>{if(worker===created)unload();};
  }
  const target=worker,preferenceStart=performance.now();let policy;
  try{policy=await chrome.storage.local.get(['processingMode','localConsent','localAIEnabled']);}
  catch{if(current===generation)busy=false;throw Error('Local preferences unavailable; no backend fallback.');}
  // Cancellation can happen during the asynchronous preference read, before a
  // pending RPC exists. Never post to a new worker or leave a stale timer behind.
  if(current!==generation||target!==worker)throw Error('Local worker stopped; retry explicitly');
  const preferenceReadMs=performance.now()-preferenceStart;
  return new Promise((resolve,reject)=>{
    const id=++nextId,timer=setTimeout(()=>unload(),180000);
    pending.set(id,{resolve,reject,timer,sent:performance.now(),preferenceReadMs,onProgress});
    try{target.postMessage({id,operation,value,policy});}
    catch{pending.delete(id);clearTimeout(timer);busy=false;reject(Error('Invalid local request; nothing was sent.'));}
  });
}
