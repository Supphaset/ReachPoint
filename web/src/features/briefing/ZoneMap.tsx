import { useEffect, useMemo, useState } from "react";
import type { FeatureCollection, Geometry, Point, Position } from "geojson";
import { W, bbox, projector, pathOf } from "../../data/mapGeometry";
import { readPackageFile } from "../../data/source";
import type { AreaBriefingView } from "../../data/contract";
import { Banner } from "../../ui/components";
import { fmtTime } from "../../data/format";
import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";

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
  const { t } = useLang();

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

  if (failed) return <Banner kind="error">{t(S.briefing.mapUnavailable)}</Banner>;
  if (!layers || !drawn) return <div className="map-loading">{t(S.briefing.mapLoading)}</div>;

  const { zones, project, height } = drawn;
  const byId = new Map(view.zones.map((z) => [z.zoneId, z]));
  const extentOk = view.layers.floodExtent.state === "available";
  const selSegs = selectedZone ? layers.segments.features.filter((f) => f.properties.zoneId === selectedZone) : [];
  const segView = new Map(byId.get(selectedZone ?? "")?.segments.map((s) => [s.segmentId, s]) ?? []);
  const marks = selectedZone ? layers.landmarks.features.filter((f) => f.properties.zoneId === selectedZone) : [];

  return (
    <figure className="zone-map">
      {!extentOk && (
        <Banner kind="stale">{t(S.briefing.extentUnavailable)}</Banner>
      )}
      <svg viewBox={`0 0 ${W} ${height}`} role="img" aria-label={t(S.briefing.mapOf(view.label))}>
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
        {view.callerWater.map((w) => {
          const [x, y] = project(w.at);
          return (
            <g key={`cw-${w.segmentId}`} transform={`translate(${x},${y})`} className={`map-caller ${w.stale ? "is-stale" : ""}`}>
              <circle r="8" />
              <title>{`Reported by callers: ${w.bandLabel} (about ${w.approxM} m) at ${w.landmarkLabel}, ${fmtTime(w.latestAt)}, ${w.callers} caller${w.callers > 1 ? "s" : ""}${w.stale ? " · older than 6 h" : ""}`}</title>
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
          <i className="lg lg-report" /> Cited news report
        </span>
        <span>
          <i className="lg lg-caller" /> Reported by callers (reviewed)
        </span>
        <span>
          <i className="lg lg-caller is-stale" /> Callers, older than 6 h
        </span>
        <span>
          <i className="lg lg-empty" /> No reports yet · not checked
        </span>
      </figcaption>
    </figure>
  );
}
