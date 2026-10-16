/**
 * The victim's phone: a short conversation with ReachPoint's AI agent. One question at a time, by typing or by
 * holding the mic (the browser's speech recognition, Thai or English). Under each answer: what the system
 * understood, with the person's own words. Check-ins, warnings and plan updates arrive here too.
 */
import { useEffect, useRef, useState } from "react";
import { v2, type Fact, type Session, type TurnResult } from "./api";

type Item =
  | { kind: "agent"; text: string }
  | { kind: "person"; text: string; voice?: boolean }
  | { kind: "understood"; facts: Fact[]; reader?: string; extra?: string }
  | { kind: "notice"; text: string; at: string; type: string };

const FIELD: Record<string, [string, string]> = {
  depthRange: ["ระดับน้ำ", "Water"],
  people: ["คน", "People"],
  elderly: ["ผู้สูงอายุ", "Elderly"],
  children: ["เด็ก", "Children"],
  cannotWalk: ["เดินไม่ได้", "Can't walk"],
  urgent: ["ด่วน", "Urgent"],
  safe: ["ปลอดภัย", "Safe"],
  trend: ["แนวโน้ม", "Trend"],
  address: ["ที่อยู่", "Address"],
};

const KIND: Record<string, [string, string]> = {
  check: ["ถามไถ่ความปลอดภัย", "Safety check"],
  morning: ["เช้าวันใหม่", "New day"],
  earlyWarning: ["แจ้งเตือนล่วงหน้า", "Early warning"],
  rain: ["แจ้งเตือนฝน", "Rain alert"],
  river: ["แจ้งเตือนน้ำขึ้น", "River alert"],
  planUpdate: ["ทีมอาสา", "Volunteer plan"],
  askBack: ["คำถามยืนยัน", "Check question"],
  quiet: ["ถามข้อมูลเพิ่ม", "Question"],
  lostCall: ["สายจาก AI", "AI call"],
};

function show(f: Fact): string {
  const v = f.value;
  if (f.field === "depthRange" && Array.isArray(v)) return `${v[0]}–${v[1]} m`;
  if (v === true) return "✓";
  return String(v);
}

interface Props {
  onTurn: (r: TurnResult) => void;
  version: number;
  lang: "th" | "en";
  setLang: (l: "th" | "en") => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Rec = any;

export function Phone({ onTurn, version, lang, setLang }: Props) {
  const [session, setSession] = useState<Session | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [speak, setSpeak] = useState(false);
  const seen = useRef(new Set<string>());
  const rec = useRef<Rec>(null);
  const end = useRef<HTMLDivElement>(null);

  const start = (l: "th" | "en") =>
    v2.newChat(l).then((s) => {
      setSession(s);
      seen.current = new Set();
      setItems(s.transcript.map((t) => ({ kind: "agent", text: t.text })));
    });
  useEffect(() => {
    start(lang);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version]);
  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" });
  }, [items]);

  // check-ins and plan updates for this household
  useEffect(() => {
    if (!session?.token) return;
    const poll = () =>
      v2.me(session.token).then((m) => {
        const fresh = m.inbox.filter((i) => !seen.current.has(`${i.kind}${i.atH}`));
        fresh.forEach((i) => seen.current.add(`${i.kind}${i.atH}`));
        if (fresh.length && seen.current.size > fresh.length - 1)
          setItems((xs) => [...xs, ...fresh.slice(-3).map((i) => ({ kind: "notice" as const, text: i.text, at: i.at, type: i.kind }))]);
      }).catch(() => undefined);
    const t = window.setInterval(poll, 4000);
    return () => window.clearInterval(t);
  }, [session?.token]);

  const say = (t: string) => {
    if (!speak || !("speechSynthesis" in window)) return;
    const u = new SpeechSynthesisUtterance(t);
    u.lang = lang === "th" ? "th-TH" : "en-US";
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  };

  const send = async (t: string, channel: "chat" | "voice") => {
    if (!session || !t.trim() || busy) return;
    setItems((xs) => [...xs, { kind: "person", text: t, voice: channel === "voice" }]);
    setText("");
    setBusy(true);
    try {
      const r = await v2.turn(session.id, t, channel);
      setSession(r.session);
      const extra: string[] = [];
      if (r.effects.located) extra.push(lang === "th" ? `พบบ้าน · โซน ${r.effects.located.zoneId}` : `House found · zone ${r.effects.located.zoneId}`);
      if (r.effects.neighbour)
        extra.push(r.effects.neighbour.known ? (lang === "th" ? "บ้านนี้มีในระบบแล้ว · ไม่นับซ้ำ" : "Already known · not counted twice") : lang === "th" ? "เพิ่มบ้านใหม่" : "New household added");
      if (r.effects.depthHere) extra.push(lang === "th" ? `น้ำที่บ้านคุณน่าจะ ≈ ${r.effects.depthHere[0]} ม.` : `Water at your house most likely ≈ ${r.effects.depthHere[0]} m`);
      else if (r.effects.simHere !== undefined && r.effects.simHere !== null && r.effects.located)
        extra.push(lang === "th" ? `แบบจำลองน้ำท่วมที่บ้านคุณ ≈ ${r.effects.simHere} ม.` : `Flood simulation at your house ≈ ${r.effects.simHere} m`);
      const facts = (r.effects.facts ?? []).filter((f) => FIELD[f.field]);
      setItems((xs) => [
        ...xs,
        ...(facts.length || extra.length ? [{ kind: "understood" as const, facts, reader: r.effects.reader, extra: extra.join(" · ") }] : []),
        { kind: "agent", text: r.reply },
      ]);
      say(r.reply);
      onTurn(r);
    } catch {
      setItems((xs) => [...xs, { kind: "agent", text: lang === "th" ? "ส่งไม่สำเร็จ ลองอีกครั้งนะคะ" : "That didn't send. Please try again." }]);
    } finally {
      setBusy(false);
    }
  };

  const SR = (window as Rec).SpeechRecognition || (window as Rec).webkitSpeechRecognition;
  const holdStart = () => {
    if (!SR || busy) return;
    const r = new SR();
    r.lang = lang === "th" ? "th-TH" : "en-US";
    r.interimResults = false;
    r.onresult = (e: Rec) => send(e.results[0][0].transcript, "voice");
    r.onend = () => setListening(false);
    rec.current = r;
    setListening(true);
    r.start();
  };
  const holdEnd = () => rec.current?.stop();

  return (
    <section className="v2-phone" aria-label="Victim's phone">
      <header className="v2-phone-top">
        <span>ReachPoint · {lang === "th" ? "แจ้งขอความช่วยเหลือ" : "Ask for help"}</span>
        <span className="v2-phone-tools">
          <button type="button" onClick={() => { const l = lang === "th" ? "en" : "th"; setLang(l); start(l); }}>{lang === "th" ? "EN" : "ไทย"}</button>
          <button type="button" aria-pressed={speak} onClick={() => setSpeak(!speak)} title="Read replies aloud">{speak ? "🔊" : "🔈"}</button>
          <button type="button" onClick={() => start(lang)}>{lang === "th" ? "เริ่มใหม่" : "Restart"}</button>
        </span>
      </header>
      <div className="v2-chat" role="log" aria-live="polite">
        {items.map((it, i) =>
          it.kind === "agent" ? (
            <p key={i} className="v2-msg is-agent">{it.text}</p>
          ) : it.kind === "person" ? (
            <p key={i} className="v2-msg is-person">{it.voice ? "🎙 " : ""}{it.text}</p>
          ) : it.kind === "notice" ? (
            <div key={i} className="v2-msg is-notice">
              <span className="v2-notice-kind">{(KIND[it.type] ?? [it.type, it.type])[lang === "th" ? 0 : 1]} · {it.at}</span>
              {it.text}
            </div>
          ) : (
            <div key={i} className="v2-understood">
              <span className="v2-understood-title">
                {lang === "th" ? "ระบบเข้าใจว่า" : "Understood"}
                {it.reader ? <em> · {it.reader.startsWith("gemini") ? "Gemini" : lang === "th" ? "กฎสำรอง" : "rules"}</em> : null}
              </span>
              {it.facts.map((f, j) => (
                <span key={j} className="v2-fact">
                  <b>{FIELD[f.field][lang === "th" ? 0 : 1]}</b> {show(f)} <q>{f.quote}</q>
                </span>
              ))}
              {it.extra ? <span className="v2-fact is-extra">{it.extra}</span> : null}
            </div>
          ),
        )}
        {busy ? <p className="v2-msg is-agent is-typing">…</p> : null}
        <div ref={end} />
      </div>
      <form
        className="v2-composer"
        onSubmit={(e) => {
          e.preventDefault();
          send(text, "chat");
        }}
      >
        <input
          id="v2-chat-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={lang === "th" ? "พิมพ์ที่นี่ หรือกดค้างที่ไมค์" : "Type here, or hold the mic"}
          aria-label="Message"
        />
        {SR ? (
          <button
            type="button"
            className={`v2-mic${listening ? " is-on" : ""}`}
            onPointerDown={holdStart}
            onPointerUp={holdEnd}
            onPointerLeave={holdEnd}
            aria-label="Hold to talk"
          >
            🎙
          </button>
        ) : null}
        <button type="submit" className="v2-send" disabled={busy || !text.trim()}>
          {lang === "th" ? "ส่ง" : "Send"}
        </button>
      </form>
      <div className="v2-samples">
        {(lang === "th"
          ? ["น้ำถึงเอวแล้ว อยู่กับแม่ แม่เดินไม่ได้ บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2", "2 คน", "บ้านข้างๆ มียายอยู่คนเดียว", "ทิศตะวันออก", "ไม่มี", "มีครอบครัว เด็กเล็ก 2 คน"]
          : ["Water is up to my waist, I'm with my mom who can't walk, house 52/9 Phetkasem Soi 2", "2 of us", "Next door an old lady lives alone", "East", "No one", "A family with 2 small kids"]
        ).map((s) => (
          <button key={s} type="button" onClick={() => send(s, "chat")} disabled={busy}>
            {s.length > 28 ? s.slice(0, 26) + "…" : s}
          </button>
        ))}
      </div>
    </section>
  );
}
