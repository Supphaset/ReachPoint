import type { Range } from "./contract";

const TZ = "Asia/Bangkok";

const int = new Intl.NumberFormat("en-US");

/** "7,900–13,000"; a range is never shown as one precise number unless both ends agree. */
export function fmtRange([lo, hi]: Range): string {
  return lo === hi ? int.format(lo) : `${int.format(lo)}–${int.format(hi)}`;
}

export function fmtInt(n: number): string {
  return int.format(n);
}

/** "10:15" in Bangkok time. */
export function fmtTime(iso: string): string {
  return new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: TZ }).format(new Date(iso));
}

/** "just now", "4 min ago", "2 h 40 min ago". */
export function fmtAgo(iso: string, nowMs: number): string {
  const mins = Math.floor((nowMs - Date.parse(iso)) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m ? `${h} h ${m} min ago` : `${h} h ago`;
}

function metres(x: number): string {
  return Number.isInteger(x) ? `${x}` : x.toFixed(1);
}

/**
 * Modelled depth band. The model is capped at the deepest report (3 m), so [3, 3] reads "over 3 m";
 * a band starting at 0 reads "up to …".
 */
export function fmtDepth([lo, hi]: Range, cap = 3, lang: "en" | "th" = "en"): string {
  if (lang === "th") {
    if (lo >= cap) return `มากกว่า ${metres(cap)} ม.`;
    if (lo <= 0) return `ไม่เกิน ${metres(hi)} ม.`;
    return `ประมาณ ${metres(lo)}–${metres(hi)} ม.`;
  }
  if (lo >= cap) return `over ${metres(cap)} m`;
  if (lo <= 0) return `up to ${metres(hi)} m`;
  return `about ${metres(lo)}–${metres(hi)} m`;
}

export const ASSISTANCE_LABEL: Record<string, string> = {
  evacuation_transport: "Evacuation",
  medical: "Medical",
  supplies: "Supplies",
};
