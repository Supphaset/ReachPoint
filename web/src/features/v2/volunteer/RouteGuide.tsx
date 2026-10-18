import type { MissionRoute } from "../api";
import { Tr, useT } from "../ui/lang";

export function warningTh(w: string): string {
  if (w === "direct line, check on the ground") return "เส้นตรง โปรดตรวจสอบหน้างาน";
  const carry = w.match(/dry (\d+) m/);
  if (carry) return `ทางแห้ง ${carry[1]} ม. ต้องยกเรือไป ${carry[1]} ม.`;
  if (w.includes("needs a boat")) return `${w.split(":")[0]}: น้ำลึกเกินขีดจำกัดพาหนะ ต้องใช้เรือ`;
  if (w.includes("coordinates")) return "ยังไม่มีพิกัดบ้าน โปรดยืนยันตำแหน่ง";
  if (w.includes("unknown")) return `${w.split(":")[0]}: ยังไม่ทราบจำนวนคน ต้องยืนยันที่นั่งก่อนออกเดินทาง`;
  if (w.includes("capacity")) return `${w.split(":")[0]}: จำนวนคนเกินที่นั่ง ต้องเพิ่มความจุ`;
  if (w.includes("shelter")) return "ไม่พบจุดส่งต่อที่แห้งและเข้าถึงได้ โปรดจัดการส่งต่อหน้างาน";
  if (w.includes("return")) return "น้ำบนเส้นทางกลับลึกเกินขีดจำกัด โปรดตรวจสอบหน้างาน";
  return "ยังยืนยันทางเข้าหรือจุดลงเรือไม่ได้ โปรดตรวจสอบหน้างาน";
}
export function runDirections(route: MissionRoute, run: MissionRoute["runs"][number]): string | null {
  const base = "https://www.google.com/maps/dir/?api=1";
  if (route.vehicle === "boat") return `${base}&destination=${route.start.lat},${route.start.lon}&travelmode=driving`;
  if (!run.shelter) return null;
  const stops = run.legs.filter(l => run.stops.includes(l.to)).map(l => l.path[l.path.length - 1]).filter(Boolean).slice(0, 9);
  return `${base}&origin=${run.start.lat},${run.start.lon}&destination=${run.shelter.lat},${run.shelter.lon}&waypoints=${stops.map(p => `${p![1]},${p![0]}`).join("|")}&travelmode=${route.vehicle === "foot" ? "walking" : "driving"}`;
}
export function RouteGuide({ route }: { route: MissionRoute }) {
  const t = useT();
  const boatLink = `${"https://www.google.com/maps/dir/?api=1"}&destination=${route.start.lat},${route.start.lon}&travelmode=driving`;
  return <section className="mission-route" aria-label={t("เส้นทางภารกิจ", "Mission route")}>
    <p><Tr th={`เส้นทางจากแบบจำลองน้ำท่วม ณ ${route.now.at}; โปรดตรวจสอบหน้างาน`} en={`Route from the flood model at ${route.now.at}; check on the ground.`} /></p>
    {route.vehicle === "boat" && <p><Tr th="Google นำทางเรือไม่ได้ ใช้เส้นทางน้ำ ReachPoint เป็นหลัก" en="Google can't route boats. Follow the ReachPoint water route as the main guidance." /> <a href={boatLink} target="_blank" rel="noopener noreferrer"><Tr th="นำทางไปจุดลงเรือ" en="Directions to launch only" /></a></p>}
    {route.runs.map(run => <div key={run.run}>
      <h3><Tr th={`เที่ยว ${run.run}`} en={`Run ${run.run}`} /> · {run.totals.km.toFixed(1)} km · <Tr th={`${Math.round(run.totals.minutes)} นาที`} en={`${Math.round(run.totals.minutes)} min`} /></h3>
      {route.vehicle !== "boat" && runDirections(route, run) && <a href={runDirections(route, run)!} target="_blank" rel="noopener noreferrer"><Tr th="เปิดทั้งเที่ยวใน Google Maps" en="Open the whole run in Google Maps" /></a>}
      {run.stops.length > 9 && route.vehicle !== "boat" && <p><Tr th="Google แสดงได้ 9 จุดแรก ใช้รายการด้านล่างสำหรับจุดที่เหลือ" en="Google includes the first 9 stops; follow the list for the remaining stops." /></p>}
      <ol>{run.legs.map((leg, i) => <li key={i}>{leg.to === "shelter" ? t("จุดส่งต่อศูนย์พักพิง", "Shelter drop-off") : leg.to === "start" ? (route.vehicle === "boat" ? t("กลับจุดลงเรือ ส่งต่อรถไปศูนย์พักพิง", "Back to the launch point: hand over to a truck") : t("กลับจุดเริ่ม", "Return to start")) : leg.to} · {leg.km.toFixed(1)} km · <Tr th={`${Math.round(leg.minutes)} นาที · น้ำลึกสุด ${leg.deepestM} ม.`} en={`${Math.round(leg.minutes)} min · deepest ${leg.deepestM} m`} />
        {leg.warnings.map(w => <p key={w}><Tr th={warningTh(w)} en={w} /></p>)}</li>)}</ol>
      {run.shelter && <p>{route.vehicle === "boat" ? <Tr th="รถรับต่อไปที่:" en="The truck takes them on to:" /> : <Tr th="ศูนย์พักพิง:" en="Shelter:" />} {t(run.shelter.name, run.shelter.nameEn || run.shelter.name)}</p>}
    </div>)}
    {route.warnings.length > 0 && <ul className="rp-warning">{route.warnings.map(w => <li key={w}><Tr th={warningTh(w)} en={w} /></li>)}</ul>}
    {route.unreachable.map(h => <p key={h.id}><b>{h.id}</b> · <Tr th={h.reasonTh} en={h.reason} /></p>)}
  </section>;
}
