import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image

from app.config import Settings
from app.models import ItemStatus, Job, JobItem, utcnow
from app.services.animations import ANIMATIONS, AnimationContext, build_animation
from app.services.storage import JobStorage
from app.services.style import (
    DEFAULT_TRANSITION_SECONDS,
    DEFAULT_ZOOM,
    GRADES,
    KEN_BURNS,
    TEXT_STYLES,
    TRANSITIONS,
)


@dataclass(frozen=True)
class VideoInfo:
    path: Path
    size_bytes: int
    frame_count: int
    duration_seconds: float
    created_at: datetime
    expires_at: datetime


class VideoBuildError(RuntimeError):
    pass


def ffmpeg_path(settings: Settings) -> str | None:
    return shutil.which(settings.ffmpeg_binary)


def _placeholder(path: Path, width: int, height: int) -> None:
    """Black frame so a failed prompt leaves a gap in the picture, not the timeline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (width, height), (0, 0, 0)).save(path, format="PNG")


def _escape_text(value: str) -> str:
    """Escape a string for ffmpeg's drawtext, which parses : ' \\ and %."""
    return (
        value.replace("\\", "\\\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace("%", r"\%")
    )


def transition_seconds_for(item: JobItem) -> float:
    """How long this scene's incoming blend lasts. Zero for a hard cut."""
    name = (item.transition or "").lower()
    if not name or name == "cut":
        return 0.0
    if TRANSITIONS.get(name, "") == "":
        return 0.0
    return item.transition_seconds or DEFAULT_TRANSITION_SECONDS


def _font_for(settings: Settings, serif: bool) -> str:
    font_path = settings.asset_path(settings.font_serif if serif else settings.font_sans)
    if not font_path.is_file():
        raise VideoBuildError(f"font not found: {font_path}")
    return str(font_path)


def build_scene_filter(item: JobItem, settings: Settings, width: int, height: int, seconds: float) -> str:
    """Motion, grade, grain and text for a single still, as one filter chain."""
    frames = max(int(round(seconds * settings.video_fps)), 1)
    chain: list[str] = []

    animation = (item.animation or "").lower()
    if animation in ANIMATIONS:
        # The animation owns framing, motion and text. Grade and grain still run
        # between its motion and its overlays so the graphics stay ungraded.
        context = AnimationContext(
            width=width,
            height=height,
            seconds=seconds,
            fps=settings.video_fps,
            text=item.text_value or "",
            font=_font_for(settings, serif=animation in {"doc_title_card", "vox_stat"}),
            value=item.animation_value,
        )
        motion, overlay = build_animation(animation, context)
        chain.extend(motion)
        if item.grade and item.grade in GRADES:
            chain.append(GRADES[item.grade])
        if item.grain:
            chain.append(f"noise=alls={int(item.grain)}:allf=t+u")
        chain.extend(overlay)
        chain.append(f"fps={settings.video_fps}")
        chain.append("setsar=1")
        chain.append("format=yuv420p")
        return ",".join(chain)

    move = (item.ken_burns or "static").lower()
    if move != "static" and move in KEN_BURNS:
        _, x_template, y_template = KEN_BURNS[move]
        x_expr = x_template.format(frames=frames)
        y_expr = y_template.format(frames=frames)
        target = item.ken_burns_scale or DEFAULT_ZOOM
        if move.startswith("zoom_out"):
            zoom_expr = f"max({target:.4f}-(on/{frames})*{target - 1:.4f},1.0)"
        elif move.startswith("zoom_in"):
            zoom_expr = f"min(1.0+(on/{frames})*{target - 1:.4f},{target:.4f})"
        else:
            # A pan still needs to be zoomed in slightly or there is nothing to move across.
            zoom_expr = f"{target:.4f}"
        # Upscale first: zoompan samples at output size, so this keeps motion smooth.
        chain.append(f"scale={width * 2}:{height * 2}")
        chain.append(
            f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':"
            f"d={frames}:s={width}x{height}:fps={settings.video_fps}"
        )
    else:
        chain.append(
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
        )

    if item.grade and item.grade in GRADES:
        chain.append(GRADES[item.grade])
    if item.grain:
        chain.append(f"noise=alls={int(item.grain)}:allf=t+u")

    if item.text_type and item.text_value and item.text_type in TEXT_STYLES:
        style = TEXT_STYLES[item.text_type]
        if style.dim_background:
            chain.append(f"eq=brightness=-{style.dim_background * 0.5:.2f}")
        font_path = _font_for(settings, serif=style.serif)

        fade = min(style.fade, seconds / 3)
        alpha = (
            f"if(lt(t,{fade:.2f}),t/{fade:.2f},"
            f"if(lt(t,{seconds - fade:.2f}),1,max(0,({seconds:.2f}-t)/{fade:.2f})))"
            if fade > 0.05
            else "1"
        )
        parts = [
            f"fontfile='{font_path}'",
            f"text='{_escape_text(item.text_value)}'",
            f"fontcolor={style.colour}",
            f"fontsize={max(int(height * style.size_ratio), 12)}",
            f"x={style.x}",
            f"y={style.y}",
            f"alpha='{alpha}'",
        ]
        if style.box:
            parts += ["box=1", "boxcolor=black@%.2f" % style.box_opacity, "boxborderw=18"]
        chain.append("drawtext=" + ":".join(parts))

    # Every clip must expose identical stream properties or the xfade chain
    # fails with "Error reinitializing filters" when it meets the first mismatch.
    chain.append(f"fps={settings.video_fps}")
    chain.append("setsar=1")
    chain.append("format=yuv420p")
    return ",".join(chain)


def _render_scene(
    item: JobItem,
    source: Path,
    target: Path,
    seconds: float,
    settings: Settings,
    binary: str,
    width: int,
    height: int,
) -> None:
    command = [
        binary, "-y",
        "-loop", "1", "-t", f"{seconds:.3f}", "-i", str(source),
        "-vf", build_scene_filter(item, settings, width, height, seconds),
        "-r", str(settings.video_fps),
        "-frames:v", str(max(int(round(seconds * settings.video_fps)), 1)),
        "-c:v", "libx264", "-preset", settings.video_preset, "-crf", str(settings.video_crf),
        "-pix_fmt", "yuv420p",
        str(target),
    ]
    completed = subprocess.run(
        command, capture_output=True, text=True, timeout=settings.video_timeout_seconds
    )
    if completed.returncode != 0 or not target.is_file():
        tail = (completed.stderr or "").strip().splitlines()[-6:]
        raise VideoBuildError(f"ffmpeg failed rendering scene {item.order_index}: " + " | ".join(tail))


def _concat_plain(clips: list[Path], work_dir: Path, target: Path, settings: Settings, binary: str) -> None:
    """Fast path: every transition is a hard cut, so no re-encode is needed."""
    listing = work_dir / "clips.txt"
    listing.write_text("".join(f"file '{clip.as_posix()}'\n" for clip in clips), encoding="utf-8")
    command = [
        binary, "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
        "-c", "copy", "-movflags", "+faststart", str(target),
    ]
    completed = subprocess.run(
        command, capture_output=True, text=True, timeout=settings.video_timeout_seconds
    )
    listing.unlink(missing_ok=True)
    if completed.returncode != 0 or not target.is_file():
        tail = (completed.stderr or "").strip().splitlines()[-6:]
        raise VideoBuildError("ffmpeg failed joining scenes: " + " | ".join(tail))


def _concat_with_transitions(
    clips: list[Path],
    durations: list[float],
    blends: list[float],
    target: Path,
    settings: Settings,
    binary: str,
    names: list[str],
) -> None:
    """Chain xfade so each blend straddles its boundary and total length is preserved."""
    inputs: list[str] = []
    for clip in clips:
        inputs += ["-i", str(clip)]

    steps: list[str] = []
    label = "0:v"
    accumulated = durations[0]
    for index in range(1, len(clips)):
        blend = max(blends[index], 0.001)
        out = f"v{index}"
        offset = max(accumulated - blend, 0.0)
        steps.append(
            f"[{label}][{index}:v]xfade=transition={names[index]}:"
            f"duration={blend:.3f}:offset={offset:.3f}[{out}]"
        )
        accumulated += durations[index] - blend
        label = out

    command = [
        binary, "-y", *inputs,
        "-filter_complex", ";".join(steps),
        "-map", f"[{label}]",
        "-r", str(settings.video_fps),
        "-c:v", "libx264", "-preset", settings.video_preset, "-crf", str(settings.video_crf),
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(target),
    ]
    completed = subprocess.run(
        command, capture_output=True, text=True, timeout=settings.video_timeout_seconds
    )
    if completed.returncode != 0 or not target.is_file():
        tail = (completed.stderr or "").strip().splitlines()[-8:]
        raise VideoBuildError("ffmpeg failed blending scenes: " + " | ".join(tail))


def build_job_video(
    job: Job,
    items: list[JobItem],
    storage: JobStorage,
    settings: Settings,
    width: int,
    height: int,
) -> VideoInfo | None:
    """Render one film: each image held for its window, with motion, grade, text and blends."""
    binary = ffmpeg_path(settings)
    if binary is None:
        raise VideoBuildError(
            f"ffmpeg not found (looked for '{settings.ffmpeg_binary}'). "
            "Install it with: brew install ffmpeg"
        )

    ordered = sorted(items, key=lambda item: item.order_index)
    if not ordered or all(item.status != ItemStatus.SUCCESS for item in ordered):
        return None

    images_dir = storage.images_dir(job.id)
    work_dir = storage.job_dir(job.id) / "clips"
    work_dir.mkdir(parents=True, exist_ok=True)

    # A blend of D seconds steals D/2 from each neighbour, so every clip is
    # rendered long enough to cover its own half of the blends on both sides.
    authored = [transition_seconds_for(item) if index else 0.0 for index, item in enumerate(ordered)]
    use_transitions = any(blend > 0 for blend in authored)

    # Mixing concat and xfade in one graph fails: xfade cannot read the duration
    # of a concat output. So once any blend exists, every boundary becomes an
    # xfade and a hard cut is expressed as a single-frame blend.
    one_frame = 1.0 / settings.video_fps
    blends = [
        (max(blend, one_frame) if index else 0.0) if use_transitions else 0.0
        for index, blend in enumerate(authored)
    ]
    clips: list[Path] = []
    clip_durations: list[float] = []

    for index, item in enumerate(ordered):
        scene_seconds = max(item.end_seconds - item.start_seconds, 0.0)
        if scene_seconds <= 0:
            continue

        source = images_dir / item.filename if item.filename else None
        if item.status != ItemStatus.SUCCESS or source is None or not source.is_file():
            source = images_dir / f"{item.order_index:03d}_missing.png"
            _placeholder(source, width, height)

        pad_in = blends[index] / 2
        pad_out = blends[index + 1] / 2 if index + 1 < len(blends) else 0.0
        clip_seconds = scene_seconds + pad_in + pad_out

        clip = work_dir / f"{item.order_index:04d}.mp4"
        _render_scene(item, source, clip, clip_seconds, settings, binary, width, height)
        clips.append(clip)
        clip_durations.append(clip_seconds)

    if not clips:
        return None

    final_path = storage.video_path(job.id)
    temp_path = final_path.with_name(final_path.name + ".tmp.mp4")
    temp_path.unlink(missing_ok=True)

    if use_transitions:
        names = [
            TRANSITIONS.get((item.transition or "").lower(), "fade") or "fade" for item in ordered
        ]
        _concat_with_transitions(
            clips, clip_durations, blends, temp_path, settings, binary, names
        )
    else:
        _concat_plain(clips, work_dir, temp_path, settings, binary)

    temp_path.replace(final_path)
    shutil.rmtree(work_dir, ignore_errors=True)

    created_at = utcnow()
    return VideoInfo(
        path=final_path,
        size_bytes=final_path.stat().st_size,
        frame_count=sum(1 for item in ordered if item.status == ItemStatus.SUCCESS),
        duration_seconds=max((item.end_seconds for item in ordered), default=0.0),
        created_at=created_at,
        expires_at=created_at + timedelta(hours=settings.zip_retention_hours),
    )
