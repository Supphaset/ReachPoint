/** Hosting forwards HTTP; voice connects straight to Cloud Run. */
export function wsOrigin(origin: string, configured = import.meta.env.VITE_WS_ORIGIN as string | undefined): URL {
  const page = new URL(origin);
  const hosting = page.hostname.endsWith(".web.app") || page.hostname.endsWith(".firebaseapp.com");
  const base = new URL(hosting ? configured || "https://reachpoint-900867850704.asia-southeast1.run.app" : origin);
  base.protocol = base.protocol === "https:" ? "wss:" : "ws:";
  return base;
}
