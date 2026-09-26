import io

import httpx
import pytest
from PIL import Image

from app.config import get_settings
from app.generators import (
    GenerationRequest,
    PollinationsImageGenerator,
    RunwareImageGenerator,
    build_generator,
)
from app.generators.imageio import snap


def png_bytes(width: int, height: int) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (90, 60, 30)).save(buffer, format="PNG")
    return buffer.getvalue()


def request_for(tmp_path, width=1280, height=720):
    return GenerationRequest(
        prompt="1947 partition railway platform, documentary still",
        output_path=tmp_path / "001.png",
        width=width,
        height=height,
        steps=4,
        seed=4242,
        model="FLUX.1-schnell",
    )


def test_snap_rounds_to_valid_increments():
    assert snap(1280, 64) == 1280
    assert snap(720, 64) == 704
    assert snap(100, 64) == 128
    assert snap(720, 1) == 720


def test_runware_sends_valid_dimensions_and_resizes_back(tmp_path):
    captured = {}

    def handler(httpx_request: httpx.Request) -> httpx.Response:
        if httpx_request.method == "POST":
            import json

            captured["body"] = json.loads(httpx_request.content)
            captured["auth"] = httpx_request.headers.get("authorization")
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "taskType": "imageInference",
                            "imageURL": "https://cdn.example/img.png",
                            "seed": 4242,
                            "cost": 0.0006,
                        }
                    ]
                },
            )
        return httpx.Response(200, content=png_bytes(1280, 704))

    generator = RunwareImageGenerator(api_key="test-key", model="runware:100@1")
    generator._client = httpx.Client(transport=httpx.MockTransport(handler))

    result = generator.generate(request_for(tmp_path))

    task = captured["body"][0]
    assert captured["auth"] == "Bearer test-key"
    assert task["model"] == "runware:100@1"
    assert task["steps"] == 4
    assert (task["width"], task["height"]) == (1280, 704)  # snapped to a multiple of 64

    with Image.open(result.output_path) as image:
        assert image.size == (1280, 720)  # resized back to the project resolution
    assert result.metadata["cost"] == 0.0006
    assert result.seed == 4242


def test_runware_accepts_bare_object_response(tmp_path):
    def handler(httpx_request: httpx.Request) -> httpx.Response:
        if httpx_request.method == "POST":
            return httpx.Response(200, json={"imageURL": "https://cdn.example/img.png"})
        return httpx.Response(200, content=png_bytes(1280, 704))

    generator = RunwareImageGenerator(api_key="k")
    generator._client = httpx.Client(transport=httpx.MockTransport(handler))

    assert generator.generate(request_for(tmp_path)).output_path.is_file()


def test_runware_surfaces_api_errors(tmp_path):
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text='{"errors":[{"message":"invalid api key"}]}')

    generator = RunwareImageGenerator(api_key="bad")
    generator._client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(Exception, match="Runware rejected"):
        generator.generate(request_for(tmp_path))


def test_runware_without_key_is_unhealthy_and_refuses(tmp_path):
    generator = RunwareImageGenerator(api_key="")

    health = generator.health_check()
    assert health.healthy is False
    assert "RUNWARE_API_KEY" in health.detail

    with pytest.raises(Exception, match="RUNWARE_API_KEY"):
        generator.generate(request_for(tmp_path))


def test_pollinations_builds_prompt_url(tmp_path):
    captured = {}

    def handler(httpx_request: httpx.Request) -> httpx.Response:
        captured["url"] = str(httpx_request.url)
        return httpx.Response(200, content=png_bytes(1280, 720))

    generator = PollinationsImageGenerator()
    generator._client = httpx.Client(transport=httpx.MockTransport(handler))

    result = generator.generate(request_for(tmp_path))

    assert "image.pollinations.ai/prompt/" in captured["url"]
    assert "width=1280" in captured["url"]
    assert "height=720" in captured["url"]
    assert "seed=4242" in captured["url"]
    assert "model=flux" in captured["url"]
    assert result.output_path.is_file()


def test_pollinations_failure_raises(tmp_path):
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(502, text="bad gateway")

    generator = PollinationsImageGenerator()
    generator._client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(Exception, match="502"):
        generator.generate(request_for(tmp_path))


@pytest.mark.parametrize("backend", ["runware", "pollinations"])
def test_hosted_backends_are_selectable(settings, monkeypatch, backend):
    monkeypatch.setenv("GENERATOR_BACKEND", backend)
    get_settings.cache_clear()

    generator = build_generator(get_settings())
    assert generator.name == backend

    get_settings.cache_clear()
