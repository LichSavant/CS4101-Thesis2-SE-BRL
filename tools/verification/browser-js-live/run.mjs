// Real Chrome, local packaged assets, strict CSP. No npm/model/browser downloads.
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import os from 'node:os';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../../..');
const local = path.join(root, '.venv-transformer/browser-harness');
const pins = JSON.parse(fs.readFileSync(path.join(root, 'tools/verification/browser-fp32/packages.v1.json'), 'utf8'));
const packages = JSON.parse(fs.readFileSync(path.join(local, 'package-integrity.json'), 'utf8'));
fs.mkdirSync(path.join(local, 'tmp'), { recursive: true });
process.env.TEMP = process.env.TMP = process.env.TMPDIR = path.join(local, 'tmp');
const require = createRequire(import.meta.url);
const automation = path.join(local, 'tools/playwright-core');
if (!fs.existsSync(automation)) {
  const shared = path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node');
  const packageRoot = process.env.SEBRL_PLAYWRIGHT_CORE ?? path.dirname(require.resolve('playwright-core/package.json', { paths: [shared] }));
  fs.cpSync(packageRoot, automation, { recursive: true });
}
if (JSON.parse(fs.readFileSync(path.join(automation, 'package.json'), 'utf8')).version !== pins.playwright_core.version) {
  throw Error('Unexpected local Playwright version');
}
const { chromium } = require(path.join(automation, 'index.js'));
const hash = (data) => crypto.createHash('sha256').update(data).digest('hex');
const automationHashes = {};
function verifyAutomation(directory, relative = '') {
  for (const entry of fs.readdirSync(path.join(directory, relative), { withFileTypes: true })) {
    const name = path.join(relative, entry.name);
    if (entry.isDirectory()) verifyAutomation(directory, name);
    else if (entry.isFile()) {
      const copied = fs.readFileSync(path.join(automation, name));
      const relativeName = name.replaceAll('\\', '/');
      if (hash(copied) !== pins.playwright_core.asset_sha256[relativeName]) throw Error('Local automation copy changed: ' + name);
      automationHashes[relativeName] = hash(copied);
    }
  }
}
verifyAutomation(automation);
if (Object.keys(automationHashes).length !== Object.keys(pins.playwright_core.asset_sha256).length) throw Error('Incomplete pinned automation assets');
const browserExe = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
if (hash(fs.readFileSync(browserExe)) !== pins.chrome.executable_sha256) throw Error('Pinned local browser executable changed');
const served = new Map();
const parity = JSON.parse(fs.readFileSync(path.join(root, 'docs/research/js-review-parity.json'), 'utf8'));
for (const name of ['review.mjs', 'contracts.mjs', 'mailbox.mjs', 'python-url.mjs']) {
  const filename = path.join(root, 'tools/verification/js-review', name), bytes = fs.readFileSync(filename);
  if (hash(bytes) !== parity.provenance.source_sha256[name]) throw Error('Phase 7B runtime changed: ' + name);
  served.set('/review/' + name, { filename, sha256: hash(bytes), bytes: bytes.length });
}
for (const record of packages.packages.filter(p => p.name !== 'pyodide')) {
  const directory = { 'onnxruntime-web': 'ort', '@huggingface/tokenizers': 'tokenizers' }[record.name];
  const exact = { 'onnxruntime-web': '1.20.1', '@huggingface/tokenizers': '0.2.0' }[record.name];
  if (record.version !== exact) throw Error('Unexpected acquired package version');
  const approved = pins.approved_packages.find(item => item.name === record.name);
  if (!approved || approved.integrity !== record.integrity || approved.url !== record.url) throw Error('Acquired package differs from approved registry pin');
  for (const [name, expected] of Object.entries(record.files)) {
    const filename = path.join(local, 'packages', directory, name);
    const data = fs.readFileSync(filename);
    if (hash(data) !== expected.sha256 || data.length !== expected.bytes) throw Error(`Asset integrity failed: ${name}`);
    served.set(`/packages/${directory}/${name}`, { filename, ...expected });
  }
}
const mode = 'verify';
const reference = mode === 'verify' ? JSON.parse(fs.readFileSync(path.join(root, '.venv-transformer/onnx-tooling/browser-js-live/reference.json'), 'utf8')) : null;
const livePreparation = JSON.parse(fs.readFileSync(path.join(root, '.venv-transformer/onnx-tooling/browser-js-live/preparation.json'), 'utf8'));
if (hash(fs.readFileSync(path.join(root, '.venv-transformer/onnx-tooling/browser-js-live/reference.json'))) !== livePreparation.reference_sha256) throw Error('Fresh oracle integrity');
if (reference) {
  const model = path.join(root, '.venv-transformer/onnx-tooling/minilm-fp32.onnx');
  if (hash(fs.readFileSync(model)) !== reference.onnx_sha256) throw Error('Canonical ONNX integrity failed');
  served.set('/model.onnx', { filename: model, sha256: reference.onnx_sha256, bytes: reference.onnx_bytes });
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'tools/verification/pinned-minilm-files.json'), 'utf8'));
  const snapshot = path.join(root, '.venv-transformer/model-cache/hub/models--cross-encoder--nli-MiniLM2-L6-H768/snapshots', manifest.revision);
  const preparation = JSON.parse(fs.readFileSync(path.join(local, 'data/preparation.json'), 'utf8'));
  for (const name of ['config.json', 'tokenizer.json', 'tokenizer_config.json']) {
    const filename = path.join(snapshot, name), bytes = fs.readFileSync(filename);
    const expected = preparation.source_files[name];
    if (hash(bytes) !== expected.sha256 || bytes.length !== expected.size) throw Error('Tokenizer/config asset integrity failed');
    served.set('/assets/' + name, { filename, bytes: bytes.length, sha256: hash(bytes) });
  }
}
const csp = "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'";
const types = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.wasm': 'application/wasm', '.json': 'application/json', '.zip': 'application/zip' };
const localRequests = [];
const server = http.createServer((request, response) => {
  const pathname = new URL(request.url, 'http://127.0.0.1').pathname;
  response.setHeader('Content-Security-Policy', csp);
  response.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
  response.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
  response.setHeader('Cross-Origin-Resource-Policy', 'same-origin');
  response.setHeader('Cache-Control', 'no-store');
  if (request.method !== 'GET') { response.writeHead(405).end(); return; }
  localRequests.push(pathname);
  if (pathname === '/') {
    response.setHeader('Content-Type', 'text/html');
    response.end('<!doctype html><meta charset="utf-8"><title>SE-BRL isolated compatibility harness</title>');
    return;
  }
  if (pathname === '/data/input.json' && reference) {
    response.setHeader('Content-Type', 'application/json');
    // Never provide expected tokens, logits, scores or review outcomes to the worker.
    response.end(JSON.stringify({ payload: { ...reference.payload, consent: reference.payload.consent.map(c => c.request) },
      onnx_sha256: reference.onnx_sha256, onnx_bytes: reference.onnx_bytes }));
    return;
  }
  const asset = pathname === '/worker.js' ? { filename: path.join(here, 'worker.js') } : served.get(pathname);
  if (!asset) { response.writeHead(404).end(); return; }
  response.setHeader('Content-Type', types[path.extname(asset.filename)] ?? 'application/octet-stream');
  fs.createReadStream(asset.filename).pipe(response);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
let browser;
const externalRequests = [], violations = [], consoleErrors = [];
const progress = [], memories = [];
let analysisStartRequestIndex = null, analysisEndRequestIndex = null;
const stable = value => JSON.stringify(value, (_key, item) => item && typeof item === 'object' && !Array.isArray(item)
  ? Object.fromEntries(Object.keys(item).sort().map(key => [key, item[key]])) : item);
function compareTokens(actual, expected) {
  return actual.length === expected.length && actual.every((row, index) => {
    const gold = expected[index];
    return row.text === gold.text && row.indicator === gold.indicator && row.oversized === gold.oversized
      && stable(row.input_ids) === stable(gold.input_ids) && stable(row.attention_mask) === stable(gold.attention_mask);
  });
}
function compareOutputs(actual, expected) {
  const errors = [], logitErrors = [], probabilityErrors = [];
  if (actual.length !== expected.length) errors.push({ type: 'request_count', actual: actual.length, expected: expected.length });
  let tokenMatches = 0, decisionMatches = 0;
  for (let i = 0; i < actual.length; i++) {
    const row = actual[i], gold = expected[i];
    if (compareTokens([row], [gold])) tokenMatches++;
    else errors.push({ request: i, type: 'tokens_or_masks' });
    if (row.oversized) continue;
    for (let hypothesis = 0; hypothesis < 3; hypothesis++) {
      for (let label = 0; label < 3; label++) {
        const delta = Math.abs(row.logits[hypothesis][label] - gold.logits[hypothesis][label]);
        logitErrors.push(delta);
        if (delta > reference.tolerances.logits_atol + reference.tolerances.logits_rtol * Math.abs(gold.logits[hypothesis][label]))
          errors.push({ request: i, hypothesis, label, type: 'logit_tolerance', delta });
      }
      for (const label of ['contradiction', 'entailment', 'neutral']) {
        const delta = Math.abs(row.scores[hypothesis][label] - gold.scores[hypothesis][label]);
        probabilityErrors.push(delta);
        if (delta > reference.tolerances.probabilities_max_absolute_error)
          errors.push({ request: i, hypothesis, label, type: 'probability_tolerance', delta });
      }
      const maxima = scores => Object.keys(scores).filter(k => scores[k] === Math.max(...Object.values(scores))).sort();
      if (stable(maxima(row.scores[hypothesis])) === stable(maxima(gold.scores[hypothesis]))) decisionMatches++;
      else errors.push({ request: i, hypothesis, type: 'nli_decision', expected: gold.scores[hypothesis], actual: row.scores[hypothesis] });
    }
  }
  const stats = values => ({ maxAbsolute: Math.max(...values), meanAbsolute: values.reduce((a, b) => a + b, 0) / values.length, count: values.length });
  return { tokenMatches, decisionMatches, logitDeviation: stats(logitErrors), probabilityDeviation: stats(probabilityErrors), errors };
}
try {
  browser = await chromium.launch({ executablePath: browserExe,
    chromiumSandbox: true, headless: true,
    args: ['--enable-automation', '--disable-background-networking', '--disable-component-update', '--disable-sync', '--no-first-run'] });
  if (browser.version() !== pins.chrome.version) throw Error(`Browser version changed: ${browser.version()}`);
  const context = await browser.newContext({ serviceWorkers: 'block', bypassCSP: false });
  const browserCdp = await browser.newBrowserCDPSession();
  const launchArguments = (await browserCdp.send('Browser.getBrowserCommandLine')).arguments;
  if (launchArguments.some(arg => ['--no-sandbox', '--disable-web-security', '--ignore-certificate-errors'].includes(arg)))
    throw Error('Browser security restriction would require weakening; stopped');
  const nativeMemory = [];
  const observeNativeMemory = async stage => {
    const processes = (await browserCdp.send('SystemInfo.getProcessInfo')).processInfo;
    const ids = processes.map(p => Number(p.id)).filter(n => Number.isSafeInteger(n) && n > 0);
    if (!ids.length) return;
    try {
      const command = `Get-Process -Id ${ids.join(',')} -ErrorAction SilentlyContinue | Select-Object Id,WorkingSet64,PeakWorkingSet64,PrivateMemorySize64 | ConvertTo-Json -Compress`;
      const output = execFileSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', command],
        { encoding: 'utf8', windowsHide: true, timeout: 10000 });
      const rows = JSON.parse(output);
      const array = Array.isArray(rows) ? rows : [rows];
      nativeMemory.push({ stage, processes: array, residentBytes: array.reduce((n, p) => n + p.WorkingSet64, 0),
        peakWorkingSetUpperBoundBytes: array.reduce((n, p) => n + p.PeakWorkingSet64, 0),
        privateBytes: array.reduce((n, p) => n + p.PrivateMemorySize64, 0) });
    } catch (error) { nativeMemory.push({ stage, unavailable: String(error) }); }
  };
  await context.route('**/*', async route => {
    if (new URL(route.request().url()).origin === origin && route.request().method() === 'GET') await route.continue();
    else { externalRequests.push(route.request().url()); await route.abort('blockedbyclient'); }
  });
  const page = await context.newPage();
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  await page.goto(origin);
  await observeNativeMemory('empty-browser-before-worker');
  await page.exposeFunction('recordProgress', async (detail) => {
    progress.push(detail);
    if (detail.stage === 'ready-for-analysis') {
      await observeNativeMemory('model-ready-before-analysis');
      await context.setOffline(true);
      analysisStartRequestIndex = localRequests.length;
    }
    if (detail.stage === 'analysis-complete') {
      analysisEndRequestIndex = localRequests.length;
      await observeNativeMemory('analysis-complete-worker-alive');
      const measurement = await page.evaluate(async () => {
        const heap = performance.memory ? { usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize, scope: 'page JS heap only, not worker/native peak' } : null;
        if (typeof performance.measureUserAgentSpecificMemory !== 'function') return { heap, userAgentMemory: null };
        try {
          const memory = await Promise.race([performance.measureUserAgentSpecificMemory(),
            new Promise(resolve => setTimeout(() => resolve(null), 3000))]);
          return { heap, userAgentMemory: memory, scope: 'post-analysis agent memory snapshot; not a proven peak' };
        } catch (error) { return { heap, userAgentMemory: null, error: String(error) }; }
      });
      memories.push(measurement);
    }
    if (detail.stage === 'js-ready') await observeNativeMemory('js-tokenizer-before-model');
  });
  const cdp = await context.newCDPSession(page);
  await cdp.send('Network.enable');
  await page.evaluate(() => {
    globalThis.policyViolations = [];
    addEventListener('securitypolicyviolation', event => policyViolations.push({ directive: event.violatedDirective, blocked: event.blockedURI }));
  });
  const runWorker = async workerMode => page.evaluate(workerMode => new Promise(resolve => {
    const worker = new Worker('/worker.js');
    const timer = setTimeout(() => { worker.terminate(); resolve({ ok: false, error: 'Bounded browser verification timed out' }); }, 240000);
    worker.onmessage = async ({ data }) => {
      if (data.type === 'progress') {
        await recordProgress(data);
        worker.postMessage({ control: 'continue' });
      } else { clearTimeout(timer); worker.terminate(); resolve(data); }
    };
    worker.onerror = event => { clearTimeout(timer); worker.terminate(); resolve({ ok: false, error: event.message }); };
    worker.postMessage({ mode: workerMode });
  }), workerMode);
  const result = await runWorker(mode);
  violations.push(...await page.evaluate(() => policyViolations));
  const report = { stage: mode, ...result, browser: browser.version(), playwright: '1.62.1', csp,
    externalRequests, policyViolations: violations, consoleErrors, localRequests,
    noProductionExtensionChanges: true, pyodideRole: 'Not served or loaded; no Python runtime in browser', progress, memories,
    nativeMemory, browserSandboxEnabled: true,
    nativeMemoryScope: 'Only process IDs returned by the isolated Chrome instance; summed live working sets are snapshots. Sum of per-process lifetime peak working sets is an upper bound, not a simultaneous aggregate peak.' };
  if (mode === 'verify' && result.ok) {
    const comparison = compareOutputs(result.scored, reference.requests);
    const reviewCases = result.outcomes.cases.map((row, i) => ({ name: row.name,
      pass: row.name === reference.expected.cases[i].name && stable(row.outcome) === stable(reference.expected.cases[i].outcome) }));
    report.comparison = comparison;
    report.reviewCases = reviewCases;
    report.casesPassed = reviewCases.filter(row => row.pass).length;
    report.casesFailed = reviewCases.filter(row => !row.pass).length;
    report.analysisWithBrowserOffline = true;
    report.localRequestsDuringAnalysis = localRequests.slice(analysisStartRequestIndex, analysisEndRequestIndex);
    const timings = [...result.inferenceMilliseconds].sort((a, b) => a - b);
    report.latencyMilliseconds = { count: timings.length, median: timings[Math.floor(timings.length / 2)],
      p95: timings[Math.ceil(timings.length * 0.95) - 1], mean: timings.reduce((a, b) => a + b, 0) / timings.length,
      scope: 'actual WASM session.run for three pairs; tokenization excluded; includes boundary-length case' };
    report.status = comparison.errors.length || report.casesFailed || reviewCases.length !== reference.expected.cases.length || report.localRequestsDuringAnalysis.length
      || result.policyViolations.length ? 'FAIL' : 'PASS';
    report.preprocessingParity = stable(result.outcomes.preprocessing) === stable(reference.expected.preprocessing);
    report.consentParity = stable(result.consent) === stable(reference.payload.consent.map(c => c.accepted));
    report.pyodideFree = result.pyodideLoaded === false && !localRequests.some(p => p.startsWith('/packages/pyodide/') || p.endsWith('.py'));
    report.noExternalRequests = externalRequests.length === 0;
    const stats = rows => { const s=[...rows].sort((a,b)=>a-b);return {count:s.length,median:s[Math.floor(s.length/2)],p95:s[Math.ceil(s.length*.95)-1]}; };
    report.warmInferenceMilliseconds = stats(result.inferenceMilliseconds.slice(1));
    report.firstInferenceMilliseconds = result.inferenceMilliseconds[0];
    report.completeCaseLatencyMilliseconds = stats(result.caseLatencyMilliseconds.map(r=>r.milliseconds));
    const baseline = nativeMemory.find(m=>m.stage==='empty-browser-before-worker'),ready = nativeMemory.find(m=>m.stage==='model-ready-before-analysis');
    report.incrementalReadyResidentBytes = ready.residentBytes-baseline.residentBytes;
    if (!report.preprocessingParity || !report.consentParity || !report.pyodideFree) report.status = 'FAIL';
    report.assetStorage = { modelBytes: reference.onnx_bytes,
      packageBytes: Object.fromEntries(packages.packages.filter(p => p.name !== 'pyodide').map(p => [p.name, Object.values(p.files).reduce((n, f) => n + f.bytes, 0)])),
      usedPackageBytes: Object.fromEntries(['ort', 'tokenizers'].map(directory => [directory,
        [...new Set(localRequests.filter(name => name.startsWith(`/packages/${directory}/`)))].reduce((n, name) => n + (served.get(name)?.bytes ?? 0), 0)])) };
    report.assetStorage.reviewRuntimeBytes = [...served.entries()].filter(([name])=>name.startsWith('/review/')).reduce((n,[,asset])=>n+asset.bytes,0);
    report.assetStorage.tokenizerConfigBytes = [...served.entries()].filter(([name])=>name.startsWith('/assets/')).reduce((n,[,asset])=>n+asset.bytes,0);
    report.assetStorage.loadedAssetsBytes = [...new Set(localRequests)].reduce((n,name)=>n+(served.get(name)?.bytes??0),0);
    report.provenance = { modelSha256: reference.onnx_sha256, frozenFixtureSha256: reference.payload.frozen_fixture_sha256,
      referenceSha256: hash(fs.readFileSync(path.join(root, '.venv-transformer/onnx-tooling/browser-js-live/reference.json'))),
      runnerSha256: hash(fs.readFileSync(fileURLToPath(import.meta.url))), workerSha256: hash(fs.readFileSync(path.join(here, 'worker.js'))),
      automationAssetHashes: automationHashes,
      browserExecutableSha256: hash(fs.readFileSync(browserExe)),
      packagePinsSha256: hash(fs.readFileSync(path.join(root, 'tools/verification/browser-fp32/packages.v1.json'))),
      sourceHashes: parity.provenance.source_sha256,
      phase6RecordSha256: livePreparation.phase6_record_sha256, phase7BRecordSha256: livePreparation.phase7b_record_sha256,
      preparationSha256: hash(fs.readFileSync(path.join(root, '.venv-transformer/onnx-tooling/browser-js-live/preparation.json'))),
      tolerances: reference.tolerances, packageIntegrityRecord: hash(fs.readFileSync(path.join(local, 'package-integrity.json'))) };
  }
  if (!result.ok || externalRequests.length || violations.length || result.policyViolations?.length) report.status = 'FAIL';
  fs.writeFileSync(path.join(root, '.venv-transformer/onnx-tooling/browser-js-live/browser-result.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ status: report.status, ok: report.ok, error: report.error, casesPassed: report.casesPassed,
    casesFailed: report.casesFailed, comparison: report.comparison, latencyMilliseconds: report.latencyMilliseconds,
    modelInitializationMilliseconds: report.modelInitializationMilliseconds, workerLifecycle: report.workerLifecycle }));
  if (report.status === 'FAIL') process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
