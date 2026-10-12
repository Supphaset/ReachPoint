/**
 * Demo clock. The synthetic records happen on 11 Oct 2026 from 10:10 Bangkok (pack §7), so "how long ago"
 * is measured against a clock that starts at 10:16 and runs in real time from page load.
 * Live data will use the real clock.
 *
 * Dev switch: `?clock=14:00` starts the demo clock at that Bangkok time instead (e.g. to show the D41 rain prompt).
 */
function demoStart(): number {
  const q = typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("clock");
  const m = q?.match(/^(\d{1,2}):(\d{2})$/);
  if (m) return Date.UTC(2026, 9, 11, Number(m[1]) - 7, Number(m[2]));
  return Date.parse("2026-10-11T03:16:00Z");
}
const DEMO_START = demoStart();
const loadedAt = Date.now();

export function now(): number {
  return DEMO_START + (Date.now() - loadedAt);
}
