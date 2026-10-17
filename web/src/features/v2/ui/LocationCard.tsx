import { Tr, useT } from "./lang";
import { useEffect, useRef, useState } from "react";
import { loadGoogleMaps, type Maps } from "../../../data/googleMaps";
import { Icon } from "../../../ui/Icon";
import { cssVar, v2, type LocationPin } from "../api";
import { Sheet } from "./Sheet";
import "./phase-three.css";

type Point = { lon: number; lat: number };
const CENTER: Point = { lon: 100.4747, lat: 7.0086 };

export function HouseLocation({ point, buildingId, zoneId, sent = false, accuracyM }: {
  point: Point; buildingId?: string; zoneId?: string; sent?: boolean; accuracyM?: number;
}) {
  const t = useT();
  const box = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let active = true;
    const shapes: Maps[] = [];
    loadGoogleMaps("en").then(api => {
      if (!active || !box.current) return;
      const position = { lng: point.lon, lat: point.lat };
      const map = new api.Map(box.current, { center: position, zoom: 16, maxZoom: 18, mapTypeId: "satellite", disableDefaultUI: true, gestureHandling: "none" });
      shapes.push(new api.Marker({ map, position, title: t("บ้าน · Your house", "Your house") }));
      if (buildingId) void v2.buildings(point.lon, point.lat, 60).then(result => {
        if (!active) return;
        const building = result.buildings.find(candidate => candidate.id === buildingId);
        if (building) shapes.push(new api.Polygon({ map, paths: building.outline.map(([lng, lat]) => ({ lng, lat })), fillColor: cssVar("--house-me"), fillOpacity: .2, strokeColor: cssVar("--house-me"), strokeWeight: 3, zIndex: 10 }));
      }, () => undefined);
    }, () => active && setFailed(true));
    return () => { active = false; shapes.forEach(shape => shape.setMap(null)); };
  }, [point.lon, point.lat, buildingId]);
  return <section className={`card p3-location p3-house${sent ? " is-sent" : ""}`}>
    <div ref={box} className="p3-house-map" aria-label="House location">{failed && <span><Tr th="โหลดแผนที่ไม่ได้" en="Map unavailable" /></span>}</div>
    <div className="v2-card-body"><b>{sent ? t("ส่งตำแหน่งแล้ว", "Location shared") : t("พบบ้านคุณแล้ว", "House found")}</b>
      <small>{sent ? "Location sent" : "Found your house"}</small>
      {zoneId && <span className="pill p-plain"><Tr th="โซน" en="Zone" /> {zoneId}</span>}
      {accuracyM != null && <span>GPS ±{Math.round(accuracyM)} m</span>}
    </div>
  </section>;
}

function LocationThumbnail() {
  const t = useT();
  const box = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let active = true;
    loadGoogleMaps("en").then(api => {
      if (active && box.current) new api.Map(box.current, {
        center: { lng: CENTER.lon, lat: CENTER.lat }, zoom: 13, maxZoom: 18,
        mapTypeId: "roadmap", disableDefaultUI: true, gestureHandling: "none",
      });
    }, () => active && setFailed(true));
    return () => { active = false; };
  }, []);
  return <div ref={box} className="p3-location-preview" aria-label={t("หาดใหญ่ · Hat Yai map", "Hat Yai map")}>
    {failed && <><Icon name="map" size={32} /><span><Tr th="แผนที่โหลดไม่ได้" en="Map unavailable" /></span></>}
  </div>;
}

export function LocationCard({ busy, outside, onPin }: { busy: boolean; outside: boolean; onPin: (pin: LocationPin) => Promise<void> }) {
  const t = useT();
  const [sheet, setSheet] = useState(outside);
  const [message, setMessage] = useState("");
  const [fix, setFix] = useState<Point | null>(null);
  const [locating, setLocating] = useState(false);
  useEffect(() => {
    if (outside) {
      setMessage(t("ตำแหน่งอยู่นอกหาดใหญ่ กรุณาปักหมุดบ้านในหาดใหญ่ · Pin outside Hat Yai. Choose your house in Hat Yai on the map.", "Pin outside Hat Yai. Choose your house in Hat Yai on the map."));
      setSheet(true);
    }
  }, [outside]);
  const gps = () => {
    setLocating(true);
    const fail = (reason: string) => {
      setLocating(false);
      setMessage(t(`ใช้ GPS ไม่ได้ กรุณาปักหมุดแทน · ${reason}. Pin on the map instead.`, `${reason}. Pin on the map instead.`));
      setSheet(true);
    };
    if (!navigator.geolocation) return fail(t("ไม่มี GPS · GPS unavailable", "GPS unavailable"));
    navigator.geolocation.getCurrentPosition(position => {
      setLocating(false);
      const point = { lon: position.coords.longitude, lat: position.coords.latitude };
      setFix(point);
      void onPin({ ...point, method: "gps", accuracyM: position.coords.accuracy });
    }, error => fail(error.code === 1 ? t("ไม่ได้อนุญาต GPS · GPS permission denied", "GPS permission denied") : error.code === 3 ? t("GPS หมดเวลา · GPS timed out", "GPS timed out") : t("ไม่มีสัญญาณ GPS · GPS unavailable", "GPS unavailable")), { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
  };
  return <div className="card p3-location">
    <LocationThumbnail />
    <p><Tr th="บ้านอยู่ที่ไหน · Where is your house? พิมพ์ที่อยู่ได้เช่นกัน" en="Where is your house? You can also type an address." /></p>
    {message && <p role="status">{message}</p>}
    <div className="p3-actions">
      <button className="btn btn-pri bl" disabled={busy || locating} onClick={gps}><Icon name="pin" /><Tr th="ใช้ GPS ของฉัน" en="Use my GPS" />{locating ? "…" : ""}</button>
      <button className="btn btn-sec" disabled={busy} onClick={() => setSheet(true)}><Tr th="ปักหมุดบนแผนที่" en="Pin on the map" /></button>
    </div>
    {sheet && <PinSheet start={outside ? CENTER : fix ?? CENTER} busy={busy} onClose={() => setSheet(false)} onConfirm={async point => { setSheet(false); await onPin({ ...point, method: "map" }); }} />}
  </div>;
}

/** Same centre-pin interaction as GoogleLocationPicker, using the v2 turn endpoint only. */
function PinSheet({ start, busy, onClose, onConfirm }: { start: Point; busy: boolean; onClose: () => void; onConfirm: (point: Point) => void }) {
  const box = useRef<HTMLDivElement>(null);
  const [point, setPoint] = useState(start);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(false);
  const [moving, setMoving] = useState(false);
  useEffect(() => {
    let active = true;
    let listener: Maps;
    let moveListener: Maps;
    loadGoogleMaps("en").then(api => {
      if (!active || !box.current) return;
      // hybrid: the satellite picture with street names, so people can find their soi
      const map = new api.Map(box.current, { center: { lng: start.lon, lat: start.lat }, zoom: 16, maxZoom: 18, mapTypeId: "hybrid", disableDefaultUI: true, zoomControl: true, gestureHandling: "greedy" });
      listener = map.addListener("idle", () => {
        setMoving(false);
        const center = map.getCenter();
        if (center) setPoint({ lon: center.lng(), lat: center.lat() });
      });
      moveListener = map.addListener("dragstart", () => setMoving(true));
      setReady(true);
    }, () => active && setError(true));
    return () => { active = false; listener?.remove(); moveListener?.remove(); };
  }, [start.lon, start.lat]);
  return <Sheet label="Pin your house" onClose={onClose}>
    <button autoFocus onClick={onClose}><Tr th="ปิด" en="Close" /></button>
    <p><Tr th="เลื่อนแผนที่ให้บ้านอยู่ใต้หมุด" en="Move your house under the pin" /></p>
    <div className="p3-picker">
      <div ref={box} className="p3-picker-map" />
      <MapsPin lifted={moving} />
    </div>
    {error && <p role="alert"><Tr th="โหลดแผนที่ไม่ได้ พิมพ์ที่อยู่ในแชทแทน" en="Map unavailable. Type your address in chat." /></p>}
    <button disabled={busy || !ready} onClick={() => onConfirm(point)}><Tr th="ใช้ตำแหน่งนี้" en="Use this spot" /></button>
  </Sheet>;
}

/** The red Google Maps pin, fixed at the centre; it lifts while the map is dragged and drops onto the spot. */
function MapsPin({ lifted }: { lifted: boolean }) {
  return <div className={`p3-pin${lifted ? " is-lifted" : ""}`} aria-hidden="true">
    <svg viewBox="0 0 27 43" width="36" height="57">
      <path className="p3-pin-body" d="M13.5 0C6 0 0 6 0 13.5c0 10.1 13.5 29.5 13.5 29.5S27 23.6 27 13.5C27 6 21 0 13.5 0z" />
      <circle className="p3-pin-dot" cx="13.5" cy="13.5" r="5" />
    </svg>
    <span className="p3-pin-shadow" />
  </div>;
}
