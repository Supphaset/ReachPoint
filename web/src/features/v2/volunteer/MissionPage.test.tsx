import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CaseRow, ZonePage as ZoneDetail } from "../api";
import { UiLangProvider } from "../ui/lang";
import { MissionPage } from "./MissionPage";

const state = vi.hoisted(() => ({ data: null as ZoneDetail | null, mission: null as import("./mission").Mission | null }));
vi.mock("./shared", async original => ({
  ...await original<typeof import("./shared")>(),
  VShell: ({ title, children }: { title: string; children: React.ReactNode }) => <main><h1>{title}</h1>{children}</main>,
  useLive: () => ({ data: state.data, error: null, reload: vi.fn() }),
  useGeo: () => null,
  useTeam: () => ["Boat 1", vi.fn()],
}));
vi.mock("./mission", async original => ({ ...await original<typeof import("./mission")>(), useMission: () => state.mission }));
vi.mock("./MissionMap", () => ({ MissionMap: () => <div data-map /> }));
const base = { zoneId: "D1", lon: 100.47, lat: 7.01, people: 3, elderly: 1, children: 0, cannotWalk: 0, urgent: false,
  status: "open", needs: ["cannotWalk"], depth: { m: 1.4, lo: 1.2, hi: 1.6, reports: 2 }, boat: true,
  messages: 1, lastHeard: "06:00", hoursSilent: 2, firstHand: true, possibleDuplicateOf: null, outcome: null, reportedBy: "self" };
const households = [
  { ...base, id: "HH-WAIT", priority: 30 },
  { ...base, id: "HH-DONE", priority: 200, status: "evacuated", outcome: { kind: "pickedUp", team: "Boat 2", at: "07:00" } },
  { ...base, id: "HH-URGENT", priority: 130, urgent: true, cannotWalk: 1 },
] as CaseRow[];
const data = { zone: { id: "D1", label: "ตลาด", labelEn: "Talat" }, households, now: { atH: 2, at: "08:00" } } as ZoneDetail;
function render(lang: "th" | "en") {
  return renderToStaticMarkup(<UiLangProvider initialLang={lang}><MemoryRouter initialEntries={["/v/mission/D1"]}><Routes><Route path="/v/mission/:zoneId" element={<MissionPage />} /></Routes></MemoryRouter></UiLangProvider>);
}
afterEach(() => { state.data = null; state.mission = null; });
describe("mission page", () => {
  it.each(["th", "en"] as const)("renders sample zone cards in visiting order in %s", lang => {
    state.data = data;
    state.mission = { zoneId: "D1", team: "Boat 1", vehicle: "boat", seats: 4, eta: "12:00", told: 2, at: "07:00" };
    const html = render(lang);
    expect(html).toContain(lang === "en" ? "D1 · Talat" : "D1 · ตลาด");
    expect(html.indexOf('data-house="HH-URGENT"')).toBeLessThan(html.indexOf('data-house="HH-WAIT"'));
    expect(html.indexOf('data-house="HH-WAIT"')).toBeLessThan(html.indexOf('data-house="HH-DONE"'));
    expect(html).toContain('mission-number is-urgent">1</span>');
    expect(html).toContain('mission-number is-waiting">2</span>');
    expect(html).toContain('mission-number is-done">✓</span>');
    expect(html).toContain('target="_blank" rel="noopener noreferrer"');
    expect(html).toContain('href="/v/case/HH-URGENT"');
    expect(html).toContain("destination=7.01,100.47");
    expect(html).toContain(lang === "th" ? "เรียบร้อย 1 จาก 3 บ้าน" : "1 of 3 houses done");
    expect(html).toContain(lang === "th" ? "แจ้ง 2 ครอบครัวแล้วว่าทีมกำลังมา" : "2 families told a team is coming");
    for (const label of lang === "th" ? ["นำทาง", "รับตัวแล้ว", "ไม่มีคนอยู่", "พาไปศูนย์พักพิง", "เงียบ 2 ชม."] : ["Directions", "Picked up", "Nobody there", "Taken to shelter", "2 hours silent"]) expect(html).toContain(label);
    expect(html).not.toContain(lang === "th" ? ">ยืนยัน<" : ">Confirm<");
    if (lang === "en") expect(html).not.toMatch(/[฀-๿]/);
  });
  it("shows the requested zone without a different mission's team details", () => {
    state.data = data;
    state.mission = { zoneId: "OTHER", team: "Different team", vehicle: "boat", seats: 8, eta: "17:00", told: 99, at: "07:00" };
    const html = render("en");
    expect(html).toContain("Mission: D1");
    expect(html).not.toContain("Different team");
    expect(html).not.toContain("99 families");
  });
  it("offers another zone when every house is done and retains completed outcomes", () => {
    state.data = { ...data, households: [households[1]] };
    const html = render("en");
    expect(html).toContain("Every house in this zone is done");
    expect(html).toContain('href="/v"');
    expect(html).toContain("Picked up");
  });
});
