import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { AreaBriefingView, ZoneBriefingView } from "../../data/contract";
import { fmtDepth, fmtRange } from "../../data/format";
import { now } from "../../data/clock";
import { useView } from "../../data/useView";
import { Banner, CountBadge, EstimateRange, LastUpdated, Skeleton } from "../../ui/components";
import { Icon } from "../../ui/Icon";
import { FactList, ZoneBriefing } from "./ZoneBriefing";
import { GaugeLine, RainLine } from "./Rain";
import { ZoneMap } from "./ZoneMap";
import { useLang } from "../../i18n/lang";
import { S, seedText } from "../../i18n/strings";
import { areaText } from "../../i18n/briefing";
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
  const { t } = useLang();
  return (
    <div className="page">
      <header className="page-head">
        <h1>{t(S.briefing.areas)}</h1>
        <p className="muted">{t(S.briefing.areasLead)}</p>
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
  const { t, lang } = useLang();
  if (v.status !== "ready")
    return (
      <li className="area-row">
        {v.status === "loading" ? <Skeleton lines={2} /> : <Banner kind="error">{t(S.briefing.unavailable(areaId))}</Banner>}
      </li>
    );
  const a = v.data;
  const txt = areaText(a.areaId, a.label, a.description, lang);
  return (
    <li>
      <Link to={`/team/map/${a.areaId}${window.location.search}`} className="area-row">
        <div className="row-main">
          <h2>{txt.label}</h2>
          <p className="muted">{txt.description}</p>
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
  const { t } = useLang();
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
        <Banner kind="info">{t(S.briefing.noBriefing(areaId))}</Banner>
      </div>
    );
  if (v.status === "error")
    return (
      <div className="page">
        <Banner kind="error" action={{ label: t(S.common.tryAgain), onClick: () => window.location.reload() }}>
          {t(S.briefing.areaUnavailable)} {v.message}
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
        <div className="segmented" role="tablist" aria-label={t(S.briefing.view)}>
          {(["list", "map"] as const).map((m) => (
            <button key={m} role="tab" aria-selected={mode === m} onClick={() => setMode(m)}>
              <Icon name={m} size={18} /> {m === "list" ? t(S.briefing.list) : t(S.briefing.map)}
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
  const { t, lang } = useLang();
  const txt = areaText(area.areaId, area.label, area.description, lang);
  return (
    <header className="area-head">
      <Link to={`/team/map${window.location.search}`} className="back-link">
        <Icon name="back" size={18} /> {t(S.briefing.areas)}
      </Link>
      <h1>{txt.label}</h1>
      <p className="muted">{txt.description}</p>
      <LastUpdated at={area.generatedAt} offline={offline} />
      {offline && <Banner kind="offline">{t(S.briefing.offline)}</Banner>}
      {!offline && stale && <Banner kind="stale">{t(S.briefing.old)}</Banner>}
      <CountBadge urgent={area.badge.urgent} unreviewed={area.badge.unreviewed} />
      <FactList facts={area.facts} />
      <EstimateRange range={fmtRange(area.estimate.notYetChecked)}>{t(S.briefing.notYetChecked)}</EstimateRange>
      <GaugeLine areaId={area.areaId} />
      <RainLine areaId={area.areaId} labels={Object.fromEntries(area.zones.flatMap((z) => z.segments.map((s) => [s.segmentId, seedText(s.label, lang)])))} />
    </header>
  );
}

function ZoneRow({ zone, selected, onOpen }: { zone: ZoneBriefingView; selected: boolean; onOpen: () => void }) {
  const { t, lang } = useLang();
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
          <p className="zone-row-line num">{t(S.briefing.zoneLine(fmtRange(zone.estimate.everyone), evac ?? null))}</p>
          {zone.depth && <p className="fine-print">{t(S.briefing.depthModel(fmtDepth(zone.depth.modelledM, 3, lang)))}</p>}
        </div>
        <Icon name="chevron" size={20} />
      </button>
    </li>
  );
}
