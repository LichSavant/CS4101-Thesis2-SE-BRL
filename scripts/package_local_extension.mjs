// Offline, hash-checked packaging from already approved local assets. No downloads.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const root=process.cwd(),out=path.join(root,'apps/gmail-extension/dist/local');
// Reuse verified local assets; never download or relax integrity checks.
const assetRoot=process.env.SEBRL_LOCAL_ASSET_ROOT || ['.venv-transformer'].find(candidate=>fs.existsSync(path.join(candidate,'browser-harness/package-integrity.json')));
if(!assetRoot)throw Error('Verified local assets unavailable. Set SEBRL_LOCAL_ASSET_ROOT.');
const asset=relative=>path.join(assetRoot,relative);
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const phase7=JSON.parse(fs.readFileSync('docs/research/js-review-parity.json','utf8'));
const phase6=JSON.parse(fs.readFileSync('docs/research/minilm-browser-fp32-verification.json','utf8'));
const integrity=JSON.parse(fs.readFileSync(asset('browser-harness/package-integrity.json'),'utf8'));
const prep=JSON.parse(fs.readFileSync(asset('browser-harness/data/preparation.json'),'utf8'));
fs.mkdirSync(out,{recursive:true});
fs.cpSync('apps/gmail-extension/local',out,{recursive:true});
const copied={};
function copy(source,name,expected){const bytes=fs.readFileSync(source);if(hash(bytes)!==expected)throw Error('Approved asset integrity failed: '+source);const target=path.join(out,name);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,bytes);copied[name]={sha256:expected,bytes:bytes.length};}
for(const name of ['review.mjs','contracts.mjs','mailbox.mjs','python-url.mjs'])copy('tools/verification/js-review/'+name,'review/'+name,phase7.provenance.source_sha256[name]);
for(const [pkg,dir,names]of [['onnxruntime-web','ort',['ort.wasm.min.mjs','ort-wasm-simd-threaded.mjs','ort-wasm-simd-threaded.wasm']],['@huggingface/tokenizers','tokenizers',['tokenizers.mjs']]]){
  const record=integrity.packages.find(p=>p.name===pkg);if(record.version!==(dir==='ort'?'1.20.1':'0.2.0'))throw Error('Unapproved version');
  for(const name of names)copy(asset('browser-harness/packages/'+dir+'/dist/'+name),'runtime/'+name,record.files['dist/'+name].sha256);
}
const snapshot=asset('model-cache/hub/models--cross-encoder--nli-MiniLM2-L6-H768/snapshots/b95119ce93d3e065de6214e38cd4a97b0f2f2c6d/');
for(const name of ['tokenizer.json','tokenizer_config.json','config.json'])copy(path.join(snapshot,name),'runtime/'+name,prep.source_files[name].sha256);
copy('experiments/vera_validation/V13_nli_hypotheses_v0.1.0.json','runtime/hypotheses.json',phase6.source_model.hypotheses_sha256);
fs.copyFileSync('tools/verification/js-review/PYTHON-NOTICE.txt',path.join(out,'PYTHON-NOTICE.txt'));
fs.copyFileSync(asset('browser-harness/packages/tokenizers/LICENSE'),path.join(out,'TOKENIZERS-LICENSE.txt'));
const application=Object.fromEntries(fs.readdirSync('apps/gmail-extension/local').filter(n=>/\.(mjs|css|html)$/.test(n)).map(n=>{const bytes=fs.readFileSync(path.join(out,n));return[n,{sha256:hash(bytes),bytes:bytes.length}];}));
fs.writeFileSync(path.join(out,'asset-integrity.json'),JSON.stringify({model:phase6.source_model,assets:copied,application},null,2)+'\n');
console.log('LOCAL_ASSETS_PACKAGED',Object.values(copied).reduce((n,v)=>n+v.bytes,0),'bytes; no model weights included');
