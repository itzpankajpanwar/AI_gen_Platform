# The animation layer

The film is still cut by ffmpeg. Motion graphics are drawn by Remotion and
handed back to ffmpeg as ordinary clips.

```
CSV row ──► image generator ──► still (PNG)
                                   │
              animation column ────┤
                                   │
        ffmpeg preset ◄────────────┴───────────► Remotion template
     (filter graph, <1s)                      (React + SVG + GSAP, 2-4s/s)
                                   │
                                   ▼
                        one clip per scene, all at the
                        same fps / SAR / pixel format
                                   │
                                   ▼
                   xfade chain ──► narration + music ──► final mp4
```

## Why two engines

ffmpeg filters are fast and need nothing installed. They are also a dead end
for real motion graphics: `drawbox` exposes no `eval=frame`, so every box it
draws is frozen at the geometry it had on frame one — bars, wipes, underlines
and redactions appear rather than animate. `drawtext` can fade and move, but it
cannot mask, stagger words, draw an SVG path or ease anything.

Remotion renders React in a headless browser, one frame at a time, so a
template can do whatever a web page can: masked reveals, `stroke-dashoffset`
line drawing, staggered typography, and GSAP easing curves. It costs roughly
2-4 seconds of CPU per second of video, so it is used per scene, by name, not
for the whole film.

## How a scene is routed

`video_service.build_job_video` plans every clip before rendering any of them,
then:

* `animation` naming an **ffmpeg preset** (`animations.py`) → `_render_scene`,
  a single ffmpeg invocation over the still.
* `animation` naming a **Remotion template** (`remotion.py`) → the clip is
  rendered by Remotion and then conformed by ffmpeg, which is also where
  `grade` and `grain` are applied so an animated scene still carries the film's
  look.
* Neither → the plain `ken_burns` / `text_type` path.

Conforming is not optional: every clip in the xfade chain must agree on fps,
sample aspect ratio and pixel format, or the graph fails at the first mismatch
with `Error reinitializing filters`.

## The bundle

`staticFile()` resolves against whatever was in the public directory when the
project was bundled, so a job:

1. copies each animated scene's still into a private staging directory,
2. copies the configured Devanagari fonts in beside them — the same two files
   ffmpeg draws with, so the two renderers cannot drift apart,
3. bundles the project **once**,
4. renders every animated scene from that bundle,
5. deletes the staging directory.

Bundling dominates the cost, which is why it is per job rather than per scene.

## Adding a template

1. Write a component in `remotion/src/templates/` taking `SceneProps`.
   Drive everything from `useCurrentFrame()` — never a live GSAP timeline, or
   frames rendered in parallel will disagree. `lib/anim.ts` has the helpers:
   `eased`, `interpolateEased`, `stagger`, and `num`/`str`/`list` for reading
   `params`.
2. Register it in `remotion/src/templates/index.ts`.
3. Describe it in `TEMPLATES` in `backend/app/services/remotion.py`: its
   summary, whether it needs `text_value`, and every parameter it reads.

Nothing else changes — the CSV validator, the renderer and the docs all read
that one table. `tests/test_remotion.py` fails if the TypeScript registry and
the Python table stop agreeing, which is what keeps step 3 from being skipped.

## Running it

```bash
npm install --prefix remotion
```

Then any CSV using a Remotion template renders through the normal pipeline.
`samples/remotion_showcase.csv` exercises all eleven.

To design a template interactively:

```bash
npm run studio --prefix remotion
```

Settings: `REMOTION_DIR`, `REMOTION_CONCURRENCY` (0 = let Remotion size it),
`REMOTION_TIMEOUT_SECONDS`, `REMOTION_CRF`, and `REMOTION_ACCENT` /
`REMOTION_INK` — the two colours every template themes itself from, so a whole
film can be re-styled without touching a CSV.
