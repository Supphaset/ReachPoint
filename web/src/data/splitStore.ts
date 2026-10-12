/**
 * Split panel data + "Ask these N teams" (C4 view, C7), fixture mode.
 * With the API: GET the stored suggestion, POST askTeams(suggestionId, inputVersions, teamIds), POST compare_scenarios.
 * Dev switch: `?ask=stale` makes the ask return VERSION_CONFLICT with the new suggestion (S1 reported unavailable).
 */
import type { AskResult, SplitPanelView } from "./contract";
import { now } from "./clock";
import { devSwitch } from "./source";

const panel = import.meta.glob("../../../contract/fixtures/splitPanel.cp3.json", { import: "default" });
const asks = import.meta.glob("../../../contract/fixtures/askTeams.*.json", { import: "default" });

export async function loadSplitPanel(): Promise<SplitPanelView> {
  await new Promise((r) => setTimeout(r, 300));
  if (devSwitch("fail") === "split") throw new Error("Split unavailable");
  const view = (await panel["../../../contract/fixtures/splitPanel.cp3.json"]()) as SplitPanelView;
  if (devSwitch("variant") === "all-unmet") {
    const v = JSON.parse(JSON.stringify(view)) as SplitPanelView;
    const s = v.scenarios.find((x) => x.id === "whatif-no-s1")!.suggestion;
    v.suggestion = { ...s, simulation: false };
    return v;
  }
  return view;
}

type AskFixture = { request: { suggestionId: string }; response: AskResult };

export async function askTeams(suggestionId: string, teamIds: string[], snapshotAt?: string): Promise<AskResult> {
  await new Promise((r) => setTimeout(r, 300));
  const stale = (await asks["../../../contract/fixtures/askTeams.stale.json"]()) as AskFixture;
  const ok = (await asks["../../../contract/fixtures/askTeams.ok.json"]()) as AskFixture;
  if (devSwitch("ask") === "stale" && suggestionId === stale.request.suggestionId) return stale.response;
  if (suggestionId === ok.request.suggestionId) return ok.response;
  // a fresh suggestion (e.g. after a conflict): the ask goes to the teams given
  return { ok: true, askedAt: new Date(Math.max(now(), snapshotAt ? Date.parse(snapshotAt) + 60000 : 0)).toISOString(), asks: teamIds.map((t) => ({ askId: `ASK-${t}`, teamId: t, listingIds: [] })), note: "" };
}
