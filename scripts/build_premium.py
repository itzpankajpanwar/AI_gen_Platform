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

KICKER = {1:"भाग एक", 2:"भाग दो", 3:"भाग तीन", 4:"भाग चार", 5:"भाग पाँच",
          6:"भाग छह", 7:"भाग सात", 8:"भाग आठ", 9:"भाग नौ", 10:"भाग दस",
          11:"भाग ग्यारह", 12:"भाग बारह", 13:"भाग तेरह", 14:"भाग चौदह", 15:"भाग पंद्रह"}

def load_part(n):
    return json.loads((ROOT/f"scripts/film/part{n}.json").read_text(encoding="utf-8"))

def chapter_cfg(N, data):
    """Chapter framing derived from the spec itself — no per-chapter hardcoding.
    `nxt` is the following chapter's title, for the end card."""
    nxt = ""
    nxt_path = ROOT/f"scripts/film/part{N+1}.json"
    if nxt_path.is_file():
        nxt = json.loads(nxt_path.read_text(encoding="utf-8")).get("title", "")
    return dict(title=data.get("title", ""), kicker=KICKER.get(N, f"भाग {N}"),
                grade=data.get("grade", "neutral"), music=data.get("music"),
                ambience=data.get("ambience"), nxt=nxt)
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
 5: [("Round Table", dict(title="गोलमेज सम्मेलन", date="1930–1932",
        lines=["लंदन", "तीनों सम्मेलनों में भागीदारी", "Depressed Classes का प्रतिनिधित्व"])),
     ("Communal Award", dict(title="Communal Award", date="1932",
        lines=["ब्रिटिश PM रैमसे मैकडॉनल्ड", "वंचित वर्गों हेतु पृथक निर्वाचन"])),
     ("24 सितंबर", dict(title="पूना पैक्ट", date="24 सितंबर 1932",
        lines=["आंबेडकर – गांधी समझौता", "पृथक निर्वाचन → आरक्षित सीटें", "यरवदा जेल उपवास के बाद"])),
     ("Annihilation of Caste", dict(title="Annihilation of Caste", date="1936",
        lines=["जाति व्यवस्था की संरचनात्मक आलोचना", "हिंदी: जाति का विनाश"]))],
 6: [("Annihilation of Caste", dict(title="Annihilation of Caste", date="1936",
        lines=["मूल रूप से जात-पात तोड़क मंडल, लाहौर हेतु", "अदत्त भाषण → स्वयं प्रकाशित"])),
     ("social democracy", dict(title="सामाजिक लोकतंत्र", date="",
        lines=["राजनीतिक + सामाजिक + आर्थिक समानता", "केवल मताधिकार पर्याप्त नहीं"]))],
 7: [("The Problem of the Rupee", dict(title="The Problem of the Rupee", date="1923",
        lines=["भारतीय मुद्रा एवं विनिमय", "लंदन D.Sc. शोध का आधार"])),
     ("Independent Labour Party", dict(title="Independent Labour Party", date="1936",
        lines=["श्रमिक–किसान राजनीति"])),
     ("बॉम्बे विधान सभा", dict(title="बॉम्बे विधान सभा", date="1937",
        lines=["निर्वाचित सदस्य", "श्रमिक अधिकारों का मंच"]))],
 8: [("Viceroy's Executive Council", dict(title="वायसराय कार्यकारी परिषद", date="1942",
        lines=["श्रम सदस्य (Labour Member)", "श्रम नीति एवं कल्याण"])),
     ("Constituent Assembly", dict(title="संविधान सभा", date="1946",
        lines=["भारत के संविधान का निर्माण", "बॉम्बे प्रांत से सदस्य"]))],
 9: [("पहले कानून मंत्री", dict(title="स्वतंत्र भारत के प्रथम कानून मंत्री", date="1947",
        lines=["नेहरू मंत्रिमंडल", "विधि एवं न्याय"])),
     ("29 अगस्त 1947", dict(title="प्रारूप समिति", date="29 अगस्त 1947",
        lines=["अध्यक्ष: डॉ. बी. आर. आंबेडकर", "सात सदस्य"])),
     ("25 नवंबर 1949", dict(title="संविधान सभा — अंतिम भाषण", date="25 नवंबर 1949",
        lines=["श्रेय अनेक सहयोगियों के साथ साझा"]))],
 10: [("Liberty. Equality. Fraternity", dict(title="स्वतंत्रता · समता · बंधुता", date="",
        lines=["लोकतंत्र = सामाजिक जीवन-पद्धति", "तीनों परस्पर अनिवार्य"])),
      ("constitutional morality", dict(title="संवैधानिक नैतिकता", date="4 नवंबर 1948",
        lines=["संविधान सभा में भाषण", "केवल पाठ नहीं, आचरण भी"])),
      ("26 जनवरी 1950", dict(title="भारत गणराज्य", date="26 जनवरी 1950",
        lines=["संविधान लागू", "26 नवंबर 1949 को अंगीकृत"]))],
 11: [("संदर्भ में Hindu Code Bill", dict(title="हिंदू कोड बिल", date="",
        lines=["विवाह · तलाक · संपत्ति · उत्तराधिकार", "महिलाओं के कानूनी अधिकार"])),
      ("इस्तीफा", dict(title="कानून मंत्री पद से त्यागपत्र", date="27 अक्टूबर 1951",
        lines=["हिंदू कोड बिल की धीमी प्रगति", "नीतिगत असहमतियाँ"]))],
 12: [("बौद्ध धर्म की दीक्षा", dict(title="धम्म दीक्षा", date="14 अक्टूबर 1956",
        lines=["नागपुर — दीक्षाभूमि", "लाखों अनुयायियों सहित धर्मांतरण"])),
      ("The Buddha and His Dhamma", dict(title="The Buddha and His Dhamma", date="1957 (मरणोपरांत)",
        lines=["आंबेडकर की बौद्ध व्याख्या", "अंतिम प्रमुख ग्रंथ"])),
      ("1935", dict(title="धर्म परिवर्तन की घोषणा", date="1935",
        lines=["येवला सम्मेलन", "\"हिंदू के रूप में नहीं मरूँगा\""]))],
 13: [("The Buddha and His Dhamma", dict(title="The Buddha and His Dhamma", date="अंतिम वर्षों में",
        lines=["आंबेडकर का अंतिम बौद्धिक ग्रंथ", "आधुनिक समाज हेतु बौद्ध दृष्टि"]))],
 14: [("6 दिसंबर 1956", dict(title="महापरिनिर्वाण", date="6 दिसंबर 1956",
        lines=["नई दिल्ली — 26 अलीपुर रोड", "आयु 65 वर्ष"]))],
 15: [("25 नवंबर 1949", dict(title="संविधान सभा — चेतावनी", date="25 नवंबर 1949",
        lines=["राजनीतिक बनाम सामाजिक-आर्थिक समानता", "लोकतंत्र की रक्षा"])),
      ("14 अप्रैल 1891", dict(title="जन्म", date="14 अप्रैल 1891",
        lines=["महू, मध्य प्रदेश", "सामाजिक सीमा से महानायक तक"])),
      ("6 दिसंबर 1956", dict(title="महापरिनिर्वाण", date="6 दिसंबर 1956",
        lines=["शरीर गया, सवाल जीवित"]))],
}

def fact_for(n, text):
    for kw, info in FACTS.get(n, []):
        if kw in text:
            return info
    return None

def scene_prompts(sc):
    """Distinct beat prompts for a scene. `beats` (a list) is preferred; a lone
    `p` is the single-image fallback (back-compat)."""
    beats = sc.get("beats")
    if isinstance(beats, list) and beats:
        return [str(x) for x in beats if str(x).strip()]
    return [sc["p"]]

def choose_beats(d, nprompts, max_beat=MAX_BEAT, min_beat=1.15):
    """How many <=3s beats to cut this scene into.

    Lower bound keeps every beat <=3s; upper bound stops cuts getting machine-gun
    fast; within that window we show as many of the distinct images as fit. Author
    generously — extra prompts are simply unused on short scenes, never crammed in.
    """
    min_beats = max(1, math.ceil(d / max_beat))
    max_beats = max(1, int(d // min_beat))
    return max(min_beats, min(nprompts, max_beats))

def dur(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)],capture_output=True,text=True).stdout or 0)

def geo_city(text):
    for k,v in GEO.items():
        if k in text: return v
    return None

def main(N):
    data = load_part(N)
    cfg = chapter_cfg(N, data)
    s = get_settings(); s.min_prompts=1; s.max_prompts=400; s.ensure_directories()
    W,H = s.default_width, s.default_height
    JOB = f"JOB-20{N}"
    storage = JobStorage(s)
    scenes = data["scenes"]
    palette = data["palette"]

    narr_dir = ROOT/f"assets/narration/ch{N:02d}"; narr_dir.mkdir(parents=True, exist_ok=True)
    img_dir = ROOT/f"assets/premium/ch{N:02d}"; img_dir.mkdir(parents=True, exist_ok=True)
    tts = SarvamTextToSpeech(api_key=s.sarvam_api_key, model=s.sarvam_model, speaker=s.sarvam_speaker,
                             sample_rate=s.sarvam_sample_rate, base_url=s.sarvam_base_url, timeout_seconds=90)
    gen = OpenAIImageGenerator(api_key=s.openai_api_key, model=s.openai_image_model,
                               size=s.openai_image_size, quality=s.openai_image_quality,
                               base_url=s.openai_base_url, timeout_seconds=s.api_timeout_seconds)

    # 1. narration (cache, one clip per scene) + 2. images (cache, one per BEAT)
    made_n = made_i = 0
    for i, sc in enumerate(scenes, start=1):
        clip = narr_dir/f"{i:03d}.m4a"
        if not clip.is_file():
            tts.synthesize(SpeechRequest(text=sc["n"], output_path=clip, voice=s.sarvam_speaker,
                           language="hi-IN", model=s.sarvam_model, pace=1.15)); made_n+=1
        sc["_dur"] = dur(clip)
        prompts = scene_prompts(sc)
        sc["_prompts"] = prompts
        sc["_geo"] = sc.get("geo")   # explicit opt-in only — a city mention never hijacks a scene
        if sc["_geo"]:
            continue  # geo_map draws itself, no image

        nbeats = choose_beats(sc["_dur"], len(prompts))
        sc["_nbeats"] = nbeats
        # which distinct prompts actually get screen time, spread across the beats
        used = sorted({b * len(prompts) // nbeats for b in range(nbeats)})
        sc["_imgs"] = {}
        for idx in used:
            legacy = img_dir/f"{i:03d}.png"            # image from the single-prompt era
            img = img_dir/f"{i:03d}_{idx}.png"
            if idx == 0 and not img.is_file() and legacy.is_file():
                img = legacy                            # REUSE — never regenerate what exists
            elif not img.is_file():
                prompt = f"{prompts[idx].rstrip('. ')}, {palette}, {STYLE}"
                try:
                    gen.generate(GenerationRequest(prompt=prompt, output_path=img, width=W, height=H,
                                 steps=1, seed=0, image_format="png")); made_i+=1
                except GenerationError as e:
                    print(f"  scene {i} beat {idx} blocked ({str(e)[:50]}) -> placeholder"); _placeholder(img, W, H)
            sc["_imgs"][idx] = img
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
            dlabel, ddate = GEO_LABEL.get(sc["_geo"], ("", ""))
            label = sc.get("geo_label", dlabel)
            gdate = sc.get("geo_date", ddate)
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
        prompts = sc["_prompts"]; nbeats = sc["_nbeats"]
        seg = d / nbeats
        # copy each distinct beat image into the job images dir once
        for idx, img in sc["_imgs"].items():
            shutil.copyfile(img, images/f"{i:03d}_{idx}.png")
        fact = fact_for(N, sc["n"]) or fact_for(N, " ".join(prompts))
        for b in range(nbeats):
            oi+=1; bs = start + b*seg; be = start + (b+1)*seg
            idx = b * len(prompts) // nbeats           # distinct image for this beat
            fn = f"{i:03d}_{idx}.png"
            if b == 0 and fact:
                anim = "info_card"
                params = f"lines={'|'.join(fact.get('lines',[]))}" + (f";date={fact['date']}" if fact.get('date') else "")
                tval = fact.get("title","")
            else:
                anim = None  # ffmpeg ken-burns move (fast, reliable, looks good)
                params = None; tval = None
            kb = None if (b==0 and fact) else KB[(i + b) % len(KB)]
            items.append(JobItem(job_id=JOB, prompt_id=oi, order_index=oi, external_id=str(oi),
                prompt_text=prompts[idx], start_seconds=round(bs,3), end_seconds=round(be,3),
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
