/**
 * Fixture data source (until the friend's Firestore views are live).
 *
 * Dev switches in the URL, so every screen state can be shown and tested (C2 test plan):
 *   ?variant=empty | stale | layer-missing   pick a fixture variant of the area briefing
 *   ?offline=1                               keep the data but report the connection as offline
 *   ?fail=view | tiles | rain                make the view (or the map tiles, or the rain view) fail to load
 *   ?clock=14:00                             start the demo clock at another Bangkok time (data/clock.ts)
 */
import type { Connection } from "./useView";
import { ApiError, get } from "./api";
import { apiMode } from "./mode";

const briefings = import.meta.glob("../../../contract/fixtures/areaBriefing.*.json", { import: "default" });
const rainFile = import.meta.glob("../../../contract/fixtures/rainStatus.hy-2025-11.json", { import: "default" });
const risingFiles = import.meta.glob("../../../contract/fixtures/risingWater.*.json", { import: "default" });
const geography = import.meta.glob("../../../data/hy-2025-11/{areas,zones,segments,landmarks,no-satellite-data,extent-2025-11-23-o164,reported-flooding,osm-lines}.geojson", { query: "?raw", import: "default" });

export function devSwitch(name: string): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get(name);
}

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

/** In API mode: GET /api/views/<rest of the path>; a 404 means "no such view" (null), like a missing fixture. */
async function readApiView<T>(path: string): Promise<{ data: T; connection: Connection } | null> {
  try {
    return { data: await get<T>(`/api/${path}`), connection: "live" };
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}

export async function readView<T>(path: string): Promise<{ data: T; connection: Connection } | null> {
  if (apiMode()) return readApiView<T>(path);
  await delay(150);
  if (devSwitch("fail") === "view") throw new Error("View failed to load");
  const r = path.match(/^views\/rain\/([\w-]+)$/);
  if (r) {
    if (devSwitch("fail") === "rain") throw new Error("Rain view failed to load");
    const doc = (await rainFile["../../../contract/fixtures/rainStatus.hy-2025-11.json"]()) as { snapshots: Record<string, unknown> };
    const snaps = doc.snapshots[r[1]];
    return snaps ? { data: snaps as T, connection: devSwitch("offline") ? "offline" : "live" } : null;
  }
  const w = path.match(/^views\/risingWater\/([\w-]+)$/);
  if (w) {
    if (devSwitch("fail") === "rain") throw new Error("Water view failed to load");
    const load = risingFiles[`../../../contract/fixtures/risingWater.${w[1]}.json`];
    if (!load) return null;
    const doc = (await load()) as { snapshots: unknown };
    return { data: doc.snapshots as T, connection: devSwitch("offline") ? "offline" : "live" };
  }
  const m = path.match(/^views\/areaBriefing\/([\w-]+)$/);
  if (!m) return null;
  const variant = devSwitch("variant");
  const base = `../../../contract/fixtures/areaBriefing.${m[1]}`;
  const load = (variant && briefings[`${base}.${variant}.json`]) || briefings[`${base}.json`];
  if (!load) return null;
  return { data: (await load()) as T, connection: devSwitch("offline") ? "offline" : "live" };
}

/** A file from the flood data package, e.g. "zones.geojson". */
export async function readPackageFile<T>(name: string): Promise<T> {
  if (devSwitch("fail") === "tiles") throw new Error("Map data failed to load");
  const load = geography[`../../../data/hy-2025-11/${name}`];
  if (!load) throw new Error(`No package file ${name}`);
  return JSON.parse((await load()) as string) as T;
}
