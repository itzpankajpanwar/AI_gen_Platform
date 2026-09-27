#!/usr/bin/env python3
"""Resolve each chapter's JSON spec into a human-readable SHOT LIST (CSV).

Shows, per scene and per beat, exactly what the premium builder will do:
the image prompt, the animation/effect, the Ken-Burns move, the transition,
the grade, and any fact/date card or geo map. Durations use cached narration
when present, else are estimated from the Hindi text (~16.6 chars/sec).

    python scripts/shotlist.py          # all chapters -> review/chapterNN.csv
    python scripts/shotlist.py 5        # one chapter, also prints to screen
"""
import csv, json, math, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = (ROOT / "scripts/build_premium.py").read_text(encoding="utf-8")

# Pull the real tables out of build_premium.py so this never drifts from it.
def _grab(name, start, end):
    seg = BP[BP.index(start):BP.index(end)]
    ns = {}
    exec(seg, ns)
    return ns[name]

FACTS = _grab("FACTS", "FACTS = {", "def fact_for")
KB = _grab("KB", "KB = [", "\n\n# Hindi label")
GEO_LABEL = _grab("GEO_LABEL", "GEO_LABEL = {", "\n\n# Verified fact")
KICKER = _grab("KICKER", "KICKER = {", "\ndef load_part")
MAX_BEAT = 3.0
CPS = 16.6  # calibrated Hindi TTS rate


def fact_for(n, text):
    for kw, info in FACTS.get(n, []):
        if kw in text:
            return info
    return None


def scene_prompts(sc):
    b = sc.get("beats")
    return [str(x) for x in b if str(x).strip()] if isinstance(b, list) and b else [sc["p"]]


def choose_beats(d, nprompts, max_beat=MAX_BEAT, min_beat=1.15):
    lo = max(1, math.ceil(d / max_beat))
    hi = max(1, int(d // min_beat))
    return max(lo, min(nprompts, hi))


def dur(p):
    try:
        return float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout or 0)
    except Exception:
        return 0.0


def rows_for(N):
    data = json.loads((ROOT / f"scripts/film/part{N}.json").read_text(encoding="utf-8"))
    grade = data.get("grade", "neutral")
    narr_dir = ROOT / f"assets/narration/ch{N:02d}"
    rows = []
    t = 0.0
    rows.append(dict(scene="—", beat="—", start="0.0", end="3.5", kind="INTRO CARD",
                     anim="intro_card", ken_burns="", transition="fade", grade="",
                     card="", narration="", prompt=f"{data.get('title','')} / {KICKER.get(N,'')}"))
    t = 3.5
    for i, sc in enumerate(data["scenes"], 1):
        clip = narr_dir / f"{i:03d}.m4a"
        d = dur(clip) if clip.is_file() else round(len(sc["n"]) / CPS, 1)
        tag = "" if clip.is_file() else " (est)"
        start = t
        # geo scene
        if sc.get("geo"):
            dl, dd = GEO_LABEL.get(sc["geo"], ("", ""))
            label = sc.get("geo_label", dl)
            gdate = sc.get("geo_date", dd)
            rows.append(dict(scene=i, beat="1/1", start=f"{start:.1f}", end=f"{start+d:.1f}{tag}",
                             kind="GEO MAP", anim="geo_map", ken_burns="auto pan+zoom",
                             transition=("fadeblack" if i == 1 else "dissolve"), grade=grade,
                             card=f"{label} [{gdate}]", narration=sc["n"], prompt=f"(map: {sc['geo']})"))
            t = start + d
            continue
        prompts = scene_prompts(sc)
        nb = choose_beats(d, len(prompts))
        seg = d / nb
        fact = fact_for(N, sc["n"]) or fact_for(N, " ".join(prompts))
        for b in range(nb):
            idx = b * len(prompts) // nb
            bs = start + b * seg
            be = start + (b + 1) * seg
            if b == 0 and fact:
                anim = "info_card"; kb = ""; card = f"{fact['title']} [{fact.get('date','')}]"
            else:
                anim = ""; kb = KB[(i + b) % len(KB)]; card = ""
            transition = "dissolve" if b > 0 else ("dissolve" if i > 1 else "fadeblack")
            rows.append(dict(scene=i, beat=f"{b+1}/{nb}", start=f"{bs:.1f}", end=f"{be:.1f}{tag if b==0 else ''}",
                             kind="INFO CARD" if anim == "info_card" else "image beat",
                             anim=anim or "ken-burns", ken_burns=kb, transition=transition, grade=grade,
                             card=card, narration=sc["n"] if b == 0 else "", prompt=prompts[idx]))
        t = start + d
    rows.append(dict(scene="—", beat="—", start=f"{t:.1f}", end=f"{t+4:.1f}", kind="END CARD",
                     anim="end_card", ken_burns="", transition="dissolve", grade="",
                     card="", narration="", prompt="SUBSCRIBE / next chapter"))
    return rows


COLS = ["scene", "beat", "start", "end", "kind", "anim", "ken_burns",
        "transition", "grade", "card", "narration", "prompt"]


def main():
    out = ROOT / "review"; out.mkdir(exist_ok=True)
    which = [int(sys.argv[1])] if len(sys.argv) > 1 else list(range(1, 16))
    for N in which:
        if not (ROOT / f"scripts/film/part{N}.json").is_file():
            continue
        rows = rows_for(N)
        f = out / f"chapter{N:02d}.csv"
        with f.open("w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            w.writeheader(); w.writerows(rows)
        print(f"wrote {f.relative_to(ROOT)}  ({len(rows)} rows)")
        if len(which) == 1:
            for r in rows[:14]:
                print(f"  s{r['scene']:>2} {r['beat']:>4} {r['start']:>5}-{r['end']:<7} "
                      f"{r['kind']:<10} {r['anim']:<11} {r['ken_burns']:<12} {r['card'][:34]}")


if __name__ == "__main__":
    main()
