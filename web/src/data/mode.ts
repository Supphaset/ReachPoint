/**
 * Where the screens get their data (one switch for the whole app):
 *   "fixtures"  the shared files in contract/fixtures, with the in-browser rules (dev, tests, offline demo)
 *   "api"       the server: GET /api/views/..., POST /api/... (contract/api.md)
 *
 * Set at build time with VITE_DATA=api (the Cloud Run image does this), or per tab with ?data=api / ?data=fixtures.
 * API calls use relative /api URLs through Cloud Run or Firebase Hosting.
 */
export type DataMode = "fixtures" | "api";

export function dataMode(): DataMode {
  const q = typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("data");
  if (q === "api" || q === "fixtures") return q;
  return import.meta.env.VITE_DATA === "api" ? "api" : "fixtures";
}

export const apiMode = () => dataMode() === "api";

/** How often live views are fetched again in API mode: 15 s, or `?refresh=2` (seconds) on the /demo phones. */
export function refreshMs(): number {
  const q = typeof window === "undefined" ? null : Number(new URLSearchParams(window.location.search).get("refresh"));
  return q && q >= 1 ? q * 1000 : 15_000;
}
