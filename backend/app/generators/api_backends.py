"""Hosted pay-per-image backends.

No GPU, no model download, no idle cost — the application sends a prompt over
HTTPS and gets pixels back. Same ImageGenerator contract as the local backends.
"""

import time
import urllib.parse
import uuid
from typing import Any

import httpx

from app.generators.base import (
    GenerationError,
    GenerationRequest,
    GenerationResult,
    HealthStatus,
    ImageGenerator,
)
from app.generators.imageio import save_image_bytes, snap


class RunwareImageGenerator(ImageGenerator):
    """Runware REST API (https://runware.ai) — FLUX.1-schnell by default."""

    name = "runware"

    def __init__(
        self,
        api_key: str,
        model: str = "runware:100@1",
        base_url: str = "https://api.runware.ai/v1",
        timeout_seconds: float = 180.0,
        dimension_multiple: int = 64,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.dimension_multiple = dimension_multiple
        self._client = httpx.Client(timeout=timeout_seconds)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self.api_key:
            raise GenerationError("RUNWARE_API_KEY is not set")

        started = time.perf_counter()
        task_uuid = str(uuid.uuid4())
        payload = [
            {
                "taskType": "imageInference",
                "taskUUID": task_uuid,
                "model": self.model,
                "positivePrompt": request.prompt,
                # Runware accepts dimensions in fixed increments; save_image_bytes
                # resizes the result back to the project's exact resolution.
                "width": snap(request.width, self.dimension_multiple),
                "height": snap(request.height, self.dimension_multiple),
                "steps": request.steps,
                "numberResults": 1,
                "outputType": "URL",
                "outputFormat": "PNG",
                "seed": request.seed,
            }
        ]

        try:
            response = self._client.post(
                self.base_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        except httpx.HTTPError as exc:
            raise GenerationError(f"Cannot reach Runware: {exc}") from exc

        if response.status_code >= 400:
            raise GenerationError(f"Runware rejected the request: {response.text[:600]}")

        entry = self._first_result(response.json())
        data = self._fetch_image(entry)
        save_image_bytes(data, request)

        return GenerationResult(
            output_path=request.output_path,
            seed=entry.get("seed", request.seed),
            duration_ms=int((time.perf_counter() - started) * 1000),
            backend=self.name,
            metadata={
                "model": self.model,
                "task_uuid": task_uuid,
                "cost": entry.get("cost"),
            },
        )

    @staticmethod
    def _first_result(body: Any) -> dict[str, Any]:
        # The API has been documented both as a bare object and as {"data": [...]}.
        if isinstance(body, dict):
            if body.get("errors"):
                raise GenerationError(f"Runware error: {str(body['errors'])[:600]}")
            items = body.get("data")
            if isinstance(items, list) and items:
                return items[0]
            if "imageURL" in body or "imageBase64Data" in body:
                return body
        if isinstance(body, list) and body:
            return body[0]
        raise GenerationError(f"Unexpected Runware response: {str(body)[:400]}")

    def _fetch_image(self, entry: dict[str, Any]) -> bytes:
        if entry.get("imageBase64Data"):
            import base64

            return base64.b64decode(entry["imageBase64Data"])

        url = entry.get("imageURL")
        if not url:
            raise GenerationError(f"Runware returned no image: {str(entry)[:400]}")
        try:
            image_response = self._client.get(url)
            image_response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GenerationError(f"Could not download image from Runware: {exc}") from exc
        return image_response.content

    def health_check(self) -> HealthStatus:
        if not self.api_key:
            return HealthStatus(
                healthy=False,
                backend=self.name,
                detail="RUNWARE_API_KEY is not set",
                info={"model": self.model},
            )
        # Deliberately no live call: every Runware request costs credits.
        return HealthStatus(
            healthy=True,
            backend=self.name,
            detail="API key configured (verified on first generation)",
            info={"model": self.model, "base_url": self.base_url},
        )

    def close(self) -> None:
        self._client.close()


class PollinationsImageGenerator(ImageGenerator):
    """Pollinations.ai — free, no API key. Rate limited and best effort."""

    name = "pollinations"

    def __init__(
        self,
        base_url: str = "https://image.pollinations.ai",
        model: str = "flux",
        timeout_seconds: float = 240.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._client = httpx.Client(timeout=timeout_seconds, follow_redirects=True)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        started = time.perf_counter()
        path = urllib.parse.quote(request.prompt.strip()[:2000], safe="")
        params = {
            "width": request.width,
            "height": request.height,
            "seed": request.seed,
            "model": self.model,
            "nologo": "true",
            "private": "true",
        }

        try:
            response = self._client.get(f"{self.base_url}/prompt/{path}", params=params)
        except httpx.HTTPError as exc:
            raise GenerationError(f"Cannot reach Pollinations: {exc}") from exc

        if response.status_code >= 400:
            raise GenerationError(
                f"Pollinations returned {response.status_code}: {response.text[:300]}"
            )

        save_image_bytes(response.content, request)

        return GenerationResult(
            output_path=request.output_path,
            seed=request.seed,
            duration_ms=int((time.perf_counter() - started) * 1000),
            backend=self.name,
            metadata={"model": self.model},
        )

    def health_check(self) -> HealthStatus:
        try:
            response = self._client.get(f"{self.base_url}/models", timeout=10.0)
            reachable = response.status_code < 500
        except httpx.HTTPError as exc:
            return HealthStatus(
                healthy=False,
                backend=self.name,
                detail=f"Pollinations unreachable: {exc}",
                info={"base_url": self.base_url},
            )
        return HealthStatus(
            healthy=reachable,
            backend=self.name,
            detail="Pollinations reachable (free tier, rate limited)",
            info={"base_url": self.base_url, "model": self.model},
        )

    def close(self) -> None:
        self._client.close()
