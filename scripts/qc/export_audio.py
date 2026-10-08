#!/usr/bin/env python3
"""Export the film's audio as separate, reusable stems.

    python scripts/qc/export_audio.py

Writes into deliverables/:
  the-ten-minutes-narration-full.m4a   every spoken line laid at its exact
                                       position in the finished film — a VO
                                       stem that drops straight onto the cut
  the-ten-minutes-narration.zip        the 127 individual clips, by chapter
  the-ten-minutes-score.zip            the seven score beds
  the-ten-minutes-ambience-sfx.zip     ambience beds and the one-shot SFX
  narration.txt / narration.csv        the script as spoken, with timings
"""
import csv, shutil, subprocess, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "qc"))
from script import CHAPTERS                                    # noqa: E402

NARR = ROOT / "assets" / "qc_narration"
OUT = ROOT / "deliverables"


def probe(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return round(float(r.stdout or 0), 3)


def main() -> int:
    OUT.mkdir(exist_ok=True)

    # --- walk the film once, collecting every spoken line and where it lands
    cues, cursor = [], 0.0
    for ch in CHAPTERS:
        for i, sc in enumerate(ch["scenes"], start=1):
            if not sc.get("n"):
                cursor += float(sc.get("silent", 3.0))
                continue
            clip = NARR / f"ch{ch['id']:02d}" / f"{i:03d}.m4a"
            if not clip.is_file():
                print(f"  missing {clip}"); continue
            d = probe(clip)
            cues.append(dict(ch=ch["id"], chapter=ch["title"], scene=i, at=round(cursor, 3),
                             dur=d, path=clip, text=sc["n"]))
            cursor += d + float(sc.get("hold", 0.0))
    total = cursor
    print(f"{len(cues)} spoken lines over {total:.1f}s ({total/60:.1f} min)")

    # --- the VO stem: each clip delayed to its own start, all mixed together
    inputs, steps, labels = [], [], []
    for n, c in enumerate(cues):
        inputs += ["-i", str(c["path"])]
        ms = int(c["at"] * 1000)
        steps.append(f"[{n}:a]aresample=44100,aformat=channel_layouts=stereo,"
                     f"adelay={ms}|{ms}[v{n}]")
        labels.append(f"[v{n}]")
    steps.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0,"
                 f"apad[vo]")
    stem = OUT / "the-ten-minutes-narration-full.m4a"
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(steps), "-map", "[vo]",
           "-t", f"{total:.3f}", "-c:a", "aac", "-b:a", "192k", str(stem)]
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0:
        print("VO stem failed:", "\n".join(done.stderr.splitlines()[-6:]))
    else:
        print(f"  {stem.name}  {probe(stem):.1f}s")

    # --- the clips themselves, kept in chapter folders
    with zipfile.ZipFile(OUT / "the-ten-minutes-narration.zip", "w", zipfile.ZIP_STORED) as z:
        for c in cues:
            z.write(c["path"], f"ch{c['ch']:02d}/{c['scene']:03d}.m4a")
    print("  the-ten-minutes-narration.zip")

    # --- score, ambience and sfx
    with zipfile.ZipFile(OUT / "the-ten-minutes-score.zip", "w", zipfile.ZIP_STORED) as z:
        for p in sorted((ROOT / "assets" / "music").glob("qc_*.mp3")):
            z.write(p, p.name.replace("qc_", ""))
    with zipfile.ZipFile(OUT / "the-ten-minutes-ambience-sfx.zip", "w", zipfile.ZIP_STORED) as z:
        for p in sorted((ROOT / "assets" / "ambience").glob("qc_*.mp3")):
            z.write(p, f"ambience/{p.name.replace('qc_', '')}")
        for name in ("beep", "tap", "sweep", "impact", "whoosh", "thud", "tick", "shimmer",
                     "riser", "sub"):
            p = ROOT / "assets" / "sfx" / f"{name}.wav"
            if p.is_file():
                z.write(p, f"sfx/{p.name}")
    print("  the-ten-minutes-score.zip\n  the-ten-minutes-ambience-sfx.zip")

    # --- the spoken script, as text and as a timed sheet
    with open(OUT / "narration.txt", "w", encoding="utf-8") as f:
        last = None
        for c in cues:
            if c["ch"] != last:
                f.write(f"\n\n{'='*70}\nCHAPTER {c['ch']:02d} — {c['chapter']}\n{'='*70}\n\n")
                last = c["ch"]
            f.write(f"[{int(c['at'])//60:02d}:{int(c['at'])%60:02d}]  {c['text']}\n\n")
    with open(OUT / "narration.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["chapter", "title", "scene", "start_seconds", "duration_seconds", "hindi"])
        for c in cues:
            w.writerow([c["ch"], c["chapter"], c["scene"], c["at"], c["dur"], c["text"]])
    print("  narration.txt\n  narration.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
