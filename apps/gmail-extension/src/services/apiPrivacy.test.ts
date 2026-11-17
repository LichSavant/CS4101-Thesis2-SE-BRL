// Legacy transport tests explicitly authorize the legacy mode.
import { afterEach, expect, it, vi } from "vitest";
import type { EmailSourceMetadata } from "@phishing-defense/shared";
import { processEmail } from "./api";

afterEach(() => vi.unstubAllGlobals());

const email = {
  userId: "fixture", messageId: "fixture:selected", senderEmail: "sender@example.test",
  senderName: "Fixture", senderDomain: "example.test", subject: "Synthetic subject",
  openedAt: "2026-11-15T00:00:00Z", bodyText: "PRIVATE_BODY", privateToken: "PRIVATE_TOKEN",
  links: ["https://example.test/opt-in"]
} as EmailSourceMetadata;

it.each([false, true])("projects metadata and never infers body consent (links=%s)", async includeLinks => {
  const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
  vi.stubGlobal("fetch", fetch);
  await processEmail("http://127.0.0.1:8000", email, { includeLinks });
  const bodies = fetch.mock.calls.map(call => JSON.parse(call[1].body as string));
  expect(bodies[0]).toEqual({ userId: "fixture", messageId: "fixture:selected", senderEmail: "sender@example.test",
    senderName: "Fixture", subject: "Synthetic subject", openedAt: email.openedAt });
  expect(bodies[1].links).toEqual(includeLinks ? email.links : []);
  expect(bodies[1].bodyCollectionAuthorized).toBe(false);
  expect(bodies[1]).not.toHaveProperty("bodyText");
  expect(JSON.stringify(bodies)).not.toContain("PRIVATE");
});

it("defaults link transmission off even when caller supplies links", async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
  vi.stubGlobal("fetch", fetch);
  await processEmail("http://127.0.0.1:8000", email);
  expect(JSON.parse(fetch.mock.calls[1][1].body as string).links).toEqual([]);
});

vi.mock("./settings", () => ({ loadSettings: async () => ({ processingMode: "legacy" }) }));
