import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { eased, interpolateEased } from "../lib/anim";
import { SANS, SERIF } from "../lib/useFont";
import {
  Beam, C, Clock, Globe, Phone, Pin, PingRings, Satellite, SpaceBackdrop,
} from "./visuals";

/* --------------------------------------------------------------- data model */
export interface ShortSeg {
  start: number;              // seconds — when this line's audio begins
  text: string;
  emphasis?: string;
  scene: string;              // a key in the scene library below
  params?: Record<string, string>;
}
export interface ShortProps {
  audio: string;              // filename in the public dir
  segments: ShortSeg[];
  accent: string;
  brand: string;
  durationInFrames: number;
  fps: number;
}

const P = (params: Record<string, string> | undefined, k: string, d = "") => params?.[k] ?? d;

/* ------------------------------------------------------------------ captions */
const Caption: React.FC<{ text: string; emphasis?: string; accent: string }> = ({ text, emphasis, accent }) => {
  const frame = useCurrentFrame();
  const { height } = useVideoConfig();
  const words = text.split(" ");
  const rise = eased(frame, 0, 10, "power3.out");
  const emph = new Set((emphasis ?? "").split(" "));
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: height * 0.20 }}>
      <div style={{ maxWidth: "86%", textAlign: "center", transform: `translateY(${(1 - rise) * 40}px)`,
                    opacity: rise, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0.22em 0.44em" }}>
        {words.map((w, i) => {
          const on = eased(frame, 3 + i * 2.2, 9, "back.out(1.6)");
          const hot = emph.has(w.replace(/[।,?…!.]/g, ""));
          return (
            <span key={i} style={{
              fontFamily: `${SANS}, sans-serif`, fontWeight: 800,
              fontSize: height * (hot ? 0.05 : 0.043), lineHeight: 1.15,
              color: hot ? accent : C.ink, opacity: on,
              transform: `translateY(${(1 - on) * 14}px)`, display: "inline-block",
              textShadow: "0 3px 20px rgba(0,0,0,0.9), 0 1px 3px rgba(0,0,0,0.9)",
            }}>{w}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Svg: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { width, height } = useVideoConfig();
  return <svg width={width} height={height} style={{ position: "absolute" }}>{children}</svg>;
};

/* ------------------------------------------------------ reusable scene library */
// Every scene takes (params, accent). They are topic-agnostic: a script picks
// scenes and feeds params (emoji, items, value…), so any narration can drive them.

const Statement: React.FC<{ accent: string }> = () => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  return (
    <AbsoluteFill>
      <SpaceBackdrop />
      <Svg><PingRings cx={width / 2} cy={560} colour={C.accent} max={200} /></Svg>
    </AbsoluteFill>
  );
};

const Keyword: React.FC<{ params?: Record<string, string>; accent: string }> = ({ params }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const emoji = P(params, "emoji", "✨");
  const pop = eased(frame, 2, 16, "back.out(1.8)");
  const danger = P(params, "danger") === "1" ? eased(frame, 26, 20) : 0;
  return (
    <AbsoluteFill>
      <SpaceBackdrop danger={danger * 0.6} />
      <Svg>{danger < 0.5 ? <PingRings cx={width / 2} cy={560} colour={C.cyan} max={160} /> : null}</Svg>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingBottom: 360 }}>
        <div style={{ fontSize: 300, transform: `scale(${pop})`, filter: `grayscale(${danger})` }}>{emoji}</div>
        {danger > 0.4 ? <div style={{ position: "absolute", fontSize: 220, color: C.danger, fontWeight: 900, marginBottom: 360 }}>✕</div> : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const ListScene: React.FC<{ params?: Record<string, string>; accent: string }> = ({ params }) => {
  const frame = useCurrentFrame();
  const items = P(params, "items", "🏦 Banking,📡 Telecom,🖥️ Systems,💳 Payments,🌐 Networks,⚙️ More")
    .split(",").map((s) => s.trim()).filter(Boolean).slice(0, 6);
  const fail = P(params, "fail") === "1";
  return (
    <AbsoluteFill>
      <SpaceBackdrop danger={fail ? eased(frame, 34, 22) * 0.6 : 0} />
      <div style={{ position: "absolute", inset: 0, top: 300, height: 700, display: "grid",
                    gridTemplateColumns: "repeat(2,1fr)", alignContent: "center", justifyItems: "center", rowGap: 30 }}>
        {items.map((it, i) => {
          const pop = eased(frame, 4 + i * 4, 12, "back.out(2)");
          const x = fail ? eased(frame, 40 + i * 3, 14) : 0;
          const [ic, ...lab] = it.split(" ");
          return (
            <div key={i} style={{ transform: `scale(${pop})`, textAlign: "center" }}>
              <div style={{ fontSize: 84, filter: `grayscale(${x}) brightness(${1 - x * 0.5})`, position: "relative" }}>
                {ic}
                {x > 0.4 ? <span style={{ position: "absolute", left: 0, right: 0, color: C.danger, fontWeight: 900 }}>✕</span> : null}
              </div>
              <div style={{ fontFamily: `${SANS},sans-serif`, color: C.dim, fontSize: 26, marginTop: 4 }}>{lab.join(" ")}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Hook: React.FC<{ params?: Record<string, string>; accent: string }> = ({ params, accent }) => {
  const frame = useCurrentFrame();
  const { height } = useVideoConfig();
  const z = interpolateEased(frame, 0, 24, 0.6, 1, "power3.out");
  const pulse = 1 + Math.sin(frame * 0.4) * 0.04;
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <SpaceBackdrop />
      <div style={{ transform: `scale(${z * pulse})`, fontSize: height * 0.34, fontWeight: 900,
                    color: accent, textShadow: `0 0 60px ${accent}99` }}>{P(params, "mark", "?")}</div>
    </AbsoluteFill>
  );
};

const GlobeScene: React.FC<{ params?: Record<string, string> }> = ({ params }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const die = P(params, "die") === "1" ? eased(frame, 34, 20, "power2.in") : 0;
  const alive = 1 - die;
  const cx = width / 2, cy = 600;
  return (
    <AbsoluteFill>
      <SpaceBackdrop danger={die} />
      <Svg>
        {alive > 0.4 ? <PingRings cx={cx} cy={cy} colour={C.accent} max={260} /> : null}
        <Globe cx={cx} cy={cy} r={150} spin={0.4} alive={alive} />
        {[0, 120, 240].map((a, i) => {
          const rad = (a + frame * 1.2) * Math.PI / 180;
          return <Satellite key={i} x={cx + Math.cos(rad) * 250} y={cy + Math.sin(rad) * 250 * 0.8} s={1.1} on={alive} rot={a} />;
        })}
        {die > 0.3 ? <text x={cx} y={cy + 12} textAnchor="middle" fontSize={90} fontWeight={900} fill={C.danger} opacity={die}>⚠</text> : null}
      </Svg>
    </AbsoluteFill>
  );
};

const Vehicle: React.FC<{ params?: Record<string, string> }> = ({ params }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const kind = P(params, "kind", "plane");
  const glyph = P(params, "emoji", kind === "ship" ? "🚢" : "✈️");
  const travel = interpolateEased(frame, 0, 60, 0.1, 0.9, "power1.inOut");
  const wob = Math.sin(frame * 0.5) * (eased(frame, 22, 20) * 60);
  const x = width * travel, y = 600 + wob;
  return (
    <AbsoluteFill>
      <SpaceBackdrop danger={eased(frame, 24, 18) * 0.5} />
      <Svg>
        <path d={`M ${width * 0.08} 600 Q ${width * 0.5} 560, ${width * 0.92} 600`} fill="none"
              stroke={C.cyan} strokeOpacity={0.35} strokeWidth={3} strokeDasharray="4 12" />
        <path d={`M ${width * 0.08} 640 q ${width * 0.2} 40, ${width * 0.4} 0 t ${width * 0.4} ${wob}`}
              fill="none" stroke={C.danger} strokeOpacity={eased(frame, 22, 18) * 0.7} strokeWidth={3} />
      </Svg>
      <div style={{ position: "absolute", left: x - 40, top: y - 40, fontSize: 80, transform: `rotate(${wob * 0.3}deg)` }}>{glyph}</div>
    </AbsoluteFill>
  );
};

const Where: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const drop = interpolateEased(frame, 4, 24, -300, 0, "bounce.out");
  return (
    <AbsoluteFill>
      <SpaceBackdrop />
      <Svg>
        <Globe cx={width / 2} cy={640} r={130} spin={0.3} alive={1} />
        <PingRings cx={width / 2} cy={520 + drop} startFrame={22} colour={accent} max={180} />
      </Svg>
      <div style={{ position: "absolute", left: width / 2 - 45, top: 470 + drop }}>
        <svg width="90" height="130" viewBox="-45 -45 90 130"><Pin x={0} y={-30} s={1.4} colour={accent} q /></svg>
      </div>
    </AbsoluteFill>
  );
};

const ClockScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const grow = eased(frame, 2, 16, "back.out(1.4)");
  return (
    <AbsoluteFill>
      <SpaceBackdrop />
      <Svg><g transform={`translate(${width / 2},620) scale(${grow}) translate(${-width / 2},-620)`}>
        <Clock cx={width / 2} cy={620} r={140} startFrame={0} />
      </g></Svg>
    </AbsoluteFill>
  );
};

const BeamScene: React.FC<{ params?: Record<string, string>; accent: string }> = ({ params, accent }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const reveal = P(params, "reveal") === "1";
  const satX = width / 2, satY = 380, phX = width / 2, phY = 760;
  return (
    <AbsoluteFill>
      <SpaceBackdrop />
      <Svg>
        {[0, 1].map((i) => {
          const rad = (i * 180 + frame * 1.1) * Math.PI / 180;
          return <Satellite key={i} x={satX + Math.cos(rad) * 150} y={satY + Math.sin(rad) * 50} s={1.2} on={1} rot={i * 40} />;
        })}
        <Beam x1={phX} y1={phY - 130} x2={satX} y2={satY + 30} startFrame={6} colour={reveal ? accent : C.cyan} reverse={reveal} />
        {reveal ? <Clock cx={satX} cy={satY} r={54} startFrame={8} /> : null}
      </Svg>
      <Phone x={phX} y={phY} s={1.0}>
        <text y={-6} textAnchor="middle" fontSize={40}>{reveal ? "🕐" : P(params, "emoji", "📍")}</text>
      </Phone>
    </AbsoluteFill>
  );
};

function renderScene(scene: string, params: Record<string, string> | undefined, accent: string): React.ReactNode {
  switch (scene) {
    case "keyword": return <Keyword params={params} accent={accent} />;
    case "list": return <ListScene params={params} accent={accent} />;
    case "hook": return <Hook params={params} accent={accent} />;
    case "globe": return <GlobeScene params={params} />;
    case "vehicle": return <Vehicle params={params} />;
    case "where": return <Where accent={accent} />;
    case "clock": return <ClockScene />;
    case "beam": return <BeamScene params={params} accent={accent} />;
    default: return <Statement accent={accent} />;
  }
}

/* ------------------------------------------------------------- composition */
export const Short: React.FC<ShortProps> = ({ audio, segments, accent, brand, fps }) => {
  const total = segments.length ? segments[segments.length - 1] : null;
  const { durationInFrames } = useVideoConfig();
  const f = (s: number) => Math.round(s * fps);
  return (
    <AbsoluteFill style={{ backgroundColor: C.bg0 }}>
      {segments.map((seg, i) => {
        const start = i === 0 ? 0 : f(seg.start);
        const end = i === segments.length - 1 ? durationInFrames : f(segments[i + 1].start);
        return (
          <Sequence key={i} from={start} durationInFrames={Math.max(1, end - start)}>
            {renderScene(seg.scene, seg.params, accent)}
          </Sequence>
        );
      })}
      {segments.map((seg, i) => {
        const start = Math.max(0, f(seg.start) - 4);
        const end = i === segments.length - 1 ? durationInFrames : f(segments[i + 1].start);
        return (
          <Sequence key={`c${i}`} from={start} durationInFrames={Math.max(1, end - start)}>
            <Caption text={seg.text} emphasis={seg.emphasis} accent={accent} />
          </Sequence>
        );
      })}
      {brand ? (
        <div style={{ position: "absolute", top: 70, width: "100%", textAlign: "center",
                      fontFamily: `${SERIF}, serif`, fontWeight: 700, letterSpacing: "0.18em",
                      color: "rgba(255,255,255,0.5)", fontSize: 30 }}>{brand}</div>
      ) : null}
      {audio ? <Audio src={staticFile(audio)} /> : null}
    </AbsoluteFill>
  );
};

export const DEFAULT_SHORT: ShortProps = {
  audio: "",
  accent: "#E0A65C",
  brand: "THE QUIET STORY",
  fps: 30,
  durationInFrames: 150,
  segments: [
    { start: 0.2, scene: "keyword", emphasis: "Short", text: "यह एक sample Short है", params: { emoji: "✨" } },
    { start: 2.5, scene: "hook", text: "स्क्रिप्ट दो, animation पाओ" },
  ],
};
