"""Narration synthesis, audio-driven re-timing, and the final audio mix."""

import logging
import shutil
import subprocess
from pathlib import Path

from app.config import Settings
from app.models import JobItem
from app.services.csv_service import resolve_ambience_beds, resolve_music_beds
from app.services.storage import JobStorage
from app.tts import SpeechRequest, SynthesisError, TextToSpeech

logger = logging.getLogger(__name__)


class AudioBuildError(RuntimeError):
    pass


def _sfx_events(ordered: list[JobItem], sfx_dir: Path) -> list[tuple[Path, float]]:
    """One-shot sound effects placed on animation/transition events.

    Derived from each scene — no authoring needed. A transition gets a whoosh;
    the animation gets an accent that matches it (a thud when a map pin lands, a
    shimmer on a reveal, ticks along a timeline, a low sub on a beat hit).
    """
    def sfx(name: str) -> Path | None:
        p = sfx_dir / f"{name}.wav"
        return p if p.is_file() else None

    events: list[tuple[Path, float]] = []
    for i, item in enumerate(ordered):
        start = item.start_seconds
        end = item.end_seconds
        trans = (item.transition or "").lower()
        anim = (item.animation or "").lower()

        # a swish as one scene gives way to the next (skip hard cuts)
        if i > 0 and trans and trans != "cut":
            if w := sfx("whoosh"):
                events.append((w, max(start - 0.12, 0.0)))

        if not anim:
            continue
        if anim.startswith(("map", "geo_map", "where")):
            if t := sfx("thud"):
                events.append((t, start + 0.35))
        elif anim.startswith(("timeline", "doc_timeline")):
            if t := sfx("tick"):
                for k in range(3):
                    at = start + 0.5 + k * max((end - start - 0.8) / 3, 0.4)
                    if at < end:
                        events.append((t, at))
        elif "counter" in anim or "stat" in anim:
            if sh := sfx("shimmer"):
                events.append((sh, start + max((end - start) * 0.7, 0.4)))
        elif anim.startswith(("title", "chapter", "cutout", "reveal", "quote")):
            if sh := sfx("shimmer"):
                events.append((sh, start + 0.15))
        elif anim.startswith("beat"):
            if sb := sfx("sub"):
                events.append((sb, start + 0.1))

        # --- THE TEN MINUTES vocabulary. Each sound is tied to something the
        # picture actually does, rather than decorating the cut.
        elif anim == "city_map":
            if t := sfx("thud"):            # a pin meeting the ground
                events.append((t, start + 0.30))
            if sw := sfx("sweep"):          # the system reading the city
                events.append((sw, start + 0.10))
        elif anim in {"system_diagram", "compare_flow"}:
            if sw := sfx("sweep"):
                events.append((sw, start + 0.12))
        elif anim == "pick_route":
            if t := sfx("tick"):            # one tick per stop on the walk
                for k in range(4):
                    at = start + 0.6 + k * max((end - start - 1.0) / 4, 0.3)
                    if at < end:
                        events.append((t, at))
        elif anim == "scan_confirm":
            if bp := sfx("beep"):           # the barcode reader, four times
                for k in range(4):
                    at = start + 0.5 + k * max((end - start - 0.9) / 4, 0.32)
                    if at < end:
                        events.append((bp, at))
        elif anim == "inventory_sync":
            if bp := sfx("beep"):
                events.append((bp, start + max((end - start) * 0.38, 0.4)))
        elif anim == "phone_ui":
            if tp := sfx("tap"):
                events.append((tp, start + max((end - start) * 0.56, 0.3)))
        elif anim == "clock":
            if t := sfx("tick"):
                events.append((t, start + 0.2))
        elif anim == "sankey":
            if sh := sfx("shimmer"):
                events.append((sh, start + 0.25))
        elif anim in {"ch_card", "title_card", "stat_big"}:
            if im := sfx("impact"):         # the film's only heavy hits
                events.append((im, start + 0.08))
        elif anim == "store_cutaway":
            if w := sfx("whoosh"):
                events.append((w, start + 0.15))
    return events


def synthesize_narration(
    job_id: str,
    items: list[JobItem],
    tts: TextToSpeech,
    storage: JobStorage,
    settings: Settings,
) -> dict[int, tuple[str, float]]:
    """Speak every narrated line. Returns {order_index: (filename, seconds)}.

    A line that fails to synthesise is skipped rather than failing the job —
    the picture still cuts correctly, it just plays silent there.
    """
    storage.audio_dir(job_id).mkdir(parents=True, exist_ok=True)
    rendered: dict[int, tuple[str, float]] = {}

    for item in items:
        if not (item.narration or "").strip():
            continue
        target = storage.audio_path(job_id, item.order_index)
        request = SpeechRequest(
            text=item.narration,
            output_path=target,
            voice=item.voice or settings.tts_voice,
            language=settings.tts_language,
            model=settings.tts_model,
            pace=settings.tts_pace,
            pitch=settings.tts_pitch,
            loudness=settings.tts_loudness,
        )
        try:
            result = tts.synthesize(request)
        except (SynthesisError, Exception) as exc:  # narration must not sink the batch
            logger.warning("%s narration %s failed: %s", job_id, item.order_index, exc)
            continue
        rendered[item.order_index] = (target.name, result.duration_seconds)

    return rendered


def reflow_timeline(items: list[JobItem], minimum_seconds: float = 1.0) -> float:
    """Re-lay the timeline so each scene lasts as long as its narration.

    Scenes without narration keep their authored length. Everything downstream
    of a change shifts with it, so picture and voice stay locked by construction.
    """
    cursor = 0.0
    for item in sorted(items, key=lambda i: i.order_index):
        authored = max(item.end_seconds - item.start_seconds, 0.0)
        spoken = item.audio_seconds or 0.0
        duration = max(spoken, minimum_seconds) if spoken else authored
        item.start_seconds = round(cursor, 3)
        item.end_seconds = round(cursor + duration, 3)
        cursor += duration
    return round(cursor, 3)


def build_audio_track(
    job_id: str,
    items: list[JobItem],
    storage: JobStorage,
    settings: Settings,
    total_seconds: float,
) -> Path | None:
    """Lay narration clips at their scene starts and mix a ducked music bed under them."""
    binary = shutil.which(settings.ffmpeg_binary)
    if binary is None:
        raise AudioBuildError(f"ffmpeg not found (looked for '{settings.ffmpeg_binary}')")

    ordered = sorted(items, key=lambda i: i.order_index)
    narration = [
        (item, storage.audio_dir(job_id) / item.audio_filename)
        for item in ordered
        if item.audio_filename
    ]
    narration = [(item, path) for item, path in narration if path.is_file()]

    music_dir = settings.asset_path(settings.music_dir)
    beds = []
    for track, start, end in resolve_music_beds(ordered):
        path = music_dir / track
        if not path.is_file():
            logger.warning("%s music '%s' not found in %s — skipping", job_id, track, music_dir)
            continue
        beds.append((path, start, end))

    ambience_dir = settings.asset_path(settings.ambience_dir)
    ambiences = []
    for track, start, end in resolve_ambience_beds(ordered):
        path = ambience_dir / track
        if not path.is_file():
            logger.warning("%s ambience '%s' not found in %s — skipping", job_id, track, ambience_dir)
            continue
        ambiences.append((path, start, end))

    sfx = _sfx_events(ordered, settings.asset_path(settings.sfx_dir))

    if not narration and not beds and not ambiences and not sfx:
        return None

    inputs: list[str] = []
    steps: list[str] = []
    voice_labels: list[str] = []
    music_labels: list[str] = []
    ambience_labels: list[str] = []
    sfx_labels: list[str] = []
    stream = 0

    voice_master = (
        "highpass=f=80,"                                   # cut rumble
        "equalizer=f=200:t=q:w=1.2:g=-2,"                  # tame boxiness
        "equalizer=f=3200:t=q:w=1.6:g=2.5,"                # presence for clarity
        "acompressor=threshold=-18dB:ratio=3:attack=5:release=120,"  # even out level
        "alimiter=limit=0.95"
    ) if settings.voice_master else "anull"
    for item, path in narration:
        inputs += ["-i", str(path)]
        delay_ms = int(item.start_seconds * 1000)
        steps.append(f"[{stream}:a]aresample=44100,{voice_master},adelay={delay_ms}|{delay_ms}[v{stream}]")
        voice_labels.append(f"[v{stream}]")
        stream += 1

    for path, start, end in beds:
        delay_ms = int(start * 1000)
        span = max(end - start, 0.1)
        inputs += ["-stream_loop", "-1", "-i", str(path)]
        steps.append(
            f"[{stream}:a]aresample=44100,atrim=0:{span:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d=1.5,afade=t=out:st={max(span - 2.0, 0):.3f}:d=2.0,"
            f"volume={settings.music_level_db}dB,adelay={delay_ms}|{delay_ms}[s{stream}]"
        )
        music_labels.append(f"[s{stream}]")
        stream += 1

    for path, start, end in ambiences:
        delay_ms = int(start * 1000)
        span = max(end - start, 0.1)
        inputs += ["-stream_loop", "-1", "-i", str(path)]
        steps.append(
            f"[{stream}:a]aresample=44100,atrim=0:{span:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d=2.0,afade=t=out:st={max(span - 2.0, 0):.3f}:d=2.0,"
            f"volume={settings.ambience_level_db}dB,adelay={delay_ms}|{delay_ms}[s{stream}]"
        )
        ambience_labels.append(f"[s{stream}]")
        stream += 1

    for path, at in sfx:
        delay_ms = int(max(at, 0.0) * 1000)
        inputs += ["-i", str(path)]
        steps.append(
            f"[{stream}:a]aresample=44100,volume={settings.sfx_level_db}dB,"
            f"adelay={delay_ms}|{delay_ms}[s{stream}]"
        )
        sfx_labels.append(f"[s{stream}]")
        stream += 1

    if voice_labels:
        steps.append(f"{''.join(voice_labels)}amix=inputs={len(voice_labels)}:duration=longest:normalize=0[voice]")
    if music_labels:
        steps.append(f"{''.join(music_labels)}amix=inputs={len(music_labels)}:duration=longest:normalize=0[music]")
    if ambience_labels:
        steps.append(f"{''.join(ambience_labels)}amix=inputs={len(ambience_labels)}:duration=longest:normalize=0[amb]")
    if sfx_labels:
        steps.append(f"{''.join(sfx_labels)}amix=inputs={len(sfx_labels)}:duration=longest:normalize=0[sfx]")

    # Duck the score under the voice; ambience stays steady (atmosphere persists);
    # SFX ride on top as transient accents. Then mix everything and master.
    layers: list[str] = []
    if voice_labels and music_labels:
        steps.append("[voice]asplit=2[voice_out][key]")
        steps.append("[music][key]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[music_duck]")
        layers += ["[voice_out]", "[music_duck]"]
    elif voice_labels:
        layers.append("[voice]")
    elif music_labels:
        layers.append("[music]")
    if ambience_labels:
        layers.append("[amb]")
    if sfx_labels:
        layers.append("[sfx]")

    if len(layers) > 1:
        steps.append(f"{''.join(layers)}amix=inputs={len(layers)}:duration=longest:normalize=0[mix]")
        final = "[mix]"
    else:
        final = layers[0]

    # Master to a consistent broadcast loudness (YouTube ~-15 LUFS) with headroom.
    # apad fills to the full length so a short layer (e.g. only SFX) never lets
    # the later -shortest mux trim the picture.
    steps.append(f"{final}loudnorm=I={settings.master_lufs}:TP=-1.5:LRA=11,aresample=44100,apad[master]")

    target = storage.job_dir(job_id) / "audio_mix.m4a"
    command = [
        binary, "-y", *inputs,
        "-filter_complex", ";".join(steps),
        "-map", "[master]",
        "-t", f"{total_seconds:.3f}",
        "-c:a", "aac", "-b:a", "192k",
        str(target),
    ]
    completed = subprocess.run(
        command, capture_output=True, text=True, timeout=settings.video_timeout_seconds
    )
    if completed.returncode != 0 or not target.is_file():
        tail = (completed.stderr or "").strip().splitlines()[-6:]
        raise AudioBuildError("ffmpeg failed building the audio mix: " + " | ".join(tail))
    return target


def mux(video: Path, audio: Path, settings: Settings) -> None:
    """Attach the finished audio mix to the finished picture without re-encoding video."""
    binary = shutil.which(settings.ffmpeg_binary)
    if binary is None:
        raise AudioBuildError(f"ffmpeg not found (looked for '{settings.ffmpeg_binary}')")

    combined = video.with_name(video.stem + ".muxed.mp4")
    command = [
        binary, "-y", "-i", str(video), "-i", str(audio),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(combined),
    ]
    completed = subprocess.run(
        command, capture_output=True, text=True, timeout=settings.video_timeout_seconds
    )
    if completed.returncode != 0 or not combined.is_file():
        tail = (completed.stderr or "").strip().splitlines()[-6:]
        raise AudioBuildError("ffmpeg failed muxing audio: " + " | ".join(tail))
    combined.replace(video)
