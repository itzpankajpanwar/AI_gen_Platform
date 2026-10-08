import React from "react";
import { AbsoluteFill } from "remotion";
import type { SceneProps } from "../lib/types";
import { eased, interpolateEased, num, str } from "../lib/anim";
import { C, DISPLAY, SANS, T, TRACK, mono, pipes, clamp01, lerp } from "./theme";
import { Ground, Hold, Kicker, Num, Plate, Rule, useT } from "./parts";

/* =====================================================================
   SYSTEM DIAGRAM — the backend as a space you travel through, not a
   flowchart you read. Nodes recede along a diagonal with real
   perspective scaling, and the order stays visible as one bright point.
   ===================================================================== */
export const SystemDiagram: React.FC<SceneProps> = ({ params }) => {
  const mode = str(params, "mode", "chain");
  const { frame, dur, t, H } = useT();
  const nodes = pipes(params.nodes);
  const fields = pipes(params.fields);
  const steps = pipes(params.steps);

  /** Node i placed along a receding diagonal: further = smaller, dimmer, higher. */
  const place = (i: number, n: number) => {
    const u = n <= 1 ? 0 : i / (n - 1);
    return { x: 180 + u * 1560, y: 760 - u * 420, s: 1 - u * 0.42, dim: 1 - u * 0.5 };
  };

  if (mode === "enter") {
    // Travelling into the machine: concentric frames rushing past the camera.
    return (
      <Hold>
        <Ground />
        <AbsoluteFill>
          <svg width="100%" height="100%" viewBox="0 0 1920 1080">
            {Array.from({ length: 16 }).map((_, i) => {
              const k = ((t * 1.25 + i / 16) % 1);
              const s = 0.04 + k * k * 2.1;
              const w = 1920 * s, h = 1080 * s;
              return <rect key={i} x={960 - w / 2} y={540 - h / 2} width={w} height={h}
                fill="none" stroke={C.system} strokeWidth={1.1}
                opacity={Math.min(k * 2.2, (1 - k) * 2.4) * 0.5} />;
            })}
            <circle cx={960} cy={540} r={5 + eased(frame, 0, dur, "power2.in") * 10} fill={C.system} />
          </svg>
          <div style={{ position: "absolute", left: "6%", bottom: "12%" }}>
            <Kicker delay={14}>THE ORDER · 412 BYTES</Kicker>
          </div>
        </AbsoluteFill>
      </Hold>
    );
  }

  if (mode === "payload") {
    return (
      <Hold>
        <Ground />
        <AbsoluteFill style={{ justifyContent: "center", padding: "0 10%" }}>
          <Kicker>THE MESSAGE</Kicker>
          <div style={{ marginTop: 26 }}>
            {fields.map((f, i) => {
              const a = eased(frame, 10 + i * 13, 20, "power3.out");
              return (
                <div key={f} style={{ display: "flex", alignItems: "center", gap: 26,
                  padding: "19px 0", borderBottom: `1px solid ${C.lineSoft}`, opacity: a,
                  transform: `translateX(${(1 - a) * -22}px)` }}>
                  <span style={{ ...mono, fontSize: T.micro * H, color: C.textFaint,
                    letterSpacing: TRACK, width: 44 }}>{String(i + 1).padStart(2, "0")}</span>
                  <span style={{ ...mono, fontSize: T.body * H * 1.15, color: C.text,
                    letterSpacing: "0.03em" }}>{f}</span>
                </div>
              );
            })}
          </div>
          <div style={{ marginTop: 22 }}>
            <Kicker delay={52} size={T.micro}>WHO · WHAT · WHERE</Kicker>
          </div>
        </AbsoluteFill>
      </Hold>
    );
  }

  if (mode === "engine" || mode === "question") {
    const q = str(params, "q", "");
    return (
      <Hold>
        <Ground />
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <svg width="100%" height="100%" viewBox="0 0 1920 1080" style={{ position: "absolute" }}>
            {Array.from({ length: 7 }).map((_, i) => {
              const a = eased(frame, 4 + i * 4, 26, "power2.out");
              const y = 220 + i * 110;
              return <line key={i} x1={0} y1={y} x2={960 * a} y2={540}
                stroke={C.systemDim} strokeWidth={1} opacity={0.4 * a} />;
            })}
            <circle cx={960} cy={540} r={interpolateEased(frame, 10, 30, 0, 96, "power3.out")}
              fill="none" stroke={C.system} strokeWidth={1.6} />
            <circle cx={960} cy={540} r={7} fill={C.system} />
          </svg>
          {mode === "question" ? (
            <div style={{ position: "relative", textAlign: "center" }}>
              <div style={{ fontFamily: `${DISPLAY}, sans-serif`, fontSize: T.title * H,
                color: C.text, fontWeight: 600, letterSpacing: "-0.01em",
                opacity: eased(frame, 18, 22, "power3.out") }}>{q}</div>
            </div>
          ) : (
            <div style={{ position: "relative", marginTop: 180 }}>
              <Kicker delay={22} colour={C.system}>ORDER ENGINE</Kicker>
            </div>
          )}
        </AbsoluteFill>
      </Hold>
    );
  }

  if (mode === "checks") {
    return (
      <Hold>
        <Ground />
        <AbsoluteFill style={{ justifyContent: "center", padding: "0 12%" }}>
          {steps.map((s, i) => {
            const at = 8 + i * Math.max(10, (dur - 30) / Math.max(1, steps.length));
            const a = eased(frame, at, 14, "power3.out");
            return (
              <div key={s} style={{ display: "flex", alignItems: "center", gap: 22,
                padding: "17px 0", opacity: 0.3 + a * 0.7 }}>
                <div style={{ width: 9, height: 9, background: a > 0.6 ? C.system : C.textFaint }} />
                <span style={{ ...mono, fontSize: T.body * H, letterSpacing: TRACK,
                  color: a > 0.6 ? C.text : C.textFaint }}>{s}</span>
              </div>
            );
          })}
        </AbsoluteFill>
      </Hold>
    );
  }

  // chain / chain_count — the seven links, in depth
  const counting = mode === "chain_count";
  const SECS = ["", "0.2 s", "1.4 s", "8 s", "1 m 40 s", "30 s", "40 s", "7 m"];
  return (
    <Hold>
      <Ground />
      <AbsoluteFill>
        <svg width="100%" height="100%" viewBox="0 0 1920 1080">
          {nodes.slice(0, -1).map((_, i) => {
            const a = place(i, nodes.length), b = place(i + 1, nodes.length);
            const p = eased(frame, 8 + i * 7, 20, "power2.inOut");
            return <line key={i} x1={a.x} y1={a.y} x2={lerp(a.x, b.x, p)} y2={lerp(a.y, b.y, p)}
              stroke={C.systemDim} strokeWidth={1.4} opacity={0.75} />;
          })}
          {nodes.map((n, i) => {
            const q = place(i, nodes.length);
            const a = eased(frame, 6 + i * 7, 16, "power3.out");
            return <g key={n} opacity={a * q.dim}>
              <circle cx={q.x} cy={q.y} r={9 * q.s} fill={C.ink} stroke={C.system} strokeWidth={1.8} />
              <circle cx={q.x} cy={q.y} r={3.4 * q.s} fill={C.system} />
            </g>;
          })}
          {/* the order itself, still visibly the same thing, moving down the chain */}
          {(() => {
            const p = clamp01((t - 0.18) / 0.72) * (nodes.length - 1);
            const i = Math.min(nodes.length - 2, Math.floor(p)), k = p - i;
            const a = place(i, nodes.length), b = place(i + 1, nodes.length);
            const x = lerp(a.x, b.x, k), y = lerp(a.y, b.y, k), s = lerp(a.s, b.s, k);
            return p >= 0 ? <g>
              <circle cx={x} cy={y} r={20 * s} fill={C.human} opacity={0.16} />
              <circle cx={x} cy={y} r={6.5 * s} fill={C.human} />
            </g> : null;
          })()}
        </svg>
        {nodes.map((n, i) => {
          const q = place(i, nodes.length);
          const a = eased(frame, 10 + i * 7, 16, "power3.out");
          return (
            <div key={n} style={{ position: "absolute", left: `${(q.x / 1920) * 100}%`,
              top: `${(q.y / 1080) * 100}%`, transform: "translate(-50%, 22px)", textAlign: "center",
              opacity: a * q.dim }}>
              <div style={{ ...mono, fontSize: T.micro * H * q.s * 1.15, letterSpacing: TRACK,
                color: C.textDim, whiteSpace: "nowrap" }}>{n}</div>
              {counting ? (
                <div style={{ ...mono, fontSize: T.micro * H * q.s * 1.3, color: C.system,
                  marginTop: 5, opacity: eased(frame, 26 + i * 6, 16) }}>{SECS[i] ?? ""}</div>
              ) : null}
            </div>
          );
        })}
      </AbsoluteFill>
    </Hold>
  );
};

/* =====================================================================
   SANKEY — the order taken apart. A real flow diagram: the ₹350 bar
   splits, the margin stream is spent down, and the running total is
   allowed to go negative on screen.
   ===================================================================== */
export const Sankey: React.FC<SceneProps> = ({ params }) => {
  const mode = str(params, "mode", "order");
  const { frame, dur, H } = useT();
  const total = num(params, "total", 350);
  const cogs = num(params, "cogs", 300);
  const margin = num(params, "margin", 50);

  // PX is sized so the full ₹64 of spending — the ₹50 available plus the
  // ₹14 it runs over by — still fits inside the frame with its labels.
  const PX = 1180, X0 = 240, Y0 = 430, BAR = 104;
  const a = (d: number, len = 22) => eased(frame, d, len, "power3.out");

  /** The four cost lines, in the order the narration spends them. */
  const SPEND: [string, number][] = [
    ["LAST-MILE DELIVERY", 32], ["PACKAGING", 7],
    ["STORE LABOUR", 14], ["RENT · POWER · TECH", 11],
  ];
  const label = str(params, "label", "");
  const value = num(params, "value", 0);
  const running = num(params, "running", 0);

  /**
   * Once the supplier's share has left, the film stops drawing ₹350 and
   * ₹50 at the same scale — at that scale the whole cost story happens in a
   * 170px sliver. From `costs_begin` on, the ₹50 IS the frame, so each cost
   * line is legible and the overspend can visibly run off the end.
   */
  const zoomed = ["costs_begin", "cost", "negative"].includes(mode);
  const perRupee = zoomed ? PX / margin : PX / total;

  const Caption: React.FC<{ x: number; w: number; top: string; right: string;
    colour?: string; delay?: number; below?: boolean }> =
  ({ x, w, top, right, colour = C.textDim, delay = 0, below }) => (
    <>
      <text x={x} y={below ? Y0 + BAR + 36 : Y0 - 18} fill={colour}
        style={{ ...mono, fontSize: 19, letterSpacing: TRACK }} opacity={a(delay)}>{top}</text>
      <text x={x + w} y={below ? Y0 + BAR + 36 : Y0 - 18} textAnchor="end" fill={C.text}
        style={{ ...mono, fontSize: 25, fontWeight: 600 }} opacity={a(delay)}>{right}</text>
    </>
  );

  return (
    <Hold>
      <Ground />
      <AbsoluteFill>
        <svg width="100%" height="100%" viewBox="0 0 1920 1080">
          {mode === "order" && (<>
            <rect x={X0} y={Y0} width={PX * a(6, 30)} height={BAR} fill={C.systemDim} />
            <Caption x={X0} w={PX} top="ONE ORDER" right={`₹${total}`} delay={12} />
          </>)}

          {["cogs", "margin"].includes(mode) && (() => {
            const split = a(4, 26);
            const wc = cogs * perRupee, wm = margin * perRupee, gap = 30 * split;
            const leaving = mode === "margin" ? a(10, 30) : 0;
            return <g>
              <g opacity={1 - leaving * 0.78} transform={`translate(${-leaving * 130} 0)`}>
                <rect x={X0} y={Y0} width={wc} height={BAR} fill={C.systemDim} opacity={0.5} />
                <Caption x={X0} w={wc} top="GOODS · PAID TO SUPPLIERS" right={`₹${cogs}`} delay={10} />
              </g>
              <rect x={X0 + wc + gap} y={Y0} width={wm} height={BAR} fill={C.system} />
              {mode === "margin" ? (
                <text x={X0 + wc + gap + wm / 2} y={Y0 + BAR + 40} textAnchor="middle" fill={C.system}
                  style={{ ...mono, fontSize: 21, letterSpacing: TRACK }} opacity={a(16)}>
                  ₹{margin} · ALL OF IT</text>
              ) : null}
            </g>;
          })()}

          {zoomed && (() => {
            const grow = mode === "costs_begin" ? a(4, 26) : 1;
            const upto = SPEND.findIndex(([k]) => k === label);
            const shown = mode === "negative" ? SPEND.length : (upto < 0 ? 0 : upto + 1);
            let acc = 0;
            return <g>
              {/* what there was to spend */}
              <rect x={X0} y={Y0} width={PX * grow} height={BAR} fill={C.system}
                opacity={shown ? 0.16 : 1} />
              {SPEND.slice(0, shown).map(([k, v], i) => {
                const w = v * perRupee, bx = X0 + acc; acc += w;
                const live = i === shown - 1 && mode !== "negative";
                const g = live ? a(4, 20) : 1;
                return <g key={k}>
                  <rect x={bx} y={Y0} width={w * g} height={BAR} fill={C.human}
                    opacity={live ? 0.95 : 0.62} />
                  <line x1={bx} y1={Y0} x2={bx} y2={Y0 + BAR} stroke={C.ink} strokeWidth={2} />
                  {live || mode === "negative" ? (
                    <text x={bx + 10} y={Y0 + BAR + 32} fill={live ? C.human : C.textFaint}
                      style={{ ...mono, fontSize: 16, letterSpacing: "0.08em" }}
                      opacity={live ? a(10) : 0.8}>{k}</text>
                  ) : null}
                </g>;
              })}
              {/* the overspend, past the end of what there was */}
              {acc > PX ? <rect x={X0 + PX} y={Y0} width={acc - PX} height={BAR}
                fill={C.bad} opacity={0.9} /> : null}
              <line x1={X0 + PX} y1={Y0 - 34} x2={X0 + PX} y2={Y0 + BAR + 56}
                stroke={C.text} strokeWidth={1.5} strokeDasharray="5 6" opacity={0.65} />
              <text x={X0 + PX - 12} y={Y0 - 44} textAnchor="end" fill={C.textDim}
                style={{ ...mono, fontSize: 18, letterSpacing: TRACK }} opacity={a(8)}>
                ₹{margin} AVAILABLE</text>
            </g>;
          })()}
        </svg>

        {["cost", "negative"].includes(mode) && (
          <div style={{ position: "absolute", right: "6%", top: "14%", textAlign: "right" }}>
            {mode !== "negative" && (<>
              <Kicker delay={8}>{label}</Kicker>
              <Num value={`−₹${value}`} size={T.big} colour={C.human} delay={12} />
            </>)}
            <div style={{ marginTop: mode === "negative" ? 0 : 26 }}>
              <Kicker delay={18} size={T.micro}>{mode === "negative" ? "LEFT ON ONE ORDER" : "RUNNING"}</Kicker>
              <Num value={`${running < 0 ? "−" : ""}₹${Math.abs(running)}`}
                size={mode === "negative" ? T.hero : T.big}
                colour={running < 0 ? C.bad : C.system} delay={20} />
            </div>
          </div>
        )}

        {["order", "cogs", "margin", "costs_begin"].includes(mode) && (
          <div style={{ position: "absolute", left: "6%", top: "14%" }}>
            <Kicker delay={6} size={T.micro}>REPRESENTATIVE ILLUSTRATION · NOT ONE COMPANY</Kicker>
          </div>
        )}

        {mode === "levers_intro" && (
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
            <div style={{ display: "flex", gap: 110 }}>
              {["BASKET SIZE", "ORDER DENSITY", "ADVERTISING"].map((l, i) => (
                <div key={l} style={{ textAlign: "center",
                  opacity: eased(frame, 10 + i * 12, 20, "power3.out") }}>
                  <Num value={`0${i + 1}`} size={T.big} colour={C.system} delay={10 + i * 12} />
                  <div style={{ marginTop: 12 }}><Kicker delay={14 + i * 12} size={T.micro}>{l}</Kicker></div>
                </div>
              ))}
            </div>
          </AbsoluteFill>
        )}

        {mode === "lever" && (
          <AbsoluteFill style={{ justifyContent: "center", padding: "0 12%" }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 26 }}>
              <Num value={`0${str(params, "n", "1")}`} size={T.title} colour={C.system} delay={4} />
              <div style={{ fontFamily: `${DISPLAY}, sans-serif`, fontSize: T.title * H * 0.74,
                color: C.text, fontWeight: 600, opacity: eased(frame, 8, 18, "power3.out") }}>
                {str(params, "label", "")}</div>
            </div>
            <Rule w={620} delay={14} colour={C.line} style={{ marginTop: 28 }} />
            <div style={{ marginTop: 26 }}>
              <div style={{ ...mono, fontSize: T.body * H, color: C.text,
                opacity: eased(frame, 20, 18) }}>{str(params, "a", "")}</div>
              <div style={{ ...mono, fontSize: T.body * H * 0.84, color: C.textDim, marginTop: 12,
                opacity: eased(frame, 30, 18) }}>{str(params, "b", "")}</div>
            </div>
          </AbsoluteFill>
        )}
      </AbsoluteFill>
    </Hold>
  );
};

/* =====================================================================
   COMPARE FLOW — the old way and the new way, held in the same frame so
   the inversion is spatial rather than stated.
   ===================================================================== */
export const CompareFlow: React.FC<SceneProps> = ({ params }) => {
  const mode = str(params, "mode", "old");
  const { frame, dur, H } = useT();
  const nodes = pipes(params.nodes);

  const Chain: React.FC<{ items: string[]; y: number; colour: string; delay?: number;
    accent?: string }> = ({ items, y, colour, delay = 0, accent }) => (
    <g>
      {items.map((n, i) => {
        const x = 170 + (i * 1580) / Math.max(1, items.length - 1);
        const a = eased(frame, delay + i * 6, 16, "power3.out");
        const nx = 170 + ((i + 1) * 1580) / Math.max(1, items.length - 1);
        return <g key={n + i} opacity={a}>
          {i < items.length - 1 ? (
            <line x1={x + 16} y1={y} x2={lerp(x + 16, nx - 16, eased(frame, delay + i * 6 + 5, 14))}
              y2={y} stroke={colour} strokeWidth={1.4} opacity={0.6} />
          ) : null}
          <circle cx={x} cy={y} r={7} fill={C.ink} stroke={accent ?? colour} strokeWidth={1.8} />
          <text x={x} y={y + 38} textAnchor="middle" fill={C.textDim}
            style={{ ...mono, fontSize: 17, letterSpacing: TRACK }}>{n}</text>
        </g>;
      })}
    </g>
  );

  const OLD = ["CUSTOMER", "TRAVEL", "STORE", "SEARCH", "CHECKOUT", "TRAVEL", "HOME"];
  const NEW = ["CUSTOMER", "DARK STORE", "PICK", "RIDER", "HOME"];

  return (
    <Hold>
      <Ground />
      <AbsoluteFill>
        <svg width="100%" height="100%" viewBox="0 0 1920 1080">
          {["old", "old_summary", "flip", "new", "tradeoff_intro", "tradeoff", "conclusion"].includes(mode) && (
            <Chain items={nodes.length && mode === "old" ? nodes : OLD} y={mode === "old" || mode === "old_summary" ? 540 : 360}
              colour={C.humanDim} accent={C.human} delay={6} />
          )}
          {["flip", "new", "tradeoff_intro", "tradeoff", "conclusion"].includes(mode) && (
            <Chain items={nodes.length && mode === "new" ? nodes : NEW} y={760}
              colour={C.systemDim} accent={C.system} delay={mode === "flip" ? 24 : 6} />
          )}
        </svg>

        {(mode === "old" || mode === "flip" || mode === "new") && (
          <>
            <div style={{ position: "absolute", left: "6%",
              top: mode === "old" ? "40%" : "26%", transform: "translateY(-50%)" }}>
              <Kicker colour={C.human} delay={2}>THE OLD WAY</Kicker>
            </div>
            {mode !== "old" && (
              <div style={{ position: "absolute", left: "6%", top: "63%" }}>
                <Kicker colour={C.system} delay={mode === "flip" ? 26 : 2}>QUICK COMMERCE</Kicker>
              </div>
            )}
          </>
        )}

        {mode === "old_summary" && (
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end", paddingBottom: "18%" }}>
            <Kicker delay={8} colour={C.human} size={T.label * 1.25}>{str(params, "label", "")}</Kicker>
          </AbsoluteFill>
        )}

        {(mode === "tradeoff" || mode === "tradeoff_intro") && (
          <div style={{ position: "absolute", left: "6%", top: "48%", transform: "translateY(-50%)" }}>
            {mode === "tradeoff" ? (
              <>
                <div style={{ display: "flex", alignItems: "baseline", gap: 20 }}>
                  <Num value={`0${str(params, "n", "1")}`} size={T.big} colour={C.bad} delay={4} />
                  <div style={{ fontFamily: `${DISPLAY}, sans-serif`, fontSize: T.big * H * 0.92,
                    color: C.text, fontWeight: 600, opacity: eased(frame, 8, 16, "power3.out") }}>
                    {str(params, "label", "")}</div>
                </div>
                <div style={{ ...mono, fontSize: T.body * H * 0.8, color: C.textDim, marginTop: 12,
                  opacity: eased(frame, 18, 18) }}>{str(params, "sub", "")}</div>
              </>
            ) : <Kicker delay={6} colour={C.bad} size={T.label * 1.3}>WHAT IT COSTS TO DO THIS</Kicker>}
          </div>
        )}

        {mode === "conclusion" && (
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontFamily: `${DISPLAY}, sans-serif`, fontSize: T.title * H,
                color: C.text, fontWeight: 600, letterSpacing: "-0.01em",
                opacity: eased(frame, 8, 22, "power3.out") }}>{str(params, "label", "")}</div>
              <div style={{ marginTop: 22, opacity: eased(frame, 26, 22, "power3.out") }}>
                <Kicker colour={C.system} size={T.label * 1.3}>{str(params, "sub", "")}</Kicker>
              </div>
            </div>
          </AbsoluteFill>
        )}
      </AbsoluteFill>
    </Hold>
  );
};
