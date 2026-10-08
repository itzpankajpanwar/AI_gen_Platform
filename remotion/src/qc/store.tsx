import React from "react";
import { AbsoluteFill } from "remotion";
import type { SceneProps } from "../lib/types";
import { eased, interpolateEased, num, str } from "../lib/anim";
import { C, DISPLAY, SANS, T, TRACK, mono, pipes, clamp01, lerp } from "./theme";
import { Hold, Kicker, Num, Panel, Plate, Row, Rule, useT } from "./parts";

/* =====================================================================
   PICK ROUTE — drawn over the real top-down plate of the store floor.
   The bins sit on actual rack rows in that photograph, and the two paths
   are measured, so the 94 m → 67 m saving on screen is the saving the
   geometry actually produces.
   ===================================================================== */
type XY = { x: number; y: number };
const DOOR: XY = { x: 150, y: 1000 };
const BINS: Record<string, XY> = {
  A12: { x: 1500, y: 900 },   // chiller, far corner
  C04: { x: 450, y: 230 },    // top-left rack
  B17: { x: 900, y: 700 },    // centre rack
  D02: { x: 1450, y: 240 },   // top-right rack
};
const ITEM_OF: Record<string, string> = { A12: "MILK", C04: "CHIPS", B17: "SHAMPOO", D02: "DRINK" };

const walk = (order: string[]): XY[] => [DOOR, ...order.map((b) => BINS[b]), DOOR];
const len = (p: XY[]) => p.reduce((a, q, i) => i ? a + Math.hypot(q.x - p[i-1].x, q.y - p[i-1].y) : 0, 0);

const Dots: React.FC<{ bins: string[]; lit: string[]; delay?: number }> = ({ bins, lit, delay = 0 }) => {
  const { frame } = useT();
  return <g>{bins.map((b, i) => {
    const p = BINS[b]; const on = lit.includes(b);
    const a = eased(frame, delay + i * 5, 16, "power2.out");
    return (
      <g key={b} opacity={a}>
        <circle cx={p.x} cy={p.y} r={30} fill="none" stroke={on ? C.system : C.textFaint}
          strokeWidth={2} opacity={on ? 0.9 : 0.5} />
        <circle cx={p.x} cy={p.y} r={6} fill={on ? C.system : C.textFaint} />
        <text x={p.x + 42} y={p.y - 8} fill={on ? C.system : C.textDim}
          style={{ ...mono, fontSize: 25, fontWeight: 600, letterSpacing: "0.06em" }}>{b}</text>
        <text x={p.x + 42} y={p.y + 20} fill={C.textFaint}
          style={{ ...mono, fontSize: 17, letterSpacing: TRACK }}>{ITEM_OF[b]}</text>
      </g>
    );
  })}</g>;
};

const Walk: React.FC<{ order: string[]; p: number; colour: string; w?: number; dash?: boolean }> =
({ order, p, colour, w = 4, dash }) => {
  const pts = walk(order);
  const d = pts.map((q, i) => `${i ? "L" : "M"}${q.x},${q.y}`).join(" ");
  const L = len(pts) * 1.2;
  return <path d={d} fill="none" stroke={colour} strokeWidth={w} strokeLinejoin="round"
    strokeLinecap="round" strokeDasharray={dash ? "10 12" : `${L}`}
    strokeDashoffset={dash ? 0 : L * (1 - clamp01(p))} opacity={dash ? 0.5 : 1} />;
};

export const PickRoute: React.FC<SceneProps> = ({ image, params }) => {
  const mode = str(params, "mode", "targets");
  const { frame, dur, H } = useT();
  const bins = pipes(params.bins);
  const order = bins.length === 4 ? bins : ["A12", "C04", "B17", "D02"];
  const p = eased(frame, 10, Math.max(20, dur - 22), "power2.inOut");

  return (
    <Hold>
      <Plate image={image} dim={0.68} zoom={1.04} />
      <AbsoluteFill>
        <svg width="100%" height="100%" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">
          {/* the door/packing anchor, present in every mode */}
          <g opacity={eased(frame, 2, 14)}>
            <rect x={DOOR.x - 26} y={DOOR.y - 14} width={52} height={28} fill="none"
              stroke={C.human} strokeWidth={2} />
            <text x={DOOR.x - 26} y={DOOR.y - 26} fill={C.human}
              style={{ ...mono, fontSize: 16, letterSpacing: TRACK }}>PACK</text>
          </g>

          {mode === "targets" && <Dots bins={order} lit={order} delay={8} />}

          {mode === "naive" && <>
            <Walk order={["A12", "C04", "B17", "D02"]} p={p} colour={C.bad} />
            <Dots bins={order} lit={[]} delay={2} />
          </>}

          {mode === "solve" && <>
            {/* every pair considered, then discarded — the search, not the answer */}
            {Object.keys(BINS).flatMap((a, i) =>
              Object.keys(BINS).slice(i + 1).map((b) => {
                const k = eased(frame, 6 + i * 4, 30, "power1.out");
                return <line key={a + b} x1={BINS[a].x} y1={BINS[a].y} x2={BINS[b].x} y2={BINS[b].y}
                  stroke={C.systemDim} strokeWidth={1.2}
                  opacity={k * 0.5 * (1 - eased(frame, dur * 0.55, dur * 0.4, "power2.in"))} />;
              }))}
            <Dots bins={order} lit={[]} delay={2} />
          </>}

          {mode === "optimal" && <>
            <Walk order={["A12", "C04", "B17", "D02"]} p={1} colour={C.textFaint} w={2} dash />
            <Walk order={order} p={p} colour={C.system} />
            <Dots bins={order} lit={order} delay={4} />
            {order.map((b, i) => {
              const q = BINS[b]; const a = eased(frame, 14 + i * 9, 16, "power3.out");
              return <g key={b} opacity={a}>
                <circle cx={q.x - 44} cy={q.y - 34} r={16} fill={C.system} />
                <text x={q.x - 44} y={q.y - 27} textAnchor="middle" fill={C.ink}
                  style={{ ...mono, fontSize: 19, fontWeight: 700 }}>{i + 1}</text>
              </g>;
            })}
          </>}

          {mode === "repeat" && <>
            {Array.from({ length: 9 }).map((_, i) => {
              const a = eased(frame, i * 5, 26, "power2.out") *
                        (1 - eased(frame, 20 + i * 5, 30, "power2.in"));
              const shuffled = [...order].sort(() => (i % 2 ? 1 : -1));
              return <g key={i} opacity={a * 0.3}>
                <Walk order={shuffled} p={1} colour={C.system} w={2} />
              </g>;
            })}
            <Walk order={order} p={1} colour={C.system} w={3.5} />
            <Dots bins={order} lit={order} delay={0} />
          </>}
        </svg>
      </AbsoluteFill>

      {(mode === "naive" || mode === "optimal") && (
        <div style={{ position: "absolute", right: "6%", top: "12%", textAlign: "right" }}>
          <Kicker delay={12} colour={mode === "optimal" ? C.system : C.bad}>{str(params, "label", "")}</Kicker>
          <Num value={str(params, "dist", "")} size={T.big} delay={16}
            colour={mode === "optimal" ? C.system : C.text} style={{ marginTop: 6 }} />
          <div style={{ marginTop: 10 }}>
            <Kicker delay={22} size={T.micro}>WALKING DISTANCE</Kicker>
          </div>
        </div>
      )}
      {mode === "repeat" && (
        <div style={{ position: "absolute", left: "6%", bottom: "12%" }}>
          <Kicker delay={10}>SOLVED PER ORDER</Kicker>
          <Num to={2000} suffix=" ×/day" size={T.big} delay={14} colour={C.system} />
        </div>
      )}
    </Hold>
  );
};

/* =====================================================================
   STORE CUTAWAY — the walls come off, then the floor is named.
   ===================================================================== */
export const StoreCutaway: React.FC<SceneProps> = ({ image, params }) => {
  const mode = str(params, "mode", "reveal");
  const { frame, dur, H } = useT();
  const k = eased(frame, 6, Math.max(24, dur - 20), "power3.inOut");

  const ZONES = [
    { x: 10, y: 6, w: 80, h: 17, label: "INBOUND", sub: "stock arrives at night" },
    { x: 14, y: 26, w: 72, h: 46, label: "PICKING AISLES", sub: "2,000–6,000 SKUs" },
    { x: 10, y: 76, w: 40, h: 17, label: "PACKING", sub: "scan · bag · seal · label" },
    { x: 56, y: 76, w: 34, h: 17, label: "DISPATCH", sub: "riders waiting outside" },
  ];

  return (
    <Hold>
      <Plate image={image} dim={mode === "zones" ? 0.66 : 0.4} zoom={1.05} />
      {mode === "reveal" && (
        <AbsoluteFill>
          {/* a hard wipe that uncovers the interior, like a wall lifting away */}
          <AbsoluteFill style={{ background: C.ink, clipPath: `inset(0 0 0 ${k * 100}%)` }} />
          <svg width="100%" height="100%" viewBox="0 0 1920 1080" style={{ position: "absolute" }}>
            <line x1={k * 1920} y1={0} x2={k * 1920} y2={1080} stroke={C.system}
              strokeWidth={2} opacity={k > 0.01 && k < 0.99 ? 0.85 : 0} />
          </svg>
          <div style={{ position: "absolute", left: "6%", bottom: "12%" }}>
            <Kicker delay={Math.round(dur * 0.45)}>SECTION THROUGH</Kicker>
          </div>
        </AbsoluteFill>
      )}
      {mode === "zones" && (
        <AbsoluteFill>
          <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
            {ZONES.map((z, i) => {
              const a = eased(frame, 8 + i * 10, 20, "power3.out");
              return <rect key={i} x={z.x} y={z.y} width={z.w * a} height={z.h} fill={C.system}
                fillOpacity={0.05} stroke={C.system} strokeOpacity={0.55} strokeWidth={0.12}
                vectorEffect="non-scaling-stroke" />;
            })}
          </svg>
          {ZONES.map((z, i) => (
            <div key={i} style={{ position: "absolute", left: `${z.x + 1.6}%`, top: `${z.y + 1.6}%` }}>
              <Kicker delay={12 + i * 10} colour={C.system} size={T.micro}>{z.label}</Kicker>
              <div style={{ ...mono, fontSize: T.micro * H * 0.95, color: C.textDim, marginTop: 3,
                opacity: eased(frame, 16 + i * 10, 18) }}>{z.sub}</div>
            </div>
          ))}
        </AbsoluteFill>
      )}
    </Hold>
  );
};

/* =====================================================================
   INVENTORY SYNC — the physical shelf and its digital record, side by
   side, moving together. The whole chapter's argument is this layout.
   ===================================================================== */
export const InventorySync: React.FC<SceneProps> = ({ image, params }) => {
  const mode = str(params, "mode", "twin");
  const { frame, dur, H } = useT();
  const items = pipes(params.items), bins = pipes(params.bins);

  const Split: React.FC<{ children: React.ReactNode; right: React.ReactNode }> =
    ({ children, right }) => {
      const k = eased(frame, 4, 24, "power3.out");
      return (
        <AbsoluteFill style={{ flexDirection: "row" }}>
          <div style={{ width: "50%", position: "relative" }}>{children}</div>
          <div style={{ width: 1, background: C.line, opacity: k }} />
          <div style={{ width: "50%", padding: "0 5%", display: "flex", flexDirection: "column",
            justifyContent: "center", opacity: k }}>{right}</div>
        </AbsoluteFill>
      );
    };

  if (mode === "field") {
    return (
      <Hold>
        <Plate image={image} dim={0.55} zoom={1.06} />
        <AbsoluteFill>
          <svg width="100%" height="100%" viewBox="0 0 1920 1080">
            {Array.from({ length: 54 }).map((_, i) => {
              const x = 120 + (i % 9) * 200, y = 150 + Math.floor(i / 9) * 150;
              const a = eased(frame, 4 + i * 1.2, 16, "power2.out");
              return <g key={i} opacity={a * 0.65}>
                <rect x={x} y={y} width={13} height={13} fill="none" stroke={C.system} strokeWidth={1.2} />
              </g>;
            })}
          </svg>
          <div style={{ position: "absolute", left: "6%", bottom: "12%" }}>
            <Kicker delay={28}>EVERY UNIT HAS A RECORD</Kicker>
          </div>
        </AbsoluteFill>
      </Hold>
    );
  }

  if (mode === "locate") {
    return (
      <Hold>
        <Plate image={image} dim={0.6} />
        <AbsoluteFill style={{ padding: "0 7%", justifyContent: "center" }}>
          {items.map((it, i) => (
            <div key={it} style={{ display: "flex", justifyContent: "space-between",
              alignItems: "baseline", borderBottom: `1px solid ${C.lineSoft}`, padding: "16px 0",
              opacity: eased(frame, 8 + i * 11, 18, "power3.out"),
              transform: `translateX(${(1 - eased(frame, 8 + i * 11, 18, "power3.out")) * -18}px)` }}>
              <span style={{ ...mono, fontSize: T.body * H, color: C.text, letterSpacing: TRACK }}>{it}</span>
              <span style={{ ...mono, fontSize: T.body * H, color: C.system, fontWeight: 600 }}>{bins[i]}</span>
            </div>
          ))}
        </AbsoluteFill>
      </Hold>
    );
  }

  if (mode === "drift") {
    const flash = Math.sin(frame * 0.45) > 0 ? 1 : 0.45;
    return (
      <Hold>
        <Plate image={image} dim={0.72} />
        <Split right={
          <>
            <Kicker colour={C.bad}>DIGITAL RECORD</Kicker>
            <Num value={str(params, "digital", "2")} size={T.hero} colour={C.bad}
              delay={10} style={{ opacity: flash }} />
            <Kicker delay={18} size={T.micro}>{str(params, "sku", "")} · {str(params, "bin", "")}</Kicker>
          </>
        }>
          <AbsoluteFill style={{ justifyContent: "center", paddingLeft: "10%" }}>
            <Kicker>ON THE SHELF</Kicker>
            <Num value={str(params, "shelf", "0")} size={T.hero} colour={C.text} delay={6} />
            <div style={{ marginTop: 26 }}>
              <Kicker delay={26} colour={C.bad} size={T.micro}>THE SYSTEM IS NOW LYING</Kicker>
            </div>
          </AbsoluteFill>
        </Split>
      </Hold>
    );
  }

  // twin / decrement
  const from = Number(str(params, "from", "14")), to = Number(str(params, "to", "13"));
  const tick = mode === "decrement" ? eased(frame, Math.round(dur * 0.38), 10, "power4.out") : 0;
  const shown = mode === "decrement" ? (tick > 0.5 ? to : from) : Number(str(params, "qty", "14"));
  return (
    <Hold>
      <Plate image={image} dim={0.7} />
      <Split right={
        <>
          <Kicker colour={C.system}>DIGITAL RECORD</Kicker>
          <div style={{ marginTop: 16 }}>
            <Row k="SKU" v={str(params, "sku", "")} delay={8} />
            <Row k="LOCATION" v={str(params, "bin", "")} delay={14} />
            <Row k="ON HAND" v={String(shown)} delay={20} accent />
          </div>
          {mode === "decrement" && (
            <div style={{ marginTop: 22, display: "flex", alignItems: "center", gap: 14,
              opacity: eased(frame, Math.round(dur * 0.38), 12) }}>
              <Num value={String(from)} size={T.big} colour={C.textFaint} />
              <div style={{ ...mono, fontSize: T.body * H, color: C.textFaint }}>→</div>
              <Num value={String(to)} size={T.big} colour={C.system} />
            </div>
          )}
        </>
      }>
        <AbsoluteFill style={{ justifyContent: "center", paddingLeft: "10%" }}>
          <Kicker>ON THE SHELF</Kicker>
          <Num value={String(shown)} size={T.hero} colour={C.text} delay={6} />
          <Kicker delay={14} size={T.micro}>UNITS PRESENT</Kicker>
        </AbsoluteFill>
      </Split>
    </Hold>
  );
};

/* =====================================================================
   SCAN CONFIRM — verification, deliberately undramatic. No green ticks.
   ===================================================================== */
export const ScanConfirm: React.FC<SceneProps> = ({ image, params }) => {
  const mode = str(params, "mode", "scanning");
  const { frame, dur, H } = useT();
  const items = pipes(params.items);

  return (
    <Hold>
      <Plate image={image} dim={0.68} zoom={1.05} />
      <AbsoluteFill style={{ padding: "0 7%", justifyContent: "center" }}>
        {mode === "scanning" && (
          <div style={{ maxWidth: "62%" }}>
            <Kicker>VERIFYING AGAINST THE ORDER</Kicker>
            <div style={{ marginTop: 20 }}>
              {items.map((it, i) => {
                const at = 10 + i * Math.max(8, (dur - 26) / Math.max(1, items.length));
                const done = eased(frame, at, 9, "power3.out");
                return (
                  <div key={it} style={{ display: "flex", alignItems: "center", gap: 20,
                    padding: "13px 0", borderBottom: `1px solid ${C.lineSoft}`,
                    opacity: 0.35 + done * 0.65 }}>
                    <div style={{ width: 11, height: 11, border: `1px solid ${done > 0.5 ? C.system : C.textFaint}`,
                      background: done > 0.5 ? C.system : "transparent" }} />
                    <span style={{ ...mono, fontSize: T.body * H, color: done > 0.5 ? C.text : C.textFaint,
                      letterSpacing: "0.04em" }}>{it}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
        {mode === "verified" && (
          <div>
            <Kicker>ITEMS VERIFIED</Kicker>
            <div style={{ display: "flex", alignItems: "baseline", gap: 14, marginTop: 8 }}>
              <Num value={str(params, "count", "4")} size={T.hero} colour={C.system} delay={6} />
              <Num value={`/ ${str(params, "of", "4")}`} size={T.big} colour={C.textFaint} delay={12} />
            </div>
            <Rule w={240} delay={18} colour={C.system} style={{ marginTop: 16 }} />
          </div>
        )}
        {mode === "status" && (
          <div>
            <Kicker>ORDER STATUS</Kicker>
            <div style={{ display: "flex", alignItems: "baseline", gap: 24, marginTop: 10 }}>
              <div style={{ ...mono, fontSize: T.big * H, color: C.textFaint,
                textDecoration: "line-through", opacity: 1 - eased(frame, 14, 16) * 0.55 }}>
                {str(params, "from", "")}</div>
              <div style={{ ...mono, fontSize: T.body * H, color: C.textFaint }}>→</div>
              <Num value={str(params, "to", "")} size={T.big} colour={C.system} delay={16} />
            </div>
          </div>
        )}
      </AbsoluteFill>
    </Hold>
  );
};
