import type { ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { resolveUiLang, saveUiLang, UI_LANG_KEY, t, Tr, UiLangProvider, useT, type UiLang } from "./lang";
import { StepHeader } from "./Shared";
import { DemoBar } from "./DemoBar";
import { UrgentList } from "../volunteer/UrgentList";
import { ChatHeader, GeminiReceipt } from "./ChatShell";
import { FamilyStatusCard, QuickActions, ReadyChecklist, runQuickAction, QUICK_ACTIONS } from "./FamilyFollowUp";
import { BoatRequestCard, NoticeCard } from "./NoticeCard";
import { DepthBars } from "./DepthBars";
import { LocationCard } from "./LocationCard";
import { ShelterAnswers, WaterLegend } from "./ShelterCard";
import { Trend } from "../volunteer/shared";
import { SectorMap } from "../volunteer/SectorMap";
import { ReportTabs } from "../V2Page";
import type { FamilyStatus } from "../api";

function markup(children: ReactNode, lang: UiLang = "en") {
  return renderToStaticMarkup(<UiLangProvider initialLang={lang}><MemoryRouter>{children}</MemoryRouter></UiLangProvider>);
}

const status: FamilyStatus = {
  householdId: "HH308", zoneId: "D7", status: "open", urgent: false, wantsOut: false, people: 2,
  water: { nowM: 0.81, loM: 0.6, hiM: 1, in6hM: 1.24, trend: "rising", reports: 3 },
  team: null, outcome: null, shelter: { name: "School", km: 1.2, deepestM: 0.4, walkable: true, minutes: 20 },
  nextCheck: "16:30", now: "14:30",
};

describe("v2 UI language", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("saves a toggle choice and replaces just the language URL parameter", () => {
    const setItem = vi.fn();
    const replaceState = vi.fn();
    const state = { idx: 2 };
    vi.stubGlobal("window", {
      location: { href: "https://demo.example/v?data=api&room=judge&lang=th#map" },
      localStorage: { setItem }, history: { state, replaceState },
    });
    saveUiLang("en");
    expect(setItem).toHaveBeenCalledWith(UI_LANG_KEY, "en");
    expect(replaceState).toHaveBeenCalledWith(state, "", new URL("https://demo.example/v?data=api&room=judge&lang=en#map"));
    setItem.mockImplementation(() => { throw new Error("Storage blocked"); });
    expect(() => saveUiLang("th")).not.toThrow();
    expect(replaceState).toHaveBeenCalledTimes(2);
  });

  it("resolves URL before storage, and storage before navigator", () => {
    const storage = vi.fn(() => "th");
    expect(resolveUiLang("?data=api&lang=en", storage, "th-TH")).toBe("en");
    expect(storage).not.toHaveBeenCalled();
    expect(resolveUiLang("?lang=th", () => "en", "en-US")).toBe("th");
    expect(resolveUiLang("", () => "en", "th-TH")).toBe("en");
    expect(resolveUiLang("?lang=invalid", () => "th", "en-US")).toBe("th");
    expect(resolveUiLang("", () => null, "th-TH")).toBe("th");
    expect(resolveUiLang("", () => "invalid", "fr-FR")).toBe("en");
    expect(resolveUiLang("", () => { throw new Error("Storage blocked"); }, "en-US")).toBe("en");
  });

  it("selects explicit text pairs and keeps a small gloss only in Thai", () => {
    expect(t("รอ", "Waiting", "en")).toBe("Waiting");
    expect(t("รอ", "Waiting", "th")).toBe("รอ");
    function Sample() {
      const text = useT();
      return <div title={text("สถานะ", "Status")}><Tr th="รอ" en="Waiting" /></div>;
    }
    expect(markup(<Sample />)).toBe('<div title="Status">Waiting</div>');
    expect(markup(<Sample />, "th")).toBe('<div title="สถานะ">รอ<small class="rp-gloss">Waiting</small></div>');
  });

  it("places both 44px language buttons in the shared header, with the selected state", () => {
    for (const lang of ["en", "th"] as const) {
      const html = markup(<StepHeader showDemo={false} />, lang);
      expect(html).toContain('class="rp-language" role="group" aria-label="UI language"');
      expect(html).toContain(`lang="${lang}" aria-pressed="true"`);
      expect(html).toContain(`lang="${lang === "en" ? "th" : "en"}" aria-pressed="false"`);
      expect(html).toContain('>ไทย</button>');
      expect(html).toContain('>EN</button>');
      expect(html.indexOf('class="rp-language"')).toBeLessThan(html.indexOf('class="rp-steps"'));
    }
  });

  it("renders the demo launcher and urgent cases without Thai in English", () => {
    const html = markup(<>
      <DemoBar onAction={async () => undefined} family={{ enabled: true, busy: false, result: "", done: ["rain"], onSimulate: async () => undefined }} />
      <UrgentList data={{ atH: 0, at: "07:00", total: 1, zones: [{ id: "D1", label: "School", sector: "D", plans: 2, depthM: 1.2, score: 100,
        cases: [{ id: "HH001", zoneId: "D1", lon: null, lat: null, people: 2, elderly: 1, children: 0, cannotWalk: 1, urgent: true, status: "open", boat: true, messages: 1, firstHand: true, possibleDuplicateOf: null, outcome: null, reportedBy: "family", priority: 75, hoursSilent: 12, lastHeard: "06:00", depth: null, needs: ["cannotWalk"], markedFirst: { team: "Boat 1", at: "07:00" } }],
      }] }} zones={[]} team="Boat 2" busy={false} highlighted="HH001" onZone={() => undefined} onFirst={async () => undefined} />
    </>);
    expect(html).not.toMatch(/[฀-๿]/);
    for (const text of ["Next: River rising", "2 teams", "silent 12", "School", "Can&#x27;t walk", "boat only"]) expect(html).toContain(text);
  });

  it("renders dynamic card chrome, reply actions, tabs and map keys in English", () => {
    // SSR does not draw the flood canvas; only its element needs a stand-in.
    vi.stubGlobal("document", { createElement: () => ({}) });
    const html = markup(<>
      <FamilyStatusCard status={status} />
      <BoatRequestCard status={status} />
      <NoticeCard kind="unknown">English server message</NoticeCard>
      <ChatHeader busy={false} onCall="off" toggleCall={() => undefined} speak={false} toggleSpeak={() => undefined} restart={() => undefined} />
      <GeminiReceipt facts={[{ field: "people", value: 2, quote: "2 people" }]} />
      <QuickActions disabled={false} onSend={async () => true} onPrefill={() => undefined} />
      <ReadyChecklist items={[["โทรศัพท์", "Phone"]]} />
      <DepthBars model={0.8} corrected={[1, 0.6, 1.2]} />
      <LocationCard busy={false} outside={false} onPin={async () => undefined} />
      <ShelterAnswers walkable onAnswer={async () => true} disabled={false} />
      <WaterLegend />
      <SectorMap geo={null} zones={[]} selection={{ sector: null, zone: null, hover: null }} onZone={() => undefined} onSector={() => undefined} />
      <Trend water={{ past3hM: null, trend: "rising", next6hM: 0.2 }} long />
      <ReportTabs tab="map" onChange={() => undefined} />
    </>);
    expect(html).not.toMatch(/[฀-๿]/);
    expect(html).toContain("1.2 m");
    expect(html).toContain("16:30");
    expect(html).not.toContain("EN / ");
  });

  it("sends English quick-action payloads in an English session", async () => {
    const send = vi.fn().mockResolvedValue(true);
    const prefill = vi.fn();
    await runQuickAction(QUICK_ACTIONS[0], send, prefill, () => undefined, "en");
    runQuickAction(QUICK_ACTIONS[3], send, prefill, () => undefined, "en");
    expect(send).toHaveBeenCalledWith("Water is rising very fast", "checkin");
    expect(prefill).toHaveBeenCalledWith("The house to the ");
  });
});
