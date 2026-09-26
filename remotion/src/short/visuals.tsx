import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig, interpolate, random } from "remotion";
import { eased, interpolateEased } from "../lib/anim";
import { SANS } from "../lib/useFont";

export const C = {
  bg0: "#05070f",
  bg1: "#0b1327",
  accent: "#E0A65C",   // brand gold
  cyan: "#5AD7E6",
  danger: "#FF5A4D",
  ink: "#F4F7FF",
  dim: "rgba(255,255,255,0.55)",
};

/** Deep-space gradient + drifting starfield + subtle grid. Ties every scene together. */
export const SpaceBackdrop: React.FC<{ danger?: number }> = ({ danger = 0 }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const stars = Array.from({ length: 90 }, (_, i) => {
    const x = random(`x${i}`) * width;
    const y = (random(`y${i}`) * height + frame * (0.2 + random(`s${i}`) * 0.6)) % height;
    const r = 0.6 + random(`r${i}`) * 1.8;
    const tw = 0.4 + 0.6 * Math.abs(Math.sin((frame + i * 30) * 0.05));
    return { x, y, r, tw };
  });
  return (
    <AbsoluteFill style={{ background: `radial-gradient(120% 90% at 50% 18%, ${C.bg1}, ${C.bg0} 70%)` }}>
      <svg width={width} height={height} style={{ position: "absolute" }}>
        {stars.map((s, i) => (
          <circle key={i} cx={s.x} cy={s.y} r={s.r} fill="white" opacity={s.tw * 0.8} />
        ))}
      </svg>
      {danger > 0 ? (
        <AbsoluteFill style={{ background: `radial-gradient(80% 60% at 50% 45%, rgba(255,60,45,${0.28 * danger}), transparent 70%)` }} />
      ) : null}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 320px rgba(0,0,0,0.85)" }} />
    </AbsoluteFill>
  );
};

/** A stylised globe with lat/long lines. `alive` fades it toward dark/red when GPS "dies". */
export const Globe: React.FC<{ cx: number; cy: number; r: number; spin?: number; alive?: number }> = ({
  cx, cy, r, spin = 0, alive = 1,
}) => {
  const frame = useCurrentFrame();
  const rot = (spin ? frame * spin : 0) % 360;
  const stroke = `rgba(90,215,230,${0.35 * alive + 0.1})`;
  const face = alive < 0.5 ? "#1a0d0f" : "#0c2036";
  return (
    <g transform={`translate(${cx},${cy})`}>
      <circle r={r} fill={face} stroke={C.cyan} strokeOpacity={0.5 * alive + 0.1} strokeWidth={2} />
      <ellipse rx={r} ry={r * 0.34} fill="none" stroke={stroke} strokeWidth={1.5} />
      <ellipse rx={r * 0.62} ry={r} fill="none" stroke={stroke} strokeWidth={1.5}
               transform={`rotate(${rot * 0.3})`} />
      <ellipse rx={r * 0.9} ry={r * 0.62} fill="none" stroke={stroke} strokeWidth={1} />
      <ellipse rx={r} ry={r * 0.66} fill="none" stroke={stroke} strokeWidth={1} transform="rotate(0)" />
    </g>
  );
};

/** A small satellite glyph (body + two solar panels). */
export const Satellite: React.FC<{ x: number; y: number; s?: number; on?: number; rot?: number }> = ({
  x, y, s = 1, on = 1, rot = 0,
}) => {
  const col = on > 0.5 ? C.accent : "#5b6472";
  return (
    <g transform={`translate(${x},${y}) scale(${s}) rotate(${rot})`} opacity={0.4 + 0.6 * on}>
      <rect x={-10} y={-8} width={20} height={16} rx={3} fill={col} />
      <rect x={-34} y={-6} width={18} height={12} rx={2} fill="#2b3550" stroke={col} strokeWidth={1.5} />
      <rect x={16} y={-6} width={18} height={12} rx={2} fill="#2b3550" stroke={col} strokeWidth={1.5} />
      <circle r={3} fill={on > 0.5 ? C.cyan : "#333"} />
    </g>
  );
};

/** Expanding signal rings from a point. */
export const PingRings: React.FC<{ cx: number; cy: number; startFrame?: number; colour?: string; max?: number }> = ({
  cx, cy, startFrame = 0, colour = C.accent, max = 220,
}) => {
  const frame = useCurrentFrame();
  return (
    <g>
      {[0, 1, 2].map((i) => {
        const local = ((frame - startFrame) - i * 14) % 42;
        if (local < 0) return null;
        const p = local / 42;
        return <circle key={i} cx={cx} cy={cy} r={p * max} fill="none" stroke={colour}
                       strokeWidth={3} opacity={(1 - p) * 0.7} />;
      })}
    </g>
  );
};

/** A beam of travelling dots between two points. */
export const Beam: React.FC<{ x1: number; y1: number; x2: number; y2: number; startFrame?: number; colour?: string; reverse?: boolean }> = ({
  x1, y1, x2, y2, startFrame = 0, colour = C.cyan, reverse = false,
}) => {
  const frame = useCurrentFrame();
  const draw = eased(frame, startFrame, 14, "power2.out");
  const dots = Array.from({ length: 6 }, (_, i) => {
    let t = (((frame - startFrame) * 0.03) + i / 6) % 1;
    if (reverse) t = 1 - t;
    return { x: x1 + (x2 - x1) * t, y: y1 + (y2 - y1) * t };
  });
  return (
    <g opacity={draw}>
      <line x1={x1} y1={y1} x2={x1 + (x2 - x1) * draw} y2={y1 + (y2 - y1) * draw}
            stroke={colour} strokeOpacity={0.35} strokeWidth={2} strokeDasharray="2 8" strokeLinecap="round" />
      {dots.map((d, i) => <circle key={i} cx={d.x} cy={d.y} r={3.2} fill={colour} />)}
    </g>
  );
};

/** A location pin (teardrop). */
export const Pin: React.FC<{ x: number; y: number; s?: number; colour?: string; q?: boolean }> = ({
  x, y, s = 1, colour = C.accent, q = false,
}) => (
  <g transform={`translate(${x},${y}) scale(${s})`}>
    <path d="M0,40 C-26,4 -22,-30 0,-30 C22,-30 26,4 0,40 Z" fill={colour} />
    {q ? <text y={-2} textAnchor="middle" fontSize={30} fontWeight={800} fill="#05070f"
              fontFamily={`${SANS},sans-serif`}>?</text>
       : <circle cy={-6} r={9} fill="#05070f" />}
  </g>
);

/** A clock face with sweeping hands + concentric time-signal waves. */
export const Clock: React.FC<{ cx: number; cy: number; r: number; startFrame?: number }> = ({
  cx, cy, r, startFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const t = frame - startFrame;
  const min = t * 6;
  const hr = t * 0.9;
  return (
    <g transform={`translate(${cx},${cy})`}>
      {[0, 1, 2].map((i) => {
        const local = (t - i * 16) % 48;
        if (local < 0) return null;
        const p = local / 48;
        return <circle key={i} r={r + p * 160} fill="none" stroke={C.cyan} strokeWidth={2} opacity={(1 - p) * 0.6} />;
      })}
      <circle r={r} fill="#0c2036" stroke={C.accent} strokeWidth={4} />
      {Array.from({ length: 12 }, (_, i) => (
        <rect key={i} x={-1.5} y={-r + 6} width={3} height={12} rx={1.5} fill={C.dim}
              transform={`rotate(${i * 30})`} />
      ))}
      <line x1={0} y1={0} x2={0} y2={-r * 0.5} stroke={C.ink} strokeWidth={6} strokeLinecap="round"
            transform={`rotate(${hr})`} />
      <line x1={0} y1={0} x2={0} y2={-r * 0.78} stroke={C.accent} strokeWidth={4} strokeLinecap="round"
            transform={`rotate(${min})`} />
      <circle r={6} fill={C.accent} />
    </g>
  );
};

/** A phone outline. */
export const Phone: React.FC<{ x: number; y: number; s?: number; children?: React.ReactNode }> = ({ x, y, s = 1, children }) => (
  <g transform={`translate(${x},${y}) scale(${s})`}>
    <rect x={-70} y={-140} width={140} height={280} rx={26} fill="#0c1424" stroke={C.dim} strokeWidth={3} />
    <rect x={-58} y={-120} width={116} height={240} rx={12} fill="#0a1830" />
    {children}
  </g>
);


/** A photographic background (dimmed, slow Ken Burns) with the space look as
 *  fallback. Motion graphics and captions render on top, so the dim is heavy
 *  enough to keep white text readable over any image. */
export const Backdrop: React.FC<{ bg?: string; danger?: number }> = ({ bg, danger = 0 }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  if (!bg) return <SpaceBackdrop danger={danger} />;
  const t = eased(frame, 0, durationInFrames, "power1.inOut");
  const scale = 1.06 + 0.08 * t;
  return (
    <AbsoluteFill style={{ backgroundColor: C.bg0, overflow: "hidden" }}>
      <Img src={staticFile(bg)} style={{ width: "100%", height: "100%", objectFit: "cover",
            transform: `scale(${scale})`, transformOrigin: "center" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(5,7,15,0.5) 0%, rgba(5,7,15,0.72) 55%, rgba(5,7,15,0.9) 100%)" }} />
      {danger > 0 ? (
        <AbsoluteFill style={{ background: `radial-gradient(80% 60% at 50% 42%, rgba(255,60,45,${0.3 * danger}), transparent 70%)` }} />
      ) : null}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.8)" }} />
    </AbsoluteFill>
  );
};
