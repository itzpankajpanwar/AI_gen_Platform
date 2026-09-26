from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),
    )

    app_name: str = "AI Image Generator"
    api_host: str = "0.0.0.0"
    api_port: int = 8200
    cors_origins: str = "*"

    data_dir: Path = Path("data")
    database_url: str = ""

    # Which ImageGenerator implementation to load. See app/generators/factory.py
    generator_backend: str = "mock"
    generation_concurrency: int = 1
    prompt_max_attempts: int = 1
    prompt_retry_backoff_seconds: float = 2.0
    run_worker_in_api: bool = True
    worker_poll_seconds: float = 1.0

    comfyui_base_url: str = "http://127.0.0.1:8188"
    comfyui_workflow_path: Path = Path("comfyui/workflows/flux_schnell.json")
    comfyui_timeout_seconds: float = 600.0
    comfyui_poll_seconds: float = 1.0

    mock_delay_seconds: float = 0.25
    mock_failure_rate: float = 0.0

    # Hosted pay-per-image backends (no GPU, no idle cost)
    runware_api_key: str = ""
    runware_model: str = "runware:100@1"
    runware_base_url: str = "https://api.runware.ai/v1"
    runware_dimension_multiple: int = 64

    pollinations_base_url: str = "https://image.pollinations.ai"
    pollinations_model: str = "flux"

    # OpenAI image generation (gpt-image). Quality "low" is the budget tier we
    # sized the film around; size is one of OpenAI's accepted values and the
    # result is resized to the project resolution.
    openai_api_key: str = ""
    openai_image_model: str = "gpt-image-1"
    openai_image_size: str = "1536x1024"
    openai_image_quality: str = "low"
    openai_base_url: str = "https://api.openai.com/v1"

    api_timeout_seconds: float = 240.0

    default_model: str = "FLUX.1-schnell"
    default_width: int = 1280
    default_height: int = 720
    default_steps: int = 4
    default_batch_size: int = 1
    default_image_format: str = "png"

    min_prompts: int = 1
    max_prompts: int = 100
    recommended_min_prompts: int = 50
    max_csv_bytes: int = 5 * 1024 * 1024

    zip_retention_hours: float = 10.0
    cleanup_interval_seconds: float = 300.0

    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"
    video_fps: int = 30
    video_crf: int = 20
    video_preset: str = "medium"
    video_timeout_seconds: float = 1800.0

    # ------------------------------------------------------------- narration
    # mock       - silent clips of realistic length; no key, no spend
    # sarvam     - Sarvam AI (Indian languages)
    # elevenlabs - ElevenLabs multilingual
    tts_provider: str = "mock"
    tts_model: str = ""
    tts_language: str = "hi-IN"
    tts_voice: str = ""
    tts_pace: float = 1.0
    tts_pitch: float = 0.0
    tts_loudness: float = 1.0
    tts_timeout_seconds: float = 120.0
    tts_mock_words_per_second: float = 3.5

    # Defaults match the voice the user auditioned on Sarvam's site: bulbul:v3,
    # speaker "ritu", 22.05 kHz. Any row can override voice/pace per scene.
    sarvam_api_key: str = ""
    sarvam_model: str = "bulbul:v3"
    sarvam_speaker: str = "ritu"
    sarvam_sample_rate: int = 22050
    sarvam_base_url: str = "https://api.sarvam.ai"
    elevenlabs_api_key: str = ""
    elevenlabs_base_url: str = "https://api.elevenlabs.io/v1"

    # fixed - start/end in the CSV are authoritative
    # audio - narration is synthesised first and its real length sets the scene
    timing_mode: str = "audio"

    # ---------------------------------------------- remotion animation layer
    # Scenes whose `animation` names a Remotion template are rendered in a
    # headless browser instead of by an ffmpeg filter graph.
    remotion_dir: Path = Path("remotion")
    remotion_binary: str = "npx"
    remotion_concurrency: int = 0  # 0 = let Remotion size it to the machine
    remotion_timeout_seconds: float = 900.0
    remotion_crf: int = 16
    remotion_accent: str = "#E0A65C"
    remotion_ink: str = "#0B0D10"

    # ------------------------------------------------------- styling assets
    font_sans: Path = Path("assets/fonts/Mukta-Regular.ttf")
    font_serif: Path = Path("assets/fonts/Mukta-Bold.ttf")
    music_dir: Path = Path("assets/music")
    ambience_dir: Path = Path("assets/ambience")
    sfx_dir: Path = Path("assets/sfx")
    archival_dir: Path = Path("assets/archival")
    music_level_db: float = -22.0
    master_lufs: float = -15.0  # final mix loudness target (YouTube ~-14 to -15)
    ambience_level_db: float = -30.0  # atmosphere sits well under score + voice
    sfx_level_db: float = -13.0       # graphic accents (whoosh/tick/thud)
    voice_master: bool = True         # EQ + compression on narration
    music_duck_db: float = -12.0

    estimated_image_mb: float = 5.0
    disk_safety_factor: float = 2.2
    disk_min_free_mb: float = 1024.0

    @field_validator("data_dir", mode="after")
    @classmethod
    def _absolute_data_dir(cls, value: Path) -> Path:
        """Anchor relative paths to the repo root, not the launch directory.

        Otherwise `uvicorn` started from backend/ and from the repo root would
        quietly use two different databases.
        """
        path = value.expanduser()
        if not path.is_absolute():
            repo_root = Path(__file__).resolve().parents[2]
            path = repo_root / path
        return path.resolve()

    @property
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def asset_path(self, value: Path) -> Path:
        """Resolve a bundled-asset path against the repo, not the launch dir."""
        path = Path(value).expanduser()
        return path if path.is_absolute() else (self.repo_root / path)

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite:///{self.data_dir / 'app.db'}"

    @property
    def jobs_dir(self) -> Path:
        return self.data_dir / "jobs"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def ensure_directories(self) -> None:
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
