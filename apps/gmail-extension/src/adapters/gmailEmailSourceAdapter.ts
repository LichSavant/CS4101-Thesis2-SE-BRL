import type { EmailSourceMetadata } from "@phishing-defense/shared";
import { EmailSourceUnavailableError, type EmailSourceAdapter } from "./emailSourceAdapter";
import { extractDomain, identityFromHash, parseSender } from "./gmailParsing";
import { GMAIL_SELECTORS } from "./gmailSelectors";

// Legacy body flags are retained for caller compatibility but cannot authorize
// collection. A future body feature requires a reviewed setting/study purpose.
export interface GmailAdapterOptions { includeLinks?: boolean; includeBody?: boolean; bodyAuthorized?: boolean; }

export class GmailEmailSourceAdapter implements EmailSourceAdapter {
  constructor(private root: Document = document, private options: GmailAdapterOptions = {}) {}

  async extractCurrentEmail(): Promise<EmailSourceMetadata> {
    const container = this.currentMessageContainer();
    if (!container) throw new EmailSourceUnavailableError("Open a Gmail message before analyzing it.");
    const senderElement = this.firstWithin(container, GMAIL_SELECTORS.sender);
    if (!senderElement) throw new EmailSourceUnavailableError("Gmail sender metadata is unavailable. Gmail may have changed its layout.");
    const sender = parseSender(
      senderElement.getAttribute("name") || senderElement.textContent || "",
      senderElement.getAttribute("email") || senderElement.getAttribute("data-hovercard-id")
    );
    const subjectElement = this.firstWithin(this.root, GMAIL_SELECTORS.subject);
    const subject = subjectElement?.textContent?.trim();
    if (!subject) throw new EmailSourceUnavailableError("Gmail subject metadata is unavailable. Gmail may have changed its layout.");
    const messageId = this.messageIdentity(container);
    if (!messageId) throw new EmailSourceUnavailableError("A stable Gmail message identifier could not be found.");
    const metadata: EmailSourceMetadata = {
      userId: "demo-user-001", messageId, senderEmail: sender.email, senderName: sender.name,
      senderDomain: extractDomain(sender.email), subject, openedAt: new Date().toISOString()
    };
    if (this.options.includeLinks === true) metadata.links = this.extractLinks(container);
    return metadata;
  }

  currentMessageContainer(): HTMLElement | null {
    for (const selector of GMAIL_SELECTORS.messageContainers) {
      const candidates = Array.from(this.root.querySelectorAll<HTMLElement>(selector));
      const visible = candidates.filter((element) => !element.hidden && element.getAttribute("aria-hidden") !== "true");
      // In expanded threads Gmail may keep several message containers visible; the last is the active/latest message.
      if (visible.length) return visible[visible.length - 1];
    }
    return null;
  }

  private messageIdentity(container: HTMLElement): string | null {
    for (const attribute of GMAIL_SELECTORS.messageIdAttributes) {
      const value = container.getAttribute(attribute) || container.closest<HTMLElement>(`[${attribute}]`)?.getAttribute(attribute);
      if (value) return value;
    }
    return identityFromHash(this.root.defaultView?.location.hash || "");
  }

  private extractLinks(container: HTMLElement): string[] {
    return [...new Set(Array.from(container.querySelectorAll<HTMLAnchorElement>(GMAIL_SELECTORS.messageLinks))
      .map((link) => link.href).filter((url) => /^https?:\/\//.test(url)).slice(0, 50))];
  }

  private firstWithin(root: ParentNode, selectors: readonly string[]): HTMLElement | null {
    for (const selector of selectors) { const result = root.querySelector<HTMLElement>(selector); if (result) return result; }
    return null;
  }
}
