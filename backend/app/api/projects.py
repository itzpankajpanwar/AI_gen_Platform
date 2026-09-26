from fastapi import APIRouter, File, UploadFile

from app.api.deps import SessionDep, SettingsDep, StorageDep
from app.schemas import (
    CsvValidationOut,
    DiskOut,
    JobOut,
    ProjectCreate,
    ProjectOut,
    PromptPreview,
    StartJobOut,
)
from app.services import job_service
from app.services.csv_service import parse_csv
from app.services.disk_service import check_disk

router = APIRouter(prefix="/projects", tags=["projects"])

PREVIEW_LIMIT = 5
PREVIEW_CHARS = 160


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, session: SessionDep, settings: SettingsDep) -> ProjectOut:
    project = job_service.create_project(
        session,
        name=payload.name,
        settings=settings,
        model=payload.model,
        width=payload.width,
        height=payload.height,
        steps=payload.steps,
        batch_size=payload.batch_size,
        image_format=payload.image_format,
        seed=payload.seed,
    )
    return ProjectOut.model_validate(project)


@router.get("", response_model=list[ProjectOut])
def list_projects(session: SessionDep) -> list[ProjectOut]:
    return [ProjectOut.model_validate(project) for project in job_service.list_projects(session)]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, session: SessionDep) -> ProjectOut:
    return ProjectOut.model_validate(job_service.get_project(session, project_id))


@router.post("/{project_id}/upload-csv", response_model=CsvValidationOut)
async def upload_csv(
    project_id: str,
    session: SessionDep,
    settings: SettingsDep,
    file: UploadFile = File(...),
) -> CsvValidationOut:
    project = job_service.get_project(session, project_id)
    data = await file.read()
    result = parse_csv(data, settings)

    if result.valid:
        job_service.replace_prompts(session, project, result.prompts, file.filename)

    return CsvValidationOut(
        valid=result.valid,
        total=result.total,
        duration_seconds=result.duration_seconds,
        narrated_count=result.narrated_count,
        filename=file.filename,
        errors=result.errors,
        warnings=result.warnings,
        preview=[
            PromptPreview(
                id=prompt.external_id,
                text=prompt.text[:PREVIEW_CHARS],
                start_seconds=prompt.start_seconds,
                end_seconds=prompt.end_seconds,
            )
            for prompt in result.prompts[:PREVIEW_LIMIT]
        ],
    )


@router.post("/{project_id}/start", response_model=StartJobOut, status_code=202)
def start_generation(
    project_id: str, session: SessionDep, settings: SettingsDep, storage: StorageDep
) -> StartJobOut:
    project = job_service.get_project(session, project_id)
    job = job_service.start_job(session, project, settings)
    disk = check_disk(job.total, settings)
    return StartJobOut(
        job=JobOut.model_validate(job_service.job_payload(job, storage, project)),
        disk=DiskOut.model_validate(disk.as_dict()),
    )


@router.get("/{project_id}/status", response_model=JobOut | None)
def project_status(project_id: str, session: SessionDep, storage: StorageDep) -> JobOut | None:
    project = job_service.get_project(session, project_id)
    job = job_service.active_job(session, project.id) or job_service.latest_job(session, project.id)
    if job is None:
        return None
    return JobOut.model_validate(job_service.job_payload(job, storage, project))


@router.post("/{project_id}/cancel", response_model=JobOut)
def cancel_generation(project_id: str, session: SessionDep, storage: StorageDep) -> JobOut:
    project = job_service.get_project(session, project_id)
    job = job_service.active_job(session, project.id)
    if job is None:
        raise job_service.ConflictError("No running job for this project")
    job = job_service.cancel_job(session, job)
    return JobOut.model_validate(job_service.job_payload(job, storage, project))


@router.get("/{project_id}/disk-check", response_model=DiskOut)
def disk_check(project_id: str, session: SessionDep, settings: SettingsDep) -> DiskOut:
    project = job_service.get_project(session, project_id)
    return DiskOut.model_validate(check_disk(project.prompt_count, settings).as_dict())
