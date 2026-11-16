import type { AnalyzeEmailRequest, EmailOpenRequest, EmailScanRecord, EmailSourceMetadata, ScanFeedbackRequest, TrackedEmail } from "@phishing-defense/shared";
import { artifactSchemaVersion, readArtifactDecision, type ArtifactDecision } from "@phishing-defense/shared";
import type { ExtensionResult } from "../messages";

export class ApiError extends Error { constructor(message: string, readonly offline = false) { super(message); } }

async function request<T>(baseUrl: string, path: string, body: unknown): Promise<T> {
  const normalizedBaseUrl = baseUrl.trim().replace(/\/$/, "");
  if (!/^https?:\/\//.test(normalizedBaseUrl)) throw new ApiError("The backend URL must start with http:// or https://.");
  try {
    const response = await fetch(`${normalizedBaseUrl}${path}`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => null) as { detail?: string | Array<{ msg?: string }> } | null;
      const detail = typeof payload?.detail === "string" ? payload.detail : Array.isArray(payload?.detail) ? payload.detail.map(item => item.msg).filter(Boolean).join("; ") : "";
      throw new ApiError(detail || `Backend request failed (${response.status}) at ${path}.`);
    }
    return await response.json() as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError("Cannot reach the backend. Start FastAPI and check the backend URL.", true);
  }
}

export async function recordScanFeedback(baseUrl: string, feedback: ScanFeedbackRequest): Promise<void> {
  await request<void>(baseUrl, "/api/v1/scan-feedback", feedback);
}

/** Manual thesis analysis only. Never records a view or collects a body. */
export async function analyzeSelectedArtifact(baseUrl: string, email: EmailSourceMetadata, language: "en" | "unknown", includeLinks: boolean): Promise<ArtifactDecision> {
  const artifact: Record<string, unknown> = { kind: "email", subject: email.subject };
  if (email.senderEmail) artifact.sender = email.senderEmail;
  if (includeLinks === true && email.links !== undefined) {
    artifact.urls = email.links;
    artifact.link_extraction_authorized = true;
  }
  const result = await request<unknown>(baseUrl, "/api/v1/artifact-analysis", {
    schema_version: artifactSchemaVersion, artifact, language, submission_authorized: true, retain_metadata: false
  });
  return readArtifactDecision(result);
}

export async function processEmail(baseUrl: string, email: EmailSourceMetadata, options: { includeLinks?: boolean } = {}): Promise<ExtensionResult> {
  // Project both wire payloads. Caller objects may contain stale body fields or
  // unrelated private properties; their presence never establishes consent.
  const metadata: EmailOpenRequest = {
    userId: email.userId, messageId: email.messageId, senderEmail: email.senderEmail,
    senderName: email.senderName, subject: email.subject, openedAt: email.openedAt
  };
  const trackedEmail = await request<TrackedEmail>(baseUrl, "/api/v1/interactions/email-open", metadata);
  const analysisRequest: AnalyzeEmailRequest = {
    schemaVersion: "1.0", messageId: email.messageId, senderEmail: email.senderEmail,
    senderName: email.senderName, senderDomain: email.senderDomain, subject: email.subject,
    openedAt: email.openedAt, links: options.includeLinks === true ? email.links ?? [] : [],
    bodyCollectionAuthorized: false
  };
  const analysis = await request<EmailScanRecord>(baseUrl, "/api/v1/analyze-email", analysisRequest);
  return { trackedEmail, analysis };
}
