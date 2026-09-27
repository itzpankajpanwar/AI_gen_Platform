# AI Video Generation Platform

Upload a CSV timeline of prompts, walk away, come back to **one rendered video**.

The application is deliberately independent of where inference runs. It assumes exactly one
thing: *there is an image-generation worker somewhere*. Whether that is a mock renderer on a
laptop, ComfyUI on a workstation, or a GPU VM you create later is a configuration value.

```
Web UI → FastAPI → Job Manager → Generation Queue → Image Generation Worker
                                       → Image Storage → Video Render → Cleanup Worker
```

---

## Quick start (no GPU, no model)

```bash
# 1. backend
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m uvicorn app.main:app --port 8200

# 2. frontend (second terminal)
cd frontend
npm install
npm run dev
```

Or just `./scripts/start.sh`, which runs both and keeps the machine awake for long batches.

Open <http://localhost:3200>. The default `GENERATOR_BACKEND=mock` renders placeholder images,
so the whole CSV → images → video → download → expiry pipeline is exercisable immediately.

**Requires ffmpeg** on the PATH (`brew install ffmpeg`) to render the video.

Need a CSV to try it with:

```bash
python scripts/make_sample_csv.py 100 sample_prompts.csv
```

---

## CSV format

```csv
start,end,prompt
0,5,"1940s Indian railway station, cinematic documentary photography..."
5,7,"Steel foundry floor in 1950s India, sparks and silhouettes..."
```

That renders a **7 second video**: the first image holds the screen for 5 seconds, the second
for the remaining 2.

Two working examples live in [`samples/`](samples/):

| File | What it is |
| ---- | ---------- |
| [`samples/minimal.csv`](samples/minimal.csv) | The two-row example above — 7 seconds |
| [`samples/explainer_intro.csv`](samples/explainer_intro.csv) | A real 8-scene, 23-second documentary intro |

Both have been rendered end to end against a live backend.

- `start` and `end` are seconds (`7`, `7.5`) or timecodes (`01:30`)
- Repeat a **style suffix** on every row (palette, light, film stock, composition). Style drift
  between scenes is far more damaging to a finished video than any single image's quality
- The timeline must be **continuous and gap-free**, starting at 0 — overlaps and gaps are
  rejected with the exact times that clash, rather than guessing what should play
- Rows may be in any order; they are sorted by `start`
- Validation runs on upload — an invalid CSV never starts a batch

## The animation layer

The `animation` column turns a scene from a still with a camera move into a piece of motion
graphics — a title, a chapter card, a drawn timeline, a route across a map, a counting
statistic. Two engines share one vocabulary:

| Engine | Cost | What it is for |
| ------ | ---- | -------------- |
| ffmpeg presets | < 1s per scene | 28 texture and camera effects — grain, letterbox, handheld, punch-ins |
| Remotion templates | 2-4s of CPU per second of video | 11 React + SVG + GSAP graphics — real eased motion, masked reveals, drawn paths |

```csv
start,end,prompt,text_value,animation,animation_params
0,4,"a courtroom at dawn...",भीमराव रामजी आंबेडकर,title_reveal,size=0.085
4,9,"a weathered map table...",आंबेडकर का जीवन,timeline,"from=1891;to=1956;marks=1891,1947,1956;highlight=1947"
```

Both kinds of clip come out at the same fps, SAR and pixel format, so they cut and blend
together in the same film, and `grade`, `grain`, `transition`, narration and music apply to
either. [`samples/remotion_showcase.csv`](samples/remotion_showcase.csv) exercises all eleven
templates.

Full column reference: [`docs/SMART_CSV.md`](docs/SMART_CSV.md). Architecture and how to add a
template: [`docs/ANIMATION_LAYER.md`](docs/ANIMATION_LAYER.md).

Remotion needs its dependencies installed once; without them the ffmpeg presets still work:

```bash
npm install --prefix remotion
```

## The documentary film pipeline

On top of the generic CSV→video engine sits a **premium documentary pipeline** —
the one that produces cinematic, narrated, scored film chapters (built for the
channel *The Quiet Story* and its 15-part **Dr. B. R. Ambedkar** film).

Instead of a flat CSV, each chapter is a small JSON script
([`scripts/film/part{N}.json`](scripts/film/)), and one command builds the whole
chapter — generating and caching images (OpenAI) and narration (Sarvam), then
rendering:

```bash
python scripts/build_premium.py 5          # build chapter 5
bash   deploy/build_all.sh                  # build all 15 chapters
python scripts/shotlist.py                  # dump a per-beat shot list to review/
```

What it adds over the base engine:

- **Distinct-image beats** — every scene is cut into ≤3s beats, each a *different*
  image (documentary coverage), while keeping one narration clip per scene.
- **Verified fact/date cards** and **animated India maps** placed automatically.
- **Intro / end cards**, per-chapter **colour grade**, film grain, transitions.
- **Full sound design** — narration mastered over a ducked music bed, ambience,
  and auto-placed SFX, mixed to −15 LUFS; **`.srt`** subtitles.
- **Generate-once / reuse** — re-running never re-spends on cached images/audio.

Full details, spec format, the 11 premium features, cost/performance and the
name convention: **[`docs/FILM_PIPELINE.md`](docs/FILM_PIPELINE.md)**.

## What a batch does

Every prompt is generated automatically, one after another. **A failed prompt never stops the
batch** — it is recorded and generation continues. When the run finishes, ffmpeg renders one
H.264 MP4 named after the job (`JOB-001.mp4`), holding each image for its `start`→`end` window.

A failed prompt becomes **black frames for its segment**, so the timeline keeps its exact length
and every later scene stays on schedule. `Retry failed` re-runs only the failed prompts and
re-renders the video.

## Retention

A finished video is downloadable for a configurable window (`ZIP_RETENTION_HOURS`, currently **24 hours**). A cleanup worker runs
every 5 minutes and deletes the video, the images and the temporary job files of jobs whose
expiry has actually passed — nothing else.

## Disk protection

Before a batch starts, the API estimates `prompts × ESTIMATED_IMAGE_MB × DISK_SAFETY_FACTOR`
and compares it to real free space. If it does not fit, the job is refused with HTTP 507 and
a message naming required vs available space. No partial batch is created.

---

## Swapping the inference backend

Everything the application needs from a model lives behind one interface
([`backend/app/generators/base.py`](backend/app/generators/base.py)):

```python
class ImageGenerator(ABC):
    def generate(self, request: GenerationRequest) -> GenerationResult: ...
    def health_check(self) -> HealthStatus: ...
    def get_status(self) -> dict: ...
```

| Backend      | `GENERATOR_BACKEND` | Use                                                  |
| ------------ | ------------------- | ---------------------------------------------------- |
| Mock         | `mock`              | Local development and CI — no GPU, no model          |
| OpenAI       | `openai`            | Hosted `gpt-image` (used by the documentary pipeline)|
| Runware      | `runware`           | Hosted FLUX.1-schnell, ~$0.0006/image, no infra      |
| Pollinations | `pollinations`      | Free hosted API, no key — rate limited, watermarked  |
| ComfyUI      | `comfyui`           | Self-hosted FLUX (or any graph) via ComfyUI HTTP     |

**Narration (text-to-speech)** is pluggable the same way behind `TextToSpeech`:
`TTS_PROVIDER=mock` (silent clips of realistic length, no key), `sarvam`
(Indian-language voices — the documentary uses `bulbul:v3`, speaker `ritu`), or
`elevenlabs`. The scene timeline re-flows to the real length of each clip.

**No GPU anywhere?** Use `runware`: set `RUNWARE_API_KEY` and a 100-prompt batch costs
roughly $0.06 with nothing running between batches. `pollinations` needs no key at all and is
useful for trying the pipeline, but it rate-limits hard and stamps a watermark on every image —
raise `PROMPT_MAX_ATTEMPTS` (5 works well) so the retry backoff can absorb the 429s.

Hosted backends may not accept arbitrary dimensions — Runware wants multiples of 64 — so images
are generated at the nearest valid size and resized to the project's exact resolution.

Adding another (Diffusers, a remote queue, a different model server) means writing one class
and registering it in [`generators/factory.py`](backend/app/generators/factory.py). Nothing in
the API, UI, job manager or video pipeline changes.

The ComfyUI graph itself is data, not code:
[`comfyui/workflows/flux_schnell.json`](comfyui/workflows/flux_schnell.json). Occurrences of
`{{prompt}}`, `{{seed}}`, `{{width}}`, `{{height}}` and `{{steps}}` are substituted per request,
so the sampler, scheduler or checkpoint can change without touching Python.

## Where the worker runs

`RUN_WORKER_IN_API=true` (default) runs generation and cleanup as threads inside the API — one
process, easiest local setup. Set it to `false` and run the worker separately:

```bash
python -m app.workers.runner
```

The queue lives in the database, so the worker can be its own container (see
`docker-compose.yml`) or sit on a different machine next to the GPU, sharing `DATA_DIR`.

---

## Configuration

Copy `.env.example` to `.env`. Every value is optional; the defaults are the V1 targets —
FLUX.1-schnell, 1280×720 (16:9), PNG, 4 steps, batch size 1, random seed, 10-hour retention.

## API

| Method | Path                                  | Purpose                        |
| ------ | ------------------------------------- | ------------------------------ |
| GET    | `/api/health`                         | Liveness + backend health      |
| GET    | `/api/system`                         | Defaults, disk, backends       |
| POST   | `/api/projects`                       | Create a project               |
| GET    | `/api/projects`                       | List projects                  |
| GET    | `/api/projects/{id}`                  | Project detail                 |
| POST   | `/api/projects/{id}/upload-csv`       | Upload + validate a CSV        |
| POST   | `/api/projects/{id}/start`            | Start generation (disk-gated)  |
| GET    | `/api/projects/{id}/status`           | Live progress                  |
| POST   | `/api/projects/{id}/cancel`           | Cancel a running batch         |
| GET    | `/api/jobs`                           | Job history                    |
| GET    | `/api/jobs/{job_id}`                  | Job detail with per-prompt rows|
| POST   | `/api/jobs/{job_id}/retry-failed`     | Re-run only failed prompts     |
| GET    | `/api/jobs/{job_id}/download`         | Download the rendered MP4      |

Interactive docs at <http://localhost:8200/docs>.

## Data model (SQLite for V1)

`projects` → `prompts`, and each run creates a `jobs` row with one `job_items` row per prompt
(status, filename, seed, duration, attempts, error). Set `DATABASE_URL` to move to PostgreSQL
later; no application code changes.

## Tests

```bash
cd backend && .venv/bin/python -m pytest      # 150 tests
cd frontend && npm run typecheck && npm run build
```

The suite covers the full acceptance path end to end against the mock backend: timeline
validation (gaps, overlaps, timecodes), rendering, **real durations probed back out of the
rendered file with ffprobe**, download, failure handling, retry-failed, cancel, the disk guard,
and expiry-based cleanup. The animation tests also assert that the Python template table
and the TypeScript template registry cannot drift apart.

## Docker

```bash
docker compose up --build
```

Runs `frontend`, `backend` and `worker` as separate services sharing a data volume. The worker
is the only service that needs to reach the model.

---

## Deploy to a VM

The whole stack — UI + API + generation/render worker — runs on one Linux VM. A
turn-key kit lives in [`deploy/`](deploy/):

```bash
# on the VM host (needs your cloud login), from the repo on your machine
bash deploy/push_to_vm.sh      # rsync repo (incl. cached assets) + provision + start services
```

`deploy/setup_vm.sh` installs ffmpeg, Node, the headless-Chrome libraries
Remotion needs, the Mukta fonts, a Python venv, builds the frontend, adds swap,
and installs two systemd services (API+worker `:8200`, web `:3200`, bound to
localhost — reach them over an SSH tunnel, or open one port to your IP). Full
runbook: [`deploy/README.md`](deploy/README.md).

Because inference is hosted (OpenAI images, Sarvam TTS), **no GPU is required** —
a general-purpose/compute-optimized VM (e.g. `c2d-standard-8`, 8 vCPU / 32 GB)
runs everything. If you prefer self-hosted models, the image backend is still
swappable to ComfyUI/FLUX as above.

## Infrastructure notes

Nothing in the app assumes a specific provider — `GENERATOR_BACKEND` /
`TTS_PROVIDER` decide where inference happens, and the queue lives in the
database so the worker can be its own container (`docker-compose.yml`) or a
separate machine sharing `DATA_DIR`.
