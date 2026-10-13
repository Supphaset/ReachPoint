import type { Feature, Geometry, Polygon, MultiPolygon, Position } from "geojson";
type Props = Record<string, unknown>;
export type Bounds = [number, number, number, number];

export const W = 1000;

export function rings(g: Geometry): Position[][] {
  if (g.type === "Polygon") return (g as Polygon).coordinates;
  if (g.type === "MultiPolygon") return (g as MultiPolygon).coordinates.flat();
  return [];
}

export function bbox(features: Feature<Geometry, Props>[]): [number, number, number, number] {
  let [x0, y0, x1, y1] = [Infinity, Infinity, -Infinity, -Infinity];
  for (const f of features)
    for (const r of rings(f.geometry))
      for (const [x, y] of r) {
        x0 = Math.min(x0, x);
        y0 = Math.min(y0, y);
        x1 = Math.max(x1, x);
        y1 = Math.max(y1, y);
      }
  return [x0, y0, x1, y1];
}

export function projector([x0, y0, x1, y1]: [number, number, number, number]) {
  const k = Math.cos(((y0 + y1) / 2) * (Math.PI / 180));
  const pad = 0.06;
  const dx = (x1 - x0) * k;
  const dy = y1 - y0;
  const s = W / (dx * (1 + 2 * pad));
  const project = ([x, y]: Position): [number, number] => [(x - x0) * k * s + dx * s * pad, (y1 - y) * s + dy * s * pad];
  const unproject = ([x, y]: Position): [number, number] => [x0 + (x - dx * s * pad) / (k * s), y1 - (y - dy * s * pad) / s];
  return { project, unproject, height: dy * s * (1 + 2 * pad) };
}

export function pathOf(g: Geometry, project: (p: Position) => [number, number]): string {
  return rings(g)
    .map((r) => "M" + r.map((p) => project(p).map((v) => v.toFixed(1)).join(",")).join("L") + "Z")
    .join("");
}


/** SVG path for roads, rivers and canals (LineString / MultiLineString). */
export function lineOf(g: Geometry, project: (p: Position) => [number, number]): string {
  const lines = g.type === "LineString" ? [g.coordinates] : g.type === "MultiLineString" ? g.coordinates : [];
  return lines.map((l) => "M" + l.map((p) => project(p).map((v) => v.toFixed(1)).join(",")).join("L")).join("");
}

/** Point in polygon (outer rings), for "which zone did they tap". */
export function contains(g: Geometry, [x, y]: Position): boolean {
  const polys = g.type === "Polygon" ? [g.coordinates] : g.type === "MultiPolygon" ? g.coordinates : [];
  return polys.some((poly) => {
    const r = poly[0];
    let inside = false;
    for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
      const [xi, yi] = r[i], [xj, yj] = r[j];
      if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
    }
    return inside;
  });
}

/** Inclusive package bbox check; invalid coordinates never pass. */
export function insideBounds([lon, lat]: Position, [west, south, east, north]: Bounds): boolean {
  return Number.isFinite(lon) && Number.isFinite(lat) && lon >= west && lon <= east && lat >= south && lat <= north;
}
