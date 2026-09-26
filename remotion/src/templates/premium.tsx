import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

import { eased, interpolateEased, num, str } from "../lib/anim";
import { SANS, SERIF } from "../lib/useFont";
import type { SceneProps } from "../lib/types";
import { Backdrop, DrawRule, Grain, StaggeredWords, Vignette, baseText } from "./shared";

/**
 * #3 — 2.5D parallax from a single still. The image is layered as two planes:
 * a background that drifts slowly and a foreground (lower portion, masked and
 * scaled a touch larger) that moves faster, so the ground/near objects travel
 * past the far background — real multiplane parallax, no depth model needed.
 * If an `overlay` cutout is supplied it becomes a true third plane on top.
 *
 * params: dir=left|right (default left)  depth=1 (strength)
 */
export const Parallax: React.FC<SceneProps> = ({ image, overlay, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();
  const dir = str(params, "dir", "left") === "right" ? 1 : -1;
  const depth = num(params, "depth", 1);
  const t = eased(frame, 0, durationInFrames, "power1.inOut");

  const bgX = dir * t * width * 0.04 * depth;
  const bgScale = 1.08 + t * 0.04;
  const fgX = dir * t * width * 0.11 * depth;   // foreground moves ~3x faster
  const fgScale = 1.18 + t * 0.06;

  const layer: React.CSSProperties = {
    position: "absolute", width: "100%", height: "100%", objectFit: "cover",
  };
  return (
    <AbsoluteFill style={{ backgroundColor: "#000", overflow: "hidden" }}>
      {/* far plane */}
      <Img src={staticFile(image)} style={{ ...layer, transform: `translateX(${bgX}px) scale(${bgScale})` }} />
      {/* near plane — bottom 55%, moves faster */}
      <Img
        src={staticFile(image)}
        style={{
          ...layer,
          transform: `translateX(${fgX}px) scale(${fgScale})`,
          WebkitMaskImage: "linear-gradient(to bottom, transparent 42%, black 62%)",
          maskImage: "linear-gradient(to bottom, transparent 42%, black 62%)",
        }}
      />
      {overlay ? (
        <Img src={staticFile(overlay)} style={{ ...layer, objectFit: "contain",
              transform: `translateX(${fgX * 1.4}px) scale(${1.02 + t * 0.04})` }} />
      ) : null}
      <AbsoluteFill style={{ background: `rgba(6,8,11,${num(params, "dim", 0.28)})` }} />
      <Vignette strength={num(params, "vignette", 0.5)} />
      {text ? (
        <AbsoluteFill style={{ justifyContent: "flex-end", padding: height * 0.08 }}>
          <div style={{ ...baseText, fontSize: height * 0.036, opacity: eased(frame, 12, 16),
                        textShadow: "0 2px 18px rgba(0,0,0,0.85)" }}>{text}</div>
        </AbsoluteFill>
      ) : null}
      <Grain />
    </AbsoluteFill>
  );
};

/** #6 — A pulled quotation: giant serif quote marks, words revealing, attribution. */
export const PullQuote: React.FC<SceneProps> = ({ image, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const by = str(params, "by");
  const markGrow = eased(frame, 0, 18, "back.out(1.5)");
  return (
    <AbsoluteFill>
      <Backdrop image={image} zoomFrom={1.0} zoomTo={1.06} curve="none" dim={0.66} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: `0 ${width * 0.1}px` }}>
        <div style={{ fontFamily: `${SERIF}, serif`, color: accent, fontSize: height * 0.16,
                      lineHeight: 0.6, opacity: 0.9, transform: `scale(${markGrow})`,
                      marginBottom: height * 0.01, alignSelf: "flex-start" }}>&ldquo;</div>
        <div style={{ ...baseText, fontFamily: `${SERIF}, serif`, fontSize: height * 0.058,
                      textAlign: "center", fontWeight: 700 }}>
          <StaggeredWords text={text} startFrame={8} perWord={2.5} />
        </div>
        <div style={{ marginTop: height * 0.04 }}>
          <DrawRule width={height * 0.1} height={3} colour={accent} startFrame={24} origin="center" />
        </div>
        {by ? (
          <div style={{ ...baseText, fontSize: height * 0.028, color: "rgba(255,255,255,0.72)",
                        marginTop: height * 0.03, letterSpacing: "0.14em",
                        opacity: eased(frame, 34, 18) }}>— {by}</div>
        ) : null}
      </AbsoluteFill>
      <Grain />
    </AbsoluteFill>
  );
};

/** #9a — Intro: brand mark + title reveal. */
export const IntroCard: React.FC<SceneProps> = ({ image, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();
  const ring = eased(frame, 4, 24, "power3.out");
  const brand = str(params, "brand", "THE QUIET STORY");
  const kicker = str(params, "kicker");
  const titleReveal = eased(frame, 20, 24, "power4.out");
  const out = 1 - eased(frame, durationInFrames - 14, 14, "power2.in");
  return (
    <AbsoluteFill style={{ backgroundColor: "#07090f" }}>
      {image ? <Backdrop image={image} zoomFrom={1.1} zoomTo={1.0} curve="power2.out" dim={0.72} /> : null}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column", opacity: out }}>
        <svg width={height * 0.14} height={height * 0.14} viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="44" fill="none" stroke={accent} strokeWidth="3"
                  strokeDasharray={2 * Math.PI * 44} strokeDashoffset={(1 - ring) * 2 * Math.PI * 44}
                  transform="rotate(-90 50 50)" />
          <circle cx="62" cy="72" r="5" fill={accent} opacity={ring} />
        </svg>
        <div style={{ ...baseText, fontFamily: `${SERIF}, serif`, letterSpacing: "0.22em",
                      fontSize: height * 0.022, color: "rgba(255,255,255,0.6)", marginTop: height * 0.03,
                      opacity: eased(frame, 10, 16) }}>{brand}</div>
        {kicker ? <div style={{ ...baseText, fontSize: height * 0.02, color: accent, letterSpacing: "0.3em",
                      marginTop: height * 0.03, opacity: eased(frame, 24, 14) }}>{kicker}</div> : null}
        <div style={{ overflow: "hidden", marginTop: height * 0.02 }}>
          <div style={{ ...baseText, fontFamily: `${SERIF}, serif`, fontSize: height * 0.07, fontWeight: 700,
                        textAlign: "center", maxWidth: width * 0.8,
                        transform: `translateY(${(1 - titleReveal) * 110}%)` }}>{text}</div>
        </div>
      </AbsoluteFill>
      <Grain />
    </AbsoluteFill>
  );
};

/** #9b — End card: subscribe + a next-up hook. */
export const EndCard: React.FC<SceneProps> = ({ image, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const pop = eased(frame, 4, 18, "back.out(1.8)");
  const brand = str(params, "brand", "THE QUIET STORY");
  const next = str(params, "next");
  return (
    <AbsoluteFill style={{ backgroundColor: "#07090f" }}>
      {image ? <Backdrop image={image} zoomFrom={1.05} zoomTo={1.0} dim={0.76} /> : null}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column" }}>
        <div style={{ ...baseText, fontFamily: `${SERIF}, serif`, letterSpacing: "0.2em",
                      fontSize: height * 0.02, color: "rgba(255,255,255,0.55)",
                      opacity: eased(frame, 2, 14) }}>{brand}</div>
        <div style={{ transform: `scale(${pop})`, marginTop: height * 0.03,
                      background: accent, color: "#07090f", fontFamily: `${SANS}, sans-serif`,
                      fontWeight: 800, fontSize: height * 0.038, padding: `${height*0.018}px ${height*0.05}px`,
                      borderRadius: 999 }}>{text || "SUBSCRIBE"}</div>
        {next ? (
          <div style={{ ...baseText, fontSize: height * 0.028, marginTop: height * 0.05,
                        opacity: eased(frame, 22, 16) }}>
            आगे देखिए: <span style={{ color: accent }}>{next}</span>
          </div>
        ) : null}
      </AbsoluteFill>
      <Grain />
    </AbsoluteFill>
  );
};
