# Privacy and extension permissions

## Data collected

For the selected Gmail message only: stable message identifier when Gmail exposes one, sender display name, sender email, sender domain, subject, and open timestamp. Link extraction is off by default and can be enabled for URL rules. The mock adapter sends equivalent fixed demo metadata.

## Data intentionally excluded

Passwords, authentication/session tokens, cookies, attachments, contact lists, unrelated inbox content, messages not selected by the user, and browser history are never collected intentionally. Email body collection is disabled in this build: the Gmail adapter has no body-reading option, button injection uses metadata only, and the API client projects allowlisted request fields and always sends `bodyCollectionAuthorized=false` without a body. A stale caller supplying body text cannot authorize its transmission.

Manual scans use the selected message's metadata and subject. Both extraction and transmission of links require the stored `includeLinks` opt-in. Automatic tracking remains separately disabled by default. No additional extension permissions are introduced.

Future body analysis requires an approved study purpose, a separate explicit authorization setting, and a compatible backend authorization contract. Presence of body text, Gmail access, or a scan click must never be interpreted as that authorization. This build does not implement that future authorization flow.

## Manifest permissions

- `storage`: saves backend URL, source mode, automatic-tracking choice, optional link choice, and the last prototype result. No credentials are stored.
- `activeTab`: lets a user-initiated popup action address the currently selected Gmail tab. It does not provide background access to unrelated tabs.
- `https://mail.google.com/*`: injects the isolated Gmail content adapter only on Gmail. No `<all_urls>` access is requested.
- `http://localhost:8000/*` and `http://127.0.0.1:8000/*`: let the service worker call the local FastAPI backend.

The extension does not request `tabs`, cookies, history, contacts, downloads, web-request interception, or attachment access. Production should replace local API hosts with one exact HTTPS backend origin.

Automatic tracking is disabled by default. When enabled, the observer watches Gmail’s main message area, debounces rerenders, extracts only the currently open message, and suppresses repeat delivery for the same visible message. The backend’s five-second deduplication window provides a second safeguard.
