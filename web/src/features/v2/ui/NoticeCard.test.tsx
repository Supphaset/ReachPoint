import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import { BoatRequestCard, NoticeCard, noticeTone } from "./NoticeCard";
import { ChoiceButtons, FamilyStatusCard, ReadyChecklist } from "./FamilyFollowUp";
import type { FamilyStatus } from "../api";

const unknown: FamilyStatus = {
  householdId: null, zoneId: null, status: "open", urgent: false, wantsOut: false,
  people: null, water: null, team: null, outcome: null, shelter: null,
  nextCheck: "16:30", now: "14:30",
};

describe("rich cards", () => {
  it("bands water warnings, progress and questions separately", () => {
    for (const kind of ["river", "rain", "rainRise", "earlyWarning"]) expect(noticeTone(kind)).toBe("water");
    for (const kind of ["planUpdate", "pickedUp", "teamVisit"]) expect(noticeTone(kind)).toBe("done");
    for (const kind of ["askBack", "quiet", "unknown"]) expect(noticeTone(kind)).toBe("ink");
    expect(renderToStaticMarkup(<NoticeCard kind="river" at="14:30">น้ำขึ้น</NoticeCard>)).toContain("River alert");
  });
  it("keeps a boat request separate from an actual plan or pickup", () => {
    const html = renderToStaticMarkup(<BoatRequestCard status={unknown} />);
    expect(html).toContain("People unknown");
    expect(html).toContain("Waiting for a team plan");
    expect(html).not.toContain("Sent to");
  });
  it("shows checklist completion without inventing items", () => {
    const html = renderToStaticMarkup(<ReadyChecklist items={[["โทรศัพท์", "Phone"], ["เอกสาร", "Papers"]]} />);
    expect(html).toContain("0/2");
    expect(html).toContain('value="0" max="2"');
    expect(html.match(/type="checkbox"/g)).toHaveLength(2);
  });
  it("makes visit answers full width and marks the still-inside reply urgent", () => {
    const send = vi.fn().mockResolvedValue(true);
    const html = renderToStaticMarkup(<ChoiceButtons kind="pickedUp" disabled onSend={send} options={[
      { label: "ออกมาแล้ว · We're out", send: "ออกมาแล้ว" },
      { label: "ยังมีคนติดอยู่ · Someone is still inside", send: "ยังมีคนติดอยู่" },
      { label: "ออกมาเอง · Left on our own", send: "ออกมาเอง" },
    ]} />);
    expect(html).toContain("is-visit");
    expect(html).toContain("is-sos");
    expect(html.match(/disabled=""/g)).toHaveLength(3);
    expect(send).not.toHaveBeenCalled();
  });
  it("keeps unknown status values unknown and exposes details through a summary", () => {
    const html = renderToStaticMarkup(<FamilyStatusCard status={unknown} />);
    expect(html).toContain("<summary>");
    expect(html).toContain("Shelter unknown");
    expect(html).toContain("No team planned yet");
    expect(html).not.toContain("0.0");
    expect(html).not.toContain("🏠");
  });
});
