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

const NEED_LABELS: Record<string, string> = {
  "can't walk": "เดินไม่ได้ · Can't walk", "cannot walk": "เดินไม่ได้ · Cannot walk",
  cannotWalk: "เดินไม่ได้ · Can't walk", elderly: "ผู้สูงอายุ · Elderly", children: "เด็ก · Children",
  "needs a ride": "ต้องการรถรับ · Needs a ride", "wants to leave": "ต้องการออก · Wants to leave",
  wantsOut: "ต้องการออก · Wants to leave", needsRide: "ต้องการรถรับ · Needs a ride",
};
export function UrgentList({ data, zones, team, busy, highlighted, focusRequest = 0, onZone, onFirst }: {
  data: UrgentView | null; zones: OverviewZone[]; team: string; busy: boolean; highlighted: string | null; focusRequest?: number;
  onZone: (id: string) => void; onFirst: (row: UrgentCase, team: string) => Promise<void>;
}) {
  const [sort, setSort] = useState<UrgentSort>("priority");
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!highlighted) return;
    const row = [...(root.current?.querySelectorAll<HTMLElement>("[data-case]") ?? [])].find(item => item.dataset.case === highlighted);
    row?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    row?.focus({ preventScroll: true });
  }, [highlighted, focusRequest]);
  return <div className="v-urgent" ref={root}>
    <label>เรียงพื้นที่ · Sort zones
      <select value={sort} onChange={event => setSort(event.target.value as UrgentSort)}>
        <option value="priority">สำคัญสุด · Priority</option>
        <option value="depth">น้ำลึกสุด · Deepest</option>
        <option value="silent">เงียบนานสุด · Longest silent</option>
      </select>
    </label>
    {!data && <p role="status">กำลังโหลด · Loading urgent cases…</p>}
    {data?.total === 0 && <p>ไม่มีรายการด่วน · No urgent cases</p>}
    {!team.trim() && <p>ตั้งชื่อทีมก่อนเลือกทำก่อน · Set your team name to mark cases</p>}
    {sortUrgentZones(data?.zones ?? [], sort).map(zone => {
      const overview = zones.find(item => item.id === zone.id);
      const go = goBy(zone.depthM);
      return <section key={zone.id} className="v-urgent-zone">
        <button className="v-urgent-heading" onClick={() => onZone(zone.id)}>
          <strong>{zone.id} · {zone.label ?? "ไม่ทราบชื่อ · Unknown place"}</strong>
          <span><Depth m={zone.depthM} /> <Trend water={overview?.water} /></span>
          <span>ไปด้วย · Go by: {go ? <>{go[0]}<small>{go[1]}</small></> : "ไม่ทราบ · Unknown"}</span>
          <span>{zone.cases.length} ด่วน · urgent · {zone.plans ? `${zone.plans} ทีม · teams` : "ไม่มีทีม · NO TEAM"}</span>
        </button>
        {zone.cases.map(row => <article key={row.id} data-case={row.id} tabIndex={-1}
          className={`v-urgent-case${highlighted === row.id ? " is-highlighted" : ""}`}>
          <div className="v-urgent-case-title"><b>{row.id}</b><span title="ลำดับความสำคัญจากระบบ ยิ่งสูงยิ่งควรตรวจสอบก่อน ไม่ใช่การคัดแยกทางคลินิก · Server operational priority; higher is reviewed first, not clinical triage">ลำดับ · Priority {row.priority}</span></div>
          <div className="v-urgent-needs">{row.needs.map((need, index) => <span className="pill" key={`${need}-${index}`}>{NEED_LABELS[need] ?? need}</span>)}</div>
          <p>น้ำ · Depth <Depth m={row.depth?.m} lo={row.depth?.lo} hi={row.depth?.hi} /></p>
          <p>ได้ยินล่าสุด · Last heard {row.lastHeard || "ไม่ทราบ · Unknown"}<br />เงียบ · Silent {Math.round(row.hoursSilent)} ชม. · h</p>
          {row.markedFirst && <p className="v-first-mark">★ {row.markedFirst.team} · {row.markedFirst.at}</p>}
          <div className="v-urgent-actions"><button aria-pressed={!!row.markedFirst} disabled={busy || !team.trim()}
            onClick={() => void onFirst(row, team)}>{row.markedFirst ? "ยกเลิกทำก่อน · Unmark" : "★ ทำก่อน · Do first"}</button>
            <Link className="btn btn-sec" to={`/v/case/${encodeURIComponent(row.id)}`}>เปิด · Open</Link></div>
        </article>)}
      </section>;
    })}
  </div>;
}
