import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { vol, type UrgentCase, type UrgentZone } from "../api";
import { UiLangProvider } from "../ui/lang";
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
    for (const text of ["D1 · คลองเตย", "NO TEAM", "2 ทีม · teams", "เดินไม่ได้", "unknown", "เงียบ 12 ชม.", "★ ทีมหนึ่ง", 'href="/v/case/HH001"', 'aria-pressed="true"', "is-highlighted"]) expect(html).toContain(text.replace("'", "&#x27;"));
    expect(html).toContain("ไม่ใช่การคัดแยกทางคลินิก");
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
  it("keeps the team-name action enabled, but disables marks during a write", () => {
    const html = renderToStaticMarkup(<UiLangProvider initialLang="en"><MemoryRouter><UrgentList data={{ atH: 0, at: "07:00", total: 3, zones }} zones={[]} team="" busy={false}
      highlighted={null} onZone={vi.fn()} onFirst={vi.fn()} /></MemoryRouter></UiLangProvider>);
    expect(html).toContain("Set your team name to mark cases");
    expect(html).not.toContain('disabled=""');
    const busyHtml = renderToStaticMarkup(<MemoryRouter><UrgentList data={{ atH: 0, at: "07:00", total: 3, zones }} zones={[]} team="ทีมสอง" busy
      highlighted={null} onZone={vi.fn()} onFirst={vi.fn()} /></MemoryRouter>);
    expect(busyHtml.match(/disabled=""/g)).toHaveLength(3);
  });
  it("initially limits the list to six zone groups and labels the remaining count", () => {
    const many = Array.from({ length: 9 }, (_, index) => ({ ...zones[0], id: `Z${index}`, cases: [{ ...cases[0], id: `HH${index}` }] }));
    const html = renderToStaticMarkup(<UiLangProvider initialLang="en"><MemoryRouter><UrgentList data={{ atH: 0, at: "07:00", total: 9, zones: many }} zones={[]} team="Boat" busy={false}
      highlighted={null} onZone={vi.fn()} onFirst={vi.fn()} /></MemoryRouter></UiLangProvider>);
    expect(html.match(/class="v-urgent-zone"/g)).toHaveLength(6);
    expect(html).not.toContain('data-case="HH6"');
    expect(html).toContain('aria-expanded="false"');
    expect(html).toContain("Show 3 more zones");
  });
});
