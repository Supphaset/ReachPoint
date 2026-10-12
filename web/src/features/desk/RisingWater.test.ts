import { describe, expect, it } from "vitest";
import fixture from "../../../../contract/fixtures/risingWater.P-B.json";
import type { RisingWaterView } from "../../data/contract";
import { pickSnapshot } from "../briefing/Rain";

const snaps = (fixture as unknown as { snapshots: RisingWaterView[] }).snapshots;
const at = (h: number, m: number) => Date.UTC(2026, 9, 11, h - 7, m);

describe("water rising view (D42)", () => {
  it("shows the gauge reading at 10:00 with no prompt, and the prompt once the DDPM forecast is out", () => {
    expect(pickSnapshot(snaps, at(10, 5))?.prompt).toBeNull();
    const p = pickSnapshot(snaps, at(10, 35))?.prompt;
    expect(p?.reconfirm.slice(0, 2).map((r) => r.caseId)).toEqual(["C-08", "C-04"]);
    expect(p?.rise?.text).toBe("Forecast rise at the canal: 1.25–1.45 m");
  });
  it("labels every rise as an estimate and never lists a RED case", () => {
    for (const s of snaps)
      for (const r of s.prompt?.reconfirm ?? []) {
        expect(r.caseId).not.toBe("C-01");
        if (r.ifItRises?.rangeM) expect(r.ifItRises.text).toMatch(/\(estimate/);
      }
  });
});
