import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

import { eased, num, str } from "../lib/anim";
import type { SceneProps } from "../lib/types";
import { Backdrop, Grain, Vignette, baseText } from "./shared";

/**
 * A camera move with a real easing curve rather than a linear ramp.
 *
 * This is the workhorse: most scenes want motion and nothing else. Unlike the
 * ffmpeg zoompan version it eases in and out, so the move settles instead of
 * stopping dead.
 *
 * params: zoom=1.12 pan=left|right|up|down curve=power2.inOut
 */
export const KenBurnsPro: React.FC<SceneProps> = ({ image, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { height } = useVideoConfig();

  const zoom = num(params, "zoom", 1.1);
  const direction = str(params, "pan", "none");
  const curve = str(params, "curve", "power1.inOut");
  const travel = num(params, "travel", 3);

  const pan = {
    left: [travel, 0],
    right: [-travel, 0],
    up: [0, travel],
    down: [0, -travel],
    none: [0, 0],
  }[direction] ?? [0, 0];

  return (
    <AbsoluteFill>
      <Backdrop
        image={image}
        zoomFrom={1.0}
        zoomTo={zoom}
        panX={pan[0]}
        panY={pan[1]}
        curve={curve}
        dim={num(params, "dim", 0)}
      />
      <Vignette strength={num(params, "vignette", 0.45)} />
      {text ? (
        <AbsoluteFill style={{ justifyContent: "flex-end", padding: height * 0.08 }}>
          <div
            style={{
              ...baseText,
              fontSize: height * 0.036,
              opacity: eased(frame, 14, 18),
              textShadow: "0 2px 18px rgba(0,0,0,0.8)",
            }}
          >
            {text}
          </div>
        </AbsoluteFill>
      ) : null}
      <Grain opacity={num(params, "grain", 0.06)} />
    </AbsoluteFill>
  );
};

/**
 * Two stills meeting at a wipe line that travels across — for before/after,
 * two places, or two eras.
 *
 * params: second=<filename in the same folder> label_a=... label_b=...
 */
export const SplitCompare: React.FC<SceneProps> = ({ image, accent, params }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const second = str(params, "second");
  const split = eased(frame, 8, 34, "power3.inOut");
  const linePosition = 0.5 + (split - 0.5) * 0;
  const revealWidth = width * split;
  const labelA = str(params, "label_a");
  const labelB = str(params, "label_b");

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <Img
        src={staticFile(image)}
        style={{ width: "100%", height: "100%", objectFit: "cover", position: "absolute" }}
      />
      {second ? (
        <AbsoluteFill style={{ clipPath: `inset(0 0 0 ${revealWidth}px)` }}>
          <Img
            src={staticFile(second)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill>
        <div
          style={{
            position: "absolute",
            left: revealWidth - 1.5,
            top: 0,
            width: 3,
            height: "100%",
            backgroundColor: accent,
            opacity: second ? 1 : 0,
          }}
        />
      </AbsoluteFill>
      {(labelA || labelB) && (
        <AbsoluteFill
          style={{
            justifyContent: "flex-end",
            flexDirection: "row",
            alignItems: "flex-start",
            padding: height * 0.06,
            gap: width * 0.04,
          }}
        >
          <div style={{ ...baseText, fontSize: height * 0.03, flex: 1, opacity: eased(frame, 20, 14) }}>
            {labelA}
          </div>
          <div
            style={{
              ...baseText,
              fontSize: height * 0.03,
              flex: 1,
              textAlign: "right",
              opacity: eased(frame, 26, 14),
            }}
          >
            {labelB}
          </div>
        </AbsoluteFill>
      )}
      <Vignette />
      <Grain />
    </AbsoluteFill>
  );
};

/**
 * A transparent-background subject (a person, an object) sliding and rising in
 * over a held background image — the "cutout over the previous image" move.
 *
 * The background (`image`) drifts slowly; the cutout (`overlay`, a PNG with
 * alpha) eases up from below with a soft shadow, so a figure appears to step
 * into the scene rather than cut to it.
 *
 * params: from=left|right|bottom (default bottom)  scale=0.92
 */
export const CutoutReveal: React.FC<SceneProps> = ({ image, overlay, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();

  const from = str(params, "from", "bottom");
  const scale = num(params, "scale", 0.94);
  const enter = eased(frame, 2, 22, "power3.out");
  const settle = eased(frame, 20, durationInFrames - 20, "sine.inOut");

  const offset = (1 - enter);
  const tx = from === "left" ? -offset * width * 0.4 : from === "right" ? offset * width * 0.4 : 0;
  const ty = from === "bottom" ? offset * height * 0.5 : 0;
  const drift = (settle - 0.5) * 14; // gentle life once settled

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <Backdrop image={image} zoomFrom={1.0} zoomTo={1.06} curve="power1.inOut" dim={num(params, "dim", 0.25)} />
      <Vignette strength={num(params, "vignette", 0.4)} />
      {overlay ? (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
          <Img
            src={staticFile(overlay)}
            style={{
              height: `${scale * 100}%`,
              objectFit: "contain",
              transform: `translate(${tx + drift}px, ${ty}px) scale(${0.98 + enter * 0.02})`,
              opacity: eased(frame, 0, 14),
              filter: "drop-shadow(0 24px 40px rgba(0,0,0,0.6))",
            }}
          />
        </AbsoluteFill>
      ) : null}
      {text ? (
        <AbsoluteFill style={{ justifyContent: "flex-end", padding: height * 0.07 }}>
          <div style={{ ...baseText, fontSize: height * 0.036, opacity: eased(frame, 16, 16),
                        textShadow: "0 2px 18px rgba(0,0,0,0.85)" }}>
            {text}
          </div>
        </AbsoluteFill>
      ) : null}
      <Grain />
    </AbsoluteFill>
  );
};
