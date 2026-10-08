#!/usr/bin/env python3
"""Build THE TEN MINUTES end to end.

    python scripts/qc/build_film.py              # the whole film
    python scripts/qc/build_film.py --ch 3       # one chapter, for review
    python scripts/qc/build_film.py --plan       # no render: print the cut

The timeline is audio-driven. Narration is synthesised first and every scene
lasts exactly as long as its spoken line plus an authored `hold` of silence,
so picture and voice are locked by construction and a rewrite re-times the
film automatically.

Generate-once / reuse-forever, in both directions:
  * plates come from the keyed library in assets/qc/ — a plate used by four
    chapters costs one generation, and nothing here ever calls the image API;
  * narration is cached per (chapter, scene); a re-run re-synthesises nothing.
To re-record one line, delete that one clip.
"""
import argparse, json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "qc"))

from app.config import get_settings
from app.models import ItemStatus, Job, JobItem
from app.services.audio_service import build_audio_track, mux
from app.services.remotion import NO_IMAGE_TEMPLATES, TEMPLATES, validate
from app.services.storage import JobStorage
from app.services.subtitles import write_srt
from app.services.video_service import build_job_video
from app.tts.base import SpeechRequest
from app.tts.providers import SarvamTextToSpeech

from script import CHAPTERS, FILM
from look import ASSETS

PLATES = ROOT / "assets" / "qc"
NARR = ROOT / "assets" / "qc_narration"
OUT = ROOT / "samples" / "film_premium"

# A beat must be long enough to be read. Graphics need more room than a still:
# a map that pans, evaluates and labels cannot land in a second and a half.
MIN_IMG, MIN_ANIM = 1.25, 2.1
PACE = 1.05            # the brief's playback pace
LANG = "hi-IN"


def probe(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return round(float(out or 0), 3)


def beat_min(beat: dict) -> float:
    return MIN_ANIM if beat.get("anim") else MIN_IMG


def fit(beats: list[dict], seconds: float) -> list[tuple[dict, float]]:
    """Share a scene's seconds across its beats by weight, dropping any the
    scene is too short to hold. Authoring stays generous: extra beats on a
    short scene are simply unused rather than crammed in."""
    n = len(beats)
    while n > 1 and seconds < sum(beat_min(b) for b in beats[:n]):
        n -= 1
        
    use = beats[:n]
    total = sum(float(b.get("w", 1)) for b in use) or 1.0
    return [(b, seconds * float(b.get("w", 1)) / total) for b in use]


def params_str(p: dict) -> str:
    """`animation_params` is `key=value;key=value`, so a value may hold commas
    and pipes (templates read those as lists) but never a ';' or '='."""
    parts = []
    for k, v in (p or {}).items():
        v = str(v)
        if ";" in v or "=" in v:
            raise SystemExit(f"param {k}={v!r} contains ';' or '=', which the param format reserves")
        parts.append(f"{k}={v}")
    return ";".join(parts)


def synthesise(chapters, settings, verbose=True) -> int:
    """One cached Sarvam clip per spoken scene."""
    tts = SarvamTextToSpeech(api_key=settings.sarvam_api_key, model=settings.sarvam_model,
                             speaker=settings.sarvam_speaker, sample_rate=settings.sarvam_sample_rate,
                             base_url=settings.sarvam_base_url, timeout_seconds=120)
    made = 0
    for ch in chapters:
        d = NARR / f"ch{ch['id']:02d}"
        d.mkdir(parents=True, exist_ok=True)
        for i, sc in enumerate(ch["scenes"], start=1):
            if not sc.get("n"):
                sc["_dur"] = float(sc.get("silent", 3.0))
                continue
            clip = d / f"{i:03d}.m4a"
            if not clip.is_file():
                tts.synthesize(SpeechRequest(text=sc["n"], output_path=clip,
                                             voice=settings.sarvam_speaker, language=LANG,
                                             model=settings.sarvam_model, pace=PACE))
                made += 1
                if verbose:
                    print(f"  voiced ch{ch['id']:02d}/{i:03d}  {len(sc['n']):3d} chars", flush=True)
            sc["_clip"] = clip
            sc["_dur"] = probe(clip) + float(sc.get("hold", 0.0))
    return made


def plan(chapters, settings):
    """Turn the screenplay into the flat list of clips the renderer takes."""
    items: list[JobItem] = []
    oi = 0
    cursor = 0.0
    for ch in chapters:
        first_of_chapter = True
        for si, sc in enumerate(ch["scenes"], start=1):
            seconds = sc["_dur"]
            shares = fit(sc["beats"], seconds)
            at = cursor
            for bi, (beat, length) in enumerate(shares):
                oi += 1
                anim = beat.get("anim")
                img_key = beat.get("img")
                no_image = anim in NO_IMAGE_TEMPLATES if anim else False

                if img_key and img_key not in ASSETS:
                    raise SystemExit(f"ch{ch['id']} scene {si}: unknown plate key {img_key!r}")
                if anim and anim not in TEMPLATES:
                    raise SystemExit(f"ch{ch['id']} scene {si}: unknown animation {anim!r}")
                if anim:
                    problems = validate(anim, beat.get("p", {}), beat.get("text", ""))
                    if problems:
                        raise SystemExit(f"ch{ch['id']} scene {si} beat {bi}: " + "; ".join(problems))

                # chapter opens on a dip to black; everything inside dissolves
                transition = "fadeblack" if (first_of_chapter and bi == 0 and si == 1) else "dissolve"

                items.append(JobItem(
                    job_id=JOB, prompt_id=oi, order_index=oi, external_id=str(oi),
                    prompt_text=(ASSETS.get(img_key, "") or anim or "")[:400],
                    start_seconds=round(at, 3), end_seconds=round(at + length, 3),
                    transition=transition,
                    grade=FILM["grade"], grain=FILM["grain"],
                    ken_burns=(beat.get("kb") if (img_key and not anim) else None),
                    ken_burns_scale=None,
                    animation=anim, animation_params=(params_str(beat.get("p", {})) if anim else None),
                    text_value=beat.get("text") or None,
                    narration=(sc.get("n") if bi == 0 else None),
                    music=(f"qc_{ch['music']}.mp3" if (first_of_chapter and bi == 0) else None),
                    ambience=(f"qc_{ch['ambience']}.mp3" if (first_of_chapter and bi == 0) else None),
                    audio_filename=(f"{ch['id']:02d}{si:03d}.m4a" if (bi == 0 and sc.get("_clip")) else None),
                    audio_seconds=(probe(sc["_clip"]) if (bi == 0 and sc.get("_clip")) else None),
                    status=ItemStatus.SUCCESS,
                    filename=(f"{img_key}.png" if (img_key and not no_image) else None),
                    needs_image=False,
                ))
                at += length
                first_of_chapter = False
            cursor += seconds
    return items, cursor


def master_srt(settings, target: Path) -> Path | None:
    """One subtitle file for the joined film.

    Built from a plan over ALL chapters, so every cue carries its absolute
    time in the finished cut rather than its offset inside a chapter.
    """
    global JOB
    JOB = "JOB-900"
    synthesise(CHAPTERS, settings, verbose=False)
    items, _ = plan(CHAPTERS, settings)
    return write_srt(items, target.with_suffix(".srt"))


def join(parts: list[Path], target: Path) -> None:
    """Concatenate the chapter files without re-encoding.

    Every chapter comes out of the same pipeline at the same resolution,
    codec and pixel format, so a stream copy is exact and costs seconds. A
    chapter boundary is a hard cut out of black, which is what the cut wants
    anyway — the dissolves live inside chapters.
    """
    listing = target.with_suffix(".txt")
    listing.write_text("".join(f"file '{p.resolve()}'\n" for p in parts), encoding="utf-8")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
           "-c", "copy", "-movflags", "+faststart", str(target)]
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0 or not target.is_file():
        # Fall back to a re-encode if the streams will not copy cleanly.
        print("  stream copy refused, re-encoding the join")
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
               "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(target)]
        done = subprocess.run(cmd, capture_output=True, text=True)
        if done.returncode != 0:
            raise SystemExit("join failed:\n" + "\n".join(done.stderr.splitlines()[-12:]))
    listing.unlink(missing_ok=True)


def build_all(settings, force: bool) -> int:
    """Each chapter is built as its own job, then the parts are joined.

    Chapter by chapter rather than one 178-clip graph: a failure costs one
    chapter instead of the whole render, finished chapters are reusable on a
    re-run, and the audio mix for each stays a size ffmpeg is comfortable with.
    """
    OUT.mkdir(parents=True, exist_ok=True)
    parts = []
    for ch in CHAPTERS:
        part = OUT / f"the-ten-minutes-ch{ch['id']:02d}.mp4"
        if part.is_file() and not force:
            print(f"ch{ch['id']:02d} {ch['title']:<24} cached ({probe(part):.1f}s)", flush=True)
            parts.append(part)
            continue
        print(f"ch{ch['id']:02d} {ch['title']:<24} building", flush=True)
        done = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--ch", str(ch["id"])],
                              cwd=str(ROOT), capture_output=True, text=True)
        if done.returncode != 0 or not part.is_file():
            print(done.stdout[-2000:]); print(done.stderr[-2000:])
            raise SystemExit(f"chapter {ch['id']} failed")
        print(f"   -> {probe(part):.1f}s", flush=True)
        parts.append(part)

    final = OUT / "the-ten-minutes.mp4"
    print(f"joining {len(parts)} chapters")
    join(parts, final)
    master_srt(settings, final)
    print(f"DONE -> {final}  ({probe(final):.1f}s = {probe(final)/60:.1f} min, "
          f"{final.stat().st_size/1e6:.0f} MB) + srt")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ch", type=int, default=0, help="build one chapter only")
    ap.add_argument("--plan", action="store_true", help="print the cut, render nothing")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="build every chapter, then join them into the finished film")
    ap.add_argument("--force", action="store_true", help="rebuild chapters that already exist")
    args = ap.parse_args()

    settings = get_settings()
    settings.min_prompts, settings.max_prompts = 1, 4000
    settings.ensure_directories()
    W, H = settings.default_width, settings.default_height

    chapters = [c for c in CHAPTERS if (not args.ch or c["id"] == args.ch)]
    if not chapters:
        raise SystemExit(f"no chapter {args.ch}")

    # Job ids are validated as JOB-<digits>; 9xx keeps this film's working
    # directories clearly apart from the other film's JOB-2xx chapters.
    global JOB
    JOB = f"JOB-9{args.ch or 0:02d}"

    missing = [k for k in ASSETS if not (PLATES / f"{k}.png").is_file()]
    if missing:
        raise SystemExit(f"{len(missing)} plates missing — run scripts/qc/gen_assets.py first: {missing[:5]}")

    if args.all:
        return build_all(settings, args.force)

    made = synthesise(chapters, settings, verbose=not args.plan)
    items, total = plan(chapters, settings)
    print(f"narration {made} new (rest cached) · {len(items)} clips · {total:.1f}s = {total/60:.1f} min")

    if args.plan:
        for ch in chapters:
            spoken = sum(1 for s in ch["scenes"] if s.get("n"))
            secs = sum(s["_dur"] for s in ch["scenes"])
            print(f"  ch{ch['id']:02d} {ch['title']:<24} {len(ch['scenes']):2d} scenes "
                  f"({spoken} spoken) {secs:6.1f}s  music={ch['music']}")
        return 0

    storage = JobStorage(settings)
    images = storage.images_dir(JOB); images.mkdir(parents=True, exist_ok=True)
    adir = storage.audio_dir(JOB); adir.mkdir(parents=True, exist_ok=True)

    # stage exactly the plates this cut references, once each
    staged = {it.filename for it in items if it.filename}
    for name in staged:
        shutil.copyfile(PLATES / name, images / name)
    for ch in chapters:
        for si, sc in enumerate(ch["scenes"], start=1):
            if sc.get("_clip"):
                shutil.copyfile(sc["_clip"], adir / f"{ch['id']:02d}{si:03d}.m4a")
    print(f"staged {len(staged)} plates · rendering picture")

    info = build_job_video(Job(id=JOB, project_id="TENMIN", status="running"),
                           items, storage, settings, W, H)
    print(f"picture {info.duration_seconds:.1f}s · building sound")

    if not args.no_audio:
        track = build_audio_track(JOB, items, storage, settings, info.duration_seconds)
        if track:
            mux(info.path, track, settings)

    OUT.mkdir(parents=True, exist_ok=True)
    name = f"the-ten-minutes{'' if not args.ch else f'-ch{args.ch:02d}'}"
    final = OUT / f"{name}.mp4"
    shutil.copyfile(info.path, final)
    srt = write_srt(items, final.with_suffix(".srt"))
    print(f"DONE -> {final}  ({probe(final):.1f}s, {final.stat().st_size/1e6:.0f} MB)"
          f"{' + srt' if srt else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
