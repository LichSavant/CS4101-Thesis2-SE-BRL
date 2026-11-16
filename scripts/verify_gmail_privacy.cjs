/* Supplemental no-install fixture verification using an explicitly supplied,
 * already installed TypeScript compiler. Does not replace Vitest/typecheck/build.
 * Usage: node scripts/verify_gmail_privacy.cjs /absolute/path/to/typescript.js
 * Runs actual extension modules in a VM with synthetic DOM, storage and fetch.
 */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
if (!process.argv[2]) {
  console.error("Usage: node scripts/verify_gmail_privacy.cjs /absolute/path/to/existing/typescript.js (no installation performed)");
  process.exit(2);
}
const ts = require(path.resolve(process.argv[2]));
const root = path.resolve(__dirname, "..");
const completed = [];

function runtime(includeLinks = false) {
  const elements = new Map();
  let bodyReads = 0, linkReads = 0;
  const sent = [], requests = [];
  class Element {
    constructor(tag = "div") { this.tag = tag; this.children = []; this.hidden = false; this.attributes = {}; this.textContent = ""; }
    setAttribute(key, value) { this.attributes[key] = value; }
    getAttribute(key) { return this.attributes[key] ?? null; }
    append(...children) { for (const child of children) { this.children.push(child); if (child.id) elements.set(child.id, child); child.parentElement = this; } }
    insertBefore(child) { this.append(child); }
    remove() { elements.delete(this.id); }
    contains(child) { return this.children.includes(child); }
    querySelector() { return null; }
    querySelectorAll() { return []; }
    closest() { return null; }
    get lastChild() { return this.children.at(-1); }
  }
  class Button extends Element {}
  const body = new Element("main"), head = new Element("head"), actions = new Element();
  const subject = new Element("h2"); subject.textContent = "Metadata-only fixture";
  function makeMessage(id, email, link) {
    const sender = new Element(); sender.setAttribute("name", "Fixture"); sender.setAttribute("email", email);
    const message = new Element(); message.setAttribute("data-legacy-message-id", id);
    const privateBody = new Element();
    Object.defineProperty(privateBody, "innerText", { get() { bodyReads++; throw new Error("Unauthorized fixture body read"); } });
    message.querySelector = selector => selector === ".a3s" ? privateBody : selector.includes("email") ? sender : null;
    message.querySelectorAll = selector => { if (selector === ".a3s a[href]") { linkReads++; return [{ href: link }]; } return []; };
    return message;
  }
  const messages = [makeMessage("fixture:privacy", "sender@example.test", "https://example.test/opt-in")];
  const document = {
    body, head, defaultView: { location: { hash: "#inbox/fixture" } },
    getElementById: id => elements.get(id) ?? null,
    querySelectorAll: selector => selector.includes("data-legacy-message-id") ? messages : [],
    querySelector: selector => selector === "main" ? body : selector.includes(".amn") ? actions : selector.includes("h2") ? subject : null,
    createElement: tag => tag === "button" ? new Button(tag) : new Element(tag),
    createElementNS: (_, tag) => new Element(tag),
    createTextNode: text => ({ textContent: text })
  };
  const context = vm.createContext({
    document, HTMLElement: Element, HTMLButtonElement: Button, URL, Date, console,
    window: { setTimeout: () => 0, clearTimeout() {}, addEventListener() {} },
    MutationObserver: class { observe() {} disconnect() {} },
    chrome: {
      storage: { local: { get: async () => ({ includeLinks, automaticTracking: false, sourceMode: "gmail" }), set: async () => {} } },
      runtime: { onMessage: { addListener() {} }, sendMessage: async message => { sent.push(message); return { ok: false, error: "Fixture stops after metadata transmission" }; } }
    },
    fetch: async (url, options) => { requests.push({ url, body: JSON.parse(options.body) }); return { ok: true, json: async () => ({}) }; }
  });
  const cache = new Map();
  function load(filename) {
    filename = path.resolve(filename);
    if (cache.has(filename)) return cache.get(filename).exports;
    const module = { exports: {} }; cache.set(filename, module);
    // Vite environment substitution only; application logic is not rewritten.
    const source = fs.readFileSync(filename, "utf8").replaceAll("import.meta.env.VITE_API_BASE_URL", "undefined");
    const result = ts.transpileModule(source, { fileName: filename, reportDiagnostics: true, compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS } });
    const errors = (result.diagnostics ?? []).filter(item => item.category === ts.DiagnosticCategory.Error);
    assert.equal(errors.length, 0, "Supplemental TypeScript syntax diagnostics");
    const compiled = new vm.Script(`(function(require,module,exports){${result.outputText}\n})`, { filename });
    compiled.runInContext(context)(name => {
      if (name === "@phishing-defense/shared") return load(path.join(root, "packages/shared/src/index.ts"));
      if (name.startsWith(".")) return load(path.resolve(path.dirname(filename), name + ".ts"));
      throw new Error("Unexpected dependency in fixture: " + name);
    }, module, module.exports);
    return module.exports;
  }
  return { load, document, elements, sent, requests, messages, makeMessage, counts: () => ({ bodyReads, linkReads }) };
}

const fixtureEmail = {
  userId: "fixture", messageId: "fixture:1", senderEmail: "sender@example.test", senderName: "Fixture",
  senderDomain: "example.test", subject: "Metadata", openedAt: "2026-11-13T00:00:00Z",
  bodyText: "PRIVATE BODY", session: "PRIVATE EXTRA", links: ["https://example.test/opt-in"]
};

async function main() {
  let env = runtime();
  let api = env.load(path.join(root, "apps/gmail-extension/src/services/api.ts"));
  await api.processEmail("http://127.0.0.1:8000", fixtureEmail);
  assert.equal(env.requests.length, 2);
  assert.equal(JSON.stringify(env.requests).includes("PRIVATE"), false);
  assert.deepEqual(JSON.parse(JSON.stringify(env.requests[1].body.links)), []);
  assert.equal(env.requests[1].body.bodyCollectionAuthorized, false);
  completed.push("API projects both payloads, strips body/extra data, and defaults links off");
  env = runtime(); api = env.load(path.join(root, "apps/gmail-extension/src/services/api.ts"));
  await api.processEmail("http://127.0.0.1:8000", fixtureEmail, { includeLinks: true });
  assert.equal(env.requests[1].body.links.length, 1);
  completed.push("API preserves explicitly opted-in links");
  env = runtime();
  const { GmailEmailSourceAdapter } = env.load(path.join(root, "apps/gmail-extension/src/adapters/gmailEmailSourceAdapter.ts"));
  const result = await new GmailEmailSourceAdapter(env.document, { includeBody: true, bodyAuthorized: true }).extractCurrentEmail();
  assert.equal(result.bodyText, undefined); assert.equal(result.links, undefined);
  assert.deepEqual(env.counts(), { bodyReads: 0, linkReads: 0 });
  completed.push("Adapter ignores stale body authorization flags without reading body");
  const selected = env.makeMessage("fixture:selected", "selected@example.test", "https://selected.example.test/");
  const hidden = env.makeMessage("fixture:hidden", "hidden@example.test", "https://hidden.example.test/");
  hidden.hidden = true;
  env.messages.push(selected, hidden);
  const selectedResult = await new GmailEmailSourceAdapter(env.document, { includeLinks: true }).extractCurrentEmail();
  assert.equal(selectedResult.messageId, "fixture:selected");
  assert.equal(selectedResult.senderEmail, "selected@example.test");
  assert.deepEqual(JSON.parse(JSON.stringify(selectedResult.links)), ["https://selected.example.test/"]);
  assert.equal(env.counts().bodyReads, 0);
  completed.push("Selected-message adapter excludes older and hidden-message metadata and links");
  env = runtime();
  const { MockEmailSourceAdapter } = env.load(path.join(root, "apps/gmail-extension/src/adapters/mockEmailSourceAdapter.ts"));
  const mockEmail = await new MockEmailSourceAdapter().extractCurrentEmail();
  assert.equal(mockEmail.messageId, "demo-message-001"); assert.equal(mockEmail.bodyText, undefined);
  api = env.load(path.join(root, "apps/gmail-extension/src/services/api.ts"));
  await api.processEmail("http://127.0.0.1:8000", mockEmail);
  assert.equal(env.requests.length, 2); assert.equal(env.requests[1].body.bodyCollectionAuthorized, false);
  assert.ok(env.requests.every(item => !("bodyText" in item.body)));
  completed.push("Existing mock adapter remains usable through the metadata-only API path");
  for (const includeLinks of [false, true]) {
    env = runtime(includeLinks);
    env.load(path.join(root, "apps/gmail-extension/src/content.ts"));
    await new Promise(resolve => setImmediate(resolve));
    assert.deepEqual(env.counts(), { bodyReads: 0, linkReads: 0 });
    const button = env.elements.get("sentinel-scan-button"); assert.ok(button, "Scan button injected");
    button.onclick();
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(env.sent.length, 1); assert.equal(env.sent[0].type, "PROCESS_EMAIL");
    assert.equal(env.sent[0].email.bodyText, undefined);
    assert.equal(env.counts().bodyReads, 0); assert.equal(env.counts().linkReads, includeLinks ? 1 : 0);
    assert.equal((env.sent[0].email.links ?? []).length, includeLinks ? 1 : 0);
    completed.push(`Actual content initialization and manual scan preserve consent (links=${includeLinks})`);
  }
  console.log(JSON.stringify({ mode: "supplemental_synthetic_VM_checks", compiler_version: ts.version, passed: completed.length, checks: completed, full_typecheck: false, vitest_executed: false, build_executed: false, real_Gmail_accessed: false }, null, 2));
}
main().catch(error => { console.error(error); process.exitCode = 1; });
