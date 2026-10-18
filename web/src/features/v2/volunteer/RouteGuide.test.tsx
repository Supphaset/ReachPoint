import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { MissionRoute } from "../api";
import { UiLangProvider } from "../ui/lang";
import { RouteGuide, runDirections } from "./RouteGuide";

const base: MissionRoute = {
  vehicle: "truck", seats: 4, start: { lon: 100.4, lat: 7, label: "Start" },
  totals: { km: 2, minutes: 10 }, deepestM: .8, now: { at: "06:00", atH: 96 },
  warnings: ["direct line, check on the ground"], unreachable: [],
  runs: [{ run: 1, stops: ["H1", "H2"], start: { lon: 100.4, lat: 7, label: "Start" },
    shelter: { id: "S1", name: "ศูนย์", nameEn: "Shelter", lon: 100.5, lat: 7.1 }, totals: { km: 2, minutes: 10 },
    legs: [{ from: "start", to: "H1", path: [[100.4, 7], [100.41, 7.01]], km: .5, minutes: 2.5, deepestM: .8,
      samples: [[100.4, 7, .8]], warnings: [], warningAt: [100.4, 7] },
    { from: "H1", to: "H2", path: [[100.41, 7.01], [100.42, 7.02]], km: .6, minutes: 3, deepestM: .4,
      samples: [[100.42, 7.02, .4]], warnings: [], warningAt: [100.42, 7.02] }] }],
};
function render(route: MissionRoute, lang: "en" | "th" = "en") {
  return renderToStaticMarkup(<UiLangProvider initialLang={lang}><RouteGuide route={route} /></UiLangProvider>);
}
describe("mission water routes", () => {
  it.each(["truck", "foot"])("renders legs, warnings and whole-run Google directions for %s", vehicle => {
    const route = { ...base, vehicle };
    const html = render(route);
    expect(html).toContain("Run 1"); expect(html).toContain("H1"); expect(html).toContain("H2");
    expect(html).toContain("0.5 km"); expect(html).toContain("2.5 min · deepest 0.8 m");
    expect(html).toContain("direct line, check on the ground");
    expect(html).toContain("Route from the flood model at 06:00; check on the ground.");
    const link = runDirections(route, route.runs[0]);
    expect(link).toContain("origin=7,100.4"); expect(link).toContain("destination=7.1,100.5");
    expect(link).toContain("waypoints=7.01,100.41|7.02,100.42");
    expect(link).toContain(`travelmode=${vehicle === "foot" ? "walking" : "driving"}`);
    expect(html).not.toMatch(/[ก-๿]/);
  });
  it("gives boat guidance and only a launch Google link", () => {
    const html = render({ ...base, vehicle: "boat" });
    expect(html).toContain("Google can&#x27;t route boats");
    expect(html).toContain("Directions to launch only");
    expect(html).toContain("destination=7,100.4");
    expect(html).not.toContain("waypoints="); expect(html).not.toContain("Open the whole run");
  });
  it("translates model guidance and warnings into Thai", () => {
    const html = render(base, "th");
    expect(html).toContain("เส้นทางจากแบบจำลองน้ำท่วม");
    expect(html).toContain("เส้นตรง โปรดตรวจสอบหน้างาน");
  });
  it("caps Google waypoints at nine", () => {
    const run = { ...base.runs[0], stops: Array.from({ length: 12 }, (_, i) => `H${i}`),
      legs: Array.from({ length: 12 }, (_, i) => ({ ...base.runs[0].legs[0], to: `H${i}` })) };
    expect(runDirections(base, run)?.split("waypoints=")[1].split("&")[0].split("|")).toHaveLength(9);
  });
});
