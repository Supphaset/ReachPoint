import { Tr, useT } from "./lang";
import { useEffect, useRef, useState } from "react";
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

export function nextSimulation(done: SimEvent[]) {
  return SIMULATIONS.find(simulation => !done.includes(simulation.event));
}

export function DemoBar({ at, onAction, family }: {
  at?: string;
  onAction: (action: ClockAction) => Promise<unknown>;
  family?: DemoControls;
}) {
  const t = useT();
  const [expanded, setExpanded] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!expanded) return;
    const close = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setExpanded(false);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") { setExpanded(false); trigger.current?.focus(); }
    };
    document.addEventListener("pointerdown", close);
    document.addEventListener("keydown", escape);
    return () => { document.removeEventListener("pointerdown", close); document.removeEventListener("keydown", escape); };
  }, [expanded]);
  const [clockOpen, setClockOpen] = useState(false);
  const [acting, setActing] = useState(false);
  const lock = useRef(false);
  const [failed, setFailed] = useState(false);
  const error = failed ? t("จำลองไม่สำเร็จ ลองอีกครั้ง · Demo action failed; try again", "Demo action failed; try again") : "";
  const disabled = acting || !!family?.busy || (family !== undefined && !family.enabled);
  const next = nextSimulation(family?.done ?? []);

  async function run(action: () => Promise<unknown>) {
    if (disabled || lock.current) return;
    lock.current = true;
    setActing(true);
    setFailed(false);
    try { await action(); }
    catch { setFailed(true); }
    finally { lock.current = false; setActing(false); }
  }

  return <div ref={root} className="rp-demo-launcher" aria-label={t("สาธิต · Demo controls", "Demo controls")}>
    <div className="rp-demo-buttons">
      {family && <button className="rp-demo-primary" disabled={disabled}
        title={next && t(next.proves, next.provesEn)} onClick={() => void run(() => next ? family.onSimulate(next.event) : onAction("reset"))}>
        {next ? t(`▶ ถัดไป · Next: ${next.label}`, `▶ Next: ${next.labelEn}`) : t("เริ่มใหม่ · Start over", "Start over")}
      </button>}
      <button ref={trigger} className="rp-demo-more" aria-label={t("ตัวเลือกสาธิต · Demo options", "Demo options")} aria-expanded={expanded}
        onClick={() => setExpanded(value => !value)}>{family ? "⋯" : t("สาธิต · Demo ⋯", "Demo ⋯")}</button>
    </div>
    {family && !family.enabled && <p className="rp-demo-hint" role="status"><Tr th="แจ้งตำแหน่งในแชทก่อน" en="Share a location first" /></p>}
    <section className="rp-demo-popover" hidden={!expanded} aria-label={t("ตัวเลือกสาธิต · Demo options", "Demo options")}>
      <div className="rp-demo-title"><b><Tr th="สาธิต" en="Demo" /></b><time>{at ?? t("รอเวลา · Time pending", "Time pending")}</time>
        <button aria-label={t("ปิด · Close", "Close")} onClick={() => { setExpanded(false); trigger.current?.focus(); }}>×</button></div>
      {family && <div className="rp-demo-events" role="group" aria-label={t("เหตุการณ์ · Family events", "Family events")}>
        {SIMULATIONS.map(simulation => <button key={simulation.event} className={`chip dark${family.done.includes(simulation.event) ? " done" : ""}`}
          disabled={disabled} title={t(simulation.proves, simulation.provesEn)} onClick={() => void run(() => family.onSimulate(simulation.event))}>
          {family.done.includes(simulation.event) && "✓ "}{t(simulation.label, simulation.labelEn)}
        </button>)}
      </div>}
      <p role="status">{error || (family && !family.enabled ? t("แจ้งตำแหน่งในแชทก่อน · Share a location first", "Share a location first")
        : family?.result || t("เลื่อนเวลาสำหรับห้องสาธิตนี้ · Changes the replay for this demo room", "Changes the replay for this demo room"))}</p>
      {family && <button className="rp-demo-clock-toggle" aria-expanded={clockOpen} onClick={() => setClockOpen(value => !value)}>
        <Tr th="นาฬิกา" en="Clock" /> {clockOpen ? "⌄" : "›"}</button>}
      {(!family || clockOpen) && <div className="rp-demo-clock" role="group" aria-label={t("นาฬิกา · Replay clock", "Replay clock")}>
        {CLOCK_ACTIONS.map(([action, th, en]) => <button className="chip dark bl" key={action} disabled={disabled}
          onClick={() => void run(() => onAction(action))}><Tr th={th} en={en} /></button>)}
      </div>}
    </section>
    {error && !expanded && <p role="alert" className="rp-demo-hint">{error}</p>}
  </div>;
}
