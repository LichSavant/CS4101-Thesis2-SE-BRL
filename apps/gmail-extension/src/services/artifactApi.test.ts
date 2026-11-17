// Legacy transport tests explicitly authorize the legacy mode.
import { afterEach, expect, it, vi } from "vitest";
import type { EmailSourceMetadata } from "@phishing-defense/shared";
import { analyzeSelectedArtifact } from "./api";

afterEach(() => vi.unstubAllGlobals());
it("only explicitly submits selected metadata without bodies, fabricated links or view events", async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: false, status: 503, json: async () => ({ detail: "Review Required" }) });
  vi.stubGlobal("fetch", fetch);
  const email: EmailSourceMetadata = { userId: "demo", messageId: "selected", senderEmail: "sender@example.test", senderDomain: "example.test",
    senderName: "Synthetic", subject: "Selected subject", openedAt: "2026-11-11T00:00:00Z", bodyText: "MUST NOT BE SENT" };
  await expect(analyzeSelectedArtifact("http://127.0.0.1:8000", email, "unknown", false)).rejects.toThrow("Review Required");
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch.mock.calls[0][0]).toBe("http://127.0.0.1:8000/api/v1/artifact-analysis");
  const body = JSON.parse(fetch.mock.calls[0][1].body as string);
  expect(body).toMatchObject({ language: "unknown", submission_authorized: true, retain_metadata: false,
    artifact: { kind: "email", subject: "Selected subject", sender: "sender@example.test" } });
  expect(body.artifact).not.toHaveProperty("urls");
  expect(JSON.stringify(body)).not.toContain("MUST NOT BE SENT");
  expect(JSON.stringify(body)).not.toContain("messageId");
});

it("forwards known empty links only with explicit link opt-in", async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: false, status: 503, json: async () => ({ detail: "Unavailable" }) });
  vi.stubGlobal("fetch", fetch);
  const email = { subject: "Synthetic", senderEmail: "", links: [] } as unknown as EmailSourceMetadata;
  await expect(analyzeSelectedArtifact("http://127.0.0.1:8000", email, "en", true)).rejects.toThrow();
  expect(JSON.parse(fetch.mock.calls[0][1].body as string).artifact).toEqual({ kind: "email", subject: "Synthetic", urls: [], link_extraction_authorized: true });
});

vi.mock("./settings", () => ({ loadSettings: async () => ({ processingMode: "legacy" }) }));
