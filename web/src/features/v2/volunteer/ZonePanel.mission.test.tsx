import { Children, isValidElement, type ReactElement, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { v2 } from "../api";
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
  useRef: () => ({ current: null }),
}));
vi.mock("react-router-dom", async original => ({ ...await original<typeof import("react-router-dom")>(), useNavigate: () => h.navigate }));
vi.mock("./mission", () => ({ saveMission: h.saveMission }));
vi.mock("./shared", () => ({ useTeam: () => ["", h.setTeam] }));
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
  it("saves the plan fields, remembers the team and navigates after a successful post", async () => {
    await post();
    expect(v2.plan).toHaveBeenCalledWith("Boat 1 to D1 at 12:00", "Boat 1");
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
