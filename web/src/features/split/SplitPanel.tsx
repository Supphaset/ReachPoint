import { useEffect, useMemo, useState } from "react";
import type { AskResult, SplitAssignment, SplitPanelView, SplitUnassigned, Suggestion } from "../../data/contract";
import { ASSISTANCE_LABEL, fmtTime } from "../../data/format";
import { askTeams, loadSplitPanel } from "../../data/splitStore";
import { Banner, BigButton, LastUpdated, PriorityBadge, Skeleton } from "../../ui/components";
import { Icon } from "../../ui/Icon";
import { fmtParty, fmtSeats } from "../team/TeamPages";
import "./split.css";

type Ask = { state: "idle" } | { state: "sending" } | { state: "sent"; result: Extract<AskResult, { ok: true }> } | { state: "stale"; result: Extract<AskResult, { ok: false }>; old: Suggestion };

const TIER_LABEL: Record<string, string> = { "1a": "Tier 1a · urgent medical", "1b": "Tier 1b · flagged urgent", "2": "Tier 2" };
const REASON: Record<string, string> = { capacity_exhausted: "capable teams are full today", no_capable_team: "no available team can do this here" };

/** Plain situation line from the numbers (not AI): who covers the urgent cases, how many people are still unmet. */
export function headline(s: Suggestion): string {
  const unmetPeople = s.unassigned.filter((u) => u.unit === "people").reduce((n, u) => n + u.units, 0);
  const urgentOut = s.unassigned.filter((u) => u.tier !== "2" && u.unit === "people").reduce((n, u) => n + u.units, 0);
  const covered = s.assignments.filter((a) => a.unit === "people").reduce((n, a) => n + a.units, 0);
  if (covered === 0 && unmetPeople > 0) return `No capacity left today: ${unmetPeople} people unmet`;
  const urgentTeams = [...new Set(s.assignments.filter((a) => a.tier !== "2").map((a) => a.teamId))].sort();
  const lead = urgentOut
    ? `${urgentOut} urgent ${urgentOut === 1 ? "person has" : "people have"} no team`
    : urgentTeams.length
      ? `${urgentTeams.join(" and ")} cover the urgent cases`
      : "No urgent cases";
  return `${lead}; ${unmetPeople} ${unmetPeople === 1 ? "person" : "people"} still unmet`;
}

function key(a: SplitAssignment) {
  return `${a.listingId}→${a.resourceId}·${a.units}`;
}

export function diffSuggestions(old: Suggestion, cur: Suggestion) {
  const o = new Map(old.assignments.map((a) => [key(a), a]));
  const n = new Map(cur.assignments.map((a) => [key(a), a]));
  return {
    removed: old.assignments.filter((a) => !n.has(key(a))),
    added: cur.assignments.filter((a) => !o.has(key(a))),
    unchanged: cur.assignments.filter((a) => o.has(key(a))),
  };
}

export function SplitPanel() {
  const [view, setView] = useState<SplitPanelView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"plan" | "whatif">("plan");
  const [scenario, setScenario] = useState<string | null>(null);
  const [ask, setAsk] = useState<Ask>({ state: "idle" });
  const [current, setCurrent] = useState<Suggestion | null>(null);

  useEffect(() => {
    loadSplitPanel()
      .then((v) => {
        setView(v);
        setCurrent(v.suggestion);
        setScenario(v.scenarios[0]?.id ?? null);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  if (error)
    return (
      <div className="page split-page">
        <Banner kind="error">Split unavailable. {error}. The open lists still work; teams can take cases.</Banner>
      </div>
    );
  if (!view || !current)
    return (
      <div className="page split-page">
        <p className="muted">Calculating split… (up to 5 s)</p>
        <Skeleton lines={6} />
      </div>
    );

  const s = current;
  const askTeamIds = [...new Set(s.assignments.filter((a) => !a.accepted).map((a) => a.teamId))].sort();
  const canAsk = tab === "plan" && s.solver.optimal && askTeamIds.length > 0 && ask.state !== "sending" && ask.state !== "stale" && ask.state !== "sent";

  const send = async () => {
    setAsk({ state: "sending" });
    try {
      const r = await askTeams(s.suggestionId, askTeamIds, s.snapshotAt);
      setAsk(r.ok ? { state: "sent", result: r } : { state: "stale", result: r, old: s });
    } catch (e) {
      setAsk({ state: "idle" });
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="page split-page">
      <header className="split-head">
        <div>
          <p className="eyebrow">Suggested split · coordinator only</p>
          <h1>{headline(s)}</h1>
          <LastUpdated at={s.snapshotAt} label="Snapshot" />
          <p className="muted">{view.label}</p>
        </div>
        <BigButton size="md" icon="hand" disabled={!canAsk} onClick={send}>
          {ask.state === "sending" ? "Asking…" : `Ask ${askTeamIds.length === 1 ? "this team" : `these ${askTeamIds.length} teams`}`}
        </BigButton>
      </header>

      {!s.solver.optimal && <Banner kind="stale">Can't send: search incomplete. Recalculate or decide by hand.</Banner>}
      {ask.state === "sent" && (
        <Banner kind="info">
          Asked {ask.result.asks.map((a) => a.teamId).join(", ")} at {fmtTime(ask.result.askedAt)}. Taken 0 of {ask.result.asks.length} · still waiting{" "}
          {ask.result.asks.length}. Teams take cases from their list; the first to take a family gets it.
        </Banner>
      )}
      {ask.state === "stale" && (
        <StaleDiff
          ask={ask}
          view={view}
          onUse={() => {
            void loadSplitPanel().then((v) => { setView(v); setCurrent(v.suggestion); setAsk({ state: "idle" }); })
              .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
          }}
        />
      )}

      <div className="segmented split-tabs" role="tablist" aria-label="View">
        <button role="tab" aria-selected={tab === "plan"} onClick={() => setTab("plan")}>
          <Icon name="list" size={18} /> Plan
        </button>
        <button role="tab" disabled={!view.scenarios.length} aria-selected={tab === "whatif"} onClick={() => setTab("whatif")}>
          <Icon name="sparkle" size={18} /> What if…
        </button>
      </div>

      {tab === "plan" ? (
        <Plan s={s} view={view} />
      ) : (
        <WhatIf view={view} scenario={scenario} setScenario={setScenario} />
      )}
    </div>
  );
}

function Plan({ s, view, simulated }: { s: Suggestion; view: SplitPanelView; simulated?: boolean }) {
  const [allFacts, setAllFacts] = useState(false);
  const teams = useMemo(() => {
    const by = new Map<string, SplitAssignment[]>();
    for (const a of s.assignments) by.set(a.resourceId, [...(by.get(a.resourceId) ?? []), a]);
    return [...by.entries()];
  }, [s]);
  const people = (rows: { unit: string; units: number }[]) => rows.filter((r) => r.unit === "people").reduce((n, r) => n + r.units, 0);
  const unmet = people(s.unassigned);

  return (
    <>
      <section className="split-section" aria-label="Team rows">
        <h2>1. Teams</h2>
        {teams.map(([rid, rows]) => {
          const r = view.resources[rid];
          const use = s.resources.find((x) => x.resourceId === rid)!;
          const typ = Object.keys(use.capacity)[0];
          return (
            <article key={rid} className={`team-row ${use.simulated ? "is-sim" : ""}`}>
              <header>
                <strong>{rows[0].teamId}</strong>
                <span className="muted">
                  {(r?.kind ?? "resource").replace("_", " ")} {rid}
                  {use.simulated && " · simulated"}
                </span>
                <span className="team-use num">
                  {Object.entries(use.capacity)
                    .filter(([t]) => rows.some((a) => a.assistanceType === t))
                    .map(([t, cap]) => `${use.used[t]} of ${cap} ${t === "evacuation_transport" ? "seats" : t === "supplies" ? "packs" : cap === 1 ? "visit" : "visits"}`)
                    .join(" · ") || `${typ}`}
                </span>
              </header>
              <ul className="split-rows">
                {rows.map((a) => (
                  <Row key={key(a)} a={a} view={view} />
                ))}
              </ul>
            </article>
          );
        })}
      </section>

      <section className="split-section" aria-label="Still unmet">
        <h2>
          2. Still unmet ({unmet} {unmet === 1 ? "person" : "people"})
        </h2>
        {s.unassigned.length === 0 ? (
          <p className="muted">Everyone reviewed has a suggested team.</p>
        ) : (
          <ul className="split-rows unmet">
            {s.unassigned.map((u) => (
              <Row key={`${u.listingId}-u`} a={u} view={view} />
            ))}
          </ul>
        )}
      </section>

      <section className="split-section" aria-label="Why">
        <h2>3. Why</h2>
        <ul className="why-list">
          {(allFacts ? s.explanations : s.explanations.filter((e) => s.assignments.some((a) => a.listingId === e.listingId && a.tier !== "2"))).map((e) => (
            <li key={e.listingId}>
              <strong>{view.needs[e.listingId]?.caseId ?? e.listingId}</strong> {e.facts.join(" · ")}
            </li>
          ))}
        </ul>
        <button className="btn btn-quiet btn-md" onClick={() => setAllFacts((x) => !x)}>
          {allFacts ? "Show urgent only" : "Show full explanation"}
        </button>
        <p className="fine-print">Facts from the deterministic solver. A suggestion is not a team commitment or a safe route.</p>
      </section>

      <p className="quiet-line num">
        {people(s.assignments) + unmet} people need evacuation or care · {people(s.assignments)} with a suggested team ·{" "}
        {s.assignments.filter((a) => a.unit === "packs").reduce((n, a) => n + a.units, 0)} packs planned · 0 confirmed outcomes
      </p>
      <p className="fine-print">
        {s.solver.optimal ? "Optimal" : "Search incomplete"} · weights w_evac {s.weights.w_evac}, w_supply {s.weights.w_supply}
        {!simulated && view.weights.setAt && ` (set by the coordinator at ${fmtTime(String(view.weights.setAt))})`} · suggestion {s.suggestionId}
      </p>
    </>
  );
}

function Row({ a, view }: { a: SplitAssignment | SplitUnassigned; view: SplitPanelView }) {
  const n = view.needs[a.listingId];
  const isUnmet = "reason" in a;
  return (
    <li className={`split-row tone-${a.colour}`}>
      <div className="split-row-top">
        <PriorityBadge priority={a.colour} lang="en" size="sm" />
        <strong>{n?.caseId}</strong>
        <span className="muted">{n?.label}</span>
        <span className="num split-units">
          {a.units}
          {n && a.units !== n.units ? ` of ${n.units}` : ""} {a.unit === "packs" ? "packs" : a.units === 1 ? "person" : "people"}
        </span>
      </div>
      <p className="split-row-meta">
        <span>{ASSISTANCE_LABEL[a.assistanceType]}</span>
        {a.part && <span>{fmtParty(a.part)}</span>}
        {!isUnmet && (a as SplitAssignment).seatUnits !== null && <span>{fmtSeats((a as SplitAssignment).seatUnits!)}</span>}
        <span className="tier-chip">{TIER_LABEL[a.tier]}</span>
        {!isUnmet && (a as SplitAssignment).accepted && <span className="chip chip-taken chip-sm">Already accepted</span>}
        {a.split && <span className="chip chip-held chip-sm">Split · you approve</span>}
      </p>
      {isUnmet && (
        <p className="unmet-reason">
          {REASON[(a as SplitUnassigned).reason]}
          {(a as SplitUnassigned).returnedFrom && ` · back from ${(a as SplitUnassigned).returnedFrom}`}
        </p>
      )}
    </li>
  );
}

function WhatIf({ view, scenario, setScenario }: { view: SplitPanelView; scenario: string | null; setScenario: (id: string) => void }) {
  const sc = view.scenarios.find((x) => x.id === scenario) ?? view.scenarios[0];
  if (!sc) return <p>No comparison scenarios in this live plan.</p>;
  const d = sc.diff.peopleCoveredDelta;
  return (
    <section className="whatif" aria-label="What if">
      <p className="sim-label">
        <Icon name="sparkle" size={16} /> {view.whatIfLabel}
      </p>
      <div className="choice-row" role="radiogroup" aria-label="Scenario">
        {view.scenarios.map((x) => (
          <label key={x.id} className={`choice ${x.id === sc.id ? "is-on" : ""}`}>
            <input type="radio" name="scenario" checked={x.id === sc.id} onChange={() => setScenario(x.id)} />
            <span>{x.label}</span>
          </label>
        ))}
      </div>
      <p className="whatif-delta num">
        {d > 0 ? `+${d} people covered` : d < 0 ? `${d} people covered` : "Same number of people covered"} compared with the plan
      </p>
      <h2 className="whatif-headline">{headline(sc.suggestion)}</h2>
      <Plan s={sc.suggestion} view={view} simulated />
      <p className="fine-print">To make it real, change the resource or ask a team from the Plan tab. Nothing here is sent.</p>
    </section>
  );
}

function StaleDiff({ ask, view, onUse }: { ask: Extract<Ask, { state: "stale" }>; view: SplitPanelView; onUse: () => void }) {
  const d = diffSuggestions(ask.old, ask.result.detail.current);
  const label = (a: SplitAssignment) => `${view.needs[a.listingId]?.caseId} · ${a.units} → ${a.resourceId} (${a.teamId})`;
  return (
    <section className="stale-diff" aria-label="Needs or resources changed">
      <Banner kind="stale">
        <strong>{ask.result.message}.</strong> {ask.result.detail.why}. Nothing was sent. Review the new split before asking.
      </Banner>
      <div className="diff-cols">
        <div>
          <h3>No longer suggested</h3>
          <ul>{d.removed.length ? d.removed.map((a) => <li key={key(a)} className="struck">{label(a)}</li>) : <li className="muted">None</li>}</ul>
        </div>
        <div>
          <h3>New</h3>
          <ul>{d.added.length ? d.added.map((a) => <li key={key(a)}>{label(a)}</li>) : <li className="muted">None</li>}</ul>
        </div>
        <div>
          <h3>Unchanged</h3>
          <ul>{d.unchanged.length ? d.unchanged.map((a) => <li key={key(a)}>{label(a)}</li>) : <li className="muted">None</li>}</ul>
        </div>
      </div>
      <BigButton size="md" onClick={onUse}>
        Review the new split
      </BigButton>
    </section>
  );
}
