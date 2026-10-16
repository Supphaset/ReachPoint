import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LangProvider } from "../../i18n/lang";
import { CallerDesk, type CallerRow, type CallerReview, type ReviewLocation } from "./CallerDesk";

const state = vi.hoisted(() => ({ rows: [] as CallerRow[], aiEnabled: true, actor: null as string | null }));
vi.mock("../../data/session", () => ({ useSession: () => ({ session: state.actor ? { actor: state.actor } : null }) }));
vi.mock("../../data/useView", () => ({ useView: () => ({ status: "ready", connection: "live", data: {
  callers: state.rows, ai_enabled: state.aiEnabled, counts: { total: state.rows.length, ai_read: 1, human_reviewed: 0, needs_review: 1 },
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
afterEach(() => { vi.unstubAllEnvs(); state.aiEnabled = true; state.actor = null; });
const resolved: ReviewLocation = { address: "Synthetic school address", latitude: 7, longitude: 100.5, source: "google_maps_link", status: "resolved", map_url: "https://maps.google.com/?q=7,100.5" };

describe("caller desk", () => {
  it("highlights medication evidence and the current boat suggestion on the queue card", () => {
    vi.stubEnv("VITE_DATA", "api");
    state.rows = [{ ...row, other_details: "Regular medication has run out", review: {
      ...review, evidence: [{ field: "other_details", quote: "Regular medication has run out", kind: "medication" }],
    } }];
    const html = renderToStaticMarkup(<CallerDesk />);
    const card = html.match(/<button[^>]*class="caller-request[^\"]*"[\s\S]*?<\/button>/)?.[0];
    expect(card).toContain("💊");
    expect(card).toContain("Medication reported");
    expect(card).toContain("🚤");
    expect(card).toContain("Boat suggested");
  });
  it("does not imply medication or boat needs from unknown or outdated results", () => {
    vi.stubEnv("VITE_DATA", "api");
    for (const r of [{ ...row, review: null }, { ...row, review: { ...review, transport_recommendation: "needs_assessment" as const } },
      { ...row, review_stale: true, review: { ...review, evidence: [{ field: "other_details", quote: "Old medication report", kind: "medication" }] } }]) {
      state.rows = [r];
      const html = renderToStaticMarkup(<CallerDesk />);
      expect(html).not.toContain('class="caller-need-tags"');
    }
  });
  it("allows approval with only the original required fields while AI results are absent", () => {
    vi.stubEnv("VITE_DATA", "api"); state.actor = "coordinator:synthetic";
    state.rows = [{ ...row, review: null, history: [], ai_processing: true, immediate_danger: false, reported_emergency_level: null }];
    const html = renderToStaticMarkup(<CallerDesk />);
    const button = [...html.matchAll(/<button\b[^>]*>[\s\S]*?<\/button>/g)].find(([button]) => button.includes("Approve review"))?.[0];
    expect(button).toBeDefined();
    expect(button).not.toContain("disabled");
    expect(html).toContain("Other fields can be completed later.");
    expect(html).toContain("Approval advances caller tracking to Reviewing request.");
  });
  it("blocks approval when an original required field is missing", () => {
    vi.stubEnv("VITE_DATA", "api"); state.actor = "coordinator:synthetic";
    for (const field of ["phone_number", "type", "location"] as const) {
      state.rows = [{ ...row, [field]: null }];
      const html = renderToStaticMarkup(<CallerDesk />);
      const button = [...html.matchAll(/<button\b[^>]*>[\s\S]*?<\/button>/g)].find(([button]) => button.includes("Approve review"))?.[0];
      expect(button).toBeDefined();
      expect(button).toContain("disabled");
      expect(html).toContain("Required: ");
    }
  });
  it("shows the chosen depth threshold and emergency guideline without inventing a measurement", () => {
    vi.stubEnv("VITE_DATA", "api"); state.rows = [{ ...row, review: { ...review, transport_threshold_cm: 50, reported_water_depth_cm: null } }];
    let html = renderToStaticMarkup(<CallerDesk />);
    expect(html).toContain("No measured water depth reported.");
    expect(html).toContain("Boat planning preference starts at 50 cm.");
    expect(html).toContain("Emergency evaluation guideline");
    state.rows = [{ ...row, review: { ...review, transport_threshold_cm: 50, reported_water_depth_cm: 60 } }];
    html = renderToStaticMarkup(<CallerDesk />);
    expect(html).toContain("Reported water: 60 cm.");
    state.rows = [{ ...row, review: { ...review, transport_threshold_cm: 50, reported_water_depth_cm: null, transport_basis: "qualitative_water" } }];
    html = renderToStaticMarkup(<CallerDesk />);
    expect(html).toContain("Boat suggested from reported waist/chest/head-level water; exact depth is unmeasured.");
  });
  it("shows evidence, urgency, transport, provenance and optional preparation", () => {
    vi.stubEnv("VITE_DATA", "api"); state.rows = [row,
      { ...row, report_id: "R-SYNTHETIC-CHAT", channel: "chat", location: "Synthetic market", review: null, history: [] },
      { ...row, report_id: "R-SYNTHETIC-VOICE", channel: "voice", location: "Synthetic temple", review: { ...review, checked_by: "Human" } },
    ];
    const html = renderToStaticMarkup(<CallerDesk />);
    for (const text of ["Boat candidate", "1b · Urgent rescue", "Immediate danger reported",
      "Volunteer prep notes", "Optional", "medicine name unknown", "Supporting caller quotes",
      "Awaiting human approval", "Approve review", "Edit details", "Text address", "Coordinates"]) expect(html).toContain(text);
    expect(html).toContain('<strong class="caller-area">Synthetic school</strong>');
    expect(html).toContain('<details class="caller-full-report"><summary>Full caller report &amp; details</summary>');
    expect(html).toContain("Water reaching last refuge");
    expect(html).not.toContain("Assign team");
    expect(html).toContain("All requests");
    expect((html.match(/class="caller-request"/g) ?? []).length).toBe(3);
    expect(html).toContain('<strong class="caller-area">Synthetic market</strong>');
    expect(html).toContain('<strong class="caller-area">Synthetic temple</strong>');
  });
  it("keeps absent AI results unresolved and has Thai labels", () => {
    vi.stubEnv("VITE_DATA", "api"); state.rows = [{ ...row, review: null, immediate_danger: false, history: [] }];
    const html = renderToStaticMarkup(<LangProvider lang="th"><CallerDesk /></LangProvider>);
    expect(html).toContain("ยังไม่ได้ตรวจสอบ");
    expect(html).toContain("ต้องประเมินการเข้าถึง");
    expect(html).toContain("บันทึกเตรียมอาสาสมัคร");
    expect(html).toContain("รอคนอนุมัติ");
    expect(html).not.toContain("AI summary for volunteer preparation");
  });
  it("labels routine requests as level 3 and preserves human provenance", () => {
    vi.stubEnv("VITE_DATA", "api"); state.rows = [{ ...row, immediate_danger: false, review: {
      ...review, emergency_level: "3", immediate_danger: false, checked_by: "Human", review_status: "human_reviewed", source: "human", volunteer_summary: null,
    } }];
    const html = renderToStaticMarkup(<CallerDesk />);
    expect(html).toContain("3 · Routine");
    expect(html).toContain("Human reviewed");
    expect(html).toContain("Awaiting human approval");
    expect(html).not.toContain("Human approved");
  });
  it("preserves reported danger before review and does not invent an area or a routine level", () => {
    vi.stubEnv("VITE_DATA", "api"); state.rows = [{ ...row, location: null, review: null, history: [], reported_emergency_level: "1b" }];
    const html = renderToStaticMarkup(<CallerDesk />);
    expect(html).toContain("Area not reported");
    expect(html).toContain("1b · Urgent rescue");
    expect(html).toContain("Immediate danger reported");
    expect(html).toContain("No preparation notes. Approval does not require notes.");
    expect(html).not.toContain('<option value="3" selected="">');
  });
  it("shows resolved AI results with no optional notes", () => {
    vi.stubEnv("VITE_DATA", "api");
    state.rows = [{ ...row, review: { ...review, resolved_location: resolved, volunteer_summary: null } }];
    const html = renderToStaticMarkup(<CallerDesk />);
    expect(html).toContain("7, 100.5");
    expect(html).toContain("Synthetic school address");
    expect(html).toContain("Google Maps");
    expect(html).toContain("No preparation notes. Approval does not require notes.");
    expect(html).not.toContain('class="caller-review-rail"');
    // There is no coordinator session in this SSR render, so approval stays disabled.
    expect(html).toContain("Approve review");
    expect(html).not.toContain("Run AI review");
  });
  it("shows an explicit human approval and invalidates it when the input is stale", () => {
    vi.stubEnv("VITE_DATA", "api");
    const approved = { ...row, review: { ...review, checked_by: "Human" as const, resolved_location: resolved, approved: true, approved_by: "coordinator:synthetic", approved_at: review.reviewed_at } };
    state.rows = [approved];
    expect(renderToStaticMarkup(<CallerDesk />)).toContain("Human approved");
    state.rows = [{ ...approved, review_stale: true }];
    const stale = renderToStaticMarkup(<CallerDesk />);
    expect(stale).not.toContain("Human approved");
    expect(stale).toContain("previous approval no longer applies");
  });
  it("does not claim AI is running when it is disabled", () => {
    vi.stubEnv("VITE_DATA", "api"); state.aiEnabled = false;
    state.rows = [{ ...row, location: "https://maps.app.goo.gl/synthetic", review: null, history: [] }];
    const html = renderToStaticMarkup(<CallerDesk />);
    expect(html).toContain("Automatic AI review is unavailable");
    expect(html).toContain("Shared map location");
    expect(html).not.toContain("AI is reviewing location");
  });
});
