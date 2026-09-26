from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class SynthesisError(RuntimeError):
    """Raised when one line of narration could not be synthesised."""


@dataclass(frozen=True)
class SpeechRequest:
    text: str
    output_path: Path
    voice: str = ""
    language: str = "hi-IN"
    model: str = ""
    pace: float = 1.0
    pitch: float = 0.0
    loudness: float = 1.0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SpeechResult:
    output_path: Path
    duration_seconds: float
    backend: str
    voice: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VoiceHealth:
    healthy: bool
    backend: str
    detail: str = ""
    info: dict[str, Any] = field(default_factory=dict)


class TextToSpeech(ABC):
    """Contract every narration backend implements.

    Mirrors ImageGenerator deliberately: the pipeline never learns which
    provider is speaking, so swapping Sarvam for ElevenLabs is configuration.
    """

    name: str = "base"

    @abstractmethod
    def synthesize(self, request: SpeechRequest) -> SpeechResult:
        """Render one line of speech to request.output_path."""

    @abstractmethod
    def health_check(self) -> VoiceHealth:
        """Report whether the backend can currently accept work."""

    def get_status(self) -> dict[str, Any]:
        health = self.health_check()
        return {
            "backend": self.name,
            "healthy": health.healthy,
            "detail": health.detail,
            "info": health.info,
        }

    def close(self) -> None:
        """Release backend resources. Optional."""
