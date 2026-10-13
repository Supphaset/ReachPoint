import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../../data/api";
import { callConfig, chooseCallLocation, confirmCall, readCall, sendCallTurn, startCall, type CallConfig, type CallSession } from "../../data/call";
import { sendRequest, type Sent } from "../../data/intake";
import { apiMode } from "../../data/mode";
import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { Banner, BigButton } from "../../ui/components";
import { Icon } from "../../ui/Icon";
import { ProgressTracker } from "../../ui/ProgressTracker";
import { GeminiLiveVoice } from "./gemini-live";
import "./intake.css";

const SESSION_KEY = "reachpoint.call.session";

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

/** A caller can use one message, or collect and confirm the same report through chat and Gemini Live. */
export function CallPage() {
  const { t, lang } = useLang();
  const [mode, setMode] = useState<"conversation" | "form">(apiMode() ? "conversation" : "form");
  const [config, setConfig] = useState<CallConfig | null>(null);
  const [session, setSession] = useState<CallSession | null>(null);
  const [message, setMessage] = useState("");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sent, setSent] = useState<Sent | null>(null);
  const [voiceState, setVoiceState] = useState<"off" | "connecting" | "active">("off");
  const [heard, setHeard] = useState("");
  const [focusEnd, setFocusEnd] = useState(0);
  const box = useRef<HTMLTextAreaElement>(null);
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
    const el = box.current;
    if (!focusEnd || !el) return;
    el.focus();
    el.setSelectionRange(el.value.length, el.value.length);
  }, [focusEnd]);

  const stopVoice = () => {
    voice.current?.stop();
    voice.current = null;
    setVoiceState("off");
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
    });
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
    try { setSession(await confirmCall(session.sessionId)); stopVoice(); }
    catch (cause) { setError(errorMessage(cause)); }
    finally { setBusy(false); }
  };

  const sendForm = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setSent(await sendRequest(text));
    setBusy(false);
  };

  const add = (line: string) => {
    setText((value) => value.trim() ? `${value.replace(/\s+$/, "")}\n${line}` : line);
    setFocusEnd((n) => n + 1);
  };

  const newConversation = async () => {
    stopVoice(); setError(""); setBusy(true);
    if (!config?.chat) { setSent(null); setText(""); setMode("form"); setBusy(false); return; }
    try {
      const current = await startCall();
      sessionStorage.setItem(SESSION_KEY, current.sessionId);
      setSession(current); setMessage(""); setHeard(""); setSent(null); setMode("conversation");
    } catch (cause) { setError(errorMessage(cause)); }
    finally { setBusy(false); }
  };

  const result: Sent | null = session?.sent
    ? { ok: true, reportId: session.sent.reportId, statusUrl: session.sent.statusUrl, aiSource: session.sent.aiSource }
    : sent;

  if (result?.ok) return (
    <div className="page narrow intake">
      <h1>{t(S.call.received)}</h1>
      <p>{t(S.call.receivedBody(result.reportId))}</p>
      <ProgressTracker steps={S.progress.family} current={0} label={S.progress.familyLabel} />
      <Link className="btn btn-primary btn-lg status-open" to={result.statusUrl + window.location.search}>{t(S.call.openStatus)}</Link>
      <p className="fine-print">{t(S.call.keepLink)}</p>
      <Link className="status-link" to={result.statusUrl + window.location.search}>{window.location.origin}{result.statusUrl}</Link>
      <BigButton variant="secondary" onClick={newConversation}>{t(S.call.another)}</BigButton>
      <p className="fine-print">{t(S.call.emergency)}</p>
    </div>
  );

  return (
    <div className="page narrow intake">
      <h1>{t(S.call.title)}</h1>
      <p className="call-danger" role="note"><Icon name="alert" size={20} /><span>{t(S.call.danger)}</span></p>
      {!apiMode() && <Banner kind="info">{t(S.common.needsServer)}</Banner>}
      <div className="call-mode" role="tablist" aria-label={t(S.call.title)}>
        <button type="button" role="tab" aria-selected={mode === "conversation"} onClick={() => setMode("conversation")} disabled={!config?.chat}>{t(S.call.conversation.tab)}</button>
        <button type="button" role="tab" aria-selected={mode === "form"} onClick={() => setMode("form")}>{t(S.call.conversation.formTab)}</button>
      </div>
      {error && <Banner kind="error">{error}</Banner>}

      {mode === "conversation" && session ? <>
        <p>{t(S.call.conversation.intro)}</p>
        <div className="call-voice-bar">
          <BigButton variant={voiceState === "off" ? "secondary" : "quiet"} onClick={voiceState === "off" ? startVoice : stopVoice} disabled={!config?.voice} icon="mic">
            {voiceState === "off" ? t(S.call.conversation.voiceStart) : t(S.call.conversation.voiceStop)}
          </BigButton>
          <span role="status">{voiceState === "connecting" ? t(S.call.conversation.voiceConnecting) : voiceState === "active" ? t(S.call.conversation.voiceActive) : ""}</span>
        </div>
        {!config?.voice && <p className="fine-print">{t(S.call.conversation.voiceUnavailable)}</p>}
        {heard && <p className="fine-print">{t(S.call.conversation.lastHeard)}: {heard}</p>}
        <div className="call-messages" role="log" aria-live="polite" aria-label={t(S.call.conversation.tab)}>
          {session.messages.map((item, index) => <div key={index} className={`call-message call-message-${item.role}`}>
            <span className="fine-print">{item.role === "user" ? (lang === "th" ? "คุณ" : "You") : (lang === "th" ? "ผู้ช่วย" : "Assistant")}</span>
            <p>{item.text}</p>
          </div>)}
          <div ref={messagesEnd} />
        </div>
        {session.locationLookup.status === "candidates" && <section className="call-location" aria-label={t(S.call.conversation.locationTitle)}>
          <h2>{t(S.call.conversation.locationTitle)}</h2>
          <p>{t(S.call.conversation.locationNote)}</p>
          {session.locationLookup.candidates?.map((candidate) => <BigButton key={candidate.id} variant="secondary" disabled={busy} onClick={() => choose("select", candidate.id)}>{candidate.label}</BigButton>)}
          <BigButton variant="quiet" disabled={busy} onClick={() => choose("reject")}>{t(S.call.conversation.locationReject)}</BigButton>
        </section>}
        {session.locationLookup.status === "confirmed" && <p className="fine-print">{t(S.call.conversation.selected)}: {session.locationLookup.label || session.locationLookup.query}</p>}
        {session.summary && <section className="call-summary" aria-label={t(S.call.conversation.confirmTitle)}>
          <h2>{t(S.call.conversation.confirmTitle)}</h2>
          <p>{session.summary}</p>
          <p className="fine-print">{t(S.call.conversation.correction)}</p>
          <BigButton onClick={confirm} disabled={!session.canConfirm || busy}>{busy ? t(S.call.sending) : t(S.call.conversation.confirm)}</BigButton>
        </section>}
        <form className="call-reply" onSubmit={sendMessage}>
          <label htmlFor="call-reply">{t(S.call.conversation.type)}</label>
          <textarea id="call-reply" rows={3} value={message} onChange={(event) => setMessage(event.target.value)} maxLength={500} placeholder={t(S.call.conversation.placeholder)} />
          <BigButton type="submit" disabled={busy || !message.trim()}>{t(S.call.conversation.send)}</BigButton>
        </form>
        <BigButton variant="quiet" onClick={newConversation} disabled={busy}>{t(S.call.conversation.restart)}</BigButton>
      </> : mode === "conversation" ? <p>{t(S.call.conversation.unavailable)}</p> :
        <form className="intake" onSubmit={sendForm}>
          <label htmlFor="intake-text">{t(S.call.prompt)}</label>
          <div className="call-hints" role="group" aria-label={t(S.call.helpTitle)}>
            <span className="fine-print">{t(S.call.helpTitle)}</span>
            <div className="call-hint-row">{S.call.hints.map((hint) => {
              const done = text.includes(t(hint.line).trim());
              return <button key={hint.key} type="button" className={`call-hint ${done ? "is-done" : ""}`} onClick={() => add(t(hint.line))} aria-pressed={done}>
                <Icon name={done ? "check" : "chevron"} size={16} /><span>{t(hint.label)}</span>
                {done && <span className="visually-hidden">{t(S.call.added)}</span>}
              </button>;
            })}</div>
          </div>
          <textarea id="intake-text" ref={box} rows={7} value={text} onChange={(event) => setText(event.target.value)} placeholder={t(S.call.placeholder)} maxLength={2000} />
          {sent && !sent.ok && <Banner kind="error">{sent.message}</Banner>}
          <div className="call-send"><BigButton type="submit" disabled={busy || !text.trim()}>{busy ? t(S.call.sending) : t(S.call.send)}</BigButton></div>
        </form>}
      <p className="fine-print">{t(S.call.privacy)}</p>
    </div>
  );
}
