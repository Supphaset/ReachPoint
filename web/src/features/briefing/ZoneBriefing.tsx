import type { AreaBriefingView, Fact, ZoneBriefingView } from "../../data/contract";
import { ASSISTANCE_LABEL, fmtAgo, fmtDepth, fmtInt, fmtRange, fmtTime } from "../../data/format";
import { now } from "../../data/clock";
import { CountBadge, EstimateRange, PriorityBadge, StatusChip } from "../../ui/components";
import { Icon } from "../../ui/Icon";
import { useLang } from "../../i18n/lang";
import { S, seedText } from "../../i18n/strings";
import { areaText, bt, unitText } from "../../i18n/briefing";

export function FactValue({ f }: { f: Fact }) {
  const { t, lang } = useLang();
  if (f.value === null) return <span className="muted">{t(S.briefing.unknownValue)}</span>;
  return (
    <span className="num">
      {fmtInt(f.value)}
      {f.of !== undefined && t(S.briefing.of(fmtInt(f.of)))}{" "}
      <span className="fact-unit">{unitText(f.unit, f.of ?? f.value, lang)}</span>
    </span>
  );
}

export function FactList({ facts }: { facts: Fact[] }) {
  const { lang } = useLang();
  return (
    <dl className="facts">
      {facts.map((f) => (
        <div key={f.key} className="fact">
          <dt>
            {bt(f.label, lang)}
            {f.basis && <span className="fact-basis">{bt(f.basis, lang)}</span>}
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
  const { t, lang } = useLang();
  const label = (segmentId: string) => seedText(zone.segments.find((s) => s.segmentId === segmentId)?.label ?? segmentId, lang);
  const evac = zone.facts.find((f) => f.key === "reviewedEvacuation");

  return (
    <article className="zone-briefing" aria-labelledby={`zb-${zone.zoneId}`}>
      <header className="zb-head">
        <div>
          <p className="muted zb-crumb">
            {areaText(area.areaId, area.label, area.description, lang).label}
            {zone.district && ` · ${zone.district}`}
          </p>
          <h2 id={`zb-${zone.zoneId}`}>{t(S.briefing.zone(zone.zoneId))}</h2>
        </div>
        {onClose && (
          <button className="icon-btn" onClick={onClose} aria-label={t(S.briefing.closeZone)}>
            <Icon name="close" size={22} />
          </button>
        )}
      </header>

      <CountBadge urgent={zone.badge.urgent} unreviewed={zone.badge.unreviewed} empty={zone.status === "no_reports"} />

      <section className="zb-headline">
        <EstimateRange range={fmtRange(zone.estimate.everyone)}>{t(S.briefing.liveHere)}</EstimateRange>
        {evac && evac.value !== null && (
          <p className="zb-reviewed">
            <Icon name="check" size={16} />
            <span>
              <strong className="num">{fmtInt(evac.value)}</strong> {t(S.briefing.reviewedEvac)}
            </span>
          </p>
        )}
      </section>

      <section>
        <h3>{t(S.briefing.facts)}</h3>
        <FactList facts={zone.facts} />
      </section>

      <section className="unknown-row" aria-label={t(S.briefing.unknown)}>
        <h3>
          <Icon name="question" size={18} /> {t(S.briefing.unknown)}
        </h3>
        {zone.unknown.length ? (
          <ul>
            {zone.unknown.map((u) => (
              <li key={u.key + (u.ref ?? "")}>{seedText(bt(u.text, lang), lang)}</li>
            ))}
          </ul>
        ) : (
          <p className="muted">{t(S.briefing.unknownNone)}</p>
        )}
      </section>

      <section className="zb-estimate">
        <h3>{t(S.briefing.peopleHere)}</h3>
        <EstimateRange range={fmtRange(zone.estimate.notYetChecked)}>{t(S.briefing.notYetChecked)}</EstimateRange>
        {zone.estimate.modelledFlooded && zone.estimate.basis === "model" && (
          <EstimateRange range={fmtRange(zone.estimate.modelledFlooded)}>{t(S.briefing.floodedPeak)}</EstimateRange>
        )}
        {zone.depth && (
          <p className="estimate">
            <Icon name="water" size={16} />
            <span>
              {t(S.briefing.waterDepth)} <strong>{fmtDepth(zone.depth.modelledM, 3, lang)}</strong>{" "}
              <span className="estimate-tag">{t(S.briefing.modelNotMeasured)}</span>
            </span>
          </p>
        )}
        <p className="fine-print">{bt(area.estimate.label, lang)}</p>
      </section>

      <section>
        <h3>
          <Icon name="water" size={18} /> {t(S.briefing.callerWater)}
        </h3>
        {zone.callerWater.length === 0 ? (
          <p className="muted">{t(S.briefing.noCallerWater)}</p>
        ) : (
          <ul className="water-list">
            {zone.callerWater.map((w) => (
              <li key={w.segmentId} className={w.stale ? "is-stale" : ""}>
                <strong>{bt(w.bandLabel, lang)}</strong> <span className="muted">{t(S.briefing.about(w.approxM))}</span>
                <span className="fine-print">
                  {seedText(w.landmarkLabel, lang)} · {fmtTime(w.latestAt)} · {t(S.briefing.callers(w.callers))}
                  {w.stale && t(S.briefing.staleWater)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h3>{t(S.briefing.cases)}</h3>
        {zone.cases.length === 0 ? (
          <p className="muted">{t(S.briefing.noCases)}</p>
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
                      <span className="need-type">{S.assistance[a.type] ? t(S.assistance[a.type]) : ASSISTANCE_LABEL[a.type]}</span>
                      <PriorityBadge priority={a.priority} lang={lang} size="sm" />
                      <StatusChip kind="job" state={a.allocation} lang={lang} size="sm" />
                      {a.teamId && <span className="muted">{a.teamId}</span>}
                      {a.note && <span className="muted">· {bt(a.note, lang)}</span>}
                    </li>
                  ))}
                </ul>
                <p className="fine-print">
                  {t(S.briefing.lastConfirmed(fmtTime(c.lastConfirmedAt), lang === "en" ? fmtAgo(c.lastConfirmedAt, now()) : t(S.units.ago(Math.floor((now() - Date.parse(c.lastConfirmedAt)) / 60000)))))}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h3>{t(S.briefing.segments)}</h3>
        <ul className="segment-list">
          {zone.segments.map((s) => (
            <li key={s.segmentId} className="segment-row">
              <div>
                <p>{seedText(s.label, lang)}</p>
                <p className="fine-print num">
                  {t(S.briefing.segLine(fmtRange(s.estimate.everyone), s.depth.modelledM ? fmtDepth(s.depth.modelledM, 3, lang) : null, s.cases))}
                </p>
                {s.check.at && (
                  <p className="fine-print">
                    {fmtTime(s.check.at)} · {s.check.teamId}
                    {s.check.householdsFound !== undefined && t(S.briefing.households(s.check.householdsFound))}
                    {s.check.pickupsNeeded ? t(S.briefing.pickupNeeded(s.check.pickupsNeeded)) : ""}
                    {s.check.reason && ` · ${s.check.reason}`}
                  </p>
                )}
              </div>
              <StatusChip kind="segment" state={s.check.state} lang={lang} size="sm" />
            </li>
          ))}
        </ul>
      </section>

      <section className="zb-text">
        <h3>
          <Icon name="sparkle" size={16} /> {t(S.briefing.briefingTitle)}
        </h3>
        {zone.briefing.state === "ready" && zone.briefing.text ? (
          <div className="zb-ai">
            <p lang="en">{zone.briefing.text}</p>
            <p className="fine-print">
              {t(S.briefing.aiNote)}
              {lang === "th" && ` ${t(S.briefing.aiEnglish)}`}
            </p>
          </div>
        ) : zone.briefing.state === "writing" ? (
          <p className="muted">{t(S.briefing.writing)}</p>
        ) : (
          <p className="muted">{t(S.briefing.briefingUnavailable)}</p>
        )}
      </section>

    </article>
  );
}
