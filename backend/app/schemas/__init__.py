from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ProjectCreate(ApiModel):
    name: str = Field(min_length=1, max_length=200)
    model: str | None = None
    width: int | None = Field(default=None, ge=64, le=4096)
    height: int | None = Field(default=None, ge=64, le=4096)
    steps: int | None = Field(default=None, ge=1, le=150)
    batch_size: int | None = Field(default=None, ge=1, le=8)
    image_format: str | None = Field(default=None, pattern="^(png|jpg|jpeg|webp|PNG|JPG|JPEG|WEBP)$")
    seed: int | None = Field(default=None, ge=0)


class ProjectOut(ApiModel):
    id: str
    name: str
    model: str
    width: int
    height: int
    steps: int
    batch_size: int
    image_format: str
    seed: int | None
    csv_filename: str | None
    prompt_count: int
    created_at: datetime


class PromptPreview(ApiModel):
    id: str
    text: str
    start_seconds: float
    end_seconds: float


class CsvValidationOut(ApiModel):
    valid: bool
    total: int
    duration_seconds: float = 0.0
    narrated_count: int = 0
    filename: str | None = None
    errors: list[str] = []
    warnings: list[str] = []
    preview: list[PromptPreview] = []


class OutputOut(ApiModel):
    filename: str
    size_bytes: int
    size_human: str
    frame_count: int
    duration_seconds: float
    created_at: datetime | None = None
    expires_at: datetime | None = None
    expires_in_seconds: int | None = None
    available: bool = False


class JobOut(ApiModel):
    job_id: str
    project_id: str
    project_name: str
    status: str
    total: int
    successful: int
    failed: int
    completed: int
    remaining: int
    percent: float
    current_index: int
    current_prompt: str | None = None
    cancel_requested: bool = False
    error: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    elapsed_seconds: int | None = None
    eta_seconds: int | None = None
    output: OutputOut | None = None


class JobItemOut(ApiModel):
    order_index: int
    external_id: str
    prompt_text: str
    start_seconds: float
    end_seconds: float
    transition: str | None = None
    ken_burns: str | None = None
    grade: str | None = None
    grain: int | None = None
    music: str | None = None
    text_type: str | None = None
    text_value: str | None = None
    narration: str | None = None
    voice: str | None = None
    audio_seconds: float | None = None
    status: str
    filename: str | None = None
    seed: int | None = None
    duration_ms: int | None = None
    attempts: int = 0
    error: str | None = None


class JobDetailOut(JobOut):
    items: list[JobItemOut] = []


class DiskOut(ApiModel):
    ok: bool
    prompt_count: int
    required_bytes: int
    available_bytes: int
    total_bytes: int
    required_gb: float
    available_gb: float
    message: str


class StartJobOut(ApiModel):
    job: JobOut
    disk: DiskOut


class DefaultsOut(ApiModel):
    model: str
    width: int
    height: int
    steps: int
    batch_size: int
    image_format: str
    min_prompts: int
    max_prompts: int
    recommended_min_prompts: int
    zip_retention_hours: float


class HealthOut(ApiModel):
    status: str
    app: str
    generator: dict
    database: bool
    disk_free_bytes: int


class SystemOut(ApiModel):
    app: str
    generator_backend: str
    available_backends: list[str]
    generator: dict
    tts_backend: str = "mock"
    available_tts_backends: list[str] = []
    tts: dict = {}
    timing_mode: str = "audio"
    defaults: DefaultsOut
    data_dir: str
    disk_total_bytes: int
    disk_free_bytes: int
    disk_free_human: str
    worker_in_api: bool
    active_jobs: int


__all__ = [
    "ApiModel",
    "CsvValidationOut",
    "DefaultsOut",
    "DiskOut",
    "HealthOut",
    "JobDetailOut",
    "JobItemOut",
    "JobOut",
    "ProjectCreate",
    "ProjectOut",
    "PromptPreview",
    "OutputOut",
    "StartJobOut",
    "SystemOut",
]
