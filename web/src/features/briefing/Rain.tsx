import { useEffect, useState } from "react";
import type { RainStatus } from "../../data/contract";
import { now } from "../../data/clock";
import { useView } from "../../data/useView";
import { Banner } from "../../ui/components";
import { Icon } from "../../ui/Icon";

/** The newest snapshot at or before the clock; null before the first one. */
export function pickSnapshot(snaps: RainStatus[], at: number): RainStatus | null {
  let best: RainStatus | null = null;
  for (const s of snaps) if (Date.parse(s.asOf) <= at && (!best || s.asOf > best.asOf)) best = s;
  return best;
}

function useMinute() {
  const [t, setT] = useState(now);
  useEffect(() => {
    const id = window.setInterval(() => setT(now()), 30_000);
    return () => window.clearInterval(id);
  }, []);
  return t;
}

/**
 * D41 rain context for an area: one line, and an amber note while the heavy-rain prompt is up. Rain is a satellite
 * estimate, never water depth; teams see the note, the coordinator accepts or dismisses the re-checks on the desk.
 */
export function RainLine({ areaId, labels = {} }: { areaId: string; labels?: Record<string, string> }) {
  const v = useView<RainStatus[]>(`views/rain/${areaId}`);
  const t = useMinute();
  if (v.status === "loading") return null;
  if (v.status !== "ready")
    return (
      <p className="rain-line fine-print">
        <Icon name="water" size={14} /> Rain data unavailable
      </p>
    );
  const s = pickSnapshot(v.data, t);
  if (!s) return null;
  return (
    <div className="rain">
      <p className="rain-line fine-print" title={s.source}>
        <Icon name="water" size={14} /> {s.line}
      </p>
      {s.prompt && (
        <Banner kind="stale">
          <strong>{s.prompt.title}</strong>
          <ul className="rain-recheck">
            {s.prompt.recheck.map((r) => (
              <li key={r.segmentId}>
                <strong>{labels[r.segmentId] ?? r.segmentId}</strong>: {r.reason}
              </li>
            ))}
          </ul>
          <span className="fine-print">Rain alone can't say where or how deep. The desk decides on re-checks.</span>
        </Banner>
      )}
    </div>
  );
}
