import { describe, expect, it } from "vitest";
import type { GeoView } from "../api";
import { nearestBoundaryPoint } from "./TripMap";
const geo: GeoView = {
  center: [100.47, 7.01],
  zones: {
    type: "FeatureCollection",
    features: [{
      type: "Feature",
      properties: { id: "D12" },
      geometry: {
        type: "Polygon",
        coordinates: [[[100.46, 7.0], [100.48, 7.0], [100.48, 7.02], [100.46, 7.02], [100.46, 7.0]]],
      },
    }],
  },
};
describe("illustrative launch point", () => {
  it("projects onto the nearest boundary segment rather than the map corner or a polygon vertex", () => {
    const point = nearestBoundaryPoint(geo, "D12", { lon: 100.49, lat: 7.01 });
    expect(point?.lon).toBeCloseTo(100.48);
    expect(point?.lat).toBeCloseTo(7.01);
  });
  it("leaves launch unknown when the zone boundary is unavailable", () => {
    expect(nearestBoundaryPoint(geo, "unknown", { lon: 100.49, lat: 7.01 })).toBeNull();
  });
});
