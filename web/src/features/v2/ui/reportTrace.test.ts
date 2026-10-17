import { describe, expect, it } from "vitest";
import type { TurnResult } from "../api";
import { buildReportTrace } from "./reportTrace";
const turn: TurnResult = {
  session: {
    id: "session", token: "synthetic-test-token", lang: "th", householdId: "HH308", pin: null,
    buildingId: "B1", zoneId: "D12", transcript: [], neighbours: [], pending: null, finished: false,
  },
  reply: "มีบ้านใกล้ ๆ ที่ยังติดอยู่ไหมคะ",
  effects: {
    reader: "gemini:test",
    facts: [{ field: "cannotWalk", value: 1, quote: "แม่เดินไม่ได้" }],
    located: { by: "address", zoneId: "D12", buildingId: "B1" },
    household: {
      id: "HH308", buildingId: "B1", zoneId: "D12", lon: 100.47, lat: 7.01, precision: "building",
      people: 2, elderly: 1, children: 0, cannotWalk: 1, urgent: true, status: "open",
      firstHand: true, reportedByOthersOnly: false, messages: 1,
    },
    simHere: 0.6,
    depthHere: [1.0, 0.9, 1.1],
  },
  zone: null,
};
describe("report trace builder", () => {
  it("builds quoted reading, location, urgency, depth correction and next question from a turn", () => {
    const trace = buildReportTrace(turn, 1, "25 Nov 06:00", 96);
    expect(trace.map(line => line.who)).toEqual(["gemini", "rules", "rules", "physics", "gemini"]);
    expect(trace[0]).toMatchObject({ quote: "แม่เดินไม่ได้", gloss: "unable to walk: 1", to: "/v/case/HH308" });
    expect(trace[1].to).toBe("/v/zone/D12");
    expect(trace[2].what).toContain("HH308 flagged urgent");
    expect(trace[3].what).toContain("Model 0.6 m → model + reports 1.0 m · likely 0.9–1.1 m");
    expect(trace[4]).toMatchObject({ quote: turn.reply, gloss: "The agent is asking about nearby households." });
    expect(trace.every(line => line.atH === 96 && line.at === "25 Nov 06:00")).toBe(true);
  });
  it("only emits an action for a confirmed neighbour and keeps known households deduplicated", () => {
    const neighbour = { side: "east", known: true, householdId: "HH309", buildingId: "B2", sure: false };
    expect(buildReportTrace({ ...turn, effects: { neighbour } }, 2, "06:01", 96).some(line => line.who === "action")).toBe(false);
    const trace = buildReportTrace({ ...turn, effects: { neighbour: { ...neighbour, sure: true } } }, 3, "06:02", 96);
    expect(trace[trace.length - 1]).toMatchObject({ who: "action", to: "/v/case/HH309" });
    expect(trace[trace.length - 1]?.what).toContain("already known; not counted twice");
  });
  it("keeps rule readers honest and does not invent facts, urgent flags or depth values", () => {
    const trace = buildReportTrace({ ...turn, reply: "How many people?", effects: { reader: "rules" } }, 4, "06:03", 96);
    expect(trace).toHaveLength(1);
    expect(trace[0]).toMatchObject({ who: "rules", quote: "How many people?" });
    expect(buildReportTrace({ ...turn, reply: "", effects: {} }, 5, "06:04", 96)).toEqual([]);
  });
  it("keeps GPS/pin provenance and distinguishes street routes from direct lines", () => {
    const route = {
      shelterId: "S1", name: "ศูนย์ตัวอย่าง", kind: "school", lon: 100.48, lat: 7.01,
      km: 1.2, minutes: 18, deepestM: 0.4, walkable: true, by: "streets" as const,
      path: [], samples: [], deepestAt: [100.48, 7.01] as [number, number],
      from: [100.47, 7.01] as [number, number], googleMaps: "https://www.google.com/maps/dir/",
    };
    const trace = buildReportTrace({ ...turn, effects: { located: { by: "your GPS", zoneId: "D12", buildingId: "B1" }, shelterRoute: route } }, 6, "06:05", 96);
    expect(trace[0]).toMatchObject({ who: "rules" });
    expect(trace[0].what).toContain("Located your house from your GPS");
    expect(trace[1]).toMatchObject({ who: "physics", what: "Walk to ศูนย์ตัวอย่าง: deepest ~0.4 m along the streets" });
    const direct = buildReportTrace({ ...turn, effects: { shelterRoute: { ...route, by: "direct line" } } }, 7, "06:06", 96);
    expect(direct[0].what).toContain("direct line (no street route)");
  });

});
