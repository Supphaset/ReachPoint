import { useEffect, useMemo, useState } from "react";
import type { Feature, FeatureCollection, Geometry, Point, Polygon, MultiPolygon, Position } from "geojson";
import { readPackageFile } from "../../data/source";
import type { AreaBriefingView } from "../../data/contract";
import { Banner } from "../../ui/components";

/**
 * Offline schematic map of an area, drawn from the flood package (no tiles, no API key).
 * Google Maps JS can replace the base later; the layers and rules stay:
 * - "No satellite data" is dotted, never drawn as dry (D26).
 * - Zones with no reports are hatched "not checked", never "safe".
 * - If the flood extent is missing, no water is drawn and nothing is shaded as dry.
 * - Markers sit at landmarks, never at houses (D25).
 */

type Props = Record<string, unknown>;
type FC = FeatureCollection<Geometry, Props>;

interface Layers {
  zones: FC;
  segments: FC;
  landmarks: FC;
  noData: FC;
  extent: FC;
  reported: FC;
}

const W = 1000;

function rings(g: Geometry): Position[][] {
  if (g.type === "Polygon") return (g as Polygon).coordinates;
  if (g.type === "MultiPolygon") return (g as MultiPolygon).coordinates.flat();
  return [];
}

function bbox(features: Feature<Geometry, Props>[]): [number, number, number, number] {
  let [x0, y0, x1, y1] = [Infinity, Infinity, -Infinity, -Infinity];
  for (const f of features)
    for (const r of rings(f.geometry))
      for (const [x, y] of r) {
        x0 = Math.min(x0, x);
        y0 = Math.min(y0, y);
        x1 = Math.max(x1, x);
        y1 = Math.max(y1, y);
      }
  return [x0, y0, x1, y1];
}

function projector([x0, y0, x1, y1]: [number, number, number, number]) {
  const k = Math.cos(((y0 + y1) / 2) * (Math.PI / 180));
  const pad = 0.06;
  const dx = (x1 - x0) * k;
  const dy = y1 - y0;
  const s = W / (dx * (1 + 2 * pad));
  const project = ([x, y]: Position): [number, number] => [(x - x0) * k * s + dx * s * pad, (y1 - y) * s + dy * s * pad];
  return { project, height: dy * s * (1 + 2 * pad) };
}

function pathOf(g: Geometry, project: (p: Position) => [number, number]): string {
  return rings(g)
    .map((r) => "M" + r.map((p) => project(p).map((v) => v.toFixed(1)).join(",")).join("L") + "Z")
    .join("");
}

export function ZoneMap({
  view,
  selectedZone,
  onSelectZone,
}: {
  view: AreaBriefingView;
  selectedZone: string | null;
  onSelectZone: (id: string) => void;
}) {
  const [layers, setLayers] = useState<Layers | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    Promise.all(
      ["zones", "segments", "landmarks", "no-satellite-data", "extent-2025-11-23-o164", "reported-flooding"].map((n) =>
        readPackageFile<FC>(`${n}.geojson`),
      ),
    )
      .then(([zones, segments, landmarks, noData, extent, reported]) => {
        if (alive) setLayers({ zones, segments, landmarks, noData, extent, reported });
      })
      .catch(() => alive && setFailed(true));
    return () => {
      alive = false;
    };
  }, []);

  const drawn = useMemo(() => {
    if (!layers) return null;
    const zoneIds = new Set(view.zones.map((z) => z.zoneId));
    const zones = layers.zones.features.filter((f) => zoneIds.has(f.properties.id as string));
    const { project, height } = projector(bbox(zones));
    return { zones, project, height };
  }, [layers, view]);

  if (failed) return <Banner kind="error">Map unavailable. List and briefing still work.</Banner>;
  if (!layers || !drawn) return <div className="map-loading">Loading map…</div>;

  const { zones, project, height } = drawn;
  const byId = new Map(view.zones.map((z) => [z.zoneId, z]));
  const extentOk = view.layers.floodExtent.state === "available";
  const selSegs = selectedZone ? layers.segments.features.filter((f) => f.properties.zoneId === selectedZone) : [];
  const segView = new Map(byId.get(selectedZone ?? "")?.segments.map((s) => [s.segmentId, s]) ?? []);
  const marks = selectedZone ? layers.landmarks.features.filter((f) => f.properties.zoneId === selectedZone) : [];

  return (
    <figure className="zone-map">
      {!extentOk && (
        <Banner kind="stale">Flood extent unavailable. Nothing on this map is shown as dry.</Banner>
      )}
      <svg viewBox={`0 0 ${W} ${height}`} role="img" aria-label={`Map of ${view.label}`}>
        <defs>
          <pattern id="nodata" width="10" height="10" patternUnits="userSpaceOnUse">
            <circle cx="2.5" cy="2.5" r="1.4" className="map-nodata-dot" />
          </pattern>
          <pattern id="hatch" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="12" className="map-hatch-line" />
          </pattern>
        </defs>
        <rect width={W} height={height} className="map-land" />
        {extentOk &&
          layers.extent.features.map((f, i) => <path key={i} d={pathOf(f.geometry, project)} className="map-water" />)}
        {layers.noData.features.map((f, i) => (
          <path key={i} d={pathOf(f.geometry, project)} className="map-nodata" />
        ))}
        {zones.map((f) => {
          const id = f.properties.id as string;
          const z = byId.get(id);
          return (
            <path
              key={id}
              d={pathOf(f.geometry, project)}
              className={`map-zone ${z?.status === "no_reports" ? "is-empty" : ""} ${id === selectedZone ? "is-selected" : ""}`}
              onClick={() => onSelectZone(id)}
            >
              <title>{id}</title>
            </path>
          );
        })}
        {selSegs.map((f) => (
          <path
            key={f.properties.id as string}
            d={pathOf(f.geometry, project)}
            className={`map-segment check-${segView.get(f.properties.id as string)?.check.state ?? "not_checked"}`}
          />
        ))}
        {layers.reported.features.map((f) => {
          const [x, y] = project((f.geometry as Point).coordinates);
          return (
            <g key={f.properties.id as string} transform={`translate(${x},${y})`} className="map-report">
              <path d="M0,-7 L6,0 L0,7 L-6,0Z" />
              <title>{`${f.properties.name_en}: ${f.properties.report} (reported ${f.properties.reported_on})`}</title>
            </g>
          );
        })}
        {marks.map((f) => {
          const [x, y] = project((f.geometry as Point).coordinates);
          return (
            <g key={f.properties.id as string} transform={`translate(${x},${y})`} className="map-landmark">
              <circle r="5" />
              <text x="8" y="4">
                {f.properties.code as string}
              </text>
            </g>
          );
        })}
        {zones.map((f) => {
          const id = f.properties.id as string;
          const at = f.properties.labelAt as Position | undefined;
          if (!at) return null;
          const [x, y] = project(at);
          const z = byId.get(id);
          return (
            <g key={`l-${id}`} transform={`translate(${x},${y})`} className="map-zone-label" onClick={() => onSelectZone(id)}>
              <text textAnchor="middle" y="5">
                {id}
              </text>
              {z && z.badge.urgent > 0 && <circle cx="22" cy="-8" r="7" className="map-urgent" />}
            </g>
          );
        })}
      </svg>
      <figcaption className="map-legend">
        {extentOk && (
          <span>
            <i className="lg lg-water" /> Satellite flood extent, 24 Nov 2025
          </span>
        )}
        <span>
          <i className="lg lg-nodata" /> No satellite data · never means dry
        </span>
        <span>
          <i className="lg lg-report" /> Cited flood report
        </span>
        <span>
          <i className="lg lg-empty" /> No reports yet · not checked
        </span>
      </figcaption>
    </figure>
  );
}
