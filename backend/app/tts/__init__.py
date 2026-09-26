from collections.abc import Callable

from app.config import Settings, get_settings
from app.tts.base import (
    SpeechRequest,
    SpeechResult,
    SynthesisError,
    TextToSpeech,
    VoiceHealth,
)
from app.tts.mock import MockTextToSpeech
from app.tts.providers import ElevenLabsTextToSpeech, SarvamTextToSpeech, probe_duration


def _build_mock(settings: Settings) -> TextToSpeech:
    return MockTextToSpeech(
        ffmpeg_binary=settings.ffmpeg_binary,
        words_per_second=settings.tts_mock_words_per_second,
    )


def _build_sarvam(settings: Settings) -> TextToSpeech:
    return SarvamTextToSpeech(
        api_key=settings.sarvam_api_key,
        model=settings.tts_model or "bulbul:v2",
        base_url=settings.sarvam_base_url,
        timeout_seconds=settings.tts_timeout_seconds,
    )


def _build_elevenlabs(settings: Settings) -> TextToSpeech:
    return ElevenLabsTextToSpeech(
        api_key=settings.elevenlabs_api_key,
        model=settings.tts_model or "eleven_multilingual_v2",
        base_url=settings.elevenlabs_base_url,
        timeout_seconds=settings.tts_timeout_seconds,
    )


REGISTRY: dict[str, Callable[[Settings], TextToSpeech]] = {
    "mock": _build_mock,
    "sarvam": _build_sarvam,
    "elevenlabs": _build_elevenlabs,
}


def available_voices_backends() -> list[str]:
    return sorted(REGISTRY)


def build_tts(settings: Settings | None = None) -> TextToSpeech:
    settings = settings or get_settings()
    backend = settings.tts_provider.strip().lower()
    builder = REGISTRY.get(backend)
    if builder is None:
        raise ValueError(
            f"Unknown TTS_PROVIDER '{backend}'. Available: {', '.join(available_voices_backends())}"
        )
    return builder(settings)


__all__ = [
    "ElevenLabsTextToSpeech",
    "MockTextToSpeech",
    "SarvamTextToSpeech",
    "SpeechRequest",
    "SpeechResult",
    "SynthesisError",
    "TextToSpeech",
    "VoiceHealth",
    "available_voices_backends",
    "build_tts",
    "probe_duration",
]
