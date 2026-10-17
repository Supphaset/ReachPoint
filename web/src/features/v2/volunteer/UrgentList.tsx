import { Tr, useT } from "../ui/lang";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { vol, type OverviewZone, type UrgentCase, type UrgentView, type UrgentZone } from "../api";
import { Depth, Trend, useTeamNameOpener } from "./shared";
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
/** The server's need words ("2 can't walk", "1 elderly", "wants to leave, needs a ride") as a Thai/English pair. */
export function needLabel(need: string): [string, string] {
  if (NEED_LABELS[need]) return NEED_LABELS[need];
  const m = need.match(/^(\d+) (can't walk|elderly|child|children)$/);
  if (m) {
    const th = { "can't walk": "เดินไม่ได้", elderly: "ผู้สูงอายุ", child: "เด็ก", children: "เด็ก" }[m[2]];
    return [`${th} ${m[1]} คน`, need];
  }
  if (need.startsWith("wants to leave")) return ["ต้องการออก ต้องมีรถรับ", "Wants to leave, needs a ride"];
  return [need, need];
}

export function UrgentSortControl({ sort, onChange }: { sort: UrgentSort; onChange: (sort: UrgentSort) => void }) {
  const t = useT();
  return <select className="v-urgent-sort" aria-label={t("เรียงพื้นที่", "Sort zones")} value={sort} onChange={event => onChange(event.target.value as UrgentSort)}>
    <option value="priority">{t("สำคัญสุด", "Priority")}</option>
    <option value="depth">{t("น้ำลึกสุด", "Deepest")}</option>
    <option value="silent">{t("เงียบนานสุด", "Longest silent")}</option>
  </select>;
}

export function UrgentList({ data, zones, team, busy, highlighted, focusRequest = 0, sort = "priority", onHighlight, onZone, onFirst }: {
  data: UrgentView | null; zones: OverviewZone[]; team: string; busy: boolean; highlighted: string | null; focusRequest?: number;
  sort?: UrgentSort; onHighlight?: (id: string | null) => void;
  onZone: (id: string) => void; onFirst: (row: UrgentCase, team: string) => Promise<void>;
}) {
  const t = useT();
  const openTeamName = useTeamNameOpener();
  const [expanded, setExpanded] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const sorted = sortUrgentZones(data?.zones ?? [], sort);
  // A map click must also reveal a case in a collapsed zone. Hover never steals focus.
  useEffect(() => {
    if (!highlighted || !focusRequest) return;
    if (sorted.slice(6).some(zone => zone.cases.some(row => row.id === highlighted))) setExpanded(true);
  }, [focusRequest]);
  useEffect(() => {
    if (!highlighted || !focusRequest) return;
    const row = [...(root.current?.querySelectorAll<HTMLElement>("[data-case]") ?? [])].find(item => item.dataset.case === highlighted);
    row?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    row?.focus({ preventScroll: true });
  }, [focusRequest, expanded]);
  return <div className="v-urgent" ref={root}>
    {/* one notice instead of a long label on every row */}
    {!team.trim() && <div className="v-urgent-team-note"><span><Tr th="ตั้งชื่อทีมเพื่อทำเครื่องหมาย “ทำก่อน”" en="Set your team name to mark cases “Do first”" /></span>
      <button className="btn btn-sec" onClick={openTeamName}><Tr th="ตั้งชื่อทีม" en="Set team name" /></button></div>}
    {!data && <p role="status"><Tr th="กำลังโหลด" en="Loading urgent cases…" /></p>}
    {data?.total === 0 && <p><Tr th="ไม่มีรายการด่วน" en="No urgent cases" /></p>}
    {sorted.slice(0, expanded ? undefined : 6).map(zone => {
      const overview = zones.find(item => item.id === zone.id);
      const go = goBy(zone.depthM);
      return <section key={zone.id} className="v-urgent-zone">
        <button className="v-urgent-heading" onClick={() => onZone(zone.id)}>
          <span className="v-urgent-zone-title"><strong>{zone.id} · {zone.label ?? t("ไม่ทราบชื่อ", "Unknown place")}</strong><b>{zone.cases.length} <Tr th="ด่วน" en="urgent" /></b></span>
          <span className="v-urgent-zone-status"><Depth m={zone.depthM} /> <Trend water={overview?.water} /><span className={`pill ${zone.plans ? "" : "p-doubt"}`}>{zone.plans ? t(`${zone.plans} ทีม · teams`, `${zone.plans} teams`) : t("ไม่มีทีม · NO TEAM", "NO TEAM")}</span></span>
          <span className="v-urgent-go"><Tr th="ไปด้วย" en="Go by:" /> {go ? t(go[0], go[1]) : t("ไม่ทราบ", "Unknown")}</span>
        </button>
        {zone.cases.map(row => <article key={row.id} data-case={row.id} tabIndex={-1}
          onMouseEnter={() => onHighlight?.(row.id)} onMouseLeave={() => onHighlight?.(null)}
          onFocus={() => onHighlight?.(row.id)} onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget)) onHighlight?.(null); }}
          className={`v-urgent-case${highlighted === row.id ? " is-highlighted" : ""}${row.markedFirst ? " is-first" : ""}`}>
          <div className="v-urgent-case-info">
            <div className="v-urgent-case-title"><b>{row.id}</b><span className="v-urgent-needs">{row.needs.filter(need => need !== "urgent").map((need, index) => <span className="pill" key={`${need}-${index}`}>{t(...needLabel(need))}</span>)}</span>
              <span className="v-priority" title={t("ลำดับความสำคัญจากระบบ ยิ่งสูงยิ่งควรตรวจสอบก่อน ไม่ใช่การคัดแยกทางคลินิก", "Server operational priority; higher is reviewed first, not clinical triage")}>{t(`P ${row.priority}`, `P ${row.priority}`)}</span>
            </div>
            <div className="v-urgent-meta"><Depth m={row.depth?.m} lo={row.depth?.lo} hi={row.depth?.hi} /><span>{t(`เงียบ ${Math.round(row.hoursSilent)} ชม.`, `silent ${Math.round(row.hoursSilent)} h`)}</span><span>{t("ล่าสุด", "last heard")} {row.lastHeard || t("ไม่ทราบ", "Unknown")}</span></div>
          </div>
          <div className="v-urgent-actions">
            <button aria-pressed={!!row.markedFirst} disabled={busy} onClick={() => { if (!team.trim()) openTeamName(); else void onFirst(row, team); }}
              title={row.markedFirst ? t(`ยกเลิกทำก่อน · ${row.markedFirst.at}`, `Unmark · ${row.markedFirst.at}`) : undefined}>
              {row.markedFirst ? <>{t("★ ทำก่อน", "★ Do first")}<span className="v-first-mark">★ {row.markedFirst.team}</span></> : t("☆ ทำก่อน", "☆ Do first")}
            </button>
            <Link className="btn btn-sec" to={`/v/case/${encodeURIComponent(row.id)}`}><Tr th="เปิด" en="Open" /></Link>
          </div>
        </article>)}
      </section>;
    })}
    {sorted.length > 6 && <button className="v-urgent-more" aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>{expanded ? t("แสดง 6 โซนแรก", "Show first 6 zones") : t(`ดูอีก ${sorted.length - 6} โซน`, `Show ${sorted.length - 6} more zones`)}</button>}
  </div>;
}
