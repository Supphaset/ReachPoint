/** One zone in depth: the water and its outlook, the AI briefing, families by priority, and who plans to come. */
import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { DepthRange } from "../ui/Shared";
import { BoardMap, zoneCenter } from "../BoardMap";
import { v2, vol, type CaseRow } from "../api";
import { MiniMap, Needs, StatusChip, VShell, useGeo, useLive, useTeam } from "./shared";
export function ZonePage() {
  const { id = "" } = useParams();
  const [team] = useTeam();
  const { data, error } = useLive(() => vol.zone(id, team), [id, team]);
  const geo = useGeo();
  const { data: board } = useLive(() => v2.state(), []);
  const focus = useMemo(() => {
    const center = geo ? zoneCenter(geo, id) : null;
    return center ? { lon: center[0], lat: center[1] } : null;
  }, [geo, id]);
  const navigate = useNavigate();
  const [showClosed, setShowClosed] = useState(false);
  const [area, setArea] = useState<string | null>(() => decodeURIComponent(window.location.hash.slice(1)) || null);
  const zone = data?.zone;
  const level = zone?.level;
  const inArea = area ? new Set(data?.subareas.find(block => block.id === area)?.households ?? []) : null;
  const rows = (data?.households ?? []).filter(household =>
    (showClosed || !["safe", "evacuated", "nobodyThere", "atShelter"].includes(household.status))
    && (!inArea || inArea.has(household.id)));
  const access = data?.subareas.filter(block => block.open).map(block => block.access) ?? [];
  const vehicle = access.includes("boat") ? "Bring a boat" : access.includes("unknown") || !access.length
    ? "Check access before choosing a vehicle" : access.includes("truck") ? "Bring a high truck" : "Walk access reported";
  return (
    <VShell title={`Zone ${id}${zone?.label ? ` · ${zone.label}` : ""}`} sub={zone?.district ?? undefined} at={data?.now.at}>
      {error && <p className="v2-error">Couldn't load zone {id}: {error}</p>}
      {data && zone && (
        <div className="rp-zone-layout">
          <div className="rp-stack">
            <section className="rp-decision rp-pad">
              <span className="v-label">Decision · review before departure</span>
              <h2>{vehicle} to {id} · {data.totals.urgent ?? zone.people.urgent} urgent</h2>
              <p>{data.totals.open} families waiting · {zone.plans.length ? `${zone.plans.length} teams planned` : "No team planned"}</p>
              <p>{data.briefing}</p>
              <Link to="/v" className="rp-button rp-primary">See where help is missing →</Link>
              <p className="rp-honesty">Access comes from blocks with waiting families. Confirm conditions; this is not a safe route.</p>
            </section>
            <div className="rp-zone-reasons">
              <section>
                <h3>Why here</h3>
                <p>{data.totals.people} people · {zone.people.cannotWalk} cannot walk · {zone.people.children} children · {zone.people.elderly} elderly.</p>
                <p>{zone.gap ?? "Review the remaining needs and posted plans."}</p>
              </section>
              <section>
                <h3>Water</h3>
                <DepthRange value={level?.depthM ?? null} lo={level?.depthLoM} hi={level?.depthHiM}
                  source={level ? `model + ${level.n} reports` : "no reports"} at={data.now.at} />
                <p>{data.totals.boat} houses need a boat.</p>
                {level?.trendCmH != null && <p>
                  {level.trendCmH > 1 ? "Rising" : level.trendCmH < -1 ? "Falling" : "Steady"} ·
                  {Math.abs(level.trendCmH).toFixed(0)} cm/h
                </p>}
              </section>
              <section>
                <h3>Teams</h3>
                {zone.plans.length ? zone.plans.map(plan => (
                  <p key={plan.id}>
                    <b>{plan.team ?? "A team"}</b> ·
                    {plan.vehicle ?? "vehicle unknown"} · ETA
                    {plan.eta ?? "unknown"}
                    <br />Posted
                    {plan.at} · planned, not rescued yet
                  </p>
                )) : <p>No team has posted a plan.</p>}
                <p>{data.unlocked ? "Your team's plan covers this zone; addresses shown." : "Exact addresses show after your team posts a plan."}</p>
              </section>
            </div>
            <section className="rp-card">
              <div className="rp-card-head">
                <h2>Who first{area ? ` · ${data.subareas.find(block => block.id === area)?.name ?? area}` : ""}</h2>
                {area && <button onClick={() => setArea(null)}>Show all blocks</button>}
                <label className="rp-filter">
                  <input type="checkbox" checked={showClosed} onChange={event => setShowClosed(event.target.checked)} /> Show safe and picked up
                </label>
              </div>
              {rows.map(household => <FamilyPriority key={household.id} household={household} />)}
              <p className="rp-pad rp-honesty">Sorted for attention only: urgent, not answering, unable to walk, deep water, elderly, children. Nobody is assigned.</p>
            </section>
            <section className="rp-warning rp-pad">
              <h3>What we are not sure about</h3>
              <p>{zone.disagree ?? "No conflicting water evidence recorded here. Unreported households and changing access remain unknown."}</p>
              {level && <p>{level.doubtful} doubtful reports retained · likely {level.depthLoM.toFixed(1)}–{level.depthHiM.toFixed(1)} m.</p>}
              <p>Silence is not safety. Posted plans do not confirm arrival or rescue.</p>
            </section>
            <details className="rp-card rp-pad">
              <summary>How we know the water</summary>
              {data.outlook.length > 0 && <Outlook points={data.outlook} />}
              <ul className="v-sources">
                {zone.sources.map((source, index) => <li key={index}>{source.text}</li>)}
              </ul>
              <p>Modelled depth, corrected by dated reports; unknown is not dry.</p>
            </details>
          </div>
          <aside className="rp-stack rp-zone-map">
            <div className="rp-report-map">
              <BoardMap geo={geo} state={board} selected={id} onSelect={zoneId => navigate(`/v/zone/${zoneId}`)}
                houses={[]} focus={focus} focusZoom={16} lang="en" simHour={data.now.atH} simMode="corrected" showPlans />
            </div>
            <details className="rp-card rp-pad">
              <summary>Street blocks and household pins</summary>
              <MiniMap geo={geo} zoneId={id} rows={data.households} onPick={householdId => navigate(`/v/case/${householdId}`)}
                height={400} cells={data.blocks} onCell={setArea} />
            </details>
            <p className="rp-honesty">Blocks follow streets · water at houses · tap a block to filter families.</p>
            <h3>Blocks with families waiting</h3>
            {data.subareas.filter(block => block.open).slice(0, 10).map(block => (
              <button className="rp-chip" key={block.id} onClick={() => setArea(area === block.id ? null : block.id)}>
                {block.name ?? block.id} · {block.open} waiting · {block.urgent} urgent · {block.access}
              </button>
            ))}
          </aside>
        </div>
      )}
    </VShell>
  );
}

export function familyTitle(household: CaseRow): string {
  const people = household.people == null ? "A family" : household.people === 1 ? "A one-person household" : `A family of ${household.people}`;
  const need = household.cannotWalk ? ` · ${household.cannotWalk} cannot walk` : household.children ? ` · ${household.children} children` : household.elderly ? ` · ${household.elderly} elderly` : "";
  return `${people}${need} ${["safe", "evacuated", "atShelter"].includes(household.status) ? "has a recorded safe outcome" : "is waiting for help"}.`;
}

function FamilyPriority({ household }: { household: CaseRow }) {
  return (
    <Link className="rp-family-row" to={`/v/case/${household.id}`}>
      <div>
        <strong>{familyTitle(household)}</strong>
        <span className="rp-pill">{household.id}</span>
        <p>{household.messages} messages · {household.firstHand ? "first-hand" : "reported by others"} · silent {household.hoursSilent} h</p>
        {household.possibleDuplicateOf && <span className="rp-warning">Possible duplicate of {household.possibleDuplicateOf} · kept separate</span>}
      </div>
      <div className="rp-chips">
        <StatusChip r={household} />
        <DepthRange value={household.depth?.m ?? null} source="at house" />
      </div>
    </Link>
  );
}

export function FamilyTable({ rows, onOpen }: { rows: CaseRow[]; onOpen: (id: string) => void }) {
  return (
    <table className="v-table">
      <thead>
        <tr>
          <th>Family</th>
          <th>State</th>
          <th>Who</th>
          <th>Water at the house</th>
          <th>Last heard</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id} onClick={() => onOpen(r.id)}>
            <td>
              <Link to={`/v/case/${r.id}`}>
                <b>{r.id}</b>
              </Link>
              {r.possibleDuplicateOf ? <span className="v2-chip is-amber" title={`May be the same family as ${r.possibleDuplicateOf}`}>maybe = {r.possibleDuplicateOf}</span> : null}
              <div className="v-muted v-small">{r.reportedBy === "family" ? "family reported" : "reported by others only"} · {r.messages} msg</div>
            </td>
            <td>
              <StatusChip r={r} />
            </td>
            <td>
              <Needs r={r} />
            </td>
            <td>
              {r.depth ? <>
                <span className={`v-depth is-${r.depth.m < 0.5 ? "1" : r.depth.m < 1 ? "2" : r.depth.m < 2 ? "3" : "4"}`}>{r.depth.m.toFixed(1)} m</span>
                {r.boat ? <span className="v-boat" title="Water at or above 0.5 m: a boat is suggested">boat</span> : null}
              </> : <span className="v-muted">unknown</span>}
            </td>
            <td className="v-small">
              {r.lastHeard}
              <div className="v-muted">
                {r.hoursSilent < 1 ? "just now" : `${Math.round(r.hoursSilent)} h ago`}
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Outlook({ points }: { points: { inH: number; wetShare: number }[] }) {
  const W = 260, H = 54;
  const x = (h: number) => 6 + (h / 6) * (W - 12);
  const y = (v: number) => H - 8 - v * (H - 18);
  const d = points.map((p, i) => `${i ? "L" : "M"}${x(p.inH).toFixed(1)} ${y(p.wetShare).toFixed(1)}`).join(" ");
  const last = points[points.length - 1];
  return (
    <figure className="v-outlook">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Share of the zone under water, next 6 hours, from the flood model">
        <line x1={6} x2={W - 6} y1={y(0)} y2={y(0)} className="v-axis" />
        <path d={`${d} L${x(6)} ${y(0)} L${x(0)} ${y(0)} Z`} className="v-outlook-area" />
        <path d={d} className="v-outlook-line" />
        <circle cx={x(6)} cy={y(last.wetShare)} r={3} className="v-outlook-end" />
        <text x={6} y={H - 1} className="v-tick">now</text>
        <text x={W - 6} y={H - 1} className="v-tick" textAnchor="end">+6 h</text>
      </svg>
      <figcaption className="v-muted v-small">Under water in the zone, flood model: {(points[0].wetShare * 100).toFixed(0)}% now → {(last.wetShare * 100).toFixed(0)}% in 6 h</figcaption>
    </figure>
  );
}
