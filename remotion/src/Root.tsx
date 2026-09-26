import React from "react";
import { Composition } from "remotion";

import { Scene } from "./Scene";
import { DEFAULT_SCENE } from "./lib/types";
import { Short, DEFAULT_SHORT } from "./short/Short";

/**
 * Two compositions:
 *  - Scene: one documentary scene (16:9), fed per-render by the Python pipeline.
 *  - Short: a 9:16 vertical Short, fed a script + audio via --props. Duration,
 *    fps and size come from the props so any narration length just works.
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
      id="Short"
      component={Short as React.ComponentType<any>}
      durationInFrames={DEFAULT_SHORT.durationInFrames}
      fps={DEFAULT_SHORT.fps}
      width={1080}
      height={1920}
      defaultProps={DEFAULT_SHORT}
      calculateMetadata={({ props }) => ({
        durationInFrames: (props as any).durationInFrames ?? 900,
        fps: (props as any).fps ?? 30,
      })}
    />
  </>
);
