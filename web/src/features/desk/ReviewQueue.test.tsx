import { renderToStaticMarkup } from "react-dom/server";
import { describe, it, expect, vi, afterEach } from "vitest";
import { LangProvider } from "../../i18n/lang";
import type { ReviewQueueView, ReviewRow } from "../../data/contract";
import { ReviewQueue, selectedReport } from "./ReviewQueue";
import { DeskPage } from "./RisingWater";

const state = vi.hoisted(() => ({ queue: { reports: [], landmarks: [], triage: null } as unknown as ReviewQueueView }));
vi.mock("../../data/useView", () => ({ useView: (path: string) => path?.includes("reviewQueue") ? { status: "ready", data: state.queue } : { status: "loading" } }));
vi.mock("../../data/teamStore", () => ({ useTeam: () => ({ status: "loading" }), loadTeam: vi.fn() }));
const report = (id: string, text: string): ReviewRow => ({ reportId: id, text, receivedAt: "2026-10-11T03:00:00Z", channel: "text", suggestedSegment: { segmentId: "B-3", label: "L2", why: "Caller said L2" }, prompts: [], triage: null, proposal: { source: "gemini:fixture", note: null, dropped: [], facts: { kind: "my_household", kindQuote: text, people: { adults: 2, children: 0, infants: 0, stretcher: 0, quote: text }, needs: [{ type: "evacuation_transport", quote: text }], water: null, place: null, dangerSigns: [], cantWalk: null, summary: "" } } });
afterEach(() => vi.unstubAllEnvs());
function setup(reports: ReviewRow[]) { vi.stubEnv("VITE_DATA", "api"); state.queue = { generatedAt: "", label: "", reports, landmarks: [{ segmentId: "B-3", label: "L2" }], triage: null }; }
describe("desk inbox", () => {
  it("selects the first server-ranked request without reordering, and keeps an existing selection", () => {
    const reports = [report("R-9", "Danger first"), report("R-1", "Later")];
    expect(selectedReport(reports, null)?.reportId).toBe("R-9");
    expect(selectedReport(reports, "R-1")?.reportId).toBe("R-1");
    expect(selectedReport(reports.slice(1), "R-9")?.reportId).toBe("R-1");
    setup(reports);
    const out = renderToStaticMarkup(<ReviewQueue />);
    expect(out.indexOf("R-9")).toBeLessThan(out.indexOf("R-1"));
    expect(out).toContain('aria-pressed="true"');
    expect(out).toContain("Approve: 2 people");
    expect(out).toContain("Decrease Adults");
    expect(out).toContain("Reject");
  });
  it("preselects the located landmark ahead of an older suggestion", () => {
    const r = report("R-location", "Synthetic request");
    r.location = { status: "located", kind: "pin", method: "map", at: [100.4705, 7.0089], precision: "house", source: "caller pin (map)", provider: "device", segmentId: "B-3-L2", zoneId: "B-3", landmarkLabel: "B-3 · L2 Market" };
    setup([r]);
    state.queue.landmarks.push({ segmentId: "B-3-L2", label: "B-3 · L2 Market" });
    const out = renderToStaticMarkup(<ReviewQueue />);
    expect(out).toContain('<option value="B-3-L2" selected="">');
    expect(out).toContain("Fix location");
    expect(out).toContain('class="desk-location-search" hidden=""');
    expect(out).toContain("from the caller&#x27;s map pin");
  });
  it("puts the caller message before the location and uses the caller’s GPS copy", () => {
    const r = report("R-001", "Synthetic family needs help");
    r.location = { status: "located", kind: "pin", method: "gps", at: [100.4705, 7.0089], precision: "house", source: "synthetic", provider: "device" };
    setup([r]);
    const out = renderToStaticMarkup(<ReviewQueue />);
    expect(out.indexOf('<blockquote class="review-text">')).toBeLessThan(out.indexOf('class="location-block"'));
    expect(out).toContain("from the caller&#x27;s phone GPS");
    expect(out).not.toContain("from your phone");
    expect(out).toContain('aria-expanded="false"');
    const thai = renderToStaticMarkup(<LangProvider lang="th"><ReviewQueue /></LangProvider>);
    expect(thai).toContain("จาก GPS โทรศัพท์ของผู้แจ้ง");
    expect(thai).toContain("แก้ตำแหน่ง");
  });
  it("explains the empty queue without an approval form", () => {
    setup([]);
    const out = renderToStaticMarkup(<ReviewQueue />);
    expect(out).toContain("No requests waiting");
    expect(out).toContain("New calls and requests will appear here");
    expect(out).not.toContain("Approve:");
    expect(selectedReport([], null)).toBeUndefined();
  });
  it("renders Thai desk tools and review controls while preserving caller quotes", () => {
    setup([report("R-2", "Please help our family")]);
    const out = renderToStaticMarkup(<LangProvider lang="th"><DeskPage /></LangProvider>);
    expect(out).toContain("โต๊ะประสานงาน");
    expect(out).toContain("อนุมัติ: 2 คน");
    expect(out).toContain("ปฏิเสธ");
    expect(out).toContain("ข้อเสนอจาก AI ต้องให้คุณอนุมัติ");
    expect(out).toContain("Please help our family");
    expect(out).not.toContain("Coordinator desk");
  });
  it("retains duplicate controls and refuses to link a new danger away", () => {
    const r = report("R-3", "Help");
    r.triage = { source: "fixture", at: "", rank: null, links: [{ caseId: "C-03", place: "L2", people: 2, reason: "Same words", quote: "Help", newHazard: false }] };
    setup([r]);
    expect(renderToStaticMarkup(<ReviewQueue />)).toContain("Link to C-03");
    expect(renderToStaticMarkup(<ReviewQueue />)).toContain("Not the same");
    r.triage.links[0].newHazard = true;
    const out = renderToStaticMarkup(<ReviewQueue />);
    expect(out).toContain("review it on its own");
    expect(out).not.toContain("Link to C-03");
  });
});
