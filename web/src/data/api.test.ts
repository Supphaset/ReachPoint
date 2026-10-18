import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, get, post } from "./api";

vi.mock("./room", () => ({ demoRoom: () => "judge" }));
afterEach(() => vi.unstubAllGlobals());

describe("rate limit replies", () => {
  it.each([get, (path: string) => post(path, {})])("shows the wait in both languages", async (call) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: "rate_limited", retryAfter: 7 }), {
      status: 429, headers: { "Retry-After": "7", "Content-Type": "application/json" },
    })));
    await expect(call("/api/v2/chat/sessions")).rejects.toMatchObject({
      code: "rate_limited", status: 429, retryAfter: 7,
      message: "Too many messages at once — wait 7 seconds / ส่งข้อความถี่เกินไป กรุณารอ 7 วินาที",
    });
  });
  it("uses the JSON wait when the header is absent", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ retryAfter: 12 }), { status: 429 })));
    try { await get("/api/v2/health"); } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).retryAfter).toBe(12);
    }
  });
});
