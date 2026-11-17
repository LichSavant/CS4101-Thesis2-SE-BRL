// Legacy transport tests explicitly authorize the legacy mode.
import { afterEach, expect, it, vi } from "vitest";
import type { EmailSourceMetadata } from "@phishing-defense/shared";
import { processEmail } from "./api";
import { MockEmailSourceAdapter } from "../adapters/mockEmailSourceAdapter";

afterEach(() => vi.unstubAllGlobals());

it("projects both outbound payloads and never infers body consent", async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
  vi.stubGlobal("fetch", fetchMock);
  const email: EmailSourceMetadata & { session: string } = {
    userId: "fixture", messageId: "message", senderEmail: "sender@example.test",
    senderName: "Sender", senderDomain: "example.test", subject: "Hello",
    openedAt: "2026-11-13T00:00:00Z", bodyText: "PRIVATE FIXTURE", session: "PRIVATE EXTRA", links: ["https://opt-in-required.example/"]
  };
  await processEmail("http://127.0.0.1:8000", email);
  const payloads = fetchMock.mock.calls.map(call => JSON.parse(call[1].body));
  expect(payloads[0]).toEqual({ userId: "fixture", messageId: "message", senderEmail: "sender@example.test", senderName: "Sender", subject: "Hello", openedAt: email.openedAt });
  expect(payloads[1].bodyCollectionAuthorized).toBe(false);
  expect(payloads[1].links).toEqual([]);
  expect(JSON.stringify(payloads)).not.toContain("PRIVATE");
  expect(payloads.every(payload => !("bodyText" in payload))).toBe(true);
});

it("retains explicitly supplied opt-in links for metadata-only scans", async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
  vi.stubGlobal("fetch", fetchMock);
  await processEmail("http://127.0.0.1:8000", {
    userId: "fixture", messageId: "message", senderEmail: "sender@example.test", senderName: "Sender",
    senderDomain: "example.test", subject: "Hello", openedAt: "2026-11-13T00:00:00Z", links: ["https://example.test/"]
  }, { includeLinks: true });
  expect(JSON.parse(fetchMock.mock.calls[1][1].body).links).toEqual(["https://example.test/"]);
});

it("preserves mock mode with body-disabled requests", async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
  vi.stubGlobal("fetch", fetchMock);
  const email = await new MockEmailSourceAdapter().extractCurrentEmail();
  await processEmail("http://127.0.0.1:8000", email);
  const payloads = fetchMock.mock.calls.map(call => JSON.parse(call[1].body));
  expect(payloads[0].messageId).toBe("demo-message-001");
  expect(payloads[1].bodyCollectionAuthorized).toBe(false);
  expect(payloads.every(payload => !("bodyText" in payload))).toBe(true);
});

vi.mock("./settings", () => ({ loadSettings: async () => ({ processingMode: "legacy" }) }));
