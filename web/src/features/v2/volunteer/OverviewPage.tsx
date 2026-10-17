import { Tr, useT } from "../ui/lang";
/** Map and list share one sector and one zone selection. Plans never imply a rescue. */
import { useEffect, useReducer, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { saveMission } from "./mission";
import { v2, vol, type Overview, type WaterTrend, type ZonePage as ZoneDetail } from "../api";
import { Depth, Trend, VShell, useGeo, useLive, useTeam } from "./shared";
import { initialSelection, selectionReducer } from "./selection";
import { displayText } from "../ui/trace";
import { SectorMap, goBy } from "./SectorMap";
import { UrgentList, UrgentSortControl, useUrgent, type UrgentSort } from "./UrgentList";
import "../ui/phase-three.css";

export function OverviewPage() {
  const t = useT();
  const { data, error, reload } = useLive(() => vol.overview(), []);
  const geo = useGeo();
  const urgent = useUrgent();
  const [sort, setSort] = useState<UrgentSort>("priority");
  const [tab, setTab] = useState("sectors");
  const [highlighted, setHighlighted] = useState<string | null>(null);
  const [focusRequest, setFocusRequest] = useState(0);
  const [sheet, setSheet] = useState("half");
  const [selection, dispatch] = useReducer(selectionReducer, initialSelection);
  const [team] = useTeam();
  const selectZone = (id: string) => dispatch({ type: "zone", id, sector: data?.zones.find(zone => zone.id === id)?.sector ?? null });
  const selectSector = (id: string) => dispatch({ type: "sector", id });
  return <VShell title={t("ช่วยตรงไหนก่อน · Where help is missing", "Where help is missing")} at={data?.at} header={<VolunteerKpis data={data} />}>
    {error && <p role="alert"><Tr th="ติดต่อเซิร์ฟเวอร์ไม่ได้" en="Could not reach the server:" /> {error}</p>}
    <div className="p3-workspace">
      <section className="p3-map-column" aria-label={t("แผนที่พื้นที่", "Sector map")}>
        <SectorMap geo={geo} zones={data?.zones ?? []} selection={selection} onZone={selectZone} onSector={selectSector} onCity={() => dispatch({ type: "sector", id: null })} highlighted={highlighted} onHighlight={setHighlighted}
          water={data ? { hour: data.atH, messages: data.overall.messages } : undefined} shelters={data?.shelters}
          urgentCases={tab === "urgent" ? (urgent.data?.zones.flatMap(zone => zone.cases) ?? []) : undefined}
          onCase={id => { setHighlighted(id); setFocusRequest(value => value + 1); setSheet("full"); }} />
      </section>
      <aside data-sheet={sheet} className="p3-sector-list" aria-label={t("พื้นที่เรียงตามความต้องการ", "Sectors ranked within each area")}>
        <div className="p3-sheet-sizes seg" aria-label={t("ขนาดรายชื่อ · List height", "List height")}>{[["peek", t("ย่อ · Peek", "Peek")], ["half", t("ครึ่ง · Half", "Half")], ["full", t("เต็ม · Full", "Full")]].map(([value, label]) => <button key={value} aria-pressed={sheet === value} onClick={() => setSheet(value)}>{label}</button>)}</div>
        <div className="v-list-toolbar"><div className="seg v-overview-tabs" role="tablist" aria-label={t("รายการช่วยเหลือ · Assistance lists", "Assistance lists")}>
          <button role="tab" aria-selected={tab === "sectors"} aria-controls="v-sector-panel" id="v-sector-tab" onClick={() => setTab("sectors")}><Tr th="พื้นที่" en="Sectors" /></button>
          <button role="tab" aria-selected={tab === "urgent"} aria-controls="v-urgent-panel" id="v-urgent-tab" onClick={() => setTab("urgent")}><Tr th="ด่วน" en="Urgent" /> ({urgent.data?.total ?? "…"})</button>
        </div>{tab === "urgent" && <UrgentSortControl sort={sort} onChange={setSort} />}</div>
        {tab === "urgent" ? <div id="v-urgent-panel" role="tabpanel" aria-labelledby="v-urgent-tab">
          {urgent.error && <p role="alert"><Tr th="โหลดหรือบันทึกไม่สำเร็จ" en="Could not load or save:" /> {urgent.error}</p>}
          <UrgentList data={urgent.data} zones={data?.zones ?? []} team={team} busy={urgent.busy} highlighted={highlighted} focusRequest={focusRequest} sort={sort} onHighlight={setHighlighted} onZone={selectZone} onFirst={urgent.first} />
        </div> : <div id="v-sector-panel" role="tabpanel" aria-labelledby="v-sector-tab">
        {selection.zone ? <ZonePanel key={selection.zone} id={selection.zone} water={data?.zones.find(zone => zone.id === selection.zone)?.water} team={team} onClose={() => dispatch({ type: "close" })} onPosted={reload} /> : <>
        {(data?.sectors ?? []).map(sector => <section key={sector.id}>
          <button className="p3-sector-row" aria-expanded={selection.sector === sector.id} onMouseEnter={() => dispatch({ type: "hover", id: sector.id })} onMouseLeave={() => dispatch({ type: "hover", id: null })} onFocus={() => dispatch({ type: "hover", id: sector.id })} onBlur={() => dispatch({ type: "hover", id: null })} onClick={() => selectSector(sector.id)}>
            <b className="p3-letter" style={{ background: `var(--sector-${sector.id})` }}>{sector.id}</b>
            <span className="p3-sector-content"><strong>{sector.name} · {sector.zones} <Tr th="โซน" en="zones" /></strong>
            <span className="p3-row-numbers"><span><b>{sector.open}</b> <Tr th="รอ" en="waiting" /></span><span><b>{sector.urgent}</b> <Tr th="ด่วน" en="urgent" /></span><span><b>{sector.noTeam}</b> <Tr th="ไม่มีทีม" en="no team" /></span></span>
            <span className="p3-need-bar"><i style={{ width: `${sector.open / Math.max(1, ...(data?.sectors ?? []).map(item => item.open)) * 100}%` }} /><u style={{ width: `${sector.urgent / Math.max(1, ...(data?.sectors ?? []).map(item => item.open)) * 100}%` }} /></span></span>
          </button>
          {selection.sector === sector.id && [...(data?.zones ?? [])].filter(zone => zone.sector === sector.id).sort((a, b) => b.score - a.score).map(zone => <button key={zone.id} className="p3-zone-row" aria-pressed={selection.zone === zone.id} onClick={() => selectZone(zone.id)}>
            <strong>{zone.id} · {zone.label}</strong>
            <span>{zone.open} <Tr th="รอ" en="waiting ·" /> {zone.urgent} <Tr th="ด่วน" en="urgent ·" /> <Depth m={zone.depthM} /> <Trend water={zone.water} /> · <span className={`pill ${zone.plans ? "" : "p-doubt"}`}>{zone.plans ? t(`${zone.plans} ทีม · teams`, `${zone.plans} teams`) : t("ไม่มีทีม · NO TEAM", "NO TEAM")}</span></span>
          </button>)}
        </section>)}
        </>}
        </div>}
      </aside>
    </div>

  </VShell>;
}

export function VolunteerKpis({ data }: { data: Overview | null }) {
  const t = useT();
  const number = (value: number | null | undefined) => value == null ? "…" : value.toLocaleString("en-US");
  const ledger = data?.overall;
  return <div className="v-overview-summary">
    <div className="v-kpis" aria-label={t("ภาพรวมการช่วยเหลือ", "Assistance overview")}>
      <span className="v-kpi is-urgent"><b>{number(data?.zones.reduce((sum, zone) => sum + zone.urgent, 0))}</b><span><Tr th="ด่วน" en="urgent" /></span></span>
      <span className="v-kpi"><b>{number(data?.zones.reduce((sum, zone) => sum + zone.open, 0))}</b><span><Tr th="รอ" en="waiting" /></span></span>
      <span className="v-kpi"><b>{number(data?.zones.filter(zone => zone.open && !zone.plans).length)}</b><span><Tr th="โซนไม่มีทีม" en="zones with no team" /></span></span>
      <span className={`v-kpi${data?.rain?.heavy ? " is-urgent" : ""}`} title={`${data?.rain?.source ?? t("ไม่ทราบแหล่งข้อมูล", "Source unknown")} · ${t("รีเพลย์: ฝนที่ตกจริงถัดไป ใช้แทนพยากรณ์", "replay: rain that fell next, standing in for a forecast")}`}>
        <b>{number(data?.rain?.next6hMm)} <Tr th="มม." en="mm" /></b><span><Tr th="ฝน 6 ชม.ข้างหน้า" en="rain next 6 h" /></span>
      </span>
    </div>
    <p className="v-ledger-line">{t(`Gemini อ่าน ${number(ledger?.messages)} ข้อความ → ${number(ledger?.households)} ครัวเรือน (รวมซ้ำ ${number(ledger?.duplicatesMerged)})`, `Gemini read ${number(ledger?.messages)} messages → ${number(ledger?.households)} households (${number(ledger?.duplicatesMerged)} duplicates merged)`)} · {t(`คาดว่า ${number(ledger?.estimatedHouseholdsAffected)} ครัวเรือนได้รับผลกระทบ`, `est. ${number(ledger?.estimatedHouseholdsAffected)} households affected`)}</p>
  </div>;
}

export function ZonePanel({ id, team, water, onClose, onPosted }: { id: string; team: string; water?: WaterTrend | null; onClose: () => void; onPosted: () => void }) {
  const t = useT();
  const navigate = useNavigate();
  const [, setTeam] = useTeam();
  const panel = useRef<HTMLElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    panel.current?.querySelector<HTMLButtonElement>("button")?.focus();
    return () => { if (previous?.isConnected) previous.focus(); };
  }, []);
  const [detail, setDetail] = useState<ZoneDetail | null>(null);
  const [error, setError] = useState("");
  const [planning, setPlanning] = useState(false);
  const [vehicle, setVehicle] = useState("boat");
  const [planTeam, setPlanTeam] = useState(team);
  const [seats, setSeats] = useState(4);
  // the arrival time starts an hour after the replay's clock, not the real one (the demo lives on 25 Nov)
  const [eta, setEta] = useState("07:00");
  const etaTouched = useRef(false);
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
    if (planning) setText(t(`${planTeam} ${vehicle} ${seats} ที่นั่ง จะเข้าโซน ${id} ประมาณ ${eta}`, `${planTeam}: ${vehicle}, ${seats} seats, zone ${id}, around ${eta}`));
  }, [planning, planTeam, vehicle, seats, id, eta, t]);
  useEffect(() => {
    const clock = detail?.now.at?.slice(-5);
    if (etaTouched.current || !clock || !/^\d\d:\d\d$/.test(clock)) return;
    const hour = (Number(clock.slice(0, 2)) + 1) % 24;
    setEta(`${String(hour).padStart(2, "0")}:${clock.slice(3)}`);
  }, [detail?.now.at]);
  const openPlan = () => setPlanning(true);
  const post = async () => {
    if (busy || posted) return;
    setBusy(true); setError("");
    try {
      const result = await v2.plan(text, planTeam.trim());
      setTold(result.plan.told ?? null);
      setPosted(true);
      setTeam(planTeam.trim());
      saveMission({ zoneId: id, team: planTeam.trim(), vehicle, seats, eta, told: result.plan.told ?? null, at: result.plan.at });
      onPosted();
      // A successful post stays successful even if the router cannot leave this panel.
      try { navigate(`/v/mission/${encodeURIComponent(id)}`); } catch { /* The posted state offers a direct link. */ }
    } catch (failure) { setError(String(failure)); }
    finally { setBusy(false); }
  };
  const zone = detail?.zone;
  return <aside ref={panel} className="p3-zone-panel" tabIndex={-1} onKeyDown={event => { if (event.key === "Escape") onClose(); }} aria-label={`Zone ${id} summary`}>
    <header className="p4-zone-heading">
      <button className="btn btn-ghost p4-zone-back" onClick={onClose}>← <Tr th="กลับไปที่รายการ" en="Back to list" /></button>
      <small><Tr th="โซนช่วยเหลือ" en="Response zone" /></small><h2>{id} · {zone?.label}</h2>
    </header>
    {error && <p role="alert">{error}</p>}
    {!detail && !error && <p role="status"><Tr th="กำลังโหลด" en="Loading zone…" /></p>}
    {zone && !planning && <>
      <p className="p4-decision">{displayText(zone.summary)}</p>
      <div className="p4-zone-stats">
        <span><b>{detail?.totals.open ?? "…"}</b><Tr th="ครอบครัวรอ" en="waiting" /></span>
        <span className={zone.people.urgent ? "is-urgent" : ""}><b>{zone.people.urgent}</b><Tr th="ด่วน" en="urgent" /></span>
        <span><b>{zone.people.cannotWalk}</b><Tr th="เดินไม่ได้" en="can’t walk" /></span>
      </div>
      {(() => {
        // the likely depth sets the vehicle; the deep end of the range is said out loud, since a team meets the worst street
        const likely = zone.level?.depthM, hi = zone.level?.depthHiM;
        const go = goBy(likely);
        const deeper = hi != null && likely != null && goBy(hi)?.[0] !== go?.[0];
        return <p className="p4-go-by"><b><Tr th="น้ำ" en="Water:" /></b> <Trend water={water} long /><br /><b><Tr th="ไปด้วย" en="Go by:" /></b> {go ? <><Tr th={<>{go[0]} </>} en={go[1]} /></> : t("ไม่ทราบระดับน้ำ เตรียมเรือไว้ · depth unknown, bring a boat", "depth unknown, bring a boat")}
          {deeper && <><br /><Tr th={<>บางจุดอาจถึง {hi.toFixed(1)} ม.</>} en={<>some streets up to {hi.toFixed(1)} m</>} /></>}</p>;
      })()}
      <p className="p4-zone-teams"><Tr th="ทีมอื่น" en="Other teams:" /> {zone.plans.map(plan => `${plan.team ?? "unnamed"} ${plan.vehicle ?? ""} ${plan.eta ?? "time unknown"}`).join(" · ") || t("ยังไม่มี · none planned", "none planned")}</p>
    </>}
    {zone && !planning && <>
      <h3><Tr th="ทำไมที่นี่" en="Why here" /></h3>
      {/* three short answers; the evidence behind each opens on demand instead of one wall of text */}
      <details className="p3-why"><summary><span className="pill p-physics"><Tr th="แบบจำลอง" en="Physics" /></span> <Tr th="น้ำ" en="Water" /> <Depth m={zone.level?.depthM} lo={zone.level?.depthLoM} hi={zone.level?.depthHiM} /></summary><p><Tr th="น้ำ" en="Water:" /> <Depth m={zone.level?.depthM} lo={zone.level?.depthLoM} hi={zone.level?.depthHiM} /> · {detail?.now.at}<br />{zone.sources.map(source => displayText(source.text)).join(" · ") || t("ยังไม่มีแหล่งข้อมูล · Sources unavailable", "Sources unavailable")}</p></details>
      <details className="p3-why"><summary><span className="pill p-gemini">Gemini</span> <Tr th="สรุปจากข้อความของครอบครัว" en="What the families said" /></summary><p>{displayText(detail?.briefing || t("ยังไม่มีคำอธิบาย · Briefing unavailable", "Briefing unavailable"))}</p></details>
      <details className="p3-why"><summary><span className="pill p-rules"><Tr th="กติกา" en="Rules" /></span> <Tr th="ช่องว่างที่ยังไม่มีใครดูแล" en="What is not covered" /></summary><p>{displayText(zone.gap || t("ทบทวนความต้องการและแผนทีม · Review needs and team plans", "Review needs and team plans"))}</p></details>
      <div className="rp-warning"><h3><Tr th="ยังไม่แน่ใจ" en="Not sure" /></h3><p>{displayText(zone.disagree || t("ยังไม่มีข้อขัดแย้งที่บันทึกไว้ ข้อมูลที่ไม่รายงานยังไม่ทราบ · No recorded conflict; unreported conditions remain unknown", "No recorded conflict; unreported conditions remain unknown"))}</p></div>
      <h3><Tr th="ใครก่อน" en="Who first" /></h3>
      {priorityFamilies(detail?.households ?? []).map(household => <Link className="p3-family" key={household.id} to={`/v/case/${household.id}`}><span className="pill">{household.id}</span><p>{household.people === null ? t("ไม่ทราบจำนวนคน · Household size unknown", "Household size unknown") : t(`${household.people} คน · people`, `${household.people} people`)} · {household.cannotWalk ? t("มีคนเดินไม่ได้ · Cannot walk", "Cannot walk") : household.urgent ? t("แจ้งความต้องการด่วน · Urgent help reported", "Urgent help reported") : t("กำลังรอความช่วยเหลือ · Waiting for help", "Waiting for help")}</p></Link>)}
      <footer className="p3-panel-footer"><Link to={`/v/zone/${id}`}><Tr th="รายละเอียด" en="Details" /></Link><button className="btn btn-pri" onClick={openPlan} disabled={!detail}><Tr th="ฉันจะไปที่นี่" en="I'll go here" /></button></footer>
    </>}
    {planning && !posted && <form onSubmit={event => { event.preventDefault(); void post(); }}>
      <label><Tr th="ทีม" en="Team" /><input required value={planTeam} onChange={event => setPlanTeam(event.target.value)} disabled={busy || posted} /></label>
      <h3><Tr th="แผนเดินทาง" en="Your plan" /></h3>
      <fieldset disabled={busy || posted}><legend><Tr th="พาหนะ" en="Vehicle" /></legend><div className="p3-plan-chips">{[["boat", "เรือ", "Boat"], ["high truck", "รถสูง", "High truck"], ["on foot", "เดิน", "On foot"]].map(([value, th, en]) => <button type="button" className={`chip ${vehicle === value ? "on" : ""}`} aria-pressed={vehicle === value} key={value} onClick={() => setVehicle(value)}><Tr th={th} en={en} /></button>)}</div></fieldset>
      <fieldset disabled={busy || posted}><legend><Tr th="ที่นั่ง" en="Seats" /></legend><div className="p3-plan-chips">{[2, 4, 6, 8].map(value => <button type="button" className={`chip ${seats === value ? "on" : ""}`} aria-pressed={seats === value} key={value} onClick={() => setSeats(value)}>{value}</button>)}</div></fieldset>
      <fieldset disabled={busy || posted}><legend><Tr th="เวลา" en="Time" /></legend><div className="p3-plan-chips">{["07:00", "12:00", "17:00"].map(value => <button type="button" key={value} className={`chip ${eta === value ? "on" : ""}`} aria-pressed={eta === value} onClick={() => { etaTouched.current = true; setEta(value); }}>{value}</button>)}</div></fieldset>
      <label><Tr th="ถึงประมาณ" en="Arrival time" /><input type="time" required value={eta} onChange={event => { etaTouched.current = true; setEta(event.target.value); }} disabled={busy || posted} /></label>
      <button type="button" className="btn btn-ghost" disabled={busy || posted} onClick={() => setPlanning(false)}><Tr th="ย้อนกลับ" en="Back" /></button>
      <label><Tr th="แผนหนึ่งบรรทัด" en="One-line plan" /><textarea required value={text} onChange={event => setText(event.target.value)} disabled={busy || posted} /></label>
      <p><Tr th="ปรับข้อความให้ตรงกับทีมและพาหนะก่อนส่ง" en="Check team and vehicle in the plan before posting." /></p>
      <p className="p4-decision"><Tr th="ตัวอย่างข้อความ" en="Preview" /><br />{text}</p>
      <footer className="p3-panel-footer"><button className="btn btn-pri" disabled={busy || posted || !planTeam.trim() || !text.trim()}>{busy ? t("กำลังส่ง · Posting…", "Posting…") : t("ส่งแผนและแจ้งครอบครัวในโซน", "Post plan and tell the families")}</button></footer>
    </form>}
    {posted && <p role="status">{told === null ? t("บันทึกแผนแล้ว ไม่ทราบจำนวนที่แจ้ง · Plan recorded; notified family count unavailable", "Plan recorded; notified family count unavailable") : t(`แจ้งแล้ว ${told} ครอบครัว`, `${told} families told`)} <Tr th="· เป็นแผน ยังไม่ได้ช่วยออกมา" en="planned, not rescued yet" /> <Link className="btn btn-pri" to={`/v/mission/${encodeURIComponent(id)}`}><Tr th="ไปที่ภารกิจ" en="Go to my mission" /></Link></p>}
  </aside>;
}

export function priorityFamilies(rows: ZoneDetail["households"]) {
  return rows.filter(row => !row.outcome && !["safe", "evacuated", "nobodyThere", "atShelter"].includes(row.status)).sort((a, b) => b.priority - a.priority);
}
