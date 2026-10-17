import { useEffect, useRef, useState } from "react";
import { loadGoogleMaps, type Maps } from "../../../data/googleMaps";
import type { LocationPin } from "../api";
import { Sheet } from "./Sheet";
import "./phase-three.css";

type Point = { lon: number; lat: number };
const CENTER: Point = { lon: 100.4747, lat: 7.0086 };

export function HouseLocation({ point }: { point: Point }) {
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let active = true;
    let marker: Maps;
    loadGoogleMaps("th").then(api => {
      if (!active || !box.current) return;
      const position = { lng: point.lon, lat: point.lat };
      const map = new api.Map(box.current, { center: position, zoom: 17, mapTypeId: "satellite", disableDefaultUI: true, gestureHandling: "none" });
      marker = new api.Marker({ map, position, title: "บ้าน · Your house" });
    }, () => undefined);
    return () => { active = false; marker?.setMap(null); };
  }, [point.lon, point.lat]);
  return <div className="p3-location"><span>บ้านอยู่ตรงนี้ · Your house is here</span><div ref={box} className="p3-house-map" aria-label="Confirmed house location" /></div>;
}

export function LocationCard({ busy, outside, onPin }: { busy: boolean; outside: boolean; onPin: (pin: LocationPin) => Promise<void> }) {
  const [sheet, setSheet] = useState(outside);
  const [message, setMessage] = useState("");
  const [fix, setFix] = useState<Point | null>(null);
  const [locating, setLocating] = useState(false);
  useEffect(() => {
    if (outside) {
      setMessage("ตำแหน่งอยู่นอกหาดใหญ่ กรุณาปักหมุดบ้านในหาดใหญ่ · Pin outside Hat Yai. Choose your house in Hat Yai on the map.");
      setSheet(true);
    }
  }, [outside]);
  const gps = () => {
    setLocating(true);
    const fail = (reason: string) => {
      setLocating(false);
      setMessage(`ใช้ GPS ไม่ได้ กรุณาปักหมุดแทน · ${reason}. Pin on the map instead.`);
      setSheet(true);
    };
    if (!navigator.geolocation) return fail("ไม่มี GPS · GPS unavailable");
    navigator.geolocation.getCurrentPosition(position => {
      setLocating(false);
      const point = { lon: position.coords.longitude, lat: position.coords.latitude };
      setFix(point);
      void onPin({ ...point, method: "gps", accuracyM: position.coords.accuracy });
    }, error => fail(error.code === 1 ? "ไม่ได้อนุญาต GPS · GPS permission denied" : error.code === 3 ? "GPS หมดเวลา · GPS timed out" : "ไม่มีสัญญาณ GPS · GPS unavailable"), { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
  };
  return <div className="p3-location">
    <p>บ้านอยู่ที่ไหน · Where is your house? พิมพ์ที่อยู่ได้เช่นกัน · You can also type an address.</p>
    {message && <p role="status">{message}</p>}
    <div className="p3-actions">
      <button disabled={busy || locating} onClick={gps}>📍 ใช้ GPS ของฉัน · Use my GPS{locating ? "…" : ""}</button>
      <button disabled={busy} onClick={() => setSheet(true)}>ปักหมุดบนแผนที่ · Pin on the map</button>
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
    loadGoogleMaps("th").then(api => {
      if (!active || !box.current) return;
      // hybrid: the satellite picture with street names, so people can find their soi
      const map = new api.Map(box.current, { center: { lng: start.lon, lat: start.lat }, zoom: 17, mapTypeId: "hybrid", disableDefaultUI: true, zoomControl: true, gestureHandling: "greedy" });
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
    <button autoFocus onClick={onClose}>ปิด · Close</button>
    <p>เลื่อนแผนที่ให้บ้านอยู่ใต้หมุด · Move your house under the pin</p>
    <div className="p3-picker">
      <div ref={box} className="p3-picker-map" />
      <MapsPin lifted={moving} />
    </div>
    {error && <p role="alert">โหลดแผนที่ไม่ได้ พิมพ์ที่อยู่ในแชทแทน · Map unavailable. Type your address in chat.</p>}
    <button disabled={busy || !ready} onClick={() => onConfirm(point)}>ใช้ตำแหน่งนี้ · Use this spot</button>
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
