#!/usr/bin/env python3
"""Synthesize royalty-free ambient score beds for the documentary.

These are generated with ffmpeg (layered detuned sine chords + slow tremolo +
reverb + warmth), so they are 100% original and safe to monetize — no licensing.
They are placeholders that sound like a calm documentary pad; swap in real tracks
from the YouTube Audio Library / Pixabay any time (same filenames).

    python scripts/make_music.py            # writes assets/music/*.mp3

Moods (set the `music` CSV column to the filename):
  somber.mp3  warm.mp3  tension.mp3  hopeful.mp3
"""
import shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "music"
DUR = 45  # seconds; the pipeline loops it to fill any length

# mood -> list of (frequency Hz, gain) building a chord pad
MOODS = {
    "somber":  [(110.00, 0.55), (130.81, 0.30), (164.81, 0.26), (220.00, 0.14)],  # A minor, low
    "warm":    [(130.81, 0.50), (164.81, 0.30), (196.00, 0.26), (261.63, 0.14)],  # C major
    "tension": [(73.42, 0.55), (146.83, 0.30), (174.61, 0.24), (207.65, 0.12)],   # D minor + unease
    "hopeful": [(196.00, 0.44), (246.94, 0.30), (293.66, 0.26), (392.00, 0.14)],  # G major, brighter
}

def build(mood: str, tones: list[tuple[float, float]], binary: str) -> Path:
    inputs, vols, labels = [], [], []
    for i, (freq, gain) in enumerate(tones):
        inputs += ["-f", "lavfi", "-i", f"sine=frequency={freq}:duration={DUR}"]
        vols.append(f"[{i}]volume={gain}[t{i}]")
        labels.append(f"[t{i}]")
    graph = (
        ";".join(vols) + ";" +
        "".join(labels) + f"amix=inputs={len(tones)}:normalize=0[m];" +
        # slow movement + reverb + warmth + gentle stereo + loop-friendly fades
        "[m]tremolo=f=0.12:d=0.35,"
        "aecho=0.8:0.9:900|1600:0.35|0.25,"
        "lowpass=f=1900,highpass=f=55,"
        f"afade=t=in:d=4,afade=t=out:st={DUR-4}:d=4,"
        "aformat=channel_layouts=stereo,volume=1.3[out]"
    )
    target = OUT / f"{mood}.mp3"
    cmd = [binary, "-y", *inputs, "-filter_complex", graph, "-map", "[out]",
           "-ar", "44100", "-b:a", "192k", str(target)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not target.is_file():
        raise SystemExit("ffmpeg failed:\n" + "\n".join(r.stderr.splitlines()[-8:]))
    return target

def main() -> None:
    binary = shutil.which("ffmpeg") or sys.exit("ffmpeg not found")
    OUT.mkdir(parents=True, exist_ok=True)
    for mood, tones in MOODS.items():
        p = build(mood, tones, binary)
        print(f"  {mood:8} -> {p.relative_to(ROOT)} ({p.stat().st_size//1024} KB)")
    print("done — set the CSV `music` column to e.g. somber.mp3")

if __name__ == "__main__":
    main()
