/**
 * The flood simulation drawn over the map: one frame per hour (depth in 2 cm steps on the 30 m grid), blended
 * between hours, and corrected per zone by what the reports say ("physics + reports"). Runs in the browser.
 */
import { demoRoom } from "../../data/room";
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
    const meta = (await fetch("/api/v2/sim", { headers: { "X-Demo-Room": demoRoom() } }).then((r) => r.json())) as SimMeta;
    const buf: ArrayBuffer = await fetch("/api/v2/sim.bin", { headers: { "X-Demo-Room": demoRoom() } }).then((r) => r.arrayBuffer());
    const frames = new Uint8Array(buf);
    const terr = (await fetch("/api/v2/terrain", { headers: { "X-Demo-Room": demoRoom() } }).then((r) => r.json())) as { zDm: number[] };
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

/** Keep the original grid separate so smoothing never changes the underlying measurements. */
const grids = new WeakMap<HTMLCanvasElement, HTMLCanvasElement>();
const BAND_ALPHA = [0.38, 0.46, 0.54, 0.62];

export function floodOpacity(zoom: number) {
  return zoom <= 16 ? 1 : zoom < 18 ? 0.6 : 0.35;
}

interface ZoomMap {
  getZoom: () => number | undefined;
  addListener: (event: string, update: () => void) => { remove: () => void };
}

/** Both report and shelter maps fade the same canvas, with listener cleanup on unmount. */
export function bindFloodZoom(map: ZoomMap, canvas: HTMLCanvasElement) {
  const update = () => { canvas.style.opacity = String(floodOpacity(map.getZoom() ?? 14)); };
  update();
  const listener = map.addListener("zoom_changed", update);
  return () => listener.remove();
}

/** Draw the data grid once, then upsample 4× for the display layer. */
export function drawFlood(
  canvas: HTMLCanvasElement,
  sim: Sim,
  hour: number,
  analysis: Analysis | null,
): { wetCells: number } {
  const { rows, cols, hours, frameBytes, stepM } = sim.meta;
  let grid = grids.get(canvas);
  if (!grid) {
    grid = document.createElement("canvas");
    grids.set(canvas, grid);
  }
  grid.width = cols;
  grid.height = rows;
  canvas.width = cols * 4;
  canvas.height = rows * 4;
  const raw = grid.getContext("2d");
  const ctx = canvas.getContext("2d");
  if (!raw || !ctx) return { wetCells: 0 };
  const img = raw.createImageData(cols, rows);
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
    const band = d < 0.5 ? 0 : d < 1 ? 1 : d < 2 ? 2 : 3;
    const c = pal[band];
    const o = k * 4;
    img.data[o] = c[0];
    img.data[o + 1] = c[1];
    img.data[o + 2] = c[2];
    img.data[o + 3] = Math.round(BAND_ALPHA[band] * 255);
  }
  raw.putImageData(img, 0, 0);
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = "high";
  ctx.filter = "blur(1.5px)";
  ctx.drawImage(grid, 0, 0, canvas.width, canvas.height);
  ctx.filter = "none";
  return { wetCells: wet };
}
