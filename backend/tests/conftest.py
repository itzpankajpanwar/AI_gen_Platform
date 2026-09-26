import json
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from app.api.deps import reset_generator
from app.config import get_settings
from app.db import init_db, reset_engine
from app.main import create_app
from app.workers.generation_worker import GenerationWorker


@pytest.fixture
def settings(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("GENERATOR_BACKEND", "mock")
    monkeypatch.setenv("MOCK_DELAY_SECONDS", "0")
    monkeypatch.setenv("MOCK_FAILURE_RATE", "0")
    monkeypatch.setenv("RUN_WORKER_IN_API", "false")
    monkeypatch.setenv("DEFAULT_WIDTH", "192")
    monkeypatch.setenv("DEFAULT_HEIGHT", "108")
    monkeypatch.setenv("MIN_PROMPTS", "1")
    monkeypatch.setenv("RECOMMENDED_MIN_PROMPTS", "50")
    monkeypatch.setenv("ESTIMATED_IMAGE_MB", "0.05")
    monkeypatch.setenv("DISK_MIN_FREE_MB", "1")
    monkeypatch.setenv("VIDEO_PRESET", "ultrafast")
    monkeypatch.setenv("VIDEO_FPS", "12")

    get_settings.cache_clear()
    reset_engine()
    reset_generator()
    current = get_settings()
    init_db()

    yield current

    reset_engine()
    reset_generator()
    get_settings.cache_clear()


@pytest.fixture
def client(settings):
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def worker(settings):
    return GenerationWorker(settings)


def make_csv(count: int, seconds_each: float = 2.0, start_at: float = 0.0) -> bytes:
    """A contiguous timeline: each prompt holds the screen for `seconds_each`."""
    rows = ["start,end,prompt"]
    cursor = start_at
    for index in range(1, count + 1):
        rows.append(
            f'{cursor:g},{cursor + seconds_each:g},'
            f'"cinematic documentary still number {index}, 1940s India"'
        )
        cursor += seconds_each
    return ("\n".join(rows) + "\n").encode("utf-8")


def probe_video(path) -> dict:
    """Read real duration/stream info back out of the rendered file."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:  # pragma: no cover - ffprobe ships with ffmpeg
        pytest.skip("ffprobe not available")
    result = subprocess.run(
        [
            ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-show_entries", "stream=width,height,codec_name",
            "-of", "json", str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    stream = payload["streams"][0]
    return {
        "duration": float(payload["format"]["duration"]),
        "width": stream["width"],
        "height": stream["height"],
        "codec": stream["codec_name"],
    }
