import React, { useEffect, useRef, useState } from "react";
import ReactDOM from "react-dom/client";
import type { ArtifactDecision, EmailSourceMetadata } from "@phishing-defense/shared";
import { MockEmailSourceAdapter } from "./adapters/mockEmailSourceAdapter";
import type { ExtensionResult, RuntimeMessage } from "./messages";
import { ApiError, processEmail, analyzeSelectedArtifact } from "./services/api";
import { loadSettings, saveSettings, type ExtensionSettings } from "./services/settings";
import "./popup.css";

const defaultSettings: ExtensionSettings = { backendUrl: "http://127.0.0.1:8000", sourceMode: "mock", automaticTracking: false, includeLinks: false };

export function Popup() {
  const analysisStarted = useRef(false);
  const [settings, setSettings] = useState(defaultSettings);
  const [result, setResult] = useState<ExtensionResult | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "success" | "offline" | "error">("idle");
  const [message, setMessage] = useState("");
  const [notice, setNotice] = useState("");
  const [artifact, setArtifact] = useState<ArtifactDecision | null>(null);
  const [artifactBusy, setArtifactBusy] = useState(false);
  const [artifactError, setArtifactError] = useState("");
  const [artifactLanguage, setArtifactLanguage] = useState<"en" | "unknown">("unknown");
  useEffect(() => {
    void loadSettings().then(value => { if (!analysisStarted.current) setSettings(value); });
    if (typeof chrome !== "undefined" && chrome.storage) void chrome.storage.local.get("lastResult").then((stored) => {
      if (stored.lastResult && !analysisStarted.current) { setResult(stored.lastResult as ExtensionResult); setState("success"); }
    });
  }, []);

  async function onAnalyze() {
    if (settings.processingMode !== "legacy") { await chrome.runtime.sendMessage({ type: "OPEN_LOCAL" }); return; }
    analysisStarted.current = true;
    setArtifact(null); setArtifactError("");
    setState("loading"); setMessage(""); setNotice("");
    try {
      await saveSettings(settings);
      const email = settings.sourceMode === "mock" ? await new MockEmailSourceAdapter().extractCurrentEmail() : await currentGmailEmail();
      setResult(await submitEmail(email)); setState("success");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unexpected analysis error.");
      setState(error instanceof ApiError && error.offline ? "offline" : "error");
    }
  }

  async function updateSettings(next: ExtensionSettings) { analysisStarted.current=true; setArtifact(null); setResult(null); setArtifactError(""); setState("idle"); setSettings(next); await saveSettings(next); }

  async function onArtifact() {
    if (settings.processingMode !== "legacy") return;
    analysisStarted.current = true;
    setArtifact(null); setResult(null); setArtifactError(""); setArtifactBusy(true);
    try {
      await saveSettings(settings);
      const email = settings.sourceMode === "mock" ? await new MockEmailSourceAdapter().extractCurrentEmail() : await currentGmailEmail();
      setArtifact(await analyzeSelectedArtifact(settings.backendUrl, email, artifactLanguage, settings.includeLinks));
    } catch { setArtifactError("Artifact analysis unavailable. Review Required; no previous prediction is reused."); }
    finally { setArtifactBusy(false); }
  }

  return <main>
    <header><div className="mark">S</div><div><span className="eyebrow">EMAIL RISK ANALYSIS</span><h1>Sentinel prototype</h1></div></header>
    <label>Processing mode<select aria-label="Processing mode" value={settings.processingMode ?? "local"} onChange={e => void updateSettings({ ...settings, processingMode: e.target.value as "local" | "legacy", automaticTracking: false })}><option value="local">Local only (no uploads)</option><option value="legacy">Legacy research backend (uploads metadata)</option></select></label>
    {settings.processingMode !== "legacy" ? <section><h2>Local protection</h2><p>Basic rules work offline. Optional MiniLM runs only on this device after explicit consent and verified model installation. It cannot override rule labels.</p><button onClick={() => void chrome.runtime.sendMessage({ type: "OPEN_LOCAL" })}>Open Local protection</button></section> : <>
    <fieldset className="controls" disabled={artifactBusy || state === "loading"} style={{border:0,padding:0,margin:0}}>
      <label>Email source<select aria-label="Email source" value={settings.sourceMode} onChange={(event) => void updateSettings({ ...settings, sourceMode: event.target.value as "mock" | "gmail" })}><option value="mock">Mock demo</option><option value="gmail">Current Gmail message</option></select></label>
      <label>Backend URL<input aria-label="Backend URL" value={settings.backendUrl} onChange={(event) => setSettings({ ...settings, backendUrl: event.target.value })} /></label>
      <label className="toggle"><input type="checkbox" checked={settings.automaticTracking} disabled={settings.sourceMode !== "gmail"} onChange={(event) => void updateSettings({ ...settings, automaticTracking: event.target.checked })}/><span>Automatic tracking</span></label>
      <label className="toggle"><input type="checkbox" checked={settings.includeLinks} onChange={(event) => void updateSettings({ ...settings, includeLinks: event.target.checked })}/><span>Include links for URL rules</span></label>
      <p className="tracking">Tracking: <strong>{settings.sourceMode === "gmail" && settings.automaticTracking ? "Automatic for selected Gmail messages" : "Manual only"}</strong></p>
    </fieldset>
    <button className="primary" onClick={() => void onAnalyze()} disabled={artifactBusy || state === "loading"}>{state === "loading" ? "Analyzing…" : settings.sourceMode === "gmail" ? "Analyze Current Email" : "Analyze Test Email"}</button>
    <section aria-label="Thesis artifact analysis">
      <h2>Deterministic artifact analysis</h2>
      <label>Declared artifact language<select disabled={artifactBusy || state === "loading"} aria-label="Declared artifact language" value={artifactLanguage} onChange={e => { setArtifactLanguage(e.target.value as typeof artifactLanguage); setArtifact(null); }}><option value="unknown">Unknown / unsupported</option><option value="en">English</option></select></label>
      <p>Submit the selected subject and sender only; optional links follow your setting. No body or visit event is sent. Missing analytical components produce Review Required.</p>
      <button disabled={artifactBusy || state === "loading"} onClick={() => void onArtifact()}>{artifactBusy ? "Analyzing artifact…" : "Submit selected artifact"}</button>
      {artifactError && <p role="alert">{artifactError}</p>}
      {artifact && <section aria-label="Artifact result"><h3>{artifact.decision.tier.replaceAll("_", " ").toUpperCase()}</h3><p>{artifact.result_category === "synthetic_model_generated" ? "Synthetic model-generated; not research validated" : "Model not evaluated"}</p><p>{artifact.classification ?? "No definitive prediction"}</p>{artifact.calibrated_probability !== null && <p>Calibrated fixture probability: {(artifact.calibrated_probability * 100).toFixed(1)}%</p>}<details><summary>Behavioral evidence and attribution</summary><ul>{artifact.behavioral_evidence.map(i => <li key={i.indicator_id}>{i.indicator_id}: {i.state}{i.evidence.map((e, n) => <span key={n}> · {e.locators.map(l => `${l.field}[${l.start}:${l.end}]`).join(", ")}</span>)}</li>)}</ul><p>Model attribution (separate from evidence): {artifact.attribution?.method ?? "unavailable"}</p>{artifact.attribution && <ul>{artifact.attribution.features.slice(0, 5).map(f => <li key={f.feature}>{f.feature}: {f.contribution.toPrecision(3)}</li>)}</ul>}</details><ul>{artifact.decision.actions.map(a => <li key={a}>{a}</li>)}</ul><p>{artifact.limitations.join(" ")}</p><small>Run: {artifact.run_id} · {artifact.versions.selected_model ?? "no selected model"}</small></section>}
    </section>
    {state === "idle" && <p className="hint">Gmail mode reads only the selected message. Email bodies are disabled and never collected by this build.</p>}
    {(state === "offline" || state === "error") && <div role="alert" className="alert"><strong>{state === "offline" ? "Backend offline" : "Analysis unavailable"}</strong><p>{message}</p></div>}
    {result && state === "success" && <ResultCard result={result} onReport={() => setNotice("Use Gmail’s More menu → Report phishing. Sentinel has not sent a report or message content.")} />}
    {notice && <p className="notice" role="status">{notice}</p>}
    </>}
    <details><summary>Privacy notice</summary><p>Sentinel reads only the selected message’s identifier, sender, domain, subject, and timestamp. Links are optional. Bodies, attachments, credentials, tokens, contacts, and unrelated inbox messages are excluded.</p></details>
  </main>;
}

function ResultCard({ result, onReport }: { result: ExtensionResult; onReport: () => void }) {
  const { trackedEmail, analysis } = result;
  return <section className="result">
    <Row label="Sender" value={trackedEmail.senderEmail} /><Row label="Sender domain" value={trackedEmail.senderEmail.split("@")[1] ?? "Unknown"}/>
    <Row label="Times Opened" value={String(trackedEmail.visitCount)} testId="visit-count" />
    <div className="score"><span>Prototype Email Risk Score</span><strong className={`risk ${analysis.riskLevel}`}>{analysis.emailRiskScore}% — {title(analysis.riskLevel)} Risk</strong><small>Source: {analysis.scoreSource}</small></div>
    <div className="behaviors"><span>Detected behaviors</span>{analysis.detectedBehaviors.length ? <ul>{analysis.detectedBehaviors.map((item) => <li key={`${item.type}-${item.evidence}`}><strong>{item.type.replaceAll("_", " ")}</strong><small>{Math.round(item.confidence * 100)}% · {item.evidence}</small></li>)}</ul> : <p>No strong prototype indicators detected.</p>}</div>
    <p className="recommendation">{analysis.recommendation}</p>
    <p className="disclaimer">Rule-based prototype result—not a trained ML prediction. Times opened is separate from email risk.</p>
    <div className="actions"><button onClick={() => void openDashboard()}>View in Dashboard</button><button onClick={onReport}>Report Email</button></div>
  </section>;
}

async function currentGmailEmail(): Promise<EmailSourceMetadata> {
  if (typeof chrome === "undefined" || !chrome.tabs) throw new Error("Gmail analysis is available only in the installed extension.");
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id || !tab.url?.startsWith("https://mail.google.com/")) throw new Error("Open and select a Gmail message, then try again.");
  try {
    const ping = await chrome.tabs.sendMessage(tab.id, { type: "PING_CONTENT_SCRIPT" } satisfies RuntimeMessage);
    if (!ping?.ok || ping.source !== "sentinel-content-script") throw new Error("Unexpected ping response");
  } catch {
    throw new Error("Sentinel could not load on this Gmail tab. Reload Gmail and try again.");
  }
  const response = await chrome.tabs.sendMessage(tab.id, { type: "GET_CURRENT_EMAIL" } satisfies RuntimeMessage);
  if (!response?.ok) throw new Error(response?.error ?? "Gmail metadata is unavailable.");
  return response.email as EmailSourceMetadata;
}

async function submitEmail(email: EmailSourceMetadata): Promise<ExtensionResult> {
  if (typeof chrome !== "undefined" && chrome.runtime?.sendMessage) {
    const response = await chrome.runtime.sendMessage({ type: "PROCESS_EMAIL", email } satisfies RuntimeMessage);
    if (!response?.ok) throw new Error(response?.error ?? "Analysis unavailable.");
    return response.result as ExtensionResult;
  }
  const settings = await loadSettings();
  return processEmail(settings.backendUrl, email, { includeLinks: settings.includeLinks });
}
async function openDashboard() { if (typeof chrome !== "undefined" && chrome.tabs) await chrome.tabs.create({ url: "http://localhost:5173" }); }
function Row({ label, value, testId }: { label: string; value: string; testId?: string }) { return <div className="row"><span>{label}</span><strong data-testid={testId}>{value}</strong></div>; }
function title(value: string) { return value.charAt(0).toUpperCase() + value.slice(1); }
if (document.getElementById("root")) ReactDOM.createRoot(document.getElementById("root")!).render(<React.StrictMode><Popup /></React.StrictMode>);
