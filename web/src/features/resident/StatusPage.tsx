import { useParams } from "react-router-dom";
import type { ResidentStatusView } from "../../data/contract";
import { apiMode } from "../../data/mode";
import { useView } from "../../data/useView";
import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { Banner, LastUpdated, Skeleton } from "../../ui/components";
import { ProgressTracker } from "../../ui/ProgressTracker";
import { statusStep } from "../../ui/progress";
import { Icon } from "../../ui/Icon";
import "../intake/intake.css";

/** The family's own status (D6, 8A): only their request, honest wording, refreshed while open. */
export function StatusPage() {
  const { token = "" } = useParams();
  const { t, pick } = useLang();
  const v = useView<ResidentStatusView>(apiMode() ? `status/${token}` : null);
  if (!apiMode())
    return (
      <div className="page narrow status-page">
        <h1>{t(S.status.title)}</h1>
        <Banner kind="info">{t(S.status.needsServer)}</Banner>
        <p className="fine-print">{t(S.status.footer)}</p>
      </div>
    );
  if (v.status === "loading") return <div className="page narrow status-page"><Skeleton lines={3} /><p className="fine-print">{t(S.status.footer)}</p></div>;
  if (v.status === "missing")
    return (
      <div className="page narrow status-page">
        <h1>{t(S.status.title)}</h1>
        <Banner kind="info">{t(S.status.notFound)}</Banner>
        <p className="fine-print">{t(S.status.footer)}</p>
      </div>
    );
  if (v.status === "error") return <div className="page narrow status-page"><Banner kind="error">{t(S.status.unavailable)} {v.message}</Banner><p className="fine-print">{t(S.status.footer)}</p></div>;
  const s = v.data;
  return (
    <div className="page narrow status-page">
      <h1>{t(S.status.title)}</h1>
      <p className="muted">
        <span className="num">{t(S.status.request(s.reportId))}</span>
        {s.caseId ? ` · ${t(S.status.case(s.caseId))}` : ""}
      </p>
      <LastUpdated at={s.generatedAt} offline={v.connection === "offline"} />
      {s.lines.map((l, i) => {
        const step = statusStep(l.state);
        const held = l.state === "held";
        const exceptional = ["already_left", "not_found", "needs_more_help"].includes(l.state);
        return (
          <section className="family-status" key={i}>
            <div className={`family-status-card ${held || exceptional ? "is-held" : step === null ? "is-unknown" : step === 4 ? "is-done" : step === 3 ? "is-moving" : step === 2 ? "is-taken" : ""}`}>
              <div className="family-status-label">
                <Icon name={held ? "pause" : exceptional ? "alert" : step === null ? "question" : step === 4 ? "check" : "hand"} />
                <strong>{l.family ? pick(l.family, l.familyTh) : t(S.status.request(s.reportId))}</strong>
                {held && <span>{t(S.progress.held)}</span>}
                {step === null && l.state !== "closed" && <span>{t(S.progress.unknown)}</span>}
              </div>
              <p>{pick(l.text, l.th)}</p>
            </div>
            <ProgressTracker steps={S.progress.family} current={step} held={held} label={S.progress.familyLabel} />
          </section>
        );
      })}
      <p className="fine-print">{t(S.status.footer)}</p>
    </div>
  );
}
