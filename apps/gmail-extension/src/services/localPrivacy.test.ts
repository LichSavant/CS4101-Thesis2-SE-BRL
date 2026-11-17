import {afterEach,expect,it,vi} from "vitest";
import {processEmail,recordScanFeedback,analyzeSelectedArtifact} from "./api";
import {loadSettings} from "./settings";
afterEach(()=>vi.unstubAllGlobals());
it("defaults to local-only even with old automatic-tracking settings",async()=>{
  vi.stubGlobal("chrome",{storage:{local:{get:vi.fn().mockResolvedValue({automaticTracking:true,sourceMode:"gmail"})}}});
  const settings=await loadSettings();expect(settings.processingMode).toBe("local");expect(settings.automaticTracking).toBe(false);
});
it("blocks every API pathway before fetch in local-only mode",async()=>{
  const fetch=vi.fn();vi.stubGlobal("fetch",fetch);
  const email={userId:"synthetic",messageId:"synthetic",senderEmail:"s@example.test",senderName:"S",senderDomain:"example.test",subject:"Act now.",openedAt:"2026-11-17T00:00:00Z"};
  await expect(processEmail("http://127.0.0.1:8000",email)).rejects.toThrow("Local-only");
  await expect(analyzeSelectedArtifact("http://127.0.0.1:8000",email,"en",false)).rejects.toThrow("Local-only");
  await expect(recordScanFeedback("http://127.0.0.1:8000",{scanId:"synthetic",messageId:"synthetic",action:"view_full_analysis",createdAt:email.openedAt})).rejects.toThrow("Local-only");
  expect(fetch).not.toHaveBeenCalled();
});
