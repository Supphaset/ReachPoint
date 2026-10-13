/**
 * Loads the Google Maps JavaScript API once, with the browser key the server hands out (GET /api/config).
 * The key is locked to our web addresses in Google Cloud and never committed. No key, no network or a load
 * failure → the promise rejects and the screens fall back to the drawn map.
 */
import { get } from "./api";
import { apiMode } from "./mode";

// The Maps API has no bundled types here (no new packages); only the few calls we use are touched.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Maps = any;

let loading: Promise<Maps> | undefined;

export function loadGoogleMaps(lang: "th" | "en"): Promise<Maps> {
  if (!apiMode()) return Promise.reject(new Error("needs the server"));
  return (loading ??= get<{ mapsKey: string | null }>("/api/config").then(
    (cfg) =>
      new Promise<Maps>((resolve, reject) => {
        if (!cfg.mapsKey) return reject(new Error("no Maps key"));
        const w = window as unknown as { google?: { maps?: Maps }; __rpMapsReady?: () => void };
        if (w.google?.maps?.Map) return resolve(w.google.maps);
        w.__rpMapsReady = () => resolve(w.google!.maps);
        const s = document.createElement("script");
        s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(cfg.mapsKey)}&language=${lang}&region=TH&callback=__rpMapsReady&loading=async`;
        s.async = true;
        s.onerror = () => reject(new Error("Maps failed to load"));
        document.head.appendChild(s);
        window.setTimeout(() => reject(new Error("Maps timed out")), 12_000);
      }),
  ).catch((e) => {
    loading = undefined; // allow a retry later
    throw e;
  }));
}
