/** Small inline icon set (24 px grid, stroke icons). Every state chip carries one, so colour is never the only signal. */
const PATHS: Record<string, string> = {
  octagon: "M8.5 2.5h7l5 5v7l-5 5h-7l-5-5v-7z M12 7.5v5.5 M12 16.5v.01",
  triangle: "M12 3.5 21.5 20h-19z M12 10v4.5 M12 17.5v.01",
  circle: "M12 3.5a8.5 8.5 0 1 1 0 17a8.5 8.5 0 1 1 0-17z M8.5 12.5l2.4 2.4 4.6-5",
  clock: "M12 3.5a8.5 8.5 0 1 1 0 17a8.5 8.5 0 1 1 0-17z M12 7.5V12l3 2",
  pause: "M12 3.5a8.5 8.5 0 1 1 0 17a8.5 8.5 0 1 1 0-17z M10 9v6 M14 9v6",
  hand: "M12 3.5a8.5 8.5 0 1 1 0 17a8.5 8.5 0 1 1 0-17z M8 12.5h8 M13 9.5l3 3-3 3",
  copy: "M9 9h11v12H9z M15 5V3H4v12h2",
  check: "M4.5 12.5l4.5 4.5 10.5-10.5",
  lock: "M6.5 10.5h11v9h-11z M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5",
  question: "M12 3.5a8.5 8.5 0 1 1 0 17a8.5 8.5 0 1 1 0-17z M9.6 9.5a2.5 2.5 0 1 1 3.4 2.3c-.7.3-1 .8-1 1.5v.4 M12 16.5v.01",
  half: "M12 3.5a8.5 8.5 0 1 1 0 17a8.5 8.5 0 1 1 0-17z M12 3.5v17",
  blocked: "M12 3.5a8.5 8.5 0 1 1 0 17a8.5 8.5 0 1 1 0-17z M6 18 18 6",
  sparkle: "M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z M18.5 16l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z",
  offline: "M3.5 3.5l17 17 M8.5 16.5a5 5 0 0 1 5.6-1 M5 13a10 10 0 0 1 4-2.4 M2 9.5A15 15 0 0 1 7 6.6 M17.5 11a10 10 0 0 1 1.5 2 M12 5.5a15 15 0 0 1 10 4 M12 20v.01",
  alert: "M12 3.5a8.5 8.5 0 1 1 0 17a8.5 8.5 0 1 1 0-17z M12 7.5v5.5 M12 16.5v.01",
  refresh: "M4 12a8 8 0 0 1 13.7-5.6L20 8.5 M20 4v4.5h-4.5 M20 12a8 8 0 0 1-13.7 5.6L4 15.5 M4 20v-4.5h4.5",
  map: "M3.5 6l5.5-2.5 6 2.5 5.5-2.5v14.5l-5.5 2.5-6-2.5-5.5 2.5z M9 3.5v14.5 M15 6v14.5",
  list: "M8.5 6.5h12 M8.5 12h12 M8.5 17.5h12 M4 6.5v.01 M4 12v.01 M4 17.5v.01",
  mission: "M5 20.5V4 M5 4.5h11l-2 3.5 2 3.5H5",
  people: "M9 11a3.5 3.5 0 1 0 0-7a3.5 3.5 0 0 0 0 7z M2.5 20a6.5 6.5 0 0 1 13 0 M16 4.3a3.5 3.5 0 0 1 0 6.4 M18 14a6.5 6.5 0 0 1 3.5 6",
  water: "M12 3.5c3 4 6 7.2 6 10.5a6 6 0 0 1-12 0c0-3.3 3-6.5 6-10.5z",
  mic: "M12 3a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3z M6 11a6 6 0 0 0 12 0 M12 17v4 M8 21h8",
  close: "M6 6l12 12 M18 6 6 18",
  chevron: "M9 5.5l6.5 6.5L9 18.5",
  back: "M15 5.5 8.5 12l6.5 6.5",
};

export type IconName = keyof typeof PATHS;

export function Icon({ name, size = 18, label }: { name: IconName; size?: number; label?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={label ? undefined : true}
      role={label ? "img" : undefined}
      aria-label={label}
      style={{ flex: "none" }}
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
