import { Tr, useT } from "./ui/lang";
/**
 * The victim's phone: a short conversation with ReachPoint's AI agent. One question at a time, by typing or by
 * holding the mic (the browser's speech recognition, Thai or English). Under each answer: what the system
 * understood, with the person's own words. Check-ins, warnings and plan updates arrive here too.
 */
import { createPortal } from "react-dom";
import { useEffect, useRef, useState } from "react";
import { v2, type LocationPin, type ShelterRoute, type NbConfirm, type Session, type TurnResult, type FamilyStatus, type Choice, type SimEvent, type SimResult } from "./api";
import { NeighbourPicture } from "./NeighbourPicture";
import { LocationCard, HouseLocation } from "./ui/LocationCard";
import { ShelterCard } from "./ui/ShelterCard";
import { ApiError } from "../../data/api";
import { FamilyStatusCard, ChoiceButtons, ReadyChecklist, QuickActions, SIMULATIONS, applySimulation } from "./ui/FamilyFollowUp";
import { Bubble, ChatHeader, GeminiReceipt, type Receipt } from "./ui/ChatShell";
import { BoatRequestCard, NoticeCard } from "./ui/NoticeCard";
import { Icon } from "../../ui/Icon";
import { DemoBar } from "./ui/DemoBar";
import type { ClockAction } from "./ui/Shared";
import { LiveCall } from "./liveVoice";

type Item =
  | { kind: "agent"; text: string; choices?: { kind: string; options: Choice[] }; checklist?: [string, string][]; route?: ShelterRoute; at?: string; boat?: FamilyStatus | null; house?: { lon: number; lat: number; buildingId?: string; zoneId?: string } }
  | { kind: "person"; text: string; voice?: boolean; pin?: LocationPin; at?: string; receipt?: Receipt }

  | { kind: "notice"; text: string; at: string; type: string; replyTo?: string; choices?: Choice[] }
  | { kind: "confirm"; c: NbConfirm };

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

const DEMO_MESSAGES = {
  th: ["น้ำถึงเอวแล้ว อยู่กับแม่ แม่เดินไม่ได้ บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2", "2 คน", "บ้านข้างๆ มียายอยู่คนเดียว", "ทิศตะวันออก", "ไม่มี", "มีครอบครัว เด็กเล็ก 2 คน"],
  en: ["Water is up to my waist, I'm with my mom who can't walk, house 52/9 Phetkasem Soi 2", "2 of us", "Next door an old lady lives alone", "East", "No one", "A family with 2 small kids"],
};

interface Props {
  at?: string;
  judgeMode?: boolean;
  onTurn: (r: TurnResult) => number;
  onClock: (action: ClockAction) => Promise<unknown>;
  activeTurn: number | null;
  onActiveTurn: (turn: number | null) => void;
  onSimulation: (result: SimResult) => void;
  version: number;
  lang: "th" | "en";
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Rec = any;

export function Phone({ onTurn, onSimulation, version, lang, at, judgeMode = true, onClock, activeTurn, onActiveTurn }: Props) {
  const t = useT();
  const [session, setSession] = useState<Session | null>(null);
  const [status, setStatus] = useState<FamilyStatus | null>(null);
  const [done, setDone] = useState<SimEvent[]>([]);
  const [simResult, setSimResult] = useState("");
  const requestBusy = useRef(false);
  const statusVersion = useRef(0);
  const currentSession = useRef<string | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [text, setText] = useState(DEMO_MESSAGES[lang][0]);
  const [askLocation, setAskLocation] = useState(false);
  const [outside, setOutside] = useState(false);
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [speak, setSpeak] = useState(false);
  const seen = useRef(new Set<string>());
  const rec = useRef<Rec>(null);
  const end = useRef<HTMLDivElement>(null);
  const call = useRef<LiveCall | null>(null);
  const [onCall, setOnCall] = useState<"off" | "connecting" | "on">("off");

  const start = (l: "th" | "en") =>
    v2.newChat(l).then((s) => {
      currentSession.current = s.id;
      statusVersion.current++;
      setStatus(null);
      setSimResult("");
      setDone([]);
      setSession(s);
      setAskLocation(!s.pin);
      setOutside(false);
      setText(DEMO_MESSAGES[l][0]);
      seen.current = new Set();
      setItems(s.transcript.map((t) => ({ kind: "agent", text: t.text, at })));
    });
  useEffect(() => {
    start(lang);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version]);
  useEffect(() => {
    // scroll the chat itself, never the page: scrollIntoView would drag the whole page to the phone
    const box = end.current?.parentElement;
    if (box) box.scrollTop = box.scrollHeight;
  }, [items.length]);

  const refreshInbox = async (s: Session) => {
    const m = await v2.me(s.token);
    if (currentSession.current !== s.id) return;
    const fresh = m.inbox.filter(i => !seen.current.has(`${i.kind}:${i.atH}:${i.text}`));
    if (!fresh.length) return; // nothing new: leave the chat (and the page's scroll) alone
    fresh.forEach(i => seen.current.add(`${i.kind}:${i.atH}:${i.text}`));
    setItems(xs => [...xs, ...fresh.map(i => ({ kind: "notice" as const, text: i.text, at: i.at, type: i.kind, choices: i.choices }))]);
  };
  useEffect(() => {
    if (!session) return;
    const s = session;
    const poll = () => refreshInbox(s).catch(() => undefined);
    const pollStatus = () => {
      const version = statusVersion.current;
      return v2.status(s.id).then(result => {
        if (currentSession.current === s.id && !requestBusy.current && statusVersion.current === version) setStatus(result);
      }).catch(() => undefined);
    };
    void poll();
    void pollStatus();
    const inboxTimer = window.setInterval(poll, 4000);
    const statusTimer = window.setInterval(pollStatus, 10000);
    return () => { window.clearInterval(inboxTimer); window.clearInterval(statusTimer); };
  }, [session?.id]);

  const simulate = async (event: SimEvent) => {
    if (!session || requestBusy.current) return;
    const s = session;
    requestBusy.current = true;
    statusVersion.current++;
    setBusy(true);
    try {
      const result = await v2.simulate(s.id, event);
      if (currentSession.current !== s.id) return;
      setStatus(result.status);
      setDone(events => events.includes(event) ? events : [...events, event]);
      const simulation = SIMULATIONS.find(sim => sim.event === event);
      setSimResult(result.message || result.inbox
        ? simulation ? t(simulation.proves, simulation.provesEn) : ""
        : t("อัปเดตสถานะแล้ว ไม่มีข้อความใหม่ · Status updated; no new family message for this event.", "Status updated; no new family message for this event."));
      onSimulation(result);
      await applySimulation(result, message => setItems(xs => [...xs, {
        kind: "notice", text: message.text, at: result.status.now,
        type: event === "teamPlan" ? "planUpdate" : event, replyTo: message.kind,
        choices: message.choices.map(([label, send]) => ({ label, send })),
      }]), async () => {
        try { await refreshInbox(s); }
        catch { setSimResult(t("จำลองแล้ว รอโหลดข้อความทีมอีกครั้ง · Event applied; team message pending. Inbox will retry.", "Event applied; team message pending. Inbox will retry.")); }
      });
    } catch (error) {
      setSimResult(error instanceof ApiError && error.status === 409 ? t("แจ้งตำแหน่งก่อน · Report first", "Report first") : t("จำลองไม่สำเร็จ ลองอีกครั้ง · Simulation failed; try again", "Simulation failed; try again"));
    } finally { requestBusy.current = false; setBusy(false); }
  };

  const say = (t: string) => {
    if (!speak || !("speechSynthesis" in window)) return;
    const u = new SpeechSynthesisUtterance(t);
    u.lang = lang === "th" ? "th-TH" : "en-US";
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  };

  const send = async (t: string, channel: "chat" | "voice", pin?: LocationPin, replyTo?: string): Promise<boolean> => {
    if (!session || !t.trim() || requestBusy.current || busy) return false;
    if (!replyTo && !pin && call.current && onCall === "on") {  // on a call: typed words go to Gemini Live like speech (it echoes them back)
      call.current.say(t);
      setText("");
      return true;
    }
    requestBusy.current = true;
    statusVersion.current++;
    const sid = session.id;
    setItems((xs) => [...xs, { kind: "person", text: t, voice: channel === "voice", pin, at }]);
    setText("");
    setBusy(true);
    try {
      const r = await v2.turn(sid, t, channel, pin, replyTo);
      if (currentSession.current !== sid) return false;
      apply(r);
      return true;
    } catch {
      setItems((xs) => [...xs, { kind: "agent", text: lang === "th" ? "ส่งไม่สำเร็จ ลองอีกครั้งนะคะ" : "That didn't send. Please try again." }]);
      return false;
    } finally {
      requestBusy.current = false;
      setBusy(false);
    }
  };

  /** Show what the agent understood and said, from a typed turn or a voice-call turn. */
  const apply = (r: TurnResult) => {
    {
      setSession(r.session);
      if (r.status) { statusVersion.current++; setStatus(r.status); }
      setAskLocation(!!r.effects.askLocation || !r.session.pin);
      setOutside(!!r.effects.pinOutside);
      const extra: string[] = [];
      if (r.effects.located) extra.push(lang === "th" ? `พบบ้าน · โซน ${r.effects.located.zoneId}` : `House found · zone ${r.effects.located.zoneId}`);
      if (r.effects.shelter?.going) extra.push(lang === "th" ? `กำลังไป ${r.effects.shelter.name}` : `Walking to ${r.effects.shelter.name}`);
      if (r.effects.neighbour)
        extra.push(r.effects.neighbour.known ? (lang === "th" ? "บ้านนี้มีในระบบแล้ว · ไม่นับซ้ำ" : "Already known · not counted twice") : lang === "th" ? "เพิ่มบ้านใหม่" : "New household added");
      if (r.effects.depthHere) extra.push(lang === "th" ? `น้ำที่บ้านคุณน่าจะ ≈ ${r.effects.depthHere[0]} ม.` : `Water at your house most likely ≈ ${r.effects.depthHere[0]} m`);
      else if (r.effects.simHere !== undefined && r.effects.simHere !== null && r.effects.located)
        extra.push(lang === "th" ? `แบบจำลองน้ำท่วมที่บ้านคุณ ≈ ${r.effects.simHere} ม.` : `Flood simulation at your house ≈ ${r.effects.simHere} m`);
      const turn = onTurn(r);
      const facts = (r.effects.facts ?? []).filter((f) => FIELD[f.field]);
      const located = r.effects.located;
      const point = located && located.lon != null && located.lat != null
        ? { lon: located.lon, lat: located.lat } : r.session.pin;
      const agent: Item = {
        kind: "agent",
        text: r.reply,
        at: r.status?.now ?? at,
        boat: r.effects.choices?.kind === "ride" ? r.status ?? null : undefined,
        choices: r.effects.choices,
        checklist: r.effects.checklist,
        route: r.effects.shelterRoute,
        house: located && point ? { ...point, buildingId: located.buildingId, zoneId: located.zoneId } : undefined,
      };
      setItems(xs => {
        const person = xs.reduce((last, item, index) => item.kind === "person" ? index : last, -1);
        return [
          ...xs.map((item, index) => index === person && item.kind === "person"
            ? { ...item, receipt: { turn, facts, reader: r.effects.reader, extra: extra.join(" · ") } } : item),
          agent,
          ...(r.effects.nbConfirm ? [{ kind: "confirm" as const, c: r.effects.nbConfirm }] : []),
        ];
      });
      if (!call.current) say(r.reply);  // on a call Gemini already speaks it
    }
  };

  const toggleCall = async () => {
    if (!session) return;
    if (call.current) {
      call.current.stop();
      call.current = null;
      setOnCall("off");
      return;
    }
    setOnCall("connecting");
    const c = new LiveCall(session.id, {
      onReady: () => setOnCall("on"),
      onCaller: (t) => { setItems((xs) => [...xs, { kind: "person", text: t, voice: true, at }]); setBusy(true); },
      onTurn: (r) => { setBusy(false); apply(r); },
      onEnd: (m) => {
        call.current = null;
        setOnCall("off");
        setBusy(false);
        if (m) setItems((xs) => [...xs, { kind: "agent", text: m }]);
      },
    });
    call.current = c;
    try {
      await c.start();
    } catch (e) {
      call.current = null;
      setOnCall("off");
      setItems((xs) => [...xs, { kind: "agent", text: lang === "th" ? "เริ่มสายไม่ได้ (ต้องอนุญาตไมโครโฟน) พิมพ์แทนได้ค่ะ" : `Couldn't start the call (${(e as Error).message}). Typing still works.` }]);
    }
  };
  useEffect(() => () => { currentSession.current = null; call.current?.stop(); }, []);

  const lastAgent = items.reduce((last, item, index) => item.kind === "agent" ? index : last, -1);
  const lastConfirm = items.reduce((k, it, i) => (it.kind === "confirm" ? i : k), -1);
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
    <div className="p4-family"><section className="v2-phone" aria-label="Victim's phone">
      <ChatHeader busy={busy} onCall={onCall} toggleCall={() => void toggleCall()}
        speak={speak} toggleSpeak={() => setSpeak(!speak)} restart={() => {
          // In the demo a restart is a new family: reset the room too, or the old family's team messages come back.
          if (judgeMode) void onClock("reset"); else void start(lang);
        }} />
      {onCall === "on" ? <p className="v2-oncall">{lang === "th" ? t("กำลังคุยกับ ReachPoint ด้วยเสียง · Gemini Live", "Gemini Live") : "On a call with ReachPoint · Gemini Live"}</p> : null}
      {status && <FamilyStatusCard status={status} />}
      <div className="v2-chat" role="log" aria-live="polite">
        {/* the Yes/No buttons stay on the latest picture even when a notice arrives after it */}
        {items.map((it, i) =>
          it.kind === "agent" ? (
            <div key={i}>
              <Bubble at={it.at} grouped={items[i - 1]?.kind === "agent"}>{it.text}</Bubble>
              {it.choices && <ChoiceButtons {...it.choices} disabled={busy} onSend={(text, kind) => send(text, "chat", undefined, kind)} />}
              {it.boat !== undefined && <BoatRequestCard status={it.boat} />}
              {it.checklist && <ReadyChecklist items={it.checklist} />}
              {it.house && <HouseLocation point={it.house} buildingId={it.house.buildingId} zoneId={it.house.zoneId} />}
              {it.route && <ShelterCard route={it.route} busy={busy} onAnswer={reply => send(reply, "chat")} />}
              {i === lastAgent && (askLocation || outside) && <LocationCard busy={busy || onCall !== "off"} outside={outside} onPin={async pin => { await send(pin.method === "gps" ? t("ตำแหน่งจาก GPS", "GPS location shared") : t("ปักหมุดบ้านแล้ว", "House pinned"), "chat", pin); }} />}
            </div>
          ) : it.kind === "person" ? (
            <div key={i} className="v2-person-turn">
              <Bubble person at={it.at} read={!!it.receipt} grouped={items[i - 1]?.kind === "person"}>{it.voice && <Icon name="mic" />}{it.text}</Bubble>
              {it.pin && <HouseLocation point={it.pin} sent accuracyM={it.pin.accuracyM} />}
              {it.receipt && <GeminiReceipt {...it.receipt} activeTurn={activeTurn} onActiveTurn={onActiveTurn} />}
            </div>
          ) : it.kind === "confirm" ? (
            <div key={i} className="v2-msg is-agent v2-confirm">
              <NeighbourPicture c={it.c} lang={lang} />
              <span className="v2-nb-legend"><i className="is-me" />{lang === "th" ? "บ้านคุณ" : "your house"} <i className="is-cand" />{lang === "th" ? `บ้านที่ถาม (${it.c.n}/${it.c.of})` : `asked about (${it.c.n}/${it.c.of})`}</span>
              {i === lastConfirm && session?.pending === "nb_confirm" ? (
                <span className="v2-confirm-btns">
                  <button type="button" onClick={() => send(lang === "th" ? "ใช่" : "Yes", "chat")} disabled={busy}>{lang === "th" ? "ใช่ หลังนี้" : "Yes, this one"}</button>
                  <button type="button" onClick={() => send(lang === "th" ? "ไม่ใช่" : "No", "chat")} disabled={busy}>{lang === "th" ? "ไม่ใช่" : "No"}</button>
                </span>
              ) : null}
            </div>
          ) : it.kind === "notice" ? (
            <NoticeCard key={i} kind={it.type} at={it.at}>
              <p>{it.text}</p>
              {it.type === "planUpdate" && <span className="pill p-plain"><Tr th="แผน ยังไม่ใช่การรับตัว" en="Planned, not rescued yet" /></span>}
              {it.choices && <ChoiceButtons kind={it.replyTo ?? it.type} options={it.choices} disabled={busy} onSend={(text, kind) => send(text, "chat", undefined, kind)} />}
            </NoticeCard>
          ) : null,
        )}
        {busy ? <p className="v2-msg is-agent is-typing">…</p> : null}
        <div ref={end} />
      </div>
      {judgeMode && <div className="v2-samples"><b>SAMPLE</b>
        {DEMO_MESSAGES[lang].map((s) => (
          <button key={s} type="button" onClick={() => send(s, "chat")} disabled={busy}>
            {s.length > 28 ? s.slice(0, 26) + "…" : s}
            {lang === "th" && <span className="rp-gloss">{DEMO_MESSAGES.en[DEMO_MESSAGES.th.indexOf(s)]}</span>}
          </button>
        ))}
      </div>}
      {status?.zoneId && <QuickActions disabled={busy} onSend={(text, kind) => send(text, "chat", undefined, kind)} onPrefill={value => { setText(value); document.getElementById("v2-chat-input")?.focus(); }} />}
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
            <Icon name="mic" />
          </button>
        ) : null}
        <button type="submit" className="v2-send" disabled={busy || !text.trim()}>
          <Icon name="send" label={t("ส่ง · Send", "Send")} />
        </button>
      </form>

    </section>
      {judgeMode && createPortal(<DemoBar at={at} onAction={onClock} family={{
        enabled: !!status?.zoneId, busy, result: simResult, done, onSimulate: simulate,
      }} />, document.body)}
    </div>
  );
}
