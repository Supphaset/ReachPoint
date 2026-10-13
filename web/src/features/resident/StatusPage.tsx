import { useParams } from "react-router-dom";
import type { ResidentStatusView } from "../../data/contract";
import { apiMode } from "../../data/mode";
import { useView } from "../../data/useView";
import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { Banner, LastUpdated, Skeleton } from "../../ui/components";
import "../intake/intake.css";

/** The family's own status (D6, 8A): only their request, honest wording, refreshed while open. */
export function StatusPage() {
  const { token = "" } = useParams();
  const { t, pick } = useLang();
  const v = useView<ResidentStatusView>(apiMode() ? `status/${token}` : null);
  if (!apiMode())
    return (
      <div className="page narrow">
        <h1>{t(S.status.title)}</h1>
        <Banner kind="info">{t(S.status.needsServer)}</Banner>
      </div>
    );
  if (v.status === "loading") return <div className="page narrow"><Skeleton lines={3} /></div>;
  if (v.status === "missing")
    return (
      <div className="page narrow">
        <h1>{t(S.status.title)}</h1>
        <Banner kind="info">{t(S.status.notFound)}</Banner>
      </div>
    );
  if (v.status === "error") return <div className="page narrow"><Banner kind="error">{t(S.status.unavailable)} {v.message}</Banner></div>;
  const s = v.data;
  return (
    <div className="page narrow">
      <h1>{t(S.status.title)}</h1>
      <p className="muted">
        <span className="num">{t(S.status.request(s.reportId))}</span>
        {s.caseId ? ` · ${t(S.status.case(s.caseId))}` : ""}
      </p>
      <LastUpdated at={s.generatedAt} offline={v.connection === "offline"} />
      <ul className="status-lines">
        {s.lines.map((l, i) => (
          <li key={i}>
            {l.family && <strong>{pick(l.family, l.familyTh)}: </strong>}
            {pick(l.text, l.th)}
          </li>
        ))}
      </ul>
      <p className="fine-print">{t(S.status.footer)}</p>
    </div>
  );
}
