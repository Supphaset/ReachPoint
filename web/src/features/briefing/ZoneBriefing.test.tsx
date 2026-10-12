import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { AreaBriefingView } from "../../data/contract";
import normal from "../../../../contract/fixtures/areaBriefing.P-B.json";
import { ZoneBriefing } from "./ZoneBriefing";

const area = normal as unknown as AreaBriefingView;
const zone = (id: string) => area.zones.find((z) => z.zoneId === id)!;
const html = (id: string) => renderToStaticMarkup(<ZoneBriefing zone={zone(id)} area={area} />);

describe("ZoneBriefing", () => {
  it("shows the quiet zone as not checked, never as safe", () => {
    const out = html("B-4");
    expect(out).toContain("No reports yet · not checked");
    expect(out).toContain("No reviewed cases. That doesn&#x27;t mean no one needs help.");
    expect(out).not.toMatch(/\bsafe\b|\bdry\b/i);
  });

  it("labels every estimate and keeps it apart from the reviewed count", () => {
    const out = html("B-3");
    expect(out).toContain("7,900–13,000");
    expect(out).toMatch(/estimate/);
    expect(out).toContain("<strong class=\"num\">9</strong> reported needing evacuation (reviewed)");
    expect(out).toContain("model, not measured");
  });

  it("always shows the Unknown row and the briefing fallback", () => {
    const out = html("B-3");
    expect(out).toContain("A neighbour stayed at B-3 · L3; identity unknown");
    expect(out).toContain("Briefing unavailable. The facts above are complete.");
  });

  it("shows cases at landmark level with priority and state", () => {
    const out = html("B-3");
    expect(out).toContain("B-3 · L3 Community building");
    expect(out).toContain("Life-threatening");
    expect(out).toContain("Waiting for a team");
  });
});
