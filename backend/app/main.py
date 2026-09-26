import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.config import get_settings
from app.db import init_db
from app.services.job_service import JobServiceError
from app.workers.cleanup_worker import CleanupWorker
from app.workers.generation_worker import GenerationWorker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.ensure_directories()
    init_db()

    workers = []
    if settings.run_worker_in_api:
        workers = [GenerationWorker(settings), CleanupWorker(settings)]
        for worker in workers:
            worker.start()
        logger.info("Workers started in-process (backend=%s)", settings.generator_backend)
    else:
        logger.info("Workers disabled in API process — run `python -m app.workers.runner`")

    app.state.workers = workers
    yield

    for worker in workers:
        worker.stop()
    for worker in workers:
        worker.join(timeout=5)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="CSV in, one ZIP of generated images out.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(JobServiceError)
    async def job_service_error_handler(_: Request, exc: JobServiceError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, **exc.payload},
        )

    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {"app": settings.app_name, "docs": "/docs", "api": "/api/health"}

    return app


app = create_app()
