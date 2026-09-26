import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

import { eased, interpolateEased, list, num, str } from "../lib/anim";
import { SERIF } from "../lib/useFont";
import type { SceneProps } from "../lib/types";
import { Backdrop, DrawRule, Grain, Vignette, baseText } from "./shared";

/**
 * An SVG timeline: the rule draws across, ticks pop in as it passes them, and a
 * marker rides the line to the highlighted year.
 *
 * params: from=1891 to=1956 marks=1907;1927;1949 highlight=1927
 */
export const Timeline: React.FC<SceneProps> = ({ image, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();

  const from = num(params, "from", 1891);
  const to = num(params, "to", 1956);
  const marks = list(params, "marks").map(Number).filter(Number.isFinite);
  const highlight = num(params, "highlight", NaN);

  const left = width * 0.12;
  const right = width * 0.88;
  const span = right - left;
  const y = height * 0.62;

  const draw = eased(frame, 8, 34, "power3.inOut");
  const at = (year: number) => left + ((year - from) / Math.max(to - from, 1)) * span;
  const markerYear = Number.isFinite(highlight) ? highlight : to;
  const markerX = interpolateEased(frame, 26, 34, left, at(markerYear), "power3.inOut");

  return (
    <AbsoluteFill>
      <Backdrop image={image} zoomFrom={1.0} zoomTo={1.04} dim={0.55} />
      <AbsoluteFill>
        <svg width={width} height={height}>
          <line
            x1={left}
            y1={y}
            x2={left + span * draw}
            y2={y}
            stroke="rgba(255,255,255,0.35)"
            strokeWidth={2}
          />
          {marks.map((year, index) => {
            const x = at(year);
            const reached = (x - left) / span <= draw ? 1 : 0;
            const pop = eased(frame, 14 + index * 4, 12, "back.out(2)") * reached;
            return (
              <g key={year} opacity={pop}>
                <line x1={x} y1={y - 10} x2={x} y2={y + 10} stroke="rgba(255,255,255,0.5)" strokeWidth={2} />
                <text
                  x={x}
                  y={y + height * 0.06}
                  fill="rgba(255,255,255,0.72)"
                  fontSize={height * 0.026}
                  fontFamily="sans-serif"
                  textAnchor="middle"
                >
                  {year}
                </text>
              </g>
            );
          })}
          <g opacity={eased(frame, 26, 12)}>
            <circle cx={markerX} cy={y} r={height * 0.016} fill={accent} />
            <circle
              cx={markerX}
              cy={y}
              r={height * 0.016 + eased(frame, 40, 30, "power2.out") * height * 0.03}
              fill="none"
              stroke={accent}
              strokeWidth={2}
              opacity={1 - eased(frame, 40, 30, "power2.out")}
            />
          </g>
          <text
            x={left}
            y={y - height * 0.06}
            fill="white"
            fontSize={height * 0.05}
            fontFamily={`${SERIF}, serif`}
            opacity={eased(frame, 4, 18)}
          >
            {text}
          </text>
        </svg>
      </AbsoluteFill>
      <Vignette />
      <Grain />
    </AbsoluteFill>
  );
};

/**
 * A route drawing itself across the frame with a travelling head.
 *
 * Uses stroke-dashoffset — the standard SVG line-drawing technique — so the
 * path appears to be drawn rather than faded in.
 *
 * params: path="10,80 35,60 62,55 88,30" (percentages of the frame)
 */
export const MapRoute: React.FC<SceneProps> = ({ image, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();

  const points = str(params, "path", "12,78 34,62 58,56 86,32")
    .split(" ")
    .map((pair) => pair.split(",").map(Number))
    .filter((pair) => pair.length === 2 && pair.every(Number.isFinite))
    .map(([px, py]) => [(px / 100) * width, (py / 100) * height] as const);

  const d = points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x},${y}`).join(" ");
  const total = points.reduce((sum, point, i) => {
    if (i === 0) return 0;
    const [x1, y1] = points[i - 1];
    const [x2, y2] = point;
    return sum + Math.hypot(x2 - x1, y2 - y1);
  }, 0);

  const drawn = eased(frame, 10, durationInFrames - 30, "power2.inOut");
  const head = points.length ? points[Math.min(points.length - 1, Math.floor(drawn * (points.length - 1) + 0.0001))] : null;

  return (
    <AbsoluteFill>
      <Backdrop image={image} zoomFrom={1.0} zoomTo={1.05} dim={0.45} />
      <AbsoluteFill>
        <svg width={width} height={height}>
          <path d={d} fill="none" stroke="rgba(255,255,255,0.18)" strokeWidth={5} strokeLinecap="round" />
          <path
            d={d}
            fill="none"
            stroke={accent}
            strokeWidth={5}
            strokeLinecap="round"
            strokeDasharray={total}
            strokeDashoffset={total * (1 - drawn)}
          />
          {points.map(([x, y], index) => (
            <circle
              key={index}
              cx={x}
              cy={y}
              r={height * 0.011}
              fill={accent}
              opacity={eased(frame, 10 + index * 8, 10)}
            />
          ))}
          {head ? (
            <circle cx={head[0]} cy={head[1]} r={height * 0.02} fill="none" stroke={accent} strokeWidth={2} opacity={0.6} />
          ) : null}
          {text ? (
            <text
              x={width * 0.5}
              y={height * 0.14}
              fill="white"
              fontSize={height * 0.045}
              fontFamily={`${SERIF}, serif`}
              textAnchor="middle"
              opacity={eased(frame, 6, 16)}
            >
              {text}
            </text>
          ) : null}
        </svg>
      </AbsoluteFill>
      <Vignette />
      <Grain />
    </AbsoluteFill>
  );
};

/** A figure counting up inside a ring that draws around it. */
export const StatCounter: React.FC<SceneProps> = ({ image, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();

  const target = num(params, "to", Number(text.replace(/[^0-9.-]/g, "")) || 0);
  const from = num(params, "from", 0);
  const suffix = str(params, "suffix");
  const label = str(params, "label");
  const climb = eased(frame, 6, Math.max(durationInFrames * 0.55, 20), "power2.out");
  const value = Math.round(from + (target - from) * climb);

  const radius = height * 0.24;
  const circumference = 2 * Math.PI * radius;
  const ring = eased(frame, 4, Math.max(durationInFrames * 0.6, 24), "power2.inOut");

  return (
    <AbsoluteFill>
      <Backdrop image={image} zoomFrom={1.04} zoomTo={1.0} dim={0.66} />
      <AbsoluteFill>
        <svg width={width} height={height}>
          <circle
            cx={width / 2}
            cy={height / 2}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.12)"
            strokeWidth={3}
          />
          <circle
            cx={width / 2}
            cy={height / 2}
            r={radius}
            fill="none"
            stroke={accent}
            strokeWidth={3}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - ring)}
            transform={`rotate(-90 ${width / 2} ${height / 2})`}
          />
        </svg>
      </AbsoluteFill>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column" }}>
        <div
          style={{
            ...baseText,
            fontFamily: `${SERIF}, serif`,
            fontSize: height * 0.17,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {value.toLocaleString("en-IN")}
          {suffix}
        </div>
        {label ? (
          <div
            style={{
              ...baseText,
              fontSize: height * 0.032,
              color: "rgba(255,255,255,0.7)",
              letterSpacing: "0.16em",
              marginTop: height * 0.02,
              opacity: eased(frame, 20, 18),
            }}
          >
            {label}
          </div>
        ) : null}
      </AbsoluteFill>
      <Grain />
    </AbsoluteFill>
  );
};

/**
 * Bars growing from a baseline.
 *
 * params: values=40;75;100 labels=1931;1941;1951
 */
export const BarChart: React.FC<SceneProps> = ({ image, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const values = list(params, "values").map(Number).filter(Number.isFinite);
  const labels = list(params, "labels");
  const peak = Math.max(...values, 1);

  const baseline = height * 0.76;
  const maxBarHeight = height * 0.42;
  const slotWidth = (width * 0.7) / Math.max(values.length, 1);
  const startX = width * 0.15;

  return (
    <AbsoluteFill>
      <Backdrop image={image} zoomFrom={1.0} zoomTo={1.03} dim={0.62} />
      <AbsoluteFill>
        <svg width={width} height={height}>
          <line
            x1={startX}
            y1={baseline}
            x2={startX + slotWidth * values.length}
            y2={baseline}
            stroke="rgba(255,255,255,0.3)"
            strokeWidth={2}
          />
          {values.map((value, index) => {
            const grow = eased(frame, 10 + index * 6, 24, "power3.out");
            const barHeight = (value / peak) * maxBarHeight * grow;
            const barWidth = slotWidth * 0.45;
            const x = startX + slotWidth * index + (slotWidth - barWidth) / 2;
            return (
              <g key={index}>
                <rect
                  x={x}
                  y={baseline - barHeight}
                  width={barWidth}
                  height={barHeight}
                  fill={accent}
                  opacity={0.92}
                />
                {labels[index] ? (
                  <text
                    x={x + barWidth / 2}
                    y={baseline + height * 0.05}
                    fill="rgba(255,255,255,0.72)"
                    fontSize={height * 0.026}
                    fontFamily="sans-serif"
                    textAnchor="middle"
                    opacity={grow}
                  >
                    {labels[index]}
                  </text>
                ) : null}
              </g>
            );
          })}
          {text ? (
            <text
              x={startX}
              y={height * 0.2}
              fill="white"
              fontSize={height * 0.05}
              fontFamily={`${SERIF}, serif`}
              opacity={eased(frame, 4, 16)}
            >
              {text}
            </text>
          ) : null}
        </svg>
      </AbsoluteFill>
      <Grain />
    </AbsoluteFill>
  );
};

/**
 * A callout that draws a ring and a leader line onto a point in the picture.
 *
 * params: x=62 y=38 (percentages of the frame)
 */
export const HighlightCallout: React.FC<SceneProps> = ({ image, text, accent, params }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const cx = (num(params, "x", 50) / 100) * width;
  const cy = (num(params, "y", 45) / 100) * height;
  const radius = height * num(params, "r", 0.12);

  const circumference = 2 * Math.PI * radius;
  const draw = eased(frame, 6, 24, "power2.inOut");
  const leaderLength = width * 0.16 * eased(frame, 24, 18, "power3.out");
  const goesLeft = cx > width * 0.55;
  const endX = goesLeft ? cx - radius - leaderLength : cx + radius + leaderLength;

  return (
    <AbsoluteFill>
      <Backdrop image={image} zoomFrom={1.0} zoomTo={1.06} curve="power1.inOut" dim={0.2} />
      <AbsoluteFill>
        <svg width={width} height={height}>
          <circle
            cx={cx}
            cy={cy}
            r={radius}
            fill="none"
            stroke={accent}
            strokeWidth={3}
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - draw)}
            transform={`rotate(-90 ${cx} ${cy})`}
          />
          <line
            x1={goesLeft ? cx - radius : cx + radius}
            y1={cy}
            x2={endX}
            y2={cy}
            stroke={accent}
            strokeWidth={2}
          />
          {text ? (
            <text
              x={endX}
              y={cy - height * 0.018}
              fill="white"
              fontSize={height * 0.034}
              fontFamily="sans-serif"
              textAnchor={goesLeft ? "start" : "end"}
              opacity={eased(frame, 34, 16)}
            >
              {text}
            </text>
          ) : null}
        </svg>
      </AbsoluteFill>
      <Grain opacity={0.05} />
    </AbsoluteFill>
  );
};
