import { useState } from "react";
import { Link } from "react-router-dom";
import { sendRequest, type Sent } from "../../data/intake";
import { apiMode } from "../../data/mode";
import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { Banner, BigButton } from "../../ui/components";
import "./intake.css";

/**
 * Ask for help (text). The caller, or a volunteer taking the call, writes what is happening in their own words.
 * The AI proposes facts for the desk; a person reviews them before anything reaches a team. The caller gets a
 * private status link straight away.
 */
export function CallPage() {
  const { t } = useLang();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState<Sent | null>(null);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setSent(await sendRequest(text));
    setBusy(false);
  };
  if (sent?.ok)
    return (
      <div className="page narrow intake">
        <h1>{t(S.call.received)}</h1>
        <p>{t(S.call.receivedBody(sent.reportId))}</p>
        <p>{t(S.call.keepLink)}</p>
        <Link className="status-link" to={sent.statusUrl + window.location.search}>
          {window.location.origin}
          {sent.statusUrl}
        </Link>
        <p className="fine-print">{t(S.call.emergency)}</p>
        <BigButton variant="secondary" onClick={() => (setSent(null), setText(""))}>
          {t(S.call.another)}
        </BigButton>
      </div>
    );
  return (
    <form className="page narrow intake" onSubmit={submit}>
      <h1>{t(S.call.title)}</h1>
      {!apiMode() && <Banner kind="info">{t(S.common.needsServer)}</Banner>}
      <label htmlFor="intake-text">{t(S.call.prompt)}</label>
      <textarea
        id="intake-text"
        rows={6}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={t(S.call.placeholder)}
        maxLength={2000}
      />
      {sent && !sent.ok && <Banner kind="error">{sent.message}</Banner>}
      <BigButton type="submit" disabled={busy || !text.trim()}>
        {busy ? t(S.call.sending) : t(S.call.send)}
      </BigButton>
      <p className="fine-print">{t(S.call.privacy)}</p>
    </form>
  );
}
