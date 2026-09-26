#!/usr/bin/env python3
"""Assemble the film's smart CSVs from its per-chapter scene files.

Each chapter is one JSON file in `scripts/film/`. A scene there carries the
narration, the subject of the picture, and a shot size — everything that is an
editorial decision. Everything mechanical is derived here:

* **Duration** from the narration's own word count, so pictures stay with the
  voice instead of being hand-timed.
* **Prompt** from subject + shot phrasing + the chapter's palette + the film's
  house style, so a chapter looks like itself and the film looks like one film.
* **Camera move** from the shot size — a wide frame drifts, a detail pushes in.
* **Transition** from how far the shot size jumps: a small change dissolves, a
  big one cuts. That is how an editor cuts, and it means no row has to say so.

    python scripts/build_film.py             # every chapter + the whole film
    python scripts/build_film.py 4           # just chapter 4
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "scripts" / "film"
OUTPUT_DIR = ROOT / "samples" / "film"

WORDS_PER_SECOND = 3.5
MIN_SCENE_SECONDS = 2.0
ROUND_TO = 0.5

HOUSE_STYLE = (
    "cinematic documentary photography, 35mm film, natural light, "
    "shallow depth of field, no text, no lettering, no signage, no logos, 16:9"
)

#: shot -> (phrase added to the prompt, camera move, distance rank)
#: The rank is what the transition rule reads: neighbouring ranks dissolve,
#: distant ones cut.
SHOTS: dict[str, tuple[str, str, int]] = {
    "xwide":    ("extreme wide shot, vast scale, human figures small in frame", "pan_right", 0),
    "wide":     ("wide shot", "zoom_in:1.06", 1),
    "overhead": ("high overhead shot looking straight down", "zoom_out:1.14", 1),
    "medium":   ("medium shot", "zoom_in:1.10", 2),
    "over":     ("over-the-shoulder shot from behind", "zoom_in:1.08", 2),
    "low":      ("low angle shot from ground level", "zoom_in:1.08", 2),
    "close":    ("close shot", "zoom_out:1.12", 3),
    "detail":   ("extreme close-up, detail shot", "zoom_in:1.18", 4),
}

#: A wide frame that drifts right then right again reads as a mistake, so the
#: two horizontal moves alternate.
PAN_ALTERNATES = {"pan_right": "pan_left", "pan_left": "pan_right"}

COLUMNS = [
    "start", "end", "prompt", "transition", "ken_burns", "grade", "grain",
    "music", "text_type", "text_value", "narration", "voice",
    "animation", "animation_params",
]


class BuildError(ValueError):
    pass


def duration_of(narration: str) -> float:
    words = len(narration.split())
    seconds = max(words / WORDS_PER_SECOND, MIN_SCENE_SECONDS)
    return round(seconds / ROUND_TO) * ROUND_TO


def compose_prompt(subject: str, shot: str, palette: str) -> str:
    phrase, _, _ = SHOTS[shot]
    return f"{subject.rstrip('. ')}, {phrase}, {palette}, {HOUSE_STYLE}"


def transition_between(previous: dict | None, scene: dict) -> str:
    """How this scene arrives, unless the scene says otherwise."""
    if "trans" in scene:
        return scene["trans"]
    if previous is None:
        return "fadeblack"
    jump = abs(SHOTS[scene["shot"]][2] - SHOTS[previous["shot"]][2])
    if jump >= 2:
        return "cut"          # a real change of framing wants a hard cut
    if jump == 0:
        return "dissolve:0.7"  # same size twice: a longer blend hides the repeat
    return "dissolve"


def build_chapter(data: dict) -> tuple[list[dict], float]:
    palette = data["palette"]
    rows: list[dict] = []
    cursor = 0.0
    previous: dict | None = None
    last_pan = "pan_left"

    for index, scene in enumerate(data["scenes"]):
        shot = scene.get("shot", "medium")
        if shot not in SHOTS:
            raise BuildError(f"chapter {data['chapter']} scene {index}: unknown shot '{shot}'")

        narration = scene["n"]
        seconds = duration_of(narration)
        animation = scene.get("anim", "")

        move = scene.get("kb") or SHOTS[shot][1]
        if move in PAN_ALTERNATES:
            move = PAN_ALTERNATES[last_pan]
            last_pan = move
        if animation:
            move = ""  # the animation owns the motion

        rows.append({
            "start": f"{cursor:g}",
            "end": f"{cursor + seconds:g}",
            "prompt": compose_prompt(scene["p"], shot, palette),
            "transition": transition_between(previous, scene),
            "ken_burns": move,
            "grade": scene.get("grade", data.get("grade", "")),
            "grain": scene.get("grain", data.get("grain", "")),
            "music": scene.get("music", data.get("music", "") if index == 0 else ""),
            "text_type": scene.get("text_type", ""),
            "text_value": scene.get("text", ""),
            "narration": narration,
            "voice": scene.get("voice", ""),
            "animation": animation,
            "animation_params": scene.get("params", ""),
        })
        cursor += seconds
        previous = scene

    return rows, cursor


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def restart_timeline(rows: list[dict], offset: float, row_offset: int) -> list[dict]:
    """Shift a chapter's rows so they sit after everything before them.

    `split_compare` points at another scene by its row number, which is
    chapter-local in a chapter CSV and film-wide in the combined one — so the
    reference has to move with the rows or it would silently show the wrong
    picture.
    """
    shifted = []
    for row in rows:
        moved = dict(row)
        moved["start"] = f"{float(row['start']) + offset:g}"
        moved["end"] = f"{float(row['end']) + offset:g}"
        params = moved.get("animation_params", "")
        if "second=" in params:
            moved["animation_params"] = ";".join(
                f"second={int(pair.split('=', 1)[1]) + row_offset}"
                if pair.strip().startswith("second=") and pair.split("=", 1)[1].strip().isdigit()
                else pair
                for pair in params.split(";")
            )
        shifted.append(moved)
    return shifted


def main() -> None:
    wanted = set(sys.argv[1:])
    sources = sorted(SOURCE_DIR.glob("part*.json"), key=lambda p: int(p.stem[4:]))
    if not sources:
        raise SystemExit(f"no chapter files in {SOURCE_DIR}")

    whole: list[dict] = []
    offset = 0.0
    total_scenes = 0

    for source in sources:
        data = json.loads(source.read_text(encoding="utf-8"))
        chapter = str(data["chapter"])
        rows, seconds = build_chapter(data)

        if not wanted or chapter in wanted:
            target = OUTPUT_DIR / f"part{int(chapter):02d}.csv"
            write_csv(rows, target)
            animated = sum(1 for row in rows if row["animation"])
            print(
                f"chapter {chapter:>2}  {len(rows):>2} scenes  {seconds:>6.1f}s  "
                f"{animated:>2} animated  -> {target.relative_to(ROOT)}"
            )

        whole.extend(restart_timeline(rows, offset, total_scenes))
        offset += seconds
        total_scenes += len(rows)

    if not wanted:
        target = OUTPUT_DIR / "full_film.csv"
        write_csv(whole, target)
        minutes, seconds = divmod(offset, 60)
        print(
            f"\nwhole film  {total_scenes} scenes  {int(minutes)}m {seconds:.0f}s  "
            f"-> {target.relative_to(ROOT)}"
        )


if __name__ == "__main__":
    main()
