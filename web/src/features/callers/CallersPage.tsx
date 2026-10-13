import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../../data/api";
import { callConfig, chooseCallLocation, confirmCall, readCall, sendCallTurn, startCall, type CallConfig, type CallSession, type HelpRequestDetails, EMPTY_REQUEST_DETAILS, REQUEST_DETAIL_FIELDS, submitCallerForm } from "../../data/callers";
import type { Sent } from "../../data/intake";
import { apiMode } from "../../data/mode";
import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { Banner, BigButton } from "../../ui/components";
import { ProgressTracker } from "../../ui/ProgressTracker";
import { GeminiLiveVoice } from "../intake/gemini-live";
import { CallCaseSidebar } from "../intake/CallCaseSidebar";
import "../intake/intake.css";
import "./callers.css";

const SESSION_KEY = "reachpoint.callers.session";
type CallerMode = "chat" | "voice" | "form";
const MODES = {
  chat: { en: "Chat", th: "แชต" },
  voice: { en: "Voice", th: "เสียง" },
  form: { en: "Form", th: "แบบฟอร์ม" },
};

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

/** All three intake modes collect the same request details and share report confirmation. */
export function CallersPage() {
  const { t, lang } = useLang();
  const [mode, setMode] = useState<CallerMode>(apiMode() ? "chat" : "form");
  const [config, setConfig] = useState<CallConfig | null>(null);
  const [session, setSession] = useState<CallSession | null>(null);
  const [message, setMessage] = useState("");
  const [form, setForm] = useState<HelpRequestDetails>({ ...EMPTY_REQUEST_DETAILS });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [voiceState, setVoiceState] = useState<"off" | "connecting" | "active">("off");
  const [heard, setHeard] = useState("");
  const voice = useRef<GeminiLiveVoice | null>(null);
  const messagesEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    if (!apiMode()) return;
    void (async () => {
      try {
        const available = await callConfig();
        if (cancelled) return;
        setConfig(available);
        if (!available.chat) { setMode("form"); return; }
        const saved = sessionStorage.getItem(SESSION_KEY);
        let current: CallSession;
        try { current = saved ? await readCall(saved) : await startCall(); }
        catch { current = await startCall(); }
        if (cancelled) return;
        sessionStorage.setItem(SESSION_KEY, current.sessionId);
        setSession(current);
      } catch (cause) {
        if (!cancelled) { setMode("form"); setError(errorMessage(cause)); }
      }
    })();
    return () => { cancelled = true; voice.current?.stop(); voice.current = null; };
  }, []);

  useEffect(() => { messagesEnd.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }, [session?.messages.length]);
  useEffect(() => {
    if (!session?.revision) return;
    const { phone_number, type, people_details, n_children, n_elders, n_pets, location, coordinates,
      location_details, water_level, situation_details, emergency_detail, other_details } = session.case;
    setForm({ phone_number, type, people_details, n_children, n_elders, n_pets, location, coordinates,
      location_details, water_level, situation_details, emergency_detail, other_details });
  }, [session?.revision]);

  const stopVoice = () => {
    voice.current?.stop();
    voice.current = null;
    setVoiceState("off");
  };

  const selectMode = (next: CallerMode) => {
    if (next !== "voice") stopVoice();
    setMode(next);
  };

  const startVoice = async () => {
    if (!session || !config?.voice || voice.current) return;
    setError("");
    setVoiceState("connecting");
    const live = new GeminiLiveVoice(session.sessionId, {
      onReady: () => setVoiceState("active"),
      onTranscript: setHeard,
      onSnapshot: (snapshot) => { setSession(snapshot); if (snapshot.sent) stopVoice(); },
      onInterrupted: () => {},
      onTurnComplete: () => {},
      onError: () => { stopVoice(); setError(t(S.call.conversation.voiceError)); },
    }, "/api/callers");
    voice.current = live;
    try { await live.start(); }
    catch (cause) { stopVoice(); setError(errorMessage(cause)); }
  };

  const sendMessage = async (event: FormEvent) => {
    event.preventDefault();
    if (!session || !message.trim() || busy) return;
    setBusy(true); setError("");
    try {
      setSession(await sendCallTurn(session.sessionId, message.trim()));
      setMessage("");
    } catch (cause) { setError(errorMessage(cause)); }
    finally { setBusy(false); }
  };

  const onMessageKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== "Enter" || event.shiftKey || event.nativeEvent.isComposing) return;
    event.preventDefault();
    event.currentTarget.form?.requestSubmit();
  };

  const choose = async (action: "select" | "reject", locationId?: string) => {
    if (!session || !session.locationLookup.query || busy) return;
    setBusy(true); setError("");
    try { setSession(await chooseCallLocation(session.sessionId, session.locationLookup.query, action, locationId)); }
    catch (cause) { setError(errorMessage(cause)); }
    finally { setBusy(false); }
  };

  const confirm = async () => {
    if (!session?.canConfirm || busy) return;
    setBusy(true); setError("");
    try { setSession(await confirmCall(session.sessionId, session.revision)); stopVoice(); }
    catch (cause) {
      if (cause instanceof ApiError && cause.status === 409) {
        try { setSession(await readCall(session.sessionId)); } catch { /* Keep the visible error. */ }
      }
      setError(errorMessage(cause));
    }
    finally { setBusy(false); }
  };

  const sendForm = async (event: FormEvent) => {
    event.preventDefault();
    if (busy) return;
    setBusy(true); setError("");
    try {
      const current = session ?? await startCall();
      sessionStorage.setItem(SESSION_KEY, current.sessionId);
      setSession(current);
      setSession(await submitCallerForm(current.sessionId, form, current.revision));
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 409 && session) {
        try { setSession(await readCall(session.sessionId)); } catch { /* Keep the visible error. */ }
      }
      setError(errorMessage(cause));
    } finally { setBusy(false); }
  };

  const newConversation = async () => {
    stopVoice(); setError(""); setBusy(true);
    if (!config?.chat) { setSession(null); setForm({ ...EMPTY_REQUEST_DETAILS }); setMode("form"); setBusy(false); return; }
    try {
      const current = await startCall();
      sessionStorage.setItem(SESSION_KEY, current.sessionId);
      setSession(current); setForm({ ...EMPTY_REQUEST_DETAILS }); setMessage(""); setHeard(""); setMode(mode === "voice" ? "voice" : "chat");
    } catch (cause) { setError(errorMessage(cause)); }
    finally { setBusy(false); }
  };

  const result: Sent | null = session?.sent
    ? { ok: true, reportId: session.sent.reportId, statusUrl: session.sent.statusUrl, aiSource: session.sent.aiSource }
    : null;

  if (result?.ok) return (
    <div className="page narrow intake">
      <h1>{t(S.call.received)}</h1>
      <p>{t(S.call.receivedBody(result.reportId))}</p>
      <ProgressTracker steps={S.status.steps} current={0} label={S.progress.familyLabel} />
      <Link className="btn btn-primary btn-lg status-open" to={result.statusUrl + window.location.search}>{t(S.call.openStatus)}</Link>
      <p className="fine-print">{t(S.call.keepLink)}</p>
      <Link className="status-link" to={result.statusUrl + window.location.search}>{window.location.origin}{result.statusUrl}</Link>
      <BigButton variant="secondary" onClick={newConversation}>{t(S.call.another)}</BigButton>
    </div>
  );

  return (
    <div className={mode !== "form" ? "call-page" : "page narrow intake"}>
      <div className="call-page-heading"><h1>{t(S.call.title)}</h1>
      </div>
      {!apiMode() && <Banner kind="info">{t(S.common.needsServer)}</Banner>}
      <div className="call-mode" role="tablist" aria-label={t(S.call.title)}>
        {(["chat", "voice", "form"] as const).map((item) => <button key={item} id={`callers-tab-${item}`} type="button" role="tab" aria-selected={mode === item} aria-controls="callers-panel" onClick={() => selectMode(item)} disabled={busy || (item === "chat" && !config?.chat) || (item === "voice" && !config?.voice)}>{t(MODES[item])}</button>)}
      </div>
      {error && <Banner kind="error">{error}</Banner>}

      {mode !== "form" && session ? <div id="callers-panel" role="tabpanel" aria-labelledby={`callers-tab-${mode}`} className="call-workspace">
        <section className="call-chat-panel" aria-label={t(MODES[mode])}>
          <div className="call-chat-head">
            <p>{t(S.call.conversation.intro)}</p>
            {mode === "voice" && <div className="call-voice-bar">
              <BigButton variant={voiceState === "off" ? "secondary" : "quiet"} onClick={voiceState === "off" ? startVoice : stopVoice} disabled={!config?.voice} icon="mic">
                {voiceState === "off" ? t(S.call.conversation.voiceStart) : t(S.call.conversation.voiceStop)}
              </BigButton>
              <span role="status">{voiceState === "connecting" ? t(S.call.conversation.voiceConnecting) : voiceState === "active" ? t(S.call.conversation.voiceActive) : ""}</span>
            </div>}
            {mode === "voice" && heard && <p className="fine-print">{t(S.call.conversation.lastHeard)}: {heard}</p>}
          </div>
          <div className="call-chat-scroll">
            <div className="call-messages" role="log" aria-live="polite" aria-label={t(MODES[mode])}>
              {session.messages.map((item, index) => <div key={index} className={`call-message call-message-${item.role}`}>
                <span className="fine-print">{item.role === "user" ? (lang === "th" ? "คุณ" : "You") : (lang === "th" ? "ผู้ช่วย" : "Assistant")}</span>
                <p>{item.text}</p>
              </div>)}
            </div>
            {session.locationLookup.status === "candidates" && <section className="call-location" aria-label={t(S.call.conversation.locationTitle)}>
              <h2>{t(S.call.conversation.locationTitle)}</h2>
              <p>{t(S.call.conversation.locationNote)}</p>
              {session.locationLookup.candidates?.map((candidate) => <BigButton key={candidate.id} variant="secondary" disabled={busy} onClick={() => choose("select", candidate.id)}>{candidate.label}</BigButton>)}
              <BigButton variant="quiet" disabled={busy} onClick={() => choose("reject")}>{t(S.call.conversation.locationReject)}</BigButton>
            </section>}
            <div ref={messagesEnd} />
          </div>
          <div className="call-composer">
            {mode === "chat" && <form className="call-reply" onSubmit={sendMessage}>
              <label className="visually-hidden" htmlFor="call-reply">{t(S.call.conversation.type)}</label>
              <textarea id="call-reply" rows={2} value={message} onChange={(event) => setMessage(event.target.value)} onKeyDown={onMessageKeyDown} maxLength={500} placeholder={t(S.call.conversation.placeholder)} />
              <BigButton type="submit" disabled={busy || !message.trim()}>{busy ? t(S.call.sending) : t(S.call.conversation.send)}</BigButton>
            </form>}
            <div className="call-composer-foot">{mode === "chat" && <span className="fine-print">{t(S.call.conversation.enterHint)}</span>}<button className="call-restart" type="button" onClick={newConversation} disabled={busy}>{t(S.call.conversation.restart)}</button></div>
          </div>
        </section>
        <CallCaseSidebar session={session} busy={busy} onConfirm={confirm} />
      </div> : mode !== "form" ? <p id="callers-panel" role="tabpanel" aria-labelledby={`callers-tab-${mode}`}>{t(S.call.conversation.unavailable)}</p> :
        <form id="callers-panel" role="tabpanel" aria-labelledby="callers-tab-form" className="intake" onSubmit={sendForm}>
          <p>{lang === "th" ? "กรอกเบอร์โทรศัพท์และเลือกประเภทความช่วยเหลือ ตรวจทานก่อนส่ง ช่องอื่นที่เว้นว่างจะบันทึกว่ายังไม่ทราบ" : "Enter your phone number and choose a help type. Review before sending; other blank fields stay unknown."}</p>
          <p className="fine-print">{lang === "th" ? "หมายเลขคำขอจะสร้างหลังส่ง · ช่องทาง: แบบฟอร์ม" : "Request ID is generated after submission · Channel: Form"}</p>
          <div className="callers-form-fields">
            {REQUEST_DETAIL_FIELDS.map((field) => {
              const count = field === "n_children" || field === "n_elders" || field === "n_pets";
              return <label key={field} htmlFor={`callers-${field}`}>
                <span>{t(S.call.conversation.caseFields[field])}{(field === "phone_number" || field === "type") && " *"}</span>
                {field === "phone_number" ? <>
                  <input id="callers-phone_number" type="tel" autoComplete="tel" required maxLength={100} value={form.phone_number ?? ""} onChange={(event) => setForm((current) => ({ ...current, phone_number: event.target.value || null }))} />
                  <span className="fine-print">{lang === "th" ? "ใช้ส่งข้อความสอบถามหลังทีมอาสาสมัครเข้าช่วยเหลือ" : "For a follow-up message after volunteers visit."}</span>
                </> : field === "type" ? <select id="callers-type" required value={form.type ?? ""} onChange={(event) => setForm((current) => ({ ...current, type: event.target.value === "food" ? "food" : event.target.value === "evacuation" ? "evacuation" : null }))}>
                  <option value="">{lang === "th" ? "เลือกประเภทความช่วยเหลือ" : "Choose a help type"}</option>
                  <option value="food">{t(S.call.conversation.food)}</option>
                  <option value="evacuation">{t(S.call.conversation.evacuation)}</option>
                </select> : count ? <input id={`callers-${field}`} type="number" min={0} step={1} value={form[field] ?? ""} onChange={(event) => setForm((current) => ({ ...current, [field]: event.target.value === "" ? null : Number(event.target.value) }))} /> :
                  <textarea id={`callers-${field}`} rows={field === "coordinates" ? 1 : 2} maxLength={1000} value={form[field] ?? ""} placeholder={field === "coordinates" ? (lang === "th" ? "ละติจูด, ลองจิจูด" : "Latitude, longitude") : undefined} onChange={(event) => setForm((current) => ({ ...current, [field]: event.target.value || null }))} />}
              </label>;
            })}
          </div>
          <div className="call-send"><BigButton type="submit" disabled={busy || !form.phone_number?.trim() || !form.type}>{busy ? t(S.call.sending) : t(S.call.conversation.confirm)}</BigButton></div>
        </form>}
      <p className="fine-print">{t(S.call.privacy)}</p>
    </div>
  );
}
