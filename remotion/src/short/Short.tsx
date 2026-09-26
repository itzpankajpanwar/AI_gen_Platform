import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { eased, interpolateEased } from "../lib/anim";
import { SANS, SERIF } from "../lib/useFont";
import { SEGMENTS, TOTAL } from "./segments";
import {
  Beam, C, Clock, Globe, Phone, Pin, PingRings, Satellite, SpaceBackdrop,
} from "./visuals";

const FPS = 30;
const f = (s: number) => Math.round(s * FPS);

/* ------------------------------------------------------------------ captions */
const Caption: React.FC<{ text: string; emphasis?: string }> = ({ text, emphasis }) => {
  const frame = useCurrentFrame();
  const { height } = useVideoConfig();
  const words = text.split(" ");
  const rise = eased(frame, 0, 10, "power3.out");
  const emphWords = new Set((emphasis ?? "").split(" "));
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: height * 0.20 }}>
      <div
        style={{
          maxWidth: "86%",
          textAlign: "center",
          transform: `translateY(${(1 - rise) * 40}px)`,
          opacity: rise,
          display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0.22em 0.44em",
        }}
      >
        {words.map((w, i) => {
          const on = eased(frame, 3 + i * 2.2, 9, "back.out(1.6)");
          const emph = emphWords.has(w.replace(/[।,?…]/g, ""));
          return (
            <span key={i} style={{
              fontFamily: `${SANS}, sans-serif`,
              fontWeight: 800,
              fontSize: height * (emph ? 0.05 : 0.043),
              lineHeight: 1.15,
              color: emph ? C.accent : C.ink,
              opacity: on,
              transform: `translateY(${(1 - on) * 14}px)`,
              display: "inline-block",
              textShadow: "0 3px 20px rgba(0,0,0,0.9), 0 1px 3px rgba(0,0,0,0.9)",
            }}>{w}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* -------------------------------------------------------------------- scenes */
const Center: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { width, height } = useVideoConfig();
  return <svg width={width} height={height} style={{ position: "absolute" }}>{children}</svg>;
};

const Shutdown: React.FC = () => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const die = eased(frame, 34, 20, "power2.in");         // GPS powers down late in the scene
  const alive = 1 - die;
  const cx = width / 2, cy = 620;
  return (
    <AbsoluteFill>
      <SpaceBackdrop danger={die} />
      <Center>
        {alive > 0.4 ? <PingRings cx={cx} cy={cy} colour={C.accent} max={260} /> : null}
        <Globe cx={cx} cy={cy} r={150} spin={0.4} alive={alive} />
        {[0, 120, 240].map((a, i) => {
          const rad = (a + frame * 1.2) * Math.PI / 180;
          return <Satellite key={i} x={cx + Math.cos(rad) * 250} y={cy + Math.sin(rad) * 250 * 0.8}
                            s={1.1} on={alive} rot={a} />;
        })}
        {die > 0.3 ? <text x={cx} y={cy + 12} textAnchor="middle" fontSize={90} fontWeight={900}
                           fill={C.danger} opacity={die} fontFamily={`${SANS},sans-serif`}>⚠</text> : null}
      </Center>
    </AbsoluteFill>
  );
};

const MapsScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const die = eased(frame, 20, 18, "power2.in");
  const cx = width / 2;
  return (
    <AbsoluteFill>
      <SpaceBackdrop danger={die * 0.6} />
      <Center>
        <Phone x={cx} y={560} s={1.15}>
          <rect x={-58} y={-120} width={116} height={240} rx={12} fill={die > 0.5 ? "#241214" : "#123047"} />
          {die < 0.6 ? <PingRings cx={0} cy={-10} colour={C.cyan} max={90} /> : null}
          <g opacity={1 - die}><Pin x={0} y={-30} s={0.9} colour={C.accent} /></g>
          {die > 0.4 ? <text x={0} y={0} textAnchor="middle" fontSize={54} fill={C.danger}
                            fontWeight={900} fontFamily={`${SANS},sans-serif`} opacity={die}>✕</text> : null}
        </Phone>
      </Center>
    </AbsoluteFill>
  );
};

const Vehicle: React.FC<{ kind: "plane" | "ship" }> = ({ kind }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const travel = interpolateEased(frame, 0, 60, 0.1, 0.9, "power1.inOut");
  const wob = Math.sin(frame * 0.5) * (eased(frame, 22, 20) * 60); // path goes erratic
  const x = width * travel, y = 600 + wob;
  const glyph = kind === "plane" ? "✈️" : "🚢";
  return (
    <AbsoluteFill>
      <SpaceBackdrop danger={eased(frame, 24, 18) * 0.5} />
      <Center>
        <path d={`M ${width * 0.08} 600 Q ${width * 0.5} ${600 - 40}, ${width * 0.92} 600`}
              fill="none" stroke={C.cyan} strokeOpacity={0.35} strokeWidth={3} strokeDasharray="4 12" />
        <path d={`M ${width * 0.08} 640 q ${width * 0.2} 40, ${width * 0.4} 0 t ${width * 0.4} ${wob}`}
              fill="none" stroke={C.danger} strokeOpacity={eased(frame, 22, 18) * 0.7} strokeWidth={3} />
      </Center>
      <div style={{ position: "absolute", left: x - 40, top: y - 40, fontSize: 80, transform: `rotate(${wob * 0.3}deg)` }}>{glyph}</div>
    </AbsoluteFill>
  );
};

const Systems: React.FC = () => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const icons = ["🏦", "📡", "🖥️", "💳", "🌐", "⚙️"];
  return (
    <AbsoluteFill>
      <SpaceBackdrop danger={eased(frame, 30, 24) * 0.6} />
      <div style={{ position: "absolute", inset: 0, display: "grid", gridTemplateColumns: "repeat(2, 1fr)",
                    alignContent: "center", justifyItems: "center", rowGap: 40, top: 360, height: 620 }}>
        {icons.map((ic, i) => {
          const pop = eased(frame, 4 + i * 4, 12, "back.out(2)");
          const fail = eased(frame, 40 + i * 3, 14);
          return (
            <div key={i} style={{ transform: `scale(${pop})`, position: "relative" }}>
              <div style={{ fontSize: 92, filter: `grayscale(${fail}) brightness(${1 - fail * 0.5})` }}>{ic}</div>
              {fail > 0.4 ? <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center",
                                          fontSize: 70, color: C.danger, fontWeight: 900 }}>✕</div> : null}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Where: React.FC = () => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const drop = interpolateEased(frame, 4, 24, -300, 0, "bounce.out");
  return (
    <AbsoluteFill>
      <SpaceBackdrop />
      <Center>
        <Globe cx={width / 2} cy={640} r={130} spin={0.3} alive={1} />
        <PingRings cx={width / 2} cy={520 + drop} startFrame={22} colour={C.accent} max={180} />
      </Center>
      <div style={{ position: "absolute", left: width / 2 - 45, top: 470 + drop, fontSize: 0 }}>
        <svg width="90" height="90" viewBox="-45 -45 90 130"><Pin x={0} y={-30} s={1.4} colour={C.accent} q /></svg>
      </div>
    </AbsoluteFill>
  );
};

const TimeScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const grow = eased(frame, 2, 16, "back.out(1.4)");
  return (
    <AbsoluteFill>
      <SpaceBackdrop />
      <Center>
        <g transform={`scale(${grow})`} transform-origin="center">
          <Clock cx={width / 2} cy={620} r={140} startFrame={0} />
        </g>
      </Center>
    </AbsoluteFill>
  );
};

const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const z = interpolateEased(frame, 0, 24, 0.6, 1, "power3.out");
  const pulse = 1 + Math.sin(frame * 0.4) * 0.04;
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <SpaceBackdrop danger={0} />
      <div style={{ transform: `scale(${z * pulse})`, fontSize: height * 0.34, fontWeight: 900,
                    color: C.accent, textShadow: "0 0 60px rgba(224,166,92,0.6)" }}>?</div>
    </AbsoluteFill>
  );
};

const AskReveal: React.FC<{ reveal?: boolean }> = ({ reveal = false }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const satX = width / 2, satY = 380, phX = width / 2, phY = 760;
  return (
    <AbsoluteFill>
      <SpaceBackdrop />
      <Center>
        {[0, 1].map((i) => {
          const rad = (i * 180 + frame * 1.1) * Math.PI / 180;
          return <Satellite key={i} x={satX + Math.cos(rad) * 150} y={satY + Math.sin(rad) * 50}
                            s={1.2} on={1} rot={i * 40} />;
        })}
        <Beam x1={phX} y1={phY - 130} x2={satX} y2={satY + 30} startFrame={6}
              colour={reveal ? C.accent : C.cyan} reverse={reveal} />
        {reveal ? <Clock cx={satX} cy={satY} r={54} startFrame={8} /> : null}
      </Center>
      <Phone x={phX} y={phY} s={1.0}>
        {reveal ? <text y={-6} textAnchor="middle" fontSize={40}>🕐</text>
                : <text y={-6} textAnchor="middle" fontSize={40}>📍</text>}
      </Phone>
    </AbsoluteFill>
  );
};

const SCENES: Record<string, React.ReactNode> = {
  shutdown: <Shutdown />, maps: <MapsScene />, planes: <Vehicle kind="plane" />,
  ships: <Vehicle kind="ship" />, systems: <Systems />, where: <Where />,
  time: <TimeScene />, hook: <Hook />, ask: <AskReveal />, reveal: <AskReveal reveal />,
};

/* ------------------------------------------------------------- composition */
export const GpsShort: React.FC = () => {
  const { width } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: C.bg0 }}>
      {SEGMENTS.map((seg, i) => {
        const start = i === 0 ? 0 : f(seg.start);
        const end = i === SEGMENTS.length - 1 ? f(TOTAL) : f(SEGMENTS[i + 1].start);
        return (
          <Sequence key={i} from={start} durationInFrames={end - start}>
            {SCENES[seg.scene]}
          </Sequence>
        );
      })}
      {/* captions ride above the visuals, appearing when each line is spoken */}
      {SEGMENTS.map((seg, i) => {
        const start = f(seg.start) - 4;
        const end = i === SEGMENTS.length - 1 ? f(TOTAL) : f(SEGMENTS[i + 1].start);
        return (
          <Sequence key={`c${i}`} from={Math.max(0, start)} durationInFrames={end - Math.max(0, start)}>
            <Caption text={seg.text} emphasis={seg.emphasis} />
          </Sequence>
        );
      })}
      {/* small brand mark, top */}
      <div style={{ position: "absolute", top: 70, width: "100%", textAlign: "center",
                    fontFamily: `${SERIF}, serif`, fontWeight: 700, letterSpacing: "0.18em",
                    color: "rgba(255,255,255,0.5)", fontSize: 30 }}>THE QUIET STORY</div>
      <Audio src={staticFile("gps.mp3")} />
    </AbsoluteFill>
  );
};
