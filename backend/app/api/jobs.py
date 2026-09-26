from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.api.deps import SessionDep, SettingsDep, StorageDep
from app.models import as_utc, utcnow
from app.schemas import JobDetailOut, JobItemOut, JobOut
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(session: SessionDep, storage: StorageDep, limit: int = 50) -> list[JobOut]:
    return [
        JobOut.model_validate(job_service.job_payload(job, storage))
        for job in job_service.list_jobs(session, limit)
    ]


@router.get("/{job_id}", response_model=JobDetailOut)
def get_job(job_id: str, session: SessionDep, storage: StorageDep) -> JobDetailOut:
    job = job_service.get_job(session, job_id)
    payload = job_service.job_payload(job, storage)
    payload["items"] = [
        JobItemOut.model_validate(item) for item in job_service.job_items(session, job_id)
    ]
    return JobDetailOut.model_validate(payload)


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: str, session: SessionDep, storage: StorageDep) -> None:
    job = job_service.get_job(session, job_id)
    job_service.delete_job(session, job, storage)


@router.post("/{job_id}/retry-failed", response_model=JobOut, status_code=202)
def retry_failed(
    job_id: str, session: SessionDep, settings: SettingsDep, storage: StorageDep
) -> JobOut:
    job = job_service.get_job(session, job_id)
    job = job_service.retry_failed(session, job, settings, storage)
    return JobOut.model_validate(job_service.job_payload(job, storage))


@router.get("/{job_id}/download")
def download_video(job_id: str, session: SessionDep, storage: StorageDep) -> FileResponse:
    job = job_service.get_job(session, job_id)
    expires_at = as_utc(job.expires_at)

    if job.cleaned_at is not None or (expires_at and expires_at <= utcnow()):
        raise job_service.GoneError(
            f"The video for {job.id} has expired and was deleted", {"status": job.status}
        )
    if not job.output_filename:
        raise job_service.NotFoundError(f"Job {job.id} has no video yet")

    path = storage.video_path(job.id)
    if not path.is_file():
        raise job_service.NotFoundError(f"Video file for {job.id} is no longer on disk")

    return FileResponse(path, media_type="video/mp4", filename=job.output_filename)
