import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { GeoView, OverviewZone } from "../api";
import { DrawnSectorMap, drawSectorLayers, featureCentroid, needBand } from "./SectorMap";
import { priorityFamilies } from "./OverviewPage";
import type { CaseRow } from "../api";

const geo: GeoView = { center: [100.47, 7.01], zones: { type: "FeatureCollection", features: [{ type: "Feature", properties: { id: "D12", sector: "D" }, geometry: { type: "Polygon", coordinates: [[[100.46, 7], [100.48, 7], [100.48, 7.02], [100.46, 7]]] } }] } };
const zone = { id: "D12", label: "คลองเตย", sector: "D", score: 100, open: 7, plans: 0 } as OverviewZone;

describe("volunteer map fallback and ranking", () => {
  it("keeps named zones keyboard selectable with need and coverage visible offline", () => {
    const html = renderToStaticMarkup(<DrawnSectorMap geo={geo} zones={[zone]} selection={{ sector: "D", zone: "D12", hover: null }} onZone={vi.fn()} onSector={vi.fn()} />);
    expect(html).toContain("D12 · คลองเตย");
    expect(html).toContain('tabindex="0"');
    expect(html).toContain('aria-pressed="true"');
    expect(html).toContain("stroke-dasharray:8 5");
    expect(html).toContain("var(--need-3)");
  });
  it("never paints unknown or closed need as high need", () => {
    expect(needBand(undefined, 100)).toBe(0);
    expect(needBand({ ...zone, open: 0 }, 100)).toBe(0);
    expect(needBand({ ...zone, score: 34 }, 100)).toBe(2);
  });
  it("uses API priority without mutating the input or including completed families", () => {
    const rows = [{ id: "a", priority: 5, status: "open" }, { id: "b", priority: 10, status: "open" }, { id: "c", priority: 100, status: "safe" }] as CaseRow[];
    expect(priorityFamilies(rows).map(row => row.id)).toEqual(["b", "a"]);
    expect(rows.map(row => row.id)).toEqual(["a", "b", "c"]);
  });
});


describe("Google map overlays", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("uses token colours, translucent need, selected halo and cleans up all overlays", () => {
    const shapes: { options: Record<string, unknown>; setMap: ReturnType<typeof vi.fn>; addListener: ReturnType<typeof vi.fn> }[] = [];
    const buttons: { onclick?: () => void; textContent: string; setAttribute: ReturnType<typeof vi.fn>; remove: ReturnType<typeof vi.fn> }[] = [];
    vi.stubGlobal("document", { createElement: () => {
      const button = { textContent: "", style: {}, setAttribute: vi.fn(), remove: vi.fn() };
      buttons.push(button); return button;
    } });
    class Polygon {
      setMap = vi.fn();
      addListener = vi.fn();
      constructor(public options: Record<string, unknown>) { shapes.push(this); }
    }
    class OverlayView {
      setMap = vi.fn();
    }
    const clear = vi.fn();
    const onZone = vi.fn(), onSector = vi.fn();
    const cleanup = drawSectorLayers({ Polygon, OverlayView, event: { clearInstanceListeners: clear } }, {}, {
      geo, zones: [zone], selection: { sector: "D", zone: "D12", hover: null }, onZone, onSector,
    }, name => `token:${name}`);
    expect(shapes[0].options).toMatchObject({ fillColor: "token:--need-3", fillOpacity: 0.6, strokeColor: "token:--ink-1", strokeWeight: 5 });
    expect(buttons[0].textContent).toBe("D12 · คลองเตย");
    buttons[0].onclick?.();
    expect(onZone).toHaveBeenCalledWith("D12");
    const click = shapes[0].addListener.mock.calls.find(call => call[0] === "click")?.[1];
    click();
    expect(onZone).toHaveBeenCalledTimes(2);
    cleanup();
    expect(shapes[0].setMap).toHaveBeenCalledWith(null);
    expect(clear).toHaveBeenCalledTimes(2);
  });
  it("places badges at the area centroid rather than the bounding box centre", () => {
    const [lng, lat] = featureCentroid(geo.zones.features[0]);
    expect(lng).toBeCloseTo((100.46 + 100.48 + 100.48) / 3, 5);
    expect(lat).toBeCloseTo((7 + 7 + 7.02) / 3, 5);
  });
});

import { goBy } from "./SectorMap";
describe("go by", () => {
  it("turns depth into how a team can get there, and admits when it doesn't know", () => {
    expect(goBy(0.3)?.[1]).toContain("walk");
    expect(goBy(0.7)?.[1]).toContain("boat better");
    expect(goBy(1.3)?.[1]).toContain("boat only");
    expect(goBy(2.4)?.[1]).toContain("current");
    expect(goBy(null)).toBeNull();
  });
});
