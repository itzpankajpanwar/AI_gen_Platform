import logging
import random
import threading
from dataclasses import replace
from datetime import timedelta

from sqlalchemy import select

from app.config import Settings, get_settings
from app.db import session_scope
from app.generators import GenerationRequest, ImageGenerator, build_generator
from app.services.remotion import CUTOUT_TEMPLATES
from app.models import ItemStatus, Job, JobItem, JobStatus, Project, utcnow
from app.services.audio_service import (
    AudioBuildError,
    build_audio_track,
    mux,
    reflow_timeline,
    synthesize_narration,
)
from app.services.storage import JobStorage
from app.services.subtitles import write_srt
from app.services.video_service import VideoBuildError, build_job_video
from app.tts import build_tts

logger = logging.getLogger(__name__)

MAX_SEED = 2**31 - 1


def recover_interrupted_jobs() -> int:
    """Re-queue jobs that were mid-flight when the process died."""
    with session_scope() as session:
        jobs = list(session.scalars(select(Job).where(Job.status == JobStatus.RUNNING)))
        for job in jobs:
            job.status = JobStatus.QUEUED
            job.current_prompt = None
            session.execute(
                JobItem.__table__.update()  # type: ignore[arg-type]
                .where(JobItem.job_id == job.id, JobItem.status == ItemStatus.RUNNING)
                .values(status=ItemStatus.PENDING)
            )
        return len(jobs)


class _Ok:
    seed = 0
    duration_ms = 0


class GenerationWorker(threading.Thread):
    """Pulls queued jobs from the database and renders them prompt by prompt.

    The queue lives in the database, so this can run inside the API process or
    as a separate container pointed at the same data directory.
    """

    def __init__(self, settings: Settings | None = None, generator: ImageGenerator | None = None):
        super().__init__(name="generation-worker", daemon=True)
        self.settings = settings or get_settings()
        self.storage = JobStorage(self.settings)
        self._generator = generator
        self._tts = None
        self._stop = threading.Event()

    # ------------------------------------------------------------------ thread

    @property
    def generator(self) -> ImageGenerator:
        if self._generator is None:
            self._generator = build_generator(self.settings)
        return self._generator

    @property
    def tts(self):
        if self._tts is None:
            self._tts = build_tts(self.settings)
        return self._tts

    def stop(self) -> None:
        self._stop.set()

    def run_once(self) -> str | None:
        """Claim and fully process a single queued job. Returns its id, if any."""
        job_id = self.claim_next_job()
        if job_id is None:
            return None
        try:
            self.process_job(job_id)
        except Exception as exc:
            logger.exception("Job %s crashed", job_id)
            self._mark_job_failed(job_id, str(exc))
        return job_id

    def run(self) -> None:  # pragma: no cover - thread entry point
        recovered = recover_interrupted_jobs()
        if recovered:
            logger.info("Re-queued %s interrupted job(s)", recovered)
        while not self._stop.is_set():
            try:
                job_id = self.run_once()
            except Exception:
                logger.exception("Worker loop error")
                job_id = None
            if job_id is None:
                self._stop.wait(self.settings.worker_poll_seconds)

    # ------------------------------------------------------------------- steps

    def claim_next_job(self) -> str | None:
        with session_scope() as session:
            job = session.scalars(
                select(Job)
                .where(Job.status == JobStatus.QUEUED)
                .order_by(Job.created_at)
                .limit(1)
            ).first()
            if job is None:
                return None
            if job.cancel_requested:
                job.status = JobStatus.CANCELLED
                job.finished_at = utcnow()
                return None
            job.status = JobStatus.RUNNING
            job.error = None
            if job.started_at is None:
                job.started_at = utcnow()
            return job.id

    def process_job(self, job_id: str) -> None:
        with session_scope() as session:
            job = session.get(Job, job_id)
            if job is None:
                return
            project = session.get(Project, job.project_id)
            config = {
                "width": project.width,
                "height": project.height,
                "steps": project.steps,
                "model": project.model_name,
                "image_format": project.image_format,
                "batch_size": project.batch_size,
                "seed": project.seed,
            }

        self.storage.prepare(job_id)
        cancelled = False

        while not self._stop.is_set():
            claimed = self._claim_next_item(job_id)
            if claimed is None:
                break
            if claimed == "cancelled":
                cancelled = True
                break

            item_id, order_index, prompt_text, animation, needs_image, source = claimed
            output_path = self.storage.image_path(job_id, order_index, config["image_format"])
            seed = config["seed"] if config["seed"] is not None else random.randint(0, MAX_SEED)

            # Real archival material: copy a local file (resized) instead of
            # generating — no API call. Public-domain photos, scans, etc.
            if source:
                src_path = Path(source).expanduser()
                if not src_path.is_absolute():
                    src_path = self.settings.asset_path(self.settings.archival_dir) / source
                try:
                    from app.generators.base import GenerationRequest as _GR
                    from app.generators.imageio import save_image_bytes as _save
                    _save(src_path.read_bytes(), _GR(prompt="", output_path=output_path,
                          width=config["width"], height=config["height"], steps=1, seed=0,
                          image_format=config["image_format"]))
                    self._record_item(job_id, item_id, _Ok(), None, output_path)
                except Exception as exc:
                    logger.warning("%s archival source '%s' failed: %s", job_id, source, exc)
                    self._record_item(job_id, item_id, None, f"archival source failed: {exc}", output_path)
                continue

            # A self-drawing animation (e.g. geo_map) uses no still, so skip the
            # generator: no API call, no spend. Mark it done and move on.
            if not needs_image:
                self._record_skipped(job_id, item_id)
                continue

            error: str | None = None
            result = None
            for attempt in range(1, self.settings.prompt_max_attempts + 1):
                request = GenerationRequest(
                    prompt=prompt_text,
                    output_path=output_path,
                    width=config["width"],
                    height=config["height"],
                    steps=config["steps"],
                    seed=seed if attempt == 1 else random.randint(0, MAX_SEED),
                    model=config["model"],
                    image_format=config["image_format"],
                    batch_size=config["batch_size"],
                    transparent=animation.lower() in CUTOUT_TEMPLATES,
                )
                try:
                    result = self.generator.generate(request)
                    error = None
                    break
                except Exception as exc:  # a failing prompt must not stop the batch
                    error = f"{type(exc).__name__}: {exc}"
                    logger.warning("%s prompt %s failed (attempt %s): %s", job_id, order_index, attempt, error)
                    # Backing off matters for rate-limited hosted backends, where an
                    # immediate retry just collects the same 429.
                    if attempt < self.settings.prompt_max_attempts:
                        self._stop.wait(self.settings.prompt_retry_backoff_seconds * attempt)

            self._record_item(job_id, item_id, result, error, output_path)

        if not cancelled:
            self._narrate(job_id)
        self._finalise_job(job_id, cancelled=cancelled)

    def _claim_next_item(self, job_id: str):
        with session_scope() as session:
            job = session.get(Job, job_id)
            if job is None:
                return None
            if job.cancel_requested:
                return "cancelled"

            item = session.scalars(
                select(JobItem)
                .where(JobItem.job_id == job_id, JobItem.status == ItemStatus.PENDING)
                .order_by(JobItem.order_index)
                .limit(1)
            ).first()
            if item is None:
                return None

            item.status = ItemStatus.RUNNING
            item.attempts += 1
            job.current_index = item.order_index
            job.current_prompt = item.prompt_text
            return (item.id, item.order_index, item.prompt_text,
                    (item.animation or ""), bool(item.needs_image), (item.source or ""))

    def _record_skipped(self, job_id: str, item_id: int) -> None:
        """Mark an image-less scene done without generating anything."""
        with session_scope() as session:
            item = session.get(JobItem, item_id)
            job = session.get(Job, job_id)
            if item is None or job is None:
                return
            item.status = ItemStatus.SUCCESS
            item.filename = None
            item.error = None
            job.successful += 1

    def _record_item(self, job_id: str, item_id: int, result, error: str | None, output_path) -> None:
        with session_scope() as session:
            item = session.get(JobItem, item_id)
            job = session.get(Job, job_id)
            if item is None or job is None:
                return

            if error is None and result is not None and output_path.is_file():
                item.status = ItemStatus.SUCCESS
                item.filename = output_path.name
                item.file_size = output_path.stat().st_size
                item.seed = result.seed
                item.duration_ms = result.duration_ms
                item.error = None
                job.successful += 1
            else:
                item.status = ItemStatus.FAILED
                item.error = error or "Generator did not produce an image"
                output_path.unlink(missing_ok=True)
                job.failed += 1

    def _narrate(self, job_id: str) -> None:
        """Speak every narrated line, then re-time the film to the audio if configured."""
        with session_scope() as session:
            items = list(session.scalars(select(JobItem).where(JobItem.job_id == job_id)))
            if not any((item.narration or "").strip() for item in items):
                return

            try:
                rendered = synthesize_narration(job_id, items, self.tts, self.storage, self.settings)
            except Exception:
                logger.exception("Narration failed for %s", job_id)
                return

            for item in items:
                if item.order_index in rendered:
                    item.audio_filename, item.audio_seconds = rendered[item.order_index]

            if self.settings.timing_mode.strip().lower() == "audio" and rendered:
                total = reflow_timeline(items)
                logger.info("%s re-timed to narration: %.1fs", job_id, total)

    def _finalise_job(self, job_id: str, cancelled: bool) -> None:
        with session_scope() as session:
            job = session.get(Job, job_id)
            if job is None:
                return
            items = list(session.scalars(select(JobItem).where(JobItem.job_id == job_id)))
            project = session.get(Project, job.project_id)

            try:
                video = build_job_video(
                    job, items, self.storage, self.settings, project.width, project.height
                )
            except VideoBuildError as exc:
                logger.exception("Video creation failed for %s", job_id)
                job.status = JobStatus.FAILED
                job.error = str(exc)
                job.finished_at = utcnow()
                job.current_prompt = None
                job.expires_at = utcnow() + timedelta(hours=self.settings.zip_retention_hours)
                return

            finished = utcnow()
            job.status = JobStatus.CANCELLED if cancelled else JobStatus.COMPLETED
            job.finished_at = finished
            job.current_prompt = None
            job.cancel_requested = False

            if video is not None:
                try:
                    write_srt(items, video.path.with_suffix(".srt"))
                except Exception:  # subtitles are a nicety, never fail the job for them
                    logger.warning("%s subtitle generation failed", job_id)
                try:
                    track = build_audio_track(
                        job_id, items, self.storage, self.settings, video.duration_seconds
                    )
                    if track is not None:
                        mux(video.path, track, self.settings)
                        video = replace(video, size_bytes=video.path.stat().st_size)
                except AudioBuildError:
                    logger.exception("Audio mix failed for %s — keeping silent video", job_id)

                job.output_filename = video.path.name
                job.output_size = video.size_bytes
                job.output_frame_count = video.frame_count
                job.output_duration_seconds = video.duration_seconds
                job.output_created_at = video.created_at
                job.expires_at = video.expires_at
            else:
                job.expires_at = finished + timedelta(hours=self.settings.zip_retention_hours)

    def _mark_job_failed(self, job_id: str, message: str) -> None:
        with session_scope() as session:
            job = session.get(Job, job_id)
            if job is None:
                return
            job.status = JobStatus.FAILED
            job.error = message
            job.finished_at = utcnow()
            job.current_prompt = None
            job.expires_at = utcnow() + timedelta(hours=self.settings.zip_retention_hours)
