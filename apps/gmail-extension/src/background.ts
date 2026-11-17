import type { EmailSourceMetadata } from "@phishing-defense/shared";
import type { ExtensionResult, RuntimeMessage } from "./messages";
import { processEmail, recordScanFeedback } from "./services/api";
import { loadSettings } from "./services/settings";

let lastResult: ExtensionResult | null = null;
let opening: Promise<chrome.tabs.Tab> | null = null;
async function localWorkspace() {
  const url = chrome.runtime.getURL("local/local.html");
  if (opening) return opening;
  opening = (async () => { const tabs = await chrome.tabs.query({ url }); const [source] = await chrome.tabs.query({active:true,currentWindow:true}); if(tabs[0]?.id){await chrome.runtime.sendMessage({type:"LOCAL_TARGET",tabId:source?.id}).catch(()=>null);return chrome.tabs.update(tabs[0].id,{active:true});}return chrome.tabs.create({ url, ...(source?.id ? {openerTabId:source.id} : {}) }); })();
  try { return await opening; } finally { opening = null; }
}

chrome.runtime.onMessage.addListener((message: RuntimeMessage, _sender, sendResponse) => {
  if (!["OPEN_LOCAL", "PROCESS_EMAIL", "GET_LAST_RESULT", "OPEN_SCAN_DASHBOARD", "RECORD_SCAN_FEEDBACK"].includes(message.type)) return false;
  if (message.type === "OPEN_LOCAL") { void localWorkspace().then(() => sendResponse({ ok: true })); return true; }
  // Every legacy handler is behind the same fail-closed mode gate, including
  // dashboard navigation, persisted results and feedback. Content stays transient.
  void (async () => {
    if ((await loadSettings()).processingMode !== "legacy") {
      if (message.type === "PROCESS_EMAIL") {
        const settings = await loadSettings(); const consent = await chrome.storage.local.get("localConsent");
        if (consent.localConsent !== true) throw new Error("Open Local protection and explicitly authorize analysis first.");
        await localWorkspace();
        // Acquisition remains metadata-only. Never forward stale body/private fields.
        const fields: Record<string, unknown> = { subject: message.email.subject, sender: message.email.senderEmail };
        if (settings.includeLinks) fields.urls = message.email.links ?? [];
        for (let attempt = 0; attempt < 30; attempt++) {
          const response = await chrome.runtime.sendMessage({ type: "LOCAL_SELECTED", fields, includeLinks: settings.includeLinks }).catch(() => null);
          if (response?.localAccepted) { sendResponse({ ok: true, local: true }); return; }
          await new Promise(resolve => setTimeout(resolve, 100));
        }
        throw new Error("Local workspace unavailable. Retry in the local workspace; no backend fallback.");
      }
      sendResponse(message.type === "GET_LAST_RESULT" ? { ok: true, result: null } : { ok: false, error: "Local-only mode blocks research network actions." }); return;
    }
    await legacyMessage(message, sendResponse);
  })().catch(error => sendResponse({ ok: false, error: error instanceof Error ? error.message : "Unavailable" }));
  return true;
});

async function legacyMessage(message: RuntimeMessage, sendResponse: (value: unknown) => void) {
  if (message.type === "GET_LAST_RESULT") { sendResponse({ ok: true, result: lastResult }); return false; }
  if (message.type === "OPEN_SCAN_DASHBOARD") {
    void chrome.tabs.create({ url: `http://localhost:5173/?scanId=${encodeURIComponent(message.scanId)}` });
    sendResponse({ ok: true }); return false;
  }
  if (message.type === "RECORD_SCAN_FEEDBACK") {
    void loadSettings().then((settings) => recordScanFeedback(settings.backendUrl, message.feedback))
      .then(() => sendResponse({ ok: true })).catch((error) => sendResponse({ ok: false, error: error instanceof Error ? error.message : "Feedback failed" }));
    return true;
  }
  if (message.type !== "PROCESS_EMAIL") return false;
  void handleEmail(message.email).then((result) => sendResponse({ ok: true, result })).catch((error) =>
    sendResponse({ ok: false, error: error instanceof Error ? error.message : "Analysis failed" }));
  return true;
}

async function handleEmail(email: EmailSourceMetadata): Promise<ExtensionResult> {
  const settings = await loadSettings();
  lastResult = await processEmail(settings.backendUrl, email, { includeLinks: settings.includeLinks });
  await chrome.storage.local.set({ lastResult });
  return lastResult;
}
