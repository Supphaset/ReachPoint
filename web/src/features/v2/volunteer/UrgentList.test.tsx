import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { vol, type UrgentCase, type UrgentZone } from "../api";
import { sortUrgentZones, UrgentList } from "./UrgentList";

const cases = [{ id: "HH001", priority: 75, hoursSilent: 12, lastHeard: "06:00", depth: null, needs: ["cannotWalk"], markedFirst: { team: "ทีมหนึ่ง", at: "07:00" } }] as UrgentCase[];
const zones: UrgentZone[] = [
  { id: "D1", label: "คลองเตย", sector: "D", plans: 0, depthM: null, score: 100, cases },
  { id: "D2", label: "วัด", sector: "D", plans: 2, depthM: 1.2, score: 90, cases: [{ ...cases[0], id: "HH002", hoursSilent: 4 }] },
  { id: "A1", label: "ตลาด", sector: "A", plans: 1, depthM: 0, score: 80, cases: [{ ...cases[0], id: "HH003", hoursSilent: 20 }] },
];
afterEach(() => vi.unstubAllGlobals());

describe("urgent groups", () => {
  it("preserves server priority order and sorts depth with unknown last, and silence by the longest case", () => {
    expect(sortUrgentZones(zones, "priority").map(zone => zone.id)).toEqual(["D1", "D2", "A1"]);
    expect(sortUrgentZones(zones, "depth").map(zone => zone.id)).toEqual(["D2", "A1", "D1"]);
    expect(sortUrgentZones(zones, "silent").map(zone => zone.id)).toEqual(["A1", "D1", "D2"]);
    expect(zones.map(zone => zone.id)).toEqual(["D1", "D2", "A1"]);
    expect(zones[0].cases).toBe(cases);
  });
  it("shows shared team marks, needs, unknown depth, open links and the highlighted row", () => {
    const html = renderToStaticMarkup(<MemoryRouter><UrgentList data={{ atH: 0, at: "07:00", total: 3, zones }} zones={[]} team="ทีมสอง" busy={false}
      highlighted="HH001" onZone={vi.fn()} onFirst={vi.fn()} /></MemoryRouter>);
    for (const text of ["D1 · คลองเตย", "NO TEAM", "2 ทีม · teams", "Can't walk", "unknown", "Silent</small> 12", "★ ทีมหนึ่ง · 07:00", 'href="/v/case/HH001"', 'aria-pressed="true"', "is-highlighted"]) expect(html).toContain(text.replace("'", "&#x27;"));
    expect(html).toContain("not clinical triage");
  });
  it("sends the current team and explicit on/off state, uses the encoded household route and returns shared state", async () => {
    const payload = { atH: 0, at: "07:00", total: 3, zones };
    const fetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => payload });
    vi.stubGlobal("fetch", fetch);
    expect(await vol.urgent()).toEqual(payload);
    expect(fetch.mock.calls[0][0]).toBe("/api/v2/v/urgent");
    expect(await vol.first("HH/001", "ทีมสอง", true)).toEqual(payload);
    expect(fetch.mock.calls[1][0]).toBe("/api/v2/v/cases/HH%2F001/first");
    expect(JSON.parse(fetch.mock.calls[1][1].body)).toEqual({ team: "ทีมสอง", first: true });
    await vol.first("HH001", "ทีมสอง", false);
    expect(JSON.parse(fetch.mock.calls[2][1].body)).toEqual({ team: "ทีมสอง", first: false });
  });
  it("disables shared marks until a team name is set or while a write is in flight", () => {
    for (const [team, busy] of [["", false], ["ทีมสอง", true]] as const) {
      const html = renderToStaticMarkup(<MemoryRouter><UrgentList data={{ atH: 0, at: "07:00", total: 3, zones }} zones={[]} team={team} busy={busy}
        highlighted={null} onZone={vi.fn()} onFirst={vi.fn()} /></MemoryRouter>);
      expect(html.match(/disabled=""/g)).toHaveLength(3);
    }
  });
});
