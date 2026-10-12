import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { AreaBriefingView, ZoneBriefingView } from "../../data/contract";
import { fmtDepth, fmtRange } from "../../data/format";
import { now } from "../../data/clock";
import { useView } from "../../data/useView";
import { Banner, CountBadge, EstimateRange, LastUpdated, Skeleton } from "../../ui/components";
import { Icon } from "../../ui/Icon";
import { FactList, ZoneBriefing } from "./ZoneBriefing";
import { RainLine } from "./Rain";
import { ZoneMap } from "./ZoneMap";
import "./briefing.css";

const AREAS = ["P-A", "P-B", "P-C"];
const STALE_MIN = 30;

/** Area list → zone list (or map) → zone briefing. Same IDs everywhere; the list works without the map. */
export function BriefingPage() {
  const { areaId, zoneId } = useParams();
  if (!areaId) return <AreaList />;
  return <AreaScreen areaId={areaId} zoneId={zoneId ?? null} />;
}

function AreaList() {
  return (
    <div className="page">
      <header className="page-head">
        <h1>Areas</h1>
        <p className="muted">Hat Yai, flood of Nov 2025 (synthetic demo records)</p>
      </header>
      <ul className="area-list">
        {AREAS.map((id) => (
          <AreaRow key={id} areaId={id} />
        ))}
      </ul>
    </div>
  );
}

function AreaRow({ areaId }: { areaId: string }) {
  const v = useView<AreaBriefingView>(`views/areaBriefing/${areaId}`);
  if (v.status !== "ready")
    return (
      <li className="area-row">
        {v.status === "loading" ? <Skeleton lines={2} /> : <Banner kind="error">{areaId}: briefing unavailable</Banner>}
      </li>
    );
  const a = v.data;
  return (
    <li>
      <Link to={`/team/map/${a.areaId}${window.location.search}`} className="area-row">
        <div className="row-main">
          <h2>{a.label}</h2>
          <p className="muted">{a.description}</p>
          <CountBadge urgent={a.badge.urgent} unreviewed={a.badge.unreviewed} />
        </div>
        <Icon name="chevron" size={22} />
      </Link>
    </li>
  );
}

function useNarrow() {
  const q = "(max-width: 767px)";
  const [narrow, setNarrow] = useState(() => window.matchMedia(q).matches);
  useEffect(() => {
    const m = window.matchMedia(q);
    const on = () => setNarrow(m.matches);
    m.addEventListener("change", on);
    return () => m.removeEventListener("change", on);
  }, []);
  return narrow;
}

function AreaScreen({ areaId, zoneId }: { areaId: string; zoneId: string | null }) {
  const v = useView<AreaBriefingView>(`views/areaBriefing/${areaId}`);
  const navigate = useNavigate();
  const narrow = useNarrow();
  const [mode, setMode] = useState<"list" | "map">("list");
  const keep = window.location.search;
  const openZone = (id: string | null) => navigate(`/team/map/${areaId}${id ? `/${id}` : ""}${keep}`);

  if (v.status === "loading")
    return (
      <div className="page">
        <Skeleton lines={5} />
      </div>
    );
  if (v.status === "missing")
    return (
      <div className="page">
        <Banner kind="info">No briefing for area {areaId}.</Banner>
      </div>
    );
  if (v.status === "error")
    return (
      <div className="page">
        <Banner kind="error" action={{ label: "Try again", onClick: () => window.location.reload() }}>
          Area briefing unavailable. {v.message}
        </Banner>
      </div>
    );

  const a = v.data;
  const offline = v.connection === "offline";
  const staleMin = (now() - Date.parse(a.generatedAt)) / 60000;
  const zone = zoneId ? (a.zones.find((z) => z.zoneId === zoneId) ?? null) : null;

  const list = (
    <div className="area-panel">
      <AreaHeader area={a} offline={offline} stale={staleMin > STALE_MIN} />
      <ul className="zone-list">
        {a.zones.map((z) => (
          <ZoneRow key={z.zoneId} zone={z} selected={z.zoneId === zoneId} onOpen={() => openZone(z.zoneId)} />
        ))}
      </ul>
    </div>
  );
  const map = <ZoneMap view={a} selectedZone={zoneId} onSelectZone={openZone} />;
  const briefing = zone && <ZoneBriefing zone={zone} area={a} onClose={() => openZone(null)} />;

  if (narrow)
    return (
      <div className="area-screen is-narrow">
        <div className="segmented" role="tablist" aria-label="View">
          {(["list", "map"] as const).map((m) => (
            <button key={m} role="tab" aria-selected={mode === m} onClick={() => setMode(m)}>
              <Icon name={m} size={18} /> {m === "list" ? "List" : "Map"}
            </button>
          ))}
        </div>
        {mode === "list" ? list : <div className="map-wrap">{map}</div>}
        {briefing && (
          <div className="sheet-backdrop" onClick={() => openZone(null)}>
            <div className="sheet" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
              <div className="sheet-grip" aria-hidden="true" />
              {briefing}
            </div>
          </div>
        )}
      </div>
    );

  return (
    <div className="area-screen is-wide">
      <aside className="wide-list">{list}</aside>
      <section className="wide-map">{map}</section>
      {briefing && <aside className="wide-briefing">{briefing}</aside>}
    </div>
  );
}

function AreaHeader({ area, offline, stale }: { area: AreaBriefingView; offline: boolean; stale: boolean }) {
  return (
    <header className="area-head">
      <Link to={`/team/map${window.location.search}`} className="back-link">
        <Icon name="back" size={18} /> Areas
      </Link>
      <h1>{area.label}</h1>
      <p className="muted">{area.description}</p>
      <LastUpdated at={area.generatedAt} offline={offline} />
      {offline && <Banner kind="offline">Offline. Showing the last data received; reconnecting.</Banner>}
      {!offline && stale && <Banner kind="stale">This briefing is old. Check with the desk before you go.</Banner>}
      <CountBadge urgent={area.badge.urgent} unreviewed={area.badge.unreviewed} />
      <FactList facts={area.facts} />
      <EstimateRange range={fmtRange(area.estimate.notYetChecked)}>in segments not yet checked</EstimateRange>
      <RainLine areaId={area.areaId} labels={Object.fromEntries(area.zones.flatMap((z) => z.segments.map((s) => [s.segmentId, s.label])))} />
    </header>
  );
}

function ZoneRow({ zone, selected, onOpen }: { zone: ZoneBriefingView; selected: boolean; onOpen: () => void }) {
  const evac = zone.facts.find((f) => f.key === "reviewedEvacuation")?.value;
  return (
    <li>
      <button className={`zone-row ${selected ? "is-selected" : ""}`} onClick={onOpen} aria-current={selected || undefined}>
        <div className="row-main">
          <div className="zone-row-top">
            <h3>{zone.zoneId}</h3>
            {zone.district && <span className="muted">{zone.district}</span>}
            <CountBadge urgent={zone.badge.urgent} unreviewed={zone.badge.unreviewed} empty={zone.status === "no_reports"} />
          </div>
          <p className="zone-row-line num">
            About {fmtRange(zone.estimate.everyone)} live here (estimate)
            {evac ? ` · ${evac} reported needing evacuation` : ""}
          </p>
          {zone.depth && <p className="fine-print">Depth {fmtDepth(zone.depth.modelledM)} (model)</p>}
        </div>
        <Icon name="chevron" size={20} />
      </button>
    </li>
  );
}
