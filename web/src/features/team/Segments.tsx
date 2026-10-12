import { useState } from "react";
import type { SegmentJob, SegmentRow, TeamMissionsView } from "../../data/contract";
import { fmtRange, fmtTime } from "../../data/format";
import { markSegment, sendFieldReport, takeSegment } from "../../data/teamStore";
import { Banner, BigButton, StatusChip } from "../../ui/components";
import "./segments.css";

function markText(m: NonNullable<SegmentRow["mark"]>) {
  if (m.state === "could_not_reach") return `Couldn't reach ${fmtTime(m.at)} · ${m.teamId} · ${m.reason}`;
  const label = m.state === "checked" ? "Checked" : "Partly checked";
  return `${label} ${fmtTime(m.at)} · ${m.teamId} · ${m.householdsFound} ${m.householdsFound === 1 ? "household" : "households"} found · ${m.pickupsNeeded} ${m.pickupsNeeded === 1 ? "pickup" : "pickups"} needed`;
}

function Facts({ s }: { s: Pick<SegmentRow, "registerCount" | "estimate" | "families"> }) {
  return (
    <p className="seg-facts">
      About {fmtRange(s.estimate.everyone)} live here (estimate)
      {s.registerCount ? ` · ${s.registerCount} on the vulnerable register (not confirmed in need)` : ""}
      {s.families.length ? ` · ${s.families.length} reviewed ${s.families.length === 1 ? "family" : "families"} here` : " · no reviewed calls here"}
    </p>
  );
}

/** Waiting list: published zone missions, one row per segment; a team takes one segment at a time. */
export function ZoneMissions({ v, offline }: { v: TeamMissionsView; offline: boolean }) {
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  if (!v.zoneMissions?.length) return null;
  const mine = (v.segmentJobs ?? []).some((j) => j.state === "taken");
  const take = async (id: string) => {
    setBusy(id);
    const r = await takeSegment(id);
    setBusy(null);
    setMsg(r.ok ? null : r.message);
  };
  return (
    <section className="zone-missions" aria-label="Zone missions">
      <h2>Zone missions</h2>
      <p className="muted">Check a segment for people who didn't call. Take one at a time; mark it when you leave.</p>
      {msg && <Banner kind="error">{msg}</Banner>}
      {v.zoneMissions.map((m) => (
        <article key={m.missionId} className="mission">
          <h3>
            Zone {m.zoneId} <span className="muted">· published {fmtTime(m.publishedAt)}</span>
          </h3>
          {m.reasons.length > 0 && <p className="fine-print">{m.reasons.join(" · ")}</p>}
          <ul className="seg-list">
            {m.segments.map((s) => (
              <li key={s.segmentId} className="seg-row">
                <div className="seg-top">
                  <strong>{s.label}</strong>
                  <StatusChip kind="segment" state={s.state} lang="en" size="sm" />
                </div>
                {s.state === "taken" && <p className="fine-print">Taken by {s.takenBy}</p>}
                {s.mark && s.state !== "taken" && <p className="fine-print">{markText(s.mark)}</p>}
                <Facts s={s} />
                {s.state === "open" || s.state === "could_not_reach" || s.state === "partly_checked" ? (
                  <BigButton size="md" variant="secondary" onClick={() => take(s.segmentId)} disabled={offline || mine || busy !== null}>
                    {busy === s.segmentId ? "Taking…" : mine ? "Finish your segment first" : "Take segment"}
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
  if (!jobs.length) return null;
  return (
    <section className="seg-jobs" aria-label="My segments">
      <h2>My segments</h2>
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
        <strong>{j.label}</strong>
        <StatusChip kind="segment" state={j.state === "taken" ? "taken" : (j.mark?.state ?? "checked")} lang="en" size="sm" />
      </div>
      <p className="fine-print">Taken {fmtTime(j.takenAt)}{j.mark ? ` · ${markText(j.mark)}` : ""}</p>
      <Facts s={j} />
      {j.families.length > 0 && (
        <p className="fine-print">Reviewed families here: {j.families.map((f) => `${f.caseId} (${f.people})`).join(", ")}. Take them from the Waiting list.</p>
      )}
      {msg && <Banner kind="error">{msg}</Banner>}
      {j.state === "taken" && (
        <>
          <label htmlFor={id("report")} className="seg-label">
            Found people who didn't call? Tell the desk (no names or phone numbers)
          </label>
          <textarea id={id("report")} rows={3} value={text} onChange={(e) => setText(e.target.value)} placeholder="e.g. Elderly couple on the 2nd floor, one bedridden" />
          {sent && <p className="fine-print">Sent to the desk as {sent}. They review it before it becomes a case.</p>}
          <BigButton size="md" variant="secondary" onClick={report} disabled={busy || !text.trim()}>Send field report</BigButton>

          <fieldset className="seg-mark">
            <legend>Mark this segment when you leave</legend>
            {([["checked", "Checked"], ["partly_checked", "Partly checked"], ["could_not_reach", "Couldn't reach"]] as const).map(([k, l]) => (
              <label key={k} className="inline" htmlFor={id(k)}>
                <input id={id(k)} type="radio" name={id("state")} checked={state === k} onChange={() => setState(k)} /> {l}
              </label>
            ))}
            {state === "could_not_reach" ? (
              <label htmlFor={id("why")}>
                Why?
                <input id={id("why")} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. access blocked, current too strong" />
              </label>
            ) : (
              <div className="seg-counts">
                <label htmlFor={id("found")}>Households found<input id={id("found")} type="number" min={0} value={found} onChange={(e) => setFound(Math.max(0, Number(e.target.value) || 0))} /></label>
                <label htmlFor={id("pick")}>Pickups needed<input id={id("pick")} type="number" min={0} value={pickups} onChange={(e) => setPickups(Math.max(0, Number(e.target.value) || 0))} /></label>
              </div>
            )}
          </fieldset>
          <BigButton size="md" onClick={mark} disabled={busy || (state === "could_not_reach" && !reason.trim())}>Mark segment</BigButton>
        </>
      )}
    </article>
  );
}
