/**
 * Demo clock. The synthetic records happen on 11 Oct 2026 from 10:10 Bangkok (pack §7), so "how long ago"
 * is measured against a clock that starts at 10:16 and runs in real time from page load.
 * Live data will use the real clock.
 */
const DEMO_START = Date.parse("2026-10-11T03:16:00Z");
const loadedAt = Date.now();

export function now(): number {
  return DEMO_START + (Date.now() - loadedAt);
}
