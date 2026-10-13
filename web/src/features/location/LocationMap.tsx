import { useEffect, useId, useMemo, useRef, useState } from "react";
import type { Point, Position } from "geojson";
import { locationLayers, type LocationLayers } from "../../data/locationMap";
import { W, bbox, contains, lineOf, pathOf, projector, insideBounds } from "../../data/mapGeometry";
import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { landmarkText } from "./LocationChip";
import "./location.css";

type At = [number, number];
export function LocationMap({ at, zoneId, segmentId, onConfirm }: { at?: At | null; zoneId?: string; segmentId?: string; onConfirm?: (at: At) => void }) {
  const { t } = useLang();
  const id = useId();
  const [layers, setLayers] = useState<LocationLayers>();
  const [failed, setFailed] = useState(false);
  // The picker opens on the city (most calls), not on every demo area; tapping a zone zooms into it.
  const [zone, setZone] = useState(zoneId ?? (onConfirm ? "city" : ""));
  const [pin, setPin] = useState<At | null>(at ?? null);
  const svg = useRef<SVGSVGElement>(null);
  const interactive = !!onConfirm;
  useEffect(() => {
    let alive = true;
    locationLayers().then(data => alive && setLayers(data)).catch(() => alive && setFailed(true));
    return () => { alive = false; };
  }, []);
  useEffect(() => { if (interactive && layers) svg.current?.focus({ preventScroll: true }); }, [interactive, layers]);
  useEffect(() => { setZone(zoneId ?? (onConfirm ? "city" : "")); }, [zoneId, onConfirm]);
  const drawn = useMemo(() => {
    if (!layers) return null;
    const zoneToDraw = zone || (!interactive && segmentId ? layers.segments.features.find(f => f.properties.id === segmentId)?.properties.zoneId as string | undefined : undefined);
    const chosen = layers.zones.features.filter(f => !zoneToDraw || (zoneToDraw === "city" ? f.properties.areaId === "P-B" : f.properties.id === zoneToDraw));
    const zones = chosen.length ? chosen : layers.zones.features;
    const bounds = bbox(zones);
    if (!interactive && at) {
      bounds[0] = Math.min(bounds[0], at[0]); bounds[1] = Math.min(bounds[1], at[1]);
      bounds[2] = Math.max(bounds[2], at[0]); bounds[3] = Math.max(bounds[3], at[1]);
    }
    const projection = projector(bounds);
    return { zones, bounds, ...projection };
  }, [layers, zone, segmentId, interactive, at]);
  if (failed) return <p role="status">{t(S.location.mapFailed)}</p>;
  if (!layers || !drawn) return <p role="status">{t(S.briefing.mapLoading)}</p>;
  const { zones, project, unproject, height, bounds } = drawn;
  const drawnZoneIds = new Set(zones.map(f => f.properties.id));
  const overview = zone === "city" || zone === "";
  const point = interactive ? pin : at;
  const [px, py] = point ? project(point) : [0, 0];
  const move = (pos: Position, tapped = false) => {
    // Padding around the drawing is not a selectable point outside the demo bbox.
    const [lon, lat] = unproject(pos);
    const next: At = [Math.max(layers.bounds[0], Math.min(layers.bounds[2], lon)), Math.max(layers.bounds[1], Math.min(layers.bounds[3], lat))];
    setPin(next);
    if (tapped && overview) {
      const hit = zones.find(f => contains(f.geometry, next));
      if (hit) setZone(String(hit.properties.id)); // first tap zooms into the zone, keeping the pin there
    }
  };
  return <div className={`location-map ${interactive ? "is-picker" : "is-mini"}`}>
    {interactive && <>
      <label htmlFor={`${id}-zone`}>{t(S.location.zone)}</label>
      <select id={`${id}-zone`} value={zone} onChange={e => { setZone(e.target.value); setPin(null); }}>
        <option value="city">{t(S.location.city)}</option>
        <option value="">{t(S.location.allZones)}</option>
        {layers.zones.features.map(f => <option key={String(f.properties.id)} value={String(f.properties.id)}>{String(f.properties.id)}</option>)}
      </select>
      <p className="fine-print" id={`${id}-help`}>{overview ? `${t(S.location.cityHelp)} ` : ""}{t(S.location.mapHelp)}</p>
      {!overview && <button type="button" className="btn btn-quiet location-back" onClick={() => setZone("city")}>{t(S.location.backToCity)}</button>}
    </>}
    <svg ref={svg} className="location-map-svg" viewBox={`0 0 ${W} ${height}`} role={interactive ? "group" : "img"}
      aria-label={t(interactive ? S.location.mapLabel : S.location.miniLabel)}
      aria-describedby={interactive ? `${id}-help` : undefined} tabIndex={interactive ? 0 : undefined}
      onClick={interactive ? e => {
        const matrix = e.currentTarget.getScreenCTM();
        if (!matrix) return;
        const pos = new DOMPoint(e.clientX, e.clientY).matrixTransform(matrix.inverse());
        move([pos.x, pos.y], true);
        e.currentTarget.focus({ preventScroll: true });
      } : undefined}
      onKeyDown={interactive ? e => {
        if (e.key === "Enter") { e.preventDefault(); if (pin) onConfirm(pin); return; }
        const steps: Record<string, At> = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
        const step = steps[e.key];
        if (!step) return;
        e.preventDefault();
        const centre: At = [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2];
        const [x, y] = project(pin && insideBounds(pin, bounds) ? pin : centre);
        const stride = e.shiftKey ? 1 : 10;
        move([x + step[0] * stride, y + step[1] * stride]);
      } : undefined}>
      <rect width={W} height={height} className="location-map-land" />
      {zones.map(f => <path key={String(f.properties.id)} d={pathOf(f.geometry, project)} className="location-map-zone" />)}
      {layers.lines.features.map((f, i) => {
        const kind = String(f.properties.kind ?? "");
        const water = kind === "river" || kind === "canal";
        if (overview && !water && kind !== "trunk" && kind !== "primary" && kind !== "rail") return null; // keep the overview readable
        return <path key={i} d={lineOf(f.geometry, project)} className={`location-map-line is-${water ? "water" : kind}`} />;
      })}
      {layers.segments.features.filter(f => drawnZoneIds.has(f.properties.zoneId)).map(f => <path key={String(f.properties.id)} d={pathOf(f.geometry, project)} className="location-map-segment" />)}
      {layers.landmarks.features.filter(f => drawnZoneIds.has(f.properties.zoneId)).map(f => {
        if (f.geometry.type !== "Point") return null;
        const [x, y] = project((f.geometry as Point).coordinates);
        return <g key={String(f.properties.id)} transform={`translate(${x},${y})`} className="location-map-landmark">
          <title>{landmarkText(String(f.properties.label ?? f.properties.code), t)}</title>
          <circle r={overview ? 3 : 6} />{!overview && <text x={10} y={4}>{String(f.properties.code)}</text>}
        </g>;
      })}
      {zones.map(f => {
        const centre = f.properties.labelAt as Position | undefined;
        if (!centre) return null;
        const [x, y] = project(centre);
        return <text key={String(f.properties.id)} x={x} y={y} className="location-map-label" textAnchor="middle">{String(f.properties.id)}</text>;
      })}
      {point && <g transform={`translate(${px},${py})`} className="location-map-pin"><title>{t(S.location.pin)}</title><circle r={overview ? 14 : 22} /><circle r={overview ? 4 : 7} className="location-map-pin-dot" /></g>}
    </svg>
    <p className="fine-print">{t(S.location.schematic)}</p>
    {interactive && <button type="button" className="btn btn-primary" disabled={!pin} onClick={() => pin && onConfirm(pin)}>{t(S.location.useSpot)}</button>}
  </div>;
}
