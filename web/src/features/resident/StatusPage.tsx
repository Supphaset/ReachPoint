import { useState } from "react";
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
import "./status.css";
import { shareStatusLink } from "./shareStatusLink";

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
        <StatusFooter />
      </div>
    );
  if (v.status === "loading") return <div className="page narrow status-page"><Skeleton lines={3} /><StatusFooter /></div>;
  if (v.status === "missing")
    return (
      <div className="page narrow status-page">
        <h1>{t(S.status.title)}</h1>
        <Banner kind="info">{t(S.status.notFound)}</Banner>
        <StatusFooter />
      </div>
    );
  if (v.status === "error") return <div className="page narrow status-page"><Banner kind="error">{t(S.status.unavailable)} {v.message}</Banner><StatusFooter /></div>;
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
      <ShareStatusLink reportId={s.reportId} />
      <StatusFooter />
    </div>
  );
}


function StatusFooter() {
  const { t } = useLang();
  return <footer className="status-footer">
    <p className="fine-print">{t(S.status.footer)}</p>
    <a className="btn btn-secondary btn-md status-call" href="tel:1669">{t(S.status.call1669)}</a>
  </footer>;
}

export function ShareStatusLink({ reportId }: { reportId: string }) {
  const { t } = useLang();
  const [result, setResult] = useState<"copied" | "failed" | null>(null);
  const [busy, setBusy] = useState(false);
  const share = async () => {
    setBusy(true); setResult(null);
    try {
      const outcome = await shareStatusLink(navigator, window.location.href, t(S.status.shareMessage(reportId)));
      if (outcome === "copied") setResult("copied");
    } catch { setResult("failed"); }
    finally { setBusy(false); }
  };
  return <div className="status-share">
    <button type="button" className="btn btn-primary btn-md" disabled={busy} onClick={() => void share()}>{t(S.status.share)}</button>
    <p role="status" aria-live="polite">{result === "copied" ? t(S.status.copied) : result === "failed" ? t(S.status.shareFailed) : ""}</p>
  </div>;
}
