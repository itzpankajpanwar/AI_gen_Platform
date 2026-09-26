import json

import pytest

from app.config import get_settings
from app.generators import GenerationRequest, build_generator
from app.generators.comfyui import ComfyUIImageGenerator


def request_for(tmp_path, prompt="a cinematic still"):
    return GenerationRequest(
        prompt=prompt,
        output_path=tmp_path / "001.png",
        width=128,
        height=72,
        steps=4,
        seed=1234,
        model="FLUX.1-schnell",
    )


def test_mock_generator_writes_requested_size(settings, tmp_path):
    from PIL import Image

    generator = build_generator(settings)
    result = generator.generate(request_for(tmp_path))

    assert result.output_path.is_file()
    assert result.seed == 1234
    with Image.open(result.output_path) as image:
        assert image.size == (128, 72)


def test_mock_generator_failure_rate_raises(settings, tmp_path):
    from app.generators import MockImageGenerator

    generator = MockImageGenerator(delay_seconds=0, failure_rate=1.0)
    with pytest.raises(Exception, match="simulated failure"):
        generator.generate(request_for(tmp_path))


def test_backend_is_selected_by_configuration(settings, monkeypatch):
    monkeypatch.setenv("GENERATOR_BACKEND", "comfyui")
    get_settings.cache_clear()
    generator = build_generator(get_settings())

    assert isinstance(generator, ComfyUIImageGenerator)
    assert generator.name == "comfyui"

    get_settings.cache_clear()


def test_unknown_backend_is_rejected(settings, monkeypatch):
    monkeypatch.setattr(settings, "generator_backend", "does-not-exist")

    with pytest.raises(ValueError, match="Unknown GENERATOR_BACKEND"):
        build_generator(settings)


def test_comfyui_workflow_placeholders_are_substituted(tmp_path):
    workflow = {
        "6": {"inputs": {"text": "{{prompt}}"}, "class_type": "CLIPTextEncode"},
        "5": {"inputs": {"width": "{{width}}", "height": "{{height}}", "batch_size": 1}},
        "31": {"inputs": {"seed": "{{seed}}", "steps": "{{steps}}"}},
        "9": {"inputs": {"filename_prefix": "batch/{{seed}}"}},
    }
    path = tmp_path / "workflow.json"
    path.write_text(json.dumps(workflow), encoding="utf-8")

    generator = ComfyUIImageGenerator(base_url="http://localhost:8188", workflow_path=path)
    graph = generator.build_graph(request_for(tmp_path, prompt="1947 partition scene"))

    assert graph["6"]["inputs"]["text"] == "1947 partition scene"
    assert graph["5"]["inputs"]["width"] == 128
    assert graph["5"]["inputs"]["height"] == 72
    assert graph["31"]["inputs"]["seed"] == 1234
    assert graph["31"]["inputs"]["steps"] == 4
    assert graph["9"]["inputs"]["filename_prefix"] == "batch/1234"


def test_comfyui_health_check_reports_unreachable_backend(tmp_path):
    generator = ComfyUIImageGenerator(
        base_url="http://127.0.0.1:9", workflow_path=tmp_path / "missing.json"
    )
    health = generator.health_check()

    assert health.healthy is False
    assert "unreachable" in health.detail
