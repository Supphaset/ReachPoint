import { Children, isValidElement, type ReactElement, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { v2, vol } from "../api";
import { ZonePanel } from "./OverviewPage";

const h = vi.hoisted(() => ({ states: [] as unknown[], index: 0, navigate: vi.fn(), setTeam: vi.fn(), saveMission: vi.fn() }));
vi.mock("react", async original => ({
  ...await original<typeof import("react")>(),
  useState: (initial: unknown) => {
    const index = h.index++;
    if (!(index in h.states)) h.states[index] = typeof initial === "function" ? initial() : initial;
    return [h.states[index], (value: unknown) => { h.states[index] = value; }];
  },
  useEffect: () => undefined,
  useRef: (value: unknown) => ({ current: value }),
}));
vi.mock("react-router-dom", async original => ({ ...await original<typeof import("react-router-dom")>(), useNavigate: () => h.navigate }));
vi.mock("./mission", () => ({ saveMission: h.saveMission }));
vi.mock("./shared", () => ({ useTeam: () => ["", h.setTeam], Trend: () => null, Depth: () => null }));
vi.mock("../ui/lang", () => ({ useT: () => (_th: string, en: string) => en, Tr: () => null }));
function elements(node: ReactNode): ReactElement<Record<string, unknown>>[] {
  return Children.toArray(node).flatMap(child => isValidElement<Record<string, unknown>>(child) ? [child, ...elements(child.props.children as ReactNode)] : []);
}
const onPosted = vi.fn();
function render() { h.index = 0; return elements(ZonePanel({ id: "D1", team: " Boat 1 ", onClose: vi.fn(), onPosted })); }
async function post() {
  const form = render().find(node => node.type === "form")!;
  (form.props.onSubmit as (e: { preventDefault: () => void }) => void)({ preventDefault: vi.fn() });
  await Promise.resolve(); await Promise.resolve();
}
beforeEach(() => {
  h.states = []; h.navigate.mockReset(); vi.clearAllMocks();
  render();
  h.states[2] = true; // Planning; remaining values are the actual ZonePanel defaults.
  h.states[7] = "Boat 1 to D1 at 12:00";
  vi.spyOn(v2, "plan").mockResolvedValue({ plan: { told: 3, at: "08:00" }, reader: "demo" } as Awaited<ReturnType<typeof v2.plan>>);
});
describe("accepted zone mission", () => {
  it("shows the model building count beside the primary action", () => {
    h.states[0] = { zone: { label: "Zone", labelEn: "Zone", summary: "", people: { urgent: 0, cannotWalk: 0 }, level: null, sources: [], plans: [], unheard: { notHeard: [8, 18], floodedBuildings: 32 } }, totals: { open: 0 }, households: [], now: { at: "08:00" } };
    h.states[2] = false;
    const tree = render();
    expect(tree.some(n => n.props.en === "≈ 32 flooded buildings with no request (model estimate)")).toBe(true);
    expect(tree.find(n => n.props.to === "/v/plan?zone=D1")).toBeUndefined();
    expect(tree.some(n => n.type === "button" && n.props.className === "btn btn-pri")).toBe(true);
  });
  it("saves the plan fields, remembers the team and navigates after a successful post", async () => {
    await post();
    expect(v2.plan).toHaveBeenCalledWith("Boat 1 to D1 at 12:00", "Boat 1", { zone: "D1" });
    expect(h.setTeam).toHaveBeenCalledWith("Boat 1");
    expect(h.saveMission).toHaveBeenCalledWith({ zoneId: "D1", team: "Boat 1", vehicle: "boat", seats: 4, eta: expect.any(String), told: 3, at: "08:00" });
    expect(h.navigate).toHaveBeenCalledWith("/v/mission/D1");
    expect(onPosted).toHaveBeenCalledOnce();
  });
  it("keeps the posted message and fallback mission link when navigation throws", async () => {
    h.navigate.mockImplementation(() => { throw Error("navigation unavailable"); });
    await post();
    const tree = render();
    expect(tree.find(node => node.props.role === "status")).toBeDefined();
    expect(tree.find(node => node.props.to === "/v/mission/D1")).toBeDefined();
    expect(tree.find(node => node.props.role === "alert")).toBeUndefined();
  });
  it("does not save or navigate if posting fails", async () => {
    vi.mocked(v2.plan).mockRejectedValueOnce(Error("offline"));
    await post();
    expect(h.saveMission).not.toHaveBeenCalled();
    expect(h.navigate).not.toHaveBeenCalled();
    expect(render().find(node => node.props.role === "alert")).toBeDefined();
  });
});

const suggestion = { reader: "gemini:test", context: { waiting: 3, people: 3, otherTeams: 0, floodedBuildings: 8, householdEstimate: [2, 4] as [number, number] },
  order: ["HH1", "HH2", "HH3"].map(householdId => ({ householdId, run: 1, reason: "Cannot walk", quote: "please help" })),
  spareSeats: 1, bring: ["stretcher"], checkStreets: [{ name: "Street", why: "No reports" }], warnings: [], summary: "Review first" };
function click(label: string) {
  const node = render().find(n => n.props["aria-label"] === label)!;
  (node.props.onClick as () => void)();
}
it("fetches the zone suggestion, renders evidence, moves/removes households, then posts that order", async () => {
  vi.spyOn(vol, "suggest").mockResolvedValue(suggestion);
  const button = render().find(n => n.type === "button" && elements(n.props.children as ReactNode).some(c => c.props.en === "Suggest visiting order (Gemini)"))!;
  (button.props.onClick as () => void)();
  await Promise.resolve(); await Promise.resolve();
  expect(vol.suggest).toHaveBeenCalledWith("D1", { team: "Boat 1", vehicle: "boat", seats: 4, eta: "07:00", lang: "en" });
  expect(render().some(n => n.type === "blockquote")).toBe(true);
  expect(render().some(n => n.props.en === "Gemini · checked against ReachPoint's records")).toBe(true);
  click("Move HH2 up");
  click("Remove HH3");
  await post();
  expect(v2.plan).toHaveBeenCalledWith(expect.any(String), "Boat 1", { zone: "D1", order: ["HH2", "HH1"], checkStreets: ["Street"] });
});
it("clears a suggestion when capacity changes", () => {
  h.states[11] = suggestion;
  expect(render().some(n => n.props["aria-label"] === "Suggested visiting order")).toBe(true);
  const button = render().find(n => n.type === "button" && n.props.children === 6)!;
  (button.props.onClick as () => void)();
  expect(render().some(n => n.props["aria-label"] === "Suggested visiting order")).toBe(false);
});

it("moves across runs and repacks without exceeding seats", () => {
  h.states[0] = { now: { at: "08:00" }, households: [1, 2, 3].map(n => ({ id: `HH${n}`, people: 2 })) };
  h.states[5] = 6;
  h.states[11] = { ...suggestion, spareSeats: 2, order: suggestion.order.map((v, i) => ({ ...v, run: i < 2 ? 1 : 2 })) };
  click("Move HH3 up");
  const edited = h.states[11] as typeof suggestion;
  expect(edited.order.map(v => [v.householdId, v.run])).toEqual([["HH1", 1], ["HH3", 1], ["HH2", 2]]);
});
