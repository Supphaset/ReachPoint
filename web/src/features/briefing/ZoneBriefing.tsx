import type { AreaBriefingView, Fact, ZoneBriefingView } from "../../data/contract";
import { ASSISTANCE_LABEL, fmtAgo, fmtDepth, fmtInt, fmtRange, fmtTime } from "../../data/format";
import { now } from "../../data/clock";
import { CountBadge, EstimateRange, PriorityBadge, StatusChip } from "../../ui/components";
import { Icon } from "../../ui/Icon";

export function FactValue({ f }: { f: Fact }) {
  if (f.value === null) return <span className="muted">Unknown</span>;
  return (
    <span className="num">
      {fmtInt(f.value)}
      {f.of !== undefined && ` of ${fmtInt(f.of)}`}{" "}
      <span className="fact-unit">{(f.of ?? f.value) === 1 ? f.unit.replace(/s$/, "") : f.unit}</span>
    </span>
  );
}

export function FactList({ facts }: { facts: Fact[] }) {
  return (
    <dl className="facts">
      {facts.map((f) => (
        <div key={f.key} className="fact">
          <dt>
            {f.label}
            {f.basis && <span className="fact-basis">{f.basis}</span>}
          </dt>
          <dd>
            <FactValue f={f} />
          </dd>
        </div>
      ))}
    </dl>
  );
}

/** Zone briefing: facts, the Unknown row, estimate and depth (labelled), cases, segments, briefing text. */
export function ZoneBriefing({ zone, area, onClose }: { zone: ZoneBriefingView; area: AreaBriefingView; onClose?: () => void }) {
  const label = (segmentId: string) => zone.segments.find((s) => s.segmentId === segmentId)?.label ?? segmentId;
  const evac = zone.facts.find((f) => f.key === "reviewedEvacuation");

  return (
    <article className="zone-briefing" aria-labelledby={`zb-${zone.zoneId}`}>
      <header className="zb-head">
        <div>
          <p className="muted zb-crumb">
            {area.label}
            {zone.district && ` · ${zone.district}`}
          </p>
          <h2 id={`zb-${zone.zoneId}`}>Zone {zone.zoneId}</h2>
        </div>
        {onClose && (
          <button className="icon-btn" onClick={onClose} aria-label="Close zone briefing">
            <Icon name="close" size={22} />
          </button>
        )}
      </header>

      <CountBadge urgent={zone.badge.urgent} unreviewed={zone.badge.unreviewed} empty={zone.status === "no_reports"} />

      <section className="zb-headline">
        <EstimateRange range={fmtRange(zone.estimate.everyone)}>live here</EstimateRange>
        {evac && evac.value !== null && (
          <p className="zb-reviewed">
            <Icon name="check" size={16} />
            <span>
              <strong className="num">{fmtInt(evac.value)}</strong> reported needing evacuation (reviewed)
            </span>
          </p>
        )}
      </section>

      <section>
        <h3>Facts</h3>
        <FactList facts={zone.facts} />
      </section>

      <section className="unknown-row" aria-label="Unknown">
        <h3>
          <Icon name="question" size={18} /> Unknown
        </h3>
        {zone.unknown.length ? (
          <ul>
            {zone.unknown.map((u) => (
              <li key={u.key + (u.ref ?? "")}>{u.text}</li>
            ))}
          </ul>
        ) : (
          <p className="muted">Nothing listed. Unknown is never zero: ask the desk if in doubt.</p>
        )}
      </section>

      <section className="zb-estimate">
        <h3>People here (estimate)</h3>
        <EstimateRange range={fmtRange(zone.estimate.notYetChecked)}>in segments not yet checked</EstimateRange>
        {zone.estimate.modelledFlooded && zone.estimate.basis === "model" && (
          <EstimateRange range={fmtRange(zone.estimate.modelledFlooded)}>likely flooded at the peak (model)</EstimateRange>
        )}
        {zone.depth && (
          <p className="estimate">
            <Icon name="water" size={16} />
            <span>
              Water depth <strong>{fmtDepth(zone.depth.modelledM)}</strong>{" "}
              <span className="estimate-tag">model, not measured</span>
            </span>
          </p>
        )}
        <p className="fine-print">{area.estimate.label}</p>
      </section>

      <section>
        <h3>
          <Icon name="water" size={18} /> Water reported by callers
        </h3>
        {zone.callerWater.length === 0 ? (
          <p className="muted">No reviewed caller has described the water here. That doesn't mean it's dry.</p>
        ) : (
          <ul className="water-list">
            {zone.callerWater.map((w) => (
              <li key={w.segmentId} className={w.stale ? "is-stale" : ""}>
                <strong>{w.bandLabel}</strong> <span className="muted">(about {w.approxM} m)</span>
                <span className="fine-print">
                  {w.landmarkLabel} · {fmtTime(w.latestAt)} · {w.callers} caller{w.callers > 1 ? "s" : ""}
                  {w.stale && " · older than 6 h, may have changed"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h3>Cases in this zone</h3>
        {zone.cases.length === 0 ? (
          <p className="muted">No reviewed cases. That doesn't mean no one needs help.</p>
        ) : (
          <ul className="case-list">
            {zone.cases.map((c) => (
              <li key={c.caseId} className="case-row">
                <div className="case-top">
                  <strong>{c.caseId}</strong>
                  <span className="muted">{label(c.segmentId)}</span>
                  <span className="num case-people">
                    <Icon name="people" size={16} /> {c.people}
                  </span>
                </div>
                <ul className="case-needs">
                  {c.assistance.map((a) => (
                    <li key={a.type}>
                      <span className="need-type">{ASSISTANCE_LABEL[a.type]}</span>
                      <PriorityBadge priority={a.priority} lang="en" size="sm" />
                      <StatusChip kind="job" state={a.allocation} lang="en" size="sm" />
                      {a.teamId && <span className="muted">{a.teamId}</span>}
                      {a.note && <span className="muted">· {a.note}</span>}
                    </li>
                  ))}
                </ul>
                <p className="fine-print">
                  Last confirmed {fmtTime(c.lastConfirmedAt)} · {fmtAgo(c.lastConfirmedAt, now())}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h3>Segments</h3>
        <ul className="segment-list">
          {zone.segments.map((s) => (
            <li key={s.segmentId} className="segment-row">
              <div>
                <p>{s.label}</p>
                <p className="fine-print num">
                  About {fmtRange(s.estimate.everyone)} live here (estimate)
                  {s.depth.modelledM && ` · depth ${fmtDepth(s.depth.modelledM)} (model)`}
                  {s.cases > 0 && ` · ${s.cases} case${s.cases > 1 ? "s" : ""}`}
                </p>
                {s.check.at && (
                  <p className="fine-print">
                    {fmtTime(s.check.at)} · {s.check.teamId}
                    {s.check.householdsFound !== undefined && ` · ${s.check.householdsFound} households found`}
                    {s.check.pickupsNeeded ? ` · ${s.check.pickupsNeeded} pickup needed` : ""}
                    {s.check.reason && ` · ${s.check.reason}`}
                  </p>
                )}
              </div>
              <StatusChip kind="segment" state={s.check.state} lang="en" size="sm" />
            </li>
          ))}
        </ul>
      </section>

      <section className="zb-text">
        <h3>
          <Icon name="sparkle" size={16} /> Briefing
        </h3>
        {zone.briefing.state === "ready" && zone.briefing.text ? (
          <div className="zb-ai">
            <p>{zone.briefing.text}</p>
            <p className="fine-print">Written by AI from the facts above only. Every number and place was checked against them before it was shown.</p>
          </div>
        ) : zone.briefing.state === "writing" ? (
          <p className="muted">Writing the briefing… The facts above are complete without it.</p>
        ) : (
          <p className="muted">Briefing unavailable. The facts above are complete.</p>
        )}
      </section>

    </article>
  );
}
