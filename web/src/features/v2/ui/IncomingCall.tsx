import { useEffect, useRef, useState } from "react";
import { Tr, useT } from "./lang";
import { v2, type Incoming } from "../api";
import "./incomingCall.css";

export interface Caption { speaker: "heard" | "said"; text: string }
export function callTime(seconds: number) { return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`; }

export function Captions({ lines }: { lines: Caption[] }) {
  const t = useT();
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => { if (root.current) root.current.scrollTop = root.current.scrollHeight; }, [lines]);
  return <div ref={root} className="rp-call-captions" role="log" aria-live="polite" aria-label={t("คำบรรยายสด", "Live captions")}>
    {lines.map((line, i) => <p key={i}><b>{line.speaker === "said" ? "ReachPoint" : t("คุณ", "You")}: </b>{line.text}</p>)}
  </div>;
}

export function CallSummary({ lines, seconds, update }: { lines: Caption[]; seconds: number; update: string }) {
  return <div className="rp-call-summary"><b><Tr th="สายโทร" en="Call" /> · {callTime(seconds)}</b>
    <p><Tr th="ข้อมูลที่บันทึก" en="Updated" />: {update || <Tr th="ไม่มีข้อมูลใหม่ที่บันทึก" en="No new update recorded" />}</p>
    <Captions lines={lines} />
  </div>;
}

export async function respondToCall(sid: string, action: "answer" | "decline", done: () => void) {
  await v2.incoming(sid, action);
  done();
}

export function IncomingCall({ incoming, zone, sid, busy, onAnswer, onDecline, onError }: {
  incoming: Incoming; zone?: string | null; sid: string; busy: boolean;
  onAnswer: () => void; onDecline: () => void; onError: () => void;
}) {
  const [acting, setActing] = useState(false);
  const respond = async (action: "answer" | "decline") => {
    if (acting || busy) return;
    setActing(true);
    try { await respondToCall(sid, action, action === "answer" ? onAnswer : onDecline); }
    catch { setActing(false); onError(); }
  };
  return <section className="rp-incoming" aria-label="ReachPoint incoming call">
    <div className="rp-call-avatar">R</div>
    <h2><Tr th="ReachPoint โทรมา" en="ReachPoint is calling" /></h2>
    <p>{incoming.kind === "lostContact" ? <Tr th="เรายังไม่ได้รับข่าวจากคุณ" en="We haven't heard from you" /> : <Tr th="ถามความปลอดภัย" en="Safety check" />}</p>
    <p>{zone} · {incoming.at}</p>
    <p><Tr th="สายผ่านเบราว์เซอร์สำหรับสาธิต" en="Browser call for this demo" /></p>
    <div className="rp-call-actions">
      <button className="rp-call-decline" disabled={busy || acting} onClick={() => void respond("decline")}><Tr th="ปฏิเสธ" en="Decline" /></button>
      <button className="rp-call-answer" disabled={busy || acting} onClick={() => void respond("answer")}><Tr th="รับสาย" en="Answer" /></button>
    </div>
  </section>;
}
