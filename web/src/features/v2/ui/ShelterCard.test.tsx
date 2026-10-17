import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { routeSegments, routeTone, ShelterAnswers } from "./ShelterCard";

describe("shelter route water colouring", () => {
  it("keeps the inclusive shallow boundaries and makes deeper water a don't-wade segment", () => {
    expect([0, 0.25, 0.251, 0.5, 0.501, 2, null].map(routeTone)).toEqual(["light", "light", "mid", "mid", "deep", "deep", "unknown"]);
  });
  it("preserves the street path and uses the nearest sample for each segment", () => {
    const path: [number, number][] = [[100, 7], [100.001, 7.001], [100.002, 7.001], [100.003, 7.002]];
    const segments = routeSegments({ path, samples: [[100.0005, 7.0005, 0.2], [100.0015, 7.001, 0.4], [100.0025, 7.0015, 0.8]] });
    expect(segments.map(segment => segment.tone)).toEqual(["light", "mid", "deep"]);
    expect(segments[1]).toMatchObject({ start: path[1], end: path[2] });
    expect(routeSegments({ path, samples: [] }).every(segment => segment.tone === "unknown")).toBe(true);
    expect(routeSegments({ path: [], samples: [] })).toEqual([]);
  });
});

describe("shelter answer choices", () => {
  it.each([true, false])("offers only the replies appropriate to walkable=%s", walkable => {
    const html = renderToStaticMarkup(<ShelterAnswers walkable={walkable} disabled={false} onAnswer={() => true} />);
    expect(html).toContain(walkable ? "Stay home" : "Need a team");
    expect(html).toContain(walkable ? "I&#x27;ll go" : "I can get there");
    expect(html).not.toContain(walkable ? "Need a team" : "Stay home");
  });
  it("disables both choices while a turn is sending", () => {
    const html = renderToStaticMarkup(<ShelterAnswers walkable={false} disabled onAnswer={() => true} />);
    expect(html.match(/disabled=""/g)).toHaveLength(2);
  });
});
