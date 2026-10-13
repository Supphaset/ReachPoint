import { useEffect, useState } from "react";
import { apiMode, refreshMs } from "./mode";
import { readView } from "./source";

export type Connection = "live" | "offline";

export type ViewState<T> =
  | { status: "loading" }
  | { status: "ready"; data: T; connection: Connection }
  | { status: "missing" }
  | { status: "error"; message: string };

/** How often a live view is fetched again in API mode (default), until the friend's Firestore listener replaces polling. */
export const REFRESH_MS = 15_000;

/**
 * Subscribe to one derived view, e.g. `useView<AreaBriefingView>("views/areaBriefing/P-B")`.
 * Fixtures: read once. API mode: fetched again every REFRESH_MS and when the tab comes back into view; a failed
 * refresh keeps the last data on screen as `connection: "offline"` (the screens show their offline banner).
 * With Firestore it becomes an `onSnapshot` listener with the same return shape, so screens don't change.
 */
export function useView<T>(path: string | null): ViewState<T> {
  const [state, setState] = useState<ViewState<T>>({ status: "loading" });

  useEffect(() => {
    if (!path) return;
    let alive = true;
    let last: T | null = null;
    setState({ status: "loading" });
    const load = () =>
      readView<T>(path)
        .then((r) => {
          if (!alive) return;
          last = r ? r.data : null;
          setState(r ? { status: "ready", data: r.data, connection: r.connection } : { status: "missing" });
        })
        .catch((e: unknown) => {
          if (!alive) return;
          if (last !== null) setState({ status: "ready", data: last, connection: "offline" });
          else setState({ status: "error", message: e instanceof Error ? e.message : String(e) });
        });
    load();
    if (!apiMode()) return () => void (alive = false);
    const id = window.setInterval(load, refreshMs());
    const onShow = () => document.visibilityState === "visible" && load();
    document.addEventListener("visibilitychange", onShow);
    return () => {
      alive = false;
      window.clearInterval(id);
      document.removeEventListener("visibilitychange", onShow);
    };
  }, [path]);

  return state;
}
