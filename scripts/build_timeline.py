#!/usr/bin/env python3
"""Turn a narration script into a timeline CSV.

Scene durations come from the narration's own word count at a chosen speaking
rate, so the pictures stay in sync with the voice-over without hand-timing
every row.

    python scripts/build_timeline.py part1.json out.csv
"""

import csv
import json
import sys

WORDS_PER_SECOND = 3.5
MIN_SCENE_SECONDS = 2.0
ROUND_TO = 0.5


def scene_duration(narration: str) -> float:
    words = len(narration.split())
    seconds = max(words / WORDS_PER_SECOND, MIN_SCENE_SECONDS)
    return round(seconds / ROUND_TO) * ROUND_TO


def build(scenes: list[dict], style: str) -> tuple[list[list], float]:
    rows: list[list] = []
    cursor = 0.0
    for scene in scenes:
        duration = scene_duration(scene["narration"])
        rows.append([f"{cursor:g}", f"{cursor + duration:g}", scene["prompt"] + style])
        cursor += duration
    return rows, cursor


def main() -> None:
    source = json.loads(open(sys.argv[1], encoding="utf-8").read())
    out_path = sys.argv[2] if len(sys.argv) > 2 else "timeline.csv"

    rows, total = build(source["scenes"], source["style"])
    with open(out_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["start", "end", "prompt"])
        writer.writerows(rows)

    print(f"{len(rows)} scenes, {total:g}s of video -> {out_path}")
    for scene, row in zip(source["scenes"], rows):
        print(f"  {row[0]:>6}-{row[1]:<6} {scene['narration'][:52]}")


if __name__ == "__main__":
    main()
