import { describe, expect, it } from "vitest";
import fixture from "../../../../contract/fixtures/rainStatus.hy-2025-11.json";
import type { RainStatus } from "../../data/contract";
import { pickSnapshot } from "./Rain";

const pb = (fixture as unknown as { snapshots: Record<string, RainStatus[]> }).snapshots["P-B"];
const at = (hhmm: string) => Date.parse(`2026-10-11T${String(Number(hhmm.slice(0, 2)) - 7).padStart(2, "0")}:${hhmm.slice(3)}:00Z`);

describe("rain snapshots (D41)", () => {
  it("shows the newest snapshot at or before the clock", () => {
    expect(pickSnapshot(pb, at("10:16"))?.asOf).toBe("2026-10-11T03:00:00Z");
    expect(pickSnapshot(pb, at("09:59"))).toBeNull();
  });
  it("has no prompt at 10:16 and the re-check prompt at 14:00", () => {
    expect(pickSnapshot(pb, at("10:16"))?.prompt).toBeNull();
    const p = pickSnapshot(pb, at("14:05"))?.prompt;
    expect(p?.title).toBe("Heavy rain since 11:00: re-check segments checked before then");
    expect(p?.recheck.map((r) => r.segmentId)).toEqual(["B-2-L1", "B-3-L3"]);
  });
  it("never says depth", () => {
    for (const s of pb) expect(s.line).not.toMatch(/deep|depth|m water/i);
  });
});
