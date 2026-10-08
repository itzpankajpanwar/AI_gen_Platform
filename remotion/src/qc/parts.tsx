import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { eased, interpolateEased } from "../lib/anim";
import { C, DISPLAY, SANS, T, TRACK, mono, clamp01 } from "./theme";

export const useT = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps, height, width } = useVideoConfig();
  return { frame, dur: durationInFrames, fps, H: height, Wd: width,
           t: durationInFrames <= 1 ? 1 : frame / (durationInFrames - 1) };
};

/** The still underneath a graphic: eased push, darkened so type stays legible. */
export const Plate: React.FC<{ image?: string; dim?: number; zoom?: number; pan?: number }> =
({ image, dim = 0.62, zoom = 1.06, pan = 0 }) => {
  const { frame, dur } = useT();
  const k = eased(frame, 0, dur, "none");
  if (!image) return <AbsoluteFill style={{ backgroundColor: C.ink }} />;
  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: C.ink }}>
      <Img src={staticFile(image)} style={{
        width: "100%", height: "100%", objectFit: "cover",
        transform: `scale(${1 + (zoom - 1) * k}) translateX(${pan * k}%)`,
      }} />
      <AbsoluteFill style={{ background:
        `linear-gradient(180deg, rgba(7,8,10,${dim + 0.1}) 0%, rgba(7,8,10,${dim * 0.55}) 45%, rgba(7,8,10,${dim + 0.14}) 100%)` }} />
    </AbsoluteFill>
  );
};

/** Flat graphic ground for scenes with no plate. A hair of vertical gradient
 *  stops a full-frame black reading as a dropout. */
export const Ground: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background:
    `radial-gradient(120% 90% at 50% 38%, #10161F 0%, ${C.ink} 72%)` }}>{children}</AbsoluteFill>
);

/** Small all-caps label. The film's only secondary type style. */
export const Kicker: React.FC<{ children: React.ReactNode; colour?: string; size?: number;
  delay?: number; style?: React.CSSProperties }> =
({ children, colour = C.textDim, size, delay = 0, style }) => {
  const { frame, H } = useT();
  const a = eased(frame, delay, 14, "power2.out");
  return <div style={{ ...mono, textTransform: "uppercase", letterSpacing: TRACK,
    fontSize: (size ?? T.label) * H, color: colour, fontWeight: 500,
    opacity: a, transform: `translateY(${(1 - a) * 8}px)`, ...style }}>{children}</div>;
};

/** A number set in Display, tabular, with an eased count-up when `to` is set. */
export const Num: React.FC<{ value?: string; from?: number; to?: number; size?: number;
  colour?: string; delay?: number; dp?: number; prefix?: string; suffix?: string;
  weight?: number; style?: React.CSSProperties }> =
({ value, from = 0, to, size = T.num, colour = C.text, delay = 0, dp = 0,
   prefix = "", suffix = "", weight = 600, style }) => {
  const { frame, H } = useT();
  const a = eased(frame, delay, 20, "power3.out");
  const shown = to !== undefined
    ? (from + (to - from) * a).toFixed(dp).replace(/\B(?=(\d{3})+(?!\d))/g, ",")
    : value ?? "";
  return <div style={{ fontFamily: `${DISPLAY}, ${SANS}, sans-serif`, fontVariantNumeric: "tabular-nums",
    fontFeatureSettings: '"tnum" 1', fontSize: size * H, color: colour, fontWeight: weight,
    letterSpacing: "-0.015em", lineHeight: 1, opacity: Math.min(1, a * 1.6), ...style }}>
    {prefix}{shown}{suffix}</div>;
};

/** A hairline that draws itself. Used to separate, underline and point. */
export const Rule: React.FC<{ w: number; delay?: number; dur?: number; colour?: string;
  thickness?: number; vertical?: boolean; style?: React.CSSProperties }> =
({ w, delay = 0, dur = 20, colour = C.line, thickness = 1, vertical = false, style }) => {
  const { frame } = useT();
  const g = interpolateEased(frame, delay, dur, 0, w, "power3.inOut");
  return <div style={{ width: vertical ? thickness : g, height: vertical ? g : thickness,
    backgroundColor: colour, ...style }} />;
};

/** The film's data panel: hairline box, no fill tricks, no glow. */
export const Panel: React.FC<{ children: React.ReactNode; delay?: number; pad?: number;
  style?: React.CSSProperties }> = ({ children, delay = 0, pad = 26, style }) => {
  const { frame } = useT();
  const a = eased(frame, delay, 16, "power3.out");
  return <div style={{ border: `1px solid ${C.line}`, background: "rgba(10,14,20,0.82)",
    backdropFilter: "blur(3px)", padding: pad, opacity: a,
    transform: `translateY(${(1 - a) * 14}px)`, ...style }}>{children}</div>;
};

/** One label/value row — the workhorse of every data callout in the film. */
export const Row: React.FC<{ k: string; v: string; delay?: number; accent?: boolean;
  dim?: boolean; size?: number }> = ({ k, v, delay = 0, accent, dim, size }) => {
  const { frame, H } = useT();
  const a = eased(frame, delay, 16, "power2.out");
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline",
      gap: 40, opacity: dim ? a * 0.38 : a, transform: `translateX(${(1 - a) * -10}px)`,
      padding: "7px 0", borderBottom: `1px solid ${C.lineSoft}` }}>
      <span style={{ ...mono, textTransform: "uppercase", letterSpacing: TRACK,
        fontSize: (size ?? T.label) * H, color: C.textFaint }}>{k}</span>
      <span style={{ ...mono, fontSize: (size ?? T.label) * H * 1.22,
        color: accent ? C.system : C.text, fontWeight: 600 }}>{v}</span>
    </div>
  );
};

/** Letterbox bars. Present on every graphic scene so cuts between a plate and
 *  a graphic never change the frame's shape. */
export const Bars: React.FC<{ h?: number }> = ({ h = 0.0 }) =>
  h <= 0 ? null : (
    <>
      <AbsoluteFill style={{ height: `${h * 100}%`, top: 0, background: C.ink }} />
      <AbsoluteFill style={{ height: `${h * 100}%`, top: `${(1 - h) * 100}%`, background: C.ink }} />
    </>
  );

/** Fade the whole graphic in and out so it sits inside the xfade chain cleanly. */
export const Hold: React.FC<{ children: React.ReactNode; inF?: number; outF?: number }> =
({ children, inF = 8, outF = 10 }) => {
  const { frame, dur } = useT();
  const o = Math.min(eased(frame, 0, inF, "power2.out"),
                     1 - eased(frame, dur - outF, outF, "power2.in"));
  return <AbsoluteFill style={{ opacity: clamp01(o) }}>{children}</AbsoluteFill>;
};
