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

## What a batch does

Every prompt is generated automatically, one after another. **A failed prompt never stops the
batch** — it is recorded and generation continues. When the run finishes, ffmpeg renders one
H.264 MP4 named after the job (`JOB-001.mp4`), holding each image for its `start`→`end` window.

A failed prompt becomes **black frames for its segment**, so the timeline keeps its exact length
and every later scene stays on schedule. `Retry failed` re-runs only the failed prompts and
re-renders the video.

## Retention

A finished video is downloadable for **10 hours** (`ZIP_RETENTION_HOURS`). A cleanup worker runs
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
| Runware      | `runware`           | Hosted FLUX.1-schnell, ~$0.0006/image, no infra      |
| Pollinations | `pollinations`      | Free hosted API, no key — rate limited, watermarked  |
| ComfyUI      | `comfyui`           | Self-hosted FLUX (or any graph) via ComfyUI HTTP     |

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
cd backend && .venv/bin/python -m pytest      # 46 tests
cd frontend && npm run typecheck && npm run build
```

The suite covers the full acceptance path end to end against the mock backend: timeline
validation (gaps, overlaps, timecodes), rendering, **real durations probed back out of the
rendered file with ffprobe**, download, failure handling, retry-failed, cancel, the disk guard,
and expiry-based cleanup.

## Docker

```bash
docker compose up --build
```

Runs `frontend`, `backend` and `worker` as separate services sharing a data volume. The worker
is the only service that needs to reach the model.

---

## Infrastructure

Deliberately undecided. No VM, GPU, machine type or cloud provider is assumed anywhere in this
repository. Once a VM exists, the remaining work is: inspect the hardware, install ComfyUI and
FLUX, benchmark, point `GENERATOR_BACKEND=comfyui` at it, and deploy. `.github/workflows/deploy.yml`
stays inert until a `DEPLOY_HOST` secret is configured.
