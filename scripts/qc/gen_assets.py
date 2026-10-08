#!/usr/bin/env python3
"""Generate the film's keyed plate library — once, and never again.

Cost control is the whole point of this file. Every photoreal plate in the
film is referenced by key, not by prompt, so:

  * a plate used by four chapters costs ONE generation;
  * a re-run regenerates nothing — an existing file is left alone;
  * a plate is only ever re-made if you delete its file on purpose.

    python scripts/qc/gen_assets.py            # fill the gaps, print the bill
    python scripts/qc/gen_assets.py --dry-run  # what WOULD be generated
    python scripts/qc/gen_assets.py --only ds_ # just the keys with this prefix
"""
import argparse, json, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "qc"))

from app.config import get_settings
from app.generators.api_backends import OpenAIImageGenerator
from app.generators.base import GenerationError, GenerationRequest
from look import ASSETS

CACHE = ROOT / "assets" / "qc"
MANIFEST = CACHE / "_manifest.json"
WORKERS = 3          # polite concurrency; the API is the slow part, not us
ATTEMPTS = 3


def generate_one(gen, key: str, prompt: str, w: int, h: int) -> tuple[str, str, float]:
    out = CACHE / f"{key}.png"
    if out.is_file() and out.stat().st_size > 10_000:
        return key, "cached", 0.0
    started = time.perf_counter()
    last = ""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            gen.generate(GenerationRequest(prompt=prompt, output_path=out, width=w, height=h,
                                           steps=1, seed=0, image_format="png"))
            return key, "generated", time.perf_counter() - started
        except GenerationError as exc:
            last = str(exc)[:160]
            # A content refusal will not pass on a retry; a transport blip will.
            if "rejected" in last and "safety" in last.lower():
                break
            time.sleep(2 * attempt)
    return key, f"FAILED {last}", time.perf_counter() - started


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    CACHE.mkdir(parents=True, exist_ok=True)
    settings = get_settings()
    keys = sorted(k for k in ASSETS if k.startswith(args.only))
    missing = [k for k in keys if not (CACHE / f"{k}.png").is_file()]

    print(f"library {len(keys)} plates · cached {len(keys) - len(missing)} · to generate {len(missing)}")
    if args.dry_run or not missing:
        for k in missing:
            print(f"  would generate {k}")
        return 0

    gen = OpenAIImageGenerator(api_key=settings.openai_api_key, model=settings.openai_image_model,
                               size=settings.openai_image_size, quality=settings.openai_image_quality,
                               timeout_seconds=300)
    print(f"model {settings.openai_image_model} · quality {settings.openai_image_quality} "
          f"· {settings.openai_image_size} -> {settings.default_width}x{settings.default_height}")

    done, failed, spent = 0, [], 0.0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(generate_one, gen, k, ASSETS[k],
                               settings.default_width, settings.default_height) for k in missing]
        for fut in futures:
            key, status, secs = fut.result()
            done += 1
            spent += secs
            flag = "!!" if status.startswith("FAILED") else "  "
            print(f"{flag} [{done:2d}/{len(missing)}] {key:<26} {status} {secs:5.1f}s", flush=True)
            if status.startswith("FAILED"):
                failed.append((key, status))

    have = sorted(k for k in keys if (CACHE / f"{k}.png").is_file())
    MANIFEST.write_text(json.dumps({"plates": have, "count": len(have)}, indent=1))
    print(f"\n{len(have)}/{len(keys)} plates present · {len(failed)} failed · {spent/60:.1f} model-minutes")
    for k, s in failed:
        print(f"  FAILED {k}: {s}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
