import { useRef, useState } from "react";
import type { SimEvent } from "../api";
import { SIMULATIONS } from "./FamilyFollowUp";
import type { ClockAction } from "./Shared";

const CLOCK_ACTIONS: [ClockAction, string, string][] = [
  ["advance", "+30 นาที", "+30 min"],
  ["morning", "เช้า 07:00", "Next 07:00"],
  ["rain", "แจ้งเตือนฝน", "Rain alert"],
  ["river", "น้ำแม่น้ำขึ้น", "River rising"],
  ["flood", "จำลองคำขอจำนวนมาก", "Flood the system"],
  ["reset", "เริ่มใหม่", "Reset"],
];

export interface DemoControls {
  enabled: boolean;
  busy: boolean;
  result: string;
  done: SimEvent[];
  onSimulate: (event: SimEvent) => Promise<void>;
}

export function DemoBar({ at, onAction, family }: {
  at?: string;
  onAction: (action: ClockAction) => Promise<unknown>;
  family?: DemoControls;
}) {
  const [expanded, setExpanded] = useState(false);
  // On the Report page the family events are the story; the replay clock folds behind one chip.
  const [clockOpen, setClockOpen] = useState(false);
  const [acting, setActing] = useState(false);
  const lock = useRef(false);
  const [error, setError] = useState("");
  const disabled = acting || !!family?.busy || (family !== undefined && !family.enabled);
  const next = SIMULATIONS.find(simulation => !family?.done.includes(simulation.event))?.event;

  async function run(action: () => Promise<unknown>) {
    if (disabled || lock.current) return;
    lock.current = true;
    setActing(true);
    setError("");
    try { await action(); }
    catch { setError("จำลองไม่สำเร็จ ลองอีกครั้ง · Demo action failed; try again"); }
    finally { lock.current = false; setActing(false); }
  }

  return <footer className={`rp-demo-bar${expanded ? " is-expanded" : ""}`} aria-label="แถบสาธิต · Demo controls">
    <button className="rp-demo-handle" aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>สาธิต · Demo {expanded ? "⌄" : "⌃"}</button>
    <div className="rp-demo-title"><span className="pill p-night">DEMO</span>
      <b>{family ? "จำลองสถานการณ์" : "นาฬิกาสาธิต"}<small>{family ? "What happens next?" : "Demo clock"}</small></b>
      <time>{at ?? "รอเวลา · Time pending"}</time>
    </div>
    {family && <div className="rp-demo-events" role="group" aria-label="เหตุการณ์ · Family events">
      {SIMULATIONS.map(simulation => {
        const done = family.done.includes(simulation.event);
        return <button key={simulation.event} className={`chip dark${done ? " done" : next === simulation.event ? " next" : ""}`}
          disabled={disabled} title={simulation.proves} onClick={() => void run(() => family.onSimulate(simulation.event))}>
          {done && <span aria-hidden="true">✓</span>}{simulation.label}
          {!done && next === simulation.event && <span className="rp-demo-next">ถัดไป · Next</span>}
        </button>;
      })}
      <button className="chip dark" aria-expanded={clockOpen} onClick={() => setClockOpen(value => !value)}>
        นาฬิกา · Clock {clockOpen ? "⌄" : "›"}</button>
    </div>}
    {(!family || clockOpen) && <div className="rp-demo-clock" role="group" aria-label="นาฬิกา · Replay clock">
      {CLOCK_ACTIONS.map(([action, th, en]) => <button className="chip dark bl" key={action} disabled={disabled}
        onClick={() => void run(() => onAction(action))}>{th}<small>{en}</small></button>)}
    </div>}
    <p role="status">{error || (family && !family.enabled
      ? "แจ้งตำแหน่งในแชทก่อน · Share a location in the phone first"
      : family?.result || "เลื่อนเวลาสำหรับห้องสาธิตนี้ · Changes the replay for this demo room")}</p>
  </footer>;
}
