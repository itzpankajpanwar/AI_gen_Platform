import csv
import io
from dataclasses import dataclass, field

from app.config import Settings
from app.services.animations import ANIMATIONS, CAMERA_ONLY, TEXT_REQUIRED
from app.services.remotion import (
    NO_IMAGE_TEMPLATES,
    ParamError,
    TEMPLATES as REMOTION_TEMPLATES,
)
from app.services.remotion import parse_params, validate as validate_animation
from app.services.style import (
    DEFAULT_TRANSITION_SECONDS,
    DEFAULT_ZOOM,
    KEN_BURNS,
    MAX_ZOOM,
    TRANSITIONS,
    StyleError,
    parse_grade,
    parse_grain,
    parse_text_type,
    parse_valued,
)

START_HEADERS = {"start", "start_seconds", "from", "begin"}
END_HEADERS = {"end", "end_seconds", "to", "stop"}
PROMPT_HEADERS = {"prompt", "text", "description"}
OPTIONAL_HEADERS = {
    "transition",
    "ken_burns",
    "grade",
    "grain",
    "music",
    "text_type",
    "text_value",
    "narration",
    "voice",
    "animation",
    "animation_params",
    "image",
    "ambience",
}
#: Every word the `animation` column accepts — ffmpeg presets and Remotion
#: templates live in one namespace so an author never picks an engine.
ANIMATION_VOCABULARY = {**ANIMATIONS, **REMOTION_TEMPLATES}
MAX_REPORTED_ERRORS = 25
EPSILON = 0.001


@dataclass(frozen=True)
class ParsedPrompt:
    external_id: str
    text: str
    order_index: int
    start_seconds: float
    end_seconds: float

    transition: str | None = None
    transition_seconds: float | None = None
    ken_burns: str | None = None
    ken_burns_scale: float | None = None
    grade: str | None = None
    grain: int | None = None
    music: str | None = None
    ambience: str | None = None
    text_type: str | None = None
    text_value: str | None = None
    narration: str | None = None
    voice: str | None = None
    animation: str | None = None
    animation_value: float | None = None
    animation_params: str | None = None
    needs_image: bool = True

    @property
    def duration(self) -> float:
        return self.end_seconds - self.start_seconds


@dataclass
class CsvValidationResult:
    valid: bool
    total: int = 0
    duration_seconds: float = 0.0
    prompts: list[ParsedPrompt] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def narrated_count(self) -> int:
        return sum(1 for prompt in self.prompts if prompt.narration)


def _decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("File is not valid UTF-8 text")


def _resolve_headers(fieldnames: list[str] | None) -> tuple[dict[str, str], list[str]]:
    """Map our canonical column names onto whatever the file actually calls them."""
    if not fieldnames:
        return {}, []

    normalised = {(name or "").strip().lower(): name for name in fieldnames}
    resolved: dict[str, str] = {}

    for canonical, aliases in (("start", START_HEADERS), ("end", END_HEADERS), ("prompt", PROMPT_HEADERS)):
        match = next((normalised[key] for key in normalised if key in aliases), None)
        if match:
            resolved[canonical] = match

    for name in OPTIONAL_HEADERS:
        if name in normalised:
            resolved[name] = normalised[name]

    unknown = [
        original
        for key, original in normalised.items()
        if key not in OPTIONAL_HEADERS
        and key not in START_HEADERS
        and key not in END_HEADERS
        and key not in PROMPT_HEADERS
        and key.strip()
    ]
    return resolved, unknown


def _parse_seconds(raw: str) -> float:
    """Plain seconds (7, 7.5) or mm:ss / hh:mm:ss timecodes."""
    value = raw.strip()
    if ":" in value:
        parts = value.split(":")
        if len(parts) > 3:
            raise ValueError(f"'{raw}' is not a valid time")
        total = 0.0
        for part in parts:
            total = total * 60 + float(part)
        return total
    return float(value)


def _parse_image_flag(raw: str, animation_name: str) -> bool:
    """Whether this row needs a generated image (an API hit).

    Explicit yes/no wins; a blank cell defaults to no for self-drawing
    animations (geo_map) and yes for everything else.
    """
    text = (raw or "").strip().lower()
    if text in {"no", "false", "0", "n", "off", "skip"}:
        return False
    if text in {"yes", "true", "1", "y", "on"}:
        return True
    return animation_name not in NO_IMAGE_TEMPLATES


def _cell(row: dict, headers: dict[str, str], name: str) -> str:
    key = headers.get(name)
    if key is None:
        return ""
    return (row.get(key) or "").strip()


def parse_csv(data: bytes, settings: Settings) -> CsvValidationResult:
    result = CsvValidationResult(valid=False)

    if len(data) > settings.max_csv_bytes:
        limit_mb = settings.max_csv_bytes / (1024 * 1024)
        result.errors.append(f"CSV is larger than the {limit_mb:.0f} MB limit")
        return result
    if not data.strip():
        result.errors.append("CSV file is empty")
        return result

    try:
        text = _decode(data)
    except ValueError as exc:
        result.errors.append(str(exc))
        return result

    reader = csv.DictReader(io.StringIO(text))
    headers, unknown = _resolve_headers(reader.fieldnames)
    for required in ("start", "end", "prompt"):
        if required not in headers:
            result.errors.append(f"CSV must contain a '{required}' column")
    if result.errors:
        return result
    if unknown:
        result.warnings.append(f"Ignoring unrecognised column(s): {', '.join(sorted(unknown))}")

    parsed: list[ParsedPrompt] = []
    order_index = 0

    for row_number, row in enumerate(reader, start=2):
        raw_start = _cell(row, headers, "start")
        raw_end = _cell(row, headers, "end")
        raw_prompt = _cell(row, headers, "prompt")
        if not any((raw_start, raw_end, raw_prompt)):
            continue  # tolerate blank trailing lines

        order_index += 1
        # csv.DictReader files surplus values under None. A cell holding commas
        # — an animation_params list, say — that was not quoted lands here, and
        # silently losing half of it is worse than refusing the row.
        if row.get(None):
            result.errors.append(
                f"Row {row_number}: more values than there are columns — a cell "
                f"containing commas must be wrapped in double quotes "
                f"(stray: {', '.join(str(extra) for extra in row[None])[:60]})"
            )
            continue
        raw_animation = _cell(row, headers, "animation")
        anim_name = raw_animation.split(":")[0].strip().lower()
        needs_image = _parse_image_flag(_cell(row, headers, "image"), anim_name)
        if needs_image and not raw_prompt:
            result.errors.append(
                f"Row {row_number}: prompt is empty (set image=no for a self-drawing "
                f"animation like geo_map, which needs no image)"
            )
            continue
        if not raw_prompt:
            raw_prompt = f"({anim_name or 'graphic'})"  # placeholder text; no image is generated
        try:
            start_seconds = _parse_seconds(raw_start)
            end_seconds = _parse_seconds(raw_end)
        except ValueError:
            result.errors.append(
                f"Row {row_number}: start and end must be seconds or mm:ss "
                f"(got '{raw_start}' and '{raw_end}')"
            )
            continue

        if start_seconds < 0:
            result.errors.append(f"Row {row_number}: start cannot be negative")
            continue
        if end_seconds <= start_seconds:
            result.errors.append(
                f"Row {row_number}: end ({end_seconds:g}s) must be greater than "
                f"start ({start_seconds:g}s)"
            )
            continue

        try:
            transition, transition_seconds = parse_valued(
                _cell(row, headers, "transition"), TRANSITIONS, "transition"
            )
            ken_burns, ken_burns_scale = parse_valued(
                _cell(row, headers, "ken_burns"), KEN_BURNS, "ken_burns"
            )
            grade = parse_grade(_cell(row, headers, "grade"))
            grain = parse_grain(_cell(row, headers, "grain"))
            text_type = parse_text_type(_cell(row, headers, "text_type"))
            animation, animation_value = parse_valued(
                _cell(row, headers, "animation"), ANIMATION_VOCABULARY, "animation"
            )
            animation_params = parse_params(_cell(row, headers, "animation_params"))
        except (StyleError, ParamError) as exc:
            result.errors.append(f"Row {row_number}: {exc}")
            continue

        if transition_seconds is not None and not 0 < transition_seconds <= 5:
            result.errors.append(
                f"Row {row_number}: transition duration must be between 0 and 5 seconds"
            )
            continue
        if ken_burns_scale is not None and not 1.0 < ken_burns_scale <= MAX_ZOOM:
            result.errors.append(
                f"Row {row_number}: ken_burns scale must be between 1.0 and {MAX_ZOOM}"
            )
            continue

        text_value = _cell(row, headers, "text_value")
        if animation in REMOTION_TEMPLATES:
            problems = validate_animation(animation, animation_params, text_value)
            if problems:
                result.errors.extend(f"Row {row_number}: {problem}" for problem in problems)
                continue
            if animation_value is not None:
                result.warnings.append(
                    f"Row {row_number}: animation '{animation}' takes its settings from "
                    "animation_params, so the ':value' is ignored"
                )
        else:
            if animation in TEXT_REQUIRED and not text_value:
                result.errors.append(
                    f"Row {row_number}: animation '{animation}' needs a text_value to display"
                )
                continue
            if animation_params:
                result.errors.append(
                    f"Row {row_number}: animation_params only applies to the Remotion "
                    f"animations; '{animation or "none"}' is an ffmpeg effect"
                )
                continue
        # A camera-only preset draws no text of its own, so a text_type layers
        # on top of it — motion and caption together. Every other animation owns
        # the scene's text, so text_type there is redundant.
        text_layers = animation in CAMERA_ONLY and text_type
        if animation and _cell(row, headers, "ken_burns"):
            result.warnings.append(
                f"Row {row_number}: animation '{animation}' overrides ken_burns"
            )
        if animation and text_type and not text_layers:
            result.warnings.append(
                f"Row {row_number}: animation '{animation}' already handles its own text, "
                f"so text_type is ignored"
            )
        if text_type and not text_value:
            result.errors.append(
                f"Row {row_number}: text_type '{text_type}' needs a text_value"
            )
            continue
        if text_value and not text_type and not animation:
            result.warnings.append(
                f"Row {row_number}: text_value is set but text_type is empty — no text will show"
            )

        parsed.append(
            ParsedPrompt(
                external_id=str(order_index),
                text=raw_prompt,
                order_index=order_index,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                transition=transition or None,
                transition_seconds=transition_seconds,
                ken_burns=ken_burns or None,
                ken_burns_scale=ken_burns_scale,
                grade=grade,
                grain=grain,
                music=_cell(row, headers, "music") or None,
                ambience=_cell(row, headers, "ambience") or None,
                text_type=text_type,
                text_value=text_value or None,
                narration=_cell(row, headers, "narration") or None,
                voice=_cell(row, headers, "voice") or None,
                animation=animation or None,
                animation_value=animation_value,
                animation_params=_cell(row, headers, "animation_params") or None,
                needs_image=needs_image,
            )
        )

    # The timeline defines the video, so it must be continuous and gap-free.
    parsed.sort(key=lambda item: item.start_seconds)
    expected_start = 0.0
    for item in parsed:
        if abs(item.start_seconds - expected_start) > EPSILON:
            if item.start_seconds > expected_start:
                result.errors.append(
                    f"Gap in the timeline: nothing plays between {expected_start:g}s "
                    f"and {item.start_seconds:g}s"
                )
            else:
                result.errors.append(
                    f"Overlapping segments: '{item.text[:40]}...' starts at "
                    f"{item.start_seconds:g}s but {expected_start:g}s is already taken"
                )
            break
        expected_start = item.end_seconds

    # A transition eats into both neighbours, so it cannot exceed either scene.
    for position, item in enumerate(parsed):
        if not item.transition or item.transition == "cut":
            continue
        seconds = item.transition_seconds or DEFAULT_TRANSITION_SECONDS
        previous = parsed[position - 1].duration if position else None
        shortest = min(filter(None, (previous, item.duration)))
        if seconds > shortest:
            result.errors.append(
                f"Row for '{item.text[:30]}...': transition of {seconds:g}s is longer than "
                f"the {shortest:g}s scene it has to blend with"
            )
            break

    parsed = [
        ParsedPrompt(**{**item.__dict__, "external_id": str(position), "order_index": position})
        for position, item in enumerate(parsed, start=1)
    ]

    result.prompts = parsed
    result.total = len(parsed)
    result.duration_seconds = parsed[-1].end_seconds if parsed else 0.0

    if result.total == 0 and not result.errors:
        result.errors.append("CSV contains no prompt rows")
    if result.total > settings.max_prompts:
        result.errors.append(
            f"CSV contains {result.total} prompts, the maximum is {settings.max_prompts}"
        )
    if 0 < result.total < settings.min_prompts:
        result.errors.append(
            f"CSV contains {result.total} prompts, the minimum is {settings.min_prompts}"
        )

    if len(result.errors) > MAX_REPORTED_ERRORS:
        hidden = len(result.errors) - MAX_REPORTED_ERRORS
        result.errors = result.errors[:MAX_REPORTED_ERRORS] + [f"... and {hidden} more problems"]

    result.valid = not result.errors
    if not result.valid:
        result.prompts = []
        result.duration_seconds = 0.0
    return result


def _resolve_beds(prompts: list[ParsedPrompt], attr: str) -> list[tuple[str, float, float]]:
    """Expand a sparse bed column (music/ambience) into (track, start, end) spans.

    A value starts a bed that plays on until another value appears; the keyword
    `stop` ends it. So authors set it once per chapter, not once per scene.
    """
    beds: list[tuple[str, float, float]] = []
    current: str | None = None
    started_at = 0.0

    for item in prompts:
        cue = (getattr(item, attr) or "").strip()
        if not cue:
            continue
        if current is not None:
            beds.append((current, started_at, item.start_seconds))
        if cue.lower() == "stop":
            current = None
        else:
            current = cue
            started_at = item.start_seconds

    if current is not None and prompts:
        beds.append((current, started_at, prompts[-1].end_seconds))
    return [bed for bed in beds if bed[2] > bed[1]]


def resolve_music_beds(prompts: list[ParsedPrompt]) -> list[tuple[str, float, float]]:
    return _resolve_beds(prompts, "music")


def resolve_ambience_beds(prompts: list[ParsedPrompt]) -> list[tuple[str, float, float]]:
    return _resolve_beds(prompts, "ambience")
