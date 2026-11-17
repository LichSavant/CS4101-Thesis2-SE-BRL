// Model data only. One atomic IndexedDB transaction activates a verified blob.
export const MODEL=Object.freeze({repository:'cross-encoder/nli-MiniLM2-L6-H768',revision:'b95119ce93d3e065de6214e38cd4a97b0f2f2c6d',sha256:'e30e5283a933a7424cd95f45450159979241771dcef999832c2626b480705596',bytes:328641531});
export async function digest(bytes){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');}
async function db(){return new Promise((resolve,reject)=>{const r=indexedDB.open('sebrl-local-model',1);r.onupgradeneeded=()=>r.result.createObjectStore('models');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(Error('Model storage unavailable'));});}
async function transaction(mode,operation){const d=await db();try{return await new Promise((resolve,reject)=>{const t=d.transaction('models',mode);let result;const request=operation(t.objectStore('models'));request.onsuccess=()=>{result=request.result;};t.oncomplete=()=>resolve(result);t.onabort=t.onerror=()=>reject(Error('Model storage operation failed; check quota'));});}finally{d.close();}}
export async function removeModel(){await transaction('readwrite',s=>s.delete('active'));}
export async function modelStatus(){const r=await transaction('readonly',s=>s.get('active'));return{installed:!!r,bytes:r?.blob?.size??0,revision:r?.revision??null};}
export async function readVerifiedModel(metrics={}){
  let start=performance.now();const r=await transaction('readonly',s=>s.get('active'));metrics.storageReadMs=performance.now()-start;if(!r)throw Error('Model not installed');
  start=performance.now();const bytes=await r.blob.arrayBuffer();metrics.modelReadMs=performance.now()-start;
  start=performance.now();const actual=await digest(bytes);metrics.hashMs=performance.now()-start;
  if(r.revision!==MODEL.revision||bytes.byteLength!==MODEL.bytes||actual!==MODEL.sha256){await removeModel();throw Error('Corrupt model removed. Reinstall the verified model.');}
  return new Uint8Array(bytes);
}
export async function installModel(file,approved,progress=()=>{}){
  if(approved!==true)throw Error('Explicit model installation approval required');
  if(!(file instanceof Blob)||file.size!==MODEL.bytes)throw Error('Only the exact approved FP32 ONNX file is accepted');
  progress({stage:'Checking available storage',step:0,total:4});const estimate=await navigator.storage.estimate();
  if(estimate.quota&&estimate.quota-(estimate.usage??0)<MODEL.bytes)throw Error('Insufficient storage quota; free space before installing');
  progress({stage:'Reading selected model file',step:1,total:4});const bytes=await file.arrayBuffer();progress({stage:'Verifying approved SHA-256',step:2,total:4});if(await digest(bytes)!==MODEL.sha256)throw Error('Model integrity verification failed. Existing model preserved.');
  // Nothing is written until every byte passes. A failed/terminated transaction
  // leaves the previous active record intact; no incomplete activation marker.
  // Blob/File data is immutable. Store the verified source Blob directly instead
  // of allocating another full 328 MB Blob copy. Session activation still hashes
  // the actual stored bytes, including after browser/worker restart.
  progress({stage:'Saving verified model atomically',step:3,total:4});await transaction('readwrite',s=>s.put({revision:MODEL.revision,sha256:MODEL.sha256,blob:file},'active'));progress({stage:'Completing installation',step:4,total:4});
  return modelStatus();
}
