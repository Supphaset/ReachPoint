import { useState } from "react";
import { useParams } from "react-router-dom";
import type { ReceiptResponse, ResidentStatusView } from "../../data/contract";
import { post, submissionId } from "../../data/api";
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

/** Four caller-facing steps; a team's completion report is still awaiting receipt confirmation. */
function trackingStep(state: string): number | null {
  if (state === "receipt_confirmed" || state === "done") return 3;
  const step = statusStep(state);
  return step === null ? null : Math.min(step, 2);
}

/** Only this request. Demo controls change local presentation, never operational state. */
export function StatusPage() {
  const { token = "" } = useParams();
  const { t, pick, lang } = useLang();
  const [preview, setPreview] = useState<{ token: string; step: number; receipt?: ReceiptResponse } | null>(null);
  const [localReceipt, setLocalReceipt] = useState<{ token: string; value: ReceiptResponse } | null>(null);
  const [savingReceipt, setSavingReceipt] = useState(false);
  const [receiptError, setReceiptError] = useState("");
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");
  const v = useView<ResidentStatusView>(apiMode() ? `status/${token}` : null);
  const demoStep = preview?.token === token ? preview.step : null;
  const trackingUrl = new URL(`/status/${encodeURIComponent(token)}`, window.location.origin);
  trackingUrl.searchParams.set("data", "api");
  trackingUrl.searchParams.set("lang", lang);
  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(trackingUrl.href);
      setCopyState("copied");
    } catch { setCopyState("failed"); }
  };

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
  const receipt = demoStep !== null ? preview?.receipt : localReceipt?.token === token ? localReceipt.value : s.receipt;
  const confirmed = receipt?.answer === "yes";
  const liveStep = confirmed && demoStep === null ? 3 : trackingStep(s.lines[0]?.state ?? s.state) ?? 0;
  const shownStep = demoStep ?? liveStep;
  const demoBase = Date.parse(s.completedAt?.[0] ?? s.generatedAt);
  const completedAt = demoStep === null ? [...(s.completedAt ?? [null, null, null, null])] : [
    ...[0, 5, 20].map((minutes, index) => demoStep >= (index === 2 ? 3 : index) ? new Date(demoBase + minutes * 60_000).toISOString() : null), null,
  ];
  completedAt[3] = confirmed ? receipt.at : null;
  const answerReceipt = async (answer: "yes" | "no") => {
    setReceiptError("");
    if (demoStep !== null) {
      setPreview({ token, step: demoStep, receipt: { answer, at: new Date(demoBase + 30 * 60_000).toISOString() } });
      return;
    }
    setSavingReceipt(true);
    try {
      const response = await post<ReceiptResponse>(`/api/status/${token}/receipt`, { answer, submissionId: submissionId() });
      setLocalReceipt({ token, value: response });
    } catch (error) { setReceiptError(error instanceof Error ? error.message : "Could not save your answer."); }
    finally { setSavingReceipt(false); }
  };
  const lines = demoStep === null ? s.lines : [{ state: "demo", text: t(S.status.demoMessages[demoStep]) }];
  return (
    <div className="page narrow status-page">
      <h1>{t(S.status.title)}</h1>
      <p className="muted">
        <span className="num">{t(S.status.request(s.reportId))}</span>
        {s.caseId ? ` · ${t(S.status.case(s.caseId))}` : ""}
      </p>
      <section className="tracking-link-card" aria-label={t(S.status.copyLink)}>
        <button className="btn btn-primary btn-lg tracking-copy" type="button" onClick={copyLink}>
          <Icon name={copyState === "copied" ? "check" : "copy"} size={24} />
          <span>{t(copyState === "copied" ? S.status.copiedLink : S.status.copyLink)}</span>
        </button>
        <p role="status">{t(copyState === "failed" ? S.status.copyFailed : copyState === "copied" ? S.status.copiedLink : S.status.linkHint)}</p>
        {copyState === "failed" && <input readOnly aria-label={t(S.status.copyLink)} value={trackingUrl.href} onFocus={(event) => event.currentTarget.select()} />}
      </section>
      {demoStep === null ? <LastUpdated at={s.generatedAt} offline={v.connection === "offline"} /> : <Banner kind="info">{t(S.status.demoActive)} · {demoStep + 1}/4</Banner>}
      <p className="tracking-time-label">{t(S.status.stepTimes)}{demoStep !== null ? (lang === "th" ? " · เวลาตัวอย่าง" : " · example times") : ""}</p>
      {lines.map((l, i) => {
        const step = confirmed ? 3 : demoStep ?? trackingStep(l.state);
        const held = demoStep === null && l.state === "held";
        const exceptional = demoStep === null && ["already_left", "not_found", "needs_more_help"].includes(l.state);
        return (
          <section className="family-status" key={i}>
            <div className={`family-status-card ${held || exceptional ? "is-held" : step === null ? "is-unknown" : step === 3 && confirmed ? "is-done" : step === 2 ? "is-moving" : ""}`}>
              <div className="family-status-label">
                <Icon name={held ? "pause" : exceptional ? "alert" : step === null ? "question" : step === 3 ? confirmed ? "check" : "question" : "hand"} />
                <strong>{l.family ? pick(l.family, l.familyTh) : t(S.status.request(s.reportId))}</strong>
                {held && <span>{t(S.progress.held)}</span>}
                {step === null && l.state !== "closed" && <span>{t(S.progress.unknown)}</span>}
              </div>
              <p>{step === 3 ? t(confirmed ? S.status.receiptConfirmed : receipt?.answer === "no" ? S.status.receiptNotReceived : S.status.pendingReceipt) : pick(l.text, l.th)}</p>
            </div>
            <ProgressTracker steps={S.status.steps} current={step} tone={step === 3 && confirmed ? "done" : step === 2 ? "moving" : "waiting"} completedAt={completedAt} label={S.progress.familyLabel} />
          </section>
        );
      })}
      {shownStep === 3 && <section className="tracking-receipt" aria-labelledby="receipt-question">
        <h2 id="receipt-question">{t(S.status.receiptQuestion)}</h2>
        <div className="tracking-receipt-actions">
          <button className="btn btn-primary btn-lg" type="button" disabled={savingReceipt} aria-pressed={receipt?.answer === "yes"} onClick={() => answerReceipt("yes")}>{t(S.status.receiptYes)}</button>
          <button className="btn btn-secondary btn-lg" type="button" disabled={savingReceipt} aria-pressed={receipt?.answer === "no"} onClick={() => answerReceipt("no")}>{t(S.status.receiptNo)}</button>
        </div>
        {savingReceipt && <p role="status">{t(S.status.receiptSaving)}</p>}
        {receipt && <p role="status">{t(confirmed ? S.status.receiptConfirmed : S.status.receiptNotReceived)}</p>}
        {receiptError && <Banner kind="error">{receiptError}</Banner>}
      </section>}
      <section className="tracking-demo" aria-label={t(S.status.demoTitle)}>
        <strong>{t(S.status.demoTitle)}</strong>
        <p>{t(S.status.demoHint)}</p>
        <button className="btn btn-secondary btn-md" type="button" disabled={savingReceipt || shownStep === 3} onClick={() => setPreview({ token, step: Math.min(shownStep + 1, 3) })}>
          {t(S.status.nextStep)} <Icon name="chevron" />
        </button>
        <div className="tracking-demo-actions">
          <button className="btn btn-quiet btn-md" type="button" disabled={savingReceipt} onClick={() => setPreview({ token, step: 0 })}>{t(S.status.resetDemo)}</button>
          {demoStep !== null && <button className="btn btn-quiet btn-md" type="button" disabled={savingReceipt} onClick={() => setPreview(null)}>{t(S.status.actualStatus)}</button>}
        </div>
      </section>
      <p className="fine-print">{t(S.status.footer)}</p>
    </div>
  );
}
