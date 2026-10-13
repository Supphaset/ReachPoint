import type { LocationInput } from "./contract";
import { demoBounds } from "./locationMap";
import { insideBounds } from "./mapGeometry";

type Failure = "outside" | "denied" | "timeout" | "unavailable" | "mapFailed";
export type DeviceLocation = { ok: true; input: LocationInput } | { ok: false; reason: Failure };
/** Never forwards an out-of-bounds GPS coordinate to a server. */
export async function deviceLocation(): Promise<DeviceLocation> {
  let bounds;
  try { bounds = await demoBounds(); }
  catch { return { ok: false, reason: "mapFailed" }; }
  if (!navigator.geolocation) return { ok: false, reason: "unavailable" };
  return new Promise(resolve => {
    try { navigator.geolocation.getCurrentPosition(position => {
      const { longitude: lon, latitude: lat, accuracy: accuracyM } = position.coords;
      resolve(insideBounds([lon, lat], bounds)
        ? { ok: true, input: { kind: "pin", lat, lon, method: "gps", accuracyM } }
        : { ok: false, reason: "outside" });
    }, error => resolve({ ok: false, reason: error.code === 1 ? "denied" : error.code === 3 ? "timeout" : "unavailable" }),
    { enableHighAccuracy: true, timeout: 10_000, maximumAge: 0 });
    } catch { resolve({ ok: false, reason: "unavailable" }); }
  });
}
