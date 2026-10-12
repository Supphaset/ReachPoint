import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { FloodSegment, WaterEstimate } from "../../data/flood";
import { loadFlood, resetReplay, stepReplay } from "../../data/flood";
import { askTeams, loadSplitPanel } from "../../data/splitStore";
import { Evidence } from "./FloodPage";
import { estimateLabel, markerLabel } from "./FloodMap";

const e: WaterEstimate = { siteId: "B-4-L5", status: "available", rangeM: [0.65, 1.05], centralM: 0.85,
  latestAt: "2026-10-11T03:20:00Z", observationCount: 2, sourceReferences: 2, independence: "unknown",
  bands: [], trends: ["rising"], reasons: ["Local estimate only; no route conclusion"], evidenceIds: ["W-1", "W-2"], method: "local-envelope-v1" };
const segment: FloodSegment = { segmentId: "B-4-L5", zoneId: "B-4", areaId: "P-B", label: "B-4 · School", at: [100.47, 7],
  noSatelliteDataShare: 0.8, needs: { reportedPeople: 10, verifiedTransportUnassigned: 3, urgentReports: 2, urgentReviewedGroups: 1, supplyReports: 1, checkOnReports: 0 },
  coverage: { activeJobs: 1, heldJobs: 2, state: "not_checked" }, estimates: [e], observations: [{ observationId: "W-1", reportId: "SIM-1",
    observedAt: null, receivedAt: "2026-10-11T03:20:00Z", reference: "unknown", source: "simulated_call", band: "chest", depthM: null, uncertaintyM: null, trend: "unknown", review: "ai_read" }] };

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

describe("flood evidence workspace", () => {
  it("describes local ranges, qualitative reports, conflicts and stale or absent evidence honestly", () => {
    expect(estimateLabel(e)).toBe("Estimated local depth: 0.65–1.05 m");
    expect(estimateLabel({ ...e, status: "conflicting", centralM: null })).toContain("Conflicting reports");
    expect(estimateLabel({ ...e, status: "qualitative_only", rangeM: null, bands: ["chest"] })).toContain("metre estimate unavailable");
    expect(estimateLabel({ ...e, status: "stale", rangeM: null })).toContain("Stale");
    expect(estimateLabel()).toContain("unknown");
  });

  it("keeps reports, reviewed needs and job progress distinct", () => {
    expect(markerLabel(segment, "needs")).toContain("2 urgent reports · 1 reviewed urgent groups · 10 people in reports · 3 verified people");
    expect(markerLabel(segment, "response")).toContain("1 active jobs · 2 held · not checked");
  });

  it("shows uncertainty and provenance without turning a body band into metres", () => {
    const out = renderToStaticMarkup(<Evidence segment={segment} />);
    expect(out).toContain("Independent observers unknown");
    expect(out).toContain("not unique households");
    expect(out).toContain("chest");
    expect(out).toContain("ai read · simulated call · unknown");
    expect(out).toContain("Observed time unknown");
    expect(out).not.toContain("1.3 m");
  });

  it("unknown water remains unknown in an empty segment", () => {
    const out = renderToStaticMarkup(<Evidence segment={{ ...segment, estimates: [], observations: [] }} />);
    expect(out).toContain("Conditions remain unknown");
    expect(out).toContain("consider a field check");
  });

  it("posts the replay revision and a stable supplied ID for retries", async () => {
    const calls: { url: string; body: unknown }[] = [];
    vi.stubGlobal("fetch", async (url: string, init: RequestInit = {}) => {
      calls.push({ url, body: init.body ? JSON.parse(String(init.body)) : null });
      return { ok: true, status: 200, json: async () => ({ ok: true, cursor: 20 }) } as Response;
    });
    await loadFlood("replay");
    await stepReplay(0, 7, 20, "STEP-ID");
    await stepReplay(0, 7, 20, "STEP-ID");
    await resetReplay(20, 8, "RESET-ID");
    expect(calls[0].url).toBe("/api/views/floodMap?source=replay");
    expect(calls[1]).toEqual(calls[2]);
    expect(calls[1].body).toEqual({ expectedCursor: 0, expectedRevision: 7, count: 20, submissionId: "STEP-ID" });
    expect(calls[3].body).toEqual({ expectedCursor: 20, expectedRevision: 8, submissionId: "RESET-ID" });
  });

  it("surfaces version conflicts instead of pretending a replay advanced", async () => {
    vi.stubGlobal("fetch", async () => ({ ok: false, status: 409, json: async () => ({ code: "VERSION_CONFLICT", message: "Refresh replay" }) }) as Response);
    await expect(stepReplay(0, 0, 20, "STALE-ID")).rejects.toMatchObject({ code: "VERSION_CONFLICT" });
  });

  it("uses the current API plan and records area-specific asks with a submission ID", async () => {
    vi.stubEnv("VITE_DATA", "api");
    vi.stubGlobal("window", { location: { search: "?data=api&area=P-B" } });
    const calls: { url: string; body: Record<string, unknown> | null }[] = [];
    vi.stubGlobal("fetch", async (url: string, init: RequestInit = {}) => {
      calls.push({ url, body: init.body ? JSON.parse(String(init.body)) : null });
      return { ok: true, status: 200, json: async () => ({}) } as Response;
    });
    await loadSplitPanel();
    await askTeams("LIVE-SUG", ["T-S"]);
    expect(calls[0].url).toBe("/api/views/splitPanel?areaId=P-B");
    expect(calls[1].url).toBe("/api/plans/ask");
    expect(calls[1].body).toMatchObject({ suggestionId: "LIVE-SUG", teamIds: ["T-S"], areaId: "P-B" });
    expect(calls[1].body!.submissionId).toMatch(/^SUB-/);
  });
});
