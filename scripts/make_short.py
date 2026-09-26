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
import argparse, hashlib, json, re, shutil, subprocess, sys
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

def generate_backgrounds(lines: list[dict], aspect: str) -> None:
    """Generate one photographic background per line that has a `bg` prompt.

    Uses the project's OpenAI backend. Cached by prompt+size hash under
    remotion/public/short_bg, so re-runs never re-spend on the same image.
    Each line gets params.bg set to the staticFile path; failures fall back to
    the animated space backdrop (no crash, no cost).
    """
    if not any(l.get("bg") for l in lines):
        return
    sys.path.insert(0, str(ROOT / "backend"))
    from app.config import get_settings
    from app.generators.api_backends import OpenAIImageGenerator
    from app.generators.base import GenerationError, GenerationRequest
    s = get_settings()
    if not s.openai_api_key:
        print("  (no OPENAI_API_KEY — skipping backgrounds, using animated space)")
        return
    w, h = (1920, 1080) if aspect == "16x9" else (1080, 1920)
    size = "1536x1024" if aspect == "16x9" else "1024x1536"
    gen = OpenAIImageGenerator(api_key=s.openai_api_key, model=s.openai_image_model,
                               size=size, quality=s.openai_image_quality,
                               base_url=s.openai_base_url, timeout_seconds=s.api_timeout_seconds)
    cache = PUBLIC / "short_bg"; cache.mkdir(parents=True, exist_ok=True)
    STYLE = ("cinematic, photorealistic, dark moody atmosphere, deep shadows, "
             "muted teal and amber tones, subtle depth, no text, no watermark")
    for i, line in enumerate(lines):
        prompt = line.get("bg")
        if not prompt:
            continue
        full = f"{prompt}, {STYLE}"
        key = hashlib.md5(f"{full}|{size}".encode()).hexdigest()[:16]
        rel = f"short_bg/{key}.png"
        path = cache / f"{key}.png"
        if not path.is_file():
            try:
                gen.generate(GenerationRequest(prompt=full, output_path=path, width=w, height=h,
                             steps=1, seed=0, image_format="png"))
                print(f"  [bg {i+1}] generated  {prompt[:44]}")
            except GenerationError as e:
                print(f"  [bg {i+1}] FAILED ({str(e)[:60]}) — using space backdrop")
                continue
        else:
            print(f"  [bg {i+1}] cached     {prompt[:44]}")
        line.setdefault("params", {})["bg"] = rel


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
    generate_backgrounds(lines, args.aspect)
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
