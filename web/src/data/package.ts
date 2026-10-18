/** Static geography used by the v2 map; no classic view fixtures are bundled. */
import type { FeatureCollection, Geometry } from "geojson";

export type MapCollection = FeatureCollection<Geometry, Record<string, unknown>>;
const geography = import.meta.glob("../../../data/hy-2025-11/osm-lines.geojson", { query: "?raw", import: "default" });

export async function readPackageFile<T>(name: string): Promise<T> {
  const load = geography[`../../../data/hy-2025-11/${name}`];
  if (!load) throw new Error(`No package file ${name}`);
  return JSON.parse((await load()) as string) as T;
}
