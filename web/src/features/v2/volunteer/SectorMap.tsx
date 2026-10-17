import { useEffect, useRef, useState } from "react";
import { loadGoogleMaps, type Maps } from "../../../data/googleMaps";
import type { BoardState, GeoView, OverviewZone, Shelter } from "../api";
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

/** Shared geometry and ids drive both sector outlines and the ranked list. No household pins are exposed. */
export function DrawnSectorMap({ geo, zones, selection, onZone, onSector }: { geo: GeoView | null; zones: OverviewZone[]; selection: Selection; onZone: (id: string) => void; onSector: (id: string) => void }) {
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
  if (!geo) return <p role="status">กำลังโหลดแผนที่ · Loading sectors…</p>;
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
  const top = [...zones].sort((a, b) => b.score - a.score).slice(0, 8).map(zone => zone.id);
  return <><div className="p3-fallback-zoom" aria-label="ซูม · Zoom"><button aria-label="ขยาย · Zoom in" onClick={() => setZoom(value => Math.min(3, value + 0.25))}>+</button><button aria-label="ย่อ · Zoom out" onClick={() => setZoom(value => Math.max(0.75, value - 0.25))}>−</button></div><svg ref={frame} className="p3-sector-map" viewBox={`0 0 ${size.width} ${size.height}`} aria-label="Team zones by help missing; thick sector boundaries A to G">
    {geo.zones.features.map(feature => {
      const id = String(feature.properties?.id);
      const zone = zones.find(candidate => candidate.id === id);
      const b = bounds([feature]);
      return <g key={id} role="button" tabIndex={0} aria-label={`Zone ${id}, ${zone?.open ?? "unknown"} waiting`} aria-pressed={selection.zone === id} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onZone(id); } }} onClick={() => onZone(id)}>
        <path d={path(feature)} className={`p3-zone ${selection.zone === id ? "is-selected" : ""}`} style={{ fill: `var(--need-${needBand(zone, maximum)})`, strokeDasharray: zone?.open && !zone.plans ? "8 5" : undefined }}><title>{`${id} · ${zone?.label ?? "ไม่ทราบชื่อ"} · ${zone?.open ?? "unknown"} waiting`}</title></path>
        {((selection.sector && zone?.sector === selection.sector) || top.includes(id)) && <text x={x((b[0] + b[2]) / 2)} y={y((b[1] + b[3]) / 2)} className="p3-zone-label">{id} · {zone?.label ?? "ไม่ทราบชื่อ"}</text>}
      </g>;
    })}
    {sectorFeatures.map(feature => {
      const id = String(feature.properties?.id);
      const b = bounds([feature]);
      const highlighted = selection.hover === id || selection.sector === id;
      return <g key={id} style={{ color: `var(--sector-${id})` }}>
        <path d={path(feature)} className={`p3-sector ${highlighted ? "is-highlighted" : ""}`} />
        <g className="p3-sector-badge" role="button" tabIndex={0} aria-label={`Sector ${id}`} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSector(id); } }} onClick={() => onSector(id)}>
          <circle cx={x((b[0] + b[2]) / 2)} cy={y((b[1] + b[3]) / 2)} r="22" />
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

export function drawSectorLayers(maps: Maps, map: Maps, props: Props, token: (name: string) => string, waterOn = false) {
  const { geo, zones, selection, onZone, onSector } = props;
  const overlays: Maps[] = [];
  if (!geo) return () => undefined;
  const maximum = Math.max(1, ...zones.map(zone => zone.score));
  const top = [...zones].sort((a, b) => b.score - a.score).slice(0, 8).map(zone => zone.id);
  const label = (feature: GeoJSON.Feature, text: string, sector: boolean, select: () => void) => {
    const [lng, lat] = featureCentroid(feature);
    // Overlay buttons provide keyboard selection and paper-backed place labels.
    const overlay = new maps.OverlayView();
    const button = document.createElement("button");
    button.className = sector ? "p3-google-badge" : "p3-google-label";
    button.textContent = text;
    button.setAttribute("aria-label", sector ? `พื้นที่ · Sector ${text}` : `โซน · Zone ${text}`);
    button.setAttribute("aria-pressed", String(sector ? selection.sector === text : selection.zone === feature.properties?.id));
    button.onclick = select;
    maps.OverlayView.preventMapHitsAndGesturesFrom?.(button);
    overlay.onAdd = () => overlay.getPanes().overlayMouseTarget.appendChild(button);
    overlay.draw = () => {
      const point = overlay.getProjection().fromLatLngToDivPixel(new maps.LatLng(lat, lng));
      if (point) { button.style.left = `${point.x}px`; button.style.top = `${point.y}px`; }
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
    const polygon = new maps.Polygon({ map, paths: component, fillColor: token(`--need-${band}`), fillOpacity: waterOn ? FILL[band] * 0.45 : FILL[band],
      strokeColor: token("--ink-1"), strokeWeight: selection.zone === id ? 5 : zone?.open && !zone.plans ? 2 : 1,
      strokeOpacity: selection.zone === id ? 1 : 0.55, zIndex: selection.zone === id ? 3 : 1 });
    polygon.addListener("click", () => onZone(id));
    overlays.push(polygon);
    }
    if (top.includes(id) || (selection.sector && zone?.sector === selection.sector)) {
      label(feature, `${id} · ${zone?.label ?? feature.properties?.label ?? "ไม่ทราบชื่อ"}`, false, () => onZone(id));
    }
  }
  for (const feature of geo.sectors?.features ?? []) {
    const id = String(feature.properties?.id);
    const polygon = new maps.Polygon({ map, paths: rings(feature).map(ring => ring.map(([lng, lat]) => ({ lng, lat }))),
      fillOpacity: 0, strokeColor: token("--ink-1"), strokeWeight: selection.sector === id || selection.hover === id ? 5 : 2.5, strokeOpacity: 0.85,
      clickable: false, zIndex: 2 });
    overlays.push(polygon);
    label(feature, id, true, () => onSector(id));
  }
  // Shelters: where a team drops people off. Green dot, name on hover/tap.
  for (const shelter of props.shelters ?? []) {
    overlays.push(new maps.Marker({ map, position: { lat: shelter.lat, lng: shelter.lon }, zIndex: 4,
      title: `ศูนย์พักพิง · Shelter: ${shelter.name}${shelter.capacity ? ` (${shelter.households}/${shelter.capacity})` : ""}`,
      icon: { path: maps.SymbolPath.CIRCLE, scale: 7, fillColor: token("--shelter"), fillOpacity: 1, strokeColor: token("--shelter-ink"), strokeWeight: 2 } }));
  }
  return () => overlays.forEach(overlay => { maps.event.clearInstanceListeners(overlay); overlay.setMap(null); });
}

export function SectorMap(props: Props) {
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
    loadGoogleMaps("th").then(maps => {
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
    ...props.zones.map(zone => `${zone.id}:${zone.score}:${zone.open}:${zone.plans}`)].join("|");
  useEffect(() => {
    if (!ready) return;
    const styles = getComputedStyle(document.documentElement);
    return drawSectorLayers(ready.maps, ready.map, {
      ...latest.current,
      onZone: id => latest.current.onZone(id),
      onSector: id => latest.current.onSector(id),
    }, name => styles.getPropertyValue(name).trim(), waterOn && !!props.water);
  }, [ready, drawn]);
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
    <div ref={host} className="p3-google-map" aria-label="แผนที่หาดใหญ่ · Hat Yai map" style={{ visibility: ready ? "visible" : "hidden", position: ready ? "relative" : "absolute" }} />
    {!ready && <><p className="p3-map-status" role="status">{failed ? "แผนที่สำรอง · Offline outline map" : "กำลังเปิดแผนที่ · Loading map"}</p><DrawnSectorMap {...props} /></>}
    {ready && <div className="seg p3-map-type" role="group" aria-label="ชนิดแผนที่ · Map type">
      <button aria-pressed={kind === "roadmap"} onClick={() => setKind("roadmap")}>แผนที่<small>Map</small></button>
      <button aria-pressed={kind === "hybrid"} onClick={() => setKind("hybrid")}>ดาวเทียม<small>Satellite</small></button>
      {props.water && <button aria-pressed={waterOn} onClick={() => setWaterOn(value => !value)}>น้ำ<small>Water</small></button>}
    </div>}
    {ready && waterOn && props.water && <div className="p3-water-key" aria-label="ระดับน้ำ ไปด้วยอะไร · Water depth and how to get there">
      <b>ระดับน้ำ · ไปด้วยอะไร <small>Water · go by</small></b>
      {GO_BY.map(([token, th, en]) => <span key={token}><i style={{ background: `var(${token})` }} />{th}<small>{en}</small></span>)}
      <span><i className="is-shelter" />ศูนย์พักพิง<small>shelter</small></span>
    </div>}
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
