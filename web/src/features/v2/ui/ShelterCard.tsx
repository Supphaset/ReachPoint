import { useEffect, useRef, useState } from "react";
import { loadGoogleMaps, type Maps } from "../../../data/googleMaps";
import { cssVar, v2, type ShelterRoute } from "../api";
import { bindFloodZoom } from "../floodLayer";
import { useFloodCanvas } from "../BoardMap";
import { useGeo, useLive } from "../volunteer/shared";
import { ChoiceButtons } from "./FamilyFollowUp";
import { Icon } from "../../../ui/Icon";
import { Sheet } from "./Sheet";
import "./phase-three.css";

export function routeTone(depth: number | null) {
  return depth === null ? "unknown" : depth <= 0.25 ? "light" : depth <= 0.5 ? "mid" : "deep";
}

/** Preserve the street geometry; samples supply the nearest local water estimate at each segment. */
export function routeSegments(route: Pick<ShelterRoute, "path" | "samples">) {
  return route.path.slice(1).map((end, index) => {
    const start = route.path[index];
    const lon = (start[0] + end[0]) / 2;
    const lat = (start[1] + end[1]) / 2;
    const nearest = [...route.samples].sort((a, b) =>
      (a[0] - lon) ** 2 + (a[1] - lat) ** 2 - ((b[0] - lon) ** 2 + (b[1] - lat) ** 2))[0];
    return { start, end, tone: routeTone(nearest?.[2] ?? null) };
  });
}

export function ShelterAnswers({ walkable, disabled, onAnswer }: { walkable: boolean; disabled: boolean; onAnswer: (text: string) => boolean | Promise<boolean> }) {
  const answers = walkable
    ? [["ไป", "ไป · I'll go"], ["อยู่บ้าน", "อยู่บ้าน · Stay home"]]
    : [["ไปได้", "ไปได้ (มีเรือ/รถยกสูง) · I can get there"], ["ต้องการทีม", "ต้องการทีม · Need a team"]];
  return <div className="p3-shelter-answers"><ChoiceButtons kind="shelter" options={answers.map(([send, label]) => ({ send, label }))}
    disabled={disabled} onSend={async text => onAnswer(text)} /></div>;
}

export function ShelterMap({ route, full = false }: { route: ShelterRoute; full?: boolean }) {
  const geo = useGeo();
  const { data: board } = useLive(() => v2.state(), []);
  const flood = useFloodCanvas(board ? geo : null, board, board?.now.atH ?? 0, "corrected");
  const box = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<Maps>(null);
  const [maps, setMaps] = useState<Maps>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let active = true;
    const shapes: Maps[] = [];
    loadGoogleMaps("th").then(api => {
      if (!active || !box.current) return;
      const instance = new api.Map(box.current, { mapTypeId: "satellite", disableDefaultUI: true, maxZoom: 18, zoomControl: full, gestureHandling: full ? "cooperative" : "none" });
      setMap(instance);
      setMaps(api);
      const bounds = new api.LatLngBounds();
      const marker = (point: number[], title: string, placement: "above" | "below" | "right" = "above") => {
        const position = { lng: point[0], lat: point[1] };
        bounds.extend(position);
        shapes.push(new api.Marker({ map: instance, position, title,
          icon: {
            path: placement === "below" ? "M 0 0 L 0 20" : placement === "right" ? "M 0 0 L 20 0" : "M 0 0 L 0 -20",
            strokeColor: cssVar("--surface"), strokeWeight: 3,
            labelOrigin: new api.Point(placement === "right" ? 70 : 0, placement === "below" ? 32 : placement === "right" ? 0 : -32),
          },
          label: full || placement === "right" ? { text: title, color: cssVar("--ink-1"), fontSize: "14px", className: "p4-map-label" } : undefined,
          zIndex: 20,
        }));
      };
      marker(route.from, "บ้าน · Home", "below");
      marker([route.lon, route.lat], route.name);
      marker(route.deepestAt, `~${route.deepestM} ม.`, "right");
      for (const segment of routeSegments(route)) {
        [segment.start, segment.end].forEach(point => bounds.extend({ lng: point[0], lat: point[1] }));
        shapes.push(new api.Polyline({ map: instance, path: [segment.start, segment.end].map(point => ({ lng: point[0], lat: point[1] })), strokeColor: cssVar(`--route-${segment.tone}`), strokeWeight: segment.tone === "deep" ? 8 : 6, zIndex: 10 }));
      }
      instance.fitBounds(bounds, full ? 80 : 44);
    }, () => active && setFailed(true));
    return () => { active = false; shapes.forEach(shape => shape.setMap(null)); };
  }, [route, full]);
  useEffect(() => {
    if (!map || !maps || !flood.sim) return;
    const [west, south, east, north] = flood.sim.meta.bbox;
    // Use the board's canvas pane: flood below route polylines and labels, redrawn in place.
    const canvas = flood.canvas;
    canvas.className = "v2-flood-canvas";
    const overlay = new class extends maps.OverlayView {
      onAdd() { this.getPanes().mapPane.appendChild(canvas); }
      draw() {
        const projection = this.getProjection();
        const sw = projection.fromLatLngToDivPixel(new maps.LatLng(south, west));
        const ne = projection.fromLatLngToDivPixel(new maps.LatLng(north, east));
        Object.assign(canvas.style, { left: `${sw.x}px`, top: `${ne.y}px`, width: `${ne.x - sw.x}px`, height: `${sw.y - ne.y}px` });
      }
      onRemove() { canvas.remove(); }
    }();
    overlay.setMap(map);
    const unbind = bindFloodZoom(map, canvas);
    return () => {
      unbind();
      overlay.setMap(null);
    };
  }, [map, maps, flood.canvas, flood.sim]);
  return <div className="p3-route-map" ref={box} aria-label="Shelter route and flood water">{failed && <p>โหลดแผนที่ไม่ได้ · Map unavailable. Open Google Maps for directions.</p>}</div>;
}

export function ShelterCard({ route, busy, onAnswer }: { route: ShelterRoute; busy: boolean; onAnswer: (text: string) => boolean | Promise<boolean> }) {
  const [full, setFull] = useState(false);
  const { data } = useLive(() => v2.state(), []);
  let directions: string | undefined;
  try {
    const url = new URL(route.googleMaps);
    if (url.protocol === "https:" && url.hostname === "www.google.com" && url.pathname.startsWith("/maps/")) directions = url.href;
  } catch { /* A malformed URL must not become a navigation link. */ }
  return <section className="card p3-shelter">
    <div className="p3-shelter-thumb"><ShelterMap route={route} />
      <button className="btn btn-sec p3-expand" aria-label="ขยายแผนที่ · Open full map" onClick={() => setFull(true)}><Icon name="map" /></button>
    </div>
    <p>ศูนย์พักพิง {route.name} · {route.km} กม. · เดินราว {route.minutes} นาที · ลึกสุด {route.deepestM} ม.</p>
    <p>Shelter · {route.km} km · about {route.minutes} min walking · deepest {route.deepestM} m</p>
    <p>{route.by === "streets" ? "ตามถนน · along streets" : "เส้นตรง · direct line (no street route)"}</p>
    {!route.walkable && <strong>อย่าเดินลุยน้ำ · Don't wade</strong>}
    <div className="p3-actions">
      <button onClick={() => setFull(true)}>เปิดแผนที่เต็มจอ · Open full map</button>
      {directions && <a href={directions} target="_blank" rel="noopener noreferrer">นำทางด้วย Google Maps · Directions in Google Maps</a>}
    </div>
    <ShelterAnswers walkable={route.walkable} disabled={busy} onAnswer={onAnswer} />
    <p>น้ำเปลี่ยนทุกชั่วโมง · Water changes by the hour; this is not a guarantee of a dry route.</p>
    {full && <Sheet label="Full shelter map" onClose={() => setFull(false)}>
      <button className="btn btn-sec" autoFocus onClick={() => setFull(false)}>ปิด · Close</button>
      <ShelterMap route={route} full />
      <WaterLegend />
      <p>สถานการณ์น้ำ ณ {data?.at ?? "ไม่ทราบเวลา · time unavailable"} · Flood model + reports at demo time</p>
    </Sheet>}
  </section>;
}

export function WaterLegend() {
  return <p className="p3-legend">{[["light", "≤0.25 m"], ["mid", "≤0.5 m"], ["deep", ">0.5 m · อย่าลุย / don't wade"], ["unknown", "unknown"]].map(([tone, text]) => <span key={tone}><i style={{ background: `var(--route-${tone})` }} />{text}</span>)}</p>;
}
