import React, { useMemo } from "react";
import { AbsoluteFill } from "remotion";
import type { SceneProps } from "../lib/types";
import { eased, interpolateEased, num, str } from "../lib/anim";
import { C, DISPLAY, SANS, T, TRACK, mono, pipes, rng, lerp, clamp01 } from "./theme";
import { city, iso, pointAt, polyLen, W, type Pt } from "./city";
import { Ground, Hold, Kicker, Num, useT } from "./parts";

/* ------------------------------------------------------------------ camera */
/** Each mode frames the city differently; the move is always eased, never linear. */
type Cam = { cx: number; cy: number; s: number };
const camFor = (mode: string, ct: ReturnType<typeof city>): [Cam, Cam] => {
  const cust = iso(ct.customer.x, ct.customer.y);
  const st = iso(ct.stores[3].p.x, ct.stores[3].p.y);
  const mid = { cx: (cust.x + st.x) / 2, cy: (cust.y + st.y) / 2 };
  // Scales are set so the model always bleeds past at least two edges of the
  // frame: a city you can see the corner of reads as a tabletop toy.
  const wide: Cam = { cx: 0, cy: 500, s: 1.42 };
  const city_: Cam = { cx: mid.cx * 0.6, cy: 480, s: 1.72 };
  const near: Cam = { cx: mid.cx, cy: mid.cy, s: 2.45 };
  switch (mode) {
    case "stores":        return [{ ...wide, s: 1.34 }, city_];
    case "candidates":    return [city_, { ...city_, s: 1.86 }];
    case "evaluate":
    case "reject":        return [{ ...city_, s: 1.86 }, { ...city_, s: 1.94 }];
    case "select":        return [{ ...city_, s: 1.94 }, { cx: st.x, cy: st.y, s: 2.3 }];
    case "node_zoom":     return [{ cx: st.x, cy: st.y, s: 2.3 }, { cx: st.x, cy: st.y, s: 4.2 }];
    case "riders":        return [{ cx: st.x, cy: st.y, s: 3.0 }, near];
    case "rider_eval":
    case "batch":
    case "rider_select":  return [near, { ...near, s: 2.6 }];
    case "route":
    case "traffic":
    case "reroute":       return [{ ...near, s: 2.3 }, { ...near, s: 2.1 }];
    case "single_thread": return [{ ...near, s: 2.1 }, { ...city_, s: 1.6 }];
    case "pullback":      return [{ ...city_, s: 1.6 }, { ...wide, s: 1.2 }];
    case "flows":         return [{ ...wide, s: 1.2 }, { ...wide, s: 1.3 }];
    case "demand_curve":  return [{ ...wide, s: 1.05 }, { ...wide, s: 1.12 }];
    case "one_spark":     return [{ ...wide, s: 1.25 }, { ...wide, s: 1.44 }];
    default:              return [{ ...wide, s: 1.36 }, { ...wide, s: 1.5 }];  // network
  }
};

/* ------------------------------------------------------------- city render */
const Buildings: React.FC = () => {
  const ct = city();
  return useMemo(() => (
    <g>
      {ct.buildings.map((b, i) => {
        const x0 = b.x, x1 = b.x + b.w, y0 = b.y, y1 = b.y + b.d, h = b.h;
        const P = (x: number, y: number, z: number) => { const p = iso(x, y, z); return `${p.x},${p.y}`; };
        const lit = b.k > 0.86;                       // a few windows are on
        const top = lit ? "#232A33" : `rgb(${22 + b.k * 9},${27 + b.k * 10},${34 + b.k * 12})`;
        const right = `rgb(${14 + b.k * 5},${18 + b.k * 6},${24 + b.k * 7})`;
        const left = `rgb(${9 + b.k * 4},${12 + b.k * 4},${17 + b.k * 5})`;
        return (
          <g key={i} shapeRendering="geometricPrecision">
            <polygon points={`${P(x1,y0,h)} ${P(x1,y1,h)} ${P(x1,y1,0)} ${P(x1,y0,0)}`} fill={right} />
            <polygon points={`${P(x0,y1,h)} ${P(x1,y1,h)} ${P(x1,y1,0)} ${P(x0,y1,0)}`} fill={left} />
            <polygon points={`${P(x0,y0,h)} ${P(x1,y0,h)} ${P(x1,y1,h)} ${P(x0,y1,h)}`} fill={top} />
            {lit ? <polygon points={`${P(x0,y0,h)} ${P(x1,y0,h)} ${P(x1,y1,h)} ${P(x0,y1,h)}`}
                     fill={C.human} opacity={0.1} /> : null}
          </g>
        );
      })}
    </g>
  ), [ct]);
};

const Roads: React.FC = () => {
  const ct = city();
  return useMemo(() => (
    <g>
      {ct.roads.map((r, i) => {
        const hw = r.w / 2;
        const vert = r.x1 === r.x2;
        const c = vert
          ? [[r.x1 - hw, 0], [r.x1 + hw, 0], [r.x1 + hw, W], [r.x1 - hw, W]]
          : [[0, r.y1 - hw], [0, r.y1 + hw], [W, r.y1 + hw], [W, r.y1 - hw]];
        const pts = c.map(([x, y]) => { const p = iso(x, y, 0); return `${p.x},${p.y}`; }).join(" ");
        return <polygon key={i} points={pts} fill={r.arterial ? "#2A323D" : "#1E242D"} />;
      })}
    </g>
  ), [ct]);
};

/* --------------------------------------------------------------- overlays */
const dot = (p: Pt, h = 0) => iso(p.x, p.y, h);

const Pin: React.FC<{ p: Pt; colour: string; r?: number; a?: number; ring?: number; lift?: number }> =
({ p, colour, r = 7, a = 1, ring = 0, lift = 34 }) => {
  const g = dot(p, lift), b = dot(p, 0);
  return (
    <g opacity={a}>
      <line x1={b.x} y1={b.y} x2={g.x} y2={g.y} stroke={colour} strokeWidth={1.4} opacity={0.55} />
      <ellipse cx={b.x} cy={b.y} rx={r * 0.9} ry={r * 0.45} fill={colour} opacity={0.22} />
      <circle cx={g.x} cy={g.y} r={r} fill={colour} />
      <circle cx={g.x} cy={g.y} r={r * 0.42} fill={C.ink} />
      {ring > 0 ? <circle cx={g.x} cy={g.y} r={r + ring * 26} fill="none" stroke={colour}
        strokeWidth={1.6} opacity={(1 - ring) * 0.7} /> : null}
    </g>
  );
};

/** A circle on the ground plane, drawn as a true projected polygon. */
const Radius: React.FC<{ p: Pt; r: number; a?: number; colour?: string }> =
({ p, r, a = 1, colour = C.system }) => {
  const pts = Array.from({ length: 48 }, (_, i) => {
    const th = (i / 48) * Math.PI * 2;
    const q = iso(p.x + Math.cos(th) * r, p.y + Math.sin(th) * r, 0);
    return `${q.x},${q.y}`;
  }).join(" ");
  return <polygon points={pts} fill={colour} fillOpacity={0.045 * a} stroke={colour}
    strokeOpacity={0.3 * a} strokeWidth={1.2} strokeDasharray="5 7" />;
};

/** A path that draws itself along the street grid. */
const Path: React.FC<{ pts: Pt[]; p: number; colour?: string; w?: number; a?: number; dash?: boolean }> =
({ pts, p, colour = C.system, w = 3, a = 1, dash }) => {
  const d = pts.map((q, i) => { const s = iso(q.x, q.y, 0); return `${i ? "L" : "M"}${s.x},${s.y}`; }).join(" ");
  const L = polyLen(pts) * 1.35;
  return <path d={d} fill="none" stroke={colour} strokeWidth={w} strokeLinecap="round"
    strokeLinejoin="round" opacity={a} strokeDasharray={dash ? "6 8" : `${L}`}
    strokeDashoffset={dash ? 0 : L * (1 - clamp01(p))} />;
};

/** The order itself, visible as one travelling point of light. */
const Spark: React.FC<{ pts: Pt[]; p: number; colour?: string; r?: number }> =
({ pts, p, colour = C.system, r = 6 }) => {
  if (p <= 0 || p > 1) return null;
  const q = pointAt(pts, p); const s = iso(q.x, q.y, 0);
  return (<g>
    <circle cx={s.x} cy={s.y} r={r * 2.6} fill={colour} opacity={0.14} />
    <circle cx={s.x} cy={s.y} r={r} fill={colour} />
  </g>);
};

/** A data panel pinned beside a point, with a leader line. */
const Callout: React.FC<{ p: Pt; title: string; value: string; delay?: number;
  state?: "on" | "off" | "win"; dx?: number; dy?: number }> =
({ p, title, value, delay = 0, state = "on", dx = 54, dy = -86 }) => {
  const { frame, H } = useT();
  const a = eased(frame, delay, 16, "power3.out");
  const g = dot(p, 34);
  const col = state === "win" ? C.system : state === "off" ? C.textFaint : C.text;
  return (
    <g opacity={state === "off" ? a * 0.45 : a}>
      <line x1={g.x} y1={g.y} x2={g.x + dx} y2={g.y + dy} stroke={col} strokeWidth={1} opacity={0.5} />
      <circle cx={g.x + dx} cy={g.y + dy} r={2} fill={col} />
      <foreignObject x={g.x + dx + 8} y={g.y + dy - 30} width={300} height={70}>
        <div style={{ ...mono, color: col }}>
          <div style={{ fontSize: 15, letterSpacing: TRACK, textTransform: "uppercase",
            color: state === "win" ? C.system : C.textFaint }}>{title}</div>
          <div style={{ fontFamily: `${DISPLAY}, sans-serif`, fontSize: 30, fontWeight: 600,
            marginTop: 2, textDecoration: state === "off" ? "line-through" : "none" }}>{value}</div>
        </div>
      </foreignObject>
    </g>
  );
};

/* ------------------------------------------------------------ the template */
export const CityMap: React.FC<SceneProps> = ({ params }) => {
  const mode = str(params, "mode", "network");
  const { frame, dur, t, H } = useT();
  const ct = city();
  const [c0, c1] = camFor(mode, ct);
  const e = eased(frame, 0, dur, "power2.inOut");
  const cam = { cx: lerp(c0.cx, c1.cx, e), cy: lerp(c0.cy, c1.cy, e), s: lerp(c0.s, c1.s, e) };

  // Candidate order matches the pipe-separated values in the script:
  // [0] wins on ETA, [1] is the busy one, [2] is nearest but short of stock.
  const CAND = [ct.stores[3], ct.stores[1], ct.stores[2]];
  const WIN = ct.stores[3];
  const RIDER_CAND = [ct.riders[6], ct.riders[3], ct.riders[4]];
  const WINR = ct.riders[6];
  const mainRoute = useMemo(() => ct.route(WIN.p, ct.customer), [ct]);
  const altRoute = useMemo(() => ct.route(WIN.p, ct.customer, true), [ct]);

  /** Background traffic + order flow for the network modes. */
  const net = useMemo(() => {
    const r = rng(77);
    const stores: Pt[] = Array.from({ length: 46 }, () => ({ x: r() * W, y: r() * W }));
    const threads = Array.from({ length: 64 }, (_, i) => {
      const s = stores[Math.floor(r() * stores.length)];
      const d = { x: s.x + (r() - 0.5) * 230, y: s.y + (r() - 0.5) * 230 };
      return { pts: ct.route(s, d), off: r(), spd: 0.45 + r() * 0.5, k: i };
    });
    return { stores, threads };
  }, [ct]);

  const values = pipes(params.values);
  const counters = pipes(params.counters);
  const intensity = num(params, "intensity", 1);
  const fade = num(params, "fade", 0);

  const show = (m: string[]) => m.includes(mode);

  return (
    <Hold>
      <Ground />
      <AbsoluteFill style={{ opacity: fade ? 1 - eased(frame, dur * 0.55, dur * 0.45, "power2.in") * 0.55 : 1 }}>
        <svg width="100%" height="100%" viewBox="-960 -60 1920 1080"
             style={{ display: "block" }} preserveAspectRatio="xMidYMid slice">
          <g transform={`translate(${-cam.cx * cam.s} ${480 - cam.cy * cam.s}) scale(${cam.s})`}>
            <Roads />
            <Buildings />

            {/* ---- service radius: ch3 opening */}
            {show(["stores"]) && ct.stores.map((s, i) => (
              <g key={s.id} opacity={eased(frame, 10 + i * 5, 22, "power2.out")}>
                <Radius p={s.p} r={125} />
              </g>
            ))}
            {show(["stores", "candidates", "evaluate", "reject", "select", "node_zoom",
                   "single_thread"]) && ct.stores.map((s, i) => {
              const isCand = CAND.some((c) => c.id === s.id);
              const isWin = s.id === WIN.id;
              let a = eased(frame, 6 + i * 4, 18, "power2.out");
              if (show(["evaluate", "reject"]) && !isCand) a *= 0.3;
              if (show(["select", "node_zoom", "single_thread"]) && !isWin)
                a *= 1 - eased(frame, 6, 24, "power2.out") * 0.78;
              return <Pin key={s.id} p={s.p} colour={isWin && show(["select", "node_zoom", "single_thread"])
                ? C.system : C.textDim} a={a} r={isWin ? 8 : 6}
                ring={isWin && mode === "select" ? eased(frame, 18, 36, "power2.out") : 0} />;
            })}

            {/* ---- the customer, present from ch3 onward */}
            {show(["candidates", "evaluate", "reject", "select", "riders", "rider_eval", "batch",
                   "rider_select", "route", "traffic", "reroute", "single_thread", "one_spark"]) &&
              <Pin p={ct.customer} colour={C.human} a={eased(frame, 4, 18, "power2.out")} r={7}
                   ring={mode === "candidates" ? eased(frame, 6, 30, "power2.out") : 0} />}

            {/* ---- candidate links, ch3 */}
            {show(["candidates", "evaluate", "reject"]) && CAND.map((s, i) => (
              <Path key={s.id} pts={[ct.customer, s.p]} p={eased(frame, 12 + i * 7, 26, "power2.inOut")}
                colour={C.systemDim} w={1.6} dash
                a={mode === "reject" && s.id !== WIN.id
                  ? 1 - eased(frame, 16, 24, "power2.out") * 0.8 : 0.75} />
            ))}
            {show(["evaluate"]) && CAND.map((s, i) => (
              <Callout key={s.id} p={s.p} title={str(params, "metric", "")} value={values[i] ?? ""}
                delay={10 + i * 8} state={i === 0 ? "win" : "on"}
                dx={i === 1 ? -250 : 54} dy={[-92, -74, -150][i]} />
            ))}
            {show(["reject"]) && CAND.map((s, i) => (
              <Callout key={s.id} p={s.p} title={["SELECTED", "FULL", "NO STOCK"][i]}
                value={["9 min", "19 queued", "3 of 4"][i]} delay={8 + i * 7}
                state={i === 0 ? "win" : "off"}
                dx={i === 1 ? -250 : 54} dy={[-92, -74, -150][i]} />
            ))}
            {show(["select"]) &&
              <Callout p={WIN.p} title="ASSIGNED" value={str(params, "label", "STORE 04")} delay={14} state="win" />}

            {/* ---- riders, ch8 */}
            {show(["riders", "rider_eval", "batch", "rider_select"]) && ct.riders.map((rd, i) => {
              const isCand = RIDER_CAND.some((c) => c.id === rd.id);
              const isWin = rd.id === WINR.id;
              let a = eased(frame, 4 + i * 2.5, 16, "power2.out");
              if (show(["rider_eval"]) && !isCand) a *= 0.26;
              if (mode === "rider_select" && !isWin) a *= 1 - eased(frame, 8, 22, "power2.out") * 0.8;
              return <g key={rd.id} opacity={a}>
                <Pin p={rd.p} colour={isWin && mode === "rider_select" ? C.human : C.textFaint}
                     r={isWin && mode === "rider_select" ? 7 : 4.5} lift={20}
                     ring={isWin && mode === "rider_select" ? eased(frame, 16, 34, "power2.out") : 0} />
              </g>;
            })}
            {show(["rider_eval"]) && RIDER_CAND.map((rd, i) => (
              <Callout key={rd.id} p={rd.p} title={str(params, "metric", "")} value={values[i] ?? ""}
                delay={10 + i * 8} state={i === 0 ? "win" : "on"}
                dx={i === 1 ? -250 : 54} dy={[-86, -70, -142][i]} />
            ))}
            {show(["batch"]) && (() => {
              const second = { x: ct.customer.x + 120, y: ct.customer.y - 80 };
              const r1 = ct.route(WINR.p, ct.customer);
              const r2 = ct.route(ct.customer, second);
              return <g>
                <Pin p={second} colour={C.human} a={eased(frame, 10, 18)} r={6} />
                <Path pts={r1} p={eased(frame, 8, 30, "power2.inOut")} colour={C.human} w={2.4} />
                <Path pts={r2} p={eased(frame, 26, 30, "power2.inOut")} colour={C.human} w={2.4} a={0.75} />
              </g>;
            })()}
            {show(["rider_select"]) &&
              <Callout p={WINR.p} title="DISPATCH" value={str(params, "label", "RIDER 07")}
                delay={16} state="win" dy={-70} />}

            {/* ---- the road, ch9 */}
            {show(["route", "traffic", "reroute", "single_thread"]) && (() => {
              const rerouting = mode === "reroute";
              const pOld = rerouting ? 1 - eased(frame, 6, 20, "power2.in") : eased(frame, 6, 40, "power2.inOut");
              const pNew = rerouting ? eased(frame, 14, 38, "power2.inOut") : 0;
              const live = rerouting ? altRoute : mainRoute;
              const prog = rerouting ? pNew : pOld;
              return <g>
                <Pin p={WIN.p} colour={C.system} r={7} />
                {mode === "traffic" && ct.roads.filter((r) => r.arterial).map((r, i) => {
                  const vert = r.x1 === r.x2; const hw = r.w / 2 + 2;
                  const c = vert ? [[r.x1 - hw, 0], [r.x1 + hw, 0], [r.x1 + hw, W], [r.x1 - hw, W]]
                                 : [[0, r.y1 - hw], [0, r.y1 + hw], [W, r.y1 + hw], [W, r.y1 - hw]];
                  const pts = c.map(([x, y]) => { const p = iso(x, y, 0); return `${p.x},${p.y}`; }).join(" ");
                  return <polygon key={i} points={pts} fill={i === 1 ? C.bad : C.human}
                    opacity={eased(frame, 8 + i * 6, 24, "power2.out") * (i === 1 ? 0.5 : 0.22)} />;
                })}
                {rerouting ? <Path pts={mainRoute} p={1} colour={C.bad} w={2.4} a={pOld * 0.5} dash /> : null}
                <Path pts={live} p={prog} colour={C.system} w={3.4} />
                <Spark pts={live} p={prog} />
              </g>;
            })()}

            {/* ---- one order's thread, ch11 opening */}
            {show(["single_thread", "one_spark"]) && (() => {
              const p = eased(frame, 4, dur * 0.72, "power1.inOut");
              return <g><Path pts={mainRoute} p={p} colour={C.system} w={3} />
                <Spark pts={mainRoute} p={p} r={7} /></g>;
            })()}

            {/* ---- THE NETWORK: the film's biggest reveal */}
            {show(["pullback", "network", "flows", "one_spark", "demand_curve"]) && (() => {
              const grow = eased(frame, 2, Math.max(18, dur * 0.55), "power2.out");
              const nStores = Math.round(net.stores.length * (mode === "pullback" ? grow * 0.5 : grow));
              const live = mode === "pullback" ? Math.round(14 * grow)
                : Math.round(net.threads.length * Math.min(1, intensity / 3) * grow);
              return <g>
                {net.stores.slice(0, nStores).map((s, i) => (
                  <circle key={i} cx={iso(s.x, s.y, 0).x} cy={iso(s.x, s.y, 0).y} r={3.4}
                    fill={C.system} opacity={0.5} />
                ))}
                {net.threads.slice(0, live).map((th, i) => {
                  const phase = (t * th.spd * 1.5 + th.off) % 1;
                  return <g key={i}>
                    <Path pts={th.pts} p={1} colour={C.systemDim} w={1.2} a={0.3} />
                    <Spark pts={th.pts} p={phase} colour={i % 7 === 0 ? C.human : C.system} r={4.2} />
                  </g>;
                })}
                {mode === "one_spark" ? <Spark pts={mainRoute} p={(t * 0.9) % 1} r={9} /> : null}
              </g>;
            })()}
          </g>
        </svg>
      </AbsoluteFill>

      {/* ------------------------------------------------- 2D HUD over the map */}
      {show(["route", "reroute"]) && (
        <div style={{ position: "absolute", left: "6%", bottom: "11%", display: "flex", gap: 54 }}>
          {[["DISTANCE", str(params, "dist", "")], ["ETA", str(params, "eta", "")]].map(([k, v], i) => (
            <div key={k}>
              <Kicker delay={10 + i * 6} size={T.micro}>{k}</Kicker>
              <Num value={v} size={T.num} delay={12 + i * 6}
                colour={mode === "reroute" && k === "ETA" ? C.system : C.text} />
            </div>
          ))}
          {mode === "reroute" ? (
            <div><Kicker delay={24} size={T.micro} colour={C.bad}>REROUTED</Kicker>
              <Num value="congestion ahead" size={T.label * 1.3} delay={26} colour={C.textDim} weight={500} /></div>
          ) : null}
        </div>
      )}

      {counters.length > 0 && (
        <div style={{ position: "absolute", left: "6%", bottom: "10%", display: "flex", gap: 64 }}>
          {counters.map((c, i) => {
            const [k, v] = [c.replace(/\s+[\d,\.]+$/, ""), (c.match(/[\d,\.]+$/) || [""])[0]];
            return <div key={i}>
              <Kicker delay={14 + i * 8} size={T.micro}>{k}</Kicker>
              <Num to={Number(v.replace(/,/g, "")) || 0} size={T.big} delay={16 + i * 8} colour={C.system} />
            </div>;
          })}
        </div>
      )}

      {mode === "flows" && (
        <div style={{ position: "absolute", left: "6%", bottom: "12%" }}>
          {pipes(params.legend).map((l, i) => {
            const [when, what] = l.split("·").map((s) => s.trim());
            return <div key={i} style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 13,
              opacity: eased(frame, 12 + i * 12, 20, "power2.out") }}>
              <div style={{ width: 34, height: 2, background: i === 0 ? C.human : i === 1 ? C.system : C.textDim }} />
              <span style={{ ...mono, fontSize: T.label * H, letterSpacing: TRACK,
                textTransform: "uppercase", color: C.textFaint }}>{when}</span>
              <span style={{ ...mono, fontSize: T.label * H * 1.15, color: C.text }}>{what}</span>
            </div>;
          })}
        </div>
      )}

      {mode === "demand_curve" && (() => {
        const hrs = [6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23];
        const dem = [12,18,26,30,27,34,52,48,33,28,31,42,68,92,100,88,61,34];
        const a = eased(frame, 8, 34, "power3.out");
        const bw = 26, gap = 9, x0 = 150, y0 = 880, hMax = 300;
        return <svg style={{ position: "absolute", inset: 0 }} width="100%" height="100%" viewBox="0 0 1920 1080">
          {dem.map((d, i) => {
            const k = clamp01(a * dem.length - i * 0.55);
            const h = (d / 100) * hMax * k;
            const peak = d >= 88;
            return <rect key={i} x={x0 + i * (bw + gap)} y={y0 - h} width={bw} height={h}
              fill={peak ? C.human : C.systemDim} opacity={peak ? 0.95 : 0.55} />;
          })}
          <line x1={x0 - 14} y1={y0} x2={x0 + dem.length * (bw + gap)} y2={y0} stroke={C.line} strokeWidth={1} />
          <text x={x0 + 12 * (bw + gap)} y={y0 - hMax - 22} fill={C.human}
            style={{ ...mono, fontSize: 21, letterSpacing: TRACK }} opacity={eased(frame, 40, 20)}>
            7–10 PM · PEAK</text>
          <text x={x0 - 14} y={y0 + 34} fill={C.textFaint} style={{ ...mono, fontSize: 17 }}>6 AM</text>
          <text x={x0 + 16 * (bw + gap)} y={y0 + 34} fill={C.textFaint} style={{ ...mono, fontSize: 17 }}>11 PM</text>
        </svg>;
      })()}
    </Hold>
  );
};
