import { Tr, useT } from "../ui/lang";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { vol, type OverviewZone, type UrgentCase, type UrgentView, type UrgentZone } from "../api";
import { Depth, Trend } from "./shared";
import { goBy } from "./SectorMap";

export type UrgentSort = "priority" | "depth" | "silent";
export function sortUrgentZones(zones: UrgentZone[], sort: UrgentSort): UrgentZone[] {
  const result = [...zones];
  if (sort === "depth") result.sort((a, b) => (b.depthM ?? -Infinity) - (a.depthM ?? -Infinity));
  if (sort === "silent") result.sort((a, b) => Math.max(0, ...b.cases.map(row => row.hoursSilent)) - Math.max(0, ...a.cases.map(row => row.hoursSilent)));
  return result;
}

/** Poll and mutation responses share a generation so an older GET cannot undo a shared mark. */
export function useUrgent() {
  const [data, setData] = useState<UrgentView | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const version = useRef(0);
  const lock = useRef(false);
  useEffect(() => {
    let active = true;
    const reload = async () => {
      if (lock.current) return;
      const request = ++version.current;
      try {
        const result = await vol.urgent();
        if (active && request === version.current) { setData(result); setError(""); }
      } catch (failure) { if (active && request === version.current) setError(String(failure)); }
    };
    void reload();
    const timer = window.setInterval(reload, 10000);
    window.addEventListener("reachpoint-clock", reload);
    return () => { active = false; version.current++; window.clearInterval(timer); window.removeEventListener("reachpoint-clock", reload); };
  }, []);
  async function first(row: UrgentCase, team: string) {
    if (lock.current || !team.trim()) return;
    lock.current = true;
    const request = ++version.current;
    setBusy(true); setError("");
    try {
      const result = await vol.first(row.id, team, !row.markedFirst);
      if (request === version.current) setData(result);
    } catch (failure) { if (request === version.current) setError(String(failure)); }
    finally { lock.current = false; setBusy(false); }
  }
  return { data, error, busy, first };
}

const NEED_LABELS: Record<string, [string, string]> = {
  "can't walk": ["เดินไม่ได้", "Can't walk"], "cannot walk": ["เดินไม่ได้", "Cannot walk"],
  cannotWalk: ["เดินไม่ได้", "Can't walk"], elderly: ["ผู้สูงอายุ", "Elderly"], children: ["เด็ก", "Children"],
  "needs a ride": ["ต้องการรถรับ", "Needs a ride"], "wants to leave": ["ต้องการออก", "Wants to leave"],
  wantsOut: ["ต้องการออก", "Wants to leave"], needsRide: ["ต้องการรถรับ", "Needs a ride"],
};
export function UrgentList({ data, zones, team, busy, highlighted, focusRequest = 0, onZone, onFirst }: {
  data: UrgentView | null; zones: OverviewZone[]; team: string; busy: boolean; highlighted: string | null; focusRequest?: number;
  onZone: (id: string) => void; onFirst: (row: UrgentCase, team: string) => Promise<void>;
}) {
  const t = useT();
  const [sort, setSort] = useState<UrgentSort>("priority");
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!highlighted) return;
    const row = [...(root.current?.querySelectorAll<HTMLElement>("[data-case]") ?? [])].find(item => item.dataset.case === highlighted);
    row?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    row?.focus({ preventScroll: true });
  }, [highlighted, focusRequest]);
  return <div className="v-urgent" ref={root}>
    <label><Tr th="เรียงพื้นที่" en="Sort zones" />
      <select value={sort} onChange={event => setSort(event.target.value as UrgentSort)}>
        <option value="priority">{t("สำคัญสุด · Priority", "Priority")}</option>
        <option value="depth">{t("น้ำลึกสุด · Deepest", "Deepest")}</option>
        <option value="silent">{t("เงียบนานสุด · Longest silent", "Longest silent")}</option>
      </select>
    </label>
    {!data && <p role="status"><Tr th="กำลังโหลด" en="Loading urgent cases…" /></p>}
    {data?.total === 0 && <p><Tr th="ไม่มีรายการด่วน" en="No urgent cases" /></p>}
    {!team.trim() && <p><Tr th="ตั้งชื่อทีมก่อนเลือกทำก่อน" en="Set your team name to mark cases" /></p>}
    {sortUrgentZones(data?.zones ?? [], sort).map(zone => {
      const overview = zones.find(item => item.id === zone.id);
      const go = goBy(zone.depthM);
      return <section key={zone.id} className="v-urgent-zone">
        <button className="v-urgent-heading" onClick={() => onZone(zone.id)}>
          <strong>{zone.id} · {zone.label ?? t("ไม่ทราบชื่อ · Unknown place", "Unknown place")}</strong>
          <span><Depth m={zone.depthM} /> <Trend water={overview?.water} /></span>
          <span><Tr th="ไปด้วย" en="Go by:" /> {go ? <><Tr th={go[0]} en={go[1]} /></> : t("ไม่ทราบ · Unknown", "Unknown")}</span>
          <span>{zone.cases.length} <Tr th="ด่วน" en="urgent ·" /> {zone.plans ? t(`${zone.plans} ทีม · teams`, `${zone.plans} teams`) : t("ไม่มีทีม · NO TEAM", "NO TEAM")}</span>
        </button>
        {zone.cases.map(row => <article key={row.id} data-case={row.id} tabIndex={-1}
          className={`v-urgent-case${highlighted === row.id ? " is-highlighted" : ""}`}>
          <div className="v-urgent-case-title"><b>{row.id}</b><span title={t("ลำดับความสำคัญจากระบบ ยิ่งสูงยิ่งควรตรวจสอบก่อน ไม่ใช่การคัดแยกทางคลินิก · Server operational priority; higher is reviewed first, not clinical triage", "Server operational priority; higher is reviewed first, not clinical triage")}><Tr th="ลำดับ" en="Priority" /> {row.priority}</span></div>
          <div className="v-urgent-needs">{row.needs.map((need, index) => <span className="pill" key={`${need}-${index}`}>{NEED_LABELS[need] ? <Tr th={NEED_LABELS[need][0]} en={NEED_LABELS[need][1]} /> : need}</span>)}</div>
          <p><Tr th="น้ำ" en="Depth" /> <Depth m={row.depth?.m} lo={row.depth?.lo} hi={row.depth?.hi} /></p>
          <p><Tr th="ได้ยินล่าสุด" en="Last heard" /> {row.lastHeard || t("ไม่ทราบ · Unknown", "Unknown")}<br /><Tr th="เงียบ" en="Silent" /> {Math.round(row.hoursSilent)} <Tr th="ชม." en="h" /></p>
          {row.markedFirst && <p className="v-first-mark">★ {row.markedFirst.team} · {row.markedFirst.at}</p>}
          <div className="v-urgent-actions"><button aria-pressed={!!row.markedFirst} disabled={busy || !team.trim()}
            onClick={() => void onFirst(row, team)}>{row.markedFirst ? t("ยกเลิกทำก่อน · Unmark", "Unmark") : t("★ ทำก่อน · Do first", "Do first")}</button>
            <Link className="btn btn-sec" to={`/v/case/${encodeURIComponent(row.id)}`}><Tr th="เปิด" en="Open" /></Link></div>
        </article>)}
      </section>;
    })}
  </div>;
}
