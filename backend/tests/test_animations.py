import pytest

from app.models import JobItem
from app.services.animations import ANIMATIONS, TEXT_REQUIRED, AnimationContext, build_animation
from app.services.csv_service import parse_csv
from app.services.video_service import build_scene_filter

HEADER = (
    "start,end,prompt,transition,ken_burns,grade,grain,music,"
    "text_type,text_value,narration,voice,animation\n"
)


def build(rows: str) -> bytes:
    return (HEADER + rows).encode("utf-8")


def context(**overrides) -> AnimationContext:
    base = dict(width=640, height=360, seconds=4.0, fps=30, text="महू छावनी", font="/tmp/f.ttf")
    base.update(overrides)
    return AnimationContext(**base)


# --------------------------------------------------------------------- presets


@pytest.mark.parametrize("name", sorted(ANIMATIONS))
def test_every_preset_produces_filters(name):
    motion, overlay = build_animation(name, context())

    assert motion, f"{name} produced no motion filters"
    assert all(isinstance(part, str) and part for part in motion + overlay)
    # No unresolved python format placeholder may reach ffmpeg. `%{eif...}` is a
    # legitimate ffmpeg text-expansion token, so only bare {name} braces count.
    import re

    for part in motion + overlay:
        leftover = re.findall(r"(?<!%)\{[a-z_]+\}", part)
        assert not leftover, f"{name} leaked {leftover}"


@pytest.mark.parametrize("name", sorted(TEXT_REQUIRED - {"type_counter"}))
def test_text_presets_render_their_text(name):
    _, overlay = build_animation(name, context(text="भीमराव"))

    assert any("drawtext" in part and "भीमराव" in part for part in overlay)


def test_counter_counts_up_to_its_number():
    _, overlay = build_animation("type_counter", context(text="1891", seconds=4.0))
    chain = "".join(overlay)

    assert "eif" in chain          # ffmpeg evaluates the figure per frame
    assert "1891" in chain
    assert "drawtext" in chain


def test_counter_survives_a_non_numeric_value():
    _, overlay = build_animation("type_counter", context(text="not a number"))

    assert "*0" in "".join(overlay)  # falls back to zero rather than crashing


def test_stack_splits_lines_on_a_pipe():
    _, overlay = build_animation("type_stack", context(text="पहली|दूसरी|तीसरी"))

    assert len([part for part in overlay if "drawtext" in part]) == 3
    assert all(any(word in part for part in overlay) for word in ("पहली", "दूसरी", "तीसरी"))


def test_optional_text_presets_skip_text_when_empty():
    for name in ("map_zoom", "map_reveal", "doc_archival", "doc_photo"):
        _, overlay = build_animation(name, context(text=""))
        assert not any("drawtext" in part for part in overlay), name


def test_animation_value_changes_intensity():
    gentle, _ = build_animation("map_zoom", context(value=1.2))
    strong, _ = build_animation("map_zoom", context(value=2.5))

    assert "1.2000" in "".join(gentle)
    assert "2.5000" in "".join(strong)


def test_unknown_preset_raises():
    with pytest.raises(KeyError):
        build_animation("does_not_exist", context())


def test_text_is_escaped_for_drawtext():
    _, overlay = build_animation("vox_title", context(text="10:30 'x' 5%"))
    joined = "".join(overlay)

    assert r"10\:30" in joined
    assert r"\'x\'" in joined
    assert r"5\%" in joined


# ------------------------------------------------------------------ CSV layer


def test_animation_column_parses(settings):
    result = parse_csv(build('0,4,"scene",,,,,,,"1891",,,doc_timeline\n'), settings)

    assert result.valid, result.errors
    assert result.prompts[0].animation == "doc_timeline"
    assert result.prompts[0].text_value == "1891"


def test_animation_value_parses(settings):
    result = parse_csv(build('0,4,"scene",,,,,,,,,,map_zoom:2.4\n'), settings)

    assert result.valid, result.errors
    assert result.prompts[0].animation == "map_zoom"
    assert result.prompts[0].animation_value == 2.4


def test_unknown_animation_is_rejected_with_options(settings):
    result = parse_csv(build('0,4,"scene",,,,,,,,,,tiktok_zoom\n'), settings)

    assert not result.valid
    assert any("unknown animation" in error for error in result.errors)
    assert any("vox_title" in error for error in result.errors)


def test_text_requiring_animation_without_text_is_rejected(settings):
    result = parse_csv(build('0,4,"scene",,,,,,,,,,vox_title\n'), settings)

    assert not result.valid
    assert any("needs a text_value" in error for error in result.errors)


def test_animation_warns_that_it_overrides_other_effects(settings):
    result = parse_csv(build('0,4,"scene",,zoom_in,,,,center_title,"x",,,vox_stat\n'), settings)

    assert result.valid, result.errors
    assert any("overrides ken_burns and text_type" in w for w in result.warnings)


# ------------------------------------------------------------- render wiring


def test_animation_replaces_ken_burns_and_text_style(settings):
    item = JobItem(
        order_index=1,
        ken_burns="zoom_in",
        text_type="lower_third",
        text_value="महू छावनी",
        animation="vox_lower_bar",
    )

    chain = build_scene_filter(item, settings, 640, 360, 4.0)

    assert "drawbox" in chain          # the animation's own bar
    assert "zoompan" not in chain      # ken_burns ignored
    assert chain.count("drawtext") == 1  # only the animation's text, not lower_third


def test_grade_and_grain_still_apply_under_an_animation(settings):
    item = JobItem(
        order_index=1, animation="doc_photo", grade="sepia", grain=20, text_value=""
    )

    chain = build_scene_filter(item, settings, 640, 360, 4.0)

    assert "colorchannelmixer" in chain
    assert "noise=alls=20" in chain


def test_animation_chain_is_normalised_like_every_other_clip(settings):
    chain = build_scene_filter(
        JobItem(order_index=1, animation="map_pin", text_value="महू"), settings, 640, 360, 4.0
    )

    assert chain.endswith("fps=12,setsar=1,format=yuv420p") or "setsar=1" in chain
