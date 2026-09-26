import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

import { eased, fadeInOut, interpolateEased, num, str } from "../lib/anim";
import { SERIF } from "../lib/useFont";
import type { SceneProps } from "../lib/types";
import { Backdrop, DrawRule, Grain, StaggeredWords, Vignette, baseText } from "./shared";

/** A masked headline that wipes up behind a sweeping accent bar. */
export const TitleReveal: React.FC<SceneProps> = ({ image, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { height, durationInFrames } = useVideoConfig();
  const reveal = eased(frame, 6, 22, "power4.out");
  const sweep = eased(frame, 4, 26, "power3.inOut");

  return (
    <AbsoluteFill>
      <Backdrop image={image} zoomFrom={1.06} zoomTo={1.0} curve="power2.out" dim={0.42} />
      <Vignette />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "8%" }}>
        <div style={{ overflow: "hidden", paddingBottom: "0.12em" }}>
          <h1
            style={{
              ...baseText,
              fontFamily: `${SERIF}, serif`,
              fontSize: height * num(params, "size", 0.085),
              textAlign: "center",
              transform: `translateY(${(1 - reveal) * 100}%)`,
              opacity: fadeInOut(frame, durationInFrames, 8, 14),
            }}
          >
            {text}
          </h1>
        </div>
        <div style={{ marginTop: height * 0.035 }}>
          <DrawRule width={height * 0.22 * sweep} height={3} colour={accent} startFrame={10} />
        </div>
      </AbsoluteFill>
      <Grain />
    </AbsoluteFill>
  );
};

/** Layered lower third: a slab slides out, an accent edge leads it, text follows. */
export const LowerThird: React.FC<SceneProps> = ({ image, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();
  const slab = eased(frame, 4, 20, "power4.out");
  const out = 1 - eased(frame, durationInFrames - 16, 16, "power2.in");
  const subtitle = str(params, "sub");

  return (
    <AbsoluteFill>
      <Backdrop image={image} zoomFrom={1.0} zoomTo={1.05} curve="none" />
      <Vignette strength={0.4} />
      <AbsoluteFill style={{ justifyContent: "flex-end", paddingBottom: height * 0.09 }}>
        <div
          style={{
            transform: `translateX(${(slab - 1) * 60}%)`,
            opacity: out,
            display: "flex",
            alignItems: "stretch",
            marginLeft: width * 0.06,
            maxWidth: width * 0.62,
          }}
        >
          <div style={{ width: 6, backgroundColor: accent }} />
          <div
            style={{
              backgroundColor: "rgba(8,10,14,0.82)",
              padding: `${height * 0.028}px ${width * 0.03}px`,
              backdropFilter: "blur(6px)",
            }}
          >
            <div style={{ ...baseText, fontSize: height * 0.05, fontWeight: 600 }}>{text}</div>
            {subtitle ? (
              <div
                style={{
                  ...baseText,
                  fontSize: height * 0.028,
                  color: "rgba(255,255,255,0.72)",
                  marginTop: height * 0.012,
                  opacity: eased(frame, 16, 16),
                }}
              >
                {subtitle}
              </div>
            ) : null}
          </div>
        </div>
      </AbsoluteFill>
      <Grain opacity={0.05} />
    </AbsoluteFill>
  );
};

/** A pulled quotation, revealed word by word above an attribution. */
export const Quote: React.FC<SceneProps> = ({ image, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { height, width } = useVideoConfig();
  const attribution = str(params, "by");

  return (
    <AbsoluteFill>
      <Backdrop image={image} zoomFrom={1.0} zoomTo={1.06} curve="none" dim={0.62} />
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          flexDirection: "column",
          padding: `0 ${width * 0.12}px`,
        }}
      >
        <DrawRule width={height * 0.12} height={3} colour={accent} startFrame={2} origin="center" />
        <div
          style={{
            ...baseText,
            fontFamily: `${SERIF}, serif`,
            fontSize: height * 0.062,
            textAlign: "center",
            marginTop: height * 0.05,
          }}
        >
          <StaggeredWords text={text} startFrame={10} perWord={2} />
        </div>
        {attribution ? (
          <div
            style={{
              ...baseText,
              fontSize: height * 0.03,
              color: "rgba(255,255,255,0.6)",
              marginTop: height * 0.05,
              letterSpacing: "0.12em",
              opacity: eased(frame, 34, 18),
            }}
          >
            {attribution}
          </div>
        ) : null}
      </AbsoluteFill>
      <Grain />
    </AbsoluteFill>
  );
};

/** A chapter opener: number, rule and title arriving in sequence. */
export const ChapterCard: React.FC<SceneProps> = ({ image, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { height, width } = useVideoConfig();
  const chapter = str(params, "chapter");
  const slide = interpolateEased(frame, 0, 26, 40, 0, "power4.out");

  return (
    <AbsoluteFill>
      <Backdrop image={image} zoomFrom={1.08} zoomTo={1.0} curve="power2.out" dim={0.58} />
      <AbsoluteFill
        style={{
          justifyContent: "center",
          flexDirection: "column",
          paddingLeft: width * 0.1,
          transform: `translateX(${slide}px)`,
        }}
      >
        {chapter ? (
          <div
            style={{
              ...baseText,
              fontSize: height * 0.028,
              color: accent,
              opacity: eased(frame, 2, 16),
              marginBottom: height * 0.03,
            }}
          >
            {chapter}
          </div>
        ) : null}
        <DrawRule width={height * 0.16} height={4} colour={accent} startFrame={8} />
        <h1
          style={{
            ...baseText,
            fontFamily: `${SERIF}, serif`,
            fontSize: height * 0.085,
            marginTop: height * 0.035,
            maxWidth: width * 0.7,
          }}
        >
          <StaggeredWords text={text} startFrame={14} perWord={3} />
        </h1>
      </AbsoluteFill>
      <Vignette />
      <Grain />
    </AbsoluteFill>
  );
};
