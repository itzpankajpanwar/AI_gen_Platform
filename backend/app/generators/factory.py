from collections.abc import Callable

from app.config import Settings, get_settings
from app.generators.api_backends import (
    OpenAIImageGenerator,
    PollinationsImageGenerator,
    RunwareImageGenerator,
)
from app.generators.base import ImageGenerator
from app.generators.comfyui import ComfyUIImageGenerator
from app.generators.mock import MockImageGenerator


def _build_mock(settings: Settings) -> ImageGenerator:
    return MockImageGenerator(
        delay_seconds=settings.mock_delay_seconds,
        failure_rate=settings.mock_failure_rate,
        model_label=settings.default_model,
    )


def _build_comfyui(settings: Settings) -> ImageGenerator:
    return ComfyUIImageGenerator(
        base_url=settings.comfyui_base_url,
        workflow_path=settings.comfyui_workflow_path,
        timeout_seconds=settings.comfyui_timeout_seconds,
        poll_seconds=settings.comfyui_poll_seconds,
    )


def _build_runware(settings: Settings) -> ImageGenerator:
    return RunwareImageGenerator(
        api_key=settings.runware_api_key,
        model=settings.runware_model,
        base_url=settings.runware_base_url,
        timeout_seconds=settings.api_timeout_seconds,
        dimension_multiple=settings.runware_dimension_multiple,
    )


def _build_openai(settings: Settings) -> ImageGenerator:
    return OpenAIImageGenerator(
        api_key=settings.openai_api_key,
        model=settings.openai_image_model,
        size=settings.openai_image_size,
        quality=settings.openai_image_quality,
        base_url=settings.openai_base_url,
        timeout_seconds=settings.api_timeout_seconds,
    )


def _build_pollinations(settings: Settings) -> ImageGenerator:
    return PollinationsImageGenerator(
        base_url=settings.pollinations_base_url,
        model=settings.pollinations_model,
        timeout_seconds=settings.api_timeout_seconds,
    )


REGISTRY: dict[str, Callable[[Settings], ImageGenerator]] = {
    "mock": _build_mock,
    "comfyui": _build_comfyui,
    "runware": _build_runware,
    "pollinations": _build_pollinations,
    "openai": _build_openai,
}


def available_backends() -> list[str]:
    return sorted(REGISTRY)


def build_generator(settings: Settings | None = None) -> ImageGenerator:
    settings = settings or get_settings()
    backend = settings.generator_backend.strip().lower()
    builder = REGISTRY.get(backend)
    if builder is None:
        raise ValueError(
            f"Unknown GENERATOR_BACKEND '{backend}'. Available: {', '.join(available_backends())}"
        )
    return builder(settings)
