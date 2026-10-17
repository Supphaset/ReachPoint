import type { ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { expect, it, vi } from "vitest";
import { UiLangProvider } from "../ui/lang";
import { CasePage } from "./CasePage";

vi.mock("./shared", () => ({
  useTeam: () => ["", () => undefined],
  useGeo: () => null,
  useLive: () => ({ data: {
    household: { id: "HH055", zoneId: "D7", reportedBy: "family", status: "open", hoursSilent: 2, messages: 1, firstHand: true },
    now: { at: "06:00", atH: 96 },
    story: [{ id: "M1", at: "06:00", source: "family", channel: "chat", reader: "rules",
      facts: [{ field: "cannotWalk", value: 1, quote: "แม่เดินไม่ได้" }], text: "แม่เดินไม่ได้" }],
    contact: { sent: [{ at: "06:00", kind: "check", text: "ทุกคนปลอดภัยไหม", en: "Is everyone safe?" }], replies: 1, unanswered: 0 },
    shelterOptions: [{ shelterId: "S1", name: "โรงเรียน", nameEn: "School", km: 1, minutes: 15, walkable: true, deepestM: 0.2 }],
    neighbours: [], possibleDuplicates: [], plans: [], depthSeries: [], depthReports: [],
  }, error: null, reload: () => undefined }),
  VShell: ({ children }: { children: ReactNode }) => <>{children}</>,
  Needs: () => null,
  StatusChip: () => null,
}));
vi.mock("./ZonePage", () => ({ familyTitle: () => "Family HH055" }));
vi.mock("../BoardMap", () => ({ BoardMap: () => null }));
vi.mock("../HouseScene", () => ({ HouseScene: () => null }));

it("shows English outbound messages and shelter names while preserving the family's Thai evidence", () => {
  const html = renderToStaticMarkup(<UiLangProvider initialLang="en"><MemoryRouter><CasePage /></MemoryRouter></UiLangProvider>);
  expect(html).toContain("Is everyone safe?");
  expect(html).not.toContain("ทุกคนปลอดภัยไหม");
  expect(html).toContain("School");
  expect(html).not.toContain("โรงเรียน");
  expect(html).toContain("แม่เดินไม่ได้");
  expect(html).toContain("unable to walk: 1");
});
