#!/usr/bin/env python3
"""Build and generate every part of the script, one job per part.

    python scripts/run_all_parts.py 2 3 4      # selected parts
    python scripts/run_all_parts.py            # every part found
"""

import csv
import io
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

API = "http://127.0.0.1:8200"
SOURCES = ["scripts/parts_02_06.json", "scripts/parts_07_11.json", "scripts/parts_12_15.json"]
WORDS_PER_SECOND = 3.5
MIN_SCENE_SECONDS = 2.0
ROUND_TO = 0.5


def post(path, data=None, files=None):
    req = urllib.request.Request(API + path, method="POST")
    if data is not None:
        body = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    elif files:
        boundary = "----bnd"
        name, content = files
        body = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
            f"Content-Type: text/csv\r\n\r\n"
        ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    else:
        body = b""
    return json.load(urllib.request.urlopen(req, body))


def get(path):
    return json.load(urllib.request.urlopen(API + path))


def load_parts() -> dict[str, tuple[str, list]]:
    parts: dict[str, tuple[str, list]] = {}
    for source in SOURCES:
        path = pathlib.Path(source)
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for number, scenes in payload["parts"].items():
            parts[number] = (payload["style"], scenes)
    return parts


def build_csv(style: str, scenes: list) -> tuple[bytes, float]:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["start", "end", "prompt"])
    cursor = 0.0
    for scene in scenes:
        words = len(scene["narration"].split())
        duration = max(words / WORDS_PER_SECOND, MIN_SCENE_SECONDS)
        duration = round(duration / ROUND_TO) * ROUND_TO
        writer.writerow([f"{cursor:g}", f"{cursor + duration:g}", scene["prompt"] + style])
        cursor += duration
    return buf.getvalue().encode(), cursor


def run_part(number: str, style: str, scenes: list) -> dict | None:
    csv_bytes, total = build_csv(style, scenes)
    out = pathlib.Path(f"samples/part{number}_timeline.csv")
    out.write_bytes(csv_bytes)

    project = post("/api/projects", {"name": f"Ambedkar PART {number}"})
    validation = post(
        f"/api/projects/{project['id']}/upload-csv",
        files=(f"part{number}.csv", csv_bytes),
    )
    if not validation["valid"]:
        print(f"  PART {number}: INVALID CSV -> {validation['errors'][:2]}")
        return None

    print(f"  PART {number}: {validation['total']} scenes, {total:g}s ", end="", flush=True)
    job = post(f"/api/projects/{project['id']}/start")["job"]

    started = time.time()
    while time.time() - started < 3600:
        time.sleep(10)
        status = get(f"/api/projects/{project['id']}/status")
        if status["status"] not in ("queued", "running"):
            break
        print(".", end="", flush=True)

    ok, failed = status["successful"], status["failed"]
    out_info = status.get("output")
    print(
        f" -> {status['status']} ok={ok} fail={failed}"
        + (f" | {out_info['filename']} {out_info['duration_seconds']:g}s" if out_info else " | no video")
    )
    if failed:
        detail = get(f"/api/jobs/{status['job_id']}")
        first = next((i for i in detail["items"] if i["status"] == "failed"), None)
        if first:
            print(f"      first failure: {(first['error'] or '')[:110]}")
    return status


def main() -> None:
    parts = load_parts()
    wanted = sys.argv[1:] or sorted(parts, key=int)

    print(f"Generating parts: {', '.join(wanted)}\n")
    results = []
    for number in wanted:
        if number not in parts:
            print(f"  PART {number}: not found")
            continue
        style, scenes = parts[number]
        status = run_part(number, style, scenes)
        if status:
            results.append((number, status))
        if status and status["failed"] and status["successful"] == 0:
            print("\n  All scenes failed — stopping (check credits).")
            break

    print("\n=== summary ===")
    total_seconds = 0.0
    for number, status in results:
        out_info = status.get("output")
        seconds = out_info["duration_seconds"] if out_info else 0
        total_seconds += seconds
        print(
            f"  PART {number:>2}: {status['successful']:>2}/{status['total']:<2} scenes  "
            f"{seconds:>6.1f}s  {status['job_id']}"
        )
    print(f"  total video: {total_seconds/60:.1f} minutes")


if __name__ == "__main__":
    main()
