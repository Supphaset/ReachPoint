/** Zone card (three questions), AI activity, the time-lapse bar and the volunteer plan box. */
import { useMemo, useState } from "react";
import { v2, depthBand, type Activity, type BoardState, type Timeline, type ZoneView } from "./api";

const fmt = (n: number) => n.toLocaleString("en-US");
const rng = (r: [number, number] | null | undefined) => (!r ? "—" : r[0] === r[1] ? fmt(r[0]) : `${fmt(r[0])}–${fmt(r[1])}`);

function timeOf(state: BoardState | null, h: number | null): string {
  if (!state || h === null) return "";
  const d = state.atH - h;
  if (d < 1) return `${Math.max(1, Math.round(d * 60))} min ago`;
  if (d < 24) return `${Math.round(d)} h ago`;
  return `${Math.round(d / 24)} d ago`;
}

export function ZoneCard({ zone, state }: { zone: ZoneView | null; state: BoardState | null }) {
  if (!zone) return <div className="v2-card v2-empty">Tap a zone on the map.</div>;
  const l = zone.level;
  const flooded = zone.people.likelyFlooded;
  const share = flooded ? (zone.people.reported[0] / ((flooded[0] + flooded[1]) / 2)) * 100 : 0;
  return (
    <article className="v2-card v2-zone" aria-label={`Zone ${zone.id}`}>
      <header className="v2-zone-head">
        <span className={`v2-swatch is-${depthBand(l?.depthM)}`} aria-hidden="true" />
        <h2>Zone {zone.id}</h2>
        <span className="v2-muted">{zone.district}</span>
        <span className="v2-chips">
          {zone.people.urgent ? <span className="v2-chip is-red">{zone.people.urgent} urgent</span> : null}
          {zone.status.lostContact ? <span className="v2-chip is-amber">{zone.status.lostContact} lost contact</span> : null}
          {zone.status.safe + zone.status.evacuated ? <span className="v2-chip is-green">{zone.status.safe + zone.status.evacuated} safe or evacuated</span> : null}
          {zone.quiet ? <span className="v2-chip is-amber">Quiet zone</span> : null}
          {zone.predicted ? <span className="v2-chip is-amber">Water predicted ≤ 6 h</span> : null}
        </span>
      </header>
      <div className="v2-zone-grid">
        <section>
          <h3>① How many people</h3>
          <dl className="v2-kv">
            <dt>Live here <small>estimate · WorldPop + buildings</small></dt>
            <dd>{rng(zone.people.everyone)}</dd>
            <dt>Likely in flooded area <small>estimate · flood model</small></dt>
            <dd>{rng(flooded)}</dd>
            <dt>Reported so far <small>{zone.people.households} households, duplicates merged</small></dt>
            <dd>{rng(zone.people.reported)}</dd>
          </dl>
          <div className="v2-bar" aria-label="Reported people compared with likely flooded">
            <i style={{ width: `${Math.min(100, Math.max(1, share))}%` }} />
          </div>
          <p className="v2-muted">{share < 5 ? "Most people here haven't reported. Silence isn't safety." : `${share.toFixed(0)}% of the likely flooded have been heard from.`}</p>
          <dl className="v2-kv is-small">
            <dt>Elderly</dt><dd>{zone.people.elderly}</dd>
            <dt>Children</dt><dd>{zone.people.children}</dd>
            <dt>Can't walk</dt><dd>{zone.people.cannotWalk}</dd>
          </dl>
        </section>
        <section>
          <h3>② How deep is the water</h3>
          {l ? (
            <div className="v2-level">
              <span className="v2-level-big">≈ {l.depthM.toFixed(1)} m</span>
              <span>likely {l.depthLoM.toFixed(1)}–{l.depthHiM.toFixed(1)} m{l.trendCmH !== null ? ` · ${l.trendCmH > 1 ? "rising" : l.trendCmH < -1 ? "falling" : "steady"} ${Math.abs(l.trendCmH).toFixed(0)} cm/h` : ""}</span>
              <span className="v2-muted">flood model corrected by {l.n} recent reports · certainty {(l.certainty * 100).toFixed(0)}%</span>
            </div>
          ) : (
            <div className="v2-level is-unknown"><span className="v2-level-big">Unknown</span><span className="v2-muted">No reports yet. Unknown, not dry.</span></div>
          )}
          <ul className="v2-sources">
            {zone.sources.map((s, i) => (
              <li key={i} className={`is-${s.kind}`}>
                <span>{s.text}{s.labels ? ` (${s.labels.consistent} fit the reports around them, ${s.labels.doubtful} doubtful)` : ""}{s.reconstructed ? " · reconstructed bulletin" : ""}</span>
                <time>{timeOf(state, s.lastH)}</time>
              </li>
            ))}
          </ul>
          {zone.disagree ? <p className="v2-note">{zone.disagree}</p> : null}
        </section>
        <section>
          <h3>③ Who plans to help</h3>
          {zone.plans.length ? (
            zone.plans.slice(-3).map((p) => (
              <div key={p.id} className="v2-plan">
                <b>{p.team ?? "A team"}</b>
                <span>{[p.eta && `≈ ${p.eta}`, p.vehicle, p.seats && `${p.seats} seats`, p.offers].filter(Boolean).join(" · ")}</span>
                <span className="v2-muted">Posted {p.at}{p.told !== undefined ? ` · ${p.told} households told` : ""}</span>
              </div>
            ))
          ) : (
            <p className="v2-muted">No team has posted a plan for this zone.</p>
          )}
          {zone.gap ? <p className="v2-gap">{zone.gap}</p> : null}
        </section>
      </div>
      <footer className="v2-summary">
        <span className="v2-label">AI summary</span>
        <p>{zone.summary}</p>
      </footer>
    </article>
  );
}

export function ActivityList({ items }: { items: Activity[] }) {
  return (
    <ol className="v2-activity" aria-label="AI activity">
      {items.slice(0, 24).map((a, i) => (
        <li key={`${a.atH}-${i}`}>
          <time>{a.at}</time>
          <b className={`v2-agent is-${a.agent.toLowerCase()}`}>{a.agent}</b>
          <span>{a.text}<small>{a.tool}</small></span>
        </li>
      ))}
    </ol>
  );
}

export function TimeBar({ timeline, viewH, nowH, onChange, playing, onPlay }: {
  timeline: Timeline | null;
  viewH: number;
  nowH: number;
  onChange: (h: number) => void;
  playing: boolean;
  onPlay: () => void;
}) {
  const stop = useMemo(() => {
    if (!timeline) return null;
    return [...timeline.stops].reverse().find((s) => s.atH <= viewH + 0.01) ?? timeline.stops[0];
  }, [timeline, viewH]);
  if (!timeline) return null;
  const H = timeline.hours;
  const W = 600, CH = 64;
  const x = (h: number) => (h / H) * W;
  const s = timeline.series;
  const maxHh = Math.max(...s.map((p) => p.households), 1);
  const hhPath = s.map((p, i) => `${i ? "L" : "M"}${x(p.atH).toFixed(1)} ${(CH - (p.households / maxHh) * (CH - 6)).toFixed(1)}`).join(" ");
  const cPath = s.map((p, i) => `${i ? "L" : "M"}${x(p.atH).toFixed(1)} ${(CH - p.certainty * (CH - 6)).toFixed(1)}`).join(" ");
  const g = s.filter((p) => p.gaugeM !== null);
  const gPath = g.map((p, i) => `${i ? "L" : "M"}${x(p.atH).toFixed(1)} ${(CH - ((p.gaugeM ?? 0) / 10.5) * (CH - 6)).toFixed(1)}`).join(" ");
  const bankY = CH - (7.4 / 10.5) * (CH - 6);
  return (
    <div className="v2-timebar">
      <div className="v2-timebar-head">
        <button type="button" className="v2-play" onClick={onPlay}>{playing ? "❚❚ Pause" : "▶ Play the flood"}</button>
        <div>
          <b>{stop?.caption}</b>
        </div>
      </div>
      <svg viewBox={`0 0 ${W} ${CH + 14}`} className="v2-chart" role="img" aria-label="Households known, map certainty and river gauge over time">
        <rect x={x(nowH)} y={0} width={Math.max(0, W - x(nowH))} height={CH} className="v2-chart-future" />
        <line x1={0} x2={W} y1={bankY} y2={bankY} className="v2-chart-bank" />
        <text x={4} y={bankY - 3} className="v2-chart-label">canal bank 7.4 m</text>
        <path d={gPath} className="v2-chart-gauge" />
        <path d={`${hhPath} L${W} ${CH} L0 ${CH} Z`} className="v2-chart-area" />
        <path d={hhPath} className="v2-chart-hh" />
        <path d={cPath} className="v2-chart-cert" />
        {timeline.stops.map((st) => (
          <line key={st.atH} x1={x(st.atH)} x2={x(st.atH)} y1={CH} y2={CH + 6} className="v2-chart-tick" />
        ))}
        <line x1={x(viewH)} x2={x(viewH)} y1={0} y2={CH} className="v2-chart-now" />
        <text x={2} y={CH + 13} className="v2-chart-label">21 Nov</text>
        <text x={x(100)} y={CH + 13} className="v2-chart-label" textAnchor="middle">25 Nov peak</text>
        <text x={W - 2} y={CH + 13} className="v2-chart-label" textAnchor="end">28 Nov</text>
      </svg>
      <input
        id="v2-time"
        type="range"
        min={0}
        max={H}
        step={1}
        value={Math.min(viewH, nowH)}
        onChange={(e) => onChange(Math.min(Number(e.target.value), nowH))}
        aria-label="Time-lapse"
      />
      <div className="v2-legend">
        <span><i className="is-hh" /> households known</span>
        <span><i className="is-cert" /> map certainty</span>
        <span><i className="is-gauge" /> river gauge X.44 (real)</span>
        <span className="v2-muted">Shaded: after the demo's "now"</span>
      </div>
    </div>
  );
}

export function PlanBox({ onPosted }: { onPosted: () => void }) {
  const [text, setText] = useState("");
  const [note, setNote] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  return (
    <form
      className="v2-planbox"
      onSubmit={async (e) => {
        e.preventDefault();
        if (!text.trim()) return;
        setBusy(true);
        try {
          const r = await v2.plan(text);
          const p = r.plan;
          setNote(`Read as: ${p.team ?? "team"} · ${p.vehicle ?? "?"}${p.seats ? ` · ${p.seats} seats` : ""} · ${(p.zones ?? []).join(" → ")}${p.eta ? ` · ≈ ${p.eta}` : ""} · ${p.offers ?? ""}. ${p.told ?? 0} households told.`);
          setText("");
          onPosted();
        } finally {
          setBusy(false);
        }
      }}
    >
      <label htmlFor="v2-plan">Volunteer? Post where you plan to go, in one line</label>
      <div>
        <input id="v2-plan" value={text} onChange={(e) => setText(e.target.value)} placeholder="เรือเรา 8 ที่ จะเข้า B-3 ราวบ่ายสอง แล้วต่อ B-5 อพยพ" />
        <button type="submit" disabled={busy || !text.trim()}>Post plan</button>
      </div>
      {note ? <p className="v2-muted">{note}</p> : null}
    </form>
  );
}
