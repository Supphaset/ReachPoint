/**
 * The flood simulation drawn over the map: one frame per hour (depth in 2 cm steps on the 30 m grid), blended
 * between hours, and corrected per zone by what the reports say ("physics + reports"). Runs in the browser.
 */
import { cssVar } from "./api";

export interface SimMeta {
  start: string;
  hours: number;
  rows: number;
  cols: number;
  bbox: [number, number, number, number];
  cellM: number;
  stepM: number;
  frameBytes: number;
  model: string;
}

export interface Analysis {
  atH: number;
  rows: number;
  cols: number;
  incStepM: number;
  wseStepM: number;
  inc: number[];
  wse: number[];
  support: number[];
}

export interface Sim {
  meta: SimMeta;
  frames: Uint8Array;
  zDm: Int16Array; // 30 m ground, decimetres
  zoneOf: Int16Array; // cell → zone index, -1 outside the city zones
  zoneIds: string[];
}

let loading: Promise<Sim> | null = null;

function inside(x: number, y: number, ring: number[][]): boolean {
  let hit = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi + 1e-12) + xi) hit = !hit;
  }
  return hit;
}

export function loadSim(zones: GeoJSON.FeatureCollection): Promise<Sim> {
  return (loading ??= (async () => {
    const meta = (await fetch("/api/v2/sim").then((r) => r.json())) as SimMeta;
    const buf: ArrayBuffer = await fetch("/api/v2/sim.bin").then((r) => r.arrayBuffer());
    const frames = new Uint8Array(buf);
    const terr = (await fetch("/api/v2/terrain").then((r) => r.json())) as { zDm: number[] };
    const zDm = Int16Array.from(terr.zDm);
    const [w, s, e, n] = meta.bbox;
    const zoneIds: string[] = [];
    const polys: { idx: number; rings: number[][][]; box: number[] }[] = [];
    for (const f of zones.features) {
      const id = (f.properties as { id: string }).id;
      const g = f.geometry as GeoJSON.Polygon | GeoJSON.MultiPolygon;
      const rings = g.type === "Polygon" ? [g.coordinates[0]] : g.coordinates.map((p) => p[0]);
      const xs = rings.flat().map((p) => p[0]);
      const ys = rings.flat().map((p) => p[1]);
      polys.push({ idx: zoneIds.length, rings, box: [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)] });
      zoneIds.push(id);
    }
    const zoneOf = new Int16Array(meta.rows * meta.cols).fill(-1);
    for (let i = 0; i < meta.rows; i++) {
      const lat = n - ((i + 0.5) * (n - s)) / meta.rows;
      for (let j = 0; j < meta.cols; j++) {
        const lon = w + ((j + 0.5) * (e - w)) / meta.cols;
        for (const p of polys) {
          if (lon < p.box[0] || lon > p.box[2] || lat < p.box[1] || lat > p.box[3]) continue;
          if (p.rings.some((r) => inside(lon, lat, r))) {
            zoneOf[i * meta.cols + j] = p.idx;
            break;
          }
        }
      }
    }
    return { meta, frames, zoneOf, zoneIds, zDm };
  })().catch((e) => {
    loading = null;
    throw e;
  }));
}

function toRgb(hex: string): [number, number, number] {
  const m = hex.replace("#", "");
  const v = parseInt(m.length === 3 ? m.split("").map((c) => c + c).join("") : m, 16);
  return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
}

/** Draws the water at a (fractional) hour into a canvas the size of the grid. */
export function drawFlood(
  canvas: HTMLCanvasElement,
  sim: Sim,
  hour: number,
  analysis: Analysis | null,
): { wetCells: number } {
  const { rows, cols, hours, frameBytes, stepM } = sim.meta;
  canvas.width = cols;
  canvas.height = rows;
  const ctx = canvas.getContext("2d");
  if (!ctx) return { wetCells: 0 };
  const img = ctx.createImageData(cols, rows);
  const h0 = Math.max(0, Math.min(hours, Math.floor(hour)));
  const h1 = Math.min(hours, h0 + 1);
  const f = Math.max(0, Math.min(1, hour - h0));
  const pal = ["--depth-1", "--depth-2", "--depth-3", "--depth-4"].map((v) => toRgb(cssVar(v)));
  const a = analysis && analysis.rows > 0 ? analysis : null;
  let wet = 0;
  for (let k = 0; k < rows * cols; k++) {
    let d = (sim.frames[h0 * frameBytes + k] * (1 - f) + sim.frames[h1 * frameBytes + k] * f) * stepM;
    if (a) {
      // the lattice cell this 30 m cell sits in
      const li = Math.min(a.rows - 1, Math.floor(((k / cols) | 0) * a.rows / rows));
      const lj = Math.min(a.cols - 1, Math.floor((k % cols) * a.cols / cols));
      const q = li * a.cols + lj;
      const sup = a.support[q] / 100;
      if (d > 0.05) d = Math.max(0, d + a.inc[q] * a.incStepM * sup);
      else if (sup > 0.35 && a.wse[q] > 0 && sim.zDm[k] > -9999) d = Math.min(6, Math.max(0, a.wse[q] * a.wseStepM - sim.zDm[k] / 10));
    }
    if (d <= 0.08) continue;
    wet++;
    const c = d < 0.5 ? pal[0] : d < 1 ? pal[1] : d < 2 ? pal[2] : pal[3];
    const o = k * 4;
    img.data[o] = c[0];
    img.data[o + 1] = c[1];
    img.data[o + 2] = c[2];
    img.data[o + 3] = Math.min(220, 110 + d * 60);
  }
  ctx.putImageData(img, 0, 0);
  return { wetCells: wet };
}
