"""The visual vocabulary of the smart CSV.

Each entry maps a word an author writes in a spreadsheet cell to the ffmpeg
filter fragment that realises it. Keeping them in one table means the CSV
validator and the renderer can never disagree about what a value means.
"""

from dataclasses import dataclass

DEFAULT_TRANSITION_SECONDS = 0.5
DEFAULT_ZOOM = 1.14
MAX_ZOOM = 2.0

# ------------------------------------------------------------------ transitions
# Values accepted in the `transition` column -> ffmpeg xfade transition name.
# "cut" is handled separately: it needs no blend at all.
TRANSITIONS: dict[str, str] = {
    "cut": "",
    "fade": "fade",
    "dissolve": "fade",
    "fadeblack": "fadeblack",
    "fadewhite": "fadewhite",
    "wipeleft": "wipeleft",
    "wiperight": "wiperight",
    "wipeup": "wipeup",
    "wipedown": "wipedown",
    "slideleft": "slideleft",
    "slideright": "slideright",
    "slideup": "slideup",
    "slidedown": "slidedown",
}

# ------------------------------------------------------------------ ken burns
# name -> (is a zoom, pan x expression, pan y expression)
# Expressions use `on` (output frame index); `{frames}` is substituted with the
# clip's total frame count. zoompan exposes no variable for that, so it must be
# baked into the expression as a literal.
KEN_BURNS: dict[str, tuple[bool, str, str]] = {
    "static": (False, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "zoom_in": (True, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "zoom_out": (True, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "pan_left": (False, "(iw-iw/zoom)*(1-on/{frames})", "ih/2-(ih/zoom/2)"),
    "pan_right": (False, "(iw-iw/zoom)*(on/{frames})", "ih/2-(ih/zoom/2)"),
    "pan_up": (False, "iw/2-(iw/zoom/2)", "(ih-ih/zoom)*(1-on/{frames})"),
    "pan_down": (False, "iw/2-(iw/zoom/2)", "(ih-ih/zoom)*(on/{frames})"),
    "zoom_in_pan_left": (True, "(iw-iw/zoom)*(1-on/{frames})", "ih/2-(ih/zoom/2)"),
    "zoom_in_pan_right": (True, "(iw-iw/zoom)*(on/{frames})", "ih/2-(ih/zoom/2)"),
    "zoom_out_pan_left": (True, "(iw-iw/zoom)*(1-on/{frames})", "ih/2-(ih/zoom/2)"),
    "zoom_out_pan_right": (True, "(iw-iw/zoom)*(on/{frames})", "ih/2-(ih/zoom/2)"),
}

# ------------------------------------------------------------------ colour
# Grades are built from eq/colorbalance/curves rather than external LUT files so
# the repo stays self-contained. Swap in lut3d here if you buy a LUT pack.
GRADES: dict[str, str] = {
    "neutral": "eq=contrast=1.03:saturation=1.0",
    "warm": "colorbalance=rs=0.06:gs=0.01:bs=-0.06:rm=0.04:bm=-0.04,eq=contrast=1.05:saturation=0.95:gamma=1.02",
    "cold": "colorbalance=rs=-0.06:gs=-0.01:bs=0.08:rm=-0.03:bm=0.05,eq=contrast=1.06:saturation=0.88",
    "sepia": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,eq=contrast=1.05:brightness=0.02",
    "bleach": "eq=contrast=1.28:saturation=0.45:brightness=0.02",
    "noir": "hue=s=0,eq=contrast=1.35:brightness=-0.02",
}

# ------------------------------------------------------------------ grain
GRAIN_LEVELS: dict[str, int] = {"light": 8, "medium": 18, "heavy": 32}
MAX_GRAIN = 100

# ------------------------------------------------------------------ text
@dataclass(frozen=True)
class TextStyle:
    """Placement and weight for one on-screen text treatment."""

    size_ratio: float  # font size as a fraction of frame height
    x: str
    y: str
    colour: str
    box: bool
    box_opacity: float
    fade: float
    serif: bool = False
    dim_background: float = 0.0  # darken the frame behind the text


TEXT_STYLES: dict[str, TextStyle] = {
    "center_title": TextStyle(0.075, "(w-text_w)/2", "(h-text_h)/2", "white", False, 0.0, 0.6, True),
    "full_card": TextStyle(0.065, "(w-text_w)/2", "(h-text_h)/2", "white", False, 0.0, 0.8, True, 0.55),
    "lower_third": TextStyle(0.042, "w*0.07", "h*0.80", "white", True, 0.45, 0.4),
    "date_stamp": TextStyle(0.034, "w-text_w-w*0.06", "h*0.08", "0xe8d9bd", False, 0.0, 0.4),
    "corner_number": TextStyle(0.030, "w*0.06", "h*0.08", "0xbfae8e", False, 0.0, 0.4),
    "subtitle": TextStyle(0.038, "(w-text_w)/2", "h*0.86", "white", True, 0.5, 0.3),
}


class StyleError(ValueError):
    pass


def parse_valued(raw: str, allowed: dict, field: str) -> tuple[str, float | None]:
    """Split `name:value` cells such as `dissolve:0.8` or `zoom_in:1.2`."""
    text = (raw or "").strip().lower()
    if not text:
        return "", None

    name, _, value_text = text.partition(":")
    name = name.strip()
    if name not in allowed:
        options = ", ".join(sorted(allowed))
        raise StyleError(f"unknown {field} '{name}' (expected one of: {options})")

    if not value_text:
        return name, None
    try:
        return name, float(value_text)
    except ValueError as exc:
        raise StyleError(f"{field} '{raw}' has a non-numeric value after ':'") from exc


def parse_grain(raw: str) -> int | None:
    """`light`/`medium`/`heavy` or a number 0-100."""
    text = (raw or "").strip().lower()
    if not text:
        return None
    if text in GRAIN_LEVELS:
        return GRAIN_LEVELS[text]
    try:
        value = float(text)
    except ValueError as exc:
        raise StyleError(
            f"unknown grain '{raw}' (expected light, medium, heavy or 0-{MAX_GRAIN})"
        ) from exc
    if not 0 <= value <= MAX_GRAIN:
        raise StyleError(f"grain must be between 0 and {MAX_GRAIN}, got {value:g}")
    return int(value)


def parse_grade(raw: str) -> str | None:
    text = (raw or "").strip().lower()
    if not text:
        return None
    if text not in GRADES:
        raise StyleError(f"unknown grade '{raw}' (expected one of: {', '.join(sorted(GRADES))})")
    return text


def parse_text_type(raw: str) -> str | None:
    text = (raw or "").strip().lower()
    if not text:
        return None
    if text not in TEXT_STYLES:
        raise StyleError(
            f"unknown text_type '{raw}' (expected one of: {', '.join(sorted(TEXT_STYLES))})"
        )
    return text
