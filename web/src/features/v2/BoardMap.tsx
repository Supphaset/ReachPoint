/**
 * The live map: satellite imagery, zones coloured by the most likely water depth (grey = unknown, never "dry"),
 * a dot per household, and the judge's house with the neighbours they talked about.
 * Google Maps (hybrid) when a browser key is configured; otherwise a drawn map from the same data.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { loadGoogleMaps, type Maps } from "../../data/googleMaps";
import { cssVar, depthBand, type BoardState, type GeoView, type HouseholdView } from "./api";
import { drawFlood, loadSim, type Analysis, type Sim } from "./floodLayer";
import { demoRoom } from "../../data/room";

export type SimMode = "corrected" | "physics" | "off";

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
  simHour: number;
  simMode: SimMode;
}

function useAnalysis(state: BoardState | null, hour: number, mode: SimMode) {
  const [a, setA] = useState<Analysis | null>(null);
  const at = state ? Math.min(hour, state.now.atH) : null;
  useEffect(() => {
    if (mode !== "corrected" || at === null) return setA(null);
    let live = true;
    fetch(`/api/v2/analysis?at=${Math.round(at)}`, { headers: { "X-Demo-Room": demoRoom() } })
      .then((r) => r.json())
      .then((j) => live && setA(j))
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, [mode, at === null ? null : Math.round(at), state?.overall.messages]);
  return a;
}

/** Loads the simulation once and redraws the water canvas whenever the hour, mode or corrections change. */
function useFloodCanvas(geo: GeoView | null, state: BoardState | null, hour: number, mode: SimMode) {
  const [sim, setSim] = useState<Sim | null>(null);
  const canvas = useRef<HTMLCanvasElement>(document.createElement("canvas"));
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (geo) loadSim(geo.zones).then(setSim, () => undefined);
  }, [geo]);
  const corr = useAnalysis(state, hour, mode);
  useEffect(() => {
    if (!sim) return;
    if (mode === "off") {
      canvas.current.width = 1;
      canvas.current.height = 1;
    } else drawFlood(canvas.current, sim, hour, corr);
    setTick((t) => t + 1);
  }, [sim, hour, corr, mode]);
  return { sim, canvas: canvas.current, tick };
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

function GoogleBoard({ maps, geo, state, selected, onSelect, houses, focus, simHour, simMode }: Props & { maps: Maps }) {
  const flood = useFloodCanvas(geo, state, simHour, simMode);
  const overlay = useRef<Maps>(null);
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

  // the water: a canvas stretched over the simulation's grid, under the dots
  useEffect(() => {
    if (!map.current || !flood.sim) return;
    if (!overlay.current) {
      const [w, s, e, n] = flood.sim.meta.bbox;
      const cv = flood.canvas;
      cv.className = "v2-flood-canvas";
      const O = class extends maps.OverlayView {
        onAdd() {
          this.getPanes().overlayLayer.appendChild(cv);
        }
        draw() {
          const p = this.getProjection();
          const sw = p.fromLatLngToDivPixel(new maps.LatLng(s, w));
          const ne = p.fromLatLngToDivPixel(new maps.LatLng(n, e));
          cv.style.left = `${sw.x}px`;
          cv.style.top = `${ne.y}px`;
          cv.style.width = `${ne.x - sw.x}px`;
          cv.style.height = `${sw.y - ne.y}px`;
        }
        onRemove() {
          cv.remove();
        }
      };
      overlay.current = new O();
      overlay.current.setMap(map.current);
    }
  }, [maps, flood.sim, flood.canvas]);

  useEffect(() => {
    if (!zones.current) return;
    const line = cssVar("--depth-line");
    zones.current.setStyle((f: Maps) => {
      const id = f.getProperty("id");
      const z = state?.zones[id];
      const known = !!z?.level;
      return {
        fillColor: zoneFill(state, id),
        fillOpacity: simMode !== "off" ? 0.04 : known ? 0.55 : 0.28,
        strokeColor: id === selected ? cssVar("--house-me") : line,
        strokeWeight: id === selected ? 3 : 1,
        strokeOpacity: 0.9,
      };
    });
  }, [state, selected, simMode]);

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
function DrawnMap({ geo, state, selected, onSelect, houses, simHour, simMode }: Props) {
  const flood = useFloodCanvas(geo, state, simHour, simMode);
  const href = useMemo(() => (flood.sim && simMode !== "off" ? flood.canvas.toDataURL() : null), [flood.tick, flood.sim, simMode, flood.canvas]);
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
      {href && flood.sim ? (
        <image
          href={href}
          x={px(flood.sim.meta.bbox[0])}
          y={py(flood.sim.meta.bbox[3])}
          width={px(flood.sim.meta.bbox[2]) - px(flood.sim.meta.bbox[0])}
          height={py(flood.sim.meta.bbox[1]) - py(flood.sim.meta.bbox[3])}
          preserveAspectRatio="none"
          className="v2-flood-image"
        />
      ) : null}
      {state?.households.map((h) => (
        <circle key={h.id} cx={px(h.lon)} cy={py(h.lat)} r={h.urgent ? 4 : 3} className={`v2-dot is-${h.status}${h.urgent ? " is-urgent" : ""}`} />
      ))}
      {houses.map((h, i) => (
        <path key={i} d={path(h.outline)} className={`v2-house is-${h.kind}`} />
      ))}
    </svg>
  );
}
