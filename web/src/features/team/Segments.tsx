import { useState } from "react";
import type { SegmentJob, SegmentRow, TeamMissionsView } from "../../data/contract";
import { fmtRange, fmtTime } from "../../data/format";
import { markSegment, sendFieldReport, takeSegment } from "../../data/teamStore";
import { Banner, BigButton, StatusChip } from "../../ui/components";
import { useLang, type Lang } from "../../i18n/lang";
import { S, seedText } from "../../i18n/strings";
import "./segments.css";

function markText(m: NonNullable<SegmentRow["mark"]>, lang: Lang) {
  if (m.state === "could_not_reach") return S.segments.couldNotLine(fmtTime(m.at), m.teamId, m.reason ?? "")[lang];
  const label = (m.state === "checked" ? S.segments.checked : S.segments.partly)[lang];
  return S.segments.markLine(label, fmtTime(m.at), m.teamId, m.householdsFound ?? 0, m.pickupsNeeded ?? 0)[lang];
}

function Facts({ s }: { s: Pick<SegmentRow, "registerCount" | "estimate" | "families"> }) {
  const { t } = useLang();
  return <p className="seg-facts">{t(S.segments.facts(fmtRange(s.estimate.everyone), s.registerCount ?? 0, s.families.length))}</p>;
}

/** Waiting list: published zone missions, one row per segment; a team takes one segment at a time. */
export function ZoneMissions({ v, offline }: { v: TeamMissionsView; offline: boolean }) {
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const { t, lang } = useLang();
  if (!v.zoneMissions?.length) return null;
  const mine = (v.segmentJobs ?? []).some((j) => j.state === "taken");
  const take = async (id: string) => {
    setBusy(id);
    const r = await takeSegment(id);
    setBusy(null);
    setMsg(r.ok ? null : r.message);
  };
  return (
    <section className="zone-missions" aria-label={t(S.segments.zoneMissions)}>
      <h2>{t(S.segments.zoneMissions)}</h2>
      <p className="muted">{t(S.segments.intro)}</p>
      {msg && <Banner kind="error">{msg}</Banner>}
      {v.zoneMissions.map((m) => (
        <article key={m.missionId} className="mission">
          <h3>
            {t(S.segments.zone(m.zoneId))} <span className="muted">· {t(S.segments.published(fmtTime(m.publishedAt)))}</span>
          </h3>
          {m.reasons.length > 0 && <p className="fine-print">{m.reasons.join(" · ")}</p>}
          <ul className="seg-list">
            {m.segments.map((s) => (
              <li key={s.segmentId} className="seg-row">
                <div className="seg-top">
                  <strong>{seedText(s.label, lang)}</strong>
                  <StatusChip kind="segment" state={s.state} lang={lang} size="sm" />
                </div>
                {s.state === "taken" && <p className="fine-print">{t(S.segments.takenBy(s.takenBy ?? ""))}</p>}
                {s.mark && s.state !== "taken" && <p className="fine-print">{markText(s.mark, lang)}</p>}
                <Facts s={s} />
                {s.state === "open" || s.state === "could_not_reach" || s.state === "partly_checked" ? (
                  <BigButton size="md" variant="secondary" onClick={() => take(s.segmentId)} disabled={offline || mine || busy !== null}>
                    {busy === s.segmentId ? t(S.segments.taking) : mine ? t(S.segments.finishFirst) : t(S.segments.take)}
                  </BigButton>
                ) : null}
              </li>
            ))}
          </ul>
        </article>
      ))}
    </section>
  );
}

/** My jobs: the segment the team holds, with the field report and the mark. */
export function SegmentJobs({ v }: { v: TeamMissionsView }) {
  const jobs = v.segmentJobs ?? [];
  const { t } = useLang();
  if (!jobs.length) return null;
  return (
    <section className="seg-jobs" aria-label={t(S.segments.mySegments)}>
      <h2>{t(S.segments.mySegments)}</h2>
      {jobs.map((j) => <SegmentJobCard key={j.claimId} j={j} />)}
    </section>
  );
}

function SegmentJobCard({ j }: { j: SegmentJob }) {
  const [text, setText] = useState("");
  const [sent, setSent] = useState<string | null>(null);
  const [state, setState] = useState<"checked" | "partly_checked" | "could_not_reach">("checked");
  const [found, setFound] = useState(0);
  const [pickups, setPickups] = useState(0);
  const [reason, setReason] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const id = (s: string) => `${j.claimId}-${s}`;
  const { t, lang } = useLang();
  const report = async () => {
    setBusy(true);
    const r = await sendFieldReport(j.segmentId, text);
    setBusy(false);
    if (!r.ok) return setMsg(r.message);
    setSent(r.value.reportId);
    setText("");
  };
  const mark = async () => {
    setBusy(true);
    const r = await markSegment(j.claimId, state, state === "could_not_reach" ? null : found, state === "could_not_reach" ? null : pickups, state === "could_not_reach" ? reason : null);
    setBusy(false);
    setMsg(r.ok ? null : r.message);
  };
  return (
    <article className="seg-job">
      <div className="seg-top">
        <strong>{seedText(j.label, lang)}</strong>
        <StatusChip kind="segment" state={j.state === "taken" ? "taken" : (j.mark?.state ?? "checked")} lang={lang} size="sm" />
      </div>
      <p className="fine-print">{t(S.segments.taken(fmtTime(j.takenAt)))}{j.mark ? ` · ${markText(j.mark, lang)}` : ""}</p>
      <Facts s={j} />
      {j.families.length > 0 && (
        <p className="fine-print">{t(S.segments.reviewedHere(j.families.map((f) => `${f.caseId} (${f.people})`).join(", ")))}</p>
      )}
      {msg && <Banner kind="error">{msg}</Banner>}
      {j.state === "taken" && (
        <>
          <label htmlFor={id("report")} className="seg-label">
            {t(S.segments.foundPeople)}
          </label>
          <textarea id={id("report")} rows={3} value={text} onChange={(e) => setText(e.target.value)} placeholder={t(S.segments.reportPlaceholder)} />
          {sent && <p className="fine-print">{t(S.segments.sentAs(sent))}</p>}
          <BigButton size="md" variant="secondary" onClick={report} disabled={busy || !text.trim()}>{t(S.segments.sendReport)}</BigButton>

          <fieldset className="seg-mark">
            <legend>{t(S.segments.markLegend)}</legend>
            {([["checked", S.segments.checked], ["partly_checked", S.segments.partly], ["could_not_reach", S.segments.couldNotReach]] as const).map(([k, l]) => (
              <label key={k} className="inline" htmlFor={id(k)}>
                <input id={id(k)} type="radio" name={id("state")} checked={state === k} onChange={() => setState(k)} /> {t(l)}
              </label>
            ))}
            {state === "could_not_reach" ? (
              <label htmlFor={id("why")}>
                {t(S.segments.whyQ)}
                <input id={id("why")} value={reason} onChange={(e) => setReason(e.target.value)} placeholder={t(S.segments.whyPlaceholder)} />
              </label>
            ) : (
              <div className="seg-counts">
                <label htmlFor={id("found")}>{t(S.segments.householdsFound)}<input id={id("found")} type="number" min={0} value={found} onChange={(e) => setFound(Math.max(0, Number(e.target.value) || 0))} /></label>
                <label htmlFor={id("pick")}>{t(S.segments.pickupsNeeded)}<input id={id("pick")} type="number" min={0} value={pickups} onChange={(e) => setPickups(Math.max(0, Number(e.target.value) || 0))} /></label>
              </div>
            )}
          </fieldset>
          <BigButton size="md" onClick={mark} disabled={busy || (state === "could_not_reach" && !reason.trim())}>{t(S.segments.mark)}</BigButton>
        </>
      )}
    </article>
  );
}
