import { describe, expect, it } from "vitest";
import type { SplitPanelView, Suggestion } from "../../data/contract";
import panelJson from "../../../../contract/fixtures/splitPanel.cp3.json";
import staleJson from "../../../../contract/fixtures/askTeams.stale.json";
import { diffSuggestions, headline } from "./SplitPanel";

const panel = panelJson as unknown as SplitPanelView;
const current = (staleJson as unknown as { response: { detail: { current: Suggestion } } }).response.detail.current;

describe("split panel", () => {
  it("says who covers the urgent cases and how many are unmet, from the numbers", () => {
    expect(headline(panel.suggestion)).toBe("T-M and T-S cover the urgent cases; 9 people still unmet");
  });

  it("puts urgent people without a team first when S1 breaks down", () => {
    expect(headline(current)).toBe("3 urgent people have no team; 25 people still unmet");
  });

  it("says when nothing is left", () => {
    const none = { ...current, assignments: [] };
    expect(headline(none)).toBe("No capacity left today: 25 people unmet");
  });

  it("diffs old and new suggestions for the stale ask", () => {
    const d = diffSuggestions(panel.suggestion, current);
    expect(d.removed.every((a) => a.resourceId === "S1")).toBe(true);
    expect(d.unchanged.map((a) => a.listingId).sort()).toEqual(["L-C01-MED", "L-PA-SUP"]);
    expect(d.added).toEqual([]);
  });

  it("every What-if is a simulation", () => {
    expect(panel.scenarios.every((s) => s.suggestion.simulation)).toBe(true);
    expect(panel.whatIfLabel).toBe("Simulation · nothing sent");
  });
});
