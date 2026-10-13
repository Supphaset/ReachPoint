import { useState } from "react";
import { post, submissionId } from "../../data/api";
import { apiMode } from "../../data/mode";
import { demoRoom, newRoomCode, roomLink } from "../../data/room";
import { LangSwitch, useLang, type Pair } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { Wordmark } from "../../shell/AppShell";
import { Banner } from "../../ui/components";
import "./demo.css";

/** One screen of the real app inside a device frame; each keeps its own language and refreshes every 2 s. */
function Screen({ name, src, wide, k }: { name: Pair; src: string; wide?: boolean; k: number }) {
  const { t } = useLang();
  return (
    <figure className={`demo-screen ${wide ? "is-wide" : "is-phone"}`}>
      <figcaption>{t(name)}</figcaption>
      <div className="demo-frame">
        <iframe key={k} src={src} title={t(name)} />
      </div>
    </figure>
  );
}

const q = (path: string, lang: "th" | "en", as: string, room: string) =>
  `${path}?data=api&refresh=2&lang=${lang}&as=${encodeURIComponent(as)}&room=${encodeURIComponent(room)}`;

/** /demo: victim and volunteer phones side by side, with the coordinator's approval between them. */
export function DemoPage() {
  const { t, lang } = useLang();
  const [k, setK] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const [copied, setCopied] = useState(false);
  const [room, setRoom] = useState(() => demoRoom());
  const [linkCopied, setLinkCopied] = useState(false);
  const fresh = () => {
    const code = newRoomCode();
    const url = new URL(window.location.href);
    url.searchParams.set("room", code);
    window.history.replaceState(null, "", url);
    setRoom(demoRoom(url.search));
    setK((n) => n + 1);
  };
  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(roomLink("/demo", room));
      setLinkCopied(true);
      window.setTimeout(() => setLinkCopied(false), 1500);
    } catch {
      /* clipboard refused: the code is on screen */
    }
  };
  const reset = async () => {
    if (!window.confirm(t(S.demo.resetConfirm))) return;
    setBusy(true);
    setError(false);
    try {
      await post("/api/demo/reset", { submissionId: submissionId() });
      setK((n) => n + 1);
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  };
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(t(S.demo.sampleText));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard refused: the text is selectable */
    }
  };
  return (
    <div className="demo">
      <header className="demo-head">
        <Wordmark />
        <h1>{t(S.demo.title)}</h1>
        <div className="demo-actions">
          <LangSwitch />
          <button type="button" className="btn btn-quiet btn-md" onClick={() => setK((n) => n + 1)}>
            {t(S.demo.reload)}
          </button>
          <button type="button" className="btn btn-secondary btn-md" onClick={reset} disabled={busy || !apiMode()}>
            {busy ? t(S.demo.resetting) : t(S.demo.reset)}
          </button>
        </div>
      </header>
      {!apiMode() && <Banner kind="info">{t(S.demo.needsServer)}</Banner>}
      {error && <Banner kind="error">{t(S.demo.resetFailed)}</Banner>}
      <p className="demo-lead">{t(S.demo.lead)}</p>
      {apiMode() && (
        <div className="demo-room">
          <strong>{t(S.demo.room(room))}</strong>
          <span className="muted">{t(S.demo.roomNote)}</span>
          <span className="demo-room-actions">
            <button type="button" className="btn btn-quiet btn-md" onClick={copyLink}>
              {linkCopied ? t(S.demo.copied) : t(S.demo.copyLink)}
            </button>
            <button type="button" className="btn btn-quiet btn-md" onClick={fresh}>
              {t(S.demo.newRoom)}
            </button>
          </span>
        </div>
      )}
      <ol className="demo-steps">
        {S.demo.steps.map((s, i) => (
          <li key={i}><span className="demo-step-number" aria-hidden="true">{i + 1}</span><span>{t(s)}</span></li>
        ))}
      </ol>
      <div className="demo-sample">
        <span className="muted">{t(S.demo.sample)}</span>
        <code lang="th">{t(S.demo.sampleText)}</code>
        <button type="button" className="btn btn-quiet btn-md" onClick={copy}>
          {copied ? t(S.demo.copied) : t(S.demo.copy)}
        </button>
      </div>
      {apiMode() && (
        <div className="demo-stage">
          <Screen k={k} name={S.demo.victim} src={q("/call", lang, "resident:demo", room)} />
          <Screen k={k} name={S.demo.desk} src={q("/desk", lang, "coordinator:demo-1", room)} wide />
          <Screen k={k} name={S.demo.volunteer} src={q("/team/list", lang, "team:T-S", room)} />
        </div>
      )}
    </div>
  );
}
