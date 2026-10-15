/**
 * Team view + team actions (C5, C6), fixture mode.
 *
 * Until the friend's API is up, this keeps T-S's view in memory and applies the same rules the rules engine
 * will enforce in one transaction (decision pack §4.2): Available status, whole open groups only, enough seats,
 * the revision the team saw, and no updates after a job is closed. Screens call these functions and read
 * `useTeam()`; with the real API they become `api.post(...)` calls plus a Firestore listener, same results.
 *
 * API mode (data/mode.ts): the view is GET /api/views/teamMissions/{teamId} and every action is a POST from
 * contract/api.md; after each one the view is fetched again, so the screen shows what the server decided.
 *
 * Dev switch: `?claim=already-taken | not-enough-capacity | need-changed | allocation-closed | version-conflict`
 * makes the first claim on this page return that result (from contract/fixtures/claim.*.json).
 */
import { useSyncExternalStore } from "react";
import { ApiError, get, post, submissionId } from "./api";
import type { ClaimCode, Group, Job, MedicalNotes, OpenListing, Outcome, Result, TeamMissionsView, TeamStatus } from "./contract";
import { apiMode } from "./mode";
import { now } from "./clock";
import { devSwitch } from "./source";

const views = import.meta.glob("../../../contract/fixtures/teamMissions.*.json", { import: "default" });
const pickupsFile = import.meta.glob("../../../contract/fixtures/pickups.synthetic.json", { import: "default" });
const claimFiles = import.meta.glob("../../../contract/fixtures/claim.*.json", { import: "default" });
const medicalFile = import.meta.glob("../../../contract/fixtures/medicalNotes.synthetic.json", { import: "default" });

type Pickups = { pickups: Record<string, Omit<Job["pickup"], "landmarkLabel">> };
type ClaimFixture = { response: { code: string; message: string } };
type Fail = Extract<Result, { ok: false }>;

type State =
  | { status: "loading" }
  | { status: "missing"; teamId: string }
  | { status: "error"; message: string }
  | { status: "ready"; view: TeamMissionsView; offline: boolean };

let state: State = { status: "loading" };
let loadedFor: string | null = null;
let pickups: Pickups["pickups"] = {};
let medical: Record<string, MedicalNotes> = {};
let forcedUsed = false;
const listeners = new Set<() => void>();

function emit(next: State) {
  state = next;
  listeners.forEach((l) => l());
}

function iso(ms = now()) {
  return new Date(ms).toISOString();
}

function clone<T>(x: T): T {
  return JSON.parse(JSON.stringify(x)) as T;
}

function update(fn: (v: TeamMissionsView) => void) {
  if (state.status !== "ready") return;
  const v = clone(state.view);
  fn(v);
  emit({ ...state, view: v });
}

export async function loadTeam(teamId: string) {
  if (loadedFor === teamId && state.status === "ready") return;
  loadedFor = teamId;
  emit({ status: "loading" });
  if (apiMode()) return fetchTeam(teamId);
  try {
    await new Promise((r) => setTimeout(r, 150));
    if (devSwitch("fail") === "view") throw new Error("Team view failed to load");
    const load = views[`../../../contract/fixtures/teamMissions.${teamId}.json`];
    if (!load) return emit({ status: "missing", teamId });
    const view = clone((await load()) as TeamMissionsView);
    const p = (await pickupsFile["../../../contract/fixtures/pickups.synthetic.json"]()) as Pickups;
    pickups = p.pickups;
    medical = ((await medicalFile["../../../contract/fixtures/medicalNotes.synthetic.json"]()) as { notes: Record<string, MedicalNotes> }).notes;
    emit({ status: "ready", view, offline: Boolean(devSwitch("offline")) });
  } catch (e) {
    emit({ status: "error", message: e instanceof Error ? e.message : String(e) });
  }
}

async function fetchTeam(teamId: string) {
  try {
    const view = await get<TeamMissionsView>(`/api/views/teamMissions/${teamId}`);
    emit({ status: "ready", view, offline: false });
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return emit({ status: "missing", teamId });
    if (state.status === "ready") return emit({ ...state, offline: true });
    emit({ status: "error", message: e instanceof Error ? e.message : String(e) });
  }
}

/** API mode: POST the action, then fetch the team view again. Rule failures come back as a Result, not a throw. */
async function remote<T = undefined>(path: string, body: object): Promise<Result<T>> {
  try {
    const r = await post<{ value?: T }>(path, { ...body, submissionId: submissionId() });
    if (loadedFor) await fetchTeam(loadedFor);
    return { ok: true, value: r.value as T };
  } catch (e) {
    if (loadedFor && e instanceof ApiError && e.status === 409) await fetchTeam(loadedFor);
    if (e instanceof ApiError) return fail((e.code as ClaimCode) ?? "VERSION_CONFLICT", e.message);
    return fail("OFFLINE", "Can't reach the server. Nothing was changed; try again");
  }
}

const teamPath = () => `/api/teams/${loadedFor}`;

/** API mode: fetch the team view again without a loading state (the screens poll this). */
export function refreshTeam() {
  if (apiMode() && loadedFor && state.status !== "loading") void fetchTeam(loadedFor);
}

export function useTeam(): State {
  return useSyncExternalStore(
    (l) => {
      listeners.add(l);
      return () => listeners.delete(l);
    },
    () => state,
  );
}

const fail = (code: Fail["code"], message: string): Fail => ({ ok: false, code, message });

async function forced(): Promise<Fail | null> {
  const name = devSwitch("claim");
  if (!name || forcedUsed) return null;
  forcedUsed = true;
  const load = claimFiles[`../../../contract/fixtures/claim.${name}.json`];
  if (!load) return null;
  const f = (await load()) as ClaimFixture;
  return fail(f.response.code as Fail["code"], f.response.message);
}

function seatsText(n: number) {
  return Number.isInteger(n) ? `${n}` : n.toFixed(1);
}

/** Take whole open groups of one listing, with the revision the team saw. */
export async function claimListing(listingId: string, groupIds: string[], seenRevision: number): Promise<Result<Job>> {
  if (apiMode()) return remote<Job>(`/api/listings/${listingId}/claim`, { teamId: loadedFor, groupIds, expectedRevision: seenRevision });
  await new Promise((r) => setTimeout(r, 250));
  if (state.status !== "ready") return fail("VERSION_CONFLICT", "Your screen was out of date; it has been refreshed");
  const f = await forced();
  if (f) {
    if (f.code === "NEED_CHANGED") {
      // The desk corrected the case while the team was looking: bump the revision so "Look again" shows it.
      update((v) => {
        const l = v.open.find((x) => x.listingId === listingId);
        if (l) {
          l.needRevision += 1;
          l.lastConfirmedAt = iso();
        }
      });
    }
    return f;
  }
  const v = state.view;
  const l = v.open.find((x) => x.listingId === listingId);
  if (!l) return fail("ALLOCATION_CLOSED", "This case is no longer open");
  if (v.team.status !== "available") return fail("NOT_AVAILABLE", "Set your team to Available to take cases");
  if (l.needRevision !== seenRevision) return fail("NEED_CHANGED", "This case changed, please look again");
  const groups = l.groups.filter((g) => groupIds.includes(g.groupId));
  const taken = groups.find((g) => g.state !== "open");
  if (taken) return fail("ALREADY_TAKEN", `Already taken by ${taken.takenBy ?? "another team"}`);
  const need = groups.reduce((s, g) => s + g.seatUnits, 0);
  if (need > v.team.resource.seatUnitsLeft)
    return fail("NOT_ENOUGH_CAPACITY", `Needs ${seatsText(need)} seats, you have ${seatsText(v.team.resource.seatUnitsLeft)}`);

  const p = pickups[listingId];
  const job: Job = {
    allocationId: `AL-${listingId.slice(2)}-${Math.floor(now() / 1000) % 100000}`,
    listingId,
    caseId: l.caseId,
    colour: l.colour,
    landmarkLabel: l.landmarkLabel,
    urgency: clone(l.urgency),
    destination: clone(l.destination),
    medical: medical[listingId] ? clone(medical[listingId]) : null,
    groups: clone(groups).map((g) => ({ ...g, state: "taken", takenBy: v.teamId })),
    seatUnits: need,
    state: "taken",
    window: null,
    acceptedAt: iso(),
    pickup: { landmarkLabel: l.landmarkLabel, ...(p ?? { at: [0, 0], precision: "landmark", source: "unknown" }) },
  };
  update((nv) => {
    const nl = nv.open.find((x) => x.listingId === listingId)!;
    nl.groups.forEach((g) => {
      if (groupIds.includes(g.groupId)) {
        g.state = "taken";
        g.takenBy = nv.teamId;
      }
    });
    nv.team.resource.seatUnitsLeft -= need;
    nv.jobs.push(job);
  });
  return { ok: true, value: job };
}

function withJob(allocationId: string, fn: (j: Job, v: TeamMissionsView) => void): Result {
  if (state.status !== "ready") return fail("VERSION_CONFLICT", "Your screen was out of date; it has been refreshed");
  const j = state.view.jobs.find((x) => x.allocationId === allocationId);
  if (!j) return fail("ALLOCATION_CLOSED", "This job is closed");
  if (j.state === "closed") return fail("ALLOCATION_CLOSED", "This job is closed");
  update((v) => fn(v.jobs.find((x) => x.allocationId === allocationId)!, v));
  return { ok: true, value: undefined };
}

function reopen(v: TeamMissionsView, j: Job, note?: string) {
  const l = v.open.find((x) => x.listingId === j.listingId);
  if (l) {
    l.groups.forEach((g: Group) => {
      if (j.groups.some((jg) => jg.groupId === g.groupId)) {
        g.state = "open";
        delete g.takenBy;
      }
    });
    if (note) l.reasons = [...l.reasons.filter((r) => !r.startsWith("Back from")), note];
  }
  v.team.resource.seatUnitsLeft += j.seatUnits;
}

export async function setWindow(allocationId: string, start: string, end: string) {
  if (apiMode()) return remote(`/api/allocations/${allocationId}/window`, { start, end });
  return withJob(allocationId, (j) => {
    j.window = { start, end, setAt: iso() };
  });
}

export async function reportProgress(allocationId: string, next: "on_the_way" | "on_scene") {
  if (apiMode()) return remote(`/api/allocations/${allocationId}/progress`, { state: next });
  return withJob(allocationId, (j) => {
    j.state = next;
  });
}

/** Close a job with its outcome. People who weren't moved free their seats again. */
export async function closeAllocation(allocationId: string, outcome: Outcome) {
  if (apiMode()) return remote(`/api/allocations/${allocationId}/close`, { outcome });
  return withJob(allocationId, (j, v) => {
    j.state = "closed";
    j.outcome = outcome;
    j.closedAt = iso();
    delete j.preparationSummary;
    if (j.medical) {
      j.medical = null; // D38: medical notes leave the team's phone when the job closes
      j.medicalRemovedAt = j.closedAt;
    }
    if (outcome === "needs_more_help") reopen(v, j, `Back from ${v.teamId}: needs more help`);
    else if (outcome !== "done") v.team.resource.seatUnitsLeft += j.seatUnits;
  });
}

/** Give the job back: its groups go back on the open list, the seats come back. */
export async function handBack(allocationId: string, reason: string) {
  if (apiMode()) return remote(`/api/allocations/${allocationId}/hand-back`, { reason });
  return withJob(allocationId, (j, v) => {
    reopen(v, j, `Back from ${v.teamId}: ${reason}`);
    v.jobs = v.jobs.filter((x) => x.allocationId !== allocationId);
  });
}

export async function setTeamStatus(status: TeamStatus, reason: string | null, backAbout: string | null): Promise<Result> {
  if (apiMode()) return remote(`${teamPath()}/status`, { status, reason, backAbout });
  update((v) => {
    v.team = { ...v.team, status, reason: status === "available" ? null : reason, backAbout: status === "available" ? null : backAbout, statusSetAt: iso() };
  });
  return { ok: true as const, value: undefined };
}

/**
 * Coordinator's urgent flag with a stated reason (tier 1b, D42 "Flag urgent"). The listing turns RED and moves to the
 * top of every team's list; the reason becomes the first "why" line. In fixture mode it changes this tab's T-S view;
 * the friend's rules engine applies it for every team. A flag without a reason is refused. `confirmedNow`: the reason
 * came from a callback just now, so "last confirmed" moves to now.
 */
export async function flagUrgent(listingId: string, reason: string, confirmedNow = false): Promise<Result> {
  const r = reason.trim();
  if (!r) return fail("INVALID", "An urgent flag needs a reason");
  if (apiMode()) return remote(`/api/listings/${listingId}/urgent-flag`, { reason: r, confirmedNow });
  if (state.status !== "ready") return fail("VERSION_CONFLICT", "Your screen was out of date; it has been refreshed");
  if (!state.view.open.some((x) => x.listingId === listingId)) return fail("ALLOCATION_CLOSED", "This case is no longer open");
  update((v) => {
    const l = v.open.find((x) => x.listingId === listingId)!;
    l.colour = "red";
    l.needRevision += 1;
    if (confirmedNow) l.lastConfirmedAt = iso(); // the flag came from a callback: the family was just confirmed
    l.urgency = {
      ...l.urgency,
      title: "Why this is an emergency",
      summary: `Coordinator flagged urgent: ${r}`,
      facts: [{ kind: "flag", text: `Coordinator flagged urgent: ${r}`, basis: "coordinator" }, ...l.urgency.facts.filter((f) => f.kind !== "flag")],
    };
    const rank = { red: 0, yellow: 1, green: 2 } as const;
    v.open = v.open.map((x, i) => [x, i] as const).sort((a, b2) => rank[a[0].colour] - rank[b2[0].colour] || a[1] - b2[1]).map(([x]) => x);
  });
  return { ok: true, value: undefined };
}

export async function requestReconfirm(listingId: string): Promise<Result> {
  if (apiMode()) return remote(`/api/listings/${listingId}/reconfirm`, { teamId: loadedFor });
  update((v) => {
    const l: OpenListing | undefined = v.open.find((x) => x.listingId === listingId);
    if (l) l.reconfirmRequestedAt = iso();
  });
  return { ok: true as const, value: undefined };
}

/* ---- Zone missions and segments (D17b, D20): server only for now ---- */

const NEEDS_SERVER = "Segments need the server. Open the app with ?data=api.";

export async function takeSegment(segmentId: string): Promise<Result> {
  if (!apiMode()) return fail("INVALID", NEEDS_SERVER);
  return remote(`/api/segments/${segmentId}/take`, { teamId: loadedFor });
}

export async function markSegment(
  claimId: string,
  state: "checked" | "partly_checked" | "could_not_reach",
  householdsFound: number | null,
  pickupsNeeded: number | null,
  reason: string | null,
): Promise<Result> {
  if (!apiMode()) return fail("INVALID", NEEDS_SERVER);
  return remote(`/api/segment-claims/${claimId}/mark`, { state, householdsFound, pickupsNeeded, reason });
}

/** People found who hadn't called: goes to the desk's review queue with this segment as the place (D20). */
export async function sendFieldReport(segmentId: string, text: string): Promise<Result<{ reportId: string }>> {
  if (!apiMode()) return fail("INVALID", NEEDS_SERVER);
  return remote<{ reportId: string }>("/api/intake/text", { text, segmentId, teamId: loadedFor });
}

/** For tests: the current snapshot, as useTeam() would return it. */
export function __peek() {
  return state.status === "ready" ? state : null;
}

/** For tests: reset to a fresh load. */
export function _resetTeamStore() {
  state = { status: "loading" };
  loadedFor = null;
  forcedUsed = false;
}
