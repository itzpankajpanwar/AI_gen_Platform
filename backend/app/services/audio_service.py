"""Narration synthesis, audio-driven re-timing, and the final audio mix."""

import logging
import shutil
import subprocess
from pathlib import Path

from app.config import Settings
from app.models import JobItem
from app.services.csv_service import resolve_music_beds
from app.services.storage import JobStorage
from app.tts import SpeechRequest, SynthesisError, TextToSpeech

logger = logging.getLogger(__name__)


class AudioBuildError(RuntimeError):
    pass


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

    if not narration and not beds:
        return None

    inputs: list[str] = []
    steps: list[str] = []
    voice_labels: list[str] = []
    music_labels: list[str] = []

    for index, (item, path) in enumerate(narration):
        inputs += ["-i", str(path)]
        delay_ms = int(item.start_seconds * 1000)
        steps.append(f"[{index}:a]aresample=44100,adelay={delay_ms}|{delay_ms}[v{index}]")
        voice_labels.append(f"[v{index}]")

    offset = len(narration)
    for index, (path, start, end) in enumerate(beds):
        stream = offset + index
        inputs += ["-stream_loop", "-1", "-i", str(path)]
        delay_ms = int(start * 1000)
        span = max(end - start, 0.1)
        steps.append(
            f"[{stream}:a]aresample=44100,atrim=0:{span:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d=1.5,afade=t=out:st={max(span - 2.0, 0):.3f}:d=2.0,"
            f"volume={settings.music_level_db}dB,adelay={delay_ms}|{delay_ms}[m{index}]"
        )
        music_labels.append(f"[m{index}]")

    if voice_labels:
        steps.append(
            f"{''.join(voice_labels)}amix=inputs={len(voice_labels)}:"
            f"duration=longest:normalize=0[voice]"
        )
    if music_labels:
        steps.append(
            f"{''.join(music_labels)}amix=inputs={len(music_labels)}:"
            f"duration=longest:normalize=0[bed]"
        )

    if voice_labels and music_labels:
        # Duck the bed whenever the narrator speaks.
        steps.append("[voice]asplit=2[voice_out][key]")
        steps.append(
            f"[bed][key]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[bed_duck]"
        )
        steps.append("[voice_out][bed_duck]amix=inputs=2:duration=longest:normalize=0[mix]")
        final = "[mix]"
    elif voice_labels:
        final = "[voice]"
    else:
        final = "[bed]"

    target = storage.job_dir(job_id) / "audio_mix.m4a"
    command = [
        binary, "-y", *inputs,
        "-filter_complex", ";".join(steps),
        "-map", final,
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
