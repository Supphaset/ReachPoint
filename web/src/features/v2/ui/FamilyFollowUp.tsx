import { Tr, useT, useUiLang, t as translate, type UiLang } from "./lang";
import { useRef, useState } from "react";
import { Icon } from "../../../ui/Icon";
import type { Choice, FamilyStatus, SimEvent, SimResult } from "../api";
import "./phase-four.css";

export function statusLabel(status: FamilyStatus, lang: UiLang = "th") {
  if (status.outcome?.kind === "pickedUp" || status.status === "evacuated") return translate("ทีมรับแล้ว · Picked up", "Picked up", lang);
  if (["safe", "atShelter"].includes(status.status)) return translate("ปลอดภัย · Safe", "Safe", lang);
  if (status.urgent) return translate("ด่วน · Urgent", "Urgent", lang);
  if (status.wantsOut) return translate("ต้องการออก · Wants to leave", "Wants to leave", lang);
  return translate("รอความช่วยเหลือ · Waiting", "Waiting", lang);
}

export function FamilyStatusCard({ status }: { status: FamilyStatus }) {
  const t = useT();
  const water = status.water;
  const { lang } = useUiLang();
  // one line by default so the chat keeps its room; tap to see the details
  const arrow = water ? { rising: "↑", falling: "↓", steady: "→" }[water.trend] : "";
  return <details className="p4-status">
    <summary>
      <span className={`v2-chip${status.urgent ? " is-red" : ""}`}>{statusLabel(status, lang)}</span>
      <span className="p4-status-line">
        {status.householdId
          ? <>{status.householdId}{status.zoneId && ` · ${status.zoneId}`}
            {water && <> · ~{water.nowM.toFixed(1)} m {arrow}</>}
            {" · "}{status.team ? `${status.team.team}${status.team.eta ? ` ~${status.team.eta}` : ""}` : t("ยังไม่มีทีม", "No team yet")}</>
          : t("ยังไม่ทราบตำแหน่งบ้าน · Location not shared yet", "Location not shared yet")}
      </span>
      <Icon name="chevron" />
    </summary>
    <div>
      <p><Tr th="น้ำขณะนี้" en="Water now" /> {water ? `~${water.nowM.toFixed(1)} m ${{ rising: "↑", falling: "↓", steady: "→" }[water.trend]} · ${t("6 ชม.", "6 h")} ~${water.in6hM.toFixed(1)} m` : t("ไม่ทราบ", "Unknown")}
        <small>Water now · 6-hour estimate</small></p>
      {water && <small><Tr th="ช่วงประมาณ" en="Estimate" /> {water.loM.toFixed(1)}–{water.hiM.toFixed(1)} m · {water.reports} <Tr th="รายงาน" en="reports" /></small>}
      <p>{status.team ? <>{status.team.team} {status.team.vehicle} ~{status.team.eta ?? "?"} <Tr th="(ยังไม่ยืนยัน)" en="Team plan · not confirmed" /></> : <><Tr th="ยังไม่มีทีมวางแผน" en="No team planned yet" /></>}</p>
      <p>{status.shelter ? <><Tr th="ศูนย์พักพิง" en="Shelter" /> {status.shelter.name} · {status.shelter.km} km · <Tr th="ลึกสุด" en="deepest" /> {status.shelter.deepestM} m<small>Nearest shelter · deepest {status.shelter.deepestM} m</small></> : <><Tr th="ศูนย์พักพิง: ไม่ทราบ" en="Shelter unknown" /></>}</p>
      <p><Tr th={<>เช็กอินถัดไป {status.nextCheck}</>} en={<>Next check-in {status.nextCheck}</>} /></p>
    </div>
  </details>;
}

/** One submission per group, including two taps before React has rendered again. Failure permits a retry. */
export function choiceSender(send: (text: string, replyTo: string) => Promise<boolean>, kind: string, select: (index: number | null) => void) {
  let locked = false;
  return async (option: Choice, index: number) => {
    if (locked) return;
    locked = true;
    select(index);
    try {
      if (await send(option.send, kind)) return;
    } catch { /* The phone shows the transport error; keep the choices retryable. */ }
    locked = false;
    select(null);
  };
}

export function ChoiceButtons({ kind, options, disabled, onSend }: { kind: string; options: Choice[]; disabled: boolean; onSend: (text: string, replyTo: string) => Promise<boolean> }) {
  const t = useT();
  const [chosen, setChosen] = useState<number | null>(null);
  const send = useRef(onSend);
  send.current = onSend;
  const choose = useRef(choiceSender((text, replyTo) => send.current(text, replyTo), kind, setChosen));
  const visit = ["teamVisit", "pickedUp", "nobodyThere", "visit"].includes(kind)
    || options.some(option => /ยังมีคน|ติดอยู่|still inside/i.test(option.label + option.send));
  return <div className={`p4-choices${visit ? " is-visit" : ""}`} role="group" aria-label={t("คำตอบ · Reply choices", "Reply choices")}>
    {options.map((option, index) => {
      const [th, ...gloss] = option.label.split(" · ");
      const urgent = visit && /ยังมีคน|ติดอยู่|still inside/i.test(option.label + option.send);
      const state = chosen === index ? " on" : chosen !== null ? " dim" : "";
      return <button key={index} className={`chip${state}${urgent ? " is-sos" : ""}`}
        disabled={disabled || chosen !== null} aria-pressed={chosen === index}
        onClick={() => void choose.current(option, index)}>
        {chosen === index && <Icon name="check" />}
        <span>{th}{gloss.length > 0 && <small>{gloss.join(" · ")}</small>}</span>
      </button>;
    })}
  </div>;
}

export function ReadyChecklist({ items }: { items: [string, string][] }) {
  const t = useT();
  const [checked, setChecked] = useState<Set<number>>(() => new Set());
  return <section className="card p4-checklist">
    <h3><Tr th="เตรียมตัว" en="Get ready" /> <span>{checked.size}/{items.length}</span></h3>
    <progress value={checked.size} max={items.length || 1} aria-label={t("เตรียมแล้ว · Ready checklist progress", "Ready checklist progress")} />
    {items.map(([th, en], index) => <label key={index} className={checked.has(index) ? "is-done" : ""}>
      <input type="checkbox" checked={checked.has(index)} onChange={event => {
        const next = new Set(checked);
        if (event.target.checked) next.add(index);
        else next.delete(index);
        setChecked(next);
      }} />
      <span><Tr th={th} en={en} /></span>
    </label>)}
  </section>;
}

export const QUICK_ACTIONS = [
  { label: "น้ำขึ้นเร็ว · Water rising fast", labelEn: "Water rising fast", send: "น้ำขึ้นเร็วมาก", sendEn: "Water is rising very fast", replyTo: "checkin" },
  { label: "ต้องการออกจากบ้าน · I need to leave", labelEn: "I need to leave", send: "ต้องการออกจากบ้าน", sendEn: "I need to leave my house", replyTo: "leaveAsk" },
  { label: "มีคนบาดเจ็บ · Someone is hurt", labelEn: "Someone is hurt", send: "มีคนบาดเจ็บ ต้องการความช่วยเหลือด่วน", sendEn: "Someone is hurt; we need urgent help", replyTo: "checkin" },
  { label: "แจ้งเพื่อนบ้าน · Report a neighbour", labelEn: "Report a neighbour", prefill: "บ้านทาง", prefillEn: "The house to the " },
  { label: "ปลอดภัยแล้ว · We're safe", labelEn: "We're safe", send: "ปลอดภัยดี", sendEn: "We're safe", replyTo: "checkin" },
] as const;

export function runQuickAction(action: typeof QUICK_ACTIONS[number], send: (text: string, replyTo: string) => Promise<boolean>, prefill: (text: string) => void, showEmergency: () => void, lang: UiLang = "th") {
  if ("prefill" in action) { prefill(translate(action.prefill, action.prefillEn, lang)); return; }
  if (action === QUICK_ACTIONS[2]) showEmergency();
  return send(translate(action.send, action.sendEn, lang), action.replyTo);
}

export function QuickActions({ disabled, onSend, onPrefill }: { disabled: boolean; onSend: (text: string, replyTo: string) => Promise<boolean>; onPrefill: (text: string) => void }) {
  const t = useT();
  const { lang } = useUiLang();
  const [hurt, setHurt] = useState(false);
  return <div className="p4-quick-group"><div className="p4-quick" aria-label={t("แจ้งเพิ่มเติม · Quick actions", "Quick actions")}>{QUICK_ACTIONS.map(action => <button className={`chip q${action === QUICK_ACTIONS[2] ? " is-sos" : ""}`} key={action.label} disabled={disabled} onClick={() => {
    void runQuickAction(action, onSend, onPrefill, () => setHurt(true), lang);
  }}>{t(action.label, action.labelEn)}</button>)}</div>{hurt && <a className="p4-emergency" href="tel:1669"><Tr th="โทร 1669" en="Call 1669" /></a>}</div>;
}

export const SIMULATIONS: { event: SimEvent; label: string; labelEn: string; proves: string; provesEn: string }[] = [
  { event: "rain", label: "ฝนตกหนักเพิ่ม · More rain", labelEn: "More rain", proves: "แจ้งเตือนฝนที่บ้านนี้ · Rain alert from the flood model's rain response at this house", provesEn: "Rain alert from the flood model's rain response at this house" },
  { event: "river", label: "น้ำแม่น้ำขึ้น · River rising", labelEn: "River rising", proves: "แจ้งครอบครัวเรื่องน้ำแม่น้ำ · River response warns this family", provesEn: "River response warns this family" },
  { event: "teamPlan", label: "ทีมวางแผนมา · A team plans to come", labelEn: "A team plans to come", proves: "ส่งแผนให้ครอบครัว ยังไม่ใช่การรับตัว · Team plan delivered to the family; pickup remains unconfirmed", provesEn: "Team plan delivered to the family; pickup remains unconfirmed" },
  { event: "teamVisit", label: "ทีมมาถึงแล้ว · The team arrives", labelEn: "The team arrives", proves: "ครอบครัวยืนยันผลการเยี่ยม · Team visit asks the family to confirm what happened", provesEn: "Team visit asks the family to confirm what happened" },
  { event: "checkin", label: "2 ชม. ต่อมา · Check-in 2 hours later", labelEn: "Check-in 2 hours later", proves: "ติดตามความปลอดภัยต่อเนื่อง · A follow-up asks whether the family is still safe", provesEn: "A follow-up asks whether the family is still safe" },
];

export async function applySimulation(result: SimResult, receive: (message: NonNullable<SimResult["message"]>) => void, refreshInbox: () => Promise<void>) {
  if (result.message) receive(result.message);
  if (result.inbox) await refreshInbox();
}

export function SimulationPanel({ enabled, busy, result, onSimulate }: { enabled: boolean; busy: boolean; result: string; onSimulate: (event: SimEvent) => void }) {
  const t = useT();
  return <section className="p4-sim"><small>Demo · simulate</small><h2><Tr th="จำลองสถานการณ์" en="What happens next?" /></h2>
    {!enabled && <p><Tr th="แจ้งตำแหน่งก่อน" en="Report first: share your location to begin." /></p>}
    <div className="p4-choices">{SIMULATIONS.map(sim => <button key={sim.event} disabled={!enabled || busy} onClick={() => onSimulate(sim.event)}>{t(sim.label, sim.labelEn)}</button>)}</div>
    <p role="status">{result || t("เลือกเหตุการณ์เพื่อติดตามครอบครัว · Choose an event to follow this family.", "Choose an event to follow this family.")}</p>
  </section>;
}
