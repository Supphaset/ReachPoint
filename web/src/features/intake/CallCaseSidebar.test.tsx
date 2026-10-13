import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { CallSession } from "../../data/call";
import { LangProvider } from "../../i18n/lang";
import { CallCaseSidebar } from "./CallCaseSidebar";

function session(): CallSession {
  return {
    sessionId: "synthetic", revision: 0, lang: "en", pinned: null, messages: [],
    locationLookup: { status: "idle" }, canConfirm: false, summary: null, sent: null,
    case: {
      reporter_name: null, people_count: 2, people_details: "2 adults", children_count: 0,
      elderly_count: null, mobility_needs: null, location: "L1", landmark: null, coordinates: null,
      water_level: "knee", water_trend: null, current_shelter: null, injuries: null,
      urgent_needs: null, immediate_danger: null, danger_details: null, callback_contact: null,
      unavailable_fields: ["callback_contact"], contradictions: [],
    },
  };
}

describe("collected call details", () => {
  it.each(["en", "th"] as const)("shows progress, known and skipped rows, and one missing line in %s", lang => {
    const out = renderToStaticMarkup(<LangProvider lang={lang}><CallCaseSidebar session={session()} busy={false} onConfirm={() => {}} /></LangProvider>);
    expect(out).toContain("4/7");
    expect(out).toContain(lang === "en" ? "4 of 7 details collected" : "รวบรวมแล้ว 4 จาก 7 ข้อ");
    expect(out).toContain(lang === "en" ? "Still needed: " : "ยังต้องการ: ");
    expect(out).toContain(lang === "en" ? "skipped" : "ข้าม");
    expect(out).not.toContain(lang === "en" ? "Not yet known" : "ยังไม่ทราบ");
    const needed = out.match(/<p class="call-case-needed">(.*?)<\/p>/)?.[1];
    expect(needed).toContain(lang === "en" ? "Mobility needs" : "การเคลื่อนไหว / ความช่วยเหลือพิเศษ");
    expect(needed).not.toContain(lang === "en" ? "Callback number" : "เบอร์ติดต่อกลับ");
    expect(out).toMatch(/<dd[^>]*>0<\/dd>/); // a stated zero is a known fact
  });
  it("does not count declined details as collected and omits an empty missing line", () => {
    const current = session();
    current.case.unavailable_fields.push("mobility_needs");
    let out = renderToStaticMarkup(<CallCaseSidebar session={current} busy={false} onConfirm={() => {}} />);
    expect(out).toContain("4/7");
    for (const key of Object.keys(current.case)) {
      if (current.case[key as keyof typeof current.case] === null) current.case.unavailable_fields.push(key);
    }
    out = renderToStaticMarkup(<CallCaseSidebar session={current} busy={false} onConfirm={() => {}} />);
    expect(out).not.toContain("call-case-needed");
  });
});
