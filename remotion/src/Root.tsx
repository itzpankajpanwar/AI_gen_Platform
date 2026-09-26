import React from "react";
import { Composition } from "remotion";

import { Scene } from "./Scene";
import { GpsShort } from "./short/Short";
import { DEFAULT_SCENE } from "./lib/types";

/**
 * Dimensions and duration are supplied per render by the Python pipeline via
 * --props, so one composition serves every scene in the film.
 */
export const RemotionRoot: React.FC = () => (
  <>
    <Composition
    id="Scene"
    component={Scene}
    durationInFrames={90}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={DEFAULT_SCENE}
    calculateMetadata={({ props }) => ({
      durationInFrames: (props as any).durationInFrames ?? 90,
      fps: (props as any).fps ?? 30,
      width: (props as any).width ?? 1920,
      height: (props as any).height ?? 1080,
    })}
  />
    <Composition
      id="GpsShort"
      component={GpsShort}
      durationInFrames={900}
      fps={30}
      width={1080}
      height={1920}
    />
  </>
);
