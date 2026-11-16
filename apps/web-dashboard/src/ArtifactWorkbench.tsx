import { useState } from "react";
import { artifactSchemaVersion, type ArtifactDecision, type ArtifactSubmission } from "@phishing-defense/shared";
import { submitArtifact } from "./api";

export function ArtifactWorkbench() {
  const [mode, setMode] = useState("email");
  const [text, setText] = useState("");
  const [subject, setSubject] = useState("");
  const [pageUrl, setPageUrl] = useState("");
  const [technicalDataset, setTechnicalDataset] = useState("UCI");
  const [language, setLanguage] = useState<"en" | "unknown">("unknown");
  const [authorized, setAuthorized] = useState(false);
  const [bodyConsent, setBodyConsent] = useState(false);
  const [linksConsent, setLinksConsent] = useState(false);
  const [state, setState] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [result, setResult] = useState<ArtifactDecision | null>(null);
  const [error, setError] = useState("");
  function reset() { setResult(null); setState("idle"); setError(""); }
  async function analyze(event: React.FormEvent) {
    event.preventDefault(); setResult(null); setError(""); setState("loading");
    try {
      let artifact: Record<string, unknown>;
      if (mode === "email") {
        artifact = { kind: "email", subject };
        if (text) {
          if (!bodyConsent) throw new Error("Email body submission requires explicit body authorization.");
          Object.assign(artifact, { body: text, body_collection_authorized: true, study_purpose: "Explicit artifact analysis requested by the submitting user" });
        }
      } else if (mode === "web_text" || mode === "web_html") {
        artifact = { kind: "webpage", [mode === "web_html" ? "html" : "visible_text"]: text };
        if (pageUrl) artifact.page_url = pageUrl;
      } else if (mode === "url") artifact = { kind: "url", url: text };
      else artifact = { kind: "technical", dataset: technicalDataset, features: JSON.parse(text) as unknown };
      if (linksConsent) artifact.link_extraction_authorized = true;
      const request: ArtifactSubmission = { schema_version: artifactSchemaVersion, artifact, language,
        submission_authorized: authorized, retain_metadata: false };
      setResult(await submitArtifact(request)); setState("ready");
    } catch (e) { setResult(null); setError(e instanceof Error ? e.message : "Analysis unavailable. Review Required."); setState("error"); }
  }
  return <section className="panel artifact-workbench" aria-label="Artifact analysis">
    <h2>Artifact analysis</h2><p>Phase 1 supports email only. Submit one email explicitly. Content is processed without crawling and is not retained by this form. Results identify synthetic models or unavailable components.</p>
    <form onSubmit={event => void analyze(event)}>
      <fieldset disabled={state === "loading"}>
      <label>Artifact mode <select aria-label="Artifact mode" value={mode} disabled={state === "loading"} onChange={e => { setMode(e.target.value); setText(""); setSubject(""); setPageUrl(""); setBodyConsent(false); reset(); }}>
        <option value="email">Email</option>
      </select></label>
      {mode === "email" && <label>Subject <input aria-label="Artifact subject" maxLength={200000} value={subject} onChange={e => { setSubject(e.target.value); reset(); }}/></label>}
      <label>{mode === "email" ? "Optional email body" : mode === "url" ? "URL" : mode === "technical" ? "Engineered feature JSON" : "Archived content"}<textarea aria-label="Artifact content" maxLength={200000} value={text} onChange={e => { setText(e.target.value); reset(); }}/></label>
      {mode.startsWith("web_") && <label>Optional archived page URL <input aria-label="Archived page URL" value={pageUrl} onChange={e => { setPageUrl(e.target.value); reset(); }}/></label>}
      {mode === "technical" && <label>Source-specific technical branch <select aria-label="Technical branch" value={technicalDataset} onChange={e => {setTechnicalDataset(e.target.value);reset();}}><option value="UCI">U1-UCI</option><option value="PhiUSIIL">U1-Ph</option></select></label>}
      <label>Declared language <select aria-label="Declared language" value={language} onChange={e => { setLanguage(e.target.value as typeof language); reset(); }}><option value="unknown">Unknown / unsupported</option><option value="en">English</option></select></label>
      {mode === "email" && <label><input type="checkbox" checked={bodyConsent} onChange={e => { setBodyConsent(e.target.checked); reset(); }}/> I authorize this body for the stated artifact analysis</label>}
      <label><input type="checkbox" checked={linksConsent} onChange={e => { setLinksConsent(e.target.checked); reset(); }}/> Allow extracting links from this submitted artifact</label>
      <label><input type="checkbox" checked={authorized} onChange={e => { setAuthorized(e.target.checked); reset(); }}/> I authorize analysis of these submitted fields</label>
      <button type="submit" disabled={!authorized || state === "loading"}>{state === "loading" ? "Analyzing artifact…" : "Submit artifact"}</button>
      </fieldset>
    </form>
    {state === "loading" && <p role="status">Analysis in progress. No previous result is displayed.</p>}
    {state === "error" && <p role="alert">Review Required: {error}</p>}
    {result && <ArtifactResult result={result}/>}
  </section>;
}

export function ArtifactResult({ result }: { result: ArtifactDecision }) {
  return <section aria-label="Artifact decision" aria-live="polite" className={`artifact-result ${result.decision.tier}`}>
    <h3>{result.decision.tier.replaceAll("_", " ").toUpperCase()}</h3>
    <p>{result.result_category === "synthetic_model_generated" ? "Synthetic model-generated result — not a validated research prediction" : "Analytical model not evaluated"}</p>
    <h4>Prediction and calibration</h4><p>{result.classification ?? "No definitive prediction"}{result.calibrated_probability !== null && ` · Calibrated fixture probability: ${(result.calibrated_probability * 100).toFixed(1)}%`}</p>
    <h4>Technical evidence</h4>{result.technical_findings.length ? <ul>{result.technical_findings.map((f, i) => <li key={i}>{f.finding}: {f.value} ({f.family})</li>)}</ul> : <p>No technical finding established.</p>}
    <h4>Deterministic behavioral evidence</h4><ul>{result.behavioral_evidence.map(i => <li key={i.indicator_id}><strong>{i.indicator_id}</strong>: {i.state}{i.evidence.map((e, j) => <span key={j}> · {e.rule_id}: {e.locators.map(l => `${l.field}[${l.start}:${l.end}]`).join(", ")}</span>)}</li>)}</ul>
    <h4>Model attribution — influence, not artifact evidence</h4>{result.attribution ? <><p>{result.attribution.method} · {result.attribution.space}</p><ul>{result.attribution.features.map(f => <li key={f.feature}>{f.feature} · value {f.value.toPrecision(3)} · contribution {f.contribution.toPrecision(3)}</li>)}</ul><p>{result.attribution.calibration_note}</p></> : <p>Unavailable; no prior attribution is reused.</p>}
    <h4>Advisory response</h4><ul>{result.decision.actions.map(a => <li key={a}>{a}</li>)}</ul>
    <h4>Limitations</h4><ul>{[...result.limitations, ...result.decision.reasons].map((l, i) => <li key={i}>{l}</li>)}</ul>
    <details><summary>Versions and traceability</summary><p>Run {result.run_id} · artifact SHA-256 {result.artifact_sha256}</p><pre>{JSON.stringify(result.versions, null, 2)}</pre><p>Analysis latency: {result.timing_ms.analysis_end_to_end?.toFixed(2)} ms (server stages; excludes network/rendering)</p></details>
  </section>;
}
