let worker=null,nextId=0,busy=false;
const pending=new Map();
export function unload(){if(worker)worker.terminate();worker=null;busy=false;for(const [,p]of pending){clearTimeout(p.timer);p.reject(Error('Local worker stopped; retry explicitly'));}pending.clear();}
export async function call(operation,value={}){
  if(busy)throw Error('Local operation already active; wait or unload before retrying');
  busy=true;
  if(!worker){worker=new Worker(new URL('./worker.mjs',import.meta.url),{type:'module'});worker.onmessage=({data})=>{const p=pending.get(data.id);if(!p)return;pending.delete(data.id);clearTimeout(p.timer);busy=false;data.ok?p.resolve(data.result):p.reject(Error(data.error));};worker.onerror=()=>unload();}
  const policy=await chrome.storage.local.get(['processingMode','localConsent','localAIEnabled']);
  return new Promise((resolve,reject)=>{const id=++nextId,timer=setTimeout(()=>unload(),180000);pending.set(id,{resolve,reject,timer});worker.postMessage({id,operation,value,policy});});
}
