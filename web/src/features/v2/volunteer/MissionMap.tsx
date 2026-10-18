import { useEffect, useRef, useState } from "react";
import { loadGoogleMaps, type Maps } from "../../../data/googleMaps";
import { cssVar, type MissionRoute, type BoardState, type CaseRow, type GeoView } from "../api";
import { useFloodCanvas } from "../BoardMap";
import { bindFloodZoom } from "../floodLayer";
import { Tr, useT, useUiLang } from "../ui/lang";
import { isDone } from "./mission";

type Props = {
  route?: MissionRoute; geo: GeoView | null; zoneId: string; rows: CaseRow[]; selected: string | null;
  hour: number; onSelect: (id: string) => void;
};

export function MissionMap({ route, geo, zoneId, rows, selected, hour, onSelect }: Props) {
  const t = useT();
  const { lang } = useUiLang();
  const host = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState<{ maps: Maps; map: Maps } | null>(null);
  const [failed, setFailed] = useState(false);
  const [kind, setKind] = useState("hybrid");
  const latest = useRef({ rows, onSelect, selected });
  latest.current = { rows, onSelect, selected };
  const clock = { now: { atH: hour }, overall: { messages: rows.reduce((n, row) => n + row.messages, 0) } } as BoardState;
  const flood = useFloodCanvas(geo, clock, hour, "corrected");
  const shape = geo?.zones.features.find(feature => String(feature.properties?.id ?? feature.id) === zoneId);
  const geometry = shape?.geometry;
  const polygons = geometry?.type === "Polygon" ? [geometry.coordinates] : geometry?.type === "MultiPolygon" ? geometry.coordinates : [];
  const geometryKey = JSON.stringify(polygons);
  const positions = rows.map(row => `${row.id}:${row.lat}:${row.lon}`).join("|");
  const routeKey = JSON.stringify(route);
  const drawn = rows.map(row => `${row.id}:${row.lat}:${row.lon}:${isDone(row)}:${row.urgent}`).join("|");

  useEffect(() => {
    let active = true;
    let instance: Maps;
    loadGoogleMaps(lang).then(maps => {
      if (!active || !host.current) return;
      instance = new maps.Map(host.current, { center: { lat: 7.01, lng: 100.47 }, zoom: 14, mapTypeId: "hybrid",
        disableDefaultUI: true, zoomControl: true, keyboardShortcuts: true, gestureHandling: "cooperative" });
      setReady({ maps, map: instance });
    }).catch(() => { if (active) setFailed(true); });
    return () => { active = false; if (instance) instance.unbindAll(); };
    // Maps is shared across the app; UI labels below still follow language changes.
  }, []);
  useEffect(() => { ready?.map.setMapTypeId(kind); }, [ready, kind]);

  useEffect(() => {
    if (!ready) return;
    const { maps, map } = ready;
    const box = new maps.LatLngBounds();
    let count = 0;
    const extend = (lon: number, lat: number) => { box.extend({ lat, lng: lon }); count++; };
    polygons.flat(2).forEach(([lon, lat]) => extend(lon, lat));
    latest.current.rows.forEach(row => { if (row.lat !== null && row.lon !== null) extend(row.lon, row.lat); });
    if (route) {
      extend(route.start.lon, route.start.lat);
      route.runs.forEach(run => { if (run.shelter) extend(run.shelter.lon, run.shelter.lat); });
    }
    const fit = () => { if (count) map.fitBounds(box, 48); };
    fit();
    const idle = maps.event.addListenerOnce(map, "idle", fit);
    const resize = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(() => { maps.event.trigger(map, "resize"); fit(); });
    if (host.current) resize?.observe(host.current);
    return () => { idle.remove(); resize?.disconnect(); };
  }, [ready, geometryKey, positions, zoneId, routeKey]);

  useEffect(() => {
    if (!ready) return;
    const { maps, map } = ready;
    const overlays: Maps[] = polygons.map(paths => new maps.Polygon({ map,
      paths: paths.map(ring => ring.map(([lng, lat]) => ({ lat, lng }))),
      strokeColor: cssVar("--ink-1"), strokeWeight: 2, fillOpacity: 0, clickable: false }));
    const open = rows.filter(row => !isDone(row));
    const path = open.filter(row => row.lat !== null && row.lon !== null).map(row => ({ lat: row.lat, lng: row.lon }));
    if (!route) overlays.push(new maps.Polyline({ map, path, strokeColor: cssVar("--ink-1"), strokeOpacity: .5, clickable: false }));
    const marker = (lon: number, lat: number, label: string) => {
      overlays.push(new maps.Marker({ map, position: { lng: lon, lat }, label: { text: label, color: cssVar("--ink-1"), fontSize: "12px" }, title: label, icon: { path: "M -6,-6 L 6,-6 L 6,6 L -6,6 Z", fillColor: cssVar("--surface"), fillOpacity: 1, strokeColor: cssVar("--ink-1"), strokeWeight: 2, scale: 2 } }));
    };
    if (route) {
      marker(route.start.lon, route.start.lat, route.vehicle === "boat" ? (route.start.label === "Launch here" ? t("จุดลงเรือ", "Launch here") : t("ยังยืนยันจุดลงเรือไม่ได้", "Launch unverified")) : t("จุดเริ่ม", "Start"));
      route.runs.forEach(run => {
        if (run.shelter) marker(run.shelter.lon, run.shelter.lat, t("ศูนย์พักพิง", "Shelter drop-off"));
        run.legs.forEach(leg => {
          leg.samples.slice(1).forEach((sample, i) => {
            const previous = leg.samples[i];
            const d = Math.max(previous[2], sample[2]);
            const token = d < .4 ? "--water-1" : d <= .5 ? "--water-2" : d <= 1 ? "--water-3" : "--water-4";
            overlays.push(new maps.Polyline({ map, path: [{ lng: previous[0], lat: previous[1] }, { lng: sample[0], lat: sample[1] }], strokeColor: cssVar(token), strokeWeight: 5, strokeOpacity: 1, clickable: false }));
          });
          if (leg.warnings.length) marker(leg.warningAt[0], leg.warningAt[1], "!");
        });
      });
      route.unreachable.forEach(h => {
        const row = rows.find(r => r.id === h.id);
        if (row?.lon != null && row.lat != null) marker(row.lon, row.lat, "!");
      });
    }
    rows.forEach(row => {
      if (row.lat === null || row.lon === null) return;
      const done = isDone(row);
      const button = document.createElement("button");
      button.type = "button";
      button.className = `mission-marker ${done ? "is-done" : row.urgent ? "is-urgent" : "is-waiting"}`;
      button.dataset.house = row.id;
      button.textContent = route?.unreachable.some(h => h.id === row.id) ? "!" : done ? "✓" : (route && !route.runs.some(run => run.stops.includes(row.id)) ? "·" : String((route?.runs.flatMap(run => run.stops) ?? open.map(r => r.id)).indexOf(row.id) + 1));
      button.setAttribute("aria-label", t(`บ้าน ${row.id}`, `House ${row.id}`));
      button.onclick = () => latest.current.onSelect(row.id);
      maps.OverlayView.preventMapHitsAndGesturesFrom?.(button);
      const marker = new maps.OverlayView();
      marker.onAdd = () => {
        button.classList.toggle("is-selected", latest.current.selected === row.id);
        button.setAttribute("aria-pressed", String(latest.current.selected === row.id));
        marker.getPanes().overlayMouseTarget.appendChild(button);
      };
      marker.draw = () => {
        const projection = marker.getProjection();
        if (!projection) return;
        const point = projection.fromLatLngToDivPixel(new maps.LatLng(row.lat, row.lon));
        if (point) Object.assign(button.style, { left: `${point.x}px`, top: `${point.y}px` });
      };
      marker.onRemove = () => { button.onclick = null; button.remove(); };
      marker.setMap(map);
      overlays.push(marker);
    });
    return () => overlays.forEach(overlay => overlay.setMap(null));
  }, [ready, geometryKey, drawn, routeKey, t]);

  useEffect(() => {
    host.current?.querySelectorAll<HTMLButtonElement>(".mission-marker").forEach(button => {
      button.classList.toggle("is-selected", button.dataset.house === selected);
      button.setAttribute("aria-pressed", String(button.dataset.house === selected));
    });
    const row = latest.current.rows.find(row => row.id === selected);
    if (ready && row?.lat != null && row.lon != null) ready.map.panTo({ lat: row.lat, lng: row.lon });
  }, [ready, selected, drawn, t]);

  useEffect(() => {
    if (!ready || !flood.sim) return;
    const { maps, map } = ready;
    const [west, south, east, north] = flood.sim.meta.bbox;
    const canvas = flood.canvas;
    canvas.className = "v2-flood-canvas";
    const layer = document.createElement("div");
    layer.className = "mission-water";
    layer.appendChild(canvas);
    const water = new maps.OverlayView();
    water.onAdd = () => water.getPanes().mapPane.appendChild(layer);
    water.draw = () => {
      const projection = water.getProjection();
      if (!projection) return;
      const sw = projection.fromLatLngToDivPixel(new maps.LatLng(south, west));
      const ne = projection.fromLatLngToDivPixel(new maps.LatLng(north, east));
      if (sw && ne) Object.assign(canvas.style, { left: `${sw.x}px`, top: `${ne.y}px`, width: `${ne.x - sw.x}px`, height: `${sw.y - ne.y}px` });
    };
    water.onRemove = () => layer.remove();
    water.setMap(map);
    const unbind = bindFloodZoom(map, canvas);
    return () => { unbind(); water.setMap(null); };
  }, [ready, flood.sim, flood.canvas]);

  return <section className="mission-map" aria-label={t("แผนที่บ้านในภารกิจ", "Mission household map")}>
    <div className="mission-map-controls" role="group" aria-label={t("ชนิดแผนที่", "Map type")}>
      <button aria-pressed={kind === "roadmap"} onClick={() => setKind("roadmap")}><Tr th="แผนที่" en="Map" /></button>
      <button aria-pressed={kind === "hybrid"} onClick={() => setKind("hybrid")}><Tr th="ดาวเทียม" en="Satellite" /></button>
    </div>
    <div className="mission-map-host" ref={host} />
    {(!ready || failed) && <p className="mission-map-fallback" role="status">{failed
      ? t("โหลดแผนที่ไม่ได้ ใช้รายการบ้านด้านล่าง", "Map could not load. Use the household list below.")
      : t("กำลังโหลดแผนที่", "Loading map…")}</p>}
    <div className="mission-map-legend"><span><Tr th="แดง = ด่วน · เหลือง = รอ · ✓ = เรียบร้อย" en="Red = urgent · Amber = waiting · ✓ = done" /></span>
      <span className="mission-order-key">{route ? <Tr th="เส้นทางถนน · สีตามความลึกน้ำแบบจำลอง" en="Street route · coloured by model water depth" /> : <Tr th="ลำดับการไป ไม่ใช่เส้นทางถนน" en="visiting order, not a road route" />}</span></div>
  </section>;
}
