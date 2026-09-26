# Smart CSV format

One row per scene. The row carries everything needed to generate the image *and* cut it
into the film — timing, transition, motion, grade, grain, music, on-screen text and narration.

**Every column except `start`, `end` and `prompt` is optional. An empty cell means
"don't apply this."**

```csv
start,end,prompt,transition,ken_burns,grade,grain,music,text_type,text_value,narration,voice,animation
```

---

## Columns

| # | Column | Required | Values |
| - | ------ | -------- | ------ |
| 1 | `start` | yes | Seconds (`7`, `7.5`) or timecode (`01:30`) |
| 2 | `end` | yes | Same. Must be greater than `start` |
| 3 | `prompt` | yes | Image prompt sent to the generator |
| 4 | `transition` | no | How this scene arrives from the previous one |
| 5 | `ken_burns` | no | Camera move across the still |
| 6 | `grade` | no | Colour treatment for this image |
| 7 | `grain` | no | Film grain strength for this image |
| 8 | `music` | no | Music bed — **starts here and continues** until changed |
| 9 | `text_type` | no | Which on-screen text style to use |
| 10 | `text_value` | no | The exact text to display (Hindi supported) |
| 11 | `narration` | no | Line to be spoken by TTS over this scene |
| 12 | `voice` | no | Voice override for this row |
| 13 | `animation` | no | **Animation preset or template — overrides `ken_burns` and `text_type`** |
| 14 | `animation_params` | no | `key=value;key=value` inputs for a Remotion template |

---

## Vocabularies

### `transition` — how this scene arrives

| Value | Effect |
| ----- | ------ |
| *(empty)* | Hard cut |
| `cut` | Hard cut (explicit) |
| `fade` / `dissolve` | Crossfade from previous image |
| `fadeblack` | Through black |
| `fadewhite` | Through white |
| `wipeleft`, `wiperight`, `wipeup`, `wipedown` | Directional wipe |
| `slideleft`, `slideright`, `slideup`, `slidedown` | Push |

Optional duration: `dissolve:0.8` (default `0.5`).

**Transitions never change total duration.** A dissolve *straddles* the boundary — the tail of
the outgoing scene overlaps the head of the incoming one. A 0–5s scene followed by a 5–7s scene
with `dissolve:0.5` blends across 4.75–5.25s and the film is still 7s long.

This is deliberate: if transitions added time, a 25-minute film would drift seconds out of sync
with its narration. Row 1 has no predecessor — a transition there fades up from black.

### `ken_burns` — motion across the still

| Value | Effect |
| ----- | ------ |
| *(empty)* | Static hold |
| `zoom_in` | Slow push in |
| `zoom_out` | Slow pull out |
| `pan_left`, `pan_right`, `pan_up`, `pan_down` | Drift |
| `zoom_in_pan_left` (etc.) | Combined |

Optional strength: `zoom_in:1.15` — the end-state scale. Default `1.08`.

Speed is derived from the scene's duration, so a long hold moves slowly and a short one moves
briskly. **Alternate direction between neighbouring scenes**; uniform motion becomes its own tell.

> **Headroom:** motion crops into the image. Generating at 2048×1152 for a 1920×1080 output
> gives only ~1.07×, enough for a gentle drift. For `zoom_in:1.2` or stronger, generate larger
> (2560×1440) or upscale first.

### `grade` — colour treatment

| Value | Look |
| ----- | ---- |
| *(empty)* | Untouched |
| `warm` | Golden, lifted blacks — childhood, dawn, hope |
| `cold` | Blue-grey, cool shadows — London, winter, institutions |
| `sepia` | Archival brown |
| `bleach` | Desaturated, high contrast — conflict, hardship |
| `noir` | Near-monochrome, crushed blacks |
| `neutral` | Mild normalisation only |

Set a different grade per chapter — one uniform look across 25 minutes reads as monotonous.

### `grain` — film texture

`light`, `medium`, `heavy`, or a number `0`–`100`. Empty means none.

Grain is the cheapest way to make AI stills feel like one coherent stock. It also hides the
soft micro-detail of cheaper generation tiers.

### `music` — audio bed

A filename (`somber.mp3`). **The bed starts on that row and continues through following rows
until another value appears.** Use `stop` to end it.

So you set music once per chapter, not once per scene. It is automatically ducked beneath the
narration via sidechain compression.

### `text_type` / `text_value` — on-screen text

| `text_type` | Placement |
| ----------- | --------- |
| `center_title` | Large, centred — chapter openings |
| `full_card` | Centred on a dimmed frame — standalone statement |
| `lower_third` | Bottom-left — names, places |
| `date_stamp` | Top-right, small caps — dates |
| `corner_number` | Small corner numeral — part/section marker |
| `subtitle` | Bottom-centre — translations, quotes |

`text_value` holds the literal string. Hindi, English and mixed strings all render.

**Use text sparingly.** Captioning every scene is what makes AI video look cheap. Reserve it for
dates, names and the occasional statement.

### `narration` / `voice`

`narration` is the line spoken over this scene. `voice` overrides the project default for that
row — useful for a second narrator or a quoted passage.

### `animation` — the animation layer

When set, the preset takes over the scene's **motion and on-screen text**.
`ken_burns` and `text_type` are ignored (the CSV warns you), while `grade` and
`grain` still apply so an animated scene keeps the film's look. Presets that show
text read it from `text_value`.

**Vox family** — bold, graphic, explainer-style:

| Value | Effect |
| ----- | ------ |
| `vox_title` | Accent bar wipes in from the left, bold text lands on it |
| `vox_lower_bar` | Full-width bottom bar wipes in with a caption |
| `vox_highlight` | Outline box draws itself around the centre, with a label |
| `vox_stat` | One large figure rises into a dimmed frame — numbers, claims |

**Map family** — location and movement:

| Value | Effect |
| ----- | ------ |
| `map_zoom` | Accelerating push into the centre, like a map diving to a place |
| `map_pin` | A marker drops, settles, then names the location |
| `map_reveal` | Frame lifts out of darkness as a frame-line opens outward |

**Documentary family** — archival texture:

| Value | Effect |
| ----- | ------ |
| `doc_archival` | Vignette, heavy grain and slow gate weave — projector footage |
| `doc_photo` | A bordered print on a dark table, slowly pushed into |
| `doc_title_card` | Picture recedes to near-black so a statement carries the beat |
| `doc_timeline` | A progress rule creeps along the foot under a year label |

Optional intensity: `map_zoom:2.5` pushes harder, `vox_highlight:0.6` draws a
bigger box, `doc_archival:8` weaves more.

`vox_title`, `vox_lower_bar`, `vox_stat`, `doc_title_card` and `doc_timeline`
**require** a `text_value`. The rest show text only if you give them one.

#### A limitation of the ffmpeg presets

ffmpeg's `drawbox` filter has no `eval=frame` option, so any box it draws has
its position and size frozen at the first frame. The presets built on boxes —
`reveal_bars`, `reveal_wipe`, `reveal_iris`, `type_underline`, `paper_redact`
and the bar in `vox_lower_bar` — therefore appear in place instead of growing
or travelling. They are still usable graphics; they simply do not animate. The
Remotion templates below exist because that ceiling is not liftable in ffmpeg.

---

### Remotion templates — the premium animation layer

Names in the same `animation` column, but rendered by Remotion (React + SVG,
with GSAP easing curves) in a headless browser rather than by a filter graph.
They get real eased motion, masked reveals, SVG line drawing and proper
Devanagari typography. Their inputs come from `animation_params`.

| Value | Effect | `animation_params` |
| ----- | ------ | ------------------ |
| `ken_burns_pro` | Eased camera move that settles instead of stopping dead | `zoom`, `pan` (left/right/up/down), `curve`, `travel`, `dim`, `vignette`, `grain` |
| `split_compare` | Two stills meeting at a travelling wipe line | `second` (**required**), `label_a`, `label_b` |
| `title_reveal` | Masked headline wiping up behind a sweeping accent rule | `size` |
| `lower_third` | Slab that slides in behind an accent edge, then slides out | `sub` |
| `quote` | Pulled quotation revealed word by word | `by` |
| `chapter_card` | Kicker, drawn rule, then the title word by word | `chapter` |
| `timeline` | A year axis that draws itself, ticks landing one by one | `from`, `to`, `marks` (**required**), `highlight` |
| `map_route` | A route drawing across the frame with a travelling head | `path` (**required**) |
| `stat_counter` | A number counting up inside a ring that fills as it climbs | `to`, `from`, `suffix`, `label` |
| `bar_chart` | Bars growing in sequence with their labels | `values` (**required**), `labels` |
| `highlight_callout` | A ring drawn onto a point of the image, with a leader and caption | `x`, `y`, `r` |

`title_reveal`, `lower_third`, `quote`, `chapter_card`, `stat_counter` and
`highlight_callout` **require** a `text_value`.

#### Writing `animation_params`

Pairs are separated by `;`, so a value may contain commas:

```
from=1891;to=1956;marks=1891,1927,1947,1956;highlight=1947
```

Because the cell contains commas, **quote it in the CSV**:

```csv
...,timeline,"from=1891;to=1956;marks=1891,1927,1947,1956;highlight=1947"
```

An unquoted cell spills into the next column; the parser rejects the row and
tells you which values were stray rather than silently dropping them.

`x`, `y` and the points in `path` are percentages of the frame, so a template
looks the same at 720p and 4K. `second` names another scene by its row number
(`second=7`) or an image filename already in the job's folder.

Unknown template names, unknown parameter keys and missing required parameters
are all caught when the CSV is uploaded — never twenty minutes into a render.

#### Cost

A Remotion scene costs roughly 2-4 seconds of CPU per second of video, against
well under a second for an ffmpeg preset. A job bundles the project once and
then renders each animated scene from that bundle, so the overhead is paid per
job, not per scene. Use Remotion for the scenes that carry information —
titles, chapter openers, statistics, maps, timelines — and the ffmpeg presets
for everything in between.

---

## Timing modes

Set at project level.

**`audio` (default when a `narration` column is present)**
Each row's narration is synthesised, its real duration measured, and the scene stretched to
match. `start`/`end` are recomputed and the whole timeline re-flowed. Picture and voice are
locked by construction — no drift, no manual sync.

**`fixed`**
`start`/`end` are authoritative. Narration is laid in as-is; if the audio is longer than the
window you get a warning naming the row.

Use `audio` for a narrated film. Use `fixed` when the timing is driven by something else —
music, or an existing edit.

---

## TTS configuration

Per project, not per row:

| Setting | Example |
| ------- | ------- |
| `tts_provider` | `sarvam`, `elevenlabs` |
| `tts_model` | `bulbul:v3` |
| `tts_language` | `hi-IN` |
| `tts_voice` | default speaker; overridden by column 12 |
| `tts_pace` | `0.9` — slower suits documentary |
| `tts_pitch` | `0` |
| `tts_loudness` | `1.0` |

Same shape as the image generator: one interface, swappable providers, keys from the
environment. Nothing else in the pipeline changes when you switch from Sarvam to ElevenLabs.

---

## Fonts

Bundled in `assets/fonts/`:

- `NotoSansDevanagari-Regular.ttf`
- `NotoSerifDevanagari-Regular.ttf`

Both are SIL Open Font License. Devanagari needs **harfbuzz** in ffmpeg for correct conjunct and
matra shaping — without it Hindi renders as disconnected glyphs. Verified working on this build.

---

## Worked example

```csv
start,end,prompt,transition,ken_burns,grade,grain,music,text_type,text_value,narration,voice,animation
0,3,"old Indian city at dawn, 1900s stone architecture",fadeblack,zoom_in,warm,light,somber.mp3,,,"भारत के इतिहास में कुछ नाम ऐसे हैं",
3,6,"empty formal chair behind an official desk",dissolve,pan_right,warm,light,,,,"जिन्हें सिर्फ उनके पद से नहीं समझा जा सकता",
6,8,"long empty corridor of a government building",dissolve,zoom_out,cold,light,,,,"कुछ लोग मंत्री बने",
13,15,"empty pale dawn sky over a central Indian plain",fade,,warm,medium,,,"1891","",,vox_stat
15,17,"British Indian Army cantonment, whitewashed barracks",cut,,sepia,medium,,,"महू छावनी, मध्य भारत","मध्य भारत की महू छावनी",,map_pin
```

Reading row by row: the film fades up from black on a warm, lightly grained city at dawn with a
slow push-in, while `somber.mp3` begins and the first line is narrated. The bed continues
through every following row. Row 4 hands the scene to `vox_stat`, which dims the frame and
raises **1891** into it. Row 5 uses `map_pin` to drop a marker and name the cantonment, keeping
the sepia grade underneath.

A third example, [`samples/animation_showcase.csv`](../samples/animation_showcase.csv), runs all
eleven presets back to back.

---

## Backwards compatibility

Three-column CSVs still validate. All new columns are optional, and the existing rules are
unchanged: the timeline must be contiguous and gap-free, a failed prompt becomes black frames
without shortening the film, `retry-failed` regenerates only the failures, and output expires
after the retention window.
