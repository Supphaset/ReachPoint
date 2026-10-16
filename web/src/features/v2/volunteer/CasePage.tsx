/** One family's whole story: every message with its words, why it was merged, the water at the house, neighbours,
 * what ReachPoint sent them, and the one tap a team can make. */
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { vol, type CaseView } from "../api";
import { FactChips } from "./FeedPage";
import { Depth, Needs, StatusChip, VShell, useLive, useTeam } from "./shared";

const SENT: Record<string, string> = {
  check: "Safety check", morning: "Morning check", earlyWarning: "Early warning", rain: "Rain alert", river: "River alert",
  askBack: "Follow-up question", quiet: "Asked about neighbours", lostCall: "AI voice call", planUpdate: "Team coming",
  pickedUp: "Picked up", nobodyThere: "Nobody there",
};

export function CasePage() {
  const { id = "" } = useParams();
  const [team] = useTeam();
  const { data, error, reload } = useLive(() => vol.case(id, team), [id, team]);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);
  const h = data?.household;
  const tap = async (kind: "pickedUp" | "nobodyThere") => {
    if (!team) return;
    setBusy(true);
    try {
      await vol.outcome(id, kind, team);
      setDone(kind === "pickedUp" ? "Recorded: picked up. The family's phone has been told." : "Recorded: nobody there. The family has been asked where they are.");
      reload();
    } finally {
      setBusy(false);
    }
  };
  return (
    <VShell
      title={`Family ${id}`}
      sub={h ? <>Zone <Link to={`/v/zone/${h.zoneId}`}>{h.zoneId}</Link>{data?.zone?.district ? ` · ${data.zone.district}` : ""} · {h.reportedBy === "family" ? "the family reported themselves" : "reported by others only"}</> : undefined}
      at={data?.now.at}
    >
      {error ? <p className="v2-error">Couldn't load this family: {error}</p> : null}
      {data && h ? (
        <>
          <section className="v-casehead v2-card v-pad">
            <div className="v-casehead-main">
              <StatusChip r={h} />
              <Needs r={h} />
              <span>Water here <Depth m={data.depth?.m} lo={data.depth?.lo} hi={data.depth?.hi} />{h.boat ? <span className="v-boat">boat</span> : null}</span>
              <span className="v-muted v-small">last heard {data.contact.lastHeard}</span>
            </div>
            <div className="v-address">
              {data.unlocked ? <><span className="v-label">Address</span> <b>{data.address ?? "not given in words; use the map pin"}</b></>
                : <span className="v-muted v-small">Exact address hidden. It shows to teams whose posted plan covers zone {h.zoneId}. <Link to={`/v/plan?zones=${h.zoneId}`}>Post a plan</Link></span>}
            </div>
            <div className="v-tap">
              {h.outcome ? (
                <p><b>{h.outcome.kind === "pickedUp" ? "Picked up" : "Nobody there"}</b> · {h.outcome.team} · {h.outcome.at}</p>
              ) : team ? (
                <>
                  <span className="v-small">After you visit:</span>
                  <button type="button" className="v-btn is-go" disabled={busy} onClick={() => tap("pickedUp")}>We picked them up</button>
                  <button type="button" className="v-btn" disabled={busy} onClick={() => tap("nobodyThere")}>Nobody there</button>
                </>
              ) : <span className="v-muted v-small">Set your team name (top right) to record a visit.</span>}
              {done ? <p className="v-ok" role="status">{done}</p> : null}
            </div>
          </section>

          <div className="v-split">
            <section aria-label="Messages about this family">
              <h2 className="v-h2">Everything we heard ({data.story.length} messages)</h2>
              <ol className="v-story">
                {data.story.map((s) => (
                  <li key={s.id}>
                    <div className="v-feed-head">
                      <time>{s.at}</time>
                      <span className="v-feed-src">{s.source} · {s.channel}</span>
                      {s.depth?.label === "doubtful" ? <span className="v2-chip is-amber">Doubtful</span> : null}
                    </div>
                    <p className="v-feed-text">{s.text}</p>
                    <FactChips facts={s.facts} />
                    <p className="v-feed-did"><b>Why it's this family:</b> {s.how ?? "–"}
                      {s.depth ? <> · <b>Water said</b> {s.depth.lo.toFixed(1)}–{s.depth.hi.toFixed(1)} m, model then {s.depth.model.toFixed(1)} m ({s.depth.label})</> : null}</p>
                  </li>
                ))}
              </ol>
            </section>
            <div className="v-side">
              <section className="v2-card v-pad">
                <h2 className="v-h2">Water at the house</h2>
                <DepthChart c={data} />
                {data.depth ? <p className="v-small">Now about <b>{data.depth.m.toFixed(1)} m</b> (likely {data.depth.lo.toFixed(1)}–{data.depth.hi.toFixed(1)}). The flood model alone says {data.depth.model.toFixed(1)} m; {data.depth.reports} nearby reports correct it.</p> : null}
                {data.doubtfulWhy ? <p className="v-note">{data.doubtfulWhy}</p> : null}
              </section>
              <section className="v2-card v-pad">
                <h2 className="v-h2">Neighbours</h2>
                <Compass c={data} />
                {data.neighbours.length ? (
                  <ul className="v-list">
                    {data.neighbours.map((n, i) => (
                      <li key={i}>
                        {n.from === id ? <>This family reported <Link to={`/v/case/${n.to}`}>{n.to}</Link>, {n.side === "unknown" ? "direction not given" : `to the ${n.side}`}</>
                          : <><Link to={`/v/case/${n.from}`}>{n.from}</Link> reported this house, {n.side === "unknown" ? "direction not given" : `to their ${n.side}`}</>}
                        {" "}<span className="v-muted">“{n.quote}”</span> {n.sure ? null : <span className="v2-chip is-amber">not sure</span>} {n.known ? <span className="v2-chip">already known</span> : <span className="v2-chip is-blue">new house</span>}
                      </li>
                    ))}
                  </ul>
                ) : <p className="v-muted v-small">No neighbour reports link to this house.</p>}
                {data.possibleDuplicates.length ? <p className="v-small">May be the same family as {data.possibleDuplicates.map((d) => <Link key={d} to={`/v/case/${d}`}>{d} </Link>)}: kept apart, counted as a range.</p> : null}
              </section>
              <section className="v2-card v-pad">
                <h2 className="v-h2">What ReachPoint sent them</h2>
                <p className="v-muted v-small">{data.contact.replies} replies · {data.contact.unanswered} checks unanswered</p>
                <ol className="v-list">
                  {data.contact.sent.slice(-8).map((o, i) => (
                    <li key={i}><time className="v-muted v-small">{o.at}</time> <b>{SENT[o.kind] ?? o.kind}</b> <span className="v-small">{o.text.split("\n")[0]}</span></li>
                  ))}
                </ol>
              </section>
              <section className="v2-card v-pad">
                <h2 className="v-h2">Teams planning to come</h2>
                {data.plans.length ? data.plans.map((p) => <p key={p.id} className="v-small"><b>{p.team ?? "A team"}</b> {[p.eta && `≈ ${p.eta}`, p.vehicle, p.offers].filter(Boolean).join(" · ")}</p>)
                  : <p className="v-muted v-small">Nobody has posted a plan for zone {h.zoneId}.</p>}
              </section>
            </div>
          </div>
        </>
      ) : null}
    </VShell>
  );
}

/** The water at the house over time: the flood model as a line, what people said as bars. */
function DepthChart({ c }: { c: CaseView }) {
  const W = 320, H = 130, L = 26, B = 18;
  const pts = c.depthSeries;
  if (!pts.length) return null;
  const maxH = Math.max(c.now.atH, 1);
  const maxD = Math.max(1, ...pts.map((p) => p[1]), ...c.depthReports.map((r) => r[2]), c.depth?.hi ?? 0);
  const x = (h: number) => L + (h / maxH) * (W - L - 6);
  const y = (d: number) => H - B - (d / maxD) * (H - B - 22);
  const ticks = [0, maxD / 2, maxD].map((v) => Math.round(v * 10) / 10);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="v-chart" role="img" aria-label="Water depth at the house over time">
      {ticks.map((t) => (
        <g key={t}><line x1={L} x2={W - 6} y1={y(t)} y2={y(t)} className="v-grid" /><text x={L - 4} y={y(t) + 3} className="v-tick" textAnchor="end">{t} m</text></g>
      ))}
      <path d={pts.map((p, i) => `${i ? "L" : "M"}${x(p[0]).toFixed(1)} ${y(p[1]).toFixed(1)}`).join(" ")} className="v-chart-model" />
      {c.depthReports.map((r, i) => (
        <rect key={i} x={x(r[0]) - 2.5} y={y(r[2])} width={5} height={Math.max(2, y(r[1]) - y(r[2]))} className={`v-chart-rep ${r[3] === "doubtful" ? "is-doubtful" : ""}`} />
      ))}
      {c.depth ? <circle cx={x(c.now.atH)} cy={y(c.depth.m)} r={4} className="v-chart-now" /> : null}
      <text x={L} y={H - 4} className="v-tick">21 Nov</text>
      <text x={W - 6} y={H - 4} className="v-tick" textAnchor="end">now</text>
      <g className="v-chart-key">
        <line x1={W - 150} x2={W - 136} y1={10} y2={10} className="v-chart-model" /><text x={W - 132} y={13} className="v-tick">model</text>
        <rect x={W - 90} y={6} width={5} height={8} className="v-chart-rep" /><text x={W - 82} y={13} className="v-tick">people said</text>
      </g>
    </svg>
  );
}

/** The house's outline with the compass, and an arrow to each neighbour report. */
function Compass({ c }: { c: CaseView }) {
  const S = 150, R = 54;
  const dir: Record<string, [number, number]> = { north: [0, -1], south: [0, 1], east: [1, 0], west: [-1, 0] };
  const o = c.building?.outline ?? [];
  const xs = o.map((p) => p[0]);
  const ys = o.map((p) => p[1]);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2;
  const cy = (Math.min(...ys) + Math.max(...ys)) / 2;
  const span = Math.max(Math.max(...xs) - Math.min(...xs), (Math.max(...ys) - Math.min(...ys)) / Math.cos((cy * Math.PI) / 180), 1e-5);
  const k = 34 / span;
  const outline = o.length ? o.map((p, i) => `${i ? "L" : "M"}${(S / 2 + (p[0] - cx) * k).toFixed(1)} ${(S / 2 - ((p[1] - cy) / Math.cos((cy * Math.PI) / 180)) * k).toFixed(1)}`).join(" ") + "Z" : null;
  const sides = new Set(c.neighbours.map((n) => n.side));
  return (
    <svg viewBox={`0 0 ${S} ${S}`} className="v-compass" role="img" aria-label="This house and the directions of neighbour reports">
      {(["north", "east", "south", "west"] as const).map((d) => {
        const [dx, dy] = dir[d];
        return (
          <g key={d}>
            <line x1={S / 2 + dx * 26} y1={S / 2 + dy * 26} x2={S / 2 + dx * R} y2={S / 2 + dy * R} className={`v-compass-ray ${sides.has(d) ? "is-on" : ""}`} />
            <text x={S / 2 + dx * (R + 10)} y={S / 2 + dy * (R + 10) + 4} textAnchor="middle" className={`v-tick ${sides.has(d) ? "is-on" : ""}`}>{d[0].toUpperCase()}</text>
          </g>
        );
      })}
      {outline ? <path d={outline} className="v-compass-house" /> : <rect x={S / 2 - 12} y={S / 2 - 12} width={24} height={24} className="v-compass-house" />}
    </svg>
  );
}
