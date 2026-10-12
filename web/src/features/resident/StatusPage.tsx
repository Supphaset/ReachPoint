import { useParams } from "react-router-dom";
import type { ResidentStatusView } from "../../data/contract";
import { apiMode } from "../../data/mode";
import { useView } from "../../data/useView";
import { Banner, LastUpdated, Skeleton } from "../../ui/components";
import "../intake/intake.css";

/** The family's own status (D6, 8A): only their request, honest wording, refreshed while open. */
export function StatusPage() {
  const { token = "" } = useParams();
  const v = useView<ResidentStatusView>(apiMode() ? `status/${token}` : null);
  if (!apiMode())
    return (
      <div className="page narrow">
        <h1>Your request</h1>
        <Banner kind="info">Status links need the server. Open the app with ?data=api, then send a request from Ask for help.</Banner>
      </div>
    );
  if (v.status === "loading") return <div className="page narrow"><Skeleton lines={3} /></div>;
  if (v.status === "missing")
    return (
      <div className="page narrow">
        <h1>Your request</h1>
        <Banner kind="info">We can't find this link. Check you copied all of it, or call again.</Banner>
      </div>
    );
  if (v.status === "error") return <div className="page narrow"><Banner kind="error">Status unavailable. {v.message}</Banner></div>;
  const s = v.data;
  return (
    <div className="page narrow">
      <h1>
        สถานะคำขอ <span className="muted">· Your request</span>
      </h1>
      <p className="muted">
        Request <span className="num">{s.reportId}</span>
        {s.caseId ? ` · case ${s.caseId}` : ""}
      </p>
      <LastUpdated at={s.generatedAt} offline={v.connection === "offline"} />
      <ul className="status-lines">
        {s.lines.map((l, i) => (
          <li key={i}>
            {l.family && <strong>{l.family}: </strong>}
            {l.text}
          </li>
        ))}
      </ul>
      <p className="fine-print">A team's time is their estimate, not a promise. If it becomes an emergency, call 1669.</p>
    </div>
  );
}
