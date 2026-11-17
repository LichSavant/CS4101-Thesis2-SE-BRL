import { afterEach, expect, it, vi } from "vitest";
import { SCAN_BUTTON_ID } from "./services/gmailScanButton";

afterEach(() => {
  window.dispatchEvent(new Event("pagehide"));
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  vi.resetModules();
  document.body.innerHTML = "";
  document.head.innerHTML = "";
});

it.each([false, true])("initialization and selected-message scan respect consent (links=%s)", async includeLinks => {
  document.body.innerHTML = `<main><h2 class="hP">Synthetic subject</h2><div class="amn"></div>
    <div data-legacy-message-id="old"><span email="old@example.test" name="Old"></span><div class="a3s"><a href="https://old.example.test">old</a></div></div>
    <div data-legacy-message-id="selected"><span email="selected@example.test" name="Selected"></span><div class="a3s"><a href="https://selected.example.test">selected</a></div></div></main>`;
  for (const body of document.querySelectorAll(".a3s")) {
    Object.defineProperty(body, "innerText", { get: () => { throw new Error("Body read without study authorization"); } });
  }
  const sendMessage = vi.fn().mockResolvedValue({ ok: false, error: "Synthetic fixture stops after transmission" });
  vi.stubGlobal("chrome", {
    storage: { local: { get: vi.fn().mockResolvedValue({ includeLinks, automaticTracking: false, sourceMode: "gmail", processingMode: "legacy" }) } },
    runtime: { onMessage: { addListener: vi.fn() }, sendMessage }
  });
  const query = vi.spyOn(Element.prototype, "querySelectorAll");
  await import("./content");
  await vi.waitFor(() => expect(document.getElementById(SCAN_BUTTON_ID)).not.toBeNull());
  expect(sendMessage).not.toHaveBeenCalled();
  expect(query.mock.calls.some(([selector]) => selector === ".a3s a[href]")).toBe(false);
  (document.getElementById(SCAN_BUTTON_ID) as HTMLButtonElement).click();
  await vi.waitFor(() => expect(sendMessage).toHaveBeenCalledTimes(1));
  const message = sendMessage.mock.calls[0][0];
  expect(message.email.messageId).toBe("selected");
  expect(message.email.senderEmail).toBe("selected@example.test");
  expect(message.email.bodyText).toBeUndefined();
  expect(message.email.links).toEqual(includeLinks ? ["https://selected.example.test/"] : undefined);
  query.mockRestore();
});

it("does not acquire selected Gmail metadata before local consent", async () => {
  document.body.innerHTML='<main><h2 class="hP">Private synthetic subject</h2><div class="amn"></div><div data-legacy-message-id="selected"><span email="s@example.test"></span></div></main>';
  const {GmailEmailSourceAdapter}=await import("./adapters/gmailEmailSourceAdapter");
  const extract=vi.spyOn(GmailEmailSourceAdapter.prototype,"extractCurrentEmail");
  const sendMessage=vi.fn();
  vi.stubGlobal("chrome",{storage:{local:{get:vi.fn().mockResolvedValue({processingMode:"local",localConsent:false,automaticTracking:true,sourceMode:"gmail"})}},runtime:{onMessage:{addListener:vi.fn()},sendMessage}});
  await import("./content");await new Promise(resolve=>setTimeout(resolve,20));
  expect(extract).not.toHaveBeenCalled();expect(sendMessage).not.toHaveBeenCalled();expect(document.getElementById(SCAN_BUTTON_ID)).toBeNull();
});
