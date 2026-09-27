# The Documentary Film Pipeline

This is the "premium" layer built on top of the generic CSV→video platform: a
repeatable pipeline that turns a written Hindi script into a cinematic
documentary — narrated, scored, colour-graded, with motion-graphic fact cards
and animated maps. It was built for **The Quiet Story** and its first film, a
15-part documentary on **Dr. B. R. Ambedkar**.

Where the base platform is *"a CSV of prompts → one video"*, this layer is
*"a chapter script → a finished film chapter"*, and it is **generate-once /
reuse-forever**: every image and every narration clip is cached the first time
and never regenerated on a re-run.

- **Builder:** [`scripts/build_premium.py`](../scripts/build_premium.py)
- **Input:** one JSON spec per chapter, [`scripts/film/part1.json`](../scripts/film/part1.json) … `part15.json`
- **Output:** `samples/film_premium/chapter{N}.mp4` + a `.srt` subtitle sidecar
- **Build one chapter:** `python scripts/build_premium.py 5`
- **Build the whole film:** [`deploy/build_all.sh`](../deploy/build_all.sh)

---

## How a chapter is built (end to end)

```
part{N}.json ─┬─▶ narration  : one Sarvam TTS clip per scene   → assets/narration/ch{NN}/  (cached)
              ├─▶ images     : one OpenAI image per BEAT        → assets/premium/ch{NN}/    (cached)
              ├─▶ beats      : each scene cut into ≤3s beats, each a DISTINCT image
              ├─▶ cards      : verified fact/date info-cards, geo maps, intro + end cards (Remotion)
              ├─▶ picture    : ffmpeg — Ken-Burns motion, colour grade, film grain, transitions
              ├─▶ sound      : voice + music bed (ducked) + ambience + auto SFX, mastered to −15 LUFS
              └─▶ subtitles  : .srt generated from the narration timings
```

The timeline is **audio-driven**: narration is synthesised first and each
scene lasts exactly as long as its spoken line, so picture and voice are locked
by construction.

---

## The chapter spec format

Each `scripts/film/part{N}.json`:

```json
{
  "chapter": 5,
  "title": "दो रास्ते",
  "palette": "split palette of London slate grey and Indian ochre, formal cold interiors",
  "grade": "neutral",
  "grain": "light",
  "music": "tension.mp3",
  "ambience": "room.mp3",
  "scenes": [
    {
      "n": "आंबेडकर और गांधी... भारतीय इतिहास के दो अत्यंत प्रभावशाली नाम।",
      "beats": [
        "Two empty wooden chairs facing each other across a bare table, cold window light, wide shot",
        "Two framed portraits turned face-away on a mantel, museum light, medium shot"
      ]
    },
    { "n": "…", "p": "single image prompt for a short scene" },
    { "n": "…", "geo": "nagpur", "geo_label": "नागपुर — दीक्षाभूमि", "geo_date": "14 अक्टूबर 1956" }
  ]
}
```

| Field | Meaning |
| ----- | ------- |
| `title` / `palette` / `grade` / `grain` / `music` / `ambience` | chapter-wide look and sound |
| scene `n` | the Hindi narration line — **one spoken clip per scene** |
| scene `beats` | a list of **distinct image prompts**, one shown per ≤3s beat |
| scene `p` | shorthand for a single-image scene (`beats` of length 1) |
| scene `geo` | opt-in animated map instead of an image (`geo_label`, `geo_date` optional) |

The chapter's colour, music, ambience, kicker ("भाग पाँच") and the end-card's
"next chapter" title are all derived from the spec — nothing is hardcoded
per chapter.

---

## Distinct-image beats (the ≤3s rule)

A long narration line would otherwise sit on one static image for 8–10s. The
builder cuts every scene into **beats of ≤3 seconds**, and each beat shows a
**different image** — documentary-style coverage with bold cuts, not one image
ken-burned.

- One **narration clip per scene** (never re-cut), so audio is untouched.
- `choose_beats(duration, n_prompts)` picks how many beats fit: enough to keep
  every beat ≤3s, capped so cuts never go faster than ~1.15s, using as many of
  the distinct prompts as fit.
- Beat images are cached per `(scene, beat)`. **Beat 0 falls back to the legacy
  `{scene}.png`**, so chapters generated in the single-image era reuse their
  existing image for free and only the *added* beats cost a new generation.
- Calibrated Hindi TTS rate ≈ **16.6 chars/sec**, so a scene needs roughly
  `ceil(chars / 50)` distinct prompts.

Inspect exactly what each beat will do with the **shot list** tool:

```bash
python scripts/shotlist.py        # → review/chapter{NN}.csv for all chapters
python scripts/shotlist.py 5      # one chapter, printed to screen too
```

The shot list resolves every beat's image prompt, animation, Ken-Burns move,
transition, grade, and any fact/date card — the things the JSON does *not*
store because the builder derives them.

---

## The 11 premium features

All eleven are implemented as **reusable pipeline features**, not per-chapter
one-offs:

| # | Feature | How |
| - | ------- | --- |
| 1 | **Music score** | Royalty-free procedural beds ([`scripts/make_music.py`](../scripts/make_music.py)): `somber`, `warm`, `tension`, `hopeful`. Ducked under the voice via sidechain compression. |
| 2 | **Sound design** | Ambience beds + one-shot SFX ([`scripts/make_sfx.py`](../scripts/make_sfx.py)) auto-placed on events — whoosh on transitions, thud on a map pin, ticks along a timeline, shimmer on a reveal. |
| 3 | **Depth / motion** | Varied ffmpeg Ken-Burns moves per beat (zoom/pan rotation). (The earlier 2.5D parallax was dropped — it looked like a split image.) |
| 4 | **Archival material** | A scene may point `source` at a real public-domain file, copied in instead of generated. |
| 5 | **Subtitles** | `.srt` generated from narration timings for every chapter. |
| 6 | **Pull-quotes** | Animated quote template (Remotion). |
| 7 | **Transitions** | xfade dissolves / fade-to-black between beats and scenes (with a frozen-tail headroom fix so long films don't collapse). |
| 8 | **Filmic grade** | Per-chapter colour grade + grain (`neutral warm cold sepia bleach teal_orange film cold_film noir`); LUT-ready. |
| 9 | **Title / intro + end cards** | Remotion intro card (brand + kicker + title) and end card (SUBSCRIBE + next chapter). |
| 10 | **Beat-cut to music** | BPM grid in the Shorts generator (`make_short --bpm`). |
| 11 | **Voice mastering** | EQ + compression + limiting on the narration, then the whole mix mastered to **−15 LUFS** (YouTube target). |

Plus two motion-graphic scene types the builder places automatically:

- **Fact / date info-cards** — verified, dated facts (Columbia 1913, Poona Pact
  24 Sept 1932, Republic 26 Jan 1950, Mahaparinirvan 6 Dec 1956, …) rendered as
  a Remotion card over the scene image. Keyword-matched from a per-chapter
  `FACTS` table in the builder.
- **Animated geo maps** — an offline India map (bundled TopoJSON, no tiles/keys)
  with an eased pan-zoom, a city pin, a Hindi label and a date badge.

---

## Devanagari text

Browsers (and therefore Remotion) shape Devanagari correctly; ffmpeg's
`drawtext` does **not**. So **every on-screen word is rendered through a
Remotion template**, never burned by ffmpeg. The film uses the **Mukta** font
(Regular + Bold), installed system-wide on the render host.

**Name convention:** the narration refers to the subject respectfully as
**डॉ. आंबेडकर** / **डॉ. भीमराव आंबेडकर**, never the bare surname.

---

## Generation backends

| Role | Backend | Config |
| ---- | ------- | ------ |
| Images | **OpenAI** `gpt-image` (quality `low`, 1536×1024, resized to 1280×720) | `GENERATOR_BACKEND=openai`, `OPENAI_API_KEY` |
| Narration | **Sarvam** `bulbul:v3`, speaker `ritu`, Hindi | `TTS_PROVIDER=sarvam`, `SARVAM_API_KEY` |

Pre-flight both keys before a long build:

```bash
python scripts/validate_keys.py
```

**Cost / performance (rough):** a low-quality gpt-image is ≈ **$0.0047**; a full
chapter is a few hundred images; the whole 15-chapter film is ≈ **$3** of images
plus Sarvam TTS. Render time depends on the host — see the VM guidance below.

---

## Shorts

[`scripts/make_short.py`](../scripts/make_short.py) produces vertical (9×16) or
landscape (16×9) Shorts with AI backgrounds, karaoke captions, motion graphics
and beat-synced cuts (`--bpm`), reusing the same audio/vfx pipeline. AI
backgrounds are cached by prompt hash so re-runs don't re-spend.

---

## Running it on a VM

The whole stack (UI + API + worker + renders) runs on a single VM. See
[`deploy/README.md`](../deploy/README.md) for the one-command push + provision.

- **`deploy/setup_vm.sh`** installs ffmpeg, Node, the headless-Chrome libraries
  Remotion needs, the Mukta fonts, the Python venv, builds the frontend, adds a
  swap file, and installs two systemd services (API+worker on `:8200`, web on
  `:3200`, both bound to localhost).
- **`deploy/push_to_vm.sh`** rsyncs the repo *including the cached assets* so
  nothing regenerates on the VM.
- **`deploy/build_all.sh`** builds all 15 chapters back to back, continuing past
  any single chapter that fails.

Sizing: rendering is CPU-bound (ffmpeg + headless-Chrome per-frame). A
`c2d-standard-8` (8 vCPU / 32 GB) renders the full film in ~1.5–2.5h; keep
`REMOTION_CONCURRENCY` around 5 and ensure ≥30 GB disk.

---

## Idempotency & re-runs

Re-running a chapter build **never re-spends**: narration is skipped if the clip
file exists, and an image is skipped if its cached file exists. To force a
regenerate, delete the specific cached file. Changing a narration line means
deleting that scene's clip so it is re-synthesised (this is what the respectful
name change required).
