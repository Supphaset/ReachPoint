import { useState } from "react";
import { Link } from "react-router-dom";
import { sendRequest, type Sent } from "../../data/intake";
import { apiMode } from "../../data/mode";
import { Banner, BigButton } from "../../ui/components";
import "./intake.css";

/**
 * Ask for help (text). The caller, or a volunteer taking the call, writes what is happening in their own words.
 * The AI proposes facts for the desk; a person reviews them before anything reaches a team. The caller gets a
 * private status link straight away.
 */
export function CallPage() {
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
        <h1>We received your request</h1>
        <p>
          Request <strong className="num">{sent.reportId}</strong>. A coordinator is reading it now. Nothing is promised until a team takes it.
        </p>
        <p>Keep this link to see what is happening with your request:</p>
        <Link className="status-link" to={sent.statusUrl}>
          {window.location.origin}
          {sent.statusUrl}
        </Link>
        <p className="fine-print">If it becomes an emergency, call 1669.</p>
        <BigButton variant="secondary" onClick={() => (setSent(null), setText(""))}>
          Send another request
        </BigButton>
      </div>
    );
  return (
    <form className="page narrow intake" onSubmit={submit}>
      <h1>
        ขอความช่วยเหลือ <span className="muted">· Ask for help</span>
      </h1>
      {!apiMode() && <Banner kind="info">This screen needs the server. Open the app with ?data=api.</Banner>}
      <label htmlFor="intake-text">
        What is happening, where, and who is with you? Thai or English.
      </label>
      <textarea
        id="intake-text"
        rows={6}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="เช่น บ้านอยู่แถวโรงเรียน B-4 น้ำถึงอกแล้ว มีผู้ใหญ่ 2 คน ยายติดเตียงเดินไม่ได้"
        maxLength={2000}
      />
      {sent && !sent.ok && <Banner kind="error">{sent.message}</Banner>}
      <BigButton type="submit" disabled={busy || !text.trim()}>
        {busy ? "Sending…" : "Send request"}
      </BigButton>
      <p className="fine-print">Synthetic demo: don't enter real names, phone numbers or addresses. An AI reads your words to help the coordinator; a person checks everything.</p>
    </form>
  );
}
