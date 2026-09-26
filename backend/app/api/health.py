import shutil

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import GeneratorDep, SessionDep, SettingsDep
from app.generators import available_backends
from app.tts import available_voices_backends, build_tts
from app.models import Job, JobStatus
from app.schemas import DefaultsOut, HealthOut, SystemOut
from app.utils.formatting import human_bytes

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthOut)
def health(settings: SettingsDep, session: SessionDep, generator: GeneratorDep) -> HealthOut:
    try:
        session.execute(select(1))
        database_ok = True
    except Exception:
        database_ok = False

    usage = shutil.disk_usage(settings.data_dir)
    generator_status = generator.get_status()
    healthy = database_ok and generator_status.get("healthy", False)

    return HealthOut(
        status="ok" if healthy else "degraded",
        app=settings.app_name,
        generator=generator_status,
        database=database_ok,
        disk_free_bytes=usage.free,
    )


@router.get("/system", response_model=SystemOut)
def system(settings: SettingsDep, session: SessionDep, generator: GeneratorDep) -> SystemOut:
    usage = shutil.disk_usage(settings.data_dir)
    active = (
        session.scalar(
            select(func.count()).select_from(Job).where(Job.status.in_(JobStatus.ACTIVE))
        )
        or 0
    )

    try:
        tts_status = build_tts(settings).get_status()
    except Exception as exc:
        tts_status = {"backend": settings.tts_provider, "healthy": False, "detail": str(exc)}

    return SystemOut(
        app=settings.app_name,
        generator_backend=settings.generator_backend,
        available_backends=available_backends(),
        generator=generator.get_status(),
        tts_backend=settings.tts_provider,
        available_tts_backends=available_voices_backends(),
        tts=tts_status,
        timing_mode=settings.timing_mode,
        defaults=DefaultsOut(
            model=settings.default_model,
            width=settings.default_width,
            height=settings.default_height,
            steps=settings.default_steps,
            batch_size=settings.default_batch_size,
            image_format=settings.default_image_format,
            min_prompts=settings.min_prompts,
            max_prompts=settings.max_prompts,
            recommended_min_prompts=settings.recommended_min_prompts,
            zip_retention_hours=settings.zip_retention_hours,
        ),
        data_dir=str(settings.data_dir),
        disk_total_bytes=usage.total,
        disk_free_bytes=usage.free,
        disk_free_human=human_bytes(usage.free),
        worker_in_api=settings.run_worker_in_api,
        active_jobs=active,
    )
