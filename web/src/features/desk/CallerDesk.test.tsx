import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LangProvider } from "../../i18n/lang";
import { CallerDesk, type CallerRow, type CallerReview } from "./CallerDesk";

const state = vi.hoisted(() => ({ rows: [] as CallerRow[] }));
vi.mock("../../data/useView", () => ({ useView: () => ({ status: "ready", connection: "live", data: {
  callers: state.rows, counts: { total: state.rows.length, ai_read: 1, human_reviewed: 0, needs_review: 1 },
} }) }));
const review: CallerReview = { transport_recommendation: "boat", emergency_level: "1b", immediate_danger: true,
  checked_by: "AI", review_status: "human_review_required", source: "gemini:fixture", reviewed_by: null,
  reviewed_at: "2026-10-15T03:00:00Z", review_revision: 1, volunteer_summary: "Reported medication need; medicine name unknown.",
  reasons: ["Water reaching last refuge"], evidence: [{ field: "emergency_detail", quote: "Water reaching last refuge", kind: "rescue_emergency" }],
  missing_information: ["Confirm access"] };
const row: CallerRow = { report_id: "R-SYNTHETIC", channel: "form", type: "evacuation", phone_number: "0000000000",
  people_details: "One older adult", n_children: 0, n_elders: 1, n_pets: null, location: "Synthetic school",
  coordinates: null, location_details: null, water_level: "Chest deep", situation_details: "Water rising",
  emergency_detail: "Water reaching last refuge", other_details: null, input_revision: "synthetic-revision",
  received_at: "2026-10-15T03:00:00Z", report_status: "proposed", review_stale: false,
  immediate_danger: true, reported_emergency_level: null, review, history: [review] };
afterEach(() => vi.unstubAllEnvs());

describe("caller desk", () => {
  it("shows evidence, urgency, transport, provenance and optional preparation", () => {
    vi.stubEnv("VITE_DATA", "api"); state.rows = [row];
    const html = renderToStaticMarkup(<CallerDesk />);
    for (const text of ["Boat candidate", "1b · Urgent rescue", "Immediate danger reported",
      "Volunteer preparation brief", "AI summary · optional", "medicine name unknown", "Supporting caller quotes",
      "Volunteer summary (optional)", "Save human review"]) expect(html).toContain(text);
    expect(html).toContain('<strong class="caller-area">Synthetic school</strong>');
    expect(html).toContain('<details class="caller-full-report"><summary>Full caller report &amp; details</summary>');
    expect(html).toContain("Water reaching last refuge");
    expect(html).not.toContain("Assign team");
  });
  it("keeps absent AI results unresolved and has Thai labels", () => {
    vi.stubEnv("VITE_DATA", "api"); state.rows = [{ ...row, review: null, immediate_danger: false, history: [] }];
    const html = renderToStaticMarkup(<LangProvider lang="th"><CallerDesk /></LangProvider>);
    expect(html).toContain("ยังไม่ได้ตรวจสอบ");
    expect(html).toContain("ต้องประเมินการเข้าถึง");
    expect(html).toContain("สรุปเตรียมทีม (ไม่บังคับ)");
    expect(html).not.toContain("AI summary for volunteer preparation");
  });
  it("labels routine requests as level 3 and preserves human provenance", () => {
    vi.stubEnv("VITE_DATA", "api"); state.rows = [{ ...row, immediate_danger: false, review: {
      ...review, emergency_level: "3", immediate_danger: false, checked_by: "Human", review_status: "human_reviewed", source: "human", volunteer_summary: null,
    } }];
    const html = renderToStaticMarkup(<CallerDesk />);
    expect(html).toContain("3 · Routine");
    expect(html).toContain("Human reviewed");
    expect(html).not.toContain("AI summary · optional");
  });
  it("preserves reported danger before review and does not invent an area or a routine level", () => {
    vi.stubEnv("VITE_DATA", "api"); state.rows = [{ ...row, location: null, review: null, history: [], reported_emergency_level: "1b" }];
    const html = renderToStaticMarkup(<CallerDesk />);
    expect(html).toContain("Area not reported");
    expect(html).toContain("1b · Urgent rescue");
    expect(html).toContain("Immediate danger reported");
    expect(html).toContain("No preparation summary available. Review can continue.");
    expect(html).not.toContain('<option value="3" selected="">');
  });
});
