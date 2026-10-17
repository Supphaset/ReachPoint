import { Children, isValidElement, type ReactElement, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { vol, type CaseRow, type ZonePage } from "../api";
import { MissionContent } from "./MissionPage";

// Keep hook state across explicit renders in the project's node test environment.
const harness = vi.hoisted(() => ({ states: [] as unknown[], refs: [] as { current: unknown }[], stateIndex: 0, refIndex: 0, openTeam: vi.fn() }));
vi.mock("react", async original => ({
  ...await original<typeof import("react")>(),
  useState: (initial: unknown) => {
    const index = harness.stateIndex++;
    if (!(index in harness.states)) harness.states[index] = initial;
    return [harness.states[index], (value: unknown) => { harness.states[index] = value; }];
  },
  useRef: (initial: unknown) => {
    const index = harness.refIndex++;
    return harness.refs[index] ??= { current: initial };
  },
}));
vi.mock("../ui/lang", () => ({ useT: () => (_th: string, en: string) => en, Tr: ({ en }: { en: ReactNode }) => en }));
vi.mock("./shared", () => ({ Depth: () => null, VShell: () => null, useGeo: () => null, useTeamNameOpener: () => harness.openTeam }));
vi.mock("./MissionMap", () => ({ MissionMap: () => null }));
const reload = vi.fn();
const row = { id: "HH1", priority: 100, status: "open", needs: [], urgent: true, people: 2, cannotWalk: 1, elderly: 0, children: 0,
  lat: 7, lon: 100, depth: null, lastHeard: "07:00", hoursSilent: 1, zoneId: "D1", boat: true, messages: 1,
  firstHand: true, possibleDuplicateOf: null, outcome: null, reportedBy: "self" } as CaseRow;
const data = { zone: { id: "D1" }, households: [row], now: { atH: 1 }, shelterOptions: [
  { shelterId: "far", km: 5 }, { shelterId: "near", km: 1 },
] } as ZonePage;
function elements(node: ReactNode): ReactElement<Record<string, unknown>>[] {
  return Children.toArray(node).flatMap(child => isValidElement<Record<string, unknown>>(child) ? [child, ...elements(child.props.children as ReactNode)] : []);
}
function render(team = "Boat 1", zone = data) {
  harness.stateIndex = 0; harness.refIndex = 0;
  return elements(MissionContent({ data: zone, mission: null, team, reload }));
}
function button(tree: ReturnType<typeof render>, label: string) {
  return tree.find(node => node.type === "button" && elements(node.props.children as ReactNode).some(child => child.props.en === label))!;
}
async function click(node: ReactElement<Record<string, unknown>>) { expect(node).toBeDefined(); await (node.props.onClick as () => unknown)(); }
beforeEach(() => { harness.states = []; harness.refs = []; vi.clearAllMocks(); vi.spyOn(vol, "outcome").mockResolvedValue({} as Awaited<ReturnType<typeof vol.outcome>>); });
describe("mission outcome actions", () => {
  it("opens the team-name control before allowing an anonymous outcome", async () => {
    await click(button(render(""), "Picked up"));
    expect(harness.openTeam).toHaveBeenCalledOnce();
    expect(button(render(""), "Confirm")).toBeUndefined();
    expect(vol.outcome).not.toHaveBeenCalled();
  });
  it.each(["Picked up", "Nobody there", "Taken to shelter"])("requires confirmation for %s, then refreshes", async label => {
    await click(button(render(), label));
    expect(vol.outcome).not.toHaveBeenCalled();
    await click(button(render(), "Confirm"));
    await Promise.resolve();
    const kind = label === "Picked up" ? "pickedUp" : label === "Nobody there" ? "nobodyThere" : "atShelter";
    expect(vol.outcome).toHaveBeenCalledWith("HH1", kind, "Boat 1", kind === "atShelter" ? "near" : undefined);
    expect(reload).toHaveBeenCalledOnce();
    expect(button(render(), "Confirm")).toBeUndefined();
  });
  it("omits a missing shelter and lets a failed send retry", async () => {
    const zone = { ...data, shelterOptions: undefined };
    vi.mocked(vol.outcome).mockRejectedValueOnce(Error("offline"));
    await click(button(render("Boat 1", zone), "Taken to shelter"));
    await click(button(render("Boat 1", zone), "Confirm"));
    await Promise.resolve();
    expect(reload).not.toHaveBeenCalled();
    expect(button(render("Boat 1", zone), "Confirm")).toBeDefined();
    await click(button(render("Boat 1", zone), "Confirm"));
    await Promise.resolve();
    expect(vol.outcome).toHaveBeenLastCalledWith("HH1", "atShelter", "Boat 1", undefined);
    expect(reload).toHaveBeenCalledOnce();
  });
  it("cancels without notifying the family", async () => {
    await click(button(render(), "Nobody there"));
    await click(button(render(), "Cancel"));
    expect(button(render(), "Confirm")).toBeUndefined();
    expect(vol.outcome).not.toHaveBeenCalled();
  });
});
