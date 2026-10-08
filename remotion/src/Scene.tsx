import React from "react";
import { AbsoluteFill } from "remotion";

import { DEFAULT_SCENE, type SceneProps } from "./lib/types";
import { useDevanagariFonts } from "./lib/useFont";
import { useFilmFonts } from "./qc/fonts";
import { TEMPLATES } from "./templates";

/**
 * One scene of the film. The template is chosen by name at render time, so the
 * Python side only ever passes data — it never needs to know about React.
 */
export const Scene: React.FC<Partial<SceneProps>> = (incoming) => {
  const props: SceneProps = { ...DEFAULT_SCENE, ...incoming, params: incoming.params ?? {} };
  useDevanagariFonts();
  useFilmFonts();

  const Template = TEMPLATES[props.template];
  if (!Template) {
    // Fail loudly in the render rather than producing a silently blank clip.
    return (
      <AbsoluteFill
        style={{
          backgroundColor: "#3b0d0d",
          color: "white",
          fontSize: 32,
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "monospace",
          padding: 60,
          textAlign: "center",
        }}
      >
        Unknown template: {props.template}
      </AbsoluteFill>
    );
  }

  return <Template {...props} />;
};
