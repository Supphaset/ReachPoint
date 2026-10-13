import { useEffect, useMemo, useState } from "react";
import type { FeatureCollection, Geometry, Position } from "geojson";
import type { FloodSegment, FloodView, MapMode, WaterEstimate } from "../../data/flood";
import { readPackageFile } from "../../data/source";
import { Banner } from "../../ui/components";

type FC = FeatureCollection<Geometry, Record<string, unknown>>;
function rings(g: Geometry): Position[][] {
  return g.type === "Polygon" ? g.coordinates : g.type === "MultiPolygon" ? g.coordinates.flat() : [];
}
export function estimateLabel(e?: WaterEstimate): string {
  if (!e) return "No water observations · unknown";
  if (e.status === "stale") return "Stale water observations";
  if (e.rangeM) return `${e.status === "conflicting" ? "Conflicting reports" : "Estimated local depth"}: ${e.rangeM.map((n) => n.toFixed(2)).join("–")} m`;
  return e.bands.length ? `${e.bands.join(" / ").replaceAll("_", " ")} reported · metre estimate unavailable` : "Insufficient comparable measurements";
}
export function markerLabel(s: FloodSegment, mode: MapMode): string {
  if (mode === "water") return estimateLabel(s.estimates[0]);
  if (mode === "needs") return `${s.needs.urgentReports} urgent reports · ${s.needs.urgentReviewedGroups} reviewed urgent groups · ${s.needs.reportedPeople} people in reports · ${s.needs.verifiedTransportUnassigned} verified people seeking transport`;
  return `${s.coverage.activeJobs} active jobs · ${s.coverage.heldJobs} held · ${s.coverage.state.replaceAll("_", " ")}`;
}
export function FloodMap({ segments, mode, selected, onSelect, zone, teams = [], onZone }: {
  segments: FloodSegment[]; mode: MapMode; teams?: FloodView["teams"]; onZone?: (zoneId: string) => void; selected: string | null; onSelect: (id: string) => void; zone: string;
}) {
  const [layers, setLayers] = useState<[FC, FC, FC] | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    let alive = true;
    Promise.all(["zones", "no-satellite-data", "extent-2025-11-23-o164"].map((n) => readPackageFile<FC>(`${n}.geojson`)))
      .then((ls) => alive && setLayers(ls as [FC, FC, FC])).catch(() => alive && setError(true));
    return () => { alive = false; };
  }, []);
  const projection = useMemo(() => {
    if (!layers) return null;
    const zones = layers[0].features.filter((f) => zone === "all" || f.properties.id === zone);
    const points = zones.flatMap((f) => rings(f.geometry).flat());
    if (!points.length) return null;
    const xs = points.map((p) => p[0]), ys = points.map((p) => p[1]);
    const x0 = Math.min(...xs), y1 = Math.max(...ys);
    const dx = Math.max(...xs) - x0, dy = y1 - Math.min(...ys);
    const scale = 880 / Math.max(dx, dy);
    const project = ([x, y]: Position) => [(x - x0) * scale + 60, (y1 - y) * scale + 60];
    const path = (g: Geometry) => rings(g).map((r) => "M" + r.map((p) => project(p).join(",")).join("L") + "Z").join("");
    return { zones, project, path };
  }, [layers, zone]);
  if (error) return <Banner kind="error">Map unavailable. Use the segment list; evidence still works.</Banner>;
  if (!layers || !projection) return <p>Loading flood geography…</p>;
  const { project, path, zones } = projection;
  const grouped = zone === "all" ? [...new Set(segments.map((s) => s.zoneId))].map((id) => {
    const rows = segments.filter((s) => s.zoneId === id);
    return { id, rows, at: [rows.reduce((n, s) => n + s.at[0], 0) / rows.length,
      rows.reduce((n, s) => n + s.at[1], 0) / rows.length] };
  }) : segments.map((s) => ({ id: s.segmentId, rows: [s], at: s.at }));
  return <figure className="flood-figure">
    <svg viewBox="0 0 1000 1000" aria-label={`Hat Yai ${mode} map; use segment list for keyboard selection`} role="img">
      <defs><pattern id="flood-blind" width="10" height="10" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.5" className="flood-blind-dot" /></pattern>
        <clipPath id="flood-clip"><rect width="1000" height="1000" /></clipPath></defs>
      <g clipPath="url(#flood-clip)">
        <rect width="1000" height="1000" className="flood-land" />
        {layers[2].features.map((f, i) => <path key={`w${i}`} d={path(f.geometry)} className="flood-historic" />)}
        {layers[1].features.map((f, i) => <path key={`b${i}`} d={path(f.geometry)} className="flood-blind" />)}
        {zones.map((f) => <path key={String(f.properties.id)} d={path(f.geometry)} className="flood-zone" />)}
        {grouped.map(({ id, rows, at }) => {
          const [x, y] = project(at);
          const count = rows.reduce((n, s) => n + (mode === "water" ? s.observations.length : mode === "needs"
            ? s.needs.reportedPeople || s.needs.verifiedTransportUnassigned : s.coverage.activeJobs + s.coverage.heldJobs), 0);
          const urgent = rows.some((s) => s.needs.urgentReports || s.needs.urgentReviewedGroups);
          const held = rows.some((s) => s.coverage.heldJobs);
          const conflict = rows.some((s) => s.estimates.some((e) => e.status === "conflicting"));
          const tone = mode === "needs" && urgent ? "urgent" : mode === "response" && held ? "held" : count ? mode : "unknown";
          const isSelected = rows.some((s) => s.segmentId === selected);
          const title = zone === "all" ? `${id}: ${count} ${mode === "water" ? "water observations" : mode === "needs" ? "people reported or verified unassigned" : "active or held jobs"}${conflict ? "; conflicting water reports" : ""}. Select to focus the zone.` : `${rows[0].label}: ${markerLabel(rows[0], mode)}. Approximate landmark, not household point.`;
          return <g key={id} transform={`translate(${x},${y})`} className={`flood-marker tone-${tone} ${isSelected ? "selected" : ""}`} onClick={() => zone === "all" ? onZone?.(id) : onSelect(id)}>
            <circle r={isSelected ? 25 : zone === "all" ? 21 : 15} />
            <text textAnchor="middle" y="4">{count || "?"}</text>
            {zone === "all" && <text textAnchor="middle" y="37" className="flood-zone-label">{id}</text>}
            {conflict && mode === "water" && <text x="20" y="-16" className="flood-conflict">!</text>}
            <title>{title}</title>
          </g>;
        })}
        {mode === "response" && teams.map((t) => {
          const [x, y] = project(t.at);
          return <g key={t.teamId} transform={`translate(${x},${y})`} className="flood-team">
            <rect x="-12" y="-12" width="24" height="24" /><text x="18" y="4">{t.teamId}</text>
            <title>{t.teamId}: {t.resourceStatus === "unavailable" ? "Unavailable" : t.status}, {t.freeSeats} free seats. Team landmark; no route inferred.</title>
          </g>;
        })}
      </g>
    </svg>
    <figcaption>Historical satellite extent: Hat Yai, 24 Nov 2025 · Dotted areas: no satellite data, never dry · City view: zone summaries · Focus view: segment landmarks, not houses · Numbers: water observations / people needing help / jobs, by mode · Response squares show team landmarks</figcaption>
  </figure>;
}
