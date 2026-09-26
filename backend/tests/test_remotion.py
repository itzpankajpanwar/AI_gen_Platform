"""The Remotion animation layer: its vocabulary, its CSV surface, its dispatch."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from app.services import remotion
from app.services.csv_service import parse_csv
from app.services.remotion_service import SceneRender, is_available, project_dir

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_TS = REPO_ROOT / "remotion" / "src" / "templates" / "index.ts"


# ------------------------------------------------------------- the two halves

def test_python_registry_matches_the_typescript_one():
    """The CSV validator must know exactly the templates the renderer can draw.

    If they drift, a job either rejects a valid animation or fails twenty
    minutes into a render with "Unknown template".
    """
    source = REGISTRY_TS.read_text(encoding="utf-8")
    body = source.split("export const TEMPLATES", 1)[1].split("};", 1)[0]
    registered = set(re.findall(r"^\s{2}(\w+):", body, flags=re.MULTILINE))

    assert registered == set(remotion.TEMPLATES), (
        "remotion/src/templates/index.ts and services/remotion.py disagree: "
        f"only in TS {sorted(registered - set(remotion.TEMPLATES))}, "
        f"only in Python {sorted(set(remotion.TEMPLATES) - registered)}"
    )


def test_every_template_documents_its_required_params():
    for spec in remotion.TEMPLATES.values():
        for key in spec.required_params:
            assert key in spec.params, f"{spec.name} requires undocumented param '{key}'"


# -------------------------------------------------------------- param parsing

def test_parse_params_reads_pairs_and_keeps_commas():
    parsed = remotion.parse_params("marks=1891,1927,1956; highlight=1927 ")
    assert parsed == {"marks": "1891,1927,1956", "highlight": "1927"}


def test_parse_params_rejects_a_pair_without_a_value():
    with pytest.raises(remotion.ParamError):
        remotion.parse_params("marks")


def test_parse_params_rejects_a_repeated_key():
    with pytest.raises(remotion.ParamError):
        remotion.parse_params("zoom=1.1;zoom=1.2")


def test_empty_cell_is_no_params():
    assert remotion.parse_params("") == {}
    assert remotion.parse_params("   ") == {}


# ------------------------------------------------------------- template rules

def test_unknown_template_is_named_with_the_alternatives():
    problems = remotion.validate("kenburns_pro", {}, "x")
    assert problems and "ken_burns_pro" in problems[0]


def test_missing_required_param_is_explained():
    problems = remotion.validate("map_route", {}, "")
    assert any("path" in problem for problem in problems)


def test_unknown_param_lists_what_is_accepted():
    problems = remotion.validate("quote", {"colour": "red"}, "text")
    assert any("colour" in problem and "by" in problem for problem in problems)


def test_text_required_templates_need_text():
    assert remotion.validate("title_reveal", {}, "") 
    assert not remotion.validate("title_reveal", {}, "शीर्षक")


# ---------------------------------------------------------------- csv surface

HEADER = "start,end,prompt,animation,animation_params,text_value\n"


def _csv(settings, rows: str):
    return parse_csv((HEADER + rows).encode("utf-8"), settings)


def test_remotion_template_is_accepted_in_the_animation_column(settings):
    result = _csv(settings, '0,4,a courtroom,title_reveal,size=0.09,भीमराव आंबेडकर\n')
    assert result.valid, result.errors
    assert result.prompts[0].animation == "title_reveal"
    assert result.prompts[0].animation_params == "size=0.09"


def test_ffmpeg_presets_still_work_alongside(settings):
    result = _csv(settings, "0,4,a courtroom,cine_dolly,,\n")
    assert result.valid, result.errors
    assert result.prompts[0].animation == "cine_dolly"


def test_bad_param_fails_validation_before_the_job_starts(settings):
    result = _csv(settings, "0,4,a courtroom,timeline,marks=1891;colour=red,\n")
    assert not result.valid
    assert any("colour" in error for error in result.errors)


def test_missing_required_param_fails_validation(settings):
    result = _csv(settings, "0,4,a map,map_route,,\n")
    assert not result.valid
    assert any("path" in error for error in result.errors)


def test_params_on_an_ffmpeg_preset_are_rejected(settings):
    result = _csv(settings, "0,4,a courtroom,cine_dolly,zoom=1.2,\n")
    assert not result.valid
    assert any("animation_params" in error for error in result.errors)


def test_unknown_animation_mentions_both_vocabularies(settings):
    result = _csv(settings, "0,4,a courtroom,sparkle,,\n")
    assert not result.valid
    joined = " ".join(result.errors)
    assert "cine_dolly" in joined and "title_reveal" in joined


# --------------------------------------------------------------- props shape

def test_props_carry_the_dimensions_the_composition_reads(settings):
    scene = SceneRender(
        template="quote",
        text="शिक्षित बनो",
        params={"by": "आंबेडकर"},
        image="scenes/0001.png",
        seconds=3.5,
        width=1280,
        height=720,
        label="scene 1",
    )
    props = scene.props(settings)
    assert props["durationInFrames"] == round(3.5 * settings.video_fps)
    assert (props["width"], props["height"], props["fps"]) == (1280, 720, settings.video_fps)
    # Devanagari must survive the JSON hop to the renderer intact.
    assert json.loads(json.dumps(props, ensure_ascii=False))["text"] == "शिक्षित बनो"


def test_availability_reports_why_it_cannot_run(settings, tmp_path):
    settings.remotion_dir = tmp_path / "absent"
    available, reason = is_available(settings)
    assert not available and "not found" in reason


# ------------------------------------------------------- image flag (API gate)

def test_geo_map_needs_no_image_and_allows_empty_prompt(settings):
    result = parse_csv(
        "start,end,prompt,animation,animation_params\n0,4,,geo_map,focus=mhow\n".encode("utf-8"),
        settings,
    )
    assert result.valid, result.errors
    assert result.prompts[0].needs_image is False


def test_plain_scene_needs_an_image_and_a_prompt(settings):
    ok = parse_csv("start,end,prompt\n0,4,a courtroom\n".encode("utf-8"), settings)
    assert ok.valid and ok.prompts[0].needs_image is True
    empty = parse_csv("start,end,prompt\n0,4,\n".encode("utf-8"), settings)
    assert not empty.valid


def test_image_flag_can_be_forced_either_way(settings):
    off = parse_csv("start,end,prompt,image\n0,4,a courtroom,no\n".encode("utf-8"), settings)
    assert off.valid and off.prompts[0].needs_image is False
    on = parse_csv("start,end,prompt,animation,image\n0,4,a map,geo_map,yes\n".encode("utf-8"), settings)
    assert on.valid and on.prompts[0].needs_image is True
