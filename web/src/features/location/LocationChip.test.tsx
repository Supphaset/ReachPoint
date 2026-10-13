import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LangProvider } from "../../i18n/lang";
import type { Location } from "../../data/contract";
import { LocationChip } from "./LocationChip";
import { CallerLocation } from "./CallerLocation";
import { DeskLocation } from "./DeskLocation";
const location: Location = { status: "located", kind: "pin", method: "gps", at: [100.4705, 7.0089], precision: "house", source: "caller pin (GPS)", provider: "device", accuracyM: 25, zoneId: "B-3", segmentId: "B-3-L2", landmarkId: "B-3-L2", landmarkLabel: "B-3 · L2 Market" };
describe("location copy", () => {
  it("shows a GPS location chip in English with an icon and accuracy, never exact coordinates", () => {
    const out = renderToStaticMarkup(<LocationChip location={location} />);
    expect(out).toContain("Near B-3 · L2 Market");
    expect(out).toContain("from your phone&#x27;s GPS");
    expect(out).toContain("±25 m");
    expect(out).toContain("<svg");
    expect(out).not.toContain("100.4705");
  });
  it("translates generic landmarks, source and accuracy into Thai", () => {
    const out = renderToStaticMarkup(<LangProvider lang="th"><LocationChip location={location} /></LangProvider>);
    expect(out).toContain("ใกล้ B-3 · L2 ตลาด"); expect(out).toContain("จาก GPS ของโทรศัพท์คุณ"); expect(out).toContain("±25 ม.");
    expect(out).not.toContain("Market"); expect(out).not.toContain("Near");
  });
  it("labels unknown and outside statuses in both languages", () => {
    for (const [status, en, th] of [["unlocated", "Address not found", "ไม่พบที่อยู่"], ["outside_area", "Outside demo area", "นอกพื้นที่สาธิต"]] as const) {
      const loc = { ...location, status, at: null };
      expect(renderToStaticMarkup(<LocationChip location={loc} />)).toContain(en);
      const out = renderToStaticMarkup(<LangProvider lang="th"><LocationChip location={loc} /></LangProvider>);
      expect(out).toContain(th); expect(out).toContain("is-unknown");
    }
  });
  it("distinguishes map pins, Pinpoint matches and synthetic stand-in addresses", () => {
    expect(renderToStaticMarkup(<LocationChip location={{ ...location, method: "map" }} />)).toContain("pinned on the map");
    expect(renderToStaticMarkup(<LocationChip location={{ ...location, kind: "address", provider: "pinpoint" }} />)).toContain("Pinpoint address match");
    expect(renderToStaticMarkup(<LangProvider lang="th"><LocationChip location={{ ...location, kind: "address", provider: "stand-in" }} /></LangProvider>)).toContain("ที่อยู่จำลองที่พบในข้อมูลสาธิต");
  });
  it("renders the optional caller tools, privacy line and desk address tool in Thai and English", () => {
    const caller = <CallerLocation onChange={() => {}} onBusy={() => {}} />;
    expect(renderToStaticMarkup(caller)).toContain("Use my location");
    const out = renderToStaticMarkup(<LangProvider lang="th">{caller}</LangProvider>);
    expect(out).toContain("คุณอยู่ที่ไหน?"); expect(out).toContain("เลือกบนแผนที่"); expect(out).toContain("จุดที่แน่นอนจะแชร์เฉพาะผู้ประสานงาน");
    const desk = <DeskLocation location={location} disabled={false} onApply={() => {}} />;
    expect(renderToStaticMarkup(desk)).toContain("Fix location");
    expect(renderToStaticMarkup(desk)).toContain('class="desk-location-search" hidden=""');
    expect(renderToStaticMarkup(<LangProvider lang="th">{desk}</LangProvider>)).toContain("แก้ตำแหน่ง");
    expect(renderToStaticMarkup(<DeskLocation disabled={false} onApply={() => {}} />)).toContain("Address from the call");
  });
});
