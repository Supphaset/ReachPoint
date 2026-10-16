/**
 * A Hat Yai shophouse in side view with the water at its real modelled depth, drawn to scale (36 px per metre).
 * The judge's own house in the demo ("you"), or a family's house on the case page (their people as figures).
 * Body marks are for a 1.65 m adult standing on the ground floor, which sits a step (0.1 m) above the street.
 */
import type { ReactNode } from "react";

const PX = 36;           // px per metre
const STREET = 268;      // y of the street (depth is measured from here)
const FLOOR = 0.1;       // ground floor a step above the street, m (reported depths are above the ground)
const UPPER = 3.5;       // upper floor above the street, m
const y = (m: number) => STREET - m * PX;

export interface Family { people: number | null; elderly: number; children: number; cannotWalk: number }

const MARKS: [number, string, string][] = [
  [0.12, "ข้อเท้า", "ankle"], [0.5, "เข่า", "knee"], [1.0, "เอว", "waist"], [1.3, "อก", "chest"], [1.5, "คอ", "neck"], [1.7, "มิดหัว", "head"],
];

export function waterWords(d: number | null | undefined, lang: "th" | "en"): string {
  if (d === null || d === undefined) return lang === "th" ? "ไม่ทราบ" : "unknown";
  const inside = d - FLOOR;
  const bands: [number, string, string][] = [
    [0.05, "แห้ง", "dry"], [FLOOR, "ท่วมถนน ยังไม่เข้าบ้าน", "street flooded, not inside yet"], [FLOOR + 0.25, "ถึงข้อเท้า", "ankle deep"],
    [FLOOR + 0.6, "ถึงเข่า", "knee deep"], [FLOOR + 0.85, "ถึงต้นขา", "thigh deep"], [FLOOR + 1.15, "ถึงเอว", "waist deep"],
    [FLOOR + 1.4, "ถึงอก", "chest deep"], [FLOOR + 1.65, "ถึงคอ", "up to the neck"], [UPPER, "มิดหัว ต้องขึ้นชั้นบน", "over head height: upstairs"],
    [99, "ท่วมถึงชั้นบน", "into the upper floor"],
  ];
  void inside;
  const b = bands.find(([lim]) => d < lim) ?? bands[bands.length - 1];
  return lang === "th" ? b[1] : b[2];
}

function Person({ x, base, kind, label }: { x: number; base: number; kind: "adult" | "elderly" | "child" | "wheelchair"; label?: string }) {
  const s = kind === "child" ? 0.62 : 1;
  const h = 1.65 * PX * s;
  if (kind === "wheelchair") {
    return (
      <g className="hs-person">
        <circle cx={x} cy={base - 12} r={12} className="hs-wheel" />
        <rect x={x - 8} y={base - 46} width={16} height={22} rx={6} />
        <circle cx={x} cy={base - 54} r={7} />
        <line x1={x - 14} y1={base - 26} x2={x + 12} y2={base - 26} className="hs-limb" />
        {label ? <text x={x} y={base + 12} textAnchor="middle" className="hs-tag">{label}</text> : null}
      </g>
    );
  }
  const head = 0.11 * h;
  return (
    <g className="hs-person">
      <circle cx={x} cy={base - h + head} r={head} />
      <rect x={x - 0.11 * h} y={base - h + 2 * head + 1} width={0.22 * h} height={0.42 * h} rx={0.07 * h} />
      <line x1={x - 0.05 * h} y1={base - 0.47 * h} x2={x - 0.06 * h} y2={base} className="hs-limb" />
      <line x1={x + 0.05 * h} y1={base - 0.47 * h} x2={x + 0.06 * h} y2={base} className="hs-limb" />
      {kind === "elderly" ? <line x1={x + 0.2 * h} y1={base - 0.5 * h} x2={x + 0.24 * h} y2={base} className="hs-cane" /> : null}
      {label ? <text x={x} y={base + 12} textAnchor="middle" className="hs-tag">{label}</text> : null}
    </g>
  );
}

function figures(f: Family | undefined): ("adult" | "elderly" | "child" | "wheelchair")[] {
  if (!f) return ["adult"];
  const out: ("adult" | "elderly" | "child" | "wheelchair")[] = [];
  for (let i = 0; i < f.cannotWalk; i++) out.push("wheelchair");
  for (let i = 0; i < Math.max(0, f.elderly - f.cannotWalk); i++) out.push("elderly");
  for (let i = 0; i < f.children; i++) out.push("child");
  const rest = Math.max(0, (f.people ?? (out.length || 1)) - out.length);
  for (let i = 0; i < rest; i++) out.push("adult");
  return out.slice(0, 6);
}

export function HouseScene({ depth, lo, hi, lang, family, caption, note }: {
  depth: number | null;
  lo?: number;
  hi?: number;
  lang: "th" | "en";
  family?: Family;
  caption?: ReactNode;
  note?: ReactNode;
}) {
  const d = depth ?? 0;
  const known = depth !== null;
  const upstairs = d - FLOOR > 1.25;            // water above the chest: the family is upstairs
  const people = figures(family);
  const base = upstairs ? y(UPPER) : y(FLOOR);
  const inBand = MARKS.findIndex(([m]) => d - FLOOR < m);
  return (
    <figure className="hs">
      <svg viewBox="0 0 360 300" role="img" aria-label={`House in side view: water ${known ? `${d.toFixed(1)} m, ${waterWords(depth, "en")}` : "unknown"}`}>
        <rect x={0} y={0} width={360} height={STREET} className="hs-sky" />
        {/* the house: two floors, a door with its handle, a window upstairs */}
        <rect x={84} y={y(6.6)} width={212} height={y(FLOOR) - y(6.6)} className="hs-inside" />
        <path d={`M76 ${y(6.6)} L188 ${y(7.3)} L304 ${y(6.6)} Z`} className="hs-roof" />
        <rect x={84} y={y(UPPER) - 4} width={212} height={4} className="hs-slab" />
        <rect x={84} y={y(FLOOR) - 2} width={212} height={2 + FLOOR * PX} className="hs-slab" />
        <rect x={84} y={y(6.6)} width={212} height={y(FLOOR) - y(6.6)} className="hs-wall" />
        <rect x={90} y={y(FLOOR + 2.3)} width={30} height={2.3 * PX} className="hs-door" />
        <circle cx={114} cy={y(FLOOR + 1.0)} r={2.2} className="hs-handle" />
        <rect x={210} y={y(5.6)} width={56} height={40} className="hs-window" />
        <line x1={238} y1={y(5.6)} x2={238} y2={y(5.6) + 40} className="hs-frame" />
        <path d={`M270 ${y(FLOOR)} L270 ${y(UPPER)} M262 ${y(FLOOR)} L262 ${y(UPPER)}`} className="hs-stairs" />
        {Array.from({ length: 9 }, (_, i) => (
          <line key={i} x1={262} x2={270} y1={y(FLOOR) - ((y(FLOOR) - y(UPPER)) / 9) * (i + 0.5)} y2={y(FLOOR) - ((y(FLOOR) - y(UPPER)) / 9) * (i + 0.5)} className="hs-stairs" />
        ))}
        {/* the people */}
        {people.map((k, i) => (
          <Person key={i} x={150 + i * 20 - (people.length - 1) * 4} base={base} kind={k} label={!family && i === 0 ? (lang === "th" ? "คุณ" : "you") : undefined} />
        ))}
        {/* the water, rising from the street; the group moves so the change animates */}
        <g className="hs-water" style={{ transform: `translateY(${-d * PX}px)` }}>
          <path className="hs-wave" d={`M-360 ${STREET} ${Array.from({ length: 24 }, (_, i) => `q 15 ${i % 2 ? 4 : -4} 30 0`).join(" ")} V ${STREET + 330} H -360 Z`} />
          <rect x={0} y={STREET + 3} width={360} height={330} className="hs-water-body" />
        </g>
        <rect x={0} y={STREET} width={360} height={300 - STREET} className="hs-street" />
        <text x={12} y={STREET + 18} className="hs-tag">{lang === "th" ? "ถนน" : "street"}</text>
        {/* body marks for an adult on the ground floor */}
        {MARKS.map(([m, th, en], i) => (
          <g key={en} className={`hs-mark${i === inBand ? " is-on" : ""}`}>
            <line x1={300} x2={312} y1={y(FLOOR + m)} y2={y(FLOOR + m)} />
            <text x={315} y={y(FLOOR + m) + 3}>{lang === "th" ? th : en}</text>
          </g>
        ))}
        <text x={300} y={y(UPPER) - 8} className="hs-tag">{lang === "th" ? "ชั้นบน" : "upper floor"}</text>
        {/* the depth readout */}
        <g className="hs-readout">
          <rect x={8} y={8} width={150} height={44} rx={6} />
          <text x={16} y={28} className="hs-big">{known ? `${d.toFixed(1)} ${lang === "th" ? "ม." : "m"}` : "?"}</text>
          <text x={16} y={44} className="hs-small">{waterWords(depth, lang)}</text>
        </g>
        {lo !== undefined && hi !== undefined && known ? (
          <rect x={56} y={y(hi)} width={6} height={Math.max(2, (hi - lo) * PX)} className="hs-range"><title>likely {lo.toFixed(1)}–{hi.toFixed(1)} m</title></rect>
        ) : null}
      </svg>
      {caption ? <figcaption>{caption}</figcaption> : null}
      {note ? <p className="hs-note">{note}</p> : null}
    </figure>
  );
}
