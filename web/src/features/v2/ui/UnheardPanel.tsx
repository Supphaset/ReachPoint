import type { Unheard, UnheardStreet } from "../api";
import { directionsUrl } from "../volunteer/mission";
import { Tr, useT } from "./lang";

export function UnheardPanel({ unheard, streets, seats, mission = false }: { unheard?: Unheard; streets?: UnheardStreet[]; seats?: number; mission?: boolean }) {
  const t = useT();
  if (!unheard || !(unheard.streets.length || (unheard.notHeard?.[1] ?? 0) > 0)) return null;
  const buildings = unheard.floodedBuildings ?? unheard.streets.reduce((n, s) => n + s.floodedBuildings, 0);
  return <section className="rp-card rp-pad">
    <h2>{mission ? <Tr th="ตรวจระหว่างทางด้วย · ประมาณการ ยังไม่มีคำขอ" en="Also check on the way · estimated, no request yet" /> : <Tr th="ยังไม่ได้ติดต่อ" en="Not heard from yet" />}</h2>
    <p><Tr th={`≈ ${buildings} อาคารน้ำท่วมยังไม่มีคำขอ (ประมาณการแบบจำลอง)`} en={`≈ ${buildings} flooded buildings with no request (model estimate)`} /></p>
    {unheard.notHeard && <p><Tr th={`≈ ${unheard.notHeard.join("–")} ครัวเรือนยังไม่ได้ติดต่อ (ประมาณการ)`} en={`≈ ${unheard.notHeard.join("–")} households not heard from (estimate)`} /></p>}
    <p><Tr th={`ประมาณ ${unheard.estimatedHouseholds?.join("–") ?? "?"} ครัวเรือนที่ได้รับผลกระทบ ติดต่อแล้ว ${unheard.heardFrom} ครัวเรือน`} en={`Estimated affected households: ${unheard.estimatedHouseholds?.join("–") ?? "unknown"}; heard from ${unheard.heardFrom} households`} /></p>
    <p><Tr th="ประเมินจากแบบจำลองน้ำท่วมและขอบเขตอาคาร ไม่ใช่รายงาน ไม่ยืนยันว่ามีคนอยู่หรือต้องอพยพ" en="Estimated from the flood model and building outlines, not reports. Occupancy and evacuation needs are unconfirmed." /></p>
    <ul>{(streets ?? unheard.streets).map(street => <li key={street.name}>
      {t(street.name, street.nameEn)} · <Tr th={`ระดับน้ำจำลอง ${street.depthM} ม. · อาคารน้ำท่วม ${street.floodedBuildings} หลัง`} en={`${street.depthM} m modelled depth · ${street.floodedBuildings} flooded buildings`} />
      {mission && <> · <a href={directionsUrl(street.lat, street.lon)!} target="_blank" rel="noopener noreferrer"><Tr th="นำทาง" en="Directions" /></a></>}</li>)}</ul>
    {!(streets ?? unheard.streets).length && <p><Tr th="ยังระบุถนนที่ไม่มีรายงานไม่ได้" en="No streets without reports identified yet." /></p>}
    {seats !== undefined && <p>{seats > 0 ? <Tr th={`เว้น ${seats} ที่นั่งสำหรับคนที่พบระหว่างทาง`} en={`Keep ${seats} seats free for people found on the way`} /> : <Tr th="คำขอเต็มเรือแล้ว ไม่มีที่นั่งเหลือ" en="Requests already fill the boat; no spare seats." />}</p>}
  </section>;
}
