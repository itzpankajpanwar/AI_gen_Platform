from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import Settings
from app.models import ItemStatus, Job, JobItem, JobStatus, Project, Prompt, as_utc, utcnow
from app.services.csv_service import ParsedPrompt
from app.services.disk_service import DiskCheck, check_disk
from app.services.storage import JobStorage
from app.utils.formatting import human_bytes


class JobServiceError(Exception):
    status_code = 400

    def __init__(self, message: str, payload: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.payload = payload or {}


class NotFoundError(JobServiceError):
    status_code = 404


class ConflictError(JobServiceError):
    status_code = 409


class GoneError(JobServiceError):
    status_code = 410


class InsufficientDiskError(JobServiceError):
    status_code = 507


# --------------------------------------------------------------------- projects


def create_project(session: Session, *, name: str, settings: Settings, **overrides) -> Project:
    project = Project(
        name=name.strip() or "Untitled project",
        model_name=overrides.get("model") or settings.default_model,
        width=overrides.get("width") or settings.default_width,
        height=overrides.get("height") or settings.default_height,
        steps=overrides.get("steps") or settings.default_steps,
        batch_size=overrides.get("batch_size") or settings.default_batch_size,
        image_format=(overrides.get("image_format") or settings.default_image_format).lower(),
        seed=overrides.get("seed"),
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def get_project(session: Session, project_id: str) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise NotFoundError(f"Project {project_id} not found")
    return project


def list_projects(session: Session, limit: int = 100) -> list[Project]:
    stmt = select(Project).order_by(Project.created_at.desc()).limit(limit)
    return list(session.scalars(stmt))


def replace_prompts(
    session: Session,
    project: Project,
    prompts: list[ParsedPrompt],
    filename: str | None,
) -> Project:
    if active_job(session, project.id) is not None:
        raise ConflictError("This project has a job running — wait for it to finish first")

    session.execute(
        Prompt.__table__.delete().where(Prompt.project_id == project.id)  # type: ignore[arg-type]
    )
    for parsed in prompts:
        session.add(
            Prompt(
                project_id=project.id,
                external_id=parsed.external_id,
                order_index=parsed.order_index,
                text=parsed.text,
                start_seconds=parsed.start_seconds,
                end_seconds=parsed.end_seconds,
                transition=parsed.transition,
                transition_seconds=parsed.transition_seconds,
                ken_burns=parsed.ken_burns,
                ken_burns_scale=parsed.ken_burns_scale,
                grade=parsed.grade,
                grain=parsed.grain,
                music=parsed.music,
                ambience=parsed.ambience,
                text_type=parsed.text_type,
                text_value=parsed.text_value,
                narration=parsed.narration,
                voice=parsed.voice,
                animation=parsed.animation,
                animation_value=parsed.animation_value,
                animation_params=parsed.animation_params,
                needs_image=parsed.needs_image,
            )
        )
    project.csv_filename = filename
    project.prompt_count = len(prompts)
    session.commit()
    session.refresh(project)
    return project


# ------------------------------------------------------------------------- jobs


def next_job_id(session: Session) -> str:
    count = session.scalar(select(func.count()).select_from(Job)) or 0
    candidate_number = count
    while True:
        candidate_number += 1
        candidate = f"JOB-{candidate_number:03d}"
        if session.get(Job, candidate) is None:
            return candidate


def active_job(session: Session, project_id: str) -> Job | None:
    stmt = (
        select(Job)
        .where(Job.project_id == project_id, Job.status.in_(JobStatus.ACTIVE))
        .order_by(Job.created_at.desc())
        .limit(1)
    )
    return session.scalars(stmt).first()


def latest_job(session: Session, project_id: str) -> Job | None:
    stmt = (
        select(Job)
        .where(Job.project_id == project_id)
        .order_by(Job.created_at.desc())
        .limit(1)
    )
    return session.scalars(stmt).first()


def get_job(session: Session, job_id: str) -> Job:
    job = session.get(Job, job_id)
    if job is None:
        raise NotFoundError(f"Job {job_id} not found")
    return job


def list_jobs(session: Session, limit: int = 50) -> list[Job]:
    stmt = (
        select(Job)
        .options(selectinload(Job.project))
        .order_by(Job.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(stmt))


def job_items(session: Session, job_id: str) -> list[JobItem]:
    stmt = select(JobItem).where(JobItem.job_id == job_id).order_by(JobItem.order_index)
    return list(session.scalars(stmt))


def start_job(session: Session, project: Project, settings: Settings) -> Job:
    prompts = list(
        session.scalars(
            select(Prompt).where(Prompt.project_id == project.id).order_by(Prompt.order_index)
        )
    )
    if not prompts:
        raise JobServiceError("Upload a valid CSV before starting generation")
    if active_job(session, project.id) is not None:
        raise ConflictError("A job is already running for this project")

    disk = check_disk(len(prompts), settings)
    if not disk.ok:
        raise InsufficientDiskError(disk.message, {"disk": disk.as_dict()})

    job = Job(
        id=next_job_id(session),
        project_id=project.id,
        status=JobStatus.QUEUED,
        total=len(prompts),
    )
    session.add(job)
    session.flush()

    for prompt in prompts:
        session.add(
            JobItem(
                job_id=job.id,
                prompt_id=prompt.id,
                order_index=prompt.order_index,
                external_id=prompt.external_id,
                prompt_text=prompt.text,
                start_seconds=prompt.start_seconds,
                end_seconds=prompt.end_seconds,
                transition=prompt.transition,
                transition_seconds=prompt.transition_seconds,
                ken_burns=prompt.ken_burns,
                ken_burns_scale=prompt.ken_burns_scale,
                grade=prompt.grade,
                grain=prompt.grain,
                music=prompt.music,
                ambience=prompt.ambience,
                text_type=prompt.text_type,
                text_value=prompt.text_value,
                narration=prompt.narration,
                voice=prompt.voice,
                animation=prompt.animation,
                animation_value=prompt.animation_value,
                animation_params=prompt.animation_params,
                needs_image=prompt.needs_image,
            )
        )
    session.commit()
    session.refresh(job)
    return job


def delete_job(session: Session, job: Job, storage: JobStorage) -> str:
    """Remove a job's video, images and database rows. Not reversible."""
    if job.status in JobStatus.ACTIVE:
        raise ConflictError(f"Job {job.id} is still running — cancel it first")

    job_id = job.id
    storage.delete(job_id)
    session.delete(job)
    session.commit()
    return job_id


def cancel_job(session: Session, job: Job) -> Job:
    if job.status not in JobStatus.ACTIVE:
        raise ConflictError(f"Job {job.id} is not running")
    job.cancel_requested = True
    if job.status == JobStatus.QUEUED:
        job.status = JobStatus.CANCELLED
        job.finished_at = utcnow()
    session.commit()
    session.refresh(job)
    return job


def retry_failed(session: Session, job: Job, settings: Settings, storage: JobStorage) -> Job:
    if job.status in JobStatus.ACTIVE:
        raise ConflictError(f"Job {job.id} is still running")
    if job.status == JobStatus.EXPIRED or job.cleaned_at is not None:
        raise ConflictError(f"Job {job.id} has expired and its files were deleted")

    failed_items = [item for item in job_items(session, job.id) if item.status == ItemStatus.FAILED]
    if not failed_items:
        raise ConflictError(f"Job {job.id} has no failed prompts to retry")

    disk = check_disk(len(failed_items), settings)
    if not disk.ok:
        raise InsufficientDiskError(disk.message, {"disk": disk.as_dict()})

    for item in failed_items:
        item.status = ItemStatus.PENDING
        item.error = None

    storage.video_path(job.id).unlink(missing_ok=True)

    job.failed = 0
    job.status = JobStatus.QUEUED
    job.cancel_requested = False
    job.error = None
    job.finished_at = None
    job.output_filename = None
    job.output_size = None
    job.output_frame_count = None
    job.output_duration_seconds = None
    job.output_created_at = None
    job.expires_at = None
    session.commit()
    session.refresh(job)
    return job


# -------------------------------------------------------------------- progress


def _seconds_between(start: datetime | None, end: datetime | None) -> float | None:
    start_utc, end_utc = as_utc(start), as_utc(end)
    if start_utc is None or end_utc is None:
        return None
    return max((end_utc - start_utc).total_seconds(), 0.0)


def output_payload(job: Job, storage: JobStorage) -> dict | None:
    if not job.output_filename:
        return None
    expires_at = as_utc(job.expires_at)
    expires_in = _seconds_between(utcnow(), expires_at)
    exists = storage.video_path(job.id).is_file()
    return {
        "filename": job.output_filename,
        "size_bytes": job.output_size or 0,
        "size_human": human_bytes(job.output_size),
        "frame_count": job.output_frame_count or 0,
        "duration_seconds": job.output_duration_seconds or 0.0,
        "created_at": as_utc(job.output_created_at),
        "expires_at": expires_at,
        "expires_in_seconds": int(expires_in) if expires_in is not None else None,
        "available": exists and (expires_in is None or expires_in > 0),
    }


def job_payload(job: Job, storage: JobStorage, project: Project | None = None) -> dict:
    project = project or job.project
    completed = job.successful + job.failed
    remaining = max(job.total - completed, 0)
    percent = round((completed / job.total) * 100, 1) if job.total else 0.0

    reference_end = as_utc(job.finished_at) or utcnow()
    elapsed = _seconds_between(job.started_at, reference_end)

    eta_seconds: float | None = None
    if job.status == JobStatus.RUNNING and elapsed and completed > 0 and remaining > 0:
        eta_seconds = (elapsed / completed) * remaining

    return {
        "job_id": job.id,
        "project_id": job.project_id,
        "project_name": project.name if project else "",
        "status": job.status,
        "total": job.total,
        "successful": job.successful,
        "failed": job.failed,
        "completed": completed,
        "remaining": remaining,
        "percent": percent,
        "current_index": job.current_index,
        "current_prompt": job.current_prompt,
        "cancel_requested": job.cancel_requested,
        "error": job.error,
        "created_at": as_utc(job.created_at),
        "started_at": as_utc(job.started_at),
        "finished_at": as_utc(job.finished_at),
        "elapsed_seconds": int(elapsed) if elapsed is not None else None,
        "eta_seconds": int(eta_seconds) if eta_seconds is not None else None,
        "output": output_payload(job, storage),
    }
