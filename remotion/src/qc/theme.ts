/**
 * THE TEN MINUTES — the film's graphic design system.
 *
 * Two colours carry the whole documentary and they carry meaning, not
 * decoration: SYSTEM is the algorithm looking at the world, HUMAN is the
 * world it is looking at. Nothing else is introduced, so a graphic in
 * chapter 12 reads as the same film as a graphic in chapter 2.
 */

export const C = {
  system: "#4DA3FF",      // data, UI, optimisation, the machine
  systemDim: "#2E6BA8",
  human: "#E8A33D",       // sodium light, the street, human labour
  humanDim: "#8A6224",
  ink: "#07080A",         // base
  ink2: "#0C1016",        // panel
  ink3: "#141A22",        // raised panel
  line: "#243040",        // hairline
  lineSoft: "#1A222C",
  text: "#E8EEF5",
  textDim: "#8A99AB",
  textFaint: "#4A5869",
  paper: "#EDF1F5",
  bad: "#D4574E",         // used exactly twice in the film, both in ch12
  good: "#5FB08A",
} as const;

export const DISPLAY = "InterDisplay";
export const SANS = "InterSans";

/** Type scale, as a fraction of frame height, so it is resolution-free. */
export const T = {
  hero: 0.095,
  title: 0.058,
  big: 0.044,
  num: 0.034,
  body: 0.021,
  label: 0.0145,
  micro: 0.0118,
} as const;

/** Letter-spacing for the all-caps label style used throughout. */
export const TRACK = "0.16em";

export const mono: React.CSSProperties = {
  fontFamily: `${SANS}, sans-serif`,
  fontVariantNumeric: "tabular-nums",
  fontFeatureSettings: '"tnum" 1, "ss01" 1',
};

export const label: React.CSSProperties = {
  ...mono,
  textTransform: "uppercase",
  letterSpacing: TRACK,
  color: C.textDim,
  fontWeight: 500,
};

/** Deterministic PRNG. The city must be the same city in every chapter. */
export const rng = (seed: number) => () => {
  seed |= 0;
  seed = (seed + 0x6d2b79f5) | 0;
  let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const clamp01 = (v: number) => (v < 0 ? 0 : v > 1 ? 1 : v);

/** Split a `|`-separated params string. The CSV layer keeps commas for lists. */
export const pipes = (raw: string | undefined): string[] =>
  (raw ?? "").split("|").map((s) => s.trim()).filter(Boolean);
