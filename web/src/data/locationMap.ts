import type { FeatureCollection, Geometry } from "geojson";
import { bbox, type Bounds } from "./mapGeometry";
import { readPackageFile } from "./source";

export type MapCollection = FeatureCollection<Geometry, Record<string, unknown>>;
export interface LocationLayers { zones: MapCollection; segments: MapCollection; landmarks: MapCollection; bounds: Bounds }
let areaBounds: Promise<Bounds> | undefined;
let layers: Promise<LocationLayers> | undefined;

/** Compute the demo-area bbox once, on the device. A failed load may be retried. */
export function demoBounds(): Promise<Bounds> {
  return areaBounds ??= readPackageFile<MapCollection>("areas.geojson")
    .then(areas => bbox(areas.features))
    .catch(e => { areaBounds = undefined; throw e; });
}
export function locationLayers(): Promise<LocationLayers> {
  return layers ??= Promise.all([
    readPackageFile<MapCollection>("zones.geojson"),
    readPackageFile<MapCollection>("segments.geojson"),
    readPackageFile<MapCollection>("landmarks.geojson"), demoBounds(),
  ]).then(([zones, segments, landmarks, bounds]) => ({ zones, segments, landmarks, bounds }))
    .catch(e => { layers = undefined; throw e; });
}
