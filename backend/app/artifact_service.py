"""Opt-in artifact analysis; trusted server bundle paths, no content persistence."""
import asyncio
import json
import sqlite3
import threading

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, StrictBool, StrictStr

from ml.artifact_analysis import ArtifactAnalyzer, load_bundle
from ml.decision import SCHEMA_VERSION


def _failure(status, code, stage):
    return HTTPException(status, {"code":code,"stage":stage,"state":"review_required",
        "limitation":"Artifact analysis could not safely complete; no definitive result is available.",
        "next_step":"Verify independently and retry only after the indicated input or component issue is resolved."})


class ArtifactSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: StrictStr
    artifact: dict
    language: StrictStr
    submission_authorized: StrictBool
    retain_metadata: StrictBool = False


class ArtifactBodyLimit:
    """Bound the new endpoint before JSON decoding, including chunked bodies."""
    def __init__(self, app, max_bytes):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") != "/api/v1/artifact-analysis":
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body = message.get("body", b"")
            size += len(body)
            if size > self.max_bytes:
                return await JSONResponse({"detail":_failure(413,"artifact_payload_too_large","validation").detail}, status_code=413)(scope, receive, send)
            chunks.append(body)
            if not message.get("more_body", False):
                break
        delivered = False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()
        await self.app(scope, replay, send)


class ArtifactAnalysisService:
    def __init__(self, settings):
        self.settings = settings
        self._lock = threading.Lock()
        self._active = threading.BoundedSemaphore(2)
        self._workers = set()
        self._memory = None

    def _analyzer(self, artifact=None):
        bundles = {}
        route = ({"email":"content_bearing_email", "webpage":"content_bearing_webpage"}.get(artifact.get("kind"))
                 if isinstance(artifact,dict) else None)
        if isinstance(artifact,dict) and artifact.get("kind")=="technical" and artifact.get("dataset") in {"UCI","PhiUSIIL"}:
            route=artifact["dataset"]
        # Reload and verify before each request: changed files cannot silently
        # reuse an earlier valid in-memory classifier. No client path accepted.
        for modality, path, digest in (
            ("content_bearing_email", self.settings.artifact_email_bundle, self.settings.artifact_email_bundle_sha256),
            ("content_bearing_webpage", self.settings.artifact_web_bundle, self.settings.artifact_web_bundle_sha256),
            ("UCI", getattr(self.settings,"artifact_uci_bundle",None), getattr(self.settings,"artifact_uci_bundle_sha256",None)),
            ("PhiUSIIL", getattr(self.settings,"artifact_phiusiil_bundle",None), getattr(self.settings,"artifact_phiusiil_bundle_sha256",None)),
        ):
            if modality != route:
                continue
            if path or digest:
                if not path or not digest:
                    raise ValueError("bundle_configuration_incomplete")
                bundles[modality] = load_bundle(path, expected_manifest_sha256=digest,
                                               max_bytes=self.settings.artifact_bundle_max_bytes)
        return ArtifactAnalyzer(bundles, timeout_seconds=self.settings.artifact_timeout_seconds)

    def run(self, submission):
        if not self._active.acquire(blocking=False):
            raise _failure(503, "artifact_analysis_busy", "model")
        return self._run_reserved(submission)

    async def run_async(self, submission):
        # Reserve before scheduling: timed-out requests must not fill the shared
        # executor queue. A running thread cannot be safely cancelled; it retains
        # its slot until it actually exits, with no persistence permission.
        if not self._active.acquire(blocking=False):
            raise _failure(503, "artifact_analysis_busy", "model")
        try:
            worker = asyncio.create_task(asyncio.to_thread(self._run_reserved, submission))
        except BaseException:
            self._active.release()
            raise
        self._workers.add(worker)
        def finished(task):
            self._workers.discard(task)
            if not task.cancelled():
                task.exception()  # Consume failures after an HTTP timeout.
        worker.add_done_callback(finished)
        return await asyncio.wait_for(asyncio.shield(worker), timeout=self.settings.artifact_timeout_seconds)

    def _run_reserved(self, submission):
        try:
            return self._analyzer(submission.artifact).analyze(submission.artifact, language=submission.language)
        except HTTPException:
            raise
        except Exception:
            raise _failure(503, "artifact_bundle_unavailable_or_incompatible", "model") from None
        finally:
            self._active.release()

    def retain(self, result):
        """Only explicit metadata opt-in; never persist artifact or explanations.

        Table created lazily at an authorized runtime action, not startup. This
        task's tests use isolated SQLite; no migration runs on the user's DB.
        """
        url = self.settings.database_url
        if not url.startswith("sqlite:///"):
            raise _failure(503, "artifact_metadata_storage_unavailable", "persistence")
        target = url[len("sqlite:///"):]
        record = {k: result[k] for k in ("schema_version", "run_id", "artifact_sha256", "modality", "status", "result_category", "versions")}
        with self._lock:
            connection = self._memory if target == ":memory:" else None
            if connection is None:
                connection = sqlite3.connect(target, check_same_thread=False)
                if target == ":memory:":
                    self._memory = connection
            try:
                connection.execute("CREATE TABLE IF NOT EXISTS artifact_analysis_metadata (run_id TEXT PRIMARY KEY, metadata_json TEXT NOT NULL)")
                connection.execute("INSERT INTO artifact_analysis_metadata VALUES (?, ?)", (result["run_id"], json.dumps(record)))
                connection.commit()
            except sqlite3.Error:
                connection.rollback()
                raise _failure(503, "artifact_metadata_storage_failed", "persistence") from None
            finally:
                if target != ":memory:":
                    connection.close()


def artifact_router(service):
    router = APIRouter()

    @router.post("/api/v1/artifact-analysis")
    async def analyze_artifact(request: Request):
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
            raise _failure(415, "artifact_json_required", "validation")
        # Avoid Pydantic/FastAPI's default validation detail echoing submitted
        # fields (including bodies) on malformed input.
        try:
            submission = ArtifactSubmission.model_validate(await request.json())
        except Exception:
            raise _failure(422, "artifact_submission_invalid", "validation") from None
        if submission.schema_version != SCHEMA_VERSION:
            raise _failure(422, "artifact_schema_incompatible", "validation")
        if not submission.submission_authorized:
            raise _failure(403, "explicit_artifact_submission_required", "consent")
        if submission.artifact.get("kind") != "email":
            raise _failure(422, "phase1_email_only", "validation")
        if submission.retain_metadata and not service.settings.artifact_metadata_retention_enabled:
            raise _failure(403, "artifact_metadata_retention_disabled", "persistence")
        try:
            result = await service.run_async(submission)
        except asyncio.TimeoutError:
            # The worker has no persistence permission and no partial result is
            # returned; the caller may retry as a new run after independent review.
            raise _failure(504, "artifact_analysis_timeout_review_required", "timeout") from None
        if submission.retain_metadata:
            service.retain(result)
        return result

    return router
