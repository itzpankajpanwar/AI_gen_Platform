#!/usr/bin/env python3
"""Rebuild chapter 1 as many short beats over the EXISTING narration.

Chapter 1's narration is already generated (assets/narration/ch01). This keeps
that audio untouched: each narration segment's real duration is read back from
its clip, and the segment is subdivided into <=3s image beats. So the voice is
identical; only the pictures get denser, better, and more animated.

    python scripts/build_ch1.py   ->  samples/film/part01_v2.csv (fixed timings)
"""

import csv
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NARR = ROOT / "assets" / "narration" / "ch01"
OUT = ROOT / "samples" / "film" / "part01_v2.csv"
MAX_BEAT = 3.0

# Photorealistic house look for gpt-image-2.5. Faces are allowed now.
STYLE = (
    "photorealistic, authentic late-1800s to early-1900s central India, "
    "period-accurate clothing and setting, natural skin texture, volumetric "
    "warm dawn light, shot on 35mm, shallow depth of field, fine film grain, "
    "muted ochre and earth tones, cinematic documentary still, no on-image text, "
    "no captions, no watermark, 16:9"
)

COLUMNS = ["start","end","prompt","transition","ken_burns","grade","grain",
           "music","text_type","text_value","narration","voice","animation","animation_params"]

# For each of the 23 narration segments: the narration line (reference only) and
# the ordered sub-shots. Each beat: (subject, motion). motion is either a
# ken_burns move, a cine_/beat_ preset, or a Remotion template dict.
# A beat may carry ("text", type, value[, params]) to layer a caption/graphic.
def kb(m): return {"ken_burns": m}
def cine(m): return {"animation": m}
def rem(name, **params): return {"animation": name, "animation_params": ";".join(f"{k}={v}" for k,v in params.items())}

SEGMENTS = [
 # 1
 [("A vast dry central-Indian plain at first light, a single cart track to the horizon, one distant walking figure, dust in low sun, extreme wide shot",
   {**rem("title_reveal", size="0.075"), "text":("center_title","भीमराव रामजी आंबेडकर")}),
  ("A wall of old sepia-toned framed portraits of distinguished 1900s Indian men in a dim archive, warm museum light, close shot", cine("cine_dolly"))],
 # 2
 [("An ornate empty ministerial chair behind a large desk in a colonial council chamber, shafts of window light, medium shot", kb("zoom_in:1.18")),
  ("A scholar's desk piled with law books, brass spectacles and an oil lamp at night, close shot", kb("zoom_out:1.16"))],
 # 3
 [("A lone young Indian man in simple 1900s dress standing and facing a large seated village assembly, strong backlight, wide shot", cine("cine_handheld")),
  ("Close portrait of a resolute young Indian man's face, early 1900s, direct gaze, warm rim light, photorealistic", kb("zoom_in:1.14"))],
 # 4
 [("A weathered barracks door with iron studs, raking dawn light on the wood grain, extreme close-up",
   {**rem("lower_third", sub="महू छावनी, मध्य भारत"), "text":("lower_third","14 अप्रैल 1891")})],
 # 5
 [("A British-Indian army cantonment at dawn, rows of whitewashed barracks around a bare parade ground, distant hills, extreme wide shot",
   {**rem("lower_third", sub="ब्रिटिश भारतीय छावनी"), "text":("lower_third","महू छावनी")})],
 # 6
 [("A spare barracks room interior, a cloth-lined wooden cradle, a mother's hands adjusting the blanket, soft dawn light, close shot", kb("zoom_in:1.16")),
  ("Extreme close-up of a newborn baby's hand curled around an adult finger, warm light, photorealistic", kb("zoom_in:1.22")),
  ("The quiet barracks room with the cradle, dust turning in a shaft of light, medium shot",
   {**rem("lower_third", sub="जन्म"), "text":("lower_third","भीमराव रामजी आंबेडकर")})],
 # 7
 [("Small bare footprints crossing the dust of an empty barracks parade ground at dawn, long soft shadows, a doorway beyond, no people in frame, wide shot", kb("zoom_in:1.15")),
  ("Low angle silhouette of a small child from behind looking up at a vast pale dawn sky, face not visible", cine("cine_punch")),
  ("The boy's small bare feet crossing a wide empty parade ground, long shadow, wide shot", kb("pan_right"))],
 # 8
 [("Overhead looking straight down at a child's bare feet at a hard line where swept earth meets rough ground", cine("cine_dolly")),
  ("A hand-written official register page under lamplight, columns of ink, no legible text, extreme close-up", cine("cine_punch")),
  ("A small child standing alone and distant at the edge of a village courtyard while others sit apart, seen from behind, wide shot", cine("cine_handheld"))],
 # 9
 [("A cluster of low mud-walled houses set apart at the edge of an 1890s Indian village, a bare strip of ground separating them, wide shot", kb("zoom_in:1.12")),
  ("A dignified Mahar family in simple clothing standing at their doorway, warm light, photorealistic faces, honest documentary portrait, medium shot", kb("zoom_in:1.14"))],
 # 10
 [("A queue of villagers at a stone well in hot light, one small group kept markedly further back, medium shot",
   {**cine("cine_handheld"), "text":("subtitle","अस्पृश्यता")}),
  ("Close portrait of a weary Indian woman waiting in the heat, dust on her shawl, photorealistic", kb("zoom_in:1.15")),
  ("An empty brass pot on cracked dry ground beside the well, harsh light, close shot", kb("zoom_out:1.16"))],
 # 11
 [("A brass pot overflowing at a village well, water breaking the surface, hands and forearms only, extreme close-up",
   {**rem("vox_title"), "text":("center_title","पानी")})],
 # 12
 [("A child's slate and chalk on a bare earth floor set apart from a row of wooden school desks, extreme close-up",
   {**rem("vox_title"), "text":("center_title","स्कूल")})],
 # 13
 [("A temple doorway from ground level at the foot of worn stone steps, dark interior beyond, low angle",
   {**rem("vox_title"), "text":("center_title","मंदिर")})],
 # 14
 [("A village square at midday, a stone platform under a peepal tree, people seated in separate clusters, wide shot",
   {**rem("vox_title"), "text":("center_title","सार्वजनिक स्थान")})],
 # 15
 [("Two men in 1890s Indian dress passing on a narrow lane, both turning their bodies away, deliberate distance, medium shot", cine("cine_handheld")),
  ("Close on one man averting his gaze as he passes, tense, photorealistic", kb("zoom_in:1.14"))],
 # 16
 [("A modern hand lifting an old sepia photograph off a dark table, present meeting past, extreme close-up", cine("cine_punch")),
  ("A sprawling late-1800s Indian town at dusk seen from a hillside, quarters divided by open ground and low walls, cooking smoke, extreme wide shot", cine("cine_dolly")),
  ("A low mud wall dividing two narrow lanes in an old Indian town, hard shadow, medium shot", kb("pan_left")),
  ("Overhead of townspeople gathered in separate clusters with clear empty ground between them, high shot", kb("zoom_out:1.18")),
  ("The divided town fading into blue dusk, lamps beginning to light in separate quarters, wide shot", cine("cine_dolly"))],
 # 17
 [("A small child sitting on a stone doorstep with a book open on his knees, seen from behind, a courtyard beyond, late light, medium shot", kb("zoom_in:1.15"))],
 # 18
 [("A dignified Indian man in British-Indian army uniform, early 1900s, honest photorealistic face, warm portrait light, medium shot",
   {**rem("lower_third", sub="ब्रिटिश भारतीय सेना"), "text":("lower_third","रामजी मालोजी सकपाल")}),
  ("A folded army coat and cap on a wooden peg with polished boots beneath, lamplight, close shot", kb("zoom_out:1.16"))],
 # 19
 [("A father's weathered hands opening a school exercise book on a low table, a child's small hand reaching in, close shot", kb("zoom_in:1.18")),
  ("A father in his 30s teaching a child by lamplight at night, the father's face warm and focused, the child seen from behind, photorealistic adult, medium shot", cine("cine_dolly")),
  ("Close on the exercise book and a slate side by side under the lamp, chalk dust, extreme close-up", kb("zoom_in:1.2")),
  ("A father and a child studying together seen from behind over their shoulders, warm pool of lamplight in the dark room, medium shot",
   {**rem("vox_title"), "text":("center_title","शिक्षा")})],
 # 20
 [("A spare one-room home at night lit by a single oil lamp, a family's few belongings against the wall, wide shot", kb("zoom_in:1.12")),
  ("A child reading on the floor by the oil lamp seen from behind, absorbed, face not visible, close shot", cine("cine_punch")),
  ("Close portrait of a mother in her 30s watching, quiet resolve, photorealistic adult face, warm lamplight", kb("zoom_in:1.15"))],
 # 21
 [("An open page of printed Devanagari script under an oil lamp, a fingertip on a line, deep dark around, extreme close-up", cine("cine_punch")),
  ("Extreme close-up of a hand following a line of Devanagari text on a page, lamplight, no face in frame", kb("zoom_in:1.18")),
  ("A single oil-lamp flame steady against total darkness, macro", kb("zoom_out:1.2")),
  ("A child silhouetted against a small window at dawn holding a book, face not visible, hopeful, wide shot", cine("cine_dolly"))],
 # 22
 [("Over the shoulder of a child writing Devanagari letters on a slate by lamplight, seen from behind, chalk dust, close shot", kb("zoom_in:1.16")),
  ("Close on a child's hands gripping chalk and pressing letters onto a slate, warm light, no face in frame", kb("zoom_in:1.15")),
  ("A small stack of well-worn books growing on a low table, morning light, close shot", kb("zoom_out:1.16")),
  ("A child holding a slate up seen from behind toward the light, quiet pride, face not visible, medium shot",
   {**rem("vox_title"), "text":("center_title","स्वाभिमान")})],
 # 23
 [("A small boy walking away down a long dusty road at dawn toward a distant town, vast sky, extreme wide shot", cine("cine_dolly")),
  ("The empty road stretching to the horizon, warm dust and light, wide shot", kb("pan_right")),
  ("The boy tiny against an enormous brightening dawn sky, low angle", cine("cine_punch")),
  ("The sun breaking fully over the plain, warm light flooding the frame, extreme wide shot", kb("zoom_in:1.14")),
  ("The lone figure reaching a rise in the road as the town appears ahead, hopeful, extreme wide shot",
   {**rem("lower_third", sub="जन्म और पहचान"), "text":("lower_third","भाग एक")})],
]

CAMERA_ONLY = {"cine_handheld","cine_dolly","cine_punch","beat_flash","beat_pulse","beat_shake","reveal_fade_up"}
TEXT_ANIMS = {"title_reveal","lower_third","vox_title","chapter_card","quote"}

def seg_duration(i: int) -> float:
    clip = NARR / f"{i:03d}.m4a"
    out = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                          "-of","csv=p=0",str(clip)], capture_output=True, text=True)
    return round(float(out.stdout.strip()), 3)

def build():
    rows = []
    cursor = 0.0
    prev_anim = None
    for idx, beats in enumerate(SEGMENTS, start=1):
        dur = seg_duration(idx)
        n = max(1, min(len(beats), math.ceil(dur / MAX_BEAT)))
        # if authored beats fewer than needed splits, still use authored count
        n = len(beats)
        slice_len = dur / n
        for b, beat in enumerate(beats):
            subject, motion = beat
            start = cursor
            end = cursor + slice_len
            cursor = end
            row = {c: "" for c in COLUMNS}
            row["start"] = f"{start:.3f}"
            row["end"] = f"{end:.3f}"
            row["prompt"] = f"{subject}, {STYLE}"
            row["grade"] = "warm"
            row["grain"] = "light"
            # transition: dissolve within a segment, gentle cut between segments
            row["transition"] = "cut" if b == 0 and idx > 1 else "dissolve"
            if idx == 1 and b == 0:
                row["transition"] = "fadeblack"
            if "animation" in motion:
                row["animation"] = motion["animation"]
                if motion.get("animation_params"):
                    row["animation_params"] = motion["animation_params"]
            elif "ken_burns" in motion:
                row["ken_burns"] = motion["ken_burns"]
            if "text" in motion:
                tt = motion["text"]
                row["text_value"] = tt[1]
                # text_type only layers on the camera-only cine/beat presets;
                # Remotion templates and vox_* read their text from text_value.
                if row["animation"] in CAMERA_ONLY:
                    row["text_type"] = tt[0]
            rows.append(row)
    total = cursor
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS); w.writeheader(); w.writerows(rows)
    animated = sum(1 for r in rows if r["animation"])
    print(f"{len(rows)} beats over {total:.2f}s ({animated} with a graphic preset) -> {OUT.relative_to(ROOT)}")
    # sanity: total should match preserved narration (130.7s)
    print(f"narration track = 130.73s ; video timeline = {total:.2f}s")

if __name__ == "__main__":
    build()
