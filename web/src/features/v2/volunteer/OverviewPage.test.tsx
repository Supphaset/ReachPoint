import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { Overview } from "../api";
import { UiLangProvider } from "../ui/lang";
import { VolunteerKpis } from "./OverviewPage";

const data = {
  overall: { messages: 1064, households: 307, duplicatesMerged: 66, estimatedHouseholdsAffected: 34947 },
  zones: [{ open: 215, urgent: 80, plans: 0 }],
  rain: { next6hMm: 17.9, past6hMm: 30.4, heavy: true, source: "Replay rain", kind: "replay" },
} as Overview;

describe("volunteer KPI strip", () => {
  it.each(["th", "en"] as const)("renders exactly four chips in %s with ledger numbers and rain provenance", lang => {
    const html = renderToStaticMarkup(<UiLangProvider initialLang={lang}><VolunteerKpis data={data} /></UiLangProvider>);
    expect(html.match(/class="v-kpi(?: is-urgent)?"/g)).toHaveLength(4);
    for (const text of ["80", "215", "17.9", "mm", "1,064", "307", "66", "34,947"]) expect(html).toContain(text);
    expect(html.match(/class="v-kpi is-urgent"/g)).toHaveLength(2);
    if (lang === "th") {
      for (const text of ["ด่วน", "รอ", "โซนไม่มีทีม", "ฝน 6 ชม.ข้างหน้า", "(Gemini · กฎเติมส่วนที่ขาด)"]) expect(html).toContain(text);
    } else {
      for (const text of ["urgent", "waiting", "zones with no team", "rain next 6 h", "(Gemini; rules fill gaps)"]) expect(html).toContain(text);
      expect(html).toContain("Replay rain · replay: rain that fell next, standing in for a forecast");
      expect(html).not.toMatch(/[฀-๿]/);
    }
  });
  it("keeps all four chips while data is loading", () => {
    const html = renderToStaticMarkup(<VolunteerKpis data={null} />);
    expect(html.match(/class="v-kpi(?: is-urgent)?"/g)).toHaveLength(4);
    expect(html).toContain("…");
  });
});
