import areasRaw from "../../../data/hy-2025-11/areas.geojson?raw";
import zonesRaw from "../../../data/hy-2025-11/zones.geojson?raw";
import { afterEach, describe, expect, it, vi } from "vitest";
import { bbox, insideBounds, projector } from "./mapGeometry";
import type { MapCollection } from "./locationMap";
import { demoBounds } from "./locationMap";
import { deviceLocation } from "./deviceLocation";
import { approveReport, locate, sendRequest, type Approval } from "./intake";
import type { LocationInput } from "./contract";

const areas = JSON.parse(areasRaw) as MapCollection;
const zones = JSON.parse(zonesRaw) as MapCollection;
const input: LocationInput = { kind: "pin", lat: 7.0089, lon: 100.4705, method: "gps", accuracyM: 25 };
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });
describe("demo location geometry", () => {
  it("loads areas through the package source and accepts inside/boundary points, never outside or invalid points", async () => {
    const bounds = bbox(areas.features);
    expect(await demoBounds()).toEqual(bounds);
    const [west, south, east, north] = bounds;
    expect(insideBounds([100.4705, 7.0089], bounds)).toBe(true);
    expect(insideBounds([west, south], bounds)).toBe(true);
    expect(insideBounds([east, north], bounds)).toBe(true);
    expect(insideBounds([west - .00001, south], bounds)).toBe(false);
    expect(insideBounds([east + .00001, north], bounds)).toBe(false);
    expect(insideBounds([west, south - .00001], bounds)).toBe(false);
    expect(insideBounds([east, north + .00001], bounds)).toBe(false);
    expect(insideBounds([NaN, south], bounds)).toBe(false);
    expect(insideBounds([Infinity, south], bounds)).toBe(false);
  });
  it("round trips lon/lat and SVG pixels for the whole area and every zoomed zone", () => {
    for (const bounds of [bbox(areas.features), ...zones.features.map(f => bbox([f]))]) {
      const { project, unproject, height } = projector(bounds);
      for (const at of [[bounds[0], bounds[1]], [bounds[2], bounds[3]], [100.4705, 7.0089]]) {
        const round = unproject(project(at));
        expect(round[0]).toBeCloseTo(at[0], 10);
        expect(round[1]).toBeCloseTo(at[1], 10);
      }
      for (const pixel of [[0, 0], [500, height / 2], [1000, height]]) {
        const round = project(unproject(pixel));
        expect(round[0]).toBeCloseTo(pixel[0], 8);
        expect(round[1]).toBeCloseTo(pixel[1], 8);
      }
    }
  });
  it("uses high-accuracy GPS and rejects an outside point without exposing it in a result or fetching", async () => {
    const fetch = vi.fn(); vi.stubGlobal("fetch", fetch);
    const gps = vi.fn((success: PositionCallback, _error?: PositionErrorCallback, _options?: PositionOptions) => success({ coords: { latitude: 13.7, longitude: 100.5, accuracy: 25 } } as GeolocationPosition));
    vi.stubGlobal("navigator", { geolocation: { getCurrentPosition: gps } });
    expect(await deviceLocation()).toEqual({ ok: false, reason: "outside" });
    expect(gps.mock.calls[0][2]).toEqual({ enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
    expect(fetch).not.toHaveBeenCalled();
    gps.mockImplementation(success => success({ coords: { latitude: 7.0089, longitude: 100.4705, accuracy: 25 } } as GeolocationPosition));
    expect(await deviceLocation()).toEqual({ ok: true, input });
  });
  it.each([[1, "denied"], [2, "unavailable"], [3, "timeout"]])("gives a usable fallback for GPS error %s", async (code, reason) => {
    vi.stubGlobal("navigator", { geolocation: { getCurrentPosition: (_: unknown, error: (e: { code: number }) => void) => error({ code: Number(code) }) } });
    expect(await deviceLocation()).toEqual({ ok: false, reason });
  });
});
describe("D25 API payloads", () => {
  it("sends location on intake and approval, and uses a read-only locate preview without a submissionId", async () => {
    vi.stubEnv("VITE_DATA", "api");
    const fetch = vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ value: { reportId: "R-demo", statusUrl: "/status/demo", aiSource: "fixture" } }) }));
    vi.stubGlobal("fetch", fetch);
    await locate(input);
    await sendRequest("Synthetic request", input);
    const approval: Approval = { segmentId: "B-3-L2", people: { adults: 1, children: 0, infants: 0, stretcher: 0 }, needs: ["supplies"], waterBand: null, urgentReason: null, deskNote: null, location: { kind: "address", text: "L2 Market" } };
    await approveReport("R-demo", approval);
    const calls = fetch.mock.calls as unknown as [string, RequestInit][];
    expect(calls.map(c => c[0])).toEqual(["/api/locate", "/api/intake/text", "/api/reports/R-demo/approve"]);
    const bodies = calls.map(c => JSON.parse(String(c[1].body)));
    expect(bodies[0]).toEqual({ location: input });
    expect(bodies[1]).toMatchObject({ text: "Synthetic request", channel: "text", location: input });
    expect(bodies[2]).toMatchObject(approval);
    expect(bodies[1].submissionId).toMatch(/^SUB-/);
    expect(bodies[2].submissionId).toMatch(/^SUB-/);
    await sendRequest("No location");
    expect(JSON.parse(String((fetch.mock.calls as unknown as [string, RequestInit][])[3][1].body))).not.toHaveProperty("location");
  });
  it("requires the server in fixtures without fetching", async () => {
    vi.stubEnv("VITE_DATA", "fixtures"); const fetch = vi.fn(); vi.stubGlobal("fetch", fetch);
    expect(await locate(input)).toMatchObject({ ok: false, message: expect.stringContaining("needs the server") });
    expect(fetch).not.toHaveBeenCalled();
  });
});
