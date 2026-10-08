# THE TEN MINUTES

A 14½-minute documentary that follows a single quick-commerce order — four
items, ₹350, one button — from a thumb on a screen to a knock on a door, and
uses it to explain the machine behind the ten-minute promise.

Built on the repo's premium film pipeline, with its own screenplay, its own
plate library and its own motion-graphics vocabulary.

```
scripts/qc/look.py        the locked visual system + 57 keyed plate prompts
scripts/qc/script.py      the screenplay: 14 chapters, 136 scenes, 180 beats
scripts/qc/gen_assets.py  generate the plate library once, never again
scripts/qc/make_audio.py  score, ambience and SFX, synthesised
scripts/qc/build_film.py  narration → timeline → picture → sound → mp4 + srt
remotion/src/qc/          15 motion-graphics templates built for this film
```

## The finished film

`samples/film_premium/the-ten-minutes.mp4` — **14:34**, 1920x1080 at 30fps,
H.264, AAC stereo 44.1 kHz, mastered to **-15.1 LUFS** (LRA 2.6), 283 MB,
with `the-ten-minutes.srt` (128 cues) beside it.

| | | | | |
|-|-|-|-|-|
| 01 THE ORDER | 69.3s | 06 THE PICK | 57.1s | 11 THE CITY AS A MACHINE · 63.3s |
| 02 THE INVISIBLE SYSTEM | 63.2s | 07 PACKING | 40.5s | 12 THE ECONOMICS · 112.2s |
| 03 LOCATION INTELLIGENCE | 62.6s | 08 THE DISPATCH | 54.7s | 13 WHY DARK STORES EXIST · 79.4s |
| 04 THE DARK STORE | 78.7s | 09 THE ROAD | 46.4s | 14 TEN MINUTES · 56.6s |
| 05 INVENTORY | 65.0s | 10 THE CLOCK | 25.6s | |

## Build it

```bash
python scripts/qc/gen_assets.py      # plates (cached; a re-run spends nothing)
python scripts/qc/make_audio.py      # score + sfx (offline, no API)
python scripts/qc/build_film.py      # the whole film
python scripts/qc/build_film.py --ch 6   # one chapter, for review
python scripts/qc/build_film.py --plan   # print the cut, render nothing
```

Output: `samples/film_premium/the-ten-minutes.mp4` + `.srt`.

## The two colours

Everything in the film is built from exactly two accents, and they mean
something rather than decorate:

| | |
|---|---|
| **cold electric blue** `#4DA3FF` | the algorithm, data, the system |
| **warm sodium amber** `#E8A33D` | the street, the worker, the city at night |

When the picture is cold you are inside the machine; when it is warm you are
in the world the machine is moving through. That contrast is the film's
thesis, which is why no third accent is ever introduced.

## How it is put together

**The timeline is audio-driven.** Narration is synthesised first and every
scene lasts exactly as long as its spoken line plus an authored `hold` of
silence. Picture and voice are locked by construction, and rewriting a line
re-times the film automatically. Nine scenes have no narration at all — the
chapter-11 reveal and the final pull-back are held in silence on purpose.

**One city, seen five times.** Chapters 3, 8, 9, 11 and 14 all look at the
same procedurally built city from the same fixed axonometric camera; they
differ only in where the camera is and what is drawn on top. The store
positions are authored so that the distances drawn on screen agree with the
figures spoken over them (~6.7 m per world unit), and the three candidate
stores in chapter 3 frame together around the customer.

**The graphics are measured, not illustrated.** Chapter 6 draws the picking
walk over the real top-down photograph of the store floor, with bins on
actual rack rows; the 94 m → 67 m saving on screen is the saving that
geometry actually produces. Chapter 12's Sankey spends the margin down line
by line and is allowed to land on a negative number.

**Generate-once, reuse-forever, in both directions.** Plates are referenced
by key, so a plate used by four chapters costs one generation; narration is
cached per scene. A re-run of the whole build spends nothing. To re-record
one line, delete that one clip.

## Narration

Hindi, Sarvam `bulbul:v3`, speaker **`tanya`**, pace **1.05**. The voice was
chosen by auditioning ten of the model's female speakers on a real line from
the script and measuring delivery: `tanya` has the steadiest pitch contour
(IQR 47 Hz) and the highest voiced continuity (74%) of the shortlist, which
is what reads as calm and unhurried rather than performed.

Swapping it is one line in `.env` plus deleting `assets/qc_narration/` so the
clips re-synthesise. The plates are language-independent and cost nothing to
keep.

To hear the film in another speaker without touching the cut:

```bash
python scripts/qc/make_voice_alt.py shubh
```

That reads every line again into its own cache and lays the clips at the
film's own scene starts, giving a drop-in voice stem plus a CSV measuring each
line against the slot the cut allows it. `shubh` reads faster than `tanya`
(575s of speech against 843s of slot), so it fits with room to spare — only
two of 128 lines run over, by 0.38s and 0.14s.

All on-screen typography is **English and numeric only** — labels, counters,
data — set in Inter and Inter Display. Nothing Devanagari is ever drawn.

## The numbers

The economics in chapter 12 are a **representative illustration of the
category**, not any one company's accounts, and the narration says so on
screen and aloud. They are there to show the shape of the problem — that a
single order often does not pay for itself, and that basket size, order
density and advertising are what close the gap.

## Cost

| | |
|---|---|
| plates | 57 generations, `gpt-image-2.5-sunburst` at `low`, 1536×1024 |
| narration | 127 Sarvam clips, ~9,800 Hindi characters |
| everything else | synthesised locally — no API |

Two plates were regenerated once: `ds_topdown_floor` (the first result was a
perspective shot, and chapter 6 needs a true nadir view to draw on) and
`ds_handover` (it had lost the Indian context the rest of the film holds).
Nothing else was regenerated.
