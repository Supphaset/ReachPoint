import { describe, expect, it } from "vitest";
import { wsOrigin } from "./wsOrigin";

describe("voice origin", () => {
  it.each(["https://reachpoint-main.web.app", "https://reachpoint-main.firebaseapp.com"])("bypasses Hosting at %s", origin => {
    const base = wsOrigin(origin);
    expect(base.origin).toBe("wss://reachpoint-900867850704.asia-southeast1.run.app");
    expect(new URL("/api/v2/chat/sessions/demo/live?room=JUDGE1", base).searchParams.get("room")).toBe("JUDGE1");
  });

  it("uses the configured Cloud Run origin on Hosting", () => {
    expect(wsOrigin("https://demo.web.app", "https://custom.run.app").origin).toBe("wss://custom.run.app");
  });

  it.each(["https://reachpoint.run.app", "https://web.app.example.com", "http://localhost:5173"])("keeps the page origin at %s", origin => {
    expect(wsOrigin(origin, "https://other.run.app").origin).toBe(origin.replace(/^http/, "ws"));
  });
});
