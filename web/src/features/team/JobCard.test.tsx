import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { Job, OpenListing } from "../../data/contract";
import { LangProvider } from "../../i18n/lang";
import { JobCard } from "./TeamPages";
import fixture from "../../../../contract/fixtures/teamMissions.T-S.json";

const row = fixture.open[0] as unknown as OpenListing;
const windowEstimate = { start: "2026-10-11T04:00:00Z", end: "2026-10-11T05:00:00Z", setAt: "2026-10-11T03:00:00Z" };
const base: Job = { ...row, allocationId: "AL-UI", state: "taken", seatUnits: 2.5,
  medical: null, window: null, acceptedAt: "2026-10-11T03:20:00Z",
  pickup: { landmarkLabel: row.landmarkLabel, at: [100.47, 7.0], precision: "landmark", source: "synthetic" } };

describe("job next action", () => {
  it("shows preparation notes only on active jobs", () => {
    const j = { ...base, preparationSummary: { text: "Synthetic medication request", checkedBy: "AI" as const, at: "2026-10-15T03:00:00Z" } };
    expect(renderToStaticMarkup(<JobCard j={j} />)).toContain("Synthetic medication request");
    expect(renderToStaticMarkup(<JobCard j={{ ...j, state: "closed" }} />)).not.toContain("Synthetic medication request");
  });
  it.each<[Job["state"], Job["window"], string]>([
    ["taken", null, "Set window"], ["taken", windowEstimate, "On the way"],
    ["on_the_way", windowEstimate, "On scene"], ["on_the_way", null, "On scene"],
    ["on_scene", windowEstimate, "Finish…"], ["on_scene", null, "Finish…"],
  ])("offers one primary action for %s with window %j", (state, window, next) => {
    const html = renderToStaticMarkup(<LangProvider lang="en"><JobCard j={{ ...base, state, window }} /></LangProvider>);
    expect(html.match(/class="btn btn-primary btn-md"/g)).toHaveLength(1);
    expect(html).toContain(`<span>${next}</span></button>`);
    expect(html).toContain('class="btn btn-secondary btn-md"><span>Hand back</span>');
  });

  it.each<Job["state"]>(["held", "closed"])("has no action on a %s job", (state) => {
    const html = renderToStaticMarkup(<JobCard j={{ ...base, state }} />);
    expect(html).not.toContain("btn-primary");
    expect(html).not.toContain("Hand back");
  });

  it("renders Thai actions and keeps the medical section private", () => {
    const html = renderToStaticMarkup(<LangProvider lang="th"><JobCard j={{ ...base, medical: {
      consent: "given", basis: "synthetic", functional: ["Synthetic functional note"], condition: "Synthetic condition",
    } }} /></LangProvider>);
    expect(html).toContain("ตั้งช่วงเวลา");
    expect(html).toContain('class="medical"');
    expect(html).toContain("เฉพาะทีมของคุณ");
    expect(html).not.toContain("Set window");
  });
});
