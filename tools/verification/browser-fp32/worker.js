/* Isolated synthetic compatibility worker. Never used by the production extension. */
self.onmessage = async ({ data }) => {
  if (data.control) return;
  const policyViolations = [];
  const violation = event => policyViolations.push({ directive: event.violatedDirective, blocked: event.blockedURI });
  self.addEventListener('securitypolicyviolation', violation);
  try {
    if (data.mode === 'security-probe') {
      let rejected = false;
      try { await fetch('https://example.invalid/sebrl-denied-probe', { cache: 'no-store' }); }
      catch { rejected = true; }
      await new Promise(resolve => setTimeout(resolve, 30));
      self.postMessage({ ok: rejected && policyViolations.some(row => row.directive.startsWith('connect-src')),
        stage: 'security-probe', rejected, policyViolations });
      return;
    }
    const start = performance.now();
    const { Tokenizer } = await import('/packages/tokenizers/dist/tokenizers.mjs');
    const ort = await import('/packages/ort/dist/ort.wasm.min.mjs');
    ort.env.wasm.wasmPaths = '/packages/ort/dist/';
    ort.env.wasm.numThreads = 1;
    ort.env.wasm.proxy = false;
    importScripts('/packages/pyodide/pyodide.js');
    const bridgeStart = performance.now();
    const pyodide = await loadPyodide({ indexURL: '/packages/pyodide/', packages: [] });
    const bridgeMilliseconds = performance.now() - bridgeStart;
    const startup = { ortVersion: ort.env.versions.web,
      pythonVersion: pyodide.runPython('import platform; platform.python_version()'),
      tokenizerConstructor: typeof Tokenizer, bridgeMilliseconds,
      bridgeHeapBytes: pyodide._module?.HEAPU8?.byteLength ?? null,
      startupMilliseconds: performance.now() - start, crossOriginIsolated: self.crossOriginIsolated };
    if (data.mode === 'smoke') {
      self.postMessage({ ok: true, stage: 'package-smoke', ...startup, policyViolations });
      return;
    }
    const waitFor = name => new Promise(resolve => {
      const handler = ({ data }) => {
        if (data.control === name) { self.removeEventListener('message', handler); resolve(data); }
      };
      self.addEventListener('message', handler);
    });
    const progress = async (stage, detail = {}) => {
      const waiting = waitFor('continue');
      self.postMessage({ type: 'progress', stage, ...detail });
      await waiting;
    };
    const input = await (await fetch('/data/input.json')).json();
    for (const file of input.python_sources) {
      const bytes = Uint8Array.from(atob(file.base64), character => character.charCodeAt(0));
      const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), x => x.toString(16).padStart(2, '0')).join('');
      if (digest !== file.sha256) throw Error(`Python source integrity failed: ${file.path}`);
      const filename = '/repo/' + file.path;
      pyodide.FS.mkdirTree(filename.slice(0, filename.lastIndexOf('/')));
      pyodide.FS.writeFile(filename, bytes);
    }
    pyodide.globals.set('payload_json', JSON.stringify(input.payload));
    const sourceStart = performance.now();
    pyodide.runPython(`import sys, json
sys.path.insert(0, '/repo')
import bridge
payload = json.loads(payload_json)
requests = bridge.discover(payload)
`);
    const requests = JSON.parse(pyodide.runPython('json.dumps(requests, ensure_ascii=False)'));
    const sourceLoadMilliseconds = performance.now() - sourceStart;
    const [tokenizerJson, tokenizerConfig, modelConfig] = await Promise.all(
      ['tokenizer.json', 'tokenizer_config.json', 'config.json'].map(async name => (await fetch('/assets/' + name)).json()));
    if (JSON.stringify(modelConfig.id2label) !== JSON.stringify({ 0: 'contradiction', 1: 'entailment', 2: 'neutral' })) throw Error('NLI class ordering changed');
    const tokenizerStart = performance.now();
    const tokenizer = new Tokenizer(tokenizerJson, tokenizerConfig);
    const tokenized = requests.map(request => {
      const pairs = input.payload.hypotheses[request.indicator].map(hypothesis => tokenizer.encode(request.text, { text_pair: hypothesis, add_special_tokens: true }));
      const length = Math.max(...pairs.map(pair => pair.ids.length));
      return { ...request, input_ids: pairs.map(pair => [...pair.ids, ...Array(length - pair.ids.length).fill(1)]),
        attention_mask: pairs.map(pair => [...pair.attention_mask, ...Array(length - pair.ids.length).fill(0)]), oversized: length > 512 };
    });
    const tokenizerMilliseconds = performance.now() - tokenizerStart;
    const tokenApproval = waitFor('tokens-approved');
    self.postMessage({ type: 'tokens', tokenized });
    if (!(await tokenApproval).ok) throw Error('Tokenizer parity failed; model execution stopped');
    await progress('bridge-ready', { startup, sourceLoadMilliseconds, tokenizerMilliseconds,
      bridgeHeapBytes: pyodide._module?.HEAPU8?.byteLength ?? null });
    let modelBytes;
    const fetchStart = performance.now();
    modelBytes = new Uint8Array(await (await fetch('/model.onnx')).arrayBuffer());
    const modelFetchMilliseconds = performance.now() - fetchStart;
    const hashStart = performance.now();
    const modelHash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', modelBytes)), x => x.toString(16).padStart(2, '0')).join('');
    if (modelHash !== input.onnx_sha256 || modelBytes.length !== input.onnx_bytes) throw Error('Model integrity failed before loading');
    const modelHashMilliseconds = performance.now() - hashStart;
    const modelStart = performance.now();
    const session = await ort.InferenceSession.create(modelBytes, { executionProviders: ['wasm'], graphOptimizationLevel: 'all' });
    const modelInitializationMilliseconds = performance.now() - modelStart;
    modelBytes = null;
    if (JSON.stringify(session.inputNames) !== JSON.stringify(['input_ids', 'attention_mask']) || JSON.stringify(session.outputNames) !== JSON.stringify(['logits'])) throw Error('Unexpected ONNX input/output contract');
    await progress('ready-for-analysis', { modelInitializationMilliseconds, modelFetchMilliseconds,
      modelHashMilliseconds, modelHash, packageStartup: startup });
    const scored = [], timings = [];
    const browserOfflineDuringAnalysis = self.navigator.onLine === false;
    if (!browserOfflineDuringAnalysis) throw Error('Browser was not switched offline before analysis');
    const analysisStart = performance.now();
    for (const item of tokenized) {
      if (item.oversized) { scored.push({ ...item, scores: null, logits: null }); continue; }
      const shape = [3, item.input_ids[0].length];
      const inputs = { input_ids: new ort.Tensor('int64', BigInt64Array.from(item.input_ids.flat(), BigInt), shape),
        attention_mask: new ort.Tensor('int64', BigInt64Array.from(item.attention_mask.flat(), BigInt), shape) };
      const started = performance.now();
      const output = await session.run(inputs);
      timings.push(performance.now() - started);
      const logits = Array.from({ length: 3 }, (_, row) => Array.from(output.logits.data.slice(row * 3, row * 3 + 3)));
      if (logits.flat().some(value => !Number.isFinite(value))) throw Error('Non-finite browser logits');
      const scores = logits.map(row => {
        const maximum = Math.max(...row), exp = row.map(value => Math.exp(value - maximum));
        const sum = exp.reduce((a, b) => a + b, 0);
        return { contradiction: exp[0] / sum, entailment: exp[1] / sum, neutral: exp[2] / sum };
      });
      scored.push({ ...item, logits, scores });
      for (const tensor of Object.values(inputs)) tensor.dispose();
      output.logits.dispose();
      if (data.mode === 'lifecycle') break;
    }
    let outcomes = null, reviewMilliseconds = null;
    if (data.mode !== 'lifecycle') {
      pyodide.globals.set('scores_json', JSON.stringify(scored));
      const reviewStart = performance.now();
      outcomes = JSON.parse(pyodide.runPython('json.dumps(bridge.run_suite(payload, json.loads(scores_json)), ensure_ascii=False)'));
      reviewMilliseconds = performance.now() - reviewStart;
    }
    const analysisMilliseconds = performance.now() - analysisStart;
    await progress('analysis-complete', { analysisMilliseconds });
    await session.release();
    self.postMessage({ ok: true, stage: 'browser-inference', mode: data.mode, ...startup,
      sourceLoadMilliseconds, tokenizerMilliseconds, modelInitializationMilliseconds, modelFetchMilliseconds,
      modelHashMilliseconds, modelHash, scored, outcomes, inferenceMilliseconds: timings,
      reviewMilliseconds, analysisMilliseconds, bridgeHeapAfterReviewBytes: pyodide._module?.HEAPU8?.byteLength ?? null,
      wasmThreads: ort.env.wasm.numThreads, browserOfflineDuringAnalysis, policyViolations });
  } catch (error) {
    self.postMessage({ ok: false, stage: data.mode === 'smoke' ? 'package-smoke' : 'browser-inference', error: String(error), stack: error.stack, policyViolations });
  } finally {
    self.removeEventListener('securitypolicyviolation', violation);
  }
};
