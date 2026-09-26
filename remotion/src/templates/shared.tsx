import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

import { eased, interpolateEased } from "../lib/anim";
import { SANS } from "../lib/useFont";

/** The still, filling the frame, with an optional eased camera move over it. */
export const Backdrop: React.FC<{
  image: string;
  zoomFrom?: number;
  zoomTo?: number;
  panX?: number;
  panY?: number;
  curve?: string;
  dim?: number;
}> = ({ image, zoomFrom = 1, zoomTo = 1, panX = 0, panY = 0, curve = "none", dim = 0 }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const t = eased(frame, 0, durationInFrames, curve);
  const scale = zoomFrom + (zoomTo - zoomFrom) * t;
  const x = panX * t;
  const y = panY * t;

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#000" }}>
      {image ? (
        <Img
          src={staticFile(image)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${scale}) translate(${x}%, ${y}%)`,
            transformOrigin: "center center",
          }}
        />
      ) : null}
      {dim > 0 ? (
        <AbsoluteFill style={{ backgroundColor: `rgba(6,8,11,${dim})` }} />
      ) : null}
    </AbsoluteFill>
  );
};

/** A soft edge darkening that stops flat AI stills looking like wallpaper. */
export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.55 }) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,${strength}) 100%)`,
    }}
  />
);

/** Animated film grain — a cheap, convincing unifier across generated images. */
export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.07 }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ opacity, mixBlendMode: "overlay", pointerEvents: "none" }}>
      <svg width="100%" height="100%">
        <filter id={`grain${frame % 5}`}>
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.85"
            numOctaves={2}
            seed={frame % 5}
          />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grain${frame % 5})`} />
      </svg>
    </AbsoluteFill>
  );
};

/** Words revealing one after another — the base of every text treatment here. */
export const StaggeredWords: React.FC<{
  text: string;
  startFrame?: number;
  perWord?: number;
  style?: React.CSSProperties;
  curve?: string;
}> = ({ text, startFrame = 0, perWord = 3, style, curve = "power3.out" }) => {
  const frame = useCurrentFrame();
  const words = text.split(" ").filter(Boolean);

  return (
    <span style={{ display: "inline-flex", flexWrap: "wrap", gap: "0.28em", ...style }}>
      {words.map((word, index) => {
        const t = eased(frame, startFrame + index * perWord, 14, curve);
        return (
          <span
            key={`${word}-${index}`}
            style={{
              display: "inline-block",
              opacity: t,
              transform: `translateY(${(1 - t) * 0.5}em)`,
            }}
          >
            {word}
          </span>
        );
      })}
    </span>
  );
};

/** A rule that draws itself outward — used to underline and to separate. */
export const DrawRule: React.FC<{
  width: number;
  height?: number;
  colour: string;
  startFrame?: number;
  durationFrames?: number;
  origin?: "left" | "center";
}> = ({ width, height = 4, colour, startFrame = 0, durationFrames = 18, origin = "left" }) => {
  const frame = useCurrentFrame();
  const grown = interpolateEased(frame, startFrame, durationFrames, 0, width, "power3.out");
  return (
    <div
      style={{
        width: grown,
        height,
        backgroundColor: colour,
        alignSelf: origin === "center" ? "center" : "flex-start",
        borderRadius: height,
      }}
    />
  );
};

export const baseText: React.CSSProperties = {
  fontFamily: `${SANS}, sans-serif`,
  color: "white",
  lineHeight: 1.25,
  margin: 0,
};
