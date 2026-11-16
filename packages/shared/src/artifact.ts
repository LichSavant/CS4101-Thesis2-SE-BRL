/** Artifact-level thesis contract. Legacy scan/event contracts remain separate. */
export const artifactSchemaVersion = "artifact-decision-1.0" as const;
export interface EvidenceLocator { field: string; start: number; end: number; location: string }
export interface ArtifactSubmission {
  schema_version: typeof artifactSchemaVersion;
  artifact: Record<string, unknown>;
  language: "en" | "unknown";
  submission_authorized: boolean;
  retain_metadata: boolean;
}
export interface ArtifactDecision {
  schema_version: typeof artifactSchemaVersion;
  run_id: string;
  artifact_sha256: string;
  modality: string;
  status: "complete" | "review_required";
  result_category: "synthetic_model_generated" | "not_evaluated";
  research_validated: false;
  classification: "phishing" | "legitimate" | null;
  calibrated_probability: number | null;
  technical_findings: Array<{ finding: string; family: string; value: number; locators: EvidenceLocator[]; provenance: string }>;
  behavioral_evidence: Array<{ indicator_id: string; dimension_id: string; state: "supported" | "absent" | "unavailable" | "not_evaluated"; evaluation_status: string; evidence: Array<{ rule_id: string; ruleset_version: string; locators: EvidenceLocator[] }> }>;
  attribution: { method: string; channel: string; space: string; selected_model_version: string; base_value: number; explained_output: number; omitted_feature_count: number; omitted_contribution: number; calibration_note: string; features: Array<{ feature: string; value: number; contribution: number }> } | null;
  decision: { tier: "review_required" | "high" | "elevated" | "informational"; reasons: string[]; severity: number; coverage: number; corroborating_families: string[]; policy_version: string; policy_reference: string; policy_scope: string; actions: string[] };
  limitations: string[];
  versions: Record<string, string>;
  timing_ms: Record<string, number>;
}

const finite = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);
const strings = (v: unknown): v is string[] => Array.isArray(v) && v.every(s => typeof s === "string");
const locatorValid = (v: EvidenceLocator): boolean => !!v && typeof v.field === "string" && typeof v.location === "string"
  && Number.isInteger(v.start) && Number.isInteger(v.end) && v.start >= 0 && v.end > v.start;

export function readArtifactDecision(value: unknown): ArtifactDecision {
  // Fail closed before any UI can label an incomplete/stale envelope a result.
  const v = value as ArtifactDecision | null;
  if (!v || v.schema_version !== artifactSchemaVersion || !/^[a-f0-9]{32}$/.test(v.run_id) || !/^[a-f0-9]{64}$/.test(v.artifact_sha256)
      || !["complete", "review_required"].includes(v.status) || !v.decision
      || !["review_required", "high", "elevated", "informational"].includes(v.decision.tier)
      || v.research_validated !== false || !["synthetic_model_generated", "not_evaluated"].includes(v.result_category)
      || !Array.isArray(v.behavioral_evidence) || !Array.isArray(v.technical_findings) || !strings(v.limitations)
      || !strings(v.decision.actions) || !strings(v.decision.reasons) || !strings(v.decision.corroborating_families)
      || !Number.isInteger(v.decision.severity) || v.decision.severity < 0 || v.decision.severity > 3
      || !finite(v.decision.coverage) || v.decision.coverage < 0 || v.decision.coverage > 1
      || !v.versions || Object.values(v.versions).some(s => typeof s !== "string")
      || !v.timing_ms || Object.values(v.timing_ms).some(n => !finite(n) || n < 0)) {
    throw new Error("Incompatible artifact result. Review Required.");
  }
  if (v.status === "review_required" ? (v.calibrated_probability !== null || v.classification !== null || v.attribution !== null || v.decision.tier !== "review_required")
      : (typeof v.calibrated_probability !== "number" || !Number.isFinite(v.calibrated_probability) || v.calibrated_probability < 0 || v.calibrated_probability > 1
         || !["phishing", "legitimate"].includes(v.classification ?? "") || !v.attribution || v.decision.tier === "review_required")) {
    throw new Error("Incomplete artifact result. Review Required.");
  }
  for (const item of v.behavioral_evidence) {
    if (!item || typeof item.indicator_id !== "string" || typeof item.dimension_id !== "string"
        || !["supported", "absent", "unavailable", "not_evaluated"].includes(item.state) || !Array.isArray(item.evidence)
        || ((item.state === "supported") !== (item.evidence.length > 0))
        || item.evidence.some(e => !e || typeof e.rule_id !== "string" || typeof e.ruleset_version !== "string"
          || !Array.isArray(e.locators) || !e.locators.length || !e.locators.every(locatorValid))) {
      throw new Error("Invalid artifact evidence. Review Required.");
    }
  }
  if (v.technical_findings.some(f => !f || typeof f.finding !== "string" || typeof f.family !== "string"
      || !finite(f.value) || !Array.isArray(f.locators) || !f.locators.every(locatorValid) || typeof f.provenance !== "string")) {
    throw new Error("Invalid technical findings. Review Required.");
  }
  if (v.attribution) {
    const a = v.attribution;
    if (a.channel !== "model_attribution_not_artifact_evidence" || typeof a.method !== "string" || typeof a.space !== "string"
        || typeof a.selected_model_version !== "string" || typeof a.calibration_note !== "string"
        || !finite(a.base_value) || !finite(a.explained_output) || !finite(a.omitted_contribution)
        || !Number.isInteger(a.omitted_feature_count) || a.omitted_feature_count < 0
        || !Array.isArray(a.features) || a.features.length > 100
        || a.features.some(f => !f || typeof f.feature !== "string" || !finite(f.value) || !finite(f.contribution))
        || Math.abs(a.base_value + a.omitted_contribution + a.features.reduce((n, f) => n + f.contribution, 0) - a.explained_output) > 2e-5 * Math.max(1, Math.abs(a.explained_output))) {
      throw new Error("Invalid model attribution. Review Required.");
    }
  }
  return v;
}
