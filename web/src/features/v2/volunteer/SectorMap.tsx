import { Tr, useT, useUiLang, t as translate, type UiLang } from "../ui/lang";
import { useEffect, useRef, useState } from "react";
import { loadGoogleMaps, type Maps } from "../../../data/googleMaps";
import type { BoardState, GeoView, OverviewZone, Shelter, UrgentCase } from "../api";
import { useFloodCanvas } from "../BoardMap";
import { bindFloodZoom } from "../floodLayer";
import type { Selection } from "./selection";

function rings(feature: GeoJSON.Feature): number[][][] {
  const geometry = feature.geometry;
  return geometry.type === "Polygon" ? geometry.coordinates : geometry.type === "MultiPolygon" ? geometry.coordinates.flat() : [];
}
function bounds(features: GeoJSON.Feature[]) {
  const points = features.flatMap(feature => rings(feature).flat());
  if (!points.length) return [100.43, 6.97, 100.52, 7.05];
  return [Math.min(...points.map(p => p[0])), Math.min(...points.map(p => p[1])), Math.max(...points.map(p => p[0])), Math.max(...points.map(p => p[1]))];
}
export function needBand(zone: OverviewZone | undefined, maximum: number) {
  if (!zone || !zone.open) return 0;
  return zone.score > maximum * 0.66 ? 3 : zone.score > maximum * 0.33 ? 2 : 1;
}

/** Greedy placement in priority order, in projected pixels; runs again whenever the map draws. */
export function deoverlapLabels<T extends { x: number; y: number }>(candidates: T[], distance = 70): T[] {
  const placed: T[] = [];
  for (const candidate of candidates) {
    if (placed.every(point => Math.hypot(point.x - candidate.x, point.y - candidate.y) >= distance)) placed.push(candidate);
  }
  return placed;
}

/** Shared geometry and ids drive both outlines and the list; urgent dots use only API-provided positions. */
export function DrawnSectorMap({ geo, zones, selection, onZone, onSector, urgentCases, onCase }: { urgentCases?: UrgentCase[]; onCase?: (id: string) => void; geo: GeoView | null; zones: OverviewZone[]; selection: Selection; onZone: (id: string) => void; onSector: (id: string) => void }) {
  const t = useT();
  const frame = useRef<SVGSVGElement>(null);
  const [zoom, setZoom] = useState(1);
  const [size, setSize] = useState({ width: 900, height: 700 });
  useEffect(() => {
    if (!frame.current || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      if (width && height) setSize({ width, height });
    });
    observer.observe(frame.current);
    return () => observer.disconnect();
  }, [!!geo]);
  if (!geo) return <p role="status"><Tr th="กำลังโหลดแผนที่" en="Loading sectors…" /></p>;
  const sectorFeatures = geo.sectors?.features ?? [];
  const selectedFeatures = selection.sector ? geo.zones.features.filter(feature => feature.properties?.sector === selection.sector || zones.find(zone => zone.id === feature.properties?.id)?.sector === selection.sector) : [];
  const [west, south, east, north] = bounds(selectedFeatures.length ? selectedFeatures : geo.zones.features);
  const spanX = Math.max(east - west, 0.001);
  const spanY = Math.max(north - south, 0.001);
  const longitudeScale = Math.cos((south + north) / 2 * Math.PI / 180);
  const scale = zoom * Math.min((size.width - 56) / (spanX * longitudeScale), (size.height - 56) / spanY);
  const x = (lon: number) => size.width / 2 + (lon - (west + east) / 2) * longitudeScale * scale;
  const y = (lat: number) => size.height / 2 - (lat - (south + north) / 2) * scale;
  const path = (feature: GeoJSON.Feature) => rings(feature).map(ring => ring.map(([lon, lat], index) => `${index ? "L" : "M"}${x(lon)} ${y(lat)}`).join(" ") + "Z").join(" ");
  const maximum = Math.max(1, ...zones.map(zone => zone.score));
  const top = [...zones].sort((a, b) => b.score - a.score).slice(0, 5).map(zone => zone.id);
  return <><div className="p3-fallback-zoom" aria-label={t("ซูม · Zoom", "Zoom")}><button aria-label={t("ขยาย · Zoom in", "Zoom in")} onClick={() => setZoom(value => Math.min(3, value + 0.25))}>+</button><button aria-label={t("ย่อ · Zoom out", "Zoom out")} onClick={() => setZoom(value => Math.max(0.75, value - 0.25))}>−</button></div><svg ref={frame} className="p3-sector-map" viewBox={`0 0 ${size.width} ${size.height}`} aria-label="Team zones by help missing; thick sector boundaries A to G">
    {geo.zones.features.map(feature => {
      const id = String(feature.properties?.id);
      const zone = zones.find(candidate => candidate.id === id);
      const b = bounds([feature]);
      return <g key={id} role="button" tabIndex={0} aria-label={`Zone ${id}, ${zone?.open ?? "unknown"} waiting`} aria-pressed={selection.zone === id} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onZone(id); } }} onClick={() => onZone(id)}>
        <path d={path(feature)} className={`p3-zone ${selection.zone === id ? "is-selected" : ""}`} style={{ fill: `var(--need-${needBand(zone, maximum)})`, strokeDasharray: zone?.open && !zone.plans ? "8 5" : undefined }}><title>{`${id} · ${zone?.label ?? t("ไม่ทราบชื่อ", "Unknown place")} · ${zone?.open ?? "unknown"} waiting`}</title></path>
        {((selection.sector && zone?.sector === selection.sector) || top.includes(id)) && <text x={x((b[0] + b[2]) / 2)} y={y((b[1] + b[3]) / 2)} className="p3-zone-label">{id} · {zone?.label ?? t("ไม่ทราบชื่อ", "Unknown place")}</text>}
      </g>;
    })}
    {(urgentCases ?? []).filter(row => row.lon != null && row.lat != null).map(row => <g key={row.id} className="p3-drawn-urgent" role="button" tabIndex={0}
      aria-label={t(`ด่วน · Urgent ${row.id}`, `Urgent ${row.id}`)} onClick={() => onCase?.(row.id)}
      onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onCase?.(row.id); } }}>
      <circle cx={x(row.lon!)} cy={y(row.lat!)} r="22" className="p3-drawn-hit" />
      <circle cx={x(row.lon!)} cy={y(row.lat!)} r="5" />
      {row.markedFirst && <text x={x(row.lon!)} y={y(row.lat!) - 10}>★</text>}
    </g>)}
    {sectorFeatures.map(feature => {
      const id = String(feature.properties?.id);
      const b = bounds([feature]);
      const highlighted = selection.hover === id || selection.sector === id;
      return <g key={id} style={{ color: `var(--sector-${id})` }}>
        <path d={path(feature)} className={`p3-sector ${highlighted ? "is-highlighted" : ""}`} />
        <g className="p3-sector-badge" role="button" tabIndex={0} aria-label={`Sector ${id}`} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSector(id); } }} onClick={() => onSector(id)}>
          <circle className="p3-badge-hit" cx={x((b[0] + b[2]) / 2)} cy={y((b[1] + b[3]) / 2)} r="22" />
          <circle cx={x((b[0] + b[2]) / 2)} cy={y((b[1] + b[3]) / 2)} r="15" />
          <text x={x((b[0] + b[2]) / 2)} y={y((b[1] + b[3]) / 2)}>{id}</text>
        </g>
      </g>;
    })}
  </svg></>;
}


type Props = Parameters<typeof DrawnSectorMap>[0] & {
  /** The replay hour and message count: the water layer redraws (model + reports) when either changes. */
  water?: { hour: number; messages: number };
  shelters?: Shelter[];
  urgentCases?: UrgentCase[];
  onCase?: (id: string) => void;
};

/** What the depth means for a team: the first thing a volunteer asks is "can we get there, and with what?" */
export const GO_BY: [string, string, string][] = [
  ["--depth-1", "ต่ำกว่า 0.5 ม. · เดิน/รถสูงได้", "under 0.5 m · walk or high truck"],
  ["--depth-2", "0.5–1 ม. · รถสูงเสี่ยง ใช้เรือดีกว่า", "0.5–1 m · high truck risky, boat better"],
  ["--depth-3", "1–2 ม. · เรือเท่านั้น", "1–2 m · boat only"],
  ["--depth-4", "เกิน 2 ม. · เรือ ระวังกระแสน้ำ", "over 2 m · boat, watch the current"],
];

export function goBy(depthM: number | null | undefined): [string, string] | null {
  if (depthM == null) return null;
  const row = GO_BY[depthM < 0.5 ? 0 : depthM < 1 ? 1 : depthM < 2 ? 2 : 3];
  return [row[1], row[2]];
}

/** Keep geographic labels readable; the data layer only adds need and coverage. */
// The need ramp is pale on purpose; on the street map it needs more alpha as need grows, and none where nobody waits.
const FILL = [0, 0.3, 0.45, 0.6];

export function drawSectorLayers(maps: Maps, map: Maps, props: Props, token: (name: string) => string, waterOn = false, lang: UiLang = "th") {
  const t = (th: string, en: string) => translate(th, en, lang);
  const { geo, zones, selection, onZone, onSector } = props;
  const overlays: Maps[] = [];
  if (!geo) return () => undefined;
  const maximum = Math.max(1, ...zones.map(zone => zone.score));
  const top = [...zones].sort((a, b) => b.score - a.score).slice(0, 5).map(zone => zone.id);
  // city view: bubbles only on the 12 zones with the most urgent cases; a chosen sector shows all of its zones
  const mostUrgent = new Set([...zones].filter(zone => zone.urgent).sort((a, b) => b.urgent - a.urgent).slice(0, 12).map(zone => zone.id));
  const labelFeatures = [...geo.zones.features].sort((a, b) =>
    (zones.find(zone => zone.id === b.properties?.id)?.score ?? 0) - (zones.find(zone => zone.id === a.properties?.id)?.score ?? 0));
  const label = (feature: GeoJSON.Feature, text: string, sector: boolean, select: () => void, bubble = false) => {
    const [lng, lat] = featureCentroid(feature);
    const overlay = new maps.OverlayView();
    const button = document.createElement("button");
    const zone = zones.find(item => item.id === feature.properties?.id);
    button.className = sector ? "p3-google-badge" : bubble ? `p3-count-bubble${zone?.urgent ? " is-urgent" : ""}` : "p3-google-label";
    button.textContent = text;
    button.setAttribute("aria-label", sector ? t(`พื้นที่ · Sector ${text}`, `Sector ${text}`) : t(`โซน · Zone ${feature.properties?.id} · ${text}`, `Zone ${feature.properties?.id} · ${text}`));
    button.setAttribute("aria-pressed", String(sector ? selection.sector === text : selection.zone === feature.properties?.id));
    button.onclick = select;
    maps.OverlayView.preventMapHitsAndGesturesFrom?.(button);
    overlay.onAdd = () => overlay.getPanes().overlayMouseTarget.appendChild(button);
    overlay.draw = () => {
      const projection = overlay.getProjection();
      const zoom = map.getZoom() ?? 12;
      const point = projection.fromLatLngToDivPixel(new maps.LatLng(lat, lng));
      let visible = sector ? zoom <= 14 : true;
      if (!sector && !bubble) {
        const candidates = labelFeatures.filter(item => {
          const id = String(item.properties?.id);
          return zoom >= 16 || top.includes(id) || zones.find(zone => zone.id === id)?.sector === selection.sector && !!selection.sector;
        }).flatMap(item => {
          const [lon, latitude] = featureCentroid(item);
          const position = new maps.LatLng(latitude, lon);
          const container = projection.fromLatLngToContainerPixel(position);
          const div = projection.fromLatLngToDivPixel(position);
          const host = map.getDiv();
          // Reserve the control strip and keep labels inside the visible map.
          if (!container || !div || container.x < 24 || container.x > host.clientWidth - 24 || container.y < 76 || container.y > host.clientHeight - 60) return [];
          return [{ id: String(item.properties?.id), x: div.x, y: div.y }];
        });
        visible = deoverlapLabels(candidates).some(item => item.id === feature.properties?.id);
      }
      button.hidden = !visible || !point;
      if (point) { button.style.left = `${point.x}px`; button.style.top = `${point.y - (!sector && !bubble && waterOn && zone?.open ? 36 : 0)}px`; }
    };
    overlay.onRemove = () => { button.onclick = null; button.remove(); };
    overlay.setMap(map);
    overlays.push(overlay);
  };
  for (const feature of geo.zones.features) {
    const id = String(feature.properties?.id);
    const zone = zones.find(item => item.id === id);
    const band = needBand(zone, maximum);
    const paths = rings(feature).map(ring => ring.map(([lng, lat]) => ({ lng, lat })));
    const components = feature.geometry.type === "MultiPolygon" ? feature.geometry.coordinates.map(polygon => polygon.map(ring => ring.map(([lng, lat]) => ({ lng, lat })))) : [paths];
    for (const component of components) {
      const polygon = new maps.Polygon({ map, paths: component, fillColor: token(`--need-${band}`), fillOpacity: waterOn ? 0 : FILL[band],
      strokeColor: token("--ink-1"), strokeWeight: selection.zone === id ? 5 : zone?.open && !zone.plans ? 2 : 1,
      strokeOpacity: selection.zone === id ? 1 : 0.55, zIndex: selection.zone === id ? 3 : 1 });
      polygon.addListener("click", () => onZone(id));
      overlays.push(polygon);
    }
    // One bubble per zone with urgent cases (the count in red); waiting-only counts appear inside a chosen sector.
    // A bubble on every zone made the map unreadable.
    const inSector = !!selection.sector && zone?.sector === selection.sector;
    if (waterOn && zone?.open && ((zone.urgent && mostUrgent.has(id)) || inSector)) label(feature, String(zone.urgent || zone.open), false, () => onZone(id), true);
    const arrow = zone?.water?.trend === "rising" ? " ↑" : zone?.water?.trend === "falling" ? " ↓" : "";
    label(feature, `${id} · ${zone?.label ?? feature.properties?.label ?? t("ไม่ทราบชื่อ", "Unknown place")}${arrow}`, false, () => onZone(id));
  }
  for (const feature of geo.sectors?.features ?? []) {
    const id = String(feature.properties?.id);
    const polygon = new maps.Polygon({ map, paths: rings(feature).map(ring => ring.map(([lng, lat]) => ({ lng, lat }))),
      fillOpacity: 0, strokeColor: token("--ink-1"), strokeWeight: selection.sector === id || selection.hover === id ? 5 : 2.5, strokeOpacity: 0.85,
      clickable: false, zIndex: 2 });
    overlays.push(polygon);
    label(feature, id, true, () => onSector(id));
  }
  for (const row of props.urgentCases ?? []) {
    if (row.lon == null || row.lat == null) continue;
    const overlay = new maps.OverlayView();
    const button = document.createElement("button");
    button.className = `p3-urgent-dot${row.markedFirst ? " is-first" : ""}`;
    button.textContent = row.markedFirst ? "★" : "";
    button.setAttribute("aria-label", t(`ด่วน · Urgent ${row.id}${row.markedFirst ? ` · ทำก่อน · Do first ${row.markedFirst.team}` : ""}`, `Urgent ${row.id}${row.markedFirst ? ` · Do first ${row.markedFirst.team}` : ""}`));
    button.onclick = () => props.onCase?.(row.id);
    maps.OverlayView.preventMapHitsAndGesturesFrom?.(button);
    overlay.onAdd = () => overlay.getPanes().overlayMouseTarget.appendChild(button);
    overlay.draw = () => {
      const point = overlay.getProjection().fromLatLngToDivPixel(new maps.LatLng(row.lat, row.lon));
      if (point) { button.style.left = `${point.x}px`; button.style.top = `${point.y}px`; }
    };
    overlay.onRemove = () => { button.onclick = null; button.remove(); };
    overlay.setMap(map);
    overlays.push(overlay);
  }
  // Shelters: where a team drops people off. Green dot, name on hover/tap.
  for (const shelter of props.shelters ?? []) {
    overlays.push(new maps.Marker({ map, position: { lat: shelter.lat, lng: shelter.lon }, zIndex: 4,
      title: `${t("ศูนย์พักพิง · Shelter", "Shelter")}: ${shelter.name}${shelter.capacity ? ` (${shelter.households}/${shelter.capacity})` : ""}`,
      icon: { path: maps.SymbolPath.CIRCLE, scale: 7, fillColor: token("--shelter"), fillOpacity: 1, strokeColor: token("--shelter-ink"), strokeWeight: 2 } }));
  }
  const zoomListener = map.addListener?.("zoom_changed", () => overlays.forEach(overlay => overlay.draw?.()));
  return () => { zoomListener?.remove(); overlays.forEach(overlay => { maps.event.clearInstanceListeners(overlay); overlay.setMap(null); }); };
}

export function SectorMap(props: Props) {
  const { lang } = useUiLang();
  const t = useT();
  const host = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState<{ maps: Maps; map: Maps } | null>(null);
  const [failed, setFailed] = useState(false);
  const [kind, setKind] = useState("roadmap");
  const refit = useRef<() => void>(() => undefined);
  const [waterOn, setWaterOn] = useState(true);
  // useAnalysis only reads the clock and the message count, so the overview's numbers stand in for the board state.
  const clock = props.water ? { now: { atH: props.water.hour }, overall: { messages: props.water.messages } } as unknown as BoardState : null;
  const flood = useFloodCanvas(props.geo, clock, props.water?.hour ?? 0, waterOn && props.water ? "corrected" : "off");
  useEffect(() => {
    let active = true;
    let resize: ResizeObserver | undefined;
    let instance: Maps;
    loadGoogleMaps("en").then(maps => {
      if (!active || !host.current) return;
      host.current.hidden = false;
      instance = new maps.Map(host.current, { center: { lat: 7.01, lng: 100.47 }, zoom: 12, mapTypeId: "roadmap",
        disableDefaultUI: true, zoomControl: true, keyboardShortcuts: true, gestureHandling: "greedy", isFractionalZoomEnabled: true });
      setReady({ maps, map: instance });
      // The first fit can run before the map has its real size; fit again once it has drawn.
      maps.event.addListenerOnce(instance, "idle", () => refit.current());
      if (typeof ResizeObserver !== "undefined") {
        resize = new ResizeObserver(() => { maps.event.trigger(instance, "resize"); refit.current(); });
        resize.observe(host.current);
      }
    }).catch(() => { if (active) setFailed(true); });
    return () => { active = false; resize?.disconnect(); if (instance) { instance.unbindAll(); } };
  }, []);
  useEffect(() => { ready?.map.setMapTypeId(kind); }, [ready, kind]);
  // Water sits in the map pane: under the zone shapes and labels, over the streets.
  useEffect(() => {
    if (!ready || !flood.sim) return;
    const { maps, map } = ready;
    const [west, south, east, north] = flood.sim.meta.bbox;
    const canvas = flood.canvas;
    canvas.className = "v2-flood-canvas";
    const water = new class extends maps.OverlayView {
      onAdd() { this.getPanes().mapPane.appendChild(canvas); }
      draw() {
        const projection = this.getProjection();
        const sw = projection.fromLatLngToDivPixel(new maps.LatLng(south, west));
        const ne = projection.fromLatLngToDivPixel(new maps.LatLng(north, east));
        Object.assign(canvas.style, { left: `${sw.x}px`, top: `${ne.y}px`, width: `${ne.x - sw.x}px`, height: `${sw.y - ne.y}px` });
      }
      onRemove() { canvas.remove(); }
    }();
    water.setMap(map);
    const unbind = bindFloodZoom(map, canvas);
    return () => { unbind(); water.setMap(null); };
  }, [ready, flood.sim, flood.canvas]);

  // Polling hands us new arrays every few seconds; redraw only when what the map shows has changed,
  // so labels don't flicker and keyboard focus stays put. Clicks always reach the latest handlers.
  const latest = useRef(props);
  latest.current = props;
  const { selection } = props;
  const drawn = [props.geo?.zones.features.length ?? 0, waterOn, props.shelters?.length ?? 0, selection.zone, selection.sector, selection.hover,
    ...(props.urgentCases ?? []).map(row => `${row.id}:${row.lon}:${row.lat}:${row.markedFirst?.team}:${row.markedFirst?.at}`),
    ...props.zones.map(zone => `${zone.id}:${zone.label}:${zone.score}:${zone.open}:${zone.urgent}:${zone.plans}:${zone.water?.trend}`)].join("|");
  useEffect(() => {
    if (!ready) return;
    const styles = getComputedStyle(document.documentElement);
    return drawSectorLayers(ready.maps, ready.map, {
      ...latest.current,
      onZone: id => latest.current.onZone(id),
      onSector: id => latest.current.onSector(id),
    }, name => styles.getPropertyValue(name).trim(), waterOn && !!props.water, lang);
  }, [ready, drawn, lang]);
  useEffect(() => {
    if (!ready || !props.geo) return;
    const { selection, zones, geo } = props;
    const features = geo.zones.features.filter(feature => selection.zone ? feature.properties?.id === selection.zone
      : selection.sector ? zones.find(zone => zone.id === feature.properties?.id)?.sector === selection.sector : true);
    if (!features.length) return;
    const [w, s, e, n] = bounds(features);
    refit.current = () => {
      if (selection.zone) { ready.map.panTo({ lat: (s + n) / 2, lng: (w + e) / 2 }); ready.map.setZoom(16); }
      else ready.map.fitBounds({ west: w, south: s, east: e, north: n }, 24);
    };
    refit.current();
  }, [ready, props.geo, props.selection.zone, props.selection.sector]);
  return <div className="p3-map-stage">
    <div ref={host} className="p3-google-map" aria-label={t("แผนที่หาดใหญ่ · Hat Yai map", "Hat Yai map")} style={{ visibility: ready ? "visible" : "hidden", position: ready ? "relative" : "absolute" }} />
    {!ready && <><p className="p3-map-status" role="status">{failed ? t("แผนที่สำรอง · Offline outline map", "Offline outline map") : t("กำลังเปิดแผนที่ · Loading map", "Loading map")}</p><DrawnSectorMap {...props} /></>}
    {ready && <div className="seg p3-map-type" role="group" aria-label={t("ชนิดแผนที่ · Map type", "Map type")}>
      <button aria-pressed={kind === "roadmap"} onClick={() => setKind("roadmap")}><Tr th="แผนที่" en="Map" /></button>
      <button aria-pressed={kind === "hybrid"} onClick={() => setKind("hybrid")}><Tr th="ดาวเทียม" en="Satellite" /></button>
      {props.water && <button aria-pressed={waterOn} onClick={() => setWaterOn(value => !value)}><Tr th="น้ำ" en="Water" /></button>}
    </div>}
    <details className="p3-map-legend">
      <summary><Tr th="คำอธิบาย" en="Legend" /></summary>
      <div className="p3-water-key" aria-label={t("ระดับน้ำและความต้องการ · Water and needs", "Water and needs")}>
      <div className="p3-legend">{[t("ไม่มีครอบครัวรอ · None waiting", "None waiting"), t("น้อย · Lower", "Lower"), t("ปานกลาง · More", "More"), t("มากสุด · Most help missing", "Most help missing")].map((label, index) => <span key={label}><i style={{ background: `var(--need-${index})` }} />{label}</span>)}</div>
      <p><Tr th="เปิดชั้นน้ำ: ตัวเลขแดง = ด่วน ตัวเลขหมึก = รอ ไม่ทราบไม่ใช่แห้ง" en="Water on: red counts urgent, ink counts waiting. Unknown is never dry." /></p>
      <b><Tr th="ระดับน้ำ · ไปด้วยอะไร" en="Water · go by" /></b>
      {GO_BY.map(([token, th, en]) => <span key={token}><i style={{ background: `var(${token})` }} /><Tr th={th} en={en} /></span>)}
      <span><i className="is-shelter" /><Tr th="ศูนย์พักพิง" en="shelter" /></span>
      </div>
    </details>
  </div>;
}

/** Area-weighted centroid of outer polygon rings; holes do not move the sector badge. */
export function featureCentroid(feature: GeoJSON.Feature): [number, number] {
  const geometry = feature.geometry;
  const outer = geometry.type === "Polygon" ? [geometry.coordinates[0]] : geometry.type === "MultiPolygon" ? geometry.coordinates.map(polygon => polygon[0]) : [];
  let weight = 0, longitude = 0, latitude = 0;
  for (const ring of outer) {
    let area = 0, x = 0, y = 0;
    for (let i = 0; i < ring.length; i++) {
      const a = ring[i], b = ring[(i + 1) % ring.length];
      const cross = a[0] * b[1] - b[0] * a[1];
      area += cross; x += (a[0] + b[0]) * cross; y += (a[1] + b[1]) * cross;
    }
    if (Math.abs(area) > 1e-12) {
      const mass = Math.abs(area);
      longitude += x / (3 * area) * mass; latitude += y / (3 * area) * mass; weight += mass;
    }
  }
  const [w, s, e, n] = bounds([feature]);
  return weight ? [longitude / weight, latitude / weight] : [(w + e) / 2, (s + n) / 2];
}
