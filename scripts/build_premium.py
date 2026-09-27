#!/usr/bin/env python3
"""Build a PREMIUM chapter (2-4) end to end, generate-once and reuse.

- narration: one Sarvam clip per scene, cached in assets/narration/ch{N}
- images:    one gpt-image per scene, cached in assets/premium/ch{N} (never
             regenerated on a re-run); Indian-location scenes use geo_map (no image)
- video:     each scene split into <=3s beats that REUSE the scene image with
             parallax / ken-burns motion, plus intro + end cards; filmic grade
- audio:     score + ambience + auto-SFX + mastered voice via the real pipeline
- subtitles: .srt sidecar

    python scripts/build_premium.py 2
Idempotent: images/narration are cached by chapter+scene, so re-runs never re-spend.
"""
import hashlib, json, math, re, shutil, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.config import get_settings
from app.services.storage import JobStorage
from app.services.video_service import build_job_video
from app.services.audio_service import build_audio_track, mux
from app.services.subtitles import write_srt
from app.generators.api_backends import OpenAIImageGenerator
from app.generators.base import GenerationError, GenerationRequest
from app.tts.providers import SarvamTextToSpeech
from app.tts.base import SpeechRequest
from app.models import JobItem, Job, ItemStatus
from app.services.video_service import _placeholder

MAX_BEAT = 3.0
STYLE = ("photorealistic, authentic early-1900s India, period-accurate, natural skin texture, "
         "volumetric light, shot on 35mm, shallow depth of field, fine film grain, cinematic "
         "documentary still, no on-image text, no watermark, 16:9")

CH = {
    2: dict(title="स्कूल और अपमान", kicker="भाग दो", grade="cold_film", music="somber.mp3",
            ambience="room.mp3", nxt="विदेश में शिक्षा"),
    3: dict(title="विदेश में शिक्षा", kicker="भाग तीन", grade="film", music="hopeful.mp3",
            ambience="room.mp3", nxt="महाड़ और नासिक"),
    4: dict(title="महाड़ और नासिक", kicker="भाग चार", grade="teal_orange", music="tension.mp3",
            ambience="crowd.mp3", nxt="दो रास्ते"),
}
GEO = {"महाड़":"mahad","नासिक":"nashik","बॉम्बे":"bombay","बम्बई":"bombay","बड़ौदा":"baroda",
       "नागपुर":"nagpur","दिल्ली":"delhi","मुंबई":"bombay"}

# Ken-Burns rotation (replaces parallax) — varied real camera moves per beat.
KB = ["zoom_in:1.12", "zoom_out:1.14", "pan_left", "pan_right", "zoom_in:1.18", "pan_up"]

# Hindi label + a contextual date for geo_map scenes.
GEO_LABEL = {"mahad": ("महाड़, महाराष्ट्र", "1927"), "nashik": ("नासिक", "1930"),
             "baroda": ("बड़ौदा रियासत", "1913"), "bombay": ("बॉम्बे", ""),
             "nagpur": ("नागपुर", ""), "delhi": ("दिल्ली", ""), "mhow": ("महू, मध्य प्रदेश", "1891")}

# Verified fact overlays (info_card) keyed by a phrase in the narration.
# Dates cross-checked; kept consistent with the spoken narration.
FACTS = {
 2: [("कोलंबिया", dict(title="कोलंबिया विश्वविद्यालय", date="1913",
        lines=["न्यूयॉर्क, अमेरिका", "M.A. — 1915", "Ph.D. अर्थशास्त्र — 1927", "गुरु: प्रो. जॉन ड्यूई"])),
     ("एल्फिंस्टन", dict(title="एल्फिंस्टन कॉलेज", date="", lines=["बॉम्बे विश्वविद्यालय", "अर्थशास्त्र एवं राजनीति"])),
     ("मैट्रिक", dict(title="मैट्रिक परीक्षा पास", date="1907", lines=["बॉम्बे प्रेसिडेंसी"])),
     ("मास्टर डिग्री", dict(title="M.A. पूर्ण", date="1915", lines=["कोलंबिया विश्वविद्यालय"]))],
 3: [("लंदन", dict(title="London School of Economics", date="1916–1923",
        lines=["अर्थशास्त्र में D.Sc.", "Gray's Inn — बैरिस्टर (1922)"])),
     ("Rupee", dict(title="The Problem of the Rupee", date="1923", lines=["भारतीय मुद्रा एवं औपनिवेशिक वित्त"])),
     ("बहिष्कृत हितकारिणी", dict(title="बहिष्कृत हितकारिणी सभा", date="1924",
        lines=["शिक्षा · संगठन · सामाजिक सुधार"]))],
 4: [("मनुस्मृति", dict(title="मनुस्मृति दहन", date="25 दिसंबर 1927", lines=["महाड़ — प्रतीकात्मक विरोध"])),
     ("महाड़ में आंदोलन", dict(title="महाड़ सत्याग्रह", date="20 मार्च 1927",
        lines=["चवदार तालाब — सार्वजनिक जल का अधिकार", "हज़ारों सत्याग्रही"])),
     ("कालाराम", dict(title="कालाराम मंदिर सत्याग्रह", date="2 मार्च 1930", lines=["मंदिर प्रवेश आंदोलन"]))],
}

def fact_for(n, text):
    for kw, info in FACTS.get(n, []):
        if kw in text:
            return info
    return None

def dur(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)],capture_output=True,text=True).stdout or 0)

def geo_city(text):
    for k,v in GEO.items():
        if k in text: return v
    return None

def main(N):
    cfg = CH[N]
    s = get_settings(); s.min_prompts=1; s.max_prompts=400; s.ensure_directories()
    W,H = s.default_width, s.default_height
    JOB = f"JOB-20{N}"
    storage = JobStorage(s)
    scenes = json.loads((ROOT/f"scripts/film/part{N}.json").read_text(encoding="utf-8"))["scenes"]
    palette = json.loads((ROOT/f"scripts/film/part{N}.json").read_text(encoding="utf-8"))["palette"]

    narr_dir = ROOT/f"assets/narration/ch{N:02d}"; narr_dir.mkdir(parents=True, exist_ok=True)
    img_dir = ROOT/f"assets/premium/ch{N:02d}"; img_dir.mkdir(parents=True, exist_ok=True)
    tts = SarvamTextToSpeech(api_key=s.sarvam_api_key, model=s.sarvam_model, speaker=s.sarvam_speaker,
                             sample_rate=s.sarvam_sample_rate, base_url=s.sarvam_base_url, timeout_seconds=90)
    gen = OpenAIImageGenerator(api_key=s.openai_api_key, model=s.openai_image_model,
                               size=s.openai_image_size, quality=s.openai_image_quality,
                               base_url=s.openai_base_url, timeout_seconds=s.api_timeout_seconds)

    # 1. narration (cache) + 2. images (cache)
    made_n = made_i = 0
    for i, sc in enumerate(scenes, start=1):
        clip = narr_dir/f"{i:03d}.m4a"
        if not clip.is_file():
            tts.synthesize(SpeechRequest(text=sc["n"], output_path=clip, voice=s.sarvam_speaker,
                           language="hi-IN", model=s.sarvam_model, pace=1.15)); made_n+=1
        sc["_dur"] = dur(clip)
        sc["_geo"] = geo_city(sc["n"]) or geo_city(sc["p"])
        if sc["_geo"]:
            continue  # geo_map draws itself, no image
        img = img_dir/f"{i:03d}.png"
        if not img.is_file():
            prompt = f"{sc['p'].rstrip('. ')}, {palette}, {STYLE}"
            try:
                gen.generate(GenerationRequest(prompt=prompt, output_path=img, width=W, height=H,
                             steps=1, seed=0, image_format="png")); made_i+=1
            except GenerationError as e:
                print(f"  scene {i} image blocked ({str(e)[:50]}) -> placeholder"); _placeholder(img, W, H)
        sc["_img"] = img
    print(f"ch{N}: narration {made_n} new / images {made_i} new (rest cached)")

    # 3. build beats (fixed timeline; intro 3.5s + scenes + end 4s)
    images = storage.images_dir(JOB); images.mkdir(parents=True, exist_ok=True)
    adir = storage.audio_dir(JOB); adir.mkdir(parents=True, exist_ok=True)
    items=[]; oi=0; pdir=0; cursor=3.5
    # intro
    oi+=1
    items.append(JobItem(job_id=JOB, prompt_id=oi, order_index=oi, external_id=str(oi), prompt_text="intro",
        start_seconds=0.0, end_seconds=3.5, transition="fade", animation="intro_card",
        animation_params=f"brand=THE QUIET STORY;kicker={cfg['kicker']}", text_value=cfg["title"],
        status=ItemStatus.SUCCESS, filename=None, needs_image=False))
    for i, sc in enumerate(scenes, start=1):
        d = sc["_dur"]; start = cursor; end = cursor + d; cursor = end
        # copy narration clip into job audio dir
        shutil.copyfile(narr_dir/f"{i:03d}.m4a", adir/f"{i:03d}.m4a")
        if sc["_geo"]:
            oi+=1
            label, gdate = GEO_LABEL.get(sc["_geo"], ("", ""))
            gp = f"focus={sc['_geo']};pins={sc['_geo']};scale=1650"
            if gdate: gp += f";date={gdate}"
            items.append(JobItem(job_id=JOB, prompt_id=oi, order_index=oi, external_id=str(oi),
                prompt_text=sc["p"], start_seconds=round(start,3), end_seconds=round(end,3),
                transition=("dissolve" if i>1 else "fadeblack"),
                grade=cfg["grade"], animation="geo_map",
                animation_params=gp,
                text_value=label, narration=sc["n"], music=(cfg["music"] if i==1 else None),
                ambience=(cfg["ambience"] if i==1 else None),
                audio_filename=f"{i:03d}.m4a", audio_seconds=d,
                status=ItemStatus.SUCCESS, filename=None, needs_image=False))
            continue
        # copy scene image into job images dir once
        fn = f"{i:03d}.png"; shutil.copyfile(sc["_img"], images/fn)
        nbeats = max(1, math.ceil(d / MAX_BEAT))   # strict <=3s per beat
        seg = d / nbeats
        fact = fact_for(N, sc["n"]) or fact_for(N, sc["p"])
        for b in range(nbeats):
            oi+=1; bs = start + b*seg; be = start + (b+1)*seg
            if b == 0 and fact:
                anim = "info_card"
                params = f"lines={'|'.join(fact.get('lines',[]))}" + (f";date={fact['date']}" if fact.get('date') else "")
                tval = fact.get("title","")
            else:
                anim = None  # ffmpeg ken-burns move (fast, reliable, looks good)
                params = None; tval = None
            kb = None if (b==0 and fact) else KB[(i + b) % len(KB)]
            items.append(JobItem(job_id=JOB, prompt_id=oi, order_index=oi, external_id=str(oi),
                prompt_text=sc["p"], start_seconds=round(bs,3), end_seconds=round(be,3),
                transition=("dissolve" if b>0 else ("dissolve" if i>1 else "fadeblack")),
                grade=cfg["grade"], grain=6, ken_burns=kb, ken_burns_scale=None,
                animation=anim, animation_params=params, text_value=tval,
                narration=(sc["n"] if b==0 else None),
                music=(cfg["music"] if (i==1 and b==0) else None),
                ambience=(cfg["ambience"] if (i==1 and b==0) else None),
                audio_filename=(f"{i:03d}.m4a" if b==0 else None),
                audio_seconds=(d if b==0 else None),
                status=ItemStatus.SUCCESS, filename=fn))
    # end card
    oi+=1
    items.append(JobItem(job_id=JOB, prompt_id=oi, order_index=oi, external_id=str(oi), prompt_text="end",
        start_seconds=round(cursor,3), end_seconds=round(cursor+4,3), transition="dissolve",
        animation="end_card", animation_params=f"brand=THE QUIET STORY;next={cfg['nxt']}",
        text_value="SUBSCRIBE", status=ItemStatus.SUCCESS, filename=None, needs_image=False))
    total = cursor + 4
    npar = sum(1 for it in items if it.animation=="parallax")
    print(f"ch{N}: {len(items)} beats ({npar} parallax) over {total:.1f}s -> render video")

    info = build_job_video(Job(id=JOB, project_id=f"CH{N}", status="running"), items, storage, s, W, H)
    print(f"video {info.duration_seconds:.1f}s -> audio")
    track = build_audio_track(JOB, items, storage, s, info.duration_seconds)
    if track: mux(info.path, track, s)
    OUT = ROOT/f"samples/film_premium/chapter{N}.mp4"; OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(info.path, OUT)
    srt = write_srt(items, OUT.with_suffix(".srt"))
    print(f"DONE -> {OUT} ({dur(OUT):.1f}s){' + srt' if srt else ''}")

if __name__ == "__main__":
    main(int(sys.argv[1]))
