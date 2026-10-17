import { useT } from "../ui/lang";
/** Plan a trip: pick zones, see the families and their needs, the water on the way and who else is going; then post
 * the plan in one line. Information to decide with, not an assignment. */
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { v2, vol } from "../api";
import { Depth, VShell, useLive, useTeam } from "./shared";
import { FamilyTable } from "./ZonePage";

export function TripPage() {
  const translate = useT();
  const [params, setParams] = useSearchParams();
  const [team, setTeam] = useTeam();
  const nav = useNavigate();
  const picked = useMemo(() => (params.get("zones") ?? "").split(",").filter(Boolean), [params]);
  const over = useLive(() => vol.overview(), []);
  const trip = useLive(() => (picked.length ? vol.trip(picked, team) : Promise.resolve(null)), [picked.join(","), team]);
  const [vehicle, setVehicle] = useState("boat");
  const [seats, setSeats] = useState(8);
  const [eta, setEta] = useState("14:00");
  const [line, setLine] = useState("");
  const [edited, setEdited] = useState(false);
  const [posted, setPosted] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (edited) return;
    const name = team || translate("ทีมของเรา", "Our team");
    setLine(picked.length ? translate(`${name} ${vehicle} ${seats} ที่ จะเข้า ${picked.join(" แล้วต่อ ")} ราว ${eta} อพยพ`, `${name}: ${vehicle}, ${seats} seats, ${picked.join(" then ")}, around ${eta}, evacuation`) : "");
  }, [team, vehicle, seats, eta, picked, edited, translate]);

  const toggle = (z: string) => {
    const next = picked.includes(z) ? picked.filter((x) => x !== z) : [...picked, z].slice(0, 4);
    setParams(next.length ? { zones: next.join(",") } : {});
  };
  const t = trip.data;
  const [sectorF, setSectorF] = useState<string | null>(null);
  const people = t?.people ?? 0;
  const post = async () => {
    if (!line.trim() || !team.trim()) return;
    setBusy(true);
    try {
      const r = await v2.plan(line, team);
      setPosted(`Posted. ${r.plan.told ?? 0} families in ${(r.plan.zones ?? []).join(", ")} were told a team is coming. Exact addresses in these zones now show on their case pages.`);
      trip.reload();
    } finally {
      setBusy(false);
    }
  };

  return (
    <VShell title="Plan a trip" sub="Pick the zones you can reach. See who is waiting there, what water you'll meet, and who else is going. Then post your plan in one line." at={over.data?.at}>
      <section className="v2-card v-pad v-pick" aria-label="Zones">
        <span className="v-label">Team zones (up to 4), most help missing first · each is about one team's shift</span>
        <div className="v-filters" role="tablist" aria-label="Sector">
          <button role="tab" aria-selected={!sectorF} onClick={() => setSectorF(null)}>All sectors</button>
          {(over.data?.sectors ?? []).map((s) => (
            <button key={s.id} role="tab" aria-selected={sectorF === s.id} onClick={() => setSectorF(s.id)}>Sector {s.id}</button>
          ))}
        </div>
        <div className="v-zonepick">
          {(over.data?.zones ?? []).filter((z) => (!sectorF || z.sector === sectorF) && (sectorF || z.open || picked.includes(z.id))).slice(0, sectorF ? 40 : 24).map((z) => (
            <button key={z.id} type="button" aria-pressed={picked.includes(z.id)} onClick={() => toggle(z.id)}>
              <b>{z.id}</b> <span>{z.label}</span> <span>{z.open} waiting{z.urgent ? ` · ${z.urgent} urgent` : ""}</span>
              {z.plans ? <i className="is-planned">{z.plans} team{z.plans > 1 ? "s" : ""}</i> : z.open ? <i className="is-none">no team</i> : null}
            </button>
          ))}
        </div>
      </section>

      {t && picked.length ? (
        <>
          <div className="v-stats">
            <div><b>{t.zones.reduce((a, z) => a + z.count, 0)}</b><span>families waiting</span></div>
            <div><b>{people}</b><span>people · your seats {seats}{people > seats ? ` → about ${Math.ceil(people / Math.max(1, seats))} trips` : ""}</span></div>
            <div><b>{t.zones.reduce((a, z) => a + z.cannotWalk, 0)}</b><span>can't walk: bring a stretcher</span></div>
            <div><b>{t.zones.reduce((a, z) => a + z.urgent, 0)}</b><span>urgent</span></div>
            <div><b>{t.boatNeeded ? "Boat" : "Truck may do"}</b><span>{t.boatNeeded ? "water at some houses ≥ 0.5 m" : "all known houses below 0.5 m"}</span></div>
          </div>
          {t.zones.map((z) => (
            <section key={z.id} className="v-tripzone">
              <div className="v-tablehead">
                <h2 className="v-h2">Zone <Link to={`/v/zone/${z.id}`}>{z.id}</Link> <span className="v-muted">{z.district}</span> · water <Depth m={z.depthM} /></h2>
                <span className="v-small">{z.count} families · {z.people} people{z.elderly ? ` · ${z.elderly} elderly` : ""}{z.children ? ` · ${z.children} children` : ""}</span>
              </div>
              {z.otherTeams.length ? (
                <p className="v-note">Also going: {z.otherTeams.map((p, i) => <span key={i}><b>{p.team ?? "a team"}</b>{p.eta ? ` ≈ ${p.eta}` : ""}{p.vehicle ? `, ${p.vehicle}` : ""}{i < z.otherTeams.length - 1 ? "; " : ""}</span>)}. Talk to them before you split the families.</p>
              ) : <p className="v-muted v-small">No other team has posted a plan here.</p>}
              {z.gap ? <p className="v2-gap">{z.gap}</p> : null}
              <div className="v-tablewrap"><FamilyTable rows={z.families.slice(0, 12)} onOpen={(id) => nav(`/v/case/${id}`)} /></div>
              {z.count > 12 ? <p className="v-small"><Link to={`/v/zone/${z.id}`}>All {z.count} families in {z.id} →</Link></p> : null}
            </section>
          ))}
          <section className="v2-card v-pad v-post" aria-label="Post your plan">
            <h2 className="v-h2">Post your plan</h2>
            <div className="v-postgrid">
              <label htmlFor="v-team">Team name<input id="v-team" value={team} onChange={(e) => setTeam(e.target.value)} placeholder={translate("ทีมเรือกู้ภัยหาดใหญ่ 1", "Hat Yai rescue boat 1")} /></label>
              <label htmlFor="v-veh">Vehicle
                <select id="v-veh" value={vehicle} onChange={(e) => { setVehicle(e.target.value); setEdited(false); }}>
                  <option value="boat">Boat</option><option value="jet ski">Jet ski</option><option value="high truck">High truck</option><option value="pickup">Pickup</option>
                </select>
              </label>
              <label htmlFor="v-seats">Seats<input id="v-seats" type="number" min={1} max={60} value={seats} onChange={(e) => { setSeats(Number(e.target.value) || 1); setEdited(false); }} /></label>
              <label htmlFor="v-eta">About when<input id="v-eta" type="time" value={eta} onChange={(e) => { setEta(e.target.value); setEdited(false); }} /></label>
            </div>
            <label htmlFor="v-line" className="v-line">The line families and other teams will see
              <input id="v-line" value={line} onChange={(e) => { setLine(e.target.value); setEdited(true); }} />
            </label>
            <div className="v-brief-actions">
              <button type="button" className="v-btn is-go" disabled={busy || !line.trim() || !team.trim()} onClick={post}>Post plan</button>
              {!team.trim() ? <span className="v-muted v-small">Add your team name first.</span> : null}
            </div>
            {posted ? <p className="v-ok" role="status">{posted}</p> : null}
          </section>
        </>
      ) : <p className="v-muted">Pick one or more zones to see who is waiting there.</p>}
    </VShell>
  );
}
