import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ResourceFailure } from "./ResourceFailure";
import { JobCard } from "../team/TeamPages";
import type { Job, OpenListing } from "../../data/contract";
import fixture from "../../../../contract/fixtures/teamMissions.T-S.json";

afterEach(() => vi.unstubAllEnvs());

describe("S1 failure review", () => {
  it("offers a coordinator review in API mode and explains the withdrawal", () => {
    vi.stubEnv("VITE_DATA", "api");
    const out = renderToStaticMarkup(<ResourceFailure />);
    expect(out).toContain("Mark S1 unavailable");
    expect(out).toContain("withdraw earlier arrival estimates");
    expect(out).toContain("Next status update (Bangkok, not an arrival time)");
    expect(out).not.toContain("disabled");
  });

  it("disables the review in fixture mode", () => {
    vi.stubEnv("VITE_DATA", "fixtures");
    const out = renderToStaticMarkup(<ResourceFailure />);
    expect(out).toContain("disabled");
    expect(out).toContain("This review needs the server");
  });

  it("strikes the old window and removes team controls from a held job", () => {
    const row = fixture.open[0] as unknown as OpenListing;
    const j: Job = { ...row, allocationId: "AL-S1", state: "held", seatUnits: 2.5,
      medical: null, window: null, acceptedAt: "2026-10-11T03:20:00Z", owner: "coordinator",
      holdReason: "Boat engine trouble", nextStatusUpdate: { at: "2026-10-11T04:00:00Z", by: "coordinator" },
      withdrawnWindow: { start: "2026-10-11T06:00:00Z", end: "2026-10-11T07:00:00Z",
        setAt: "2026-10-11T03:20:00Z", state: "withdrawn", withdrawnAt: "2026-10-11T03:32:00Z", withdrawnBy: "coordinator" },
      pickup: { landmarkLabel: row.landmarkLabel, at: [100.47, 7.0], precision: "landmark", source: "synthetic" } };
    const out = renderToStaticMarkup(<JobCard j={j} />);
    expect(out).toContain('<s class="num">13:00–14:00</s>');
    expect(out).toContain("estimate withdrawn");
    expect(out).toContain("New time not known");
    expect(out).toContain("Next status update 11:00 from the coordinator desk");
    expect(out).not.toMatch(/Set window|Finish…|Hand back|the family sees it now/);
  });
});
