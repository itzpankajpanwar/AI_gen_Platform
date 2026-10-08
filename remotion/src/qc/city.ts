/**
 * One city, generated once, used by every map in the film.
 *
 * Chapters 3, 8, 9, 11 and 14 all look at the same streets from the same
 * angle, because they are literally the same geometry with a different
 * camera and a different overlay. That is what stops the map sequences
 * feeling like five unrelated graphics — the single most important
 * continuity decision in the picture.
 *
 * Projection is a true 2:1 axonometric, lit from one fixed direction, so
 * extruded blocks read as an architectural model rather than a game map.
 */
import { rng } from "./theme";

export const W = 1000;          // world is a W x W square
export type Pt = { x: number; y: number };

export interface Building { x: number; y: number; w: number; d: number; h: number; k: number }
export interface Road { x1: number; y1: number; x2: number; y2: number; w: number; arterial: boolean }
export interface Store { id: number; p: Pt; label: string }
export interface Rider { id: number; p: Pt; busy: number }

export interface City {
  roads: Road[];
  buildings: Building[];
  stores: Store[];
  riders: Rider[];
  customer: Pt;
  /** road-following polyline from a store to the customer */
  route: (from: Pt, to: Pt, detour?: boolean) => Pt[];
  gridX: number[];
  gridY: number[];
}

/** 2:1 axonometric with a fixed camera. h raises a point off the ground. */
export const iso = (x: number, y: number, h = 0) => ({
  x: (x - y) * 0.866,
  y: (x + y) * 0.5 - h,
});

const SEED = 20251008;

export const buildCity = (): City => {
  const r = rng(SEED);

  // --- irregular street grid: a few arterials, the rest local streets
  const lines = (count: number) => {
    const out: number[] = [0];
    let v = 0;
    for (let i = 0; i < count; i++) {
      v += 62 + r() * 58;              // 62-120 unit blocks: dense, Indian
      if (v > W - 40) break;
      out.push(Math.round(v));
    }
    out.push(W);
    return out;
  };
  const gridX = lines(14);
  const gridY = lines(14);

  // Two arterials each way, wider and brighter — the roads the riders use.
  const artX = [gridX[Math.floor(gridX.length * 0.33)], gridX[Math.floor(gridX.length * 0.72)]];
  const artY = [gridY[Math.floor(gridY.length * 0.28)], gridY[Math.floor(gridY.length * 0.66)]];

  const roads: Road[] = [];
  for (const x of gridX) {
    const arterial = artX.includes(x);
    roads.push({ x1: x, y1: 0, x2: x, y2: W, w: arterial ? 15 : 7, arterial });
  }
  for (const y of gridY) {
    const arterial = artY.includes(y);
    roads.push({ x1: 0, y1: y, x2: W, y2: y, w: arterial ? 15 : 7, arterial });
  }

  // --- fill each block with lots, leave a few blocks open (parks, grounds)
  const buildings: Building[] = [];
  for (let i = 0; i < gridX.length - 1; i++) {
    for (let j = 0; j < gridY.length - 1; j++) {
      const x0 = gridX[i] + 6, x1 = gridX[i + 1] - 6;
      const y0 = gridY[j] + 6, y1 = gridY[j + 1] - 6;
      const bw = x1 - x0, bd = y1 - y0;
      if (bw < 24 || bd < 24) continue;
      if (r() < 0.07) continue;                       // open ground

      // Denser, taller towards the middle of the city.
      const cx = (x0 + x1) / 2 - W / 2, cy = (y0 + y1) / 2 - W / 2;
      const core = 1 - Math.min(1, Math.hypot(cx, cy) / (W * 0.62));

      const cols = Math.max(1, Math.round(bw / (26 + r() * 16)));
      const rows = Math.max(1, Math.round(bd / (26 + r() * 16)));
      for (let a = 0; a < cols; a++) {
        for (let b = 0; b < rows; b++) {
          if (r() < 0.1) continue;                    // gaps, lanes, courtyards
          const lw = bw / cols, ld = bd / rows;
          const pad = 1.4 + r() * 2.2;
          const h = (7 + r() * 16) * (0.55 + core * 1.5) * (r() < 0.07 ? 2.1 : 1);
          buildings.push({
            x: x0 + a * lw + pad,
            y: y0 + b * ld + pad,
            w: Math.max(6, lw - pad * 2),
            d: Math.max(6, ld - pad * 2),
            h,
            k: r(),                                   // per-building shade jitter
          });
        }
      }
    }
  }
  // Painter's algorithm: far blocks first, so near ones overlap correctly.
  buildings.sort((a, b) => a.x + a.y - (b.x + b.y));

  // --- the fixed cast of the film. Positions are authored, not random:
  // store 4 wins in ch3, rider 7 wins in ch8, and the customer is the flat.
  const snap = (v: number, g: number[]) =>
    g.reduce((best, c) => (Math.abs(c - v) < Math.abs(best - v) ? c : best), g[0]);

  // Placed so chapter 3's three candidates frame together around the customer
  // AND so the drawn distances agree with the figures spoken over them:
  // at ~6.7 m per world unit, store 4 is 1.4 km out, store 2 is 2.1 km, and
  // store 3 — the one that loses on stock — really is the closest at 0.6 km.
  const storePts: [number, number][] = [
    [205, 250],   // 1  background
    [430, 230],   // 2  candidate: busy, 19 queued
    [600, 350],   // 3  candidate: closest, but 3 of 4 in stock
    [790, 560],   // 4  candidate: wins on estimated delivery
    [250, 690],   // 5  background
    [880, 760],   // 6  background
  ];
  const stores: Store[] = storePts.map((p, i) => ({
    id: i + 1,
    p: { x: snap(p[0], gridX) + 18, y: snap(p[1], gridY) + 18 },
    label: `STORE ${String(i + 1).padStart(2, "0")}`,
  }));

  const customer: Pt = { x: snap(640, gridX) + 20, y: snap(430, gridY) + 22 };

  // Rider 7 is the one dispatched in chapter 8 — parked ~400 m from store 4.
  const riders: Rider[] = [
    [600, 520], [520, 300], [700, 430], [430, 470], [820, 650], [350, 560],
    [745, 505], [760, 220], [300, 380], [880, 420], [470, 680], [690, 740],
  ].map((p, i) => ({
    id: i + 1,
    p: { x: p[0], y: p[1] },
    busy: i % 3 === 0 ? 0 : i % 3,
  }));

  /**
   * A path that stays on the street grid: out to the nearest avenue, along
   * it, then in. `detour` swings via a different avenue — that is the ch9
   * reroute, so both routes are real paths through the same city.
   */
  const route = (from: Pt, to: Pt, detour = false): Pt[] => {
    const ax = snap(detour ? (from.x + to.x) / 2 + 95 : (from.x + to.x) / 2, gridX);
    const ay = snap(detour ? to.y - 70 : (from.y + to.y) / 2, gridY);
    return [
      { x: from.x, y: from.y },
      { x: from.x, y: ay },
      { x: ax, y: ay },
      { x: ax, y: to.y },
      { x: to.x, y: to.y },
    ];
  };

  return { roads, buildings, stores, riders, customer, route, gridX, gridY };
};

/** Built once per render process, not per frame. */
let cached: City | null = null;
export const city = (): City => (cached ??= buildCity());

/** Polyline length and point-at-distance, for drawing a route progressively. */
export const polyLen = (pts: Pt[]) => {
  let L = 0;
  for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
  return L;
};
export const pointAt = (pts: Pt[], t: number): Pt => {
  const total = polyLen(pts);
  let want = total * Math.max(0, Math.min(1, t));
  for (let i = 1; i < pts.length; i++) {
    const seg = Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
    if (want <= seg || i === pts.length - 1) {
      const k = seg === 0 ? 0 : want / seg;
      return { x: pts[i - 1].x + (pts[i].x - pts[i - 1].x) * k,
               y: pts[i - 1].y + (pts[i].y - pts[i - 1].y) * k };
    }
    want -= seg;
  }
  return pts[pts.length - 1];
};
