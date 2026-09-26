#!/usr/bin/env python3
"""Write a sample timeline CSV.

    python scripts/make_sample_csv.py 100 samples.csv 4
"""

import csv
import sys

SCENES = [
    "1940s Indian railway station at dawn, cinematic documentary photography, steam and crowds",
    "young industrialist in a 1920s Bombay office, natural window light, 35mm film grain",
    "1947 Partition railway platform, historical documentary scene, muted colour palette",
    "steel foundry floor in 1950s India, sparks and silhouettes, wide cinematic frame",
    "first tractor rolling off an assembly line, archival documentary still, warm tungsten light",
    "monsoon over a Mumbai dockyard, moody overcast light, anamorphic lens flare",
    "engineers reviewing blueprints by lamplight, 1960s, shallow depth of field",
    "rural Maharashtra farmland at golden hour, aerial documentary establishing shot",
    "1970s boardroom portrait, formal composition, soft key light",
    "modern electric SUV on a coastal highway, dusk, cinematic colour grade",
]


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    path = sys.argv[2] if len(sys.argv) > 2 else "sample_prompts.csv"
    seconds = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0

    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["start", "end", "prompt"])
        cursor = 0.0
        for index in range(1, count + 1):
            scene = SCENES[(index - 1) % len(SCENES)]
            writer.writerow([f"{cursor:g}", f"{cursor + seconds:g}", f"{scene}, shot {index}"])
            cursor += seconds

    print(f"Wrote {count} scenes ({cursor:g}s of video) to {path}")


if __name__ == "__main__":
    main()
