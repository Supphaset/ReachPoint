import { describe, expect, it } from "vitest";
import { fmtAgo, fmtDepth, fmtRange, fmtTime } from "./format";

describe("format", () => {
  it("shows ranges with a dash and never invents precision", () => {
    expect(fmtRange([7900, 13000])).toBe("7,900–13,000");
    expect(fmtRange([0, 0])).toBe("0");
  });

  it("shows Bangkok times", () => {
    expect(fmtTime("2026-10-11T03:15:00Z")).toBe("10:15");
  });

  it("says how long ago", () => {
    const now = Date.parse("2026-10-11T03:16:00Z");
    expect(fmtAgo("2026-10-11T03:15:30Z", now)).toBe("just now");
    expect(fmtAgo("2026-10-11T03:12:00Z", now)).toBe("4 min ago");
    expect(fmtAgo("2026-10-11T00:36:00Z", now)).toBe("2 h 40 min ago");
  });

  it("reads the capped model honestly", () => {
    expect(fmtDepth([3, 3])).toBe("over 3 m");
    expect(fmtDepth([1.5, 3])).toBe("about 1.5–3 m");
    expect(fmtDepth([0, 0.5])).toBe("up to 0.5 m");
  });
});
