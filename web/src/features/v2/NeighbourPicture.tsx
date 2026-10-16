/** The satellite picture the agent shows to confirm a neighbour: your house outlined yellow, the candidate orange. */
import { useEffect, useRef, useState } from "react";
import { loadGoogleMaps, type Maps } from "../../data/googleMaps";
import { cssVar, type NbConfirm } from "./api";

export function NeighbourPicture({ c, lang }: { c: NbConfirm; lang: "th" | "en" }) {
  const el = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let live = true;
    loadGoogleMaps(lang).then((maps: Maps) => {
      if (!live || !el.current) return;
      const mid = c.me ? { lng: (c.me.lon + c.candidate.lon) / 2, lat: (c.me.lat + c.candidate.lat) / 2 } : { lng: c.candidate.lon, lat: c.candidate.lat };
      const map = new maps.Map(el.current, { center: mid, zoom: 20, mapTypeId: "satellite", disableDefaultUI: true, gestureHandling: "none", keyboardShortcuts: false, tilt: 0 });
      const poly = (o: [number, number][], color: string) =>
        new maps.Polygon({ map, paths: o.map(([lng, lat]) => ({ lng, lat })), strokeColor: color, strokeWeight: 4, fillColor: color, fillOpacity: 0.25, clickable: false });
      if (c.me) poly(c.me.outline, cssVar("--house-me"));
      poly(c.candidate.outline, cssVar("--house-new"));
    }, () => live && setFailed(true));
    return () => { live = false; };
  }, [c, lang]);
  if (failed) return <Drawn c={c} />;
  return <div ref={el} className="v2-nbpic" role="img" aria-label={lang === "th" ? "ภาพถ่ายดาวเทียม บ้านคุณสีเหลือง บ้านที่ถามสีส้ม" : "Satellite picture: your house yellow, the house asked about orange"} />;
}

function Drawn({ c }: { c: NbConfirm }) {
  const all = [...(c.me?.outline ?? []), ...c.candidate.outline];
  const xs = all.map((p) => p[0]);
  const ys = all.map((p) => p[1]);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const k = 220 / Math.max(x1 - x0, y1 - y0, 1e-6);
  const d = (o: [number, number][]) => o.map(([x, y], i) => `${i ? "L" : "M"}${(20 + (x - x0) * k).toFixed(1)} ${(20 + (y1 - y) * k).toFixed(1)}`).join(" ") + "Z";
  return (
    <svg className="v2-nbpic" viewBox="0 0 260 260" role="img" aria-label="Your house and the house asked about">
      {c.me ? <path d={d(c.me.outline)} className="v2-nb-me" /> : null}
      <path d={d(c.candidate.outline)} className="v2-nb-cand" />
    </svg>
  );
}
