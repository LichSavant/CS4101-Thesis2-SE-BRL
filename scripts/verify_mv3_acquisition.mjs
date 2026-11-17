// Loaded-extension UI and activeTab tests. Every visited webpage is synthesized
// by routing; no actual Gmail, webpage, account, cookies or user content is used.
import fs from 'node:fs';import path from 'node:path';import {createRequire} from 'node:module';
const root=process.cwd(),require=createRequire(import.meta.url),{chromium}=require(path.join(root,'.venv-transformer/browser-harness/tools/playwright-core'));
const output=path.join(root,'.venv-transformer/mv3-verification');fs.mkdirSync(output,{recursive:true});process.env.TEMP=process.env.TMP=process.env.TMPDIR=output;
const tests=[],outbound=[],report={status:'FAIL',tests,outbound};let context;
const check=(name,value)=>{tests.push({name,pass:!!value});if(!value)throw Error(name);};
try{
  fs.writeFileSync('apps/gmail-extension/dist/local/csp-probe.mjs',`globalThis.sebrlProbe={};addEventListener('securitypolicyviolation',e=>{if(e.violatedDirective.startsWith('connect-src'))sebrlProbe.connectViolation=true;});try{new Function('return 1')();sebrlProbe.evalBlocked=false;}catch{sebrlProbe.evalBlocked=true;}try{await fetch('http://127.0.0.1:8000/synthetic-private');sebrlProbe.network=false;}catch{sebrlProbe.network=true;}`);
  context=await chromium.launchPersistentContext(path.join(output,'acquisition-'+Date.now()),{executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',chromiumSandbox:true,headless:true,ignoreDefaultArgs:['--disable-extensions'],args:['--enable-automation','--enable-unsafe-extension-debugging','--disable-background-networking','--disable-sync','--no-first-run']});
  const cdp=await context.browser().newBrowserCDPSession();const {id}=await cdp.send('Extensions.loadUnpacked',{path:path.join(root,'apps/gmail-extension/dist')});
  const fixtures=new Map([
    ['https://mail.google.com/mail/u/0/', '<main><h2 class="hP">Act now.</h2><div class="amn"></div><div data-legacy-message-id="synthetic-selected"><span email="sender@example.test">Sender</span><div class="a3s">PRIVATE_SYNTHETIC_BODY<form><input value="PRIVATE_SYNTHETIC_INPUT"></form></div></div></main>'],
    ['https://synthetic.example.test/page','<title>Notice</title><main><p>Act now. Submit your password.</p><form>PRIVATE_SYNTHETIC_FORM<input value="PRIVATE_SYNTHETIC_INPUT"></form><div contenteditable>PRIVATE_SYNTHETIC_EDIT</div></main>'],
    ['https://revoked.example.test/page','<p>Act now.</p>']]);
  await context.route('**/*',route=>{const url=route.request().url();if(url.startsWith('chrome-extension://'))return route.continue();if(fixtures.has(url))return route.fulfill({contentType:'text/html',body:fixtures.get(url)});outbound.push({url,method:route.request().method()});return route.abort();});
  const local=await context.newPage();await local.goto(`chrome-extension://${id}/local/local.html`);await local.waitForFunction(()=>document.querySelector('#model-status').textContent.includes('No model'));
  await local.locator('#language').selectOption('en');await local.locator('#consent').check();
  await local.evaluate(async()=>{const {call}=await import('./client.mjs');await call('status');});
  const duplicate=await context.newPage();await duplicate.goto(`chrome-extension://${id}/local/local.html`);await duplicate.waitForFunction(()=>document.querySelector('#model-status').textContent.includes('No backend fallback'));check('second workspace cannot acquire a second model worker',true);await duplicate.close();
  const invalidScores=await local.evaluate(async()=>{const {reviewRecord,validateReview,predictorValues}=await import('./review/review.mjs');const r={record_id:'synthetic',source_dataset:'synthetic',modality:'content_bearing_email',artifact_input:{kind:'email',subject:'Act now.'},fields_available:['subject'],content_available:true,provenance:{reference:'synthetic'}};const bad=await reviewRecord(r,{scorer:{score(){return[{entailment:NaN,neutral:0,contradiction:0}].flatMap(x=>[x,x,x]);}}});return bad.indicators.every(row=>row.semantic_candidates.length===0)&&bad.indicators[0].failure_codes.includes('semantic_failed');});check('malformed semantic scores abstain without label promotion',invalidScores);
  async function target(url){const page=await context.newPage();await page.goto(url);await page.bringToFront();const targets=await cdp.send('Target.getTargets',{filter:[{type:'tab',exclude:false}]});const tab=targets.targetInfos.find(t=>t.url===url);if(!tab)throw Error('Synthetic tab target unavailable: '+JSON.stringify(targets));await cdp.send('Extensions.triggerAction',{id,targetId:tab.targetId});await local.evaluate(()=>chrome.runtime.sendMessage({type:'OPEN_LOCAL'}));await local.bringToFront();return page;}
  const gmail=await target('https://mail.google.com/mail/u/0/');await local.locator('#gmail').click();await local.waitForFunction(()=>document.querySelector('#status').textContent.includes('Local analysis complete'));
  check('Gmail selected metadata only',!(await local.locator('#result').innerText()).includes('PRIVATE_')&&(await local.locator('#result li').count())===12);
  const web=await target('https://synthetic.example.test/page');await local.locator('#webpage').click();await local.waitForFunction(()=>document.querySelector('#status').textContent.includes('Local analysis complete'));
  check('authorized activeTab webpage capture excludes forms/editable/input',!(await local.locator('#result').innerText()).includes('PRIVATE_')&&(await local.locator('#result').innerText()).includes('call_to_action'));
  await local.locator('#url').click();await local.waitForFunction(()=>document.querySelector('#status').textContent.includes('Local analysis complete'));
  check('URL modality has twelve unavailable content indicators',(await local.locator('#result').innerText()).match(/unavailable/g)?.length>=12);
  // Navigation revokes the temporary host grant. No new action is invoked.
  await web.goto('https://revoked.example.test/page');await local.bringToFront();await local.locator('#webpage').click();await local.waitForFunction(()=>document.querySelector('#status').textContent.includes('unavailable'));
  check('activeTab revocation fails closed',(await local.locator('#status').innerText()).includes('unavailable'));check('failed new capture clears prior artifact evidence',await local.locator('#result li').count()===0);
  // Execute a normal packaged module, not Runtime.evaluate's privileged eval,
  // which explicitly bypasses unsafe-eval CSP for debugger expressions.
  await local.evaluate(()=>{const s=document.createElement('script');s.type='module';s.src='./csp-probe.mjs';document.body.append(s);});await local.waitForFunction(()=>globalThis.sebrlProbe?.network===true&&globalThis.sebrlProbe?.connectViolation===true);
  const csp=await local.evaluate(()=>globalThis.sebrlProbe);check('local-page CSP blocks backend and eval',csp.network&&csp.evalBlocked&&csp.connectViolation);
  await local.locator('#consent').uncheck();await local.locator('#gmail').click();check('no Gmail acquisition without consent',(await local.locator('#status').innerText()).includes('authorize'));
  check('zero unauthorized outbound content requests',outbound.length===0);
  report.status='PASS';
}catch(e){report.error=String(e);console.error(e);}finally{await context?.close();fs.rmSync('apps/gmail-extension/dist/local/csp-probe.mjs',{force:true});fs.writeFileSync(path.join(output,'acquisition-result.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));if(report.status!=='PASS')process.exitCode=1;}
