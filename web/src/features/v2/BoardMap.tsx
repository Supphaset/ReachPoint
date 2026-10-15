/**
 * The live map: satellite imagery, zones coloured by the most likely water depth (grey = unknown, never "dry"),
 * a dot per household, and the judge's house with the neighbours they talked about.
 * Google Maps (hybrid) when a browser key is configured; otherwise a drawn map from the same data.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { loadGoogleMaps, type Maps } from "../../data/googleMaps";
import { cssVar, depthBand, type BoardState, type GeoView, type HouseholdView } from "./api";

export interface HouseMark {
  outline: [number, number][];
  kind: "me" | "known" | "new";
}

interface Props {
  geo: GeoView | null;
  state: BoardState | null;
  selected: string | null;
  onSelect: (zoneId: string) => void;
  houses: HouseMark[];
  focus: { lon: number; lat: number } | null;
  lang: "th" | "en";
}

function zoneFill(state: BoardState | null, id: string): string {
  const z = state?.zones[id];
  return cssVar(`--depth-${depthBand(z?.level ? z.level.depthM : null)}`);
}

function householdColor(h: HouseholdView): string {
  if (h.status === "lostContact") return cssVar("--household-lost");
  if (h.status === "safe" || h.status === "evacuated") return cssVar("--household-safe");
  if (h.urgent) return cssVar("--household-urgent");
  return cssVar("--household-open");
}

export function BoardMap(props: Props) {
  const [maps, setMaps] = useState<Maps | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    loadGoogleMaps(props.lang).then(setMaps, () => setFailed(true));
  }, [props.lang]);
  if (failed || !props.geo) return <DrawnMap {...props} />;
  if (!maps) return <div className="v2-map v2-map-loading">Loading satellite map…</div>;
  return <GoogleBoard maps={maps} {...props} />;
}

function GoogleBoard({ maps, geo, state, selected, onSelect, houses, focus }: Props & { maps: Maps }) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<Maps>(null);
  const zones = useRef<Maps>(null);
  const dots = useRef<Maps>(null);
  const marks = useRef<Maps>(null);
  const select = useRef(onSelect);
  select.current = onSelect;

  useEffect(() => {
    if (!el.current || !geo) return;
    map.current = new maps.Map(el.current, {
      center: { lng: geo.center[0], lat: geo.center[1] },
      zoom: 14,
      mapTypeId: "hybrid",
      disableDefaultUI: true,
      zoomControl: true,
      gestureHandling: "greedy",
      tilt: 0,
    });
    zones.current = new maps.Data({ map: map.current });
    zones.current.addGeoJson(geo.zones);
    zones.current.addListener("click", (e: Maps) => select.current(e.feature.getProperty("id")));
    dots.current = new maps.Data({ map: map.current });
    marks.current = new maps.Data({ map: map.current });
  }, [maps, geo]);

  useEffect(() => {
    if (!zones.current) return;
    const line = cssVar("--depth-line");
    zones.current.setStyle((f: Maps) => {
      const id = f.getProperty("id");
      const z = state?.zones[id];
      const known = !!z?.level;
      return {
        fillColor: zoneFill(state, id),
        fillOpacity: known ? 0.55 : 0.28,
        strokeColor: id === selected ? cssVar("--house-me") : line,
        strokeWeight: id === selected ? 3 : 1,
        strokeOpacity: 0.9,
      };
    });
  }, [state, selected]);

  useEffect(() => {
    const d = dots.current;
    if (!d || !state) return;
    d.forEach((f: Maps) => d.remove(f));
    d.addGeoJson({
      type: "FeatureCollection",
      features: state.households
        .filter((h) => h.lon && h.lat)
        .map((h) => ({ type: "Feature", properties: { c: householdColor(h), u: h.urgent && h.status === "open" }, geometry: { type: "Point", coordinates: [h.lon, h.lat] } })),
    });
    d.setStyle((f: Maps) => ({
      icon: {
        path: maps.SymbolPath.CIRCLE,
        scale: f.getProperty("u") ? 5 : 3.5,
        fillColor: f.getProperty("c"),
        fillOpacity: 1,
        strokeColor: cssVar("--v2-phone-bg"),
        strokeWeight: 1,
      },
      clickable: false,
    }));
  }, [state, maps]);

  useEffect(() => {
    const m = marks.current;
    if (!m) return;
    m.forEach((f: Maps) => m.remove(f));
    m.addGeoJson({
      type: "FeatureCollection",
      features: houses.map((h) => ({ type: "Feature", properties: { k: h.kind }, geometry: { type: "Polygon", coordinates: [h.outline] } })),
    });
    m.setStyle((f: Maps) => {
      const k = f.getProperty("k");
      const c = cssVar(k === "me" ? "--house-me" : k === "known" ? "--house-known" : "--house-new");
      return { fillColor: c, fillOpacity: 0.75, strokeColor: c, strokeWeight: 2, zIndex: 10, clickable: false };
    });
  }, [houses]);

  useEffect(() => {
    if (focus && map.current) {
      map.current.panTo({ lng: focus.lon, lat: focus.lat });
      map.current.setZoom(18);
    }
  }, [focus]);

  return <div ref={el} className="v2-map" aria-label="Satellite map of Hat Yai city with flood zones" />;
}

/** No Maps key: the same zones, dots and houses drawn as SVG over a dark ground. */
function DrawnMap({ geo, state, selected, onSelect, houses }: Props) {
  const box = useMemo(() => {
    if (!geo) return null;
    let x0 = 180, y0 = 90, x1 = -180, y1 = -90;
    for (const f of geo.zones.features) {
      const g = f.geometry as GeoJSON.Polygon | GeoJSON.MultiPolygon;
      const rings = g.type === "Polygon" ? [g.coordinates[0]] : g.coordinates.map((p) => p[0]);
      for (const r of rings) for (const [x, y] of r) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
    }
    return { x0, y0, x1, y1 };
  }, [geo]);
  if (!geo || !box) return <div className="v2-map v2-map-loading">Loading map…</div>;
  const W = 1000, H = Math.round((W * (box.y1 - box.y0)) / ((box.x1 - box.x0) * Math.cos((7 * Math.PI) / 180)));
  const px = (x: number) => ((x - box.x0) / (box.x1 - box.x0)) * W;
  const py = (y: number) => H - ((y - box.y0) / (box.y1 - box.y0)) * H;
  const path = (ring: number[][]) => ring.map(([x, y], i) => `${i ? "L" : "M"}${px(x).toFixed(1)} ${py(y).toFixed(1)}`).join(" ") + "Z";
  return (
    <svg className="v2-map v2-map-drawn" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Drawn map of Hat Yai city flood zones">
      {geo.zones.features.map((f) => {
        const id = (f.properties as { id: string }).id;
        const g = f.geometry as GeoJSON.Polygon | GeoJSON.MultiPolygon;
        const rings = g.type === "Polygon" ? [g.coordinates[0]] : g.coordinates.map((p) => p[0]);
        return (
          <g key={id} className={`v2-zone${id === selected ? " is-selected" : ""}`} onClick={() => onSelect(id)}>
            {rings.map((r, i) => (
              <path key={i} d={path(r)} style={{ fill: `var(--depth-${depthBand(state?.zones[id]?.level?.depthM ?? null)})` }} />
            ))}
          </g>
        );
      })}
      {state?.households.map((h) => (
        <circle key={h.id} cx={px(h.lon)} cy={py(h.lat)} r={h.urgent ? 4 : 3} className={`v2-dot is-${h.status}${h.urgent ? " is-urgent" : ""}`} />
      ))}
      {houses.map((h, i) => (
        <path key={i} d={path(h.outline)} className={`v2-house is-${h.kind}`} />
      ))}
    </svg>
  );
}
