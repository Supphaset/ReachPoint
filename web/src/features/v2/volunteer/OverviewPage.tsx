/** City overview: zones ranked by how much help is missing, not just by how deep the water is. */
import { Link, useNavigate } from "react-router-dom";
import { vol } from "../api";
import { Depth, MiniMap, VShell, useGeo, useLive } from "./shared";

export function OverviewPage() {
  const { data, error } = useLive(() => vol.overview(), []);
  const geo = useGeo();
  const nav = useNavigate();
  const o = data?.overall;
  const top = data?.zones[0];
  return (
    <VShell
      title="Where help is missing"
      sub="Zones ranked by families still waiting, weighted by urgency, lost contact and people who can't walk. A zone with a team on the way counts half."
      at={data?.at}
    >
      {error ? <p className="v2-error">Couldn't reach the server: {error}</p> : null}
      {o ? (
        <div className="v-stats">
          <div><b>{o.households.toLocaleString()}</b><span>families known · {o.duplicatesMerged} duplicate messages merged</span></div>
          <div><b>{data!.zones.reduce((a, z) => a + z.open, 0)}</b><span>still waiting at home</span></div>
          <div><b className="is-red">{data!.zones.reduce((a, z) => a + z.urgent, 0)}</b><span>urgent</span></div>
          <div><b className="is-amber">{data!.zones.reduce((a, z) => a + z.lostContact, 0)}</b><span>not answering</span></div>
          <div><b>{data!.zones.filter((z) => z.open && !z.plans).length}</b><span>zones with families and no team planned</span></div>
        </div>
      ) : null}
      {top ? (
        <p className="v-callout">
          <b>Most help missing: zone {top.id} · {top.label}</b> ({top.district}). {top.open} families waiting
          {top.urgent ? `, ${top.urgent} urgent` : ""}{top.cannotWalk ? `, ${top.cannotWalk} people who can't walk` : ""}.{" "}
          {top.plans ? `${top.plans} team plan${top.plans > 1 ? "s" : ""} posted.` : "No team has posted a plan."}{" "}
          <Link to={`/v/zone/${top.id}`}>Open zone {top.id} →</Link>
        </p>
      ) : null}
      {data?.hotspots.length ? (
        <section className="v2-card v-pad" aria-label="Smaller areas with the most help missing">
          <h2 className="v-h2">Hotspots: smaller areas (about 350 m) with the most help missing</h2>
          <ol className="v-hot">
            {data.hotspots.slice(0, 8).map((c) => (
              <li key={c.id}>
                <Link to={`/v/zone/${c.zoneId}#${encodeURIComponent(c.id)}`}><b>{c.name ?? c.id}</b></Link>
                <span className="v-muted v-small">{c.id}</span>
                <span className="v-small">{c.open} waiting{c.urgent ? <> · <b className="is-red">{c.urgent} urgent</b></> : null}{c.cannotWalk ? ` · ${c.cannotWalk} can't walk` : ""}</span>
                <Depth m={c.depthM} />
              </li>
            ))}
          </ol>
        </section>
      ) : null}
      <div className="v-split">
        <div className="v-tablewrap">
          <table className="v-table">
            <thead>
              <tr>
                <th>Zone</th><th className="num">Waiting</th><th className="num">Urgent</th><th className="num">Not answering</th>
                <th className="num">Can't walk</th><th className="num">Need a boat</th><th>Water</th><th>Teams</th>
              </tr>
            </thead>
            <tbody>
              {(data?.zones ?? []).map((z, i) => (
                <tr key={z.id} onClick={() => nav(`/v/zone/${z.id}`)} className={i < 3 && z.score > 0 ? "is-top" : ""}>
                  <td><Link to={`/v/zone/${z.id}`}><b>{z.id}</b></Link> {z.label} <span className="v-muted v-small">{z.district}</span>
                    {z.quiet ? <span className="v2-chip is-amber">quiet</span> : null}
                    {z.predicted ? <span className="v2-chip is-amber">water ≤ 6 h</span> : null}</td>
                  <td className="num">{z.open}</td>
                  <td className="num">{z.urgent ? <b className="is-red">{z.urgent}</b> : "–"}</td>
                  <td className="num">{z.lostContact ? <b className="is-amber">{z.lostContact}</b> : "–"}</td>
                  <td className="num">{z.cannotWalk || "–"}</td>
                  <td className="num">{z.boat || "–"}</td>
                  <td><Depth m={z.depthM} /></td>
                  <td>{z.plans ? <span className="v2-chip is-green">{z.plans} planned</span> : z.open ? <span className="v2-chip is-red">none</span> : <span className="v-muted">–</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <section className="v2-card v-pad" aria-label="Map">
          <h2 className="v-h2">Families waiting</h2>
          <p className="v-muted v-small">Red urgent · amber not answering · white waiting · green safe or picked up. Tap a dot.</p>
          <MiniMap
            geo={geo}
            rows={data?.points ?? []}
            height={480}
            onPick={(id) => nav(`/v/case/${id}`)}
            onZone={(id) => nav(`/v/zone/${id}`)}
            shelters={data?.shelters}
            zoneTone={Object.fromEntries((data?.zones ?? []).map((z, i) => [z.id, i < 3 && z.score > 0 ? "is-gap-high" : z.open ? "is-gap-mid" : ""]))}
          />
          <p className="v-muted v-small">Shaded zones: the three with the most help missing. Green squares: shelters.</p>
          <h2 className="v-h2">Shelters</h2>
          <table className="v-table is-compact">
            <thead><tr><th>Shelter</th><th className="num">Checked in</th><th className="num">On the way</th><th className="num">Room for</th></tr></thead>
            <tbody>
              {(data?.shelters ?? []).map((s) => (
                <tr key={s.id}><td><b>{s.name}</b> <span className="v-muted v-small">{s.kind}</span></td><td className="num">{s.people}</td><td className="num">{s.coming || "–"}</td><td className="num">≈ {s.capacity}</td></tr>
              ))}
            </tbody>
          </table>
          <p className="v-muted v-small">Candidate shelters: real public buildings from OpenStreetMap that stay dry in the flood model all week and have no deep-water report nearby. Not the official 2025 list; room is estimated from the building size.</p>
        </section>
      </div>
    </VShell>
  );
}
