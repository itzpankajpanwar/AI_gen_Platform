#!/usr/bin/env python3
"""Turn a script + a narration audio file into an animated 9:16 Short.

    python scripts/make_short.py --audio speech.mp3 --script scripts/shorts/gps.json \
        --out samples/clips/gps_short.mp4

The script JSON is just the lines and which scene animates each one; timing is
derived from the audio so captions and visuals land on the actual speech:
  - each line gets a slice of the audio weighted by its character count, then
  - each start is snapped to the nearest real pause (ffmpeg silencedetect),
so you never hand-time anything. Any line may set an explicit "start" to override.

Scenes available: keyword (emoji), list (items), hook, globe, vehicle, where,
clock, beam, statement (default). Params are scene-specific (emoji, items, die,
kind, reveal, mark, fail).
"""
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTION = ROOT / "remotion"
PUBLIC = REMOTION / "public"
FPS = 30

def probe_duration(path: Path) -> float:
    out = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                          "-of","csv=p=0",str(path)], capture_output=True, text=True)
    return float(out.stdout.strip())

def silence_boundaries(path: Path) -> list[float]:
    """Speech onsets: the end of each detected silence (plus 0.0)."""
    out = subprocess.run(["ffmpeg","-hide_banner","-i",str(path),
                          "-af","silencedetect=noise=-32dB:d=0.3","-f","null","-"],
                         capture_output=True, text=True)
    ends = [0.0]
    for m in re.finditer(r"silence_end:\s*([0-9.]+)", out.stderr):
        ends.append(float(m.group(1)))
    return sorted(set(ends))

def char_weight(text: str) -> int:
    return max(1, len(re.sub(r"\s+", "", text)))

def build_segments(lines: list[dict], duration: float, boundaries: list[float]) -> list[dict]:
    lead = min(0.2, boundaries[1] if len(boundaries) > 1 else 0.2)
    weights = [char_weight(l["text"]) for l in lines]
    span = duration - lead
    total_w = sum(weights)
    segs, cursor = [], lead
    for i, line in enumerate(lines):
        start = float(line["start"]) if "start" in line else cursor
        # snap to the nearest real pause within 0.7s for tight sync
        if "start" not in line:
            near = min(boundaries, key=lambda b: abs(b - start))
            if abs(near - start) <= 0.7:
                start = near
        segs.append({
            "start": round(start, 3),
            "text": line["text"],
            "emphasis": line.get("emphasis", ""),
            "scene": line.get("scene", "statement"),
            "params": line.get("params", {}),
        })
        cursor += span * weights[i] / total_w
    # keep strictly increasing
    for i in range(1, len(segs)):
        if segs[i]["start"] <= segs[i-1]["start"]:
            segs[i]["start"] = round(segs[i-1]["start"] + 0.4, 3)
    return segs

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--accent", default=None)
    ap.add_argument("--brand", default=None)
    ap.add_argument("--aspect", default="9x16", choices=["9x16", "16x9"])
    args = ap.parse_args()

    audio = Path(args.audio).expanduser().resolve()
    if not audio.is_file():
        sys.exit(f"audio not found: {audio}")
    spec = json.loads(Path(args.script).read_text(encoding="utf-8"))
    lines = spec["lines"]
    duration = probe_duration(audio)
    boundaries = silence_boundaries(audio)
    segs = build_segments(lines, duration, boundaries)

    # stage the audio where staticFile() can reach it
    PUBLIC.mkdir(parents=True, exist_ok=True)
    staged = f"short_audio{audio.suffix}"
    shutil.copyfile(audio, PUBLIC / staged)
    subprocess.run(["node", "stage-fonts.mjs"], cwd=REMOTION, capture_output=True)

    w, h = (1920, 1080) if args.aspect == "16x9" else (1080, 1920)
    props = {
        "audio": staged,
        "accent": args.accent or spec.get("accent", "#E0A65C"),
        "brand": args.brand or spec.get("brand", "THE QUIET STORY"),
        "fps": FPS,
        "width": w,
        "height": h,
        "durationInFrames": round((duration + 0.2) * FPS),
        "segments": segs,
    }
    props_file = REMOTION / "props.short.json"
    props_file.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")

    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"{len(segs)} scenes over {duration:.1f}s -> rendering {out.name}")
    for s in segs:
        print(f"  {s['start']:6.2f}s  {s['scene']:9}  {s['text'][:44]}")
    cmd = ["npx","remotion","render","src/index.ts","Short",str(out),
           f"--props={props_file}","--codec=h264","--crf=18","--log=error"]
    r = subprocess.run(cmd, cwd=REMOTION)
    props_file.unlink(missing_ok=True)
    if r.returncode != 0:
        sys.exit("render failed")
    print(f"DONE -> {out}")

if __name__ == "__main__":
    main()
