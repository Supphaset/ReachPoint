import { Tr, useT, useUiLang, localizeNames } from "../ui/lang";
/** Shared parts of the volunteer pages: the shell and navigation, the team name, live refresh, chips and a small map. */
import { createContext, useContext, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { depthBand, v2, type CaseRow, type GeoView } from "../api";
import { StepHeader } from "../ui/Shared";
import { useMission } from "./mission";
import "../v2.css";
import "./volunteer.css";

const TEAM_KEY = "rp.v2.team";

export function useTeam(): [string, (t: string) => void] {
  const [team, setTeamState] = useState<string>(() => {
    try {
      return localStorage.getItem(TEAM_KEY) ?? "";
    } catch {
      return "";
    }
  });
  useEffect(() => {
    const sync = (event: Event) => {
      if (event instanceof CustomEvent) setTeamState(event.detail as string);
      else { try { setTeamState(localStorage.getItem(TEAM_KEY) ?? ""); } catch { /* Keep the tab's team. */ } }
    };
    window.addEventListener("reachpoint-team", sync);
    window.addEventListener("storage", sync);
    return () => { window.removeEventListener("reachpoint-team", sync); window.removeEventListener("storage", sync); };
  }, []);
  const setTeam = useCallback((t: string) => {
    setTeamState(t);
    window.dispatchEvent(new CustomEvent("reachpoint-team", { detail: t }));
    try {
      localStorage.setItem(TEAM_KEY, t);
    } catch {
      /* private window: the name lasts for this tab only */
    }
  }, []);
  return [team, setTeam];
}

/** Loads now, then again every 6 s (the board changes as messages arrive). */
export function useLive<T>(load: () => Promise<T>, deps: unknown[]): { data: T | null; error: string | null; reload: () => void } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fn = useRef(load);
  fn.current = load;
  const reload = useCallback(() => {
    fn.current().then((d) => { setData(d); setError(null); }, (e) => setError(String(e?.message ?? e)));
  }, []);
  useEffect(() => {
    setData(null);
    reload();
    const t = window.setInterval(reload, 6000);
    window.addEventListener("reachpoint-clock", reload);
    return () => {
      window.clearInterval(t);
      window.removeEventListener("reachpoint-clock", reload);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  const { lang } = useUiLang();
  const named = useMemo(() => localizeNames(data, lang), [data, lang]);
  return { data: named, error, reload };
}

let geoCache: Promise<GeoView> | null = null;
export function useGeo(): GeoView | null {
  const [g, setG] = useState<GeoView | null>(null);
  useEffect(() => {
    (geoCache ??= v2.geo()).then(setG, () => { geoCache = null; });
  }, []);
  const { lang } = useUiLang();
  return useMemo(() => localizeNames(g, lang), [g, lang]);
}

const TeamNameContext = createContext<() => void>(() => undefined);
export const useTeamNameOpener = () => useContext(TeamNameContext);

/** Navigation shared by the volunteer pages. */
export function VNavLinks() {
  const mission = useMission();
  return <>
    <NavLink to="/v" end><Tr th="ช่วยที่ไหน" en="Where help is missing" /></NavLink>
    <NavLink to="/v/feed"><Tr th="การตัดสินใจ" en="AI decisions" /></NavLink>
    {mission && <NavLink to={`/v/mission/${encodeURIComponent(mission.zoneId)}`}><Tr th="ภารกิจของฉัน" en="My mission" /></NavLink>}
  </>;
}

export function VShell({ title, sub, at, header, children }: { title: string; sub?: ReactNode; at?: string; header?: ReactNode; children: ReactNode }) {
  const t = useT();
  const [team, setTeam] = useTeam();
  const [editing, setEditing] = useState(false);
  const teamInput = useRef<HTMLInputElement>(null);
  const openTeamName = () => { setEditing(true); teamInput.current?.focus(); };
  return (
    <TeamNameContext.Provider value={openTeamName}><main className="v-page rp-app">
      <StepHeader at={at} onAction={async action => { await v2.clock(action); window.dispatchEvent(new Event("reachpoint-clock")); }} />
      <nav className="rp-subnav" aria-label={t("หน้าอาสา", "Volunteer pages")}>
        <span className="rp-subnav-label"><Tr th="อาสา" en="Volunteers" /></span>
        <VNavLinks />
        <div className="v-team">
          {editing ? (
            <form onSubmit={(e) => { e.preventDefault(); setEditing(false); }}>
              <label htmlFor="v-team-name" className="v-sr"><Tr th="ชื่อทีมของคุณ" en="Your team name" /></label>
              <input ref={teamInput} id="v-team-name" autoFocus value={team} onChange={(e) => setTeam(e.target.value)} placeholder={t("e.g. ทีมเรือกู้ภัยหาดใหญ่ 1", "e.g. Hat Yai rescue boat 1")} />
              <button type="submit"><Tr th="บันทึก" en="Save" /></button>
            </form>
          ) : (
            <button type="button" className="v-team-btn" onClick={openTeamName} title={t("ทีมเห็นที่อยู่ในโซนที่มีแผนของตน", "Teams see exact addresses in zones their own plans cover")}>
              {team ? <><Tr th="ทีม" en="Team:" /> <b>{team}</b></> : t("ชื่อทีม · Set team name", "Set team name")}
            </button>
          )}
        </div>
      </nav>
      <div className="v-body">
        <div className="v-titlebar">
          <div>
            <h1>{title}</h1>
            {sub ? <p className="v-sub">{sub}</p> : null}
          </div>
        </div>
        {header}
        {children}
      </div>
    </main></TeamNameContext.Provider>
  );
}

export function StatusChip({ r }: { r: Pick<CaseRow, "status" | "urgent" | "outcome"> }) {
  if (r.outcome?.kind === "pickedUp") return <span className="v2-chip is-green">Picked up · {r.outcome.team}</span>;
  if (r.status === "nobodyThere") return <span className="v2-chip is-amber">Nobody there</span>;
  if (r.status === "atShelter") return <span className="v2-chip is-green">At a shelter</span>;
  if (r.status === "toShelter") return <span className="v2-chip is-blue">Walking to a shelter</span>;
  if (r.urgent) return <span className="v2-chip is-red">Urgent</span>;
  if (r.status === "lostContact") return <span className="v2-chip is-amber">Not answering</span>;
  if (r.status === "evacuated") return <span className="v2-chip is-green">Evacuated</span>;
  if (r.status === "safe") return <span className="v2-chip is-green">Safe</span>;
  return <span className="v2-chip">Waiting</span>;
}

export function Depth({ m, lo, hi }: { m: number | null | undefined; lo?: number; hi?: number }) {
  const t = useT();
  if (m === null || m === undefined) return <span className="v-depth is-unknown"><Tr th="ไม่ทราบ" en="unknown" /></span>;
  return (
    <span className={`v-depth is-${depthBand(m)}`} title={lo !== undefined ? t(`คาดว่า ${lo.toFixed(1)}–${hi?.toFixed(1)} ม.`, `likely ${lo.toFixed(1)}–${hi?.toFixed(1)} m`) : undefined}>
      {m.toFixed(1)} <Tr th="ม." en="m" />
    </span>
  );
}

export function Needs({ r }: { r: CaseRow }) {
  return (
    <span className="v-needs">
      {r.needs.filter(need => /wants.*leave|needs.*ride|ต้องการออก|ต้องการ.*รถ/i.test(need)).map(need => <span key={need} className="is-strong"><Tr th="ต้องการออก ต้องมีรถรับ ·" en="Wants to leave, needs a ride ·" /> {need}</span>)}
      {r.people ? <span>{r.people} people</span> : <span className="v-muted">people ?</span>}
      {r.cannotWalk ? <span className="is-strong">{r.cannotWalk} can't walk</span> : null}
      {r.elderly ? <span>{r.elderly} elderly</span> : null}
      {r.children ? <span>{r.children} {r.children === 1 ? "child" : "children"}</span> : null}
    </span>
  );
}

/** A small drawn map: zone outlines and household dots, coloured by state. Click a dot to open its case. */
export function MiniMap({ geo, zoneId, rows, onPick, height = 280, mark, zoneTone, onZone, shelters, cells, onCell }: {
  geo: GeoView | null;
  zoneId?: string;
  rows: Pick<CaseRow, "id" | "lon" | "lat" | "status" | "urgent" | "outcome" | "needs" | "depth">[];
  onPick?: (id: string) => void;
  height?: number;
  mark?: string;
  zoneTone?: Record<string, string>;
  onZone?: (id: string) => void;
  shelters?: { id: string; name: string; lon: number; lat: number; people?: number }[];
  cells?: { id: string; name: string | null; geometry?: GeoJSON.Polygon | GeoJSON.MultiPolygon; need: number; open: number; access?: string }[];
  onCell?: (id: string) => void;
}) {
  const shapes = useMemo(() => {
    if (!geo) return null;
    const feats = geo.zones.features.filter((f) => !zoneId || (f.properties as { id: string }).id === zoneId);
    const rings: { id: string; ring: number[][] }[] = [];
    for (const f of feats) {
      const g = f.geometry as GeoJSON.Polygon | GeoJSON.MultiPolygon;
      const polys = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
      for (const p of polys) rings.push({ id: (f.properties as { id: string }).id, ring: p[0] });
    }
    const pts = [...rings.flatMap((r) => r.ring), ...(zoneId ? [] : (shelters ?? []).map((s) => [s.lon, s.lat]))];
    const xs = pts.map((p) => p[0]);
    const ys = pts.map((p) => p[1]);
    return { rings, box: [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)] };
  }, [geo, zoneId, shelters?.length]);
  if (!shapes) return <div className="v-minimap is-loading" style={{ height }} />;
  const [w, s, e, n] = shapes.box;
  const k = Math.cos((((s + n) / 2) * Math.PI) / 180);
  const W = 600;
  const H = Math.max(160, Math.min(600, (W * (n - s)) / ((e - w) * k)));
  const px = (lon: number) => ((lon - w) / (e - w)) * (W - 20) + 10;
  const py = (lat: number) => ((n - lat) / (n - s)) * (H - 20) + 10;
  return (
    <svg className="v-minimap" viewBox={`0 0 ${W} ${H}`} style={{ maxHeight: height }} role="img" aria-label="Map of households">
      {shapes.rings.map((r, i) => (
        <path
          key={i}
          d={r.ring.map((p, j) => `${j ? "L" : "M"}${px(p[0]).toFixed(1)} ${py(p[1]).toFixed(1)}`).join(" ") + "Z"}
          className={`v-minimap-zone ${zoneTone?.[r.id] ?? ""}${onZone ? " is-link" : ""}`}
          onClick={onZone ? () => onZone(r.id) : undefined}
        >
          <title>{`Zone ${r.id}`}</title>
        </path>
      ))}
      {(cells ?? []).filter((c) => c.geometry).map((c) => {
        const g = c.geometry!;
        const rings = g.type === "Polygon" ? [g.coordinates[0]] : g.coordinates.map((p) => p[0]);
        const d = rings.map((r) => r.map((p, j) => `${j ? "L" : "M"}${px(p[0]).toFixed(1)} ${py(p[1]).toFixed(1)}`).join(" ") + "Z").join(" ");
        return (
          <path key={c.id} d={d} className={`v-block is-${c.access ?? "unknown"}${c.open ? " has-open" : ""}${onCell ? " is-link" : ""}`}
            onClick={onCell ? () => onCell(c.id) : undefined}>
            <title>{`${c.id}${c.name ? ` · ${c.name}` : ""} · ${c.open} families waiting · ${c.access === "walk" ? "can walk out" : c.access === "truck" ? "high truck" : c.access === "boat" ? "boat needed" : "unknown"}`}</title>
          </path>
        );
      })}
      {(shelters ?? []).filter((s) => s.lon >= w && s.lon <= e && s.lat >= s0(shapes) && s.lat <= n).map((s) => (
        <g key={s.id} className="v-shelter">
          <rect x={px(s.lon) - 6} y={py(s.lat) - 6} width={12} height={12} rx={2}><title>{`${s.name}${s.people !== undefined ? ` · ${s.people} people checked in` : ""}`}</title></rect>
        </g>
      ))}
      {rows.filter((r) => r.lon !== null && r.lat !== null).map((r) => (
        <circle
          key={r.id}
          cx={px(r.lon!)}
          cy={py(r.lat!)}
          r={r.id === mark ? 7 : r.urgent ? 5 : 4}
          className={`v-dot is-${r.outcome?.kind === "pickedUp" ? "evacuated" : r.status}${r.urgent ? " is-urgent" : ""}${r.id === mark ? " is-mark" : ""}`}
          onClick={onPick ? () => onPick(r.id) : undefined}
        >
          <title>{`${r.id} · ${r.needs.join(", ") || "no special needs"}${r.depth ? ` · ${r.depth.m.toFixed(1)} m` : ""}`}</title>
        </circle>
      ))}
    </svg>
  );
}

function s0(shapes: { box: number[] }): number {
  return shapes.box[1];
}

export function fmtTags(tags: string[]): { key: string; label: string; tone: string }[] {
  const L: Record<string, [string, string]> = {
    urgent: ["Urgent", "is-red"], new: ["New family", "is-blue"], merged: ["Merged", ""], doubtful: ["Doubtful", "is-amber"],
    possibleDuplicate: ["Possible duplicate", "is-amber"], lostContact: ["Not answering", "is-amber"], neighbour: ["Neighbour", "is-blue"],
    team: ["Team visit", "is-green"],
  };
  return tags.filter((t) => L[t]).map((t) => ({ key: t, label: L[t][0], tone: L[t][1] }));
}

/** "↑ rising ~0.2 m in 6 h": the trend a team needs before it sets out (water rising = go sooner, bigger boat). */
export function Trend({ water, long = false }: { water: import("../api").WaterTrend | null | undefined; long?: boolean }) {
  if (!water) return <span className="p3-trend"><Tr th="แนวโน้มไม่ทราบ" en="trend unknown" /></span>;
  const arrow = { rising: "↑", falling: "↓", steady: "→" }[water.trend];
  const word = { rising: <Tr th="น้ำขึ้น" en="Rising" />, falling: <Tr th="น้ำลด" en="Falling" />, steady: <Tr th="ทรงตัว" en="Steady" /> }[water.trend];
  const change = Math.abs(water.next6hM);
  return <span className={`p3-trend is-${water.trend}`}>{arrow} {word}
    {long && water.trend !== "steady" && <> <Tr th={<>~{change.toFixed(1)} ม. ใน 6 ชม.</>} en={<>~{change.toFixed(1)} m in 6 h</>} /></>}</span>;
}
