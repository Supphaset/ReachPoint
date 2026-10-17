import { useEffect, useRef } from "react";
import { TraceLine } from "./Shared";
import type { TraceEntry } from "./trace";

export function traceGroups(lines: TraceEntry[]) {
  const groups = new Map<string, TraceEntry[]>();
  for (const line of lines) {
    const key = line.turn === undefined ? line.id : String(line.turn);
    const group = groups.get(key) ?? [];
    group.push(line);
    groups.set(key, group);
  }
  return [...groups.entries()];
}

export function TraceTimeline({ lines, activeTurn, onActiveTurn }: {
  lines: TraceEntry[]; activeTurn: number | null; onActiveTurn: (turn: number | null) => void;
}) {
  const box = useRef<HTMLDivElement>(null);
  const groups = traceGroups(lines);
  useEffect(() => {
    if (box.current) box.current.scrollTop = box.current.scrollHeight;
  }, [lines.length]);

  return <div className="rp-trace-timeline" ref={box} aria-live="polite">
    {!lines.length && <div className="rp-pad rp-stack">
      <h3>คำพูดกลายเป็นหลักฐาน<small className="rp-gloss">Her words become evidence.</small></h3>
      <p>ส่งข้อความในแชท แล้วติดตามการอ่านและการคำนวณ<small className="rp-gloss">Send a message to follow Gemini, rules and the flood model.</small></p>
    </div>}
    {groups.map(([key, group], index) => {
      const latest = index === groups.length - 1;
      const turn = group[0].turn;
      const summary = <><b>ข้อความ · Turn {turn ?? index + 1}</b> · {group[0].at} · {group.length} ขั้นตอน / decisions</>;
      const content = group.map(line => <TraceLine key={line.id} {...line} />);
      const shared = {
        "data-turn": turn,
        onMouseEnter: () => onActiveTurn(turn ?? null),
        onMouseLeave: () => onActiveTurn(null),
        onFocus: () => onActiveTurn(turn ?? null),
        onBlur: () => onActiveTurn(null),
        className: `rp-trace-group${latest ? " is-latest" : ""}${turn !== undefined && activeTurn === turn ? " is-linked" : ""}`,
      };
      return latest ? <section key={key} {...shared}><div className="rp-turn-heading">{summary}</div>{content}</section>
        : <details key={key} {...shared}><summary>{summary}</summary>{content}</details>;
    })}
  </div>;
}
