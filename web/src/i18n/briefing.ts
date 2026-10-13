/**
 * Thai for the area briefing's server text (labels, units, bases, unknowns, river and rain lines).
 * The server writes these from fixed templates; anything not listed here is shown as written.
 */
import type { Lang } from "./lang";

const AREA: Record<string, { label: string; description: string }> = {
  "P-A": { label: "P-A · ช่วยเหลือในที่พัก", description: "น้ำตื้นกว่าทางขอบเหนือ ส่วนใหญ่อยู่บ้านได้ถ้ามีสิ่งของจำเป็น" },
  "P-B": { label: "P-B · น้ำลึก ต้องอพยพ", description: "ใจกลางเมืองหนาแน่น มีรายงานน้ำถึงอกจนท่วมหัว ดาวเทียมมองไม่เห็นพื้นที่นี้" },
  "P-C": { label: "P-C · ยังไม่มีการประเมินล่าสุด", description: "ขอบด้านใต้ มีรายงานที่อ้างอิงได้หนึ่งครั้งว่ามีคนอยู่บนหลังคา หลังจากนั้นไม่มีข้อมูล" },
};

const LABEL: Record<string, string> = {
  "Reviewed cases": "เคสที่ตรวจสอบแล้ว",
  "Seats offered, not yet confirmed": "ที่นั่งที่เสนอ ยังไม่ยืนยัน",
  "Still without a confirmed seat": "ยังไม่มีที่นั่งที่ยืนยัน",
  "Medical needs under qualified review": "ความต้องการทางการแพทย์ที่รอผู้มีคุณวุฒิประเมิน",
  "Cited flood reports in this zone": "รายงานน้ำท่วมที่อ้างอิงได้ในโซนนี้",
  "People needing evacuation (reviewed)": "คนที่ต้องอพยพ (ตรวจสอบแล้ว)",
  "Reviewed needs": "ความต้องการที่ตรวจสอบแล้ว",
  "Reported needing evacuation (reviewed)": "แจ้งว่าต้องอพยพ (ตรวจสอบแล้ว)",
  "Segments not checked": "ช่วงพื้นที่ที่ยังไม่ได้ตรวจ",
  Delivered: "ส่งแล้ว",
  "Food packs needed": "ถุงยังชีพที่ต้องการ",
  "Still needed": "ยังต้องการ",
  "Not yet in a plan": "ยังไม่อยู่ในแผน",
  "People living here (estimate). Not victims, not people needing rescue; never adds to reviewed counts.":
    "จำนวนคนที่อาศัยอยู่ (ประมาณการ) ไม่ใช่ผู้ประสบภัยหรือคนที่ต้องช่วยเหลือ และไม่นำไปรวมกับยอดที่ตรวจสอบแล้ว",
  "needed minus delivered": "ที่ต้องการ ลบ ที่ส่งแล้ว",
  "no assessment since the water rose": "ไม่มีการประเมินตั้งแต่น้ำขึ้น",
  "remaining minus plan PL-A": "ที่เหลือ ลบ แผน PL-A",
  "reviewed cases": "เคสที่ตรวจสอบแล้ว",
  "reviewed demand minus confirmed seats": "ความต้องการที่ตรวจสอบแล้ว ลบ ที่นั่งที่ยืนยัน",
  "reviewed requests": "คำขอที่ตรวจสอบแล้ว",
  "team reports": "รายงานจากทีม",
  "Water depth: no team measurement yet": "ความลึกของน้ำ: ทีมยังไม่ได้วัด",
  "Linked to the medical need": "เชื่อมกับความต้องการทางการแพทย์",
  "Needs qualified review": "ต้องให้ผู้มีคุณวุฒิประเมิน",
  "Chest deep": "น้ำถึงอก",
  "Knee deep": "น้ำถึงเข่า",
  "Waist deep": "น้ำถึงเอว",
  "Over head height": "น้ำท่วมหัว",
  "Up to the 2nd floor": "น้ำถึงชั้น 2",
};

const UNIT: Record<string, string> = { cases: "เคส", packs: "ถุง", people: "คน", reports: "รายงาน", seats: "ที่นั่ง", segments: "ช่วง" };

const PATTERNS: [RegExp, string][] = [
  [/^(T-\S+) (boat|truck) (\S+) \(conditional\)$/, "$1 $2 $3 (มีเงื่อนไข)"],
  [/^Who needs help: (\d+) of (\d+) segments not checked, (\d+) partly checked$/, "ใครต้องการความช่วยเหลือ: ยังไม่ได้ตรวจ $1 จาก $2 ช่วง ตรวจบางส่วน $3 ช่วง"],
  [/^Who needs help: (\d+) of (\d+) segments not checked$/, "ใครต้องการความช่วยเหลือ: ยังไม่ได้ตรวจ $1 จาก $2 ช่วง"],
  [/^(.+): couldn't reach \((.+)\)$/, "$1: เข้าไม่ถึง ($2)"],
  [
    /^River (\S+) at (\d\d:\d\d): ([\d.]+) m, ([\d.]+) m over the bank, ([+−-][\d.]+) m in 24 h \((.+)\)$/,
    "แม่น้ำ/คลอง $1 เวลา $2: $3 ม. สูงกว่าตลิ่ง $4 ม. เปลี่ยน $5 ม. ใน 24 ชม. ($6)",
  ],
  [
    /^Rain \(satellite estimate\): (\d+) mm in the last 3 h · (\d+) mm in 24 h \((.+)\)$/,
    "ฝน (ประมาณจากดาวเทียม): $1 มม. ใน 3 ชม.ล่าสุด · $2 มม. ใน 24 ชม. ($3)",
  ],
];

const WORD: Record<string, string> = { boat: "เรือ", truck: "รถบรรทุก", "very heavy": "หนักมาก", heavy: "หนัก", moderate: "ปานกลาง", light: "เบา", reading: "ค่าที่อ่านได้" };

/** Server briefing text in the chosen language; unknown text comes back unchanged. */
export function bt(text: string | null | undefined, lang: Lang): string {
  if (!text) return "";
  if (lang === "en") return text;
  if (LABEL[text]) return LABEL[text];
  for (const [re, th] of PATTERNS) {
    if (re.test(text)) return text.replace(re, th).replace(/\b(boat|truck|very heavy|heavy|moderate|light|reading)\b/g, (w) => WORD[w] ?? w);
  }
  return text;
}

export function areaText(id: string, label: string, description: string, lang: Lang) {
  return lang === "th" && AREA[id] ? AREA[id] : { label, description };
}

export function unitText(unit: string, n: number, lang: Lang) {
  if (lang === "th") return UNIT[unit] ?? unit;
  return n === 1 ? unit.replace(/s$/, "") : unit;
}
