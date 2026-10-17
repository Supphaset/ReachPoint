/** One zone in depth: the water and its outlook, the AI briefing, families by priority, and who plans to come. */
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { vol, type CaseRow } from "../api";
import { Depth, MiniMap, Needs, StatusChip, VShell, useGeo, useLive, useTeam } from "./shared";

export function ZonePage() {
  const { id = "" } = useParams();
  const [team] = useTeam();
  const { data, error } = useLive(() => vol.zone(id, team), [id, team]);
  const geo = useGeo();
  const nav = useNavigate();
  const [showClosed, setShowClosed] = useState(false);
  const [area, setArea] = useState<string | null>(() => decodeURIComponent(window.location.hash.slice(1)) || null);
  const z = data?.zone;
  const l = z?.level;
  const inArea = area ? new Set(data?.subareas.find((c) => c.id === area)?.households ?? []) : null;
  const rows = (data?.households ?? []).filter((r) => (showClosed || !["safe", "evacuated", "nobodyThere", "atShelter"].includes(r.status))
    && (!inArea || inArea.has(r.id)));
  return (
    <VShell title={`Zone ${id}${z?.label ? ` · ${z.label}` : ""}`} sub={z?.district ?? undefined} at={data?.now.at}>
      {error ? <p className="v2-error">Couldn't load zone {id}: {error}</p> : null}
      {data ? (
        <>
          <section className="v-brief v2-card v-pad" aria-label="Briefing for teams">
            <span className="v-label">Briefing for teams · from the numbers on this page</span>
            <p>{data.briefing}</p>
            <div className="v-brief-actions">
              <Link to={`/v/plan?zones=${id}`} className="v-btn">Plan a trip to {id}</Link>
              {!data.unlocked ? <span className="v-muted v-small">Exact addresses show after your team posts a plan for this zone.</span>
                : <span className="v2-chip is-green">Your team's plan covers {id}: addresses shown</span>}
            </div>
          </section>
          <div className="v-grid3">
            <section className="v2-card v-pad">
              <h2 className="v-h2">Water</h2>
              {l ? (
                <>
                  <p className="v-big"><Depth m={l.depthM} /> <span className="v-muted">likely {l.depthLoM.toFixed(1)}–{l.depthHiM.toFixed(1)} m</span></p>
                  <p className="v-muted v-small">{l.trendCmH !== null ? `${l.trendCmH > 1 ? "Rising" : l.trendCmH < -1 ? "Falling" : "Steady"} ${Math.abs(l.trendCmH).toFixed(0)} cm/h · ` : ""}model corrected by {l.n} recent reports · certainty {(l.certainty * 100).toFixed(0)}%</p>
                </>
              ) : <p className="v-muted">Unknown: no reports yet. Unknown is not dry.</p>}
              <Outlook points={data.outlook} />
              <ul className="v-sources">
                {z!.sources.map((s, i) => <li key={i} className={`is-${s.kind}`}>{s.text}</li>)}
              </ul>
              {z!.disagree ? <p className="v-note">{z!.disagree}</p> : null}
            </section>
            <section className="v2-card v-pad">
              <h2 className="v-h2">People</h2>
              <dl className="v2-kv">
                <dt>Families still at home</dt><dd>{data.totals.open}</dd>
                <dt>People in them</dt><dd>{data.totals.people}</dd>
                <dt>Need a boat (water ≥ 0.5 m at the house)</dt><dd>{data.totals.boat}</dd>
                <dt>Urgent</dt><dd className="is-red">{z!.people.urgent}</dd>
                <dt>Can't walk</dt><dd>{z!.people.cannotWalk}</dd>
                <dt>Elderly · children</dt><dd>{z!.people.elderly} · {z!.people.children}</dd>
                <dt>Safe, evacuated or picked up</dt><dd>{data.totals.closed}</dd>
                <dt>Likely in flooded area <small>estimate</small></dt><dd>{z!.people.likelyFlooded ? `${z!.people.likelyFlooded[0].toLocaleString()}–${z!.people.likelyFlooded[1].toLocaleString()}` : "–"}</dd>
              </dl>
              <p className="v-muted v-small">Most people in a flood never send a message. Silence isn't safety.</p>
            </section>
            <section className="v2-card v-pad">
              <h2 className="v-h2">Teams planning to come</h2>
              {z!.plans.length ? z!.plans.map((p) => (
                <div key={p.id} className="v2-plan">
                  <b>{p.team ?? "A team"}</b>
                  <span>{[p.eta && `≈ ${p.eta}`, p.vehicle, p.seats && `${p.seats} seats`, p.offers].filter(Boolean).join(" · ")}</span>
                  <span className="v-muted">Posted {p.at}{p.told !== undefined ? ` · ${p.told} families told` : ""}</span>
                </div>
              )) : <p className="v-muted">No team has posted a plan for this zone.</p>}
              {z!.gap ? <p className="v2-gap">{z!.gap}</p> : null}
            </section>
          </div>
          <div className="v-split">
            <section className="v-tablewrap" aria-label="Families by priority">
              <div className="v-tablehead">
                <h2 className="v-h2">Families by priority{area ? <> in {data.subareas.find((c) => c.id === area)?.name ?? area} <button type="button" className="v-linkbtn" onClick={() => setArea(null)}>show all</button></> : null}</h2>
                <label className="v-small"><input type="checkbox" checked={showClosed} onChange={(e) => setShowClosed(e.target.checked)} /> show safe and picked up</label>
              </div>
              <FamilyTable rows={rows} onOpen={(hid) => nav(`/v/case/${hid}`)} />
              <p className="v-muted v-small">Sorted for attention only: urgent, then not answering, can't walk, deep water, elderly, children. Nobody is assigned.</p>
            </section>
            <section className="v2-card v-pad">
              <h2 className="v-h2">Map of zone {id}</h2>
              <MiniMap geo={geo} zoneId={id} rows={data.households} onPick={(hid) => nav(`/v/case/${hid}`)} height={460}
                cells={data.blocks} onCell={(cid) => setArea(cid)} />
              <p className="v-legend-access"><i className="is-walk" />can walk out <i className="is-truck" />high truck <i className="is-boat" />boat needed
                <span className="v-muted"> · blocks follow streets; water now at their houses. Tap one to list its families.</span></p>
              <h3 className="v-h2">Blocks with families waiting</h3>
              <ol className="v-hot">
                {data.subareas.filter((c) => c.open).slice(0, 10).map((c) => (
                  <li key={c.id} className={area === c.id ? "is-on" : ""}>
                    <button type="button" className="v-linkbtn" onClick={() => setArea(area === c.id ? null : c.id)}><b>{c.name ?? c.id}</b></button>
                    <span className="v-muted v-small">{c.id}</span>
                    <span className="v-small">{c.open} waiting{c.urgent ? ` · ${c.urgent} urgent` : ""}{c.cannotWalk ? ` · ${c.cannotWalk} can't walk` : ""}</span>
                    <span className={`v-access is-${c.access}`}>{c.access === "walk" ? "walk" : c.access === "truck" ? "truck" : c.access === "boat" ? "boat" : "?"}</span>
                  </li>
                ))}
              </ol>
            </section>
          </div>
        </>
      ) : null}
    </VShell>
  );
}

export function FamilyTable({ rows, onOpen }: { rows: CaseRow[]; onOpen: (id: string) => void }) {
  return (
    <table className="v-table">
      <thead>
        <tr><th>Family</th><th>State</th><th>Who</th><th>Water at the house</th><th>Last heard</th></tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id} onClick={() => onOpen(r.id)}>
            <td><Link to={`/v/case/${r.id}`}><b>{r.id}</b></Link>{r.possibleDuplicateOf ? <span className="v2-chip is-amber" title={`May be the same family as ${r.possibleDuplicateOf}`}>maybe = {r.possibleDuplicateOf}</span> : null}
              <div className="v-muted v-small">{r.reportedBy === "family" ? "family reported" : "reported by others only"} · {r.messages} msg</div></td>
            <td><StatusChip r={r} /></td>
            <td><Needs r={r} /></td>
            <td>{r.depth ? <><span className={`v-depth is-${r.depth.m < 0.5 ? "1" : r.depth.m < 1 ? "2" : r.depth.m < 2 ? "3" : "4"}`}>{r.depth.m.toFixed(1)} m</span>{r.boat ? <span className="v-boat" title="Water at or above 0.5 m: a boat is suggested">boat</span> : null}</> : <span className="v-muted">unknown</span>}</td>
            <td className="v-small">{r.lastHeard}<div className="v-muted">{r.hoursSilent < 1 ? "just now" : `${Math.round(r.hoursSilent)} h ago`}</div></td>
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
