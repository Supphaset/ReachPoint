import type { ReactNode } from "react";
import { fmtAgo, fmtTime } from "../data/format";
import { now } from "../data/clock";
import { Icon, type IconName } from "./Icon";
import { useLang } from "../i18n/lang";
import { S } from "../i18n/strings";
import { JOB, OUTCOME, PRIORITY, REVIEW, SEGMENT, TEAM_STATUS, type StateStyle } from "./states";
import "./components.css";

function Chip({ s, lang = "both", size = "md" }: { s: StateStyle; lang?: "both" | "en" | "th"; size?: "sm" | "md" }) {
  const text = lang === "en" ? s.en : lang === "th" ? s.th : `${s.th} · ${s.en}`;
  return (
    <span className={`chip chip-${s.tone} chip-${size}`}>
      <Icon name={s.icon} size={size === "sm" ? 14 : 16} />
      <span>{text}</span>
    </span>
  );
}

/** Priority from the shared tiers (RED → YELLOW → GREEN). Red is used for nothing else. */
export function PriorityBadge({ priority, lang, size }: { priority: keyof typeof PRIORITY; lang?: "both" | "en" | "th"; size?: "sm" | "md" }) {
  return <Chip s={PRIORITY[priority]} lang={lang} size={size} />;
}

/** Job, segment-check or review state. */
export function StatusChip({
  kind,
  state,
  lang,
  size,
}: {
  kind: "job" | "segment" | "review" | "team" | "outcome";
  state: string;
  lang?: "both" | "en" | "th";
  size?: "sm" | "md";
}) {
  const table = { job: JOB, segment: SEGMENT, review: REVIEW, team: TEAM_STATUS, outcome: OUTCOME }[kind];
  const s = table[state] ?? { th: state, en: state, icon: "question", tone: "unknown" };
  return <Chip s={s} lang={lang} size={size} />;
}

/** Count badge for an area or zone row, e.g. "1 urgent · 1 unreviewed". Nothing is shown as "safe". */
export function CountBadge({ urgent, unreviewed, empty }: { urgent: number; unreviewed: number; empty?: boolean }) {
  const { t } = useLang();
  if (empty) {
    return (
      <span className="chip chip-unknown chip-sm hatched">
        <Icon name="question" size={14} />
        <span>{t(S.common.noReports)}</span>
      </span>
    );
  }
  return (
    <span className="count-badge">
      {urgent > 0 && (
        <span className="chip chip-red chip-sm">
          <Icon name="octagon" size={14} />
          <span className="num">{t(S.common.urgentN(urgent))}</span>
        </span>
      )}
      {unreviewed > 0 && (
        <span className="chip chip-unknown chip-sm">
          <Icon name="question" size={14} />
          <span className="num">{t(S.common.unreviewedN(unreviewed))}</span>
        </span>
      )}
    </span>
  );
}

/** Dashed "AI proposal" card: nothing in it counts until a person approves it. */
export function ProposalCard({
  label,
  title,
  quote,
  children,
  onApprove,
  onReject,
  busy,
}: {
  label?: string;
  title: string;
  quote?: string;
  children?: ReactNode;
  onApprove?: () => void;
  onReject?: () => void;
  busy?: boolean;
}) {
  return (
    <section className="proposal" aria-label={`${label ?? "AI proposal"}: ${title}`}>
      <header className="proposal-head">
        <Icon name="sparkle" size={16} />
        <span>{label ?? "ข้อเสนอจาก AI · AI proposal, needs your approval"}</span>
      </header>
      <h3>{title}</h3>
      {quote && <blockquote className="proposal-quote">“{quote}”</blockquote>}
      {children}
      {(onApprove || onReject) && (
        <div className="proposal-actions">
          {onApprove && (
            <BigButton onClick={onApprove} disabled={busy} size="md">
              Approve
            </BigButton>
          )}
          {onReject && (
            <BigButton onClick={onReject} disabled={busy} variant="secondary" size="md">
              Reject
            </BigButton>
          )}
        </div>
      )}
    </section>
  );
}

const BANNER: Record<string, { icon: IconName; role: "status" | "alert" }> = {
  offline: { icon: "offline", role: "status" },
  stale: { icon: "clock", role: "status" },
  overdue: { icon: "clock", role: "status" },
  error: { icon: "alert", role: "alert" },
  info: { icon: "alert", role: "status" },
};

/** Error / offline / stale / overdue banner. Errors are ink, delays amber; never red alarm. */
export function Banner({
  kind,
  children,
  action,
}: {
  kind: "offline" | "stale" | "overdue" | "error" | "info";
  children: ReactNode;
  action?: { label: string; onClick: () => void };
}) {
  const b = BANNER[kind];
  return (
    <div className={`banner banner-${kind}`} role={b.role}>
      <Icon name={b.icon} size={20} />
      <div className="banner-text">{children}</div>
      {action && (
        <button className="banner-action" onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </div>
  );
}

/** "Last updated 10:15 · 3 min ago"; offline adds "reconnecting". Times keep their own labels. */
export function LastUpdated({ at, offline, label }: { at: string; offline?: boolean; label?: string }) {
  const { t, lang } = useLang();
  const mins = Math.floor((now() - Date.parse(at)) / 60000);
  return (
    <p className="last-updated">
      <Icon name={offline ? "offline" : "refresh"} size={14} />
      <span>
        {label ?? t(S.common.lastUpdated)} <time dateTime={at}>{fmtTime(at)}</time> · {lang === "en" ? fmtAgo(at, now()) : t(S.units.ago(mins))}
        {offline && ` · ${t(S.common.reconnecting)}`}
      </span>
    </p>
  );
}

export function BigButton({
  children,
  onClick,
  variant = "primary",
  size = "lg",
  disabled,
  icon,
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "quiet";
  size?: "md" | "lg";
  disabled?: boolean;
  icon?: IconName;
  type?: "button" | "submit";
}) {
  return (
    <button type={type} className={`btn btn-${variant} btn-${size}`} onClick={onClick} disabled={disabled}>
      {icon && <Icon name={icon} size={20} />}
      <span>{children}</span>
    </button>
  );
}

/** A labelled estimate. Always says "estimate", always a range, never added to counts. */
export function EstimateRange({ range, children }: { range: string; children: ReactNode }) {
  const { t } = useLang();
  return (
    <p className="estimate">
      <Icon name="people" size={16} />
      <span>
        {t(S.common.about)} <strong className="num">{range}</strong> {children} <span className="estimate-tag">{t(S.common.estimate)}</span>
      </span>
    </p>
  );
}

export function Skeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="skeleton" aria-busy="true" aria-label="กำลังโหลด… Loading">
      {Array.from({ length: lines }, (_, i) => (
        <div key={i} className="skeleton-line" style={{ width: `${90 - i * 15}%` }} />
      ))}
    </div>
  );
}
