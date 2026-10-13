import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { LangProvider, type Pair } from "./lang";
import { S, seedText } from "./strings";
import { CallPage } from "../features/intake/CallPage";

/** Every fixed entry in the word list has both languages (functions are called with sample values). */
function pairs(x: unknown, out: Pair[] = []): Pair[] {
  if (typeof x === "function") return pairs((x as (...a: unknown[]) => unknown)(1, 2, 3, 4, 5), out);
  if (x && typeof x === "object") {
    if ("en" in x && "th" in x) out.push(x as Pair);
    else Object.values(x).forEach((v) => pairs(v, out));
  }
  return out;
}

describe("Thai / English", () => {
  it("has Thai and English for every word-list entry", () => {
    const all = pairs(S);
    expect(all.length).toBeGreaterThan(150);
    for (const p of all) {
      expect(p.en.trim()).not.toBe("");
      expect(p.th).toMatch(/[฀-๿]/);
    }
  });

  it("shows the call screen in the chosen language", () => {
    const th = renderToStaticMarkup(<LangProvider lang="th"><MemoryRouter><CallPage /></MemoryRouter></LangProvider>);
    const en = renderToStaticMarkup(<LangProvider lang="en"><MemoryRouter><CallPage /></MemoryRouter></LangProvider>);
    expect(th).toContain("ส่งคำขอ");
    expect(th).not.toContain("Send request");
    expect(en).toContain("Send request");
  });

  it("translates generic landmark labels but leaves IDs and unknown text alone", () => {
    expect(seedText("B-3 · L2 Market", "th")).toBe("B-3 · L2 ตลาด");
    expect(seedText("Family 2", "th")).toBe("ครอบครัว 2");
    expect(seedText("Oxygen running out", "th")).toBe("Oxygen running out");
    expect(seedText("B-3 · L2 Market", "en")).toBe("B-3 · L2 Market");
  });
});
