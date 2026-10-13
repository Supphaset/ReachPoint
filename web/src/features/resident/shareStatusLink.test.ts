import { describe, expect, it, vi } from "vitest";
import { S } from "../../i18n/strings";
import { shareStatusLink } from "./shareStatusLink";

const url = "https://example.test/status/synthetic-token?data=api";
describe("family status sharing", () => {
  it.each(["en", "th"] as const)("copies the %s pre-written message and exact status URL", async lang => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    expect(await shareStatusLink({ clipboard: { writeText } }, url, S.status.shareMessage("R-001")[lang])).toBe("copied");
    expect(writeText).toHaveBeenCalledWith(`${lang === "th" ? "ติดตามคำขอความช่วยเหลือ R-001 ได้ที่ลิงก์นี้" : "Follow help request R-001 here"}\n${url}`);
  });
  it("uses native sharing when available", async () => {
    const share = vi.fn().mockResolvedValue(undefined), writeText = vi.fn();
    expect(await shareStatusLink({ share, clipboard: { writeText } }, url, "Follow help request R-001 here")).toBe("shared");
    expect(share).toHaveBeenCalledWith({ url, text: "Follow help request R-001 here" });
    expect(writeText).not.toHaveBeenCalled();
  });
  it("falls back when sharing fails, but respects cancellation", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    const share = vi.fn().mockRejectedValue(new Error("Unavailable"));
    expect(await shareStatusLink({ share, clipboard: { writeText } }, url, "Message")).toBe("copied");
    writeText.mockClear();
    share.mockRejectedValue(Object.assign(new Error("Cancelled"), { name: "AbortError" }));
    expect(await shareStatusLink({ share, clipboard: { writeText } }, url, "Message")).toBe("cancelled");
    expect(writeText).not.toHaveBeenCalled();
  });
});
