import { afterEach, describe, expect, it, vi } from "vitest";
import { bindFloodZoom, drawFlood, floodOpacity, type Sim } from "./floodLayer";

afterEach(() => vi.unstubAllGlobals());

describe("water display", () => {
  it("fades at report zoom levels and removes its listener", () => {
    expect([13, 16, 17, 18, 20].map(floodOpacity)).toEqual([1, 1, 0.6, 0.35, 0.35]);
    let zoom = 16;
    let update: () => void = () => undefined;
    const remove = vi.fn();
    const map = {
      getZoom: () => zoom,
      addListener: vi.fn((_event: string, callback: () => void) => { update = callback; return { remove }; }),
    };
    const canvas = { style: { opacity: "" } } as HTMLCanvasElement;
    const cleanup = bindFloodZoom(map, canvas);
    expect(canvas.style.opacity).toBe("1");
    zoom = 17;
    update();
    expect(canvas.style.opacity).toBe("0.6");
    zoom = 18;
    update();
    expect(canvas.style.opacity).toBe("0.35");
    cleanup();
    expect(remove).toHaveBeenCalledOnce();
  });

  it("preserves wet cells and band alpha before smoothing to a 4× canvas", () => {
    const pixels = new Uint8ClampedArray(6 * 4);
    const raw = {
      createImageData: vi.fn(() => ({ data: pixels })),
      putImageData: vi.fn(),
    };
    const display = { drawImage: vi.fn(), imageSmoothingEnabled: false, imageSmoothingQuality: "low", filter: "" };
    const grid = { width: 0, height: 0, getContext: () => raw };
    const canvas = { width: 0, height: 0, getContext: () => display } as unknown as HTMLCanvasElement;
    vi.stubGlobal("document", { createElement: vi.fn(() => grid), documentElement: {} });
    vi.stubGlobal("getComputedStyle", () => ({ getPropertyValue: () => "#24599b" }));
    const sim: Sim = {
      meta: { rows: 1, cols: 6, hours: 0, frameBytes: 6, stepM: 0.02, start: "", bbox: [0, 0, 1, 1], cellM: 30, model: "test" },
      frames: new Uint8Array([0, 5, 30, 60, 110, 200]),
      zDm: new Int16Array(6), zoneOf: new Int16Array(6), zoneIds: [],
    };
    expect(drawFlood(canvas, sim, 0, null)).toEqual({ wetCells: 5 });
    expect([0, 1, 2, 3, 4, 5].map(index => pixels[index * 4 + 3])).toEqual([0, 97, 117, 138, 158, 158]);
    expect(canvas.width).toBe(24);
    expect(canvas.height).toBe(4);
    expect(display.imageSmoothingQuality).toBe("high");
    expect(display.imageSmoothingEnabled).toBe(true);
    expect(display.drawImage).toHaveBeenCalledWith(grid, 0, 0, 24, 4);
    expect(raw.putImageData).toHaveBeenCalledOnce();
    expect(sim.frames).toEqual(new Uint8Array([0, 5, 30, 60, 110, 200]));
  });
});
