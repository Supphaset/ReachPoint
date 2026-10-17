/** Map and list share one sector and one zone selection. Plans never imply a rescue. */
import { useEffect, useReducer, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { v2, vol, type ZonePage as ZoneDetail } from "../api";
import { Depth, VShell, useGeo, useLive, useTeam } from "./shared";
import { initialSelection, selectionReducer } from "./selection";
import { displayText } from "../ui/trace";
import { SectorMap, goBy } from "./SectorMap";
import "../ui/phase-three.css";

export function OverviewPage() {
  const { data, error, reload } = useLive(() => vol.overview(), []);
  const geo = useGeo();
  const [sheet, setSheet] = useState("half");
  const [selection, dispatch] = useReducer(selectionReducer, initialSelection);
  const [team] = useTeam();
  const selectZone = (id: string) => dispatch({ type: "zone", id, sector: data?.zones.find(zone => zone.id === id)?.sector ?? null });
  const selectSector = (id: string) => dispatch({ type: "sector", id });
  return <VShell title="ช่วยตรงไหนก่อน · Where help is missing" sub="เลือกพื้นที่บนแผนที่หรือรายชื่อ · Select a sector or team zone to see uncovered needs." at={data?.at} ledger={data?.overall}>
    {error && <p role="alert">Couldn't reach the server: {error}</p>}
    <div className="p3-numbers">
      <span><b>{data?.zones.reduce((sum, zone) => sum + zone.open, 0) ?? "…"}</b> ครอบครัวรอ · waiting</span>
      <span><b>{data?.zones.reduce((sum, zone) => sum + zone.urgent, 0) ?? "…"}</b> ด่วน · urgent</span>
      <span><b>{data?.zones.filter(zone => zone.open && !zone.plans).length ?? "…"}</b> โซนไม่มีทีม · zones with no team</span>
    </div>
    <div className="p3-workspace">
      <section className="p3-map-column" aria-label="Sector map">
        <div className="p3-breadcrumb"><button className="btn btn-sec" onClick={() => dispatch({ type: "sector", id: null })}>หาดใหญ่ · Hat Yai</button>{selection.sector && <span> / {selection.sector}</span>}{selection.zone && <span> / {selection.zone}</span>}</div>
        <SectorMap geo={geo} zones={data?.zones ?? []} selection={selection} onZone={selectZone} onSector={selectSector}
          water={data ? { hour: data.atH, messages: data.overall.messages } : undefined} shelters={data?.shelters} />
        <div className="p3-legend">{["ไม่มีครอบครัวรอ · None waiting", "น้อย · Lower", "ปานกลาง · More", "มากสุด · Most help missing"].map((label, index) => <span key={label}><i style={{ background: `var(--need-${index})` }} />{label}</span>)}</div>
        <p>เส้นประ / ขอบหนา: มีครอบครัวรอ ไม่มีทีม · Dashed / heavier edges: waiting, no team. Thick outlines and letters: sectors. Water unknown is never dry.</p>
      </section>
      <aside data-sheet={sheet} className="p3-sector-list" aria-label="Sectors ranked within each area">
        <div className="p3-sheet-sizes seg" aria-label="ขนาดรายชื่อ · List height">{[["peek", "ย่อ · Peek"], ["half", "ครึ่ง · Half"], ["full", "เต็ม · Full"]].map(([value, label]) => <button key={value} aria-pressed={sheet === value} onClick={() => setSheet(value)}>{label}</button>)}</div>
        {selection.zone ? <ZonePanel key={selection.zone} id={selection.zone} team={team} onClose={() => dispatch({ type: "close" })} onPosted={reload} /> : <>
        {(data?.sectors ?? []).map(sector => <section key={sector.id}>
          <button className="p3-sector-row" aria-expanded={selection.sector === sector.id} onMouseEnter={() => dispatch({ type: "hover", id: sector.id })} onMouseLeave={() => dispatch({ type: "hover", id: null })} onFocus={() => dispatch({ type: "hover", id: sector.id })} onBlur={() => dispatch({ type: "hover", id: null })} onClick={() => selectSector(sector.id)}>
            <b className="p3-letter" style={{ background: `var(--sector-${sector.id})` }}>{sector.id}</b>
            <span className="p3-sector-content"><strong>{sector.name} · {sector.zones} โซน <small>zones</small></strong>
            <span className="p3-row-numbers"><span><b>{sector.open}</b> รอ <small>waiting</small></span><span><b>{sector.urgent}</b> ด่วน <small>urgent</small></span><span><b>{sector.noTeam}</b> ไม่มีทีม <small>no team</small></span></span>
            <span className="p3-need-bar"><i style={{ width: `${sector.open / Math.max(1, ...(data?.sectors ?? []).map(item => item.open)) * 100}%` }} /><u style={{ width: `${sector.urgent / Math.max(1, ...(data?.sectors ?? []).map(item => item.open)) * 100}%` }} /></span></span>
          </button>
          {selection.sector === sector.id && [...(data?.zones ?? [])].filter(zone => zone.sector === sector.id).sort((a, b) => b.score - a.score).map(zone => <button key={zone.id} className="p3-zone-row" aria-pressed={selection.zone === zone.id} onClick={() => selectZone(zone.id)}>
            <strong>{zone.id} · {zone.label}</strong>
            <span>{zone.open} รอ · waiting · {zone.urgent} ด่วน · urgent · <Depth m={zone.depthM} /> · <span className={`pill ${zone.plans ? "" : "p-doubt"}`}>{zone.plans ? `${zone.plans} ทีม · teams` : "ไม่มีทีม · NO TEAM"}</span></span>
          </button>)}
        </section>)}
        </>}
      </aside>
    </div>

  </VShell>;
}

export function ZonePanel({ id, team, onClose, onPosted }: { id: string; team: string; onClose: () => void; onPosted: () => void }) {
  const panel = useRef<HTMLElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    panel.current?.querySelector<HTMLButtonElement>("button")?.focus();
    return () => { if (previous?.isConnected) previous.focus(); };
  }, []);
  const [detail, setDetail] = useState<ZoneDetail | null>(null);
  const [error, setError] = useState("");
  const [planning, setPlanning] = useState(false);
  const [vehicle, setVehicle] = useState("เรือ · boat");
  const [planTeam, setPlanTeam] = useState(team);
  const [seats, setSeats] = useState(4);
  const [eta, setEta] = useState(() => new Date(Date.now() + 30 * 60000).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }));
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
    if (planning) setText(`${planTeam} ${vehicle} ${seats} ที่นั่ง จะเข้าโซน ${id} ประมาณ ${eta}`);
  }, [planning, planTeam, vehicle, seats, id, eta]);
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
  return <aside ref={panel} className="p3-zone-panel" tabIndex={-1} onKeyDown={event => { if (event.key === "Escape") onClose(); }} aria-label={`Zone ${id} summary`}>
    <button onClick={onClose}>ปิด · Close</button>
    <header className="p4-zone-heading"><small>โซนช่วยเหลือ · Response zone</small><h2>{id} · {zone?.label}</h2></header>
    {error && <p role="alert">{error}</p>}
    {!detail && !error && <p role="status">กำลังโหลด · Loading zone…</p>}
    {zone && !planning && <>
      <p className="p4-decision">{displayText(zone.summary)}</p>
      <div className="p4-zone-stats"><span>{detail?.totals.open} ครอบครัวรอ · waiting</span><span>{zone.people.urgent} ด่วน · urgent</span><span>{zone.people.cannotWalk} เดินไม่ได้ · can’t walk</span></div>
      {(() => {
        // the likely depth sets the vehicle; the deep end of the range is said out loud, since a team meets the worst street
        const likely = zone.level?.depthM, hi = zone.level?.depthHiM;
        const go = goBy(likely);
        const deeper = hi != null && likely != null && goBy(hi)?.[0] !== go?.[0];
        return <p className="p4-go-by"><b>ไปด้วย · Go by:</b> {go ? <>{go[0]} <small>{go[1]}</small></> : "ไม่ทราบระดับน้ำ เตรียมเรือไว้ · depth unknown, bring a boat"}
          {deeper && <><br />บางจุดอาจถึง {hi.toFixed(1)} ม. <small>some streets up to {hi.toFixed(1)} m</small></>}</p>;
      })()}
      <p className="p4-zone-teams">ทีมอื่น · Other teams: {zone.plans.map(plan => `${plan.team ?? "unnamed"} ${plan.vehicle ?? ""} ${plan.eta ?? "time unknown"}`).join(" · ") || "ยังไม่มี · none planned"}</p>
    </>}
    {zone && !planning && <>
      <h3>ทำไมที่นี่ · Why here</h3>
      <div className="p3-why"><span className="pill p-physics">แบบจำลอง · Physics</span><p>น้ำ · Water: <Depth m={zone.level?.depthM} lo={zone.level?.depthLoM} hi={zone.level?.depthHiM} /> · {detail?.now.at}<br />{zone.sources.map(source => displayText(source.text)).join(" · ") || "ยังไม่มีแหล่งข้อมูล · Sources unavailable"}</p></div>
      <div className="p3-why"><span className="pill p-gemini">Gemini</span><p>{displayText(detail?.briefing || "ยังไม่มีคำอธิบาย · Briefing unavailable")}</p></div>
      <div className="p3-why"><span className="pill p-rules">กติกา · Rules</span><p>{displayText(zone.gap || "ทบทวนความต้องการและแผนทีม · Review needs and team plans")}</p></div>
      <div className="rp-warning"><h3>ยังไม่แน่ใจ · Not sure</h3><p>{displayText(zone.disagree || "ยังไม่มีข้อขัดแย้งที่บันทึกไว้ ข้อมูลที่ไม่รายงานยังไม่ทราบ · No recorded conflict; unreported conditions remain unknown")}</p></div>
      <h3>ใครก่อน · Who first</h3>
      {priorityFamilies(detail?.households ?? []).map(household => <Link className="p3-family" key={household.id} to={`/v/case/${household.id}`}><span className="pill">{household.id}</span><p>{household.people === null ? "ไม่ทราบจำนวนคน · Household size unknown" : `${household.people} คน · people`} · {household.cannotWalk ? "มีคนเดินไม่ได้ · Cannot walk" : household.urgent ? "แจ้งความต้องการด่วน · Urgent help reported" : "กำลังรอความช่วยเหลือ · Waiting for help"}</p></Link>)}
      <footer className="p3-panel-footer"><Link to={`/v/zone/${id}`}>รายละเอียด · Details</Link><button className="btn btn-pri" onClick={openPlan} disabled={!detail}>ฉันจะไปที่นี่ · I'll go here</button></footer>
    </>}
    {planning && !posted && <form onSubmit={event => { event.preventDefault(); void post(); }}>
      <label>ทีม · Team<input required value={planTeam} onChange={event => setPlanTeam(event.target.value)} disabled={busy || posted} /></label>
      <h3>แผนเดินทาง · Your plan</h3>
      <fieldset disabled={busy || posted}><legend>พาหนะ · Vehicle</legend><div className="p3-plan-chips">{["เรือ · boat", "รถสูง · high truck", "เดิน · on foot"].map(value => <button type="button" className={`chip ${vehicle === value ? "on" : ""}`} aria-pressed={vehicle === value} key={value} onClick={() => setVehicle(value)}>{value}</button>)}</div></fieldset>
      <fieldset disabled={busy || posted}><legend>ที่นั่ง · Seats</legend><div className="p3-plan-chips">{[2, 4, 6, 8].map(value => <button type="button" className={`chip ${seats === value ? "on" : ""}`} aria-pressed={seats === value} key={value} onClick={() => setSeats(value)}>{value}</button>)}</div></fieldset>
      <fieldset disabled={busy || posted}><legend>เวลา · Time</legend><div className="p3-plan-chips">{["07:00", "12:00", "17:00"].map(value => <button type="button" key={value} className={`chip ${eta === value ? "on" : ""}`} aria-pressed={eta === value} onClick={() => setEta(value)}>{value}</button>)}</div></fieldset>
      <label>ถึงประมาณ · Arrival time<input type="time" required value={eta} onChange={event => setEta(event.target.value)} disabled={busy || posted} /></label>
      <button type="button" className="btn btn-ghost" disabled={busy || posted} onClick={() => setPlanning(false)}>ย้อนกลับ · Back</button>
      <label>แผนหนึ่งบรรทัด · One-line plan<textarea required value={text} onChange={event => setText(event.target.value)} disabled={busy || posted} /></label>
      <p>ปรับข้อความให้ตรงกับทีมและพาหนะก่อนส่ง · Check team and vehicle in the plan before posting.</p>
      <p className="p4-decision">ตัวอย่างข้อความ · Preview<br />{text}</p>
      <footer className="p3-panel-footer"><button className="btn btn-pri" disabled={busy || posted || !planTeam.trim() || !text.trim()}>{busy ? "กำลังส่ง · Posting…" : `จะแจ้ง ${detail?.totals.open ?? "?"} ครอบครัว · ${detail?.totals.open ?? "?"} families will be told`}</button></footer>
    </form>}
    {posted && <p role="status">{told === null ? "บันทึกแผนแล้ว ไม่ทราบจำนวนที่แจ้ง · Plan recorded; notified family count unavailable" : `แจ้งแล้ว ${told} ครอบครัว · ${told} families told`} · เป็นแผน ยังไม่ได้ช่วยออกมา · planned, not rescued yet</p>}
  </aside>;
}

export function priorityFamilies(rows: ZoneDetail["households"]) {
  return rows.filter(row => !row.outcome && !["safe", "evacuated", "nobodyThere", "atShelter"].includes(row.status)).sort((a, b) => b.priority - a.priority);
}
