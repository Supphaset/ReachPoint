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

import { deoverlapLabels } from "./SectorMap";
describe("projected label spacing", () => {
  it("keeps priority order, skips labels within 70 projected pixels, and includes the boundary", () => {
    const candidates = [{ id: "first", x: 0, y: 0 }, { id: "near", x: 40, y: 40 }, { id: "edge", x: 70, y: 0 }, { id: "far", x: 0, y: 100 }];
    expect(deoverlapLabels(candidates).map(point => point.id)).toEqual(["first", "edge", "far"]);
    expect(candidates).toHaveLength(4);
    expect(deoverlapLabels([])).toEqual([]);
  });
  it("reconsiders labels after zoom spreads projected positions apart", () => {
    const points = [{ id: "a", x: 0, y: 0 }, { id: "b", x: 60, y: 0 }];
    expect(deoverlapLabels(points)).toHaveLength(1);
    expect(deoverlapLabels(points.map(point => ({ ...point, x: point.x * 2 })))).toHaveLength(2);
  });
  it("removes need fill on water, provides an urgent count and selects its zone", () => {
    const shapes: Record<string, unknown>[] = [];
    const buttons: { textContent: string; onclick?: () => void; className?: string }[] = [];
    vi.stubGlobal("document", { createElement: () => {
      const button = { textContent: "", style: {}, setAttribute: vi.fn(), remove: vi.fn() };
      buttons.push(button); return button;
    } });
    class Polygon { constructor(options: Record<string, unknown>) { shapes.push(options); } addListener = vi.fn(); setMap = vi.fn(); }
    class OverlayView { setMap = vi.fn(); }
    const onZone = vi.fn();
    const cleanup = drawSectorLayers({ Polygon, OverlayView, event: { clearInstanceListeners: vi.fn() } }, {}, {
      geo, zones: [{ ...zone, urgent: 3 }], selection: { sector: null, zone: null, hover: null }, onZone, onSector: vi.fn(),
    }, name => `token:${name}`, true);
    expect(shapes[0].fillOpacity).toBe(0);
    expect(buttons[0].textContent).toBe("3");
    expect(buttons[0].className).toContain("is-urgent");
    buttons[0].onclick?.();
    expect(onZone).toHaveBeenCalledWith("D12");
    cleanup();
    vi.unstubAllGlobals();
  });
});

describe("overlay projection and zoom", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("draws only spaced, visible labels and hides sector badges above zoom 14", () => {
    const buttons: { hidden?: boolean; textContent: string; style: Record<string, string> }[] = [];
    const overlays: OverlayView[] = [];
    vi.stubGlobal("document", { createElement: () => {
      const button = { textContent: "", hidden: false, style: {}, setAttribute: vi.fn(), remove: vi.fn() };
      buttons.push(button); return button;
    } });
    let zoom = 14;
    const projection = {
      fromLatLngToDivPixel: ({ lng, lat }: { lng: number; lat: number }) => ({ x: 200 + (lng - 100.47) * (zoom >= 16 ? 15000 : 2000), y: 200 + (lat - 7.01) * 2000 }),
      fromLatLngToContainerPixel: ({ lng, lat }: { lng: number; lat: number }) => ({ x: 200 + (lng - 100.47) * (zoom >= 16 ? 15000 : 2000), y: 200 + (lat - 7.01) * 2000 }),
    };
    class OverlayView {
      draw?: () => void;
      constructor() { overlays.push(this); }
      setMap = vi.fn();
      getProjection = () => projection;
    }
    class Polygon { addListener = vi.fn(); setMap = vi.fn(); }
    class LatLng { constructor(public lat: number, public lng: number) {} }
    const added = vi.fn();
    const remove = vi.fn();
    const map = { getZoom: () => zoom, getDiv: () => ({ clientWidth: 800, clientHeight: 600 }), addListener: added.mockReturnValue({ remove }) };
    const nearby = structuredClone(geo.zones.features[0]);
    nearby.properties = { id: "D13", sector: "D" };
    if (nearby.geometry.type === "Polygon") nearby.geometry.coordinates = nearby.geometry.coordinates.map(ring => ring.map(([lng, lat]) => [lng + 0.01, lat]));
    const view = { ...geo, zones: { ...geo.zones, features: [geo.zones.features[0], nearby] }, sectors: { type: "FeatureCollection" as const, features: [{ ...geo.zones.features[0], properties: { id: "D" } }] } };
    const cleanup = drawSectorLayers({ Polygon, OverlayView, LatLng, event: { clearInstanceListeners: vi.fn() } }, map, {
      geo: view, zones: [zone, { ...zone, id: "D13", score: 50 }], selection: { sector: null, zone: null, hover: null }, onZone: vi.fn(), onSector: vi.fn(),
    }, name => name);
    overlays.forEach(overlay => overlay.draw?.());
    expect(buttons[0].hidden).toBe(false);
    expect(buttons[1].hidden).toBe(true);
    expect(buttons[2].hidden).toBe(false);
    zoom = 16;
    added.mock.calls[0][1]();
    expect(buttons[1].hidden).toBe(false);
    expect(buttons[2].hidden).toBe(true);
    cleanup();
    expect(remove).toHaveBeenCalledOnce();
  });
});

describe("urgent map dots", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("links hover and keyboard focus to the case list, preserves the star, and opens on click", () => {
    const buttons: { className?: string; dataset: Record<string, string>; textContent: string; onmouseenter?: () => void; onmouseleave?: () => void; onfocus?: () => void; onclick?: () => void }[] = [];
    vi.stubGlobal("document", { createElement: () => {
      const button = { textContent: "", dataset: {}, style: {}, setAttribute: vi.fn(), remove: vi.fn() };
      buttons.push(button); return button;
    } });
    class Polygon { addListener = vi.fn(); setMap = vi.fn(); }
    class OverlayView { setMap = vi.fn(); }
    const highlight = vi.fn(), open = vi.fn();
    const cleanup = drawSectorLayers({ Polygon, OverlayView, event: { clearInstanceListeners: vi.fn() } }, {}, {
      geo, zones: [zone], selection: { sector: null, zone: null, hover: null }, onZone: vi.fn(), onSector: vi.fn(),
      urgentCases: [{ id: "HH1", lon: 100.47, lat: 7.01, markedFirst: { team: "Boat", at: "07:00" } } as import("../api").UrgentCase],
      highlighted: "HH1", onHighlight: highlight, onCase: open,
    }, name => name);
    const dot = buttons.find(button => button.dataset.case === "HH1")!;
    expect(dot.className).toContain("is-highlighted");
    expect(dot.className).toContain("is-first");
    expect(dot.textContent).toBe("★");
    dot.onmouseenter?.();
    expect(highlight).toHaveBeenLastCalledWith("HH1");
    dot.onmouseleave?.();
    expect(highlight).toHaveBeenLastCalledWith(null);
    dot.onfocus?.();
    expect(highlight).toHaveBeenLastCalledWith("HH1");
    dot.onclick?.();
    expect(open).toHaveBeenCalledWith("HH1");
    cleanup();
  });
});

import { needLabel } from "./UrgentList";
describe("need labels", () => {
  it("turns the server's need words into Thai and English", () => {
    expect(needLabel("2 can't walk")).toEqual(["เดินไม่ได้ 2 คน", "2 can't walk"]);
    expect(needLabel("1 child")[0]).toBe("เด็ก 1 คน");
    expect(needLabel("wants to leave, needs a ride")[0]).toContain("ต้องการออก");
  });
});
