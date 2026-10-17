/** Map and list share one sector and one zone selection. Plans never imply a rescue. */
import { useEffect, useReducer, useState } from "react";
import { Link } from "react-router-dom";
import { v2, vol, type ZonePage as ZoneDetail } from "../api";
import { Depth, VShell, useGeo, useLive, useTeam } from "./shared";
import { initialSelection, selectionReducer } from "./selection";
import { SectorMap } from "./SectorMap";
import "../ui/phase-three.css";

export function OverviewPage() {
  const { data, error, reload } = useLive(() => vol.overview(), []);
  const geo = useGeo();
  const [selection, dispatch] = useReducer(selectionReducer, initialSelection);
  const [team] = useTeam();
  const selectZone = (id: string) => dispatch({ type: "zone", id, sector: data?.zones.find(zone => zone.id === id)?.sector ?? null });
  const selectSector = (id: string) => dispatch({ type: "sector", id });
  return <VShell title="ช่วยตรงไหนก่อน · Where help is missing" sub="เลือกพื้นที่บนแผนที่หรือรายชื่อ · Select a sector or team zone to see uncovered needs." at={data?.at}>
    {error && <p role="alert">Couldn't reach the server: {error}</p>}
    <div className="p3-numbers">
      <span><b>{data?.zones.reduce((sum, zone) => sum + zone.open, 0) ?? "…"}</b> ครอบครัวรอ · waiting</span>
      <span><b>{data?.zones.reduce((sum, zone) => sum + zone.urgent, 0) ?? "…"}</b> ด่วน · urgent</span>
      <span><b>{data?.zones.filter(zone => zone.open && !zone.plans).length ?? "…"}</b> โซนไม่มีทีม · zones with no team</span>
    </div>
    <div className="p3-workspace">
      <section className="p3-map-column" aria-label="Sector map">
        <button onClick={() => dispatch({ type: "sector", id: null })}>ทุกพื้นที่ · All sectors</button>
        <SectorMap geo={geo} zones={data?.zones ?? []} selection={selection} onZone={selectZone} onSector={selectSector} />
        <div className="p3-legend">{["ไม่มีครอบครัวรอ · None waiting", "น้อย · Lower", "ปานกลาง · More", "มากสุด · Most help missing"].map((label, index) => <span key={label}><i style={{ background: `var(--need-${index})` }} />{label}</span>)}</div>
        <p>เส้นประ: มีครอบครัวรอ ไม่มีทีม · Dashed: waiting families, no team planned. Thick outlines and letters: sectors. Water unknown is never dry.</p>
      </section>
      <aside className="p3-sector-list" aria-label="Sectors ranked within each area">
        {(data?.sectors ?? []).map(sector => <section key={sector.id}>
          <button className="p3-sector-row" aria-expanded={selection.sector === sector.id} onMouseEnter={() => dispatch({ type: "hover", id: sector.id })} onMouseLeave={() => dispatch({ type: "hover", id: null })} onFocus={() => dispatch({ type: "hover", id: sector.id })} onBlur={() => dispatch({ type: "hover", id: null })} onClick={() => selectSector(sector.id)}>
            <b className="p3-letter" style={{ background: `var(--sector-${sector.id})` }}>{sector.id}</b>
            <span>{sector.name} · {sector.zones} zones<br />{sector.open} waiting · {sector.urgent} urgent · {sector.noTeam} no team · {sector.boat} need boat</span>
          </button>
          {selection.sector === sector.id && [...(data?.zones ?? [])].filter(zone => zone.sector === sector.id).sort((a, b) => b.score - a.score).map(zone => <button key={zone.id} className="p3-zone-row" aria-pressed={selection.zone === zone.id} onClick={() => selectZone(zone.id)}>
            <strong>{zone.id} · {zone.label}</strong>
            <span>{zone.open} waiting · {zone.urgent} urgent · <Depth m={zone.depthM} /> · {zone.plans ? `${zone.plans} teams planned` : "no team"}</span>
          </button>)}
        </section>)}
      </aside>
    </div>
    {selection.zone && <ZonePanel key={selection.zone} id={selection.zone} team={team} onClose={() => dispatch({ type: "close" })} onPosted={reload} />}
  </VShell>;
}

function ZonePanel({ id, team, onClose, onPosted }: { id: string; team: string; onClose: () => void; onPosted: () => void }) {
  const [detail, setDetail] = useState<ZoneDetail | null>(null);
  const [error, setError] = useState("");
  const [planning, setPlanning] = useState(false);
  const [vehicle, setVehicle] = useState("เรือ · boat");
  const [planTeam, setPlanTeam] = useState(team);
  const [eta] = useState(() => new Date(Date.now() + 30 * 60000).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }));
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [posted, setPosted] = useState(false);
  const [told, setTold] = useState<number | null>(null);
  useEffect(() => {
    let active = true;
    vol.zone(id, team).then(result => { if (active) setDetail(result); }, failure => { if (active) setError(String(failure)); });
    return () => { active = false; };
  }, [id, team]);
  useEffect(() => {
    if (planning) setText(`${planTeam} ${vehicle} จะเข้าโซน ${id} ประมาณ ${eta}`);
  }, [planning, planTeam, vehicle, id, eta]);
  const openPlan = () => setPlanning(true);
  const post = async () => {
    if (busy || posted) return;
    setBusy(true); setError("");
    try {
      const result = await v2.plan(text, planTeam);
      setTold(result.plan.told ?? null);
      setPosted(true);
      onPosted();
    } catch (failure) { setError(String(failure)); }
    finally { setBusy(false); }
  };
  const zone = detail?.zone;
  return <aside className="p3-zone-panel" role="dialog" aria-label={`Zone ${id} summary`}>
    <button onClick={onClose}>ปิด · Close</button>
    <header className="p4-zone-heading"><small>โซนช่วยเหลือ · Response zone</small><h2>{id} · {zone?.label}</h2></header>
    {error && <p role="alert">{error}</p>}
    {!detail && !error && <p role="status">กำลังโหลด · Loading zone…</p>}
    {zone && <>
      <p className="p4-decision">{detail?.briefing || zone.summary}</p><p>จุดตัดสินใจ · Decision: {zone.gap ?? "See waiting families and planned teams below"}</p>
      <div className="p4-zone-stats"><span>{detail?.totals.open} ครอบครัวรอ · waiting</span><span>{zone.people.urgent} ด่วน · urgent</span><span>{zone.people.cannotWalk} เดินไม่ได้ · can’t walk</span></div>
      <p className="p4-zone-water">น้ำ · Water: <Depth m={zone.level?.depthM} lo={zone.level?.depthLoM} hi={zone.level?.depthHiM} /></p>
      <p className="p4-zone-teams">ทีมอื่น · Other teams: {zone.plans.map(plan => `${plan.team ?? "unnamed"} ${plan.vehicle ?? ""} ${plan.eta ?? "time unknown"}`).join(" · ") || "ยังไม่มี · none planned"}</p>
    </>}
    <div className="p3-actions"><Link to={`/v/zone/${id}`}>เปิดโซน · Open zone →</Link><button onClick={openPlan} disabled={!detail || planning}>ฉันจะไปที่นี่ · I'll go here</button></div>
    {planning && <form onSubmit={event => { event.preventDefault(); void post(); }}>
      <label>ทีม · Team<input required value={planTeam} onChange={event => setPlanTeam(event.target.value)} disabled={busy || posted} /></label>
      <label>พาหนะ · Vehicle<input value={vehicle} onChange={event => setVehicle(event.target.value)} disabled={busy || posted} /></label>
      <label>แผนหนึ่งบรรทัด · One-line plan<textarea required value={text} onChange={event => setText(event.target.value)} disabled={busy || posted} /></label>
      <p>ปรับข้อความให้ตรงกับทีมและพาหนะก่อนส่ง · Check team and vehicle in the plan before posting.</p>
      <button disabled={busy || posted || !planTeam.trim() || !text.trim()}>แจ้งแผน · Post plan</button>
    </form>}
    {posted && <p role="status">{told === null ? "บันทึกแผนแล้ว ไม่ทราบจำนวนที่แจ้ง · Plan recorded; notified family count unavailable" : `แจ้งแล้ว ${told} ครอบครัว · ${told} families told`} · planned, not rescued yet</p>}
  </aside>;
}
