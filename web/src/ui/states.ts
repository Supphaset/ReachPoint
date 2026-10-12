import type { IconName } from "./Icon";

/** One colour + one icon + a Thai/English label per state. The Thai labels need a native-speaker check. */
export interface StateStyle {
  th: string;
  en: string;
  icon: IconName;
  tone: string; // CSS class suffix -> token pair
}

export const PRIORITY: Record<"red" | "yellow" | "green", StateStyle> = {
  red: { th: "ด่วนมาก", en: "Life-threatening", icon: "octagon", tone: "red" },
  yellow: { th: "ด่วน", en: "Urgent", icon: "triangle", tone: "yellow" },
  green: { th: "รอได้", en: "Can wait", icon: "circle", tone: "green" },
};

export const JOB: Record<string, StateStyle> = {
  open: { th: "รอทีม", en: "Waiting for a team", icon: "clock", tone: "waiting" },
  taken: { th: "มีทีมรับแล้ว", en: "Taken", icon: "hand", tone: "taken" },
  on_the_way: { th: "กำลังไป", en: "On the way", icon: "chevron", tone: "moving" },
  on_scene: { th: "ถึงที่แล้ว", en: "On scene", icon: "mission", tone: "moving" },
  held: { th: "พักไว้", en: "On hold", icon: "pause", tone: "held" },
  done: { th: "เสร็จแล้ว", en: "Done", icon: "check", tone: "done" },
  closed: { th: "ปิดแล้ว", en: "Closed", icon: "lock", tone: "done" },
};

export const SEGMENT: Record<string, StateStyle> = {
  not_checked: { th: "ยังไม่ได้ตรวจ", en: "Not checked", icon: "question", tone: "unknown" },
  partly_checked: { th: "ตรวจบางส่วน", en: "Partly checked", icon: "half", tone: "held" },
  checked: { th: "ตรวจแล้ว", en: "Checked", icon: "check", tone: "done" },
  could_not_reach: { th: "เข้าไม่ถึง", en: "Couldn't reach", icon: "blocked", tone: "held" },
};

export const REVIEW: Record<string, StateStyle> = {
  reported: { th: "ยังไม่ตรวจสอบ", en: "Unreviewed", icon: "question", tone: "unknown" },
  validated: { th: "ตรวจสอบแล้ว", en: "Reviewed", icon: "check", tone: "done" },
  needs_clarification: { th: "ต้องถามเพิ่ม", en: "Needs clarification", icon: "alert", tone: "held" },
};

export const TEAM_STATUS: Record<string, StateStyle> = {
  available: { th: "พร้อม", en: "Available", icon: "check", tone: "brand" },
  busy: { th: "ไม่ว่าง", en: "Busy", icon: "clock", tone: "held" },
  off_duty: { th: "พักงาน", en: "Off duty", icon: "pause", tone: "done" },
};

export const OUTCOME: Record<string, StateStyle> = {
  done: { th: "เสร็จแล้ว", en: "Done", icon: "check", tone: "done" },
  already_left: { th: "ออกไปแล้ว", en: "Already left", icon: "chevron", tone: "done" },
  not_found: { th: "ไม่พบ", en: "Not found", icon: "question", tone: "held" },
  needs_more_help: { th: "ต้องการความช่วยเหลือเพิ่ม", en: "Needs more help", icon: "alert", tone: "held" },
};
