#!/usr/bin/env python3
"""Synthesize a royalty-free SFX + ambience library with ffmpeg.

All original (no licensing) — safe to monetize. SFX are short one-shots placed
on animation events; ambience are loopable beds that sit under the score.

    python scripts/make_sfx.py     # writes assets/sfx/*.wav and assets/ambience/*.mp3
"""
import shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SFX = ROOT / "assets" / "sfx"
AMB = ROOT / "assets" / "ambience"

def run(args, out):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0 or not Path(out).is_file():
        raise SystemExit(f"ffmpeg failed for {out}:\n" + "\n".join(r.stderr.splitlines()[-6:]))

def sfx(b):
    SFX.mkdir(parents=True, exist_ok=True)
    # whoosh: pink-noise swish with a quick swell, for transitions/reveals
    run([b,"-y","-f","lavfi","-i","anoisesrc=d=0.7:c=pink:a=0.8",
         "-af","bandpass=f=1400:width_type=o:w=2.2,afade=t=in:d=0.08,afade=t=out:st=0.25:d=0.45,"
               "aecho=0.7:0.7:60:0.3,volume=0.7,aformat=channel_layouts=mono",
         str(SFX/"whoosh.wav")], SFX/"whoosh.wav")
    # thud: low impact for a pin drop / heavy cut
    run([b,"-y","-f","lavfi","-i","aevalsrc=0.9*sin(2*PI*(150-90*t)*t)*exp(-6*t):d=0.5",
         "-af","lowpass=f=400,volume=1.4,aformat=channel_layouts=mono", str(SFX/"thud.wav")], SFX/"thud.wav")
    # tick: short click for timeline ticks / counters
    run([b,"-y","-f","lavfi","-i","aevalsrc=0.6*sin(2*PI*2200*t)*exp(-70*t):d=0.06",
         "-af","volume=0.8,aformat=channel_layouts=mono", str(SFX/"tick.wav")], SFX/"tick.wav")
    # shimmer: bright bell for a reveal / title
    run([b,"-y","-f","lavfi","-i","aevalsrc=(0.5*sin(2*PI*1400*t)+0.3*sin(2*PI*2100*t)+0.2*sin(2*PI*2800*t))*exp(-3*t):d=1.1",
         "-af","aecho=0.8:0.85:120|300:0.4|0.25,volume=0.6,aformat=channel_layouts=mono", str(SFX/"shimmer.wav")], SFX/"shimmer.wav")
    # riser: rising chirp for hooks / tension
    run([b,"-y","-f","lavfi","-i","aevalsrc=0.5*sin(2*PI*(200+900*t)*t)*(t/1.4):d=1.4",
         "-af","bandpass=f=1200:width_type=o:w=3,afade=t=out:st=1.2:d=0.2,volume=0.55,aformat=channel_layouts=mono", str(SFX/"riser.wav")], SFX/"riser.wav")
    # sub: soft low boom for beats/impacts
    run([b,"-y","-f","lavfi","-i","aevalsrc=0.9*sin(2*PI*55*t)*exp(-4*t):d=0.6",
         "-af","volume=1.5,aformat=channel_layouts=mono", str(SFX/"sub.wav")], SFX/"sub.wav")

def amb(b):
    AMB.mkdir(parents=True, exist_ok=True)
    D=30
    beds = {
        # wind: filtered noise with slow movement — open/outdoor scenes
        "wind":  f"anoisesrc=d={D}:c=brown:a=0.5",
        # room: very low broadband hiss — interiors
        "room":  f"anoisesrc=d={D}:c=brown:a=0.18",
        # crowd: layered noise murmur — gatherings
        "crowd": f"anoisesrc=d={D}:c=pink:a=0.35",
        # ocean/water: brown noise with slow surf swell
        "ocean": f"anoisesrc=d={D}:c=brown:a=0.6",
    }
    filt = {
        "wind":  "lowpass=f=900,highpass=f=120,tremolo=f=0.1:d=0.5,volume=0.5",
        "room":  "lowpass=f=500,volume=0.5",
        "crowd": "lowpass=f=1600,highpass=f=200,tremolo=f=0.3:d=0.4,volume=0.45",
        "ocean": "lowpass=f=700,tremolo=f=0.12:d=0.6,volume=0.6",
    }
    for name, src in beds.items():
        out = AMB/f"{name}.mp3"
        run([b,"-y","-f","lavfi","-i",src,
             "-af", f"{filt[name]},afade=t=in:d=2,afade=t=out:st={D-2}:d=2,aformat=channel_layouts=stereo",
             "-ar","44100","-b:a","160k", str(out)], out)

def main():
    b = shutil.which("ffmpeg") or sys.exit("ffmpeg not found")
    sfx(b); amb(b)
    print("SFX:", ", ".join(p.name for p in sorted(SFX.glob("*.wav"))))
    print("Ambience:", ", ".join(p.name for p in sorted(AMB.glob("*.mp3"))))

if __name__ == "__main__":
    main()
