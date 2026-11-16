"""Thread lifecycle tests, using events and no classifier fits."""
import asyncio
import threading
from types import SimpleNamespace

from fastapi import HTTPException
import pytest

from backend.app.artifact_service import ArtifactAnalysisService


def test_timeouts_retain_slots_and_reject_queue_until_workers_finish():
    async def scenario():
        service = ArtifactAnalysisService(SimpleNamespace(artifact_timeout_seconds=.02))
        release = threading.Event()
        entered = []
        class Analyzer:
            def analyze(self, *args, **kwargs):
                entered.append(1)
                assert release.wait(2)
                return {"complete": True}
        service._analyzer = lambda *_: Analyzer()
        submission = SimpleNamespace(artifact={}, language="en")
        try:
            for _ in range(2):
                with pytest.raises(asyncio.TimeoutError):
                    await service.run_async(submission)
            assert len(entered) == 2 and len(service._workers) == 2
            for _ in range(20):
                with pytest.raises(HTTPException) as error:
                    await service.run_async(submission)
                assert error.value.status_code == 503
            assert len(entered) == 2 and len(service._workers) == 2
        finally:
            release.set()
            await asyncio.gather(*tuple(service._workers))
            await asyncio.sleep(0)
        assert not service._workers
        # Recovery verifies capacity release, not a 20 ms thread-pool scheduling
        # benchmark. Keep the short timeout above for the blocked-worker phase.
        service.settings.artifact_timeout_seconds = 2
        assert await service.run_async(submission) == {"complete": True}
    asyncio.run(scenario())


def test_client_cancellation_does_not_free_running_slot_and_failure_is_consumed():
    async def scenario():
        service = ArtifactAnalysisService(SimpleNamespace(artifact_timeout_seconds=2))
        release, started = threading.Event(), threading.Event()
        def fail(*_):
            started.set()
            assert release.wait(2)
            raise ValueError("private diagnostic")
        service._analyzer = fail
        submission = SimpleNamespace(artifact={}, language="en")
        task = asyncio.create_task(service.run_async(submission))
        try:
            while not started.is_set():
                await asyncio.sleep(.001)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert len(service._workers) == 1
        finally:
            release.set()
            results = await asyncio.gather(*tuple(service._workers), return_exceptions=True)
            await asyncio.sleep(0)
        assert isinstance(results[0], HTTPException)
        assert not service._workers
        assert service._active.acquire(blocking=False)
        assert service._active.acquire(blocking=False)
        assert not service._active.acquire(blocking=False)
        service._active.release(); service._active.release()
    asyncio.run(scenario())
