import { useState, type ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";
import { v2 } from "../api";
import { displayText, type TraceEntry } from "./trace";
import "./phase-one.css";
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

const clockActions: [ClockAction, string][] = [
  ["advance", "+30 min"],
  ["morning", "Next 07:00"],
  ["rain", "Rain alert"],
  ["river", "River rising"],
  ["flood", "Flood the system"],
  ["reset", "Reset"],
];
export function StepHeader({ at, onAction }: { at?: string; onAction?: (action: ClockAction) => Promise<unknown> }) {
  const [explore, setExplore] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function act(action: ClockAction) {
    setBusy(true);
    setError("");
    try {
      if (onAction) await onAction(action);
      else await v2.clock(action);
    } catch (failure) {
      setError(String(failure));
    } finally {
      setBusy(false);
    }
  }
  return (
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
          <NavLink to="/" end>1 Overview</NavLink>
          <NavLink to="/report" end>2 Report</NavLink>
          <NavLink to="/v">3 Volunteer</NavLink>
          <button onClick={() => setExplore(!explore)} aria-expanded={explore}>
            {explore ? "Guided steps" : "Explore freely"}
          </button>
        </nav>
        <DemoMenu busy={busy} act={act} />
      </div>
      {explore && (
        <nav className="rp-explore">
          <Link to="/v">Volunteer overview</Link>
          <Link to="/v/feed">Every AI decision</Link>
        </nav>
      )}
      {error && <p role="alert">{error}</p>}
    </header>
  );
}

function DemoMenu({ busy, act }: { busy: boolean; act: (action: ClockAction) => Promise<void> }) {
  return (
    <details className="rp-demo">
      <summary>Demo controls ▾</summary>
      <div className="rp-menu">
        {clockActions.map(([action, label]) => (
          <button key={action} disabled={busy} onClick={() => act(action)}>{label}</button>
        ))}
      </div>
    </details>
  );
}

export function Panel({ title, children, className = "" }: { title: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`rp-card ${className}`}>
      <div className="rp-card-head">
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

export const questions = ["I have one boat with 6 seats. Where first?", "Who can't walk?"];
