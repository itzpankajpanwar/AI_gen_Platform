import React from "react";
import { AbsoluteFill } from "remotion";
import type { SceneProps } from "../lib/types";
import { eased, interpolateEased, num, str } from "../lib/anim";
import { C, DISPLAY, SANS, T, TRACK, mono, pipes, clamp01 } from "./theme";
import { Ground, Hold, Kicker, Num, Plate, Rule, useT } from "./parts";

/* =====================================================================
   PHONE UI — a believable, boring app. Restraint is the point: a real
   quick-commerce app is a list and a button, so that is what this is.
   ===================================================================== */
export const PhoneUI: React.FC<SceneProps> = ({ params }) => {
  const mode = str(params, "mode", "cart");
  const { frame, dur, H } = useT();
  const items = pipes(params.items), prices = pipes(params.prices);
  const PW = 0.252, PH = 0.88;                  // phone size as a fraction of frame
  const w = PW * 1920, h = PH * 1080;

  const press = mode === "button" ? eased(frame, Math.round(dur * 0.56), 7, "power3.out") : 0;
  const rel = mode === "button" ? eased(frame, Math.round(dur * 0.56) + 7, 10, "power2.out") : 0;
  const pushed = press - rel;

  return (
    <Hold>
      <Ground />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: w, height: h, borderRadius: 46, background: "#0A0D12",
          border: `1px solid ${C.line}`, overflow: "hidden", position: "relative",
          boxShadow: "0 60px 140px rgba(0,0,0,0.65)",
          transform: `scale(${1 + eased(frame, 0, dur, "none") * 0.035})` }}>
          {/* status bar */}
          <div style={{ display: "flex", justifyContent: "space-between", padding: "22px 30px 0",
            ...mono, fontSize: 17, color: C.textFaint }}>
            <span>21:46</span><span>▮▮▮</span>
          </div>

          {mode === "confirmed" ? (
            <div style={{ padding: "0 30px", height: "100%", display: "flex", flexDirection: "column",
              justifyContent: "center", alignItems: "flex-start" }}>
              <div style={{ width: 34, height: 34, border: `1.6px solid ${C.system}`,
                borderRadius: 17, opacity: eased(frame, 4, 16, "power3.out") }} />
              <div style={{ ...mono, fontSize: 25, color: C.text, marginTop: 22, letterSpacing: "0.02em",
                opacity: eased(frame, 10, 18) }}>{str(params, "label", "ORDER PLACED")}</div>
              <div style={{ ...mono, fontSize: 18, color: C.textDim, marginTop: 12,
                opacity: eased(frame, 18, 18) }}>Arriving in about 10 minutes</div>
              <div style={{ width: "100%", height: 2, background: C.lineSoft, marginTop: 30 }}>
                <div style={{ width: `${eased(frame, 22, 40, "power2.out") * 100}%`, height: 2,
                  background: C.system }} />
              </div>
            </div>
          ) : (
            <div style={{ padding: "34px 30px 0" }}>
              <div style={{ ...mono, fontSize: 16, letterSpacing: TRACK, color: C.textFaint,
                textTransform: "uppercase" }}>Your order</div>
              <div style={{ marginTop: 20 }}>
                {items.map((it, i) => {
                  const a = eased(frame, 6 + i * 9, 16, "power3.out");
                  return (
                    <div key={it} style={{ display: "flex", justifyContent: "space-between",
                      alignItems: "center", padding: "17px 0",
                      borderBottom: `1px solid ${C.lineSoft}`, opacity: a,
                      transform: `translateY(${(1 - a) * 12}px)` }}>
                      <span style={{ ...mono, fontSize: 19, color: C.text }}>{it}</span>
                      <span style={{ ...mono, fontSize: 19, color: C.textDim }}>₹{prices[i] ?? ""}</span>
                    </div>
                  );
                })}
              </div>
              {str(params, "total", "") ? (
                <div style={{ display: "flex", justifyContent: "space-between", marginTop: 26,
                  opacity: eased(frame, 44, 18) }}>
                  <span style={{ ...mono, fontSize: 17, letterSpacing: TRACK, color: C.textFaint,
                    textTransform: "uppercase" }}>Total</span>
                  <span style={{ fontFamily: `${DISPLAY}, sans-serif`, fontSize: 32, fontWeight: 600,
                    color: C.text }}>₹{str(params, "total", "")}</span>
                </div>
              ) : null}
            </div>
          )}

          {/* A real app puts its promise and its call to action at the bottom of
              the screen. Showing them here fills the device honestly and sets up
              the button the next beat presses. */}
          {mode === "cart" ? (
            <div style={{ position: "absolute", left: 30, right: 30, bottom: 44,
              opacity: eased(frame, 52, 20, "power2.out") }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
                <div style={{ width: 6, height: 6, borderRadius: 3, background: C.system }} />
                <span style={{ ...mono, fontSize: 16, color: C.textDim }}>
                  Delivery in about 10 minutes</span>
              </div>
              <div style={{ height: 70, border: `1px solid ${C.line}`, borderRadius: 10,
                display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ ...mono, fontSize: 21, fontWeight: 650, color: C.textFaint,
                  letterSpacing: "0.1em" }}>PLACE ORDER</span>
              </div>
            </div>
          ) : null}

          {mode === "button" && (
            <div style={{ position: "absolute", left: 30, right: 30, bottom: 46 }}>
              <div style={{ height: 70, background: C.system, borderRadius: 10,
                display: "flex", alignItems: "center", justifyContent: "center",
                transform: `scale(${1 - pushed * 0.035})`, filter: `brightness(${1 - pushed * 0.22})` }}>
                <span style={{ ...mono, fontSize: 21, fontWeight: 650, color: "#06121F",
                  letterSpacing: "0.1em" }}>{str(params, "label", "PLACE ORDER")}</span>
              </div>
            </div>
          )}
        </div>
      </AbsoluteFill>
    </Hold>
  );
};

/* =====================================================================
   CLOCK — the film's one recurring motif. Hero at milestones, a quiet
   corner stamp elsewhere, and a split bar in chapter 10.
   ===================================================================== */
export const Clock: React.FC<SceneProps> = ({ image, params }) => {
  const mode = str(params, "mode", "corner");
  const { frame, dur, H } = useT();
  const value = str(params, "value", "10:00");
  const label = str(params, "label", "");
  const bar = num(params, "bar", -1);

  if (mode === "corner") {
    const a = eased(frame, 6, 18, "power3.out");
    return (
      <Hold>
        <Plate image={image} dim={0.42} zoom={1.05} />
        <div style={{ position: "absolute", right: "6%", top: "10%", textAlign: "right", opacity: a }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, justifyContent: "flex-end" }}>
            <div style={{ width: 7, height: 7, borderRadius: 4, background: C.system,
              opacity: 0.45 + 0.55 * (Math.sin(frame * 0.3) * 0.5 + 0.5) }} />
            <Num value={value} size={T.num} colour={C.text} delay={6} />
          </div>
          <div style={{ marginTop: 4 }}><Kicker delay={12} size={T.micro}>{label}</Kicker></div>
        </div>
      </Hold>
    );
  }

  if (mode === "split") {
    const pct = clamp01(bar / 100);
    const grown = eased(frame, 6, 26, "power3.out") * pct;
    return (
      <Hold>
        <Ground />
        <AbsoluteFill style={{ justifyContent: "center", padding: "0 10%" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <Kicker delay={4}>{label}</Kicker>
            <Num value={value} size={T.title} colour={C.text} delay={4} />
          </div>
          <div style={{ width: "100%", height: 3, background: C.lineSoft, marginTop: 30 }}>
            <div style={{ width: `${grown * 100}%`, height: 3, background: C.system }} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 14 }}>
            <Kicker delay={16} size={T.micro}>ORDER PLACED</Kicker>
            <Kicker delay={16} size={T.micro}>DELIVERED</Kicker>
          </div>
        </AbsoluteFill>
      </Hold>
    );
  }

  // hero
  const a = eased(frame, 4, 24, "power3.out");
  return (
    <Hold>
      {image ? <Plate image={image} dim={0.68} zoom={1.05} /> : <Ground />}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center", opacity: a, transform: `translateY(${(1 - a) * 16}px)` }}>
          <div style={{ fontFamily: `${DISPLAY}, sans-serif`, fontSize: T.hero * H * 1.5,
            fontWeight: 300, color: C.text, letterSpacing: "-0.02em", fontVariantNumeric: "tabular-nums" }}>
            {value}</div>
          <div style={{ marginTop: 18 }}><Kicker delay={16} size={T.label}>{label}</Kicker></div>
        </div>
      </AbsoluteFill>
    </Hold>
  );
};

/* =====================================================================
   CARDS — chapter openers, the film title, and the three small data
   treatments that sit over plates.
   ===================================================================== */
export const ChCard: React.FC<SceneProps> = ({ text, params }) => {
  const { frame, H } = useT();
  const a = eased(frame, 6, 24, "power3.out");
  return (
    <Hold>
      <Ground />
      <AbsoluteFill style={{ justifyContent: "center", padding: "0 11%" }}>
        <Kicker delay={2} colour={C.system}>{str(params, "kicker", "")}</Kicker>
        <Rule w={760} delay={10} dur={26} colour={C.line} style={{ marginTop: 22 }} />
        <div style={{ fontFamily: `${DISPLAY}, sans-serif`, fontSize: T.title * H, fontWeight: 600,
          color: C.text, letterSpacing: "-0.015em", marginTop: 26, opacity: a,
          transform: `translateY(${(1 - a) * 18}px)` }}>{text}</div>
      </AbsoluteFill>
    </Hold>
  );
};

export const TitleCard: React.FC<SceneProps> = ({ text, params }) => {
  const { frame, dur, H } = useT();
  const a = eased(frame, 8, 30, "power3.out");
  return (
    <Hold outF={14}>
      <Ground />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <Kicker delay={2} colour={C.textFaint} size={T.micro}>{str(params, "brand", "")}</Kicker>
          <div style={{ fontFamily: `${DISPLAY}, sans-serif`, fontSize: T.hero * H, fontWeight: 600,
            color: C.text, letterSpacing: "-0.025em", marginTop: 26, opacity: a,
            transform: `scale(${0.985 + a * 0.015})` }}>{text}</div>
          <div style={{ display: "flex", justifyContent: "center", marginTop: 26 }}>
            <Rule w={300} delay={26} dur={28} colour={C.system} />
          </div>
          <div style={{ marginTop: 24, opacity: eased(frame, 38, 22) }}>
            <Kicker size={T.micro}>{str(params, "sub", "")}</Kicker>
          </div>
        </div>
      </AbsoluteFill>
    </Hold>
  );
};

export const MetricStrip: React.FC<SceneProps> = ({ image, params }) => {
  const { frame, H } = useT();
  const items = pipes(params.items);
  return (
    <Hold>
      <Plate image={image} dim={0.5} zoom={1.06} />
      <div style={{ position: "absolute", left: "6%", bottom: "13%" }}>
        {items.map((it, i) => (
          <div key={it} style={{ display: "flex", alignItems: "center", gap: 18, marginTop: i ? 14 : 0,
            opacity: eased(frame, 8 + i * 12, 20, "power3.out"),
            transform: `translateX(${(1 - eased(frame, 8 + i * 12, 20, "power3.out")) * -16}px)` }}>
            <div style={{ width: 26, height: 1, background: i === 0 ? C.system : C.textFaint }} />
            <span style={{ ...mono, fontSize: T.body * H * 0.86, color: i === 0 ? C.text : C.textDim,
              letterSpacing: "0.04em" }}>{it}</span>
          </div>
        ))}
      </div>
    </Hold>
  );
};

export const SpecStrip: React.FC<SceneProps> = ({ image, params }) => {
  const { frame, H } = useT();
  const items = pipes(params.items);
  return (
    <Hold>
      <Plate image={image} dim={0.58} zoom={1.05} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: "14%",
        display: "flex", justifyContent: "center", gap: "7%" }}>
        {items.map((it, i) => (
          <div key={it} style={{ textAlign: "center",
            opacity: eased(frame, 8 + i * 10, 20, "power3.out") }}>
            <div style={{ fontFamily: `${DISPLAY}, sans-serif`, fontSize: T.num * H * 0.92,
              fontWeight: 600, color: C.text, fontVariantNumeric: "tabular-nums" }}>{it}</div>
            <Rule w={46} delay={14 + i * 10} colour={C.system}
              style={{ margin: "12px auto 0" }} />
          </div>
        ))}
      </div>
    </Hold>
  );
};

export const StatBig: React.FC<SceneProps> = ({ text, params }) => {
  const { frame, H } = useT();
  return (
    <Hold>
      <Ground />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontFamily: `${DISPLAY}, sans-serif`, fontSize: T.hero * H * 1.25,
            fontWeight: 600, color: C.system, letterSpacing: "-0.02em",
            opacity: eased(frame, 4, 22, "power3.out") }}>{text}</div>
          <div style={{ marginTop: 20 }}><Kicker delay={18}>{str(params, "label", "")}</Kicker></div>
          <div style={{ marginTop: 28, opacity: eased(frame, 30, 20) }}>
            <Kicker size={T.micro} colour={C.textFaint}>{str(params, "foot", "")}</Kicker>
          </div>
        </div>
      </AbsoluteFill>
    </Hold>
  );
};
