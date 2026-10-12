import { beforeEach, describe, expect, it } from "vitest";
import type { TeamMissionsView } from "./contract";
import {
  __peek,
  _resetTeamStore,
  claimListing,
  closeAllocation,
  handBack,
  loadTeam,
  setTeamStatus,
  setWindow,
} from "./teamStore";

const read = () => (__peek() as { view: TeamMissionsView }).view;

beforeEach(async () => {
  _resetTeamStore();
  await loadTeam("T-S");
});

const listing = (id: string) => read().open.find((l) => l.listingId === id)!;

describe("team actions (C6 rules, fixture mode)", () => {
  it("takes a family: seats go down, the job has the exact point", async () => {
    const r = await claimListing("L-C01-EVAC", ["L-C01-EVAC-G1"], 2);
    expect(r.ok).toBe(true);
    expect(read().team.resource.seatUnitsLeft).toBe(9.5);
    const job = read().jobs[0];
    expect(job.pickup.precision).toBe("building");
    expect(job.window).toBeNull();
  });

  it("one winner per group", async () => {
    expect((await claimListing("L-C01-EVAC", ["L-C01-EVAC-G1"], 2)).ok).toBe(true);
    const again = await claimListing("L-C01-EVAC", ["L-C01-EVAC-G1"], 2);
    expect(again).toMatchObject({ ok: false, code: "ALREADY_TAKEN", message: "Already taken by T-S" });
  });

  it("Families 1+2 now, Family 3 still open (CP2)", async () => {
    const r = await claimListing("L-C06-EVAC", ["L-C06-EVAC-G1", "L-C06-EVAC-G2"], 1);
    expect(r.ok).toBe(true);
    expect(listing("L-C06-EVAC").groups.map((g) => g.state)).toEqual(["taken", "taken", "open"]);
  });

  it("an old revision gets NEED_CHANGED", async () => {
    expect(await claimListing("L-C01-EVAC", ["L-C01-EVAC-G1"], 1)).toMatchObject({ code: "NEED_CHANGED" });
  });

  it("not enough seats says how many", async () => {
    for (const [id, rev] of [["L-C02-EVAC", 1], ["L-C04-EVAC", 1], ["L-C06-EVAC", 1]] as const)
      await claimListing(id, listing(id).groups.map((g) => g.groupId), rev);
    expect(read().team.resource.seatUnitsLeft).toBe(2);
    const r = await claimListing("L-C05-EVAC", ["L-C05-EVAC-G1"], 1);
    expect(r).toMatchObject({ ok: false, code: "NOT_ENOUGH_CAPACITY", message: "Needs 5 seats, you have 2" });
  });

  it("a busy team can't take", async () => {
    await setTeamStatus("busy", "Refuelling", "2026-10-11T04:30:00Z");
    expect(await claimListing("L-C01-EVAC", ["L-C01-EVAC-G1"], 2)).toMatchObject({ code: "NOT_AVAILABLE" });
  });

  it("hand back reopens the family and returns the seats", async () => {
    const r = await claimListing("L-C02-EVAC", ["L-C02-EVAC-G1"], 1);
    if (!r.ok) throw new Error(r.message);
    await handBack(r.value.allocationId, "Boat problem");
    expect(listing("L-C02-EVAC").groups[0].state).toBe("open");
    expect(read().team.resource.seatUnitsLeft).toBe(12);
    expect(listing("L-C02-EVAC").reasons).toContain("Back from T-S: Boat problem");
  });

  it("a closed job refuses late updates", async () => {
    const r = await claimListing("L-C03-EVAC", ["L-C03-EVAC-G1"], 1);
    if (!r.ok) throw new Error(r.message);
    await closeAllocation(r.value.allocationId, "done");
    expect(await setWindow(r.value.allocationId, "2026-10-11T04:00:00Z", "2026-10-11T05:00:00Z")).toMatchObject({
      ok: false,
      code: "ALLOCATION_CLOSED",
      message: "This job is closed",
    });
  });

  it("not found frees the seats; done keeps them used", async () => {
    const a = await claimListing("L-C03-EVAC", ["L-C03-EVAC-G1"], 1);
    const b = await claimListing("L-C08-EVAC", ["L-C08-EVAC-G1"], 1);
    if (!a.ok || !b.ok) throw new Error("claim failed");
    await closeAllocation(a.value.allocationId, "done");
    await closeAllocation(b.value.allocationId, "not_found");
    expect(read().team.resource.seatUnitsLeft).toBe(10);
  });

  it("the job carries why it's urgent and what to bring", async () => {
    const r = await claimListing("L-C01-EVAC", ["L-C01-EVAC-G1"], 2);
    if (!r.ok) throw new Error(r.message);
    expect(r.value.urgency.title).toBe("Why this is an emergency");
    expect(r.value.urgency.kit).toContain("Boat needed (water 1.2 m or more)");
    expect(r.value.urgency.withheld).toBe("Medical details stay with the desk and the medical team");
  });
});
