import logging
import threading

from sqlalchemy import select

from app.config import Settings, get_settings
from app.db import session_scope
from app.models import Job, JobStatus, utcnow
from app.services.storage import JobStorage

logger = logging.getLogger(__name__)


def run_cleanup_once(settings: Settings | None = None) -> list[str]:
    """Delete ZIP + images + temp files of jobs whose retention window has passed."""
    settings = settings or get_settings()
    storage = JobStorage(settings)
    removed: list[str] = []
    now = utcnow()

    with session_scope() as session:
        expired = list(
            session.scalars(
                select(Job).where(
                    Job.expires_at.is_not(None),
                    Job.expires_at <= now,
                    Job.cleaned_at.is_(None),
                    Job.status.notin_(JobStatus.ACTIVE),
                )
            )
        )
        for job in expired:
            try:
                storage.delete(job.id)
            except OSError:
                logger.exception("Could not delete files for %s", job.id)
                continue
            job.status = JobStatus.EXPIRED
            job.cleaned_at = now
            job.output_filename = None
            job.output_size = None
            removed.append(job.id)

    if removed:
        logger.info("Cleaned up expired jobs: %s", ", ".join(removed))
    return removed


class CleanupWorker(threading.Thread):
    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(name="cleanup-worker", daemon=True)
        self.settings = settings or get_settings()
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:  # pragma: no cover - thread entry point
        while not self._stop.is_set():
            try:
                run_cleanup_once(self.settings)
            except Exception:
                logger.exception("Cleanup pass failed")
            self._stop.wait(self.settings.cleanup_interval_seconds)
