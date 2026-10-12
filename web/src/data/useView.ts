import { useEffect, useState } from "react";
import { readView } from "./source";

export type Connection = "live" | "offline";

export type ViewState<T> =
  | { status: "loading" }
  | { status: "ready"; data: T; connection: Connection }
  | { status: "missing" }
  | { status: "error"; message: string };

/**
 * Subscribe to one derived view, e.g. `useView<AreaBriefingView>("views/areaBriefing/P-B")`.
 * Today it reads the shared fixtures; with Firestore it becomes an `onSnapshot` listener with the same
 * return shape, so screens don't change. `connection: "offline"` keeps the last data on screen with a banner.
 */
export function useView<T>(path: string | null): ViewState<T> {
  const [state, setState] = useState<ViewState<T>>({ status: "loading" });

  useEffect(() => {
    if (!path) return;
    let alive = true;
    setState({ status: "loading" });
    readView<T>(path)
      .then((r) => {
        if (!alive) return;
        setState(r ? { status: "ready", data: r.data, connection: r.connection } : { status: "missing" });
      })
      .catch((e: unknown) => alive && setState({ status: "error", message: e instanceof Error ? e.message : String(e) }));
    return () => {
      alive = false;
    };
  }, [path]);

  return state;
}
