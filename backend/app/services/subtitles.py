"""Emit a subtitle (.srt) sidecar from the narrated timeline.

Runs on every render, so each video ships with captions for accessibility and
reach — no manual work. Uses the reflowed scene timings, so cues land on speech.
"""
from pathlib import Path

from app.models import JobItem


def _ts(seconds: float) -> str:
    seconds = max(seconds, 0.0)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(items: list[JobItem], path: Path) -> Path | None:
    """Write an SRT of every narrated scene. Returns the path, or None if silent."""
    cues = [
        it for it in sorted(items, key=lambda i: i.order_index)
        if (it.narration or "").strip()
    ]
    if not cues:
        return None

    blocks = []
    for n, it in enumerate(cues, start=1):
        start = _ts(it.start_seconds)
        end = _ts(max(it.end_seconds - 0.05, it.start_seconds + 0.3))
        blocks.append(f"{n}\n{start} --> {end}\n{it.narration.strip()}\n")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(blocks), encoding="utf-8")
    return path
