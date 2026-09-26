#!/usr/bin/env python3
"""Generate chapter-1 v2 images, render the animated video, mux preserved narration.

Idempotent: an image already on disk is never regenerated, so a re-run resumes
without re-spending. Narration is NOT synthesised — the existing 130.7s track in
assets/narration/ch01/narration.m4a is muxed onto the finished silent video.
"""
import sys, subprocess, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings
from app.services.csv_service import parse_csv
from app.services.storage import JobStorage
from app.services.video_service import build_job_video
from app.generators.factory import build_generator
from app.generators.base import GenerationError, GenerationRequest
from app.models import JobItem, Job, ItemStatus
from app.services.video_service import _placeholder

JOB = "JOB-101"
NARR = ROOT / "assets" / "narration" / "ch01" / "narration.m4a"
FINAL = ROOT / "data" / "jobs" / JOB / "chapter1.mp4"

def main():
    s = get_settings(); s.min_prompts = 1; s.max_prompts = 400
    s.ensure_directories()
    W, H = s.default_width, s.default_height
    result = parse_csv((ROOT / "samples/film/part01_v2.csv").read_bytes(), s)
    assert result.valid, result.errors

    storage = JobStorage(s)
    images = storage.prepare(JOB)
    gen = build_generator(s)
    print(f"backend={s.generator_backend} model={s.openai_image_model} beats={result.total}")

    items = []
    made = 0
    failed = []
    for p in result.prompts:
        fn = f"{p.order_index:03d}.png"
        path = images / fn
        if not path.is_file():                      # idempotent: never regenerate
            t = time.time()
            try:
                gen.generate(GenerationRequest(prompt=p.text, output_path=path,
                              width=W, height=H, steps=1, seed=0))
                made += 1
                print(f"  [{p.order_index:02d}/{result.total}] {time.time()-t:.1f}s  {p.text[:48]}")
            except GenerationError as exc:
                # Failure isolation: keep the film's timing, leave a black beat,
                # and report it so only that prompt gets reworked — never a rerun
                # of the whole batch.
                _placeholder(path, W, H)
                failed.append((p.order_index, str(exc)[:120]))
                print(f"  [{p.order_index:02d}/{result.total}] BLOCKED -> placeholder :: {str(exc)[:90]}")
        items.append(JobItem(
            job_id=JOB, prompt_id=p.order_index, order_index=p.order_index,
            external_id=p.external_id, prompt_text=p.text,
            start_seconds=p.start_seconds, end_seconds=p.end_seconds,
            transition=p.transition, transition_seconds=p.transition_seconds,
            ken_burns=p.ken_burns, ken_burns_scale=p.ken_burns_scale,
            grade=p.grade, grain=p.grain, text_type=p.text_type, text_value=p.text_value,
            animation=p.animation, animation_params=p.animation_params,
            status=ItemStatus.SUCCESS, filename=fn))
    print(f"images: {made} generated, {result.total-made-len(failed)} reused, {len(failed)} blocked")
    if failed:
        print("BLOCKED beats (reprompt these, then rerun to fill only them):")
        for idx, msg in failed:
            print(f"  beat {idx}: {msg}")

    print("rendering animated video (silent)...")
    info = build_job_video(Job(id=JOB, project_id="CH1", status="running"), items, storage, s, W, H)
    silent = info.path
    print(f"video: {silent} ({info.duration_seconds:.2f}s)")

    print("muxing preserved narration...")
    cmd = ["ffmpeg","-y","-i",str(silent),"-i",str(NARR),
           "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k",
           "-shortest","-movflags","+faststart",str(FINAL)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("MUX FAILED:", r.stderr[-500:]); sys.exit(1)
    dur = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                          "-of","csv=p=0",str(FINAL)], capture_output=True, text=True).stdout.strip()
    print(f"DONE -> {FINAL}  ({dur}s, {FINAL.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
