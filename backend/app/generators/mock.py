import random
import textwrap
import time
from typing import Any

from PIL import Image, ImageDraw

from app.generators.base import (
    GenerationError,
    GenerationRequest,
    GenerationResult,
    HealthStatus,
    ImageGenerator,
)


class MockImageGenerator(ImageGenerator):
    """Renders a deterministic placeholder image instead of calling a model.

    Lets the whole CSV -> images -> ZIP pipeline be exercised (including the
    failure paths, via failure_rate) on a machine with no GPU and no model.
    """

    name = "mock"

    def __init__(
        self,
        delay_seconds: float = 0.25,
        failure_rate: float = 0.0,
        model_label: str = "mock",
    ) -> None:
        self.delay_seconds = delay_seconds
        self.failure_rate = failure_rate
        self.model_label = model_label

    def generate(self, request: GenerationRequest) -> GenerationResult:
        started = time.perf_counter()
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)

        rng = random.Random(request.seed)
        if self.failure_rate > 0 and rng.random() < self.failure_rate:
            raise GenerationError(f"mock backend simulated failure (seed={request.seed})")

        image = self._render(request, rng)
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(request.output_path, format=request.image_format.upper())

        duration_ms = int((time.perf_counter() - started) * 1000)
        return GenerationResult(
            output_path=request.output_path,
            seed=request.seed,
            duration_ms=duration_ms,
            backend=self.name,
            metadata={"model": request.model or self.model_label, "simulated": True},
        )

    def _render(self, request: GenerationRequest, rng: random.Random) -> Image.Image:
        width, height = request.width, request.height
        base = (rng.randint(20, 90), rng.randint(20, 90), rng.randint(40, 120))
        accent = (rng.randint(120, 235), rng.randint(90, 200), rng.randint(60, 160))

        image = Image.new("RGB", (width, height), base)
        draw = ImageDraw.Draw(image)
        for y in range(0, height, 4):
            ratio = y / max(height - 1, 1)
            draw.rectangle(
                [(0, y), (width, y + 4)],
                fill=tuple(int(base[i] + (accent[i] - base[i]) * ratio) for i in range(3)),
            )

        margin = max(int(width * 0.05), 24)
        draw.rectangle(
            [(margin, margin), (width - margin, height - margin)],
            outline=(255, 255, 255),
            width=3,
        )

        wrapped = textwrap.fill(request.prompt.strip(), width=54)[:600]
        draw.multiline_text(
            (margin + 24, margin + 24),
            f"MOCK RENDER\nseed {request.seed}\n{width}x{height}\n\n{wrapped}",
            fill=(255, 255, 255),
            spacing=6,
        )
        return image

    def health_check(self) -> HealthStatus:
        return HealthStatus(
            healthy=True,
            backend=self.name,
            detail="Mock backend always available",
            info={"delay_seconds": self.delay_seconds, "failure_rate": self.failure_rate},
        )

    def get_status(self) -> dict[str, Any]:
        status = super().get_status()
        status["model"] = self.model_label
        return status
