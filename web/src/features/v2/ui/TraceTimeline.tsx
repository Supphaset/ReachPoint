import { Tr } from "./lang";
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
      <h3><Tr th="คำพูดกลายเป็นหลักฐาน" en="Her words become evidence." /></h3>
      <p><Tr th="ส่งข้อความในแชท แล้วติดตามการอ่านและการคำนวณ" en="Send a message to follow Gemini, rules and the flood model." /></p>
    </div>}
    {groups.map(([key, group], index) => {
      const latest = index === groups.length - 1;
      const turn = group[0].turn;
      const summary = <><b><Tr th="ข้อความ" en="Turn" /> {turn ?? index + 1}</b> · {group[0].at} · {group.length} <Tr th="ขั้นตอน / decisions" en="decisions" /></>;
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
