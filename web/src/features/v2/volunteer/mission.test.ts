import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { CaseRow } from "../api";
import { directionsUrl, isDone, loadMission, MISSION_KEY, saveMission, visitingOrder, type Mission } from "./mission";

const mission: Mission = { zoneId: "D1", team: "Boat 1", vehicle: "boat", seats: 4, eta: "12:00", told: 6, at: "07:00" };
beforeEach(() => {
  const values = new Map<string, string>();
  vi.stubGlobal("localStorage", { getItem: vi.fn((key: string) => values.get(key) ?? null), setItem: vi.fn((key: string, value: string) => values.set(key, value)) });
  vi.stubGlobal("window", { dispatchEvent: vi.fn() });
  saveMission(mission);
  values.clear();
  vi.clearAllMocks();
});
afterEach(() => vi.unstubAllGlobals());
describe("current mission", () => {
  it("saves and loads the full mission and announces the update", () => {
    expect(loadMission()).toBeNull();
    saveMission(mission);
    expect(localStorage.setItem).toHaveBeenCalledWith(MISSION_KEY, JSON.stringify(mission));
    expect(loadMission()).toEqual(mission);
    expect(window.dispatchEvent).toHaveBeenCalledWith(expect.objectContaining({ type: "reachpoint-mission" }));
  });
  it("rejects invalid saved records", () => {
    for (const raw of ["{", "null", "{}", JSON.stringify({ ...mission, seats: "4" }), JSON.stringify({ ...mission, told: -1 })]) {
      localStorage.setItem(MISSION_KEY, raw);
      expect(loadMission()).toBeNull();
    }
  });
  it("uses the new mission when writes fail but reads still return an older mission", () => {
    saveMission(mission);
    vi.mocked(localStorage.setItem).mockImplementation(() => { throw Error("quota"); });
    saveMission({ ...mission, zoneId: "D2" });
    expect(loadMission()?.zoneId).toBe("D2");
  });
  it("continues in memory when storage is denied", () => {
    vi.stubGlobal("localStorage", { getItem: () => { throw Error("denied"); }, setItem: () => { throw Error("denied"); } });
    expect(() => saveMission(mission)).not.toThrow();
    expect(loadMission()).toEqual(mission);
  });
});
describe("visiting order", () => {
  it("puts open households first by priority, with urgent and mobility tie breaks; done last", () => {
    const rows = [
      { id: "done", status: "evacuated", priority: 500 },
      { id: "waiting", status: "open", priority: 30 },
      { id: "silent", status: "lostContact", priority: 60 },
      { id: "urgent", status: "open", urgent: true, priority: 130 },
      { id: "urgent-mobility", status: "open", urgent: true, cannotWalk: 1, priority: 130 },
      { id: "shelter", status: "atShelter", priority: 10 },
    ].map(row => ({ urgent: false, cannotWalk: 0, ...row })) as CaseRow[];
    expect(visitingOrder(rows).map(row => row.id)).toEqual(["urgent-mobility", "urgent", "silent", "waiting", "done", "shelter"]);
    expect(rows[0].id).toBe("done");
    for (const status of ["safe", "evacuated", "nobodyThere", "atShelter"] as const) expect(isDone({ status } as CaseRow)).toBe(true);
    expect(isDone({ status: "toShelter" } as CaseRow)).toBe(false);
  });
});
describe("directions", () => {
  it("uses latitude before longitude and requests driving directions", () => {
    expect(directionsUrl(7.01, 100.47)).toBe("https://www.google.com/maps/dir/?api=1&destination=7.01,100.47&travelmode=driving");
    expect(directionsUrl(0, 0)).toContain("destination=0,0");
  });
  it("does not invent a destination when coordinates are missing or invalid", () => {
    for (const [lat, lon] of [[null, 100], [7, null], [NaN, 100], [91, 100], [7, 181]]) expect(directionsUrl(lat, lon)).toBeNull();
  });
});
