// Model data only. One atomic IndexedDB transaction activates a verified blob.
export const MODEL=Object.freeze({repository:'cross-encoder/nli-MiniLM2-L6-H768',revision:'b95119ce93d3e065de6214e38cd4a97b0f2f2c6d',sha256:'e30e5283a933a7424cd95f45450159979241771dcef999832c2626b480705596',bytes:328641531});
export async function digest(bytes){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');}
async function db(){return new Promise((resolve,reject)=>{const r=indexedDB.open('sebrl-local-model',1);r.onupgradeneeded=()=>r.result.createObjectStore('models');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(Error('Model storage unavailable'));});}
async function transaction(mode,operation){const d=await db();try{return await new Promise((resolve,reject)=>{const t=d.transaction('models',mode);let result;const request=operation(t.objectStore('models'));request.onsuccess=()=>{result=request.result;};t.oncomplete=()=>resolve(result);t.onabort=t.onerror=()=>reject(Error('Model storage operation failed; check quota'));});}finally{d.close();}}
export async function removeModel(){await transaction('readwrite',s=>s.delete('active'));}
export async function modelStatus(){const r=await transaction('readonly',s=>s.get('active'));return{installed:!!r,bytes:r?.blob?.size??0,revision:r?.revision??null};}
export async function readVerifiedModel(){
  const r=await transaction('readonly',s=>s.get('active'));if(!r)throw Error('Model not installed');
  const bytes=await r.blob.arrayBuffer();
  if(r.revision!==MODEL.revision||bytes.byteLength!==MODEL.bytes||await digest(bytes)!==MODEL.sha256){await removeModel();throw Error('Corrupt model removed. Reinstall the verified model.');}
  return new Uint8Array(bytes);
}
export async function installModel(file,approved){
  if(approved!==true)throw Error('Explicit model installation approval required');
  if(!(file instanceof Blob)||file.size!==MODEL.bytes)throw Error('Only the exact approved FP32 ONNX file is accepted');
  const estimate=await navigator.storage.estimate();
  if(estimate.quota&&estimate.quota-(estimate.usage??0)<MODEL.bytes)throw Error('Insufficient storage quota; free space before installing');
  const bytes=await file.arrayBuffer();if(await digest(bytes)!==MODEL.sha256)throw Error('Model integrity verification failed. Existing model preserved.');
  // Nothing is written until every byte passes. A failed/terminated transaction
  // leaves the previous active record intact; no incomplete activation marker.
  await transaction('readwrite',s=>s.put({revision:MODEL.revision,sha256:MODEL.sha256,blob:new Blob([bytes])},'active'));
  return modelStatus();
}
