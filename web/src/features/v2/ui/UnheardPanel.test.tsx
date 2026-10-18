import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { UiLangProvider } from "./lang";
import { UnheardPanel } from "./UnheardPanel";
import type { Unheard } from "../api";

export const unheard: Unheard = { estimatedHouseholds: [10, 20], heardFrom: 2, notHeard: [8, 18], quiet: true, atH: 96,
  basis: "estimated from the flood model and building outlines, not reports",
  streets: [{ name: "ถนนเพชรเกษม", nameEn: "Thanon Phetkasem", depthM: 1.2, floodedBuildings: 12, lon: 100.47, lat: 7.01 }] };
describe("unheard panels", () => {
  it.each(["th", "en"] as const)("explains estimates, streets and spare seats in %s", lang => {
    const html = renderToStaticMarkup(<UiLangProvider initialLang={lang}><UnheardPanel unheard={unheard} seats={2} /></UiLangProvider>);
    for (const text of lang === "en" ? ["Not heard from yet", "8–18 households", "10–20", "building outlines, not reports", "Thanon Phetkasem", "1.2 m", "Keep 2 seats free"] : ["ยังไม่ได้ติดต่อ", "8–18", "ถนนเพชรเกษม", "เว้น 2 ที่นั่ง"]) expect(html).toContain(text);
    if (lang === "en") expect(html).not.toMatch(/[฀-๿]/);
  });
  it("shows mission directions and a household range", () => {
    const html = renderToStaticMarkup(<UiLangProvider initialLang="en"><UnheardPanel unheard={unheard} mission /></UiLangProvider>);
    expect(html).toContain("Also check on the way · estimated, no request yet");
    expect(html).toContain("8–18 households");
    expect(html).toContain("destination=7.01,100.47");
    expect(html).toContain("Directions");
  });
  it("explains a full boat and preserves building evidence when household estimates are unknown", () => {
    const render = (u: Unheard | undefined, seats = 0) => renderToStaticMarkup(<UiLangProvider initialLang="en"><UnheardPanel unheard={u} seats={seats} /></UiLangProvider>);
    expect(render(unheard)).toContain("Requests already fill the boat; no spare seats.");
    expect(render({ ...unheard, notHeard: null })).toContain("12 flooded buildings");
    expect(render({ ...unheard, streets: [], notHeard: [0, 0] })).toBe("");
    expect(render(undefined)).toBe("");
  });
});
