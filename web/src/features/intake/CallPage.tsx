import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { sendRequest, type Sent } from "../../data/intake";
import { apiMode } from "../../data/mode";
import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { Banner, BigButton } from "../../ui/components";
import { Icon } from "../../ui/Icon";
import { ProgressTracker } from "../../ui/ProgressTracker";
import "./intake.css";

/**
 * Ask for help (text). The caller, or a volunteer taking the call, writes what is happening in their own words.
 * Hint chips add a labelled line (where, water, who, can't walk) so callers give teams what they need; the words
 * stay the caller's own. The AI proposes facts for the desk; a person reviews them before anything reaches a team.
 */
export function CallPage() {
  const { t } = useLang();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState<Sent | null>(null);
  const box = useRef<HTMLTextAreaElement>(null);
  const [focusEnd, setFocusEnd] = useState(0);
  useEffect(() => {
    // After a hint line is added, put the caret at the end so the caller can type straight after the label.
    const el = box.current;
    if (!focusEnd || !el) return;
    el.focus();
    el.setSelectionRange(el.value.length, el.value.length);
  }, [focusEnd]);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setSent(await sendRequest(text));
    setBusy(false);
  };
  const add = (line: string) => {
    setText((v) => (v.trim() ? `${v.replace(/\s+$/, "")}\n${line}` : line));
    setFocusEnd((n) => n + 1);
  };
  if (sent?.ok)
    return (
      <div className="page narrow intake">
        <h1>{t(S.call.received)}</h1>
        <p>{t(S.call.receivedBody(sent.reportId))}</p>
        <ProgressTracker steps={S.progress.family} current={0} label={S.progress.familyLabel} />
        <Link className="btn btn-primary btn-lg status-open" to={sent.statusUrl + window.location.search}>
          {t(S.call.openStatus)}
        </Link>
        <p className="fine-print">{t(S.call.keepLink)}</p>
        <Link className="status-link" to={sent.statusUrl + window.location.search}>
          {window.location.origin}
          {sent.statusUrl}
        </Link>
        <BigButton variant="secondary" onClick={() => (setSent(null), setText(""))}>
          {t(S.call.another)}
        </BigButton>
        <p className="fine-print">{t(S.call.emergency)}</p>
      </div>
    );
  return (
    <form className="page narrow intake" onSubmit={submit}>
      <h1>{t(S.call.title)}</h1>
      <p className="call-danger" role="note">
        <Icon name="alert" size={20} />
        <span>{t(S.call.danger)}</span>
      </p>
      {!apiMode() && <Banner kind="info">{t(S.common.needsServer)}</Banner>}
      <label htmlFor="intake-text">{t(S.call.prompt)}</label>
      <div className="call-hints" role="group" aria-label={t(S.call.helpTitle)}>
        <span className="fine-print">{t(S.call.helpTitle)}</span>
        <div className="call-hint-row">
          {S.call.hints.map((h) => {
            const done = text.includes(t(h.line).trim());
            return (
              <button key={h.key} type="button" className={`call-hint ${done ? "is-done" : ""}`} onClick={() => add(t(h.line))} aria-pressed={done}>
                <Icon name={done ? "check" : "chevron"} size={16} />
                <span>{t(h.label)}</span>
                {done && <span className="visually-hidden">{t(S.call.added)}</span>}
              </button>
            );
          })}
        </div>
      </div>
      <textarea
        id="intake-text"
        ref={box}
        rows={7}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={t(S.call.placeholder)}
        maxLength={2000}
      />
      {sent && !sent.ok && <Banner kind="error">{sent.message}</Banner>}
      <div className="call-send">
        <BigButton type="submit" disabled={busy || !text.trim()}>
          {busy ? t(S.call.sending) : t(S.call.send)}
        </BigButton>
      </div>
      <p className="fine-print">{t(S.call.privacy)}</p>
    </form>
  );
}
