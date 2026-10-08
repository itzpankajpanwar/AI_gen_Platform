#!/usr/bin/env python3
"""Render the film's narration in a different Sarvam voice, synced to the cut.

    python scripts/qc/make_voice_alt.py shubh

Generates every line again with the named speaker — same model, same pace,
same language as the film — into its OWN cache (assets/qc_narration_<voice>/),
so the cut's existing narration is never touched. Then it lays the new clips
at the SAME scene start times the finished film uses, producing one continuous
voice-only stem that drops straight onto the rendered picture.

Because a different speaker reads at a different rate, a line can come out
longer than the slot the cut gives it. Every scene is measured and any overrun
is reported, with the worst cases named, so the drift is a known quantity
rather than something you discover while watching.
"""
import argparse, csv, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "qc"))

from app.config import get_settings                                    # noqa: E402
from app.tts.base import SpeechRequest                                  # noqa: E402
from app.tts.providers import SarvamTextToSpeech                        # noqa: E402
from script import CHAPTERS                                             # noqa: E402

CUT_NARR = ROOT / "assets" / "qc_narration"      # the voice the film is cut to
OUT = ROOT / "deliverables"
PACE, LANG = 1.05, "hi-IN"


def probe(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return round(float(r.stdout or 0), 3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("voice")
    args = ap.parse_args()
    voice = args.voice.strip().lower()

    s = get_settings()
    alt = ROOT / "assets" / f"qc_narration_{voice}"
    tts = SarvamTextToSpeech(api_key=s.sarvam_api_key, model=s.sarvam_model, speaker=voice,
                             sample_rate=s.sarvam_sample_rate, base_url=s.sarvam_base_url,
                             timeout_seconds=120)

    # --- walk the film exactly as the builder does, so starts match the cut
    cues, cursor, made = [], 0.0, 0
    for ch in CHAPTERS:
        d = alt / f"ch{ch['id']:02d}"
        d.mkdir(parents=True, exist_ok=True)
        for i, sc in enumerate(ch["scenes"], start=1):
            if not sc.get("n"):
                cursor += float(sc.get("silent", 3.0))
                continue
            cut_clip = CUT_NARR / f"ch{ch['id']:02d}" / f"{i:03d}.m4a"
            cut_dur = probe(cut_clip) if cut_clip.is_file() else 0.0
            hold = float(sc.get("hold", 0.0))

            clip = d / f"{i:03d}.m4a"
            if not clip.is_file():
                tts.synthesize(SpeechRequest(text=sc["n"], output_path=clip, voice=voice,
                                             language=LANG, model=s.sarvam_model, pace=PACE))
                made += 1
                if made % 20 == 0:
                    print(f"  {made} lines voiced", flush=True)
            cues.append(dict(ch=ch["id"], title=ch["title"], scene=i, at=round(cursor, 3),
                             slot=round(cut_dur + hold, 3), dur=probe(clip),
                             path=clip, text=sc["n"]))
            cursor += cut_dur + hold
    total = cursor
    print(f"{voice}: {made} new / {len(cues)} lines, cut is {total:.1f}s ({total/60:.1f} min)")

    # --- how well the new read fits the slots the cut gives it
    over = [c for c in cues if c["dur"] > c["slot"] + 0.05]
    worst = sorted(over, key=lambda c: c["slot"] - c["dur"])[:8]
    tot_alt = sum(c["dur"] for c in cues)
    tot_cut = sum(c["slot"] for c in cues)
    print(f"spoken time: {tot_alt:.1f}s in this voice vs {tot_cut:.1f}s of slot "
          f"({100*tot_alt/tot_cut:.1f}%)")
    print(f"{len(over)}/{len(cues)} lines run past their slot")
    for c in worst:
        print(f"   ch{c['ch']:02d} scene {c['scene']:03d}  +{c['dur']-c['slot']:.2f}s  {c['text'][:48]}…")

    # --- the stem, positioned at the cut's scene starts
    inputs, steps, labels = [], [], []
    for n, c in enumerate(cues):
        inputs += ["-i", str(c["path"])]
        ms = int(c["at"] * 1000)
        steps.append(f"[{n}:a]aresample=44100,aformat=channel_layouts=stereo,"
                     f"adelay={ms}|{ms}[v{n}]")
        labels.append(f"[v{n}]")
    steps.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0,apad[vo]")
    stem = OUT / f"the-ten-minutes-narration-{voice}.m4a"
    OUT.mkdir(exist_ok=True)
    done = subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(steps),
                           "-map", "[vo]", "-t", f"{total:.3f}", "-c:a", "aac", "-b:a", "192k",
                           str(stem)], capture_output=True, text=True)
    if done.returncode != 0:
        raise SystemExit("stem failed:\n" + "\n".join(done.stderr.splitlines()[-8:]))
    print(f"-> {stem}  ({probe(stem):.1f}s)")

    with open(OUT / f"narration-{voice}-fit.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["chapter", "title", "scene", "start_s", "slot_s", f"{voice}_s", "over_s", "hindi"])
        for c in cues:
            w.writerow([c["ch"], c["title"], c["scene"], c["at"], c["slot"], c["dur"],
                        round(c["dur"] - c["slot"], 3), c["text"]])
    print(f"-> {OUT / f'narration-{voice}-fit.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
