import { beforeEach, describe, expect, it } from "vitest";
import { demoRoom, newRoomCode, roomLink } from "./room";

const store = new Map<string, string>();
beforeEach(() => {
  store.clear();
  (globalThis as any).window = {
    location: { search: "", origin: "https://reachpoint.example" },
    localStorage: { getItem: (k: string) => store.get(k) ?? null, setItem: (k: string, v: string) => store.set(k, v) },
  };
});

describe("demo room", () => {
  it("makes a readable 6-character code", () => {
    expect(newRoomCode()).toMatch(/^[A-HJKMNP-Z2-9]{6}$/);
  });
  it("keeps the same room in this browser", () => {
    const first = demoRoom("");
    expect(demoRoom("")).toBe(first);
  });
  it("joins the room in the link, and ignores a bad one", () => {
    expect(demoRoom("?room=AB12CD")).toBe("AB12CD");
    expect(demoRoom("")).toBe("AB12CD");
    expect(demoRoom("?room=../x")).toBe("AB12CD");
  });
  it("still works when storage is blocked", () => {
    (globalThis as any).window.localStorage = { getItem: () => { throw new Error("blocked"); }, setItem: () => { throw new Error("blocked"); } };
    const a = demoRoom("");
    expect(demoRoom("")).toBe(a);
  });
  it("builds a link for another phone", () => {
    expect(roomLink("/demo", "AB12CD")).toBe("https://reachpoint.example/demo?data=api&room=AB12CD");
  });
});
