import type { ReactNode } from "react";
import type { Fact } from "../api";
import { Icon } from "../../../ui/Icon";
import { readerLabel } from "./trace";

export interface Receipt {
  facts: Fact[];
  reader?: string;
  extra?: string;
  turn?: number;
  activeTurn?: number | null;
  onActiveTurn?: (turn: number | null) => void;
}

const FIELDS: Record<string, string> = {
  depthRange: "ระดับน้ำ · Water", people: "คน · People", elderly: "ผู้สูงอายุ · Elderly",
  children: "เด็ก · Children", cannotWalk: "เดินไม่ได้ · Can't walk", urgent: "ด่วน · Urgent",
  safe: "ปลอดภัย · Safe", trend: "แนวโน้ม · Trend", address: "ที่อยู่ · Address",
};

export function GeminiReceipt({ facts, reader, extra, turn, activeTurn, onActiveTurn }: Receipt) {
  return <div className={`v2-receipt${turn !== undefined && activeTurn === turn ? " is-linked" : ""}`} data-turn={turn}
    tabIndex={0} onMouseEnter={() => onActiveTurn?.(turn ?? null)} onMouseLeave={() => onActiveTurn?.(null)}
    onFocus={() => onActiveTurn?.(turn ?? null)} onBlur={() => onActiveTurn?.(null)}>
    <b>{readerLabel(reader)} · อ่านแล้ว / Read</b>
    {facts.map((fact, index) => <span key={index} className={`v2-receipt-fact${fact.field === "urgent" && fact.value ? " is-urgent" : ""}`} title={fact.quote}>
      {FIELDS[fact.field] ?? fact.field}: {Array.isArray(fact.value) ? `${fact.value.join("–")} m` : fact.value === true ? "✓" : String(fact.value)}
    </span>)}
    {extra && <span className="v2-receipt-fact">{extra}</span>}
  </div>;
}

export function Bubble({ person = false, grouped = false, at, read = false, children }: {
  person?: boolean; grouped?: boolean; at?: string; read?: boolean; children: ReactNode;
}) {
  const clock = at?.match(/\b\d{1,2}:\d{2}\b/)?.[0] ?? at;
  return <div className={`v2-bubble-group${person ? " is-person" : " is-agent"}${grouped ? " is-grouped" : ""}`}>
    {!person && !grouped && <span className="v2-bubble-name">ReachPoint</span>}
    <div className="v2-bubble-row">
      {!person && <span className={`v2-avatar small${grouped ? " is-spacer" : ""}`}><Icon name="sparkle" /></span>}
      <p className={`v2-msg ${person ? "is-person" : "is-agent"}`}>{children}</p>
      <span className="v2-message-time">{person && read && <b>อ่านแล้ว · Read</b>}{clock && <time title={at}>{clock}</time>}</span>
    </div>
  </div>;
}

export function ChatHeader({ busy, onCall, toggleCall, lang, changeLanguage, speak, toggleSpeak, restart }: {
  busy: boolean; onCall: "off" | "connecting" | "on"; toggleCall: () => void;
  lang: "th" | "en"; changeLanguage: () => void; speak: boolean; toggleSpeak: () => void; restart: () => void;
}) {
  return <header className="v2-phone-top">
    <span className="v2-avatar"><Icon name="people" /><i><Icon name="sparkle" size={14} /></i></span>
    <div className="v2-agent-name"><b>ReachPoint</b><span>ผู้ช่วย AI · Gemini<small>ตอบทันที · Replies instantly</small></span></div>
    <button type="button" aria-label={onCall === "on" ? "วางสาย · Hang up" : "โทร · Call"} className={`btn btn-sec v2-callbtn is-${onCall}`} onClick={toggleCall} disabled={onCall === "connecting"}>
      <Icon name="call" />{onCall === "on" ? "วางสาย" : onCall === "connecting" ? "…" : "โทร"}
    </button>
    {/* a choice closes the menu */}
    <details className="v2-chat-menu" onClick={event => { if ((event.target as HTMLElement).closest("button")) event.currentTarget.open = false; }}>
      <summary aria-label="เมนู · Chat menu">⋯</summary>
      <div>
        <button className="btn btn-ghost" disabled={busy} onClick={changeLanguage}>{lang === "th" ? "EN / ไทย" : "ไทย / EN"}</button>
        <button className="btn btn-ghost" aria-pressed={speak} onClick={toggleSpeak}><Icon name="volume" />อ่านออกเสียง · Read aloud</button>
        <button className="btn btn-ghost" disabled={busy} onClick={restart}>เริ่มใหม่ · Restart</button>
      </div>
    </details>
  </header>;
}
