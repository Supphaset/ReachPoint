import { useEffect, useRef, useState } from "react";
import type { GeoView, OverviewZone } from "../api";
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
export function SectorMap({ geo, zones, selection, onZone, onSector }: { geo: GeoView | null; zones: OverviewZone[]; selection: Selection; onZone: (id: string) => void; onSector: (id: string) => void }) {
  const frame = useRef<SVGSVGElement>(null);
  const [size, setSize] = useState({ width: 900, height: 700 });
  useEffect(() => {
    if (!frame.current) return;
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
  const scale = Math.min((size.width - 56) / (spanX * longitudeScale), (size.height - 56) / spanY);
  const x = (lon: number) => size.width / 2 + (lon - (west + east) / 2) * longitudeScale * scale;
  const y = (lat: number) => size.height / 2 - (lat - (south + north) / 2) * scale;
  const path = (feature: GeoJSON.Feature) => rings(feature).map(ring => ring.map(([lon, lat], index) => `${index ? "L" : "M"}${x(lon)} ${y(lat)}`).join(" ") + "Z").join(" ");
  const maximum = Math.max(1, ...zones.map(zone => zone.score));
  const top = [...zones].sort((a, b) => b.score - a.score).slice(0, 8).map(zone => zone.id);
  return <svg ref={frame} className="p3-sector-map" viewBox={`0 0 ${size.width} ${size.height}`} aria-label="Team zones by help missing; thick sector boundaries A to G">
    {geo.zones.features.map(feature => {
      const id = String(feature.properties?.id);
      const zone = zones.find(candidate => candidate.id === id);
      const b = bounds([feature]);
      return <g key={id} role="button" tabIndex={0} aria-label={`Zone ${id}, ${zone?.open ?? "unknown"} waiting`} aria-pressed={selection.zone === id} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onZone(id); } }} onClick={() => onZone(id)}>
        <path d={path(feature)} className={`p3-zone ${selection.zone === id ? "is-selected" : ""}`} style={{ fill: `var(--need-${needBand(zone, maximum)})`, strokeDasharray: zone?.open && !zone.plans ? "8 5" : undefined }}><title>{id} · {zone?.label} · {zone?.open ?? "unknown"} waiting</title></path>
        {(selection.sector || top.includes(id)) && <text x={x((b[0] + b[2]) / 2)} y={y((b[1] + b[3]) / 2)} className="p3-zone-label">{id}</text>}
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
  </svg>;
}
