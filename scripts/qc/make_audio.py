#!/usr/bin/env python3
"""Score and sound design for THE TEN MINUTES — synthesised, not licensed.

Everything here is built from oscillators and filtered noise with ffmpeg, so
the film carries no licensing risk and the beds can be regenerated at any
length. The existing `scripts/make_music.py` beds are tuned for a period
historical film; a technology documentary needs a different palette, so these
are written alongside under a `qc_` prefix rather than replacing them.

    python scripts/qc/make_audio.py

Score beds (the `music` field in script.py):
    quiet_pulse  a low drone with a slow heartbeat — the opening
    system       cool, repeating, machine-like — decisions and algorithms
    room_tone    almost nothing; air and a low hum — the dark store
    drive        forward motion — the road
    machine      the big one: layered pulses that stack — the city reveal
    investigate  sparse and minor — the economics
    resolve      warm, settling, final

Ambience beds and the one-shot SFX the audio pipeline places on events.
"""
import shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MUSIC, AMB, SFX = ROOT/"assets"/"music", ROOT/"assets"/"ambience", ROOT/"assets"/"sfx"
DUR = 60          # the pipeline loops a bed to fill any length

def run(b, args, out):
    r = subprocess.run([b, "-y", *args, str(out)], capture_output=True, text=True)
    if r.returncode != 0 or not Path(out).is_file():
        raise SystemExit(f"ffmpeg failed for {out}:\n" + "\n".join(r.stderr.splitlines()[-8:]))
    print(f"  {Path(out).relative_to(ROOT)}")

# ---------------------------------------------------------------- score
# (tones, pulse Hz, pulse sharpness, filter, reverb, output gain)
BEDS = {
 "quiet_pulse": dict(tones=[(55,.55),(82.41,.22),(110,.18),(164.81,.07)],
                     pulse=0.58, sharp=6, lp=1800, verb="0.8:0.85:1100|1800:0.30|0.22", gain=0.52),
 "system":      dict(tones=[(65.41,.50),(98,.26),(130.81,.22),(196,.10)],
                     pulse=1.33, sharp=10, lp=2600, verb="0.7:0.8:420|760:0.26|0.18", gain=0.50),
 "room_tone":   dict(tones=[(49,.46),(73.42,.14),(98,.08)],
                     pulse=0.22, sharp=3, lp=900, verb="0.9:0.9:1500|2300:0.22|0.16", gain=0.40),
 "drive":       dict(tones=[(73.42,.52),(110,.26),(146.83,.20),(220,.10)],
                     pulse=2.0, sharp=12, lp=3200, verb="0.6:0.7:260|480:0.24|0.16", gain=0.54),
 "machine":     dict(tones=[(43.65,.60),(65.41,.30),(87.31,.24),(130.81,.16),(174.61,.09)],
                     pulse=1.0, sharp=8, lp=4200, verb="0.7:0.8:600|1100:0.30|0.22", gain=0.60),
 "investigate": dict(tones=[(58.27,.52),(69.30,.24),(103.83,.18),(138.59,.08)],
                     pulse=0.75, sharp=14, lp=2100, verb="0.8:0.85:820|1400:0.28|0.20", gain=0.48),
 "resolve":     dict(tones=[(65.41,.48),(98,.30),(123.47,.24),(164.81,.13)],
                     pulse=0.42, sharp=4, lp=2000, verb="0.85:0.9:1200|1900:0.30|0.22", gain=0.50),
}

def bed(b, name, tones, pulse, sharp, lp, verb, gain):
    """Detuned chord + a slow amplitude pulse, low-passed and reverbed.

    The pulse is an explicit expression rather than `tremolo` so each bed can
    have its own shape — a heartbeat in the opening, a hard machine pulse in
    the city reveal — instead of all of them breathing identically.
    """
    ins, filt, labels = [], [], []
    for i, (f, g) in enumerate(tones):
        # two voices a few cents apart: the beating is what stops it sounding synthetic
        ins += ["-f", "lavfi", "-i", f"sine=frequency={f}:duration={DUR}",
                "-f", "lavfi", "-i", f"sine=frequency={f*1.004:.4f}:duration={DUR}"]
        filt.append(f"[{2*i}]volume={g}[a{i}]")
        filt.append(f"[{2*i+1}]volume={g*0.7}[b{i}]")
        labels += [f"[a{i}]", f"[b{i}]"]
    graph = (";".join(filt) + ";" + "".join(labels) +
             f"amix=inputs={len(labels)}:normalize=0[chord];"
             # the pulse: a raised sine so the swell is gentle and the gap is real
             f"[chord]volume='0.40+0.60*pow(abs(sin(PI*t*{pulse})),{sharp})':eval=frame[p];"
             f"[p]lowpass=f={lp},aecho={verb},"
             f"volume={gain},afade=t=in:d=2.5,afade=t=out:st={DUR-3}:d=3,"
             "aformat=channel_layouts=stereo[out]")
    run(b, [*ins, "-filter_complex", graph, "-map", "[out]", "-ac", "2", "-ar", "44100",
            "-b:a", "192k"], MUSIC/f"qc_{name}.mp3")

# ------------------------------------------------------------ ambience
AMBS = {
 # name: (noise colour, filter chain) — all loopable, all sit far under the voice
 "warehouse":  ("brown", "lowpass=f=520,highpass=f=60,volume=0.22,"
                         "aecho=0.6:0.7:180|320:0.22|0.14"),
 "traffic":    ("brown", "lowpass=f=1500,highpass=f=90,volume=0.26,"
                         "tremolo=f=0.12:d=0.25,aecho=0.5:0.6:260|420:0.18|0.12"),
 "city_night": ("pink",  "lowpass=f=1100,highpass=f=120,volume=0.18,"
                         "tremolo=f=0.10:d=0.18,aecho=0.6:0.7:450|700:0.20|0.14"),
 "server_hum": ("brown", "lowpass=f=320,highpass=f=45,volume=0.24"),
 "room_night": ("brown", "lowpass=f=400,highpass=f=40,volume=0.13"),
}

def ambience(b, name, colour, chain):
    run(b, ["-f", "lavfi", "-i", f"anoisesrc=d={DUR}:c={colour}:a=0.9",
            "-af", f"{chain},afade=t=in:d=2,afade=t=out:st={DUR-2}:d=2,"
                   "aformat=channel_layouts=stereo",
            "-ac", "2", "-ar", "44100", "-b:a", "160k"], AMB/f"qc_{name}.mp3")

# ----------------------------------------------------------------- SFX
def sfx(b):
    # scanner beep: the single most-used diegetic sound in the film
    run(b, ["-f", "lavfi", "-i", "aevalsrc=0.55*sin(2*PI*2650*t)*exp(-16*t):d=0.18",
            "-af", "bandpass=f=2650:width_type=o:w=1.2,volume=0.9,"
                   "aformat=channel_layouts=mono"], SFX/"beep.wav")
    # phone tap: a soft, short, glassy click
    run(b, ["-f", "lavfi", "-i", "aevalsrc=0.5*sin(2*PI*900*t)*exp(-55*t):d=0.10",
            "-af", "highpass=f=400,volume=0.75,aformat=channel_layouts=mono"], SFX/"tap.wav")
    # data sweep: the system thinking — a rising filtered noise, no sci-fi whoosh
    run(b, ["-f", "lavfi", "-i", "anoisesrc=d=0.9:c=pink:a=0.7",
            "-af", "highpass=f=700,lowpass=f=5200,afade=t=in:d=0.35,"
                   "afade=t=out:st=0.5:d=0.4,volume=0.42,"
                   "aformat=channel_layouts=mono"], SFX/"sweep.wav")
    # reveal impact: low, short, felt rather than heard. Used sparingly.
    run(b, ["-f", "lavfi", "-i", "aevalsrc=0.95*sin(2*PI*(62-26*t)*t)*exp(-3.2*t):d=1.3",
            "-af", "lowpass=f=180,volume=1.5,aformat=channel_layouts=mono"], SFX/"impact.wav")

def main():
    b = shutil.which("ffmpeg")
    if not b:
        raise SystemExit("ffmpeg not found")
    for d in (MUSIC, AMB, SFX):
        d.mkdir(parents=True, exist_ok=True)
    print("score:")
    for name, cfg in BEDS.items():
        bed(b, name, **cfg)
    print("ambience:")
    for name, (colour, chain) in AMBS.items():
        ambience(b, name, colour, chain)
    print("sfx:")
    sfx(b)
    print("done")

if __name__ == "__main__":
    main()
