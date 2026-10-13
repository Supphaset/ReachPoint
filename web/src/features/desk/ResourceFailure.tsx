import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { useState } from "react";
import { ApiError, post, submissionId } from "../../data/api";
import { apiMode } from "../../data/mode";
import { loadTeam } from "../../data/teamStore";
import { fmtTime } from "../../data/format";
import { Banner, BigButton } from "../../ui/components";

/** Coordinator review, not a team report: one write holds jobs and withdraws their estimates. */
export function ResourceFailure() {
  const { t: tr } = useLang();
  const [reason, setReason] = useState("Boat engine trouble");
  const [next, setNext] = useState("2026-10-11T11:00");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [alreadyUnavailable, setAlreadyUnavailable] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Keep this ID on network failure: the server may already have committed the review.
  const [id] = useState(submissionId);
  const [attempt, setAttempt] = useState<{ reason: string; nextStatusUpdate: string } | null>(null);
  const review = async () => {
    const body = attempt ?? { reason, nextStatusUpdate: new Date(`${next}:00+07:00`).toISOString() };
    setAttempt(body);
    setBusy(true);
    setError(null);
    try {
      const r = await post<{ value: { alreadyUnavailable?: boolean } }>("/api/resources/S1/unavailable", { ...body, submissionId: id });
      setAlreadyUnavailable(!!r.value.alreadyUnavailable);
      setDone(true);
      void loadTeam("T-S");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : tr(S.desk.saveError));
      if (e instanceof ApiError && e.status > 0) setAttempt(null);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="rising" aria-label={tr(S.desk.boatTitle)}>
      <h2>{tr(S.desk.boatTitle)}</h2>
      <p>{tr(S.desk.boatBody)}</p>
      {done ? (
        <Banner kind="info">
          {alreadyUnavailable ? tr(S.desk.boatAlready) :
            tr(S.desk.boatDone(fmtTime(attempt!.nextStatusUpdate)))}
        </Banner>
      ) : (
        <>
          <label>{tr(S.desk.reason)}<input value={reason} disabled={busy || !!attempt} onChange={(e) => setReason(e.target.value)} /></label>
          <label>{tr(S.desk.nextUpdate)}<input type="datetime-local" value={next} disabled={busy || !!attempt} onChange={(e) => setNext(e.target.value)} /></label>
          {error && <Banner kind="error">{error}</Banner>}
          {!apiMode() && <p className="fine-print">{tr(S.desk.boatServer)}</p>}
          <BigButton size="md" disabled={!apiMode() || busy || !reason.trim() || !next} onClick={review}>
            {busy ? tr(S.desk.saving) : attempt ? tr(S.desk.retryBoat) : tr(S.desk.markBoat)}
          </BigButton>
        </>
      )}
    </section>
  );
}
