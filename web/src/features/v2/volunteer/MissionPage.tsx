import { useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { vol, type CaseRow, type ZonePage as ZoneDetail } from "../api";
import { Tr, useT } from "../ui/lang";
import { Depth, VShell, useGeo, useLive, useTeam, useTeamNameOpener } from "./shared";
import { directionsUrl, isDone, useMission, visitingOrder, type Mission } from "./mission";
import { MissionMap } from "./MissionMap";
import { UnheardPanel } from "../ui/UnheardPanel";
import { goBy } from "./SectorMap";
import { needLabel } from "./UrgentList";

type Outcome = "pickedUp" | "nobodyThere" | "atShelter";
const OUTCOMES: [Outcome, string, string][] = [
  ["pickedUp", "รับตัวแล้ว", "Picked up"],
  ["nobodyThere", "ไม่มีคนอยู่", "Nobody there"],
  ["atShelter", "พาไปศูนย์พักพิง", "Taken to shelter"],
];

export function MissionPage() {
  const { zoneId = "" } = useParams();
  const t = useT();
  const saved = useMission();
  const mission = saved?.zoneId === zoneId ? saved : null;
  const [currentTeam] = useTeam();
  const team = currentTeam.trim() || mission?.team || "";
  const { data, error, reload } = useLive(() => vol.zone(zoneId, team), [zoneId, team]);
  return <VShell title={t(`ภารกิจ · Mission: ${zoneId}${data?.zone.label ? ` · ${data.zone.label}` : ""}`,
    `Mission: ${zoneId}${data?.zone.label ? ` · ${data.zone.labelEn || data.zone.label}` : ""}`)} at={data?.now.at}>
    {error && <p role="alert"><Tr th="โหลดภารกิจไม่ได้ โปรดลองอีกครั้ง" en="Could not refresh the mission. Please try again." /> <button className="btn btn-ghost" onClick={reload}><Tr th="ลองอีกครั้ง" en="Retry" /></button></p>}
    {!data && !error && <p role="status"><Tr th="กำลังโหลดภารกิจ" en="Loading mission…" /></p>}
    {data && <MissionContent key={zoneId} data={data} mission={mission} team={team} reload={reload} />}
  </VShell>;
}

/** Content lives below VShell so missing team names open its existing name control. */
export function MissionContent({ data, mission, team, reload }: { data: ZoneDetail; mission: Mission | null; team: string; reload: () => void }) {
  const t = useT();
  const geo = useGeo();
  const openTeamName = useTeamNameOpener();
  const postedOrder = data.plan?.order;
  const rows = postedOrder ? postedOrder.flatMap(id => data.households.filter(h => h.id === id)) : visitingOrder(data.households);
  const checkStreets = data.plan?.checkStreets;
  const streets = checkStreets ? data.zone.unheard?.streets.filter(s => checkStreets.includes(s.name) || checkStreets.includes(s.nameEn)) : undefined;
  const done = rows.filter(isDone).length;
  const [selected, setSelected] = useState<string | null>(null);
  const [pending, setPending] = useState<{ id: string; kind: Outcome } | null>(null);
  const [busy, setBusy] = useState(false);
  const sending = useRef(false);
  const [error, setError] = useState(false);
  const [sent, setSent] = useState(false);
  const cards = useRef(new Map<string, HTMLElement>());
  const selectMarker = (id: string) => {
    setSelected(id);
    cards.current.get(id)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    cards.current.get(id)?.querySelector<HTMLButtonElement>(".mission-house-select")?.focus({ preventScroll: true });
  };
  const requestOutcome = (id: string, kind: Outcome) => {
    if (!team.trim()) { openTeamName(); return; }
    setPending({ id, kind }); setError(false); setSent(false);
  };
  const confirm = async () => {
    if (!pending || sending.current) return;
    if (!team.trim()) { openTeamName(); return; }
    const row = rows.find(row => row.id === pending.id);
    if (!row || isDone(row)) { setPending(null); return; }
    sending.current = true; setBusy(true); setError(false);
    const nearest = [...(data.shelterOptions ?? [])].sort((a, b) => a.km - b.km)[0];
    try {
      await vol.outcome(pending.id, pending.kind, team.trim(), pending.kind === "atShelter" ? nearest?.shelterId : undefined);
      setPending(null); setSent(true); reload();
    } catch { setError(true); }
    finally { sending.current = false; setBusy(false); }
  };
  const ownMission = mission?.zoneId === data.zone.id ? mission : null;
  return <div className="mission-page">
    <section className="mission-strip" aria-label={t("ความคืบหน้าภารกิจ", "Mission progress")}>
      {ownMission && <p><b>{ownMission.team}</b> · {t(...vehicleLabel(ownMission.vehicle))} · <Tr th={`${ownMission.seats} ที่นั่ง`} en={`${ownMission.seats} seats`} /> · <Tr th={`ถึงประมาณ ${ownMission.eta}`} en={`ETA ${ownMission.eta}`} /></p>}
      <label className="mission-progress"><Tr th={`เรียบร้อย ${done} จาก ${rows.length} บ้าน`} en={`${done} of ${rows.length} houses done`} />
        <progress max={rows.length || 1} value={done} /></label>
      {ownMission && <p>{ownMission.told === null ? t("ไม่ทราบจำนวนครอบครัวที่แจ้ง", "Notified family count unavailable")
        : t(`แจ้ง ${ownMission.told} ครอบครัวแล้วว่าทีมกำลังมา`, `${ownMission.told} families told a team is coming`)}</p>}
    </section>
    <UnheardPanel unheard={data.zone.unheard} streets={streets} mission />
    {sent && <p role="status"><Tr th="บันทึกผลแล้ว แจ้งครอบครัวแล้ว" en="Outcome recorded. The family has been notified." /></p>}
    {done === rows.length && <section className="mission-empty"><h2>{(data.zone.unheard?.notHeard?.[1] ?? 0) > 0 ? <Tr th="คำขอที่แจ้งมาครบแล้ว ยังต้องตรวจถนนที่ประเมินไว้" en="All reported requests are done. Check the estimated streets too." /> : <Tr th="ทุกบ้านในโซนนี้เรียบร้อย" en="Every house in this zone is done" />}</h2><Link to="/v"><Tr th="กลับไปเลือกโซน" en="Back to zones" /></Link></section>}
    <div className="mission-layout">
      <MissionMap geo={geo} zoneId={data.zone.id} rows={rows} selected={selected} hour={data.now.atH} onSelect={selectMarker} />
      <section className="mission-list" aria-label={t("บ้านตามลำดับการไป", "Houses in visiting order")}>
        {rows.map((row, index) => {
          const closed = isDone(row);
          const directions = directionsUrl(row.lat, row.lon);
          const advice = goBy(row.depth?.m);
          const confirming = pending?.id === row.id;
          return <article key={row.id} ref={node => { if (node) cards.current.set(row.id, node); else cards.current.delete(row.id); }}
            data-house={row.id} className={`mission-house${closed ? " is-done" : ""}${selected === row.id ? " is-selected" : ""}`}
            onClick={() => setSelected(row.id)}>
            <button type="button" className="mission-house-select" aria-pressed={selected === row.id} onClick={() => setSelected(row.id)}>
              <span className={`mission-number ${closed ? "is-done" : row.urgent ? "is-urgent" : "is-waiting"}`}>{closed ? "✓" : index + 1}</span><b>{row.id}</b>
              {row.urgent && !closed && <span><Tr th="ด่วน" en="Urgent" /></span>}
            </button>
            <div className="mission-needs">{row.needs.filter(need => need !== "urgent").map((need, i) => <span className="pill" key={`${need}-${i}`}>{t(...needLabel(need))}</span>)}</div>
            <p>{row.people === null ? t("ไม่ทราบจำนวนคน", "People unknown") : t(`${row.people} คน`, `${row.people} people`)}
              {row.cannotWalk > 0 && <> · <Tr th={`เดินไม่ได้ ${row.cannotWalk} คน`} en={`${row.cannotWalk} cannot walk`} /></>}
              {row.elderly > 0 && <> · <Tr th={`ผู้สูงอายุ ${row.elderly} คน`} en={`${row.elderly} elderly`} /></>}
              {row.children > 0 && <> · <Tr th={`เด็ก ${row.children} คน`} en={`${row.children} children`} /></>}</p>
            <p className="mission-depth"><Depth m={row.depth?.m} lo={row.depth?.lo} hi={row.depth?.hi} /> {advice ? t(...advice) : t("ตรวจสอบการเข้าถึงก่อนออกเดินทาง", "Check access before departure")}</p>
            <p><Tr th={`ติดต่อล่าสุด ${row.lastHeard} · เงียบ ${row.hoursSilent} ชม.`} en={`Last heard ${row.lastHeard} · ${row.hoursSilent} hours silent`} /></p>
            {closed && <p className="mission-outcome">{t(...outcomeLabel(row))}{row.outcome && <> · {row.outcome.team} · {row.outcome.at}</>}</p>}
            <div className="mission-actions">
              {directions ? <a href={directions} target="_blank" rel="noopener noreferrer"><Tr th="นำทาง" en="Directions" /></a> : <span><Tr th="ยังไม่มีพิกัดบ้าน" en="House coordinates unavailable" /></span>}
              <Link to={`/v/case/${encodeURIComponent(row.id)}`}><Tr th="เปิด" en="Open" /></Link>
              {!closed && OUTCOMES.map(([kind, th, en]) => <button type="button" key={kind} disabled={busy} onClick={() => requestOutcome(row.id, kind)}><Tr th={th} en={en} /></button>)}
            </div>
            {confirming && !closed && <div className="mission-confirm" role="group" aria-label={t("ยืนยันผลการช่วยเหลือ", "Confirm outcome")}>
              <p>{t(...outcomeText(pending.kind))} · <Tr th="จะแจ้งครอบครัว" en="This notifies the family" /> · {team}</p>
              <button type="button" disabled={busy} onClick={() => void confirm()}><Tr th="ยืนยัน" en="Confirm" /></button>
              <button type="button" disabled={busy} onClick={() => setPending(null)}><Tr th="ยกเลิก" en="Cancel" /></button>
              {error && <p role="alert"><Tr th="ส่งไม่สำเร็จ โปรดลองอีกครั้ง" en="Could not send. Please try again." /></p>}
            </div>}
          </article>;
        })}
      </section>
    </div>
  </div>;
}
function vehicleLabel(vehicle: string): [string, string] {
  return vehicle === "boat" ? ["เรือ", "Boat"] : ["truck", "high truck"].includes(vehicle) ? ["รถสูง", "High truck"] : ["foot", "on foot"].includes(vehicle) ? ["เดิน", "On foot"] : [vehicle, vehicle];
}
function outcomeLabel(row: CaseRow): [string, string] {
  if (row.status === "atShelter") return ["พาไปศูนย์พักพิง", "Taken to shelter"];
  if (row.status === "nobodyThere") return ["ไม่มีคนอยู่", "Nobody there"];
  if (row.outcome?.kind === "pickedUp") return ["รับตัวแล้ว", "Picked up"];
  if (row.status === "evacuated") return ["อพยพแล้ว", "Evacuated"];
  return ["ปลอดภัย", "Safe"];
}

function outcomeText(kind: Outcome): [string, string] {
  const [, th, en] = OUTCOMES.find(([value]) => value === kind)!;
  return [th, en];
}
