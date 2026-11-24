"""Bounded official UCI archive acquisition; never extract or parse records."""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


URL = "https://archive.ics.uci.edu/static/public/327/phishing%2Bwebsites.zip"
EXPECTED_SHA256 = "514f582cb44cba17251baf1d59f64cddff16efa2b644d091ce8d2a1e8d492940"


def _official(url):
    parsed = urlsplit(url)
    return (parsed.scheme == "https" and parsed.hostname == "archive.ics.uci.edu"
            and parsed.path in {"/static/public/327/phishing%2Bwebsites.zip",
                                "/static/public/327/phishing+websites.zip"}
            and not parsed.query and not parsed.fragment and not parsed.username)


class OfficialRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _official(newurl):
            raise ValueError("uci_redirect_outside_official_archive")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def acquire_archive(directory, *, authorization_reference, opener=None):
    """Exclusive opaque acquisition under the user's explicit Phase A scope.

    Exact expected archive digest comes from the prior source evidence. Failure
    removes only this call's newly created file/directory. No LFS commands, ZIP
    member reads, label interpretation, source-record processing or model calls.
    """
    if type(authorization_reference) is not str or not authorization_reference.strip():
        raise ValueError("explicit_opaque_acquisition_authorization_required")
    directory = Path(directory)
    directory.mkdir()  # Never reuse user data or a previous acquisition.
    path = directory / "phishing-websites.zip"
    opener = opener or build_opener(OfficialRedirects()).open
    digest, size = hashlib.sha256(), 0
    try:
        with opener(Request(URL, headers={"User-Agent": "SE-BRL bounded official source acquisition"}), timeout=25) as response:
            effective = response.geturl()
            if not _official(effective):
                raise ValueError("uci_response_not_official_archive")
            with path.open("xb") as stream:
                while True:
                    block = response.read(min(65536, 2_000_001 - size))
                    if not block:
                        break
                    size += len(block)
                    if size > 2_000_000:
                        raise ValueError("uci_archive_size_budget_exceeded")
                    digest.update(block)
                    stream.write(block)
        if digest.hexdigest() != EXPECTED_SHA256:
            raise ValueError("uci_archive_differs_from_pinned_original:" + digest.hexdigest())
    except Exception:
        if path.exists():
            path.unlink()
        directory.rmdir()
        raise
    return {"operation": "opaque_official_archive_acquisition", "source_url": URL,
            "effective_url": effective, "sha256": digest.hexdigest(), "bytes": size,
            "acquired_utc": datetime.now(timezone.utc).isoformat(),
            "local_path": path.as_posix(), "authorization_reference": authorization_reference,
            "license": "CC BY 4.0; official UCI page retained in source-retrieval.json",
            "source_records_parsed": 0, "archive_extracted": False,
            "historical_acquisition_date_established": False, "scientific_admission": False}
