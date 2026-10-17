import { Children, isValidElement, type ReactElement, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { UrgentCase, UrgentZone } from "../api";
import { UrgentList } from "./UrgentList";

// The project's test environment has no DOM. Exercise row/button handlers with
// a small state harness; SSR tests separately verify their rendered markup.
const state = vi.hoisted(() => ({ expanded: false, openTeam: vi.fn() }));
vi.mock("react", async importOriginal => ({
  ...await importOriginal<typeof import("react")>(),
  useState: () => [state.expanded, (value: boolean | ((previous: boolean) => boolean)) => {
    state.expanded = typeof value === "function" ? value(state.expanded) : value;
  }],
  useEffect: () => undefined,
  useRef: () => ({ current: null }),
}));
vi.mock("../ui/lang", () => ({ useT: () => (_th: string, en: string) => en, Tr: () => null }));
vi.mock("./shared", () => ({ Depth: () => null, Trend: () => null, useTeamNameOpener: () => state.openTeam }));

function elements(node: ReactNode): ReactElement<Record<string, unknown>>[] {
  return Children.toArray(node).flatMap(child => {
    if (!isValidElement<Record<string, unknown>>(child)) return [];
    return [child, ...elements(child.props.children as ReactNode)];
  });
}
const row = { id: "HH001", needs: [], hoursSilent: 10, priority: 226, markedFirst: null } as unknown as UrgentCase;
const zones = Array.from({ length: 9 }, (_, i) => ({ id: `Z${i}`, cases: [{ ...row, id: `HH${i}` }], plans: 0, depthM: null } as UrgentZone));
const first = vi.fn().mockResolvedValue(undefined);
function render(team = "") {
  return elements(UrgentList({ data: { atH: 0, at: "07:00", total: 9, zones }, zones: [], team, busy: false, highlighted: null, onZone: vi.fn(), onFirst: first }));
}
function click(element: ReactElement<Record<string, unknown>> | undefined) {
  expect(element).toBeDefined();
  (element!.props.onClick as () => void)();
}

beforeEach(() => { state.expanded = false; vi.clearAllMocks(); });
describe("urgent list actions", () => {
  it("opens the existing team-name control instead of trying to mark anonymously", () => {
    click(render().find(item => item.type === "button" && item.props.children === "☆ Do first"));
    expect(state.openTeam).toHaveBeenCalledOnce();
    expect(first).not.toHaveBeenCalled();
    click(render("Boat 1").find(item => item.type === "button" && item.props["aria-pressed"] === false));
    expect(first).toHaveBeenCalledWith(zones[0].cases[0], "Boat 1");
  });
  it("expands beyond six zones and can collapse again", () => {
    expect(render().filter(item => item.props.className === "v-urgent-zone")).toHaveLength(6);
    click(render().find(item => item.props.className === "v-urgent-more"));
    const expanded = render();
    expect(expanded.filter(item => item.props.className === "v-urgent-zone")).toHaveLength(9);
    expect(expanded.find(item => item.props.className === "v-urgent-more")?.props["aria-expanded"]).toBe(true);
    click(expanded.find(item => item.props.className === "v-urgent-more"));
    expect(render().filter(item => item.props.className === "v-urgent-zone")).toHaveLength(6);
  });
});
