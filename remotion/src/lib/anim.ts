import gsap from "gsap";

/**
 * GSAP supplies the easing curves; Remotion supplies the clock.
 *
 * We never run a GSAP timeline at render time — that would be wall-clock driven
 * and non-deterministic, so two renders of the same frame could differ. Instead
 * we derive a normalised progress from the current frame and push it through
 * `gsap.parseEase`, which is a pure function. Same frame in, same pixel out.
 */

export const clamp = (value: number, min = 0, max = 1): number =>
  Math.min(Math.max(value, min), max);

/** Normalised 0→1 progress of a segment, in frames. */
export const progress = (frame: number, startFrame: number, durationFrames: number): number =>
  durationFrames <= 0 ? 1 : clamp((frame - startFrame) / durationFrames);

const easeCache = new Map<string, (t: number) => number>();

export const easeWith = (name: string, t: number): number => {
  let fn = easeCache.get(name);
  if (!fn) {
    fn = gsap.parseEase(name) as (t: number) => number;
    easeCache.set(name, fn);
  }
  return fn(clamp(t));
};

/** Eased progress in one call — the workhorse of every template. */
export const eased = (
  frame: number,
  startFrame: number,
  durationFrames: number,
  curve = "power3.out",
): number => easeWith(curve, progress(frame, startFrame, durationFrames));

export const interpolateEased = (
  frame: number,
  startFrame: number,
  durationFrames: number,
  from: number,
  to: number,
  curve = "power3.out",
): number => from + (to - from) * eased(frame, startFrame, durationFrames, curve);

/** Fade up, hold, fade out — expressed in frames. */
export const fadeInOut = (
  frame: number,
  totalFrames: number,
  inFrames = 12,
  outFrames = 12,
): number => {
  const rise = eased(frame, 0, inFrames, "power2.out");
  const fall = 1 - eased(frame, totalFrames - outFrames, outFrames, "power2.in");
  return clamp(Math.min(rise, fall));
};

/** Stagger helper: the delay for item `index` in a sequence. */
export const stagger = (index: number, everyFrames: number, offsetFrames = 0): number =>
  offsetFrames + index * everyFrames;

/** Params arrive from the CSV as strings; read them safely. */
export const num = (params: Record<string, string>, key: string, fallback: number): number => {
  const raw = params?.[key];
  if (raw === undefined || raw === "") return fallback;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : fallback;
};

export const str = (params: Record<string, string>, key: string, fallback = ""): string =>
  params?.[key] ?? fallback;

export const list = (params: Record<string, string>, key: string): string[] =>
  str(params, key)
    .split(/[;,]/)
    .map((part) => part.trim())
    .filter(Boolean);
