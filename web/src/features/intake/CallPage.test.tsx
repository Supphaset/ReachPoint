import { Children, isValidElement, type ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { CallSession } from "../../data/call";
import { CallPage } from "./CallPage";

// Node-only test harness: exercise the actual page handlers without DOM packages or network calls.
const harness = vi.hoisted(() => ({ values: [] as unknown[], index: 0, refIndex: 0, lang: "en" as "en" | "th", focus: vi.fn(), send: vi.fn() }));
vi.mock("react", async importOriginal => ({
  ...await importOriginal<typeof import("react")>(),
  useEffect: vi.fn(),
  useState: (initial: unknown) => {
    const index = harness.index++;
    if (!(index in harness.values)) harness.values[index] = initial;
    return [harness.values[index], (value: unknown) => { harness.values[index] = typeof value === "function" ? value(harness.values[index]) : value; }];
  },
  useRef: () => ({ current: harness.refIndex++ === 2 ? { focus: harness.focus } : null }),
}));
vi.mock("../../i18n/lang", () => ({ useLang: () => ({ lang: harness.lang, t: (pair: { en: string; th: string }) => pair[harness.lang] }) }));
vi.mock("../../data/mode", () => ({ apiMode: () => true }));
vi.mock("../../data/call", () => ({ sendCallTurn: harness.send }));
vi.mock("react-router-dom", () => ({ Link: ({ children }: { children: ReactNode }) => <a>{children}</a> }));
vi.mock("../location/CallerLocation", () => ({ CallerLocation: () => null }));
vi.mock("./CallCaseSidebar", () => ({ CallCaseSidebar: () => null }));

function page(messages: CallSession["messages"] = [{ role: "assistant", text: "Synthetic greeting" }], draft = "") {
  harness.values = ["conversation", { chat: true, voice: false }, { sessionId: "synthetic", messages, sent: null, pinned: null, locationLookup: { status: "idle" } }, draft, "", false, "", null, undefined, false, "off", "", 0];
  harness.index = 0; harness.refIndex = 0;
  return CallPage();
}
function buttons(node: ReactNode): { children: ReactNode; onClick: () => void; className?: string }[] {
  const found: ReturnType<typeof buttons> = [];
  Children.forEach(node, child => {
    if (!isValidElement<{ children: ReactNode; onClick: () => void; className?: string }>(child)) return;
    if (child.type === "button" && child.props.className === "call-hint") found.push(child.props);
    found.push(...buttons(child.props.children));
  });
  return found;
}
beforeEach(() => { harness.lang = "en"; harness.focus.mockClear(); harness.send.mockClear(); });

describe("suggested first call replies", () => {
  it.each(["en", "th"] as const)("shows four localized chips before the first user message in %s", lang => {
    harness.lang = lang;
    const tree = page();
    expect(buttons(tree)).toHaveLength(4);
    const out = renderToStaticMarkup(tree);
    expect(out).toContain(lang === "en" ? "Water in the house" : "น้ำเข้าบ้าน");
    expect(out).toContain(lang === "en" ? "We need a boat" : "ต้องการเรือ");
    expect(buttons(page([{ role: "user", text: "Synthetic caller reply" }]))).toHaveLength(0);
  });
  it.each(["en", "th"] as const)("inserts and appends a reply in %s, focuses the box, and never sends", lang => {
    harness.lang = lang;
    const chip = buttons(page())[0];
    chip.onClick();
    expect(harness.values[3]).toBe(lang === "en" ? "Water in the house" : "น้ำเข้าบ้าน");
    const next = buttons(page(undefined, "Help "))[3];
    next.onClick();
    expect(harness.values[3]).toBe(lang === "en" ? "Help We need a boat" : "Help ต้องการเรือ");
    expect(harness.focus).toHaveBeenCalledTimes(2);
    expect(harness.send).not.toHaveBeenCalled();
  });
});
