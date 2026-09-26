from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class GenerationError(RuntimeError):
    """Raised when a single image could not be generated."""


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    output_path: Path
    width: int
    height: int
    steps: int
    seed: int
    model: str = ""
    image_format: str = "png"
    batch_size: int = 1
    transparent: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationResult:
    output_path: Path
    seed: int
    duration_ms: int
    backend: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HealthStatus:
    healthy: bool
    backend: str
    detail: str = ""
    info: dict[str, Any] = field(default_factory=dict)


class ImageGenerator(ABC):
    """Contract every inference backend implements.

    Nothing above this interface knows whether inference runs on this machine,
    in another container, or on a remote GPU host.
    """

    name: str = "base"

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Render one image and write it to request.output_path."""

    @abstractmethod
    def health_check(self) -> HealthStatus:
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
