import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { ComposableMap, Geographies, Geography, Marker, Line } from "react-simple-maps";

import { eased, interpolateEased, list, num, str } from "../lib/anim";
import { SERIF, SANS } from "../lib/useFont";
import type { SceneProps } from "../lib/types";
import { Grain, Vignette } from "./shared";
import indiaStates from "../data/india-states.geo.json";

/** Cities the film visits — real coordinates [lng, lat]. Extend as needed. */
const PLACES: Record<string, { c: [number, number]; label: string }> = {
  mhow:     { c: [75.7649, 22.5519], label: "महू" },
  bombay:   { c: [72.8777, 19.0760], label: "बम्बई" },
  baroda:   { c: [73.1812, 22.3072], label: "बड़ौदा" },
  mahad:    { c: [73.4180, 18.0833], label: "महाड़" },
  nashik:   { c: [73.7898, 19.9975], label: "नासिक" },
  nagpur:   { c: [79.0882, 21.1458], label: "नागपुर" },
  delhi:    { c: [77.2090, 28.6139], label: "दिल्ली" },
  london:   { c: [-0.1276, 51.5074], label: "लंदन" },
  newyork:  { c: [-74.0060, 40.7128], label: "न्यूयॉर्क" },
};

/**
 * A real map of India (actual state borders, real city coordinates) with an
 * eased camera push, pins that drop, routes that draw, and an optional state
 * highlight. Geography comes from react-simple-maps (d3-geo under the hood);
 * only the camera/reveal progress is driven per frame, so the render stays
 * deterministic.
 *
 * params: focus=mhow  scale=our zoom  pins=mahad,nashik  route=bombay,london
 *         highlight=Maharashtra
 */
export const GeoMap: React.FC<SceneProps> = ({ text, accent, ink, params }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();

  const focus = str(params, "focus", "mhow");
  const centre = PLACES[focus]?.c ?? [79, 22];
  const scale = num(params, "scale", 1500);
  const date = str(params, "date");
  // Ken-Burns move over the whole map so it never feels static
  const kz = interpolateEased(frame, 0, durationInFrames, 1.03, 1.18, "power1.inOut");
  const kx = interpolateEased(frame, 0, durationInFrames, 2.5, -2.5, "power1.inOut");

  const pins = list(params, "pins").filter((p) => PLACES[p]);
  const route = list(params, "route").filter((p) => PLACES[p]);
  const highlight = str(params, "highlight");

  return (
    <AbsoluteFill style={{ backgroundColor: "#0d0f13" }}>
     <AbsoluteFill style={{ transform: `scale(${kz}) translate(${kx}%, 0%)`, transformOrigin: "50% 45%" }}>
      <ComposableMap
        width={width}
        height={height}
        projection="geoMercator"
        projectionConfig={{ center: centre as [number, number], scale }}
        style={{ width: "100%", height: "100%" }}
      >
        <Geographies geography={indiaStates as any}>
          {({ geographies }: any) =>
            geographies.map((geo: any) => {
              const isHi = highlight && geo.properties.state === highlight;
              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill={isHi ? accent : "#20262e"}
                  stroke="#3a434f"
                  strokeWidth={0.5}
                  style={{
                    default: { outline: "none", opacity: isHi ? eased(frame, 8, 20) * 0.55 + 0.45 : 1 },
                    hover: { outline: "none" },
                    pressed: { outline: "none" },
                  } as any}
                />
              );
            })
          }
        </Geographies>

        {/* Routes draw in order, each segment timed after the last */}
        {route.length >= 2 &&
          route.slice(1).map((to, i) => {
            const seg = eased(frame, 14 + i * 10, 12, "power2.inOut");
            const from = PLACES[route[i]].c;
            const dest = PLACES[to].c;
            const cx = from[0] + (dest[0] - from[0]) * seg;
            const cy = from[1] + (dest[1] - from[1]) * seg;
            return (
              <Line
                key={`ln-${i}`}
                from={from}
                to={[cx, cy] as [number, number]}
                stroke={accent}
                strokeWidth={2.5}
                strokeLinecap="round"
              />
            );
          })}

        {/* Pins drop with a back-eased bounce, then a label rises */}
        {pins.map((p, i) => {
          const drop = eased(frame, 10 + i * 6, 16, "back.out(2.2)");
          const place = PLACES[p];
          return (
            <Marker key={p} coordinates={place.c}>
              <g transform={`translate(0, ${(1 - drop) * -40})`} opacity={drop}>
                <circle r={6} fill={accent} stroke="#0d0f13" strokeWidth={1.5} />
                <circle r={6 + eased(frame, 16 + i * 6, 30) * 14} fill="none" stroke={accent}
                        strokeWidth={1} opacity={1 - eased(frame, 16 + i * 6, 30)} />
                <text
                  y={-16}
                  textAnchor="middle"
                  style={{ fontFamily: `${SANS}, sans-serif`, fill: "white",
                           fontSize: 20, fontWeight: 700,
                           opacity: eased(frame, 18 + i * 6, 12),
                           paintOrder: "stroke", stroke: "#0d0f13", strokeWidth: 4 }}
                >
                  {place.label}
                </text>
              </g>
            </Marker>
          );
        })}
      </ComposableMap>
     </AbsoluteFill>

      <Vignette strength={0.5} />
      {(text || date) ? (
        <AbsoluteFill style={{ justifyContent: "flex-start", padding: height * 0.07 }}>
          {date ? (
            <div style={{ display: "inline-block", alignSelf: "flex-start", background: accent, color: "#0d0f13",
                          fontFamily: `${SANS}, sans-serif`, fontWeight: 800, fontSize: height * 0.028,
                          padding: `${height*0.006}px ${height*0.02}px`, borderRadius: 6,
                          marginBottom: height * 0.02, opacity: eased(frame, 6, 12) }}>{date}</div>
          ) : null}
          {text ? (
            <div style={{ fontFamily: `${SERIF}, serif`, color: "white", fontWeight: 700,
                          fontSize: height * 0.056, opacity: eased(frame, 4, 16),
                          textShadow: "0 2px 18px rgba(0,0,0,0.85)" }}>{text}</div>
          ) : null}
        </AbsoluteFill>
      ) : null}
      <Grain opacity={0.05} />
    </AbsoluteFill>
  );
};
