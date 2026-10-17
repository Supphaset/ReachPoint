import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import { v2, type FamilyStatus, type SimResult, type TurnResult } from "../api";
import { ReadyChecklist, applySimulation, choiceSender, ChoiceButtons, FamilyStatusCard, QUICK_ACTIONS, runQuickAction, statusLabel, SimulationPanel } from "./FamilyFollowUp";
import { buildFollowUpTrace, buildReportTrace } from "./reportTrace";

const status: FamilyStatus = {
  householdId: "HH308", zoneId: "D7", status: "open", urgent: false, wantsOut: false, people: 2,
  water: { nowM: 0.81, loM: 0.6, hiM: 1, in6hM: 1.24, trend: "rising", reports: 3 },
  team: null, outcome: null, shelter: { name: "School", km: 1.2, deepestM: 0.4, walkable: true, minutes: 20 },
  nextCheck: "16:30", now: "14:30",
};

afterEach(() => vi.unstubAllGlobals());

describe("choice groups", () => {
  it("sends text and replyTo once, selects immediately, and locks after success", async () => {
    let resolve!: (ok: boolean) => void;
    const send = vi.fn(() => new Promise<boolean>(done => { resolve = done; }));
    const select = vi.fn();
    const choose = choiceSender(send, "leaveAsk", select);
    const pending = choose({ label: "ออก · Leave", send: "ต้องการออก" }, 0);
    await choose({ label: "อยู่ · Stay", send: "อยู่" }, 1);
    expect(select).toHaveBeenCalledWith(0);
    expect(send).toHaveBeenCalledTimes(1);
    expect(send).toHaveBeenCalledWith("ต้องการออก", "leaveAsk");
    resolve(true);
    await pending;
    await choose({ label: "อยู่", send: "อยู่" }, 1);
    expect(send).toHaveBeenCalledTimes(1);
  });
  it("unlocks a failed group for retry and disables all buttons while busy", async () => {
    const send = vi.fn().mockResolvedValueOnce(false).mockResolvedValue(true);
    const select = vi.fn();
    const choose = choiceSender(send, "checkin", select);
    await choose({ label: "Safe", send: "ปลอดภัยดี" }, 0);
    expect(select).toHaveBeenLastCalledWith(null);
    await choose({ label: "Safe", send: "ปลอดภัยดี" }, 0);
    expect(send).toHaveBeenCalledTimes(2);
    const html = renderToStaticMarkup(<ChoiceButtons kind="checkin" options={[{ label: "Safe", send: "safe" }, { label: "Help", send: "help" }]} disabled onSend={send} />);
    expect(html.match(/disabled=""/g)).toHaveLength(2);
  });
});

describe("family status", () => {
  it("formats house, water, trend, forecast, team, shelter and next check-in", () => {
    const html = renderToStaticMarkup(<FamilyStatusCard status={status} />);
    for (const value of ["HH308", "D7", "Waiting", "~0.8 m ↑", "6 ชม. ~1.2 m", "No team planned yet", "School", "deepest 0.4 m", "16:30"]) expect(html).toContain(value);
    expect(renderToStaticMarkup(<FamilyStatusCard status={{ ...status, water: null, team: { team: "Boat 1", vehicle: "boat", seats: 4, eta: "15:00", at: "14:00" } }} />)).toContain("Boat 1 boat ~15:00 (ยังไม่ยืนยัน)");
  });
  it("keeps confirmed outcome, reported safe, urgency and departure distinct", () => {
    expect(statusLabel({ ...status, wantsOut: true })).toContain("Wants to leave");
    expect(statusLabel({ ...status, urgent: true, wantsOut: true })).toContain("Urgent");
    expect(statusLabel({ ...status, status: "safe" })).toContain("Safe");
    expect(statusLabel({ ...status, outcome: { kind: "pickedUp", team: "T", at: "now" } })).toContain("Picked up");
  });
});

describe("simulation responses", () => {
  it("appends message choices without polling inbox for message-only events", async () => {
    const message = { text: "Water rising", kind: "river", choices: [["ออก · Leave", "ออก"]] as [string, string][] };
    const receive = vi.fn(), inbox = vi.fn();
    await applySimulation({ event: "river", status, message }, receive, inbox);
    expect(receive).toHaveBeenCalledWith(message);
    expect(inbox).not.toHaveBeenCalled();
  });
  it("refreshes the inbox immediately for team notices and handles both effects", async () => {
    const receive = vi.fn(), inbox = vi.fn().mockResolvedValue(undefined);
    const result: SimResult = { event: "teamPlan", status, inbox: true };
    await applySimulation(result, receive, inbox);
    expect(receive).not.toHaveBeenCalled();
    expect(inbox).toHaveBeenCalledTimes(1);
    await applySimulation({ ...result, message: { text: "Hi", kind: "checkin", choices: [] } }, receive, inbox);
    expect(receive).toHaveBeenCalledTimes(1);
    expect(inbox).toHaveBeenCalledTimes(2);
    expect(buildFollowUpTrace(result, 1, "14:00", 2)[0].what).toContain("Team plan told to this family");
    expect(buildFollowUpTrace({ ...result, inbox: false }, 2, "14:00", 2)).toEqual([]);
  });
  it("explains Report first and disables all five events before location", () => {
    const html = renderToStaticMarkup(<SimulationPanel enabled={false} busy={false} result="" onSimulate={() => undefined} />);
    expect(html).toContain("Report first");
    expect(html.match(/disabled=""/g)).toHaveLength(5);
  });
});

describe("follow-up rules trace", () => {
  const turn: TurnResult = {
    session: { id: "S1", token: "synthetic", lang: "th", householdId: "HH308", pin: null, buildingId: null, zoneId: "D7", transcript: [], neighbours: [], pending: null, finished: false },
    reply: "", zone: null, status: { ...status, urgent: true, wantsOut: true },
    effects: { household: { id: "HH308", buildingId: null, zoneId: "D7", lon: 100, lat: 7, precision: "zone", people: 2, elderly: 1, children: 0, cannotWalk: 1, urgent: true, status: "open", firstHand: true, reportedByOthersOnly: false, messages: 2 } },
  };
  it("explains why a family asking to leave needs a ride", () => {
    expect(buildReportTrace(turn, 1, "now", 1).some(line => line.who === "rules" && line.what.includes("Family wants to leave; can't walk → teams see 'needs a ride'"))).toBe(true);
    expect(buildReportTrace({ ...turn, status: { ...status, wantsOut: false } }, 2, "now", 1).some(line => line.what.includes("needs a ride"))).toBe(false);
  });
  it("explains an urgent reopening after a team visit only from the returned state", () => {
    expect(buildReportTrace(turn, 1, "now", 1, null, true).some(line => line.what.includes("case reopened, urgent"))).toBe(true);
    expect(buildReportTrace({ ...turn, status: { ...status, status: "safe" } }, 2, "now", 1, null, true).some(line => line.what.includes("case reopened"))).toBe(false);
  });
});

describe("quick action payloads", () => {
  it("uses the requested replies, prefills neighbour text and reveals the emergency phone", async () => {
    const send = vi.fn().mockResolvedValue(true), prefill = vi.fn(), emergency = vi.fn();
    for (const action of QUICK_ACTIONS) await runQuickAction(action, send, prefill, emergency);
    expect(send.mock.calls).toEqual([
      ["น้ำขึ้นเร็วมาก", "checkin"], ["ต้องการออกจากบ้าน", "leaveAsk"],
      ["มีคนบาดเจ็บ ต้องการความช่วยเหลือด่วน", "checkin"], ["ปลอดภัยดี", "checkin"],
    ]);
    expect(prefill).toHaveBeenCalledTimes(1);
    expect(prefill).toHaveBeenCalledWith("บ้านทาง");
    expect(emergency).toHaveBeenCalledTimes(1);
  });
  it("passes replyTo through the API and uses the status and simulate routes", async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) });
    vi.stubGlobal("fetch", fetcher);
    await v2.turn("S1", "ปลอดภัยดี", "chat", undefined, "checkin");
    expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual({ text: "ปลอดภัยดี", channel: "chat", replyTo: "checkin" });
    await v2.simulate("S1", "teamVisit");
    expect(fetcher.mock.calls[1][0]).toBe("/api/v2/chat/sessions/S1/simulate");
    expect(JSON.parse(fetcher.mock.calls[1][1].body)).toEqual({ event: "teamVisit" });
    await v2.status("S1");
    expect(fetcher.mock.calls[2][0]).toBe("/api/v2/chat/sessions/S1/status");
  });
});

describe("checklist rows", () => {
  it("puts each native checkbox beside one Thai label with its English gloss below", () => {
    const html = renderToStaticMarkup(<ReadyChecklist items={[["โทรศัพท์", "Phone"], ["เอกสาร", "Papers"]]} />);
    expect(html.match(/<label/g)).toHaveLength(2);
    expect(html).toMatch(/<label class=""><input type="checkbox"\/><span>โทรศัพท์<small>Phone<\/small><\/span><\/label>/);
    expect(html).toContain('<progress value="0" max="2"');
    expect(html).not.toContain("<img");
  });
});
