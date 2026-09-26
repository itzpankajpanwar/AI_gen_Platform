"""The Remotion animation vocabulary.

The ffmpeg presets in `animations.py` are fast and cheap but limited to what a
filter graph can express — and ffmpeg's `drawbox` in particular freezes its
geometry at init, so anything that should grow or travel cannot. Remotion runs a
real browser per frame, so these templates get eased motion, SVG line drawing,
masking and typography that ffmpeg simply cannot do.

This table is the Python half of `remotion/src/templates/index.ts`: it lets the
CSV validator reject a bad template name or a misspelled parameter before a job
starts, instead of after twenty minutes of rendering. `test_remotion.py` fails
if the two halves drift apart.
"""

from dataclasses import dataclass, field


class ParamError(ValueError):
    pass


@dataclass(frozen=True)
class TemplateSpec:
    """One animation template and the inputs it understands."""

    name: str
    summary: str
    #: "required" | "optional" | "none" — whether text_value must be present.
    text: str = "optional"
    #: Recognised animation_params keys -> what they do.
    params: dict[str, str] = field(default_factory=dict)
    #: Keys without which the template renders nothing meaningful.
    required_params: tuple[str, ...] = ()


_CAMERA = "zoom, pan, curve, travel, dim, vignette, grain"

TEMPLATES: dict[str, TemplateSpec] = {
    # ------------------------------------------------------------- camera
    "ken_burns_pro": TemplateSpec(
        name="ken_burns_pro",
        summary="Eased camera move over the still — the default for talking scenes.",
        text="optional",
        params={
            "zoom": "target scale, e.g. 1.12",
            "pan": "left | right | up | down | none",
            "curve": "GSAP easing name, e.g. power2.inOut",
            "travel": "pan distance in percent of the frame (default 3)",
            "dim": "0-1 darkening over the image",
            "vignette": "0-1 edge darkening (default 0.45)",
            "grain": "0-1 film grain opacity (default 0.06)",
        },
    ),
    "split_compare": TemplateSpec(
        name="split_compare",
        summary="Two stills meeting at a travelling wipe line — before/after, two eras.",
        text="none",
        params={
            "second": "filename of the second image, staged alongside the first",
            "label_a": "caption under the left half",
            "label_b": "caption under the right half",
        },
        required_params=("second",),
    ),
    "cutout_reveal": TemplateSpec(
        name="cutout_reveal",
        summary="A transparent-background subject rising in over the previous image.",
        text="optional",
        params={
            "from": "entrance direction: left | right | bottom (default bottom)",
            "scale": "cutout height as a fraction of the frame (default 0.94)",
            "dim": "0-1 darkening of the background (default 0.25)",
        },
    ),
    # --------------------------------------------------------------- text
    "title_reveal": TemplateSpec(
        name="title_reveal",
        summary="Masked headline wiping up behind a sweeping accent rule.",
        text="required",
        params={"size": "headline height as a fraction of the frame (default 0.085)"},
    ),
    "word_mark": TemplateSpec(
        name="word_mark",
        summary="A single emphatic word or short phrase scaling in over a drawn accent rule.",
        text="required",
        params={"size": "word height as a fraction of the frame (default 0.11)"},
    ),
    "lower_third": TemplateSpec(
        name="lower_third",
        summary="Slab lower third that slides in behind an accent edge and slides out.",
        text="required",
        params={"sub": "second line, e.g. a role or a date"},
    ),
    "quote": TemplateSpec(
        name="quote",
        summary="Pulled quotation revealed word by word above an attribution.",
        text="required",
        params={"by": "attribution line"},
    ),
    "chapter_card": TemplateSpec(
        name="chapter_card",
        summary="Chapter opener: kicker, drawn rule, then the title word by word.",
        text="required",
        params={"chapter": "kicker above the rule, e.g. 'भाग ३'"},
    ),
    # ----------------------------------------------------------- graphics
    "timeline": TemplateSpec(
        name="timeline",
        summary="A year axis that draws itself, with ticks landing one by one.",
        text="optional",
        params={
            "from": "first year on the axis",
            "to": "last year on the axis",
            "marks": "comma-separated years to tick",
            "highlight": "one year to emphasise",
        },
        required_params=("marks",),
    ),
    "map_route": TemplateSpec(
        name="map_route",
        summary="A route drawing across a stylised map via stroke-dashoffset.",
        text="optional",
        params={"path": "space-separated x,y points in percent, e.g. '12,78 34,62 86,32'"},
        required_params=("path",),
    ),
    "geo_map": TemplateSpec(
        name="geo_map",
        summary="A real map of India (true borders and city coordinates) with an eased "
                "camera push, dropping pins, drawn routes and optional state highlight.",
        text="optional",
        params={
            "focus": "city to centre on: mhow, bombay, baroda, mahad, nashik, nagpur, delhi, london, newyork",
            "scale": "final zoom (higher = closer, default 1400)",
            "pins": "comma-separated cities to drop pins on",
            "route": "comma-separated cities to draw a route through, in order",
            "highlight": "a state name to emphasise, e.g. Maharashtra",
        },
    ),
    "stat_counter": TemplateSpec(
        name="stat_counter",
        summary="A number counting up inside a ring that fills as it climbs.",
        text="required",
        params={
            "to": "final value (defaults to the digits in text_value)",
            "from": "starting value (default 0)",
            "suffix": "unit drawn after the number, e.g. '%'",
            "label": "caption under the number",
        },
    ),
    "bar_chart": TemplateSpec(
        name="bar_chart",
        summary="Bars growing in sequence with their labels.",
        text="optional",
        params={
            "values": "comma-separated numbers",
            "labels": "comma-separated labels, same order",
        },
        required_params=("values",),
    ),
    "highlight_callout": TemplateSpec(
        name="highlight_callout",
        summary="A ring drawn onto a point of the image with a leader line and caption.",
        text="required",
        params={
            "x": "centre x in percent of the frame (default 50)",
            "y": "centre y in percent of the frame (default 45)",
            "r": "radius as a fraction of frame height (default 0.12)",
        },
    ),
}

TEMPLATE_NAMES = frozenset(TEMPLATES)
TEXT_REQUIRED = frozenset(name for name, spec in TEMPLATES.items() if spec.text == "required")
#: Templates whose own image is a transparent cutout composited over the
#: previous scene's still (which is passed in as the background).
CUTOUT_TEMPLATES = frozenset({"cutout_reveal"})
#: Templates that draw their own scene and never use a generated still, so
#: a row using one needs no image and should not spend an API call.
NO_IMAGE_TEMPLATES = frozenset({"geo_map"})


def parse_params(raw: str) -> dict[str, str]:
    """Read an `animation_params` cell: `key=value;key=value`.

    Values keep their commas so a template can read them as a list, which is why
    pairs are separated by `;` and not by `,`.
    """
    text = (raw or "").strip()
    if not text:
        return {}

    params: dict[str, str] = {}
    for chunk in text.split(";"):
        piece = chunk.strip()
        if not piece:
            continue
        key, separator, value = piece.partition("=")
        key = key.strip().lower()
        if not separator or not key:
            raise ParamError(f"'{piece}' is not a key=value pair")
        if key in params:
            raise ParamError(f"parameter '{key}' is set twice")
        params[key] = value.strip()
    return params


def validate(template: str, params: dict[str, str], text_value: str) -> list[str]:
    """Problems with one scene's animation, as sentences an author can act on."""
    spec = TEMPLATES.get(template)
    if spec is None:
        options = ", ".join(sorted(TEMPLATES))
        return [f"unknown animation '{template}' (expected one of: {options})"]

    problems: list[str] = []
    if spec.text == "required" and not text_value.strip():
        problems.append(f"animation '{template}' needs a text_value to display")

    unknown = sorted(set(params) - set(spec.params))
    if unknown:
        known = ", ".join(sorted(spec.params)) or "none"
        problems.append(
            f"animation '{template}' does not understand "
            f"{', '.join(unknown)} (it accepts: {known})"
        )
    missing = [key for key in spec.required_params if not params.get(key)]
    if missing:
        problems.append(
            f"animation '{template}' needs animation_params {', '.join(missing)} "
            f"— {'; '.join(spec.params[key] for key in missing)}"
        )
    return problems
