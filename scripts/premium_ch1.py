#!/usr/bin/env python3
"""Chapter 1 PREMIUM — reuses the existing 56 images + narration (zero API),
adds: filmic grade, parallax on establishing shots, full sound design
(score + wind ambience + SFX), an end card, and subtitles."""
import subprocess, sys, shutil, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.config import get_settings
from app.services.csv_service import parse_csv
from app.services.storage import JobStorage
from app.services.video_service import build_job_video
from app.services.audio_service import _sfx_events
from app.models import JobItem, Job, ItemStatus

JOB = "JOB-101"
NARR = ROOT / "assets/narration/ch01/narration.m4a"
OUT = ROOT / "samples/film_premium/chapter1.mp4"
DEV = str.maketrans("०१२३४५६७८९", "0123456789")
KB = ["zoom_in:1.12","zoom_out:1.14","pan_left","pan_right","zoom_in:1.18","pan_up"]
CH1_FACTS = {
  "अप्रैल": dict(title="जन्म", date="14 अप्रैल 1891", lines=["महू छावनी, मध्य भारत","महार समुदाय"]),
  "रामजी मालोजी": dict(title="रामजी मालोजी सकपाल", date="", lines=["ब्रिटिश भारतीय सेना — सूबेदार"]),
}
WIDE = re.compile(r"vast|wide|aerial|plain|town|road|landscape|hillside|cantonment|horizon|parade ground|dawn|sky", re.I)

def dur(p):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)],capture_output=True,text=True).stdout or 0)

def main():
    s = get_settings(); s.min_prompts=1; s.max_prompts=400; s.ensure_directories()
    W,H = s.default_width, s.default_height
    storage = JobStorage(s)
    r = parse_csv((ROOT/"samples/film/part01_v2.csv").read_bytes(), s)
    assert r.valid, r.errors
    images = storage.images_dir(JOB)

    items=[]
    for idx, p in enumerate(r.prompts):
        fn = f"{p.order_index:03d}.png"
        anim = p.animation or ""
        params = p.animation_params or ""
        kb = p.ken_burns or ""
        tval = (p.text_value or "").translate(DEV)  # Western numerals
        # date/name cards -> richer info_card (verified)
        fact = None
        for kw, info in CH1_FACTS.items():
            if (p.text_value and kw in p.text_value):
                fact = info; break
        if fact:
            anim = "info_card"
            params = f"lines={'|'.join(fact['lines'])}" + (f";date={fact['date']}" if fact['date'] else "")
            tval = fact["title"]; kb = ""
        elif not anim:
            # every plain beat gets a real camera move (no parallax)
            kb = kb or KB[idx % len(KB)]
        items.append(JobItem(job_id=JOB, prompt_id=p.order_index, order_index=p.order_index,
            external_id=str(p.order_index), prompt_text=p.text,
            start_seconds=p.start_seconds, end_seconds=p.end_seconds,
            transition=p.transition, transition_seconds=p.transition_seconds,
            ken_burns=kb or None, grade="film", grain=p.grain, text_type=p.text_type,
            text_value=tval, animation=anim or None, animation_params=params or None,
            status=ItemStatus.SUCCESS, filename=fn))
    beats_end = items[-1].end_seconds
    # end card (no image)
    items.append(JobItem(job_id=JOB, prompt_id=999, order_index=999, external_id="999",
        prompt_text="end", start_seconds=beats_end, end_seconds=beats_end+4.0,
        transition="dissolve", grade=None, grain=None,
        animation="end_card", animation_params="brand=THE QUIET STORY;next=स्कूल और अपमान",
        text_value="SUBSCRIBE", status=ItemStatus.SUCCESS, filename=None, needs_image=False))
    total = beats_end + 4.0

    parallax_n = sum(1 for it in items if it.animation=="parallax")
    print(f"ch1: {len(items)} beats ({parallax_n} parallax) -> rendering video (reusing {len(r.prompts)} images)...")
    info = build_job_video(Job(id=JOB, project_id="CH1", status="running"), items, storage, s, W, H)
    silent = info.path
    print(f"video: {silent} {info.duration_seconds:.1f}s")

    # premium audio: reuse VO + score + ambience + SFX + master
    binary = shutil.which("ffmpeg")
    vo = str(NARR); vlen = dur(vo)
    sfx = _sfx_events(sorted(items,key=lambda x:x.order_index), s.asset_path(s.sfx_dir))
    music = s.asset_path(s.music_dir)/"warm.mp3"; amb = s.asset_path(s.ambience_dir)/"wind.mp3"
    inp = ["-i", vo, "-stream_loop","-1","-i",str(music), "-stream_loop","-1","-i",str(amb)]
    fc = [
      f"[0:a]aresample=44100,{'highpass=f=80,equalizer=f=3200:t=q:w=1.6:g=2.5,acompressor=threshold=-18dB:ratio=3,alimiter=limit=0.95' if s.voice_master else 'anull'},asplit=2[voice][key]",
      f"[1:a]aresample=44100,atrim=0:{total:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=1.5,afade=t=out:st={total-3:.3f}:d=3,volume={s.music_level_db}dB[mus]",
      f"[2:a]aresample=44100,atrim=0:{total:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=2,afade=t=out:st={total-2:.3f}:d=2,volume={s.ambience_level_db}dB[amb]",
      f"[mus][key]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[musd]",
    ]
    idx=3; sl=[]
    for path,at in sfx:
        inp += ["-i", str(path)]
        fc.append(f"[{idx}:a]aresample=44100,volume={s.sfx_level_db}dB,adelay={int(at*1000)}|{int(at*1000)}[x{idx}]")
        sl.append(f"[x{idx}]"); idx+=1
    sfxmix = ""
    if sl:
        fc.append(f"{''.join(sl)}amix=inputs={len(sl)}:duration=longest:normalize=0[sfx]"); sfxmix="[sfx]"
    layers = f"[voice][musd][amb]{sfxmix}"
    nlayers = 3 + (1 if sfxmix else 0)
    fc.append(f"{layers}amix=inputs={nlayers}:duration=longest:normalize=0[mixed]")
    fc.append(f"[mixed]loudnorm=I={s.master_lufs}:TP=-1.5:LRA=11,aresample=44100,apad[master]")
    amix_out = storage.job_dir(JOB)/"premium_audio.m4a"
    cmd = [binary,"-y",*inp,"-filter_complex",";".join(fc),"-map","[master]","-t",f"{total:.3f}","-c:a","aac","-b:a","192k",str(amix_out)]
    r2 = subprocess.run(cmd,capture_output=True,text=True)
    if r2.returncode!=0: print("AUDIO FAIL:", r2.stderr[-800:]); sys.exit(1)
    print(f"audio: {amix_out} {dur(amix_out):.1f}s")

    # subtitles from the original narration lines + clip durations
    import json
    scenes = json.loads((ROOT/"scripts/film/part1.json").read_text(encoding="utf-8"))["scenes"]
    cues=[]; t=0.0
    for i,sc in enumerate(scenes, start=1):
        clip = ROOT/f"assets/narration/ch01/{i:03d}.m4a"
        d = dur(clip) if clip.is_file() else 3.0
        def ts(x):
            h=int(x//3600);m=int((x%3600)//60);sec=int(x%60);ms=int(round((x-int(x))*1000));return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
        cues.append(f"{i}\n{ts(t)} --> {ts(t+d-0.05)}\n{sc['n'].strip()}\n"); t+=d
    OUT.parent.mkdir(parents=True, exist_ok=True)
    (OUT.with_suffix(".srt")).write_text("\n".join(cues), encoding="utf-8")

    # mux
    muxcmd=[binary,"-y","-i",str(silent),"-i",str(amix_out),"-map","0:v:0","-map","1:a:0",
            "-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",str(OUT)]
    r3=subprocess.run(muxcmd,capture_output=True,text=True)
    if r3.returncode!=0: print("MUX FAIL:", r3.stderr[-500:]); sys.exit(1)
    print(f"DONE -> {OUT} ({dur(OUT):.1f}s)  + {OUT.with_suffix('.srt').name}")

if __name__=="__main__":
    main()
