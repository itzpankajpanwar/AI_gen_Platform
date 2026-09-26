import json
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

from app.generators.base import (
    GenerationError,
    GenerationRequest,
    GenerationResult,
    HealthStatus,
    ImageGenerator,
)
from app.generators.imageio import save_image_bytes

PLACEHOLDERS = ("prompt", "seed", "width", "height", "steps", "model")


class ComfyUIImageGenerator(ImageGenerator):
    """Drives a ComfyUI server over its HTTP API.

    The graph itself lives in a workflow JSON file (ComfyUI "API format") so the
    model, sampler and scheduler can change without touching this code. Values
    written as {{prompt}}, {{seed}}, {{width}}, {{height}}, {{steps}} or {{model}}
    in that file are replaced per request.
    """

    name = "comfyui"

    def __init__(
        self,
        base_url: str,
        workflow_path: Path,
        timeout_seconds: float = 600.0,
        poll_seconds: float = 1.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.workflow_path = Path(workflow_path)
        self.timeout_seconds = timeout_seconds
        self.poll_seconds = poll_seconds
        self.client_id = uuid.uuid4().hex
        self._client = httpx.Client(base_url=self.base_url, timeout=30.0)
        self._workflow_cache: tuple[float, dict[str, Any]] | None = None

    # ------------------------------------------------------------------ setup

    def _load_workflow(self) -> dict[str, Any]:
        if not self.workflow_path.exists():
            raise GenerationError(f"ComfyUI workflow not found: {self.workflow_path}")
        mtime = self.workflow_path.stat().st_mtime
        if self._workflow_cache and self._workflow_cache[0] == mtime:
            return self._workflow_cache[1]
        try:
            workflow = json.loads(self.workflow_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise GenerationError(f"Invalid workflow JSON at {self.workflow_path}: {exc}") from exc
        self._workflow_cache = (mtime, workflow)
        return workflow

    @staticmethod
    def _substitute(node: Any, values: dict[str, Any]) -> Any:
        if isinstance(node, dict):
            return {key: ComfyUIImageGenerator._substitute(val, values) for key, val in node.items()}
        if isinstance(node, list):
            return [ComfyUIImageGenerator._substitute(val, values) for val in node]
        if isinstance(node, str):
            stripped = node.strip()
            for key in PLACEHOLDERS:
                token = "{{%s}}" % key
                if stripped == token:
                    return values[key]
                if token in node:
                    node = node.replace(token, str(values[key]))
            return node
        return node

    def build_graph(self, request: GenerationRequest) -> dict[str, Any]:
        values = {
            "prompt": request.prompt,
            "seed": int(request.seed),
            "width": int(request.width),
            "height": int(request.height),
            "steps": int(request.steps),
            "model": request.model,
        }
        return self._substitute(self._load_workflow(), values)

    # ------------------------------------------------------------- generation

    def generate(self, request: GenerationRequest) -> GenerationResult:
        started = time.perf_counter()
        graph = self.build_graph(request)
        prompt_id = self._queue(graph)
        outputs = self._await_outputs(prompt_id, deadline=started + self.timeout_seconds)
        image_ref = self._first_image(outputs, prompt_id)
        data = self._download(image_ref)
        save_image_bytes(data, request)

        duration_ms = int((time.perf_counter() - started) * 1000)
        return GenerationResult(
            output_path=request.output_path,
            seed=request.seed,
            duration_ms=duration_ms,
            backend=self.name,
            metadata={"prompt_id": prompt_id, "source": image_ref, "model": request.model},
        )

    def _queue(self, graph: dict[str, Any]) -> str:
        try:
            response = self._client.post(
                "/prompt", json={"prompt": graph, "client_id": self.client_id}
            )
        except httpx.HTTPError as exc:
            raise GenerationError(f"Cannot reach ComfyUI at {self.base_url}: {exc}") from exc
        if response.status_code >= 400:
            raise GenerationError(f"ComfyUI rejected the workflow: {response.text[:800]}")
        prompt_id = response.json().get("prompt_id")
        if not prompt_id:
            raise GenerationError("ComfyUI did not return a prompt_id")
        return str(prompt_id)

    def _await_outputs(self, prompt_id: str, deadline: float) -> dict[str, Any]:
        while True:
            if time.perf_counter() > deadline:
                raise GenerationError(f"Timed out after {self.timeout_seconds}s waiting for ComfyUI")
            try:
                response = self._client.get(f"/history/{prompt_id}")
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise GenerationError(f"ComfyUI history request failed: {exc}") from exc

            entry = response.json().get(prompt_id)
            if entry:
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    raise GenerationError(f"ComfyUI execution error: {json.dumps(status)[:800]}")
                if status.get("completed") or entry.get("outputs"):
                    return entry.get("outputs", {})
            time.sleep(self.poll_seconds)

    @staticmethod
    def _first_image(outputs: dict[str, Any], prompt_id: str) -> dict[str, Any]:
        for node_output in outputs.values():
            for image in node_output.get("images", []) or []:
                if image.get("type") == "temp":
                    continue
                return image
        raise GenerationError(f"ComfyUI produced no image for prompt {prompt_id}")

    def _download(self, image_ref: dict[str, Any]) -> bytes:
        params = {
            "filename": image_ref.get("filename", ""),
            "subfolder": image_ref.get("subfolder", ""),
            "type": image_ref.get("type", "output"),
        }
        try:
            response = self._client.get("/view", params=params, timeout=120.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GenerationError(f"Could not download image from ComfyUI: {exc}") from exc
        if not response.content:
            raise GenerationError("ComfyUI returned an empty image")
        return response.content

    # ----------------------------------------------------------------- health

    def health_check(self) -> HealthStatus:
        try:
            response = self._client.get("/system_stats", timeout=5.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return HealthStatus(
                healthy=False,
                backend=self.name,
                detail=f"ComfyUI unreachable at {self.base_url}: {exc}",
                info={"base_url": self.base_url},
            )
        stats = response.json()
        devices = stats.get("devices", [])
        return HealthStatus(
            healthy=True,
            backend=self.name,
            detail="ComfyUI reachable",
            info={
                "base_url": self.base_url,
                "workflow": str(self.workflow_path),
                "devices": [
                    {
                        "name": device.get("name"),
                        "type": device.get("type"),
                        "vram_total": device.get("vram_total"),
                        "vram_free": device.get("vram_free"),
                    }
                    for device in devices
                ],
            },
        )

    def close(self) -> None:
        self._client.close()
