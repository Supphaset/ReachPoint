import { useState, type ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";
import { v2 } from "../api";
import { DemoBar } from "./DemoBar";
import { displayText, type TraceEntry } from "./trace";
import "./phase-one.css";
import "./kit.css";
export type ClockAction = Parameters<typeof v2.clock>[0];
export function HonestyLabel() {
  return <div className="rp-honesty">Hat Yai flood · real water data, synthetic people</div>;
}

interface DepthRangeProps {
  value: number | null;
  lo?: number;
  hi?: number;
  source?: string;
  at?: string;
}

export function DepthRange({ value, lo, hi, source, at }: DepthRangeProps) {
  const range = lo !== undefined && hi !== undefined ? ` · likely ${lo.toFixed(1)}–${hi.toFixed(1)} m` : "";
  return (
    <span className="rp-pill rp-depth">
      {value === null ? "Depth unknown" : `${value.toFixed(1)} m`}
      {range}
      {source ? ` · ${source}` : ""}
      {at ? ` · ${at}` : ""}
    </span>
  );
}

const whoLabels = {
  gemini: "✦ Gemini",
  rules: "≡ Rules",
  physics: "∿ Physics",
  action: "→ Action",
  doubt: "? Doubt",
};
export function TraceLine({ who, at, what, quote, gloss, to }: Omit<TraceEntry, "id" | "atH">) {
  return (
    <article className={`rp-trace rp-${who}`}>
      <div className="rp-trace-meta">
        <span className="rp-who">{whoLabels[who]}</span>
        <time>{at}</time>
      </div>
      <strong>
        {to ? <Link to={to}>{displayText(what)}</Link> : displayText(what)}
      </strong>
      {quote && (
        <blockquote lang="th">
          {displayText(quote)}
          <span className="rp-gloss">{gloss}</span>
        </blockquote>
      )}
    </article>
  );
}

export function StepHeader({ at, onAction, showDemo = true }: {
  at?: string; onAction?: (action: ClockAction) => Promise<unknown>; showDemo?: boolean;
}) {
  const [explore, setExplore] = useState(false);
  return (
    <>
    <header className="rp-header">
      <div className="rp-bar">
        <Link className="rp-logo" to="/">
          <span aria-hidden="true">◉</span> ReachPoint
        </Link>
        <div className="rp-replay">
          <b>REPLAY</b>
          <span>{at ?? "21–28 Nov 2025"}</span>
        </div>
        <nav className="rp-steps" aria-label="Demo steps">
          <NavLink to="/" end><span>1 ภาพรวม</span><small>Overview</small></NavLink>
          <NavLink to="/report" end><span>2 แจ้งเหตุ</span><small>Report</small></NavLink>
          <NavLink to="/v"><span>3 อาสา</span><small>Volunteer</small></NavLink>
          <button onClick={() => setExplore(!explore)} aria-expanded={explore}>
            <span>{explore ? "ตามขั้นตอน" : "สำรวจ"}<small>{explore ? "Guided steps" : "Explore freely"}</small></span>
          </button>
        </nav>
      </div>
      {explore && (
        <nav className="rp-explore">
          <Link to="/v">Volunteer overview</Link>
          <Link to="/v/feed">Every AI decision</Link>
        </nav>
      )}
    </header>
    {showDemo && <DemoBar at={at} onAction={onAction ?? (action => v2.clock(action))} />}
    </>
  );
}

export function Panel({ title, children, className = "" }: { title: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`card rp-card ${className}`}>
      <div className="rp-card-head">
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

export const questions = ["I have one boat with 6 seats. Where first?", "Who can't walk?"];
