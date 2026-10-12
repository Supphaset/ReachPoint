import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { _resetTeamStore, claimListing, flagUrgent, loadTeam } from "./teamStore";
import fixture from "../../../contract/fixtures/teamMissions.T-S.json";

type Call = { url: string; method: string; body: Record<string, unknown> | null };
let calls: Call[] = [];

function respond(handler: (c: Call) => [number, unknown]) {
  vi.stubGlobal("fetch", async (url: string, init: RequestInit = {}) => {
    const c = { url, method: init.method ?? "GET", body: init.body ? JSON.parse(init.body as string) : null };
    calls.push(c);
    const [status, json] = handler(c);
    return { ok: status < 400, status, statusText: String(status), json: async () => json } as Response;
  });
}

beforeEach(() => {
  vi.stubEnv("VITE_DATA", "api");
  calls = [];
  _resetTeamStore();
});
afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("API mode (contract/api.md)", () => {
  it("loads the team view from the server and posts a claim with a submission ID, then reloads", async () => {
    respond((c) => (c.method === "GET" ? [200, fixture] : [200, { ok: true, value: { allocationId: "AL-1" } }]));
    await loadTeam("T-S");
    expect(calls[0].url).toBe("/api/views/teamMissions/T-S");
    const r = await claimListing("L-C01-EVAC", ["L-C01-EVAC-G1"], 2);
    expect(r).toEqual({ ok: true, value: { allocationId: "AL-1" } });
    const post = calls.find((c) => c.method === "POST")!;
    expect(post.url).toBe("/api/listings/L-C01-EVAC/claim");
    expect(post.body).toMatchObject({ teamId: "T-S", groupIds: ["L-C01-EVAC-G1"], expectedRevision: 2 });
    expect(String(post.body!.submissionId)).toMatch(/^SUB-/);
    expect(calls[calls.length - 1].method).toBe("GET"); // fetched again after the write
  });

  it("turns a 409 into the same result the screens already handle", async () => {
    respond((c) => (c.method === "GET" ? [200, fixture] : [409, { code: "ALREADY_TAKEN", message: "Already taken by T-R" }]));
    await loadTeam("T-S");
    expect(await claimListing("L-C04-EVAC", ["L-C04-EVAC-G1"], 1)).toEqual({ ok: false, code: "ALREADY_TAKEN", message: "Already taken by T-R" });
  });

  it("says nothing changed when the server can't be reached, and keeps the last view", async () => {
    let up = true;
    vi.stubGlobal("fetch", async () => {
      if (!up) throw new TypeError("network");
      return { ok: true, status: 200, json: async () => fixture } as Response;
    });
    await loadTeam("T-S");
    up = false;
    expect(await flagUrgent("L-C08-EVAC", "Callback: 2nd floor")).toMatchObject({ ok: false, code: "OFFLINE" });
  });

  it("refuses an urgent flag without a reason before calling the server", async () => {
    respond(() => [200, fixture]);
    await loadTeam("T-S");
    calls = [];
    expect(await flagUrgent("L-C08-EVAC", " ")).toMatchObject({ ok: false, code: "INVALID" });
    expect(calls).toHaveLength(0);
  });
});
