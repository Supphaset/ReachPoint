import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../../data/api";
import { callConfig, chooseCallLocation, confirmCall, pinCall, readCall, sendCallTurn, startCall, type CallConfig, type CallSession } from "../../data/call";
import type { LocationInput } from "../../data/contract";
import { CallerLocation } from "../location/CallerLocation";
import { sendRequest, type Sent } from "../../data/intake";
import { apiMode } from "../../data/mode";
import { useLang } from "../../i18n/lang";
import { S, seedText } from "../../i18n/strings";
import { callerPlace } from "../location/LocationChip";
import { Banner, BigButton } from "../../ui/components";
import { Icon } from "../../ui/Icon";
import { ProgressTracker } from "../../ui/ProgressTracker";
import { GeminiLiveVoice } from "./gemini-live";
import { CallCaseSidebar } from "./CallCaseSidebar";
import "./intake.css";

const SESSION_KEY = "reachpoint.call.session";

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

/**
 * Ask for help. The chat (typed, or spoken through Gemini Live) is the main way: the assistant asks only what is
 * missing, in the caller's language, and nothing is sent until they confirm the summary. The location card in the
 * chat lets them pin their spot (GPS, the map or an address) instead of describing it. The one-message form is the
 * fallback when the AI is unavailable; it works with the keyword stand-in.
 */
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
  const [location, setLocation] = useState<LocationInput>();
  const [locating, setLocating] = useState(false);
  const sheet = useRef<HTMLDialogElement>(null);
  const openSheet = () => sheet.current?.showModal();
  const closeSheet = () => sheet.current?.close();
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
        try { current = saved ? await readCall(saved) : await startCall(lang); }
        catch { current = await startCall(lang); }
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

  /** The location card in the chat: a located pin or address goes to the conversation, so it stops asking where. */
  const pinLocation = async (input?: LocationInput) => {
    if (!session) return;
    setError("");
    try {
      const next = await pinCall(session.sessionId, input ?? null);
      setSession(next);
      if (next.pinned?.status === "located") closeSheet(); // back to the chat once the spot is set
    }
    catch (cause) { setError(errorMessage(cause)); }
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
    setBusy(true);
    setSent(await sendRequest(text, location));
    setBusy(false);
  };

  const add = (line: string) => {
    setText((value) => value.trim() ? `${value.replace(/\s+$/, "")}\n${line}` : line);
    setFocusEnd((n) => n + 1);
  };

  const newConversation = async () => {
    if (session && !session.sent && session.messages.length > 1 && !window.confirm(t(S.call.conversation.restartConfirm))) return;
    stopVoice(); setError(""); setBusy(true);
    if (!config?.chat) { setSent(null); setText(""); setMode("form"); setBusy(false); return; }
    try {
      const current = await startCall(lang);
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
      <BigButton variant="secondary" onClick={() => { setLocation(undefined); void newConversation(); }}>{t(S.call.another)}</BigButton>
      <a className="call-danger" href="tel:1669"><Icon name="alert" size={20} /><span>{t(S.call.emergency)}</span><strong className="call-danger-cta">1669</strong></a>
    </div>
  );

  return (
    <div className={mode === "conversation" ? "call-page" : "page narrow intake"}>
      <div className="call-page-heading"><h1>{t(S.call.title)}</h1>
      <a className="call-danger" href="tel:1669"><Icon name="alert" size={20} /><span>{t(S.call.danger)}</span><strong className="call-danger-cta">1669</strong></a>
      </div>
      {!apiMode() && <Banner kind="info">{t(S.common.needsServer)}</Banner>}
      <div className="call-mode" role="tablist" aria-label={t(S.call.title)}>
        <button type="button" role="tab" aria-selected={mode === "conversation"} onClick={() => setMode("conversation")} disabled={!config?.chat}>{t(S.call.conversation.tab)}</button>
        <button type="button" role="tab" aria-selected={mode === "form"} onClick={() => setMode("form")}>{t(S.call.conversation.formTab)}</button>
      </div>
      {error && <Banner kind="error">{error}</Banner>}

      {mode === "conversation" && session ? <div className="call-workspace">
        <section className="call-chat-panel" aria-label={t(S.call.conversation.tab)}>
          <div className="call-chat-head">
            <p className="call-intro">{t(S.call.conversation.intro)}</p>
            {voiceState !== "off" && <p className="call-voice-status" role="status">
              <span className="call-voice-dot" aria-hidden="true" />
              {voiceState === "connecting" ? t(S.call.conversation.voiceConnecting) : t(S.call.conversation.voiceActive)}
              {heard && <span className="fine-print"> · {t(S.call.conversation.lastHeard)}: {heard}</span>}
            </p>}
          </div>
          <div className="call-chat-scroll">
            <div className="call-messages" role="log" aria-live="polite" aria-label={t(S.call.conversation.tab)}>
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
          {!session.sent && <div className="call-chat-location">
            {session.pinned?.status === "located" && session.pinned.landmarkLabel
              ? <div className="call-location-set"><Icon name="pin" size={18} /><span>{t(S.location.near(callerPlace(seedText(session.pinned.landmarkLabel, lang))))}</span>
                  <button type="button" className="btn btn-quiet btn-md" onClick={openSheet} aria-haspopup="dialog">{t(S.location.change)}</button></div>
              : <button type="button" className="btn btn-md call-location-cta" onClick={openSheet} aria-haspopup="dialog"><Icon name="pin" />{t(S.call.conversation.shareLocation)}</button>}
            <dialog ref={sheet} className="call-location-sheet" aria-labelledby="caller-location-title"
              onClick={(event) => { if (event.target === event.currentTarget) closeSheet(); }}>
              <CallerLocation key={session.sessionId} variant="sheet" onClose={closeSheet} onChange={pinLocation} onBusy={setLocating} />
            </dialog>
          </div>}
          <div className="call-composer">
            <form className={`call-reply ${config?.voice ? "has-voice" : ""}`} onSubmit={sendMessage}>
              {config?.voice && <button type="button" className={`btn btn-secondary call-voice-btn ${voiceState !== "off" ? "is-on" : ""}`}
                aria-pressed={voiceState !== "off"} onClick={voiceState === "off" ? startVoice : stopVoice}
                aria-label={voiceState === "off" ? t(S.call.conversation.voiceStart) : t(S.call.conversation.voiceStop)}
                title={voiceState === "off" ? t(S.call.conversation.voiceStart) : t(S.call.conversation.voiceStop)}><Icon name="mic" /></button>}
              <label className="visually-hidden" htmlFor="call-reply">{t(S.call.conversation.type)}</label>
              <textarea id="call-reply" rows={2} value={message} onChange={(event) => setMessage(event.target.value)} onKeyDown={onMessageKeyDown} maxLength={500} placeholder={t(S.call.conversation.placeholder)} />
              <BigButton type="submit" disabled={busy || locating || !message.trim()}>{busy ? t(S.call.sending) : t(S.call.conversation.send)}</BigButton>
            </form>
            <div className="call-composer-foot"><span className="fine-print">{t(S.call.conversation.enterHint)}</span><span className="call-composer-links"><button className="call-restart" type="button" onClick={() => setMode("form")}>{t(S.call.conversation.formLink)}</button><button className="call-restart" type="button" onClick={newConversation} disabled={busy}>{t(S.call.conversation.restart)}</button></span></div>
          </div>
        </section>
        <CallCaseSidebar session={session} busy={busy} onConfirm={confirm} />
      </div> : mode === "conversation" ? <p>{t(S.call.conversation.unavailable)}</p> :
        <form className="intake" onSubmit={sendForm}>
          <CallerLocation onChange={setLocation} onBusy={setLocating} />
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
          <div className="call-send"><BigButton type="submit" disabled={busy || locating || !text.trim()}>{busy ? t(S.call.sending) : t(S.call.send)}</BigButton></div>
        </form>}
      <p className={`fine-print ${mode === "conversation" ? "call-privacy" : ""}`}>{t(S.call.privacy)}</p>
    </div>
  );
}
