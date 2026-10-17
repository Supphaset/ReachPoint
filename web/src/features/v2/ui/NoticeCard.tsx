import type { ReactNode } from "react";
import type { FamilyStatus } from "../api";
import { Icon } from "../../../ui/Icon";

export const NOTICE_LABELS: Record<string, [string, string]> = {
  check: ["ถามไถ่ความปลอดภัย", "Safety check"], morning: ["เช้าวันใหม่", "New day"],
  earlyWarning: ["แจ้งเตือนล่วงหน้า", "Early warning"], rain: ["แจ้งเตือนฝน", "Rain alert"],
  rainRise: ["คาดว่าน้ำจะขึ้น", "Expected rise"], pickedUp: ["ทีมรับแล้ว", "Pickup report"],
  nobodyThere: ["ทีมไปแล้วไม่พบ", "Nobody there"], river: ["แจ้งเตือนน้ำขึ้น", "River alert"],
  planUpdate: ["แผนทีมอาสา", "Volunteer plan"], askBack: ["คำถามยืนยัน", "Check question"],
  quiet: ["ถามข้อมูลเพิ่ม", "Question"], lostCall: ["สายจาก AI", "AI call"],
  teamVisit: ["ทีมมาถึงแล้ว", "Team visit"], ride: ["คำขอเรือ", "Boat request"],
};

export function noticeTone(kind: string) {
  if (["river", "rain", "rainRise", "earlyWarning"].includes(kind)) return "water";
  if (["planUpdate", "pickedUp", "teamVisit"].includes(kind)) return "done";
  return "ink";
}

export function NoticeCard({ kind, at, children }: { kind: string; at?: string; children: ReactNode }) {
  const label = NOTICE_LABELS[kind] ?? ["แจ้งข้อมูล", "Update"];
  const tone = noticeTone(kind);
  return <section className={`card v2-notice-card is-${tone}`}>
    <header className={`v2-card-band is-${tone}`}>
      <Icon name={tone === "water" ? "water" : tone === "done" ? "check" : "question"} />
      <b>{label[0]}<small>{label[1]}</small></b>
      {at && <time>{at}</time>}
    </header>
    <div className="v2-card-body">{children}</div>
  </section>;
}

export function BoatRequestCard({ status }: { status: FamilyStatus | null }) {
  return <NoticeCard kind="ride" at={status?.now}>
    <p>ต้องการทีมช่วยออกจากบ้าน<small>Requested help to leave the house</small></p>
    <p>{status?.zoneId ? `โซน ${status.zoneId} · Zone ${status.zoneId}` : "ยังไม่ทราบโซน · Zone unknown"}</p>
    <p>{status?.people == null ? "จำนวนคนยังไม่ทราบ · People unknown" : `${status.people} คน · People`}</p>
    <p>{status?.team ? <>{status.team.team} ~{status.team.eta}<small>แผน ยังไม่ยืนยันการรับตัว · Planned, pickup unconfirmed</small></> : <>รอทีมวางแผน<small>Waiting for a team plan</small></>}</p>
  </NoticeCard>;
}
