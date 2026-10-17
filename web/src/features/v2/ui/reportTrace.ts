import type { FamilyStatus, SimResult, TurnResult } from "../api";
import { displayText, factGloss, readerLabel, type TraceEntry } from "./trace";
/** A turn is the evidence boundary: no scripted facts or synthetic trace timestamps. */
export function buildReportTrace(turn: TurnResult, turnIndex: number, at: string, atH: number, previous?: FamilyStatus | null, afterTeamVisit = false): TraceEntry[] {
  const lines: TraceEntry[] = [];
  const effects = turn.effects;
  const household = effects.household;
  const prefix = `turn-${turnIndex}`;
  const to = household ? `/v/case/${household.id}` : undefined;
  const add = (suffix: string, entry: Omit<TraceEntry, "id" | "at" | "atH">) => {
    lines.push({ id: `${prefix}-${suffix}`, at, atH, turn: turnIndex, ...entry });
  };
  for (const [index, fact] of (effects.facts ?? []).entries()) {
    if (!fact.quote)
      continue;
    add(`fact-${index}`, {
      who: readerLabel(effects.reader) === "Gemini" ? "gemini" : "rules",
      what: `Read · ${factGloss(fact)}`,
      quote: fact.quote,
      gloss: factGloss(fact),
      to,
    });
  }
  if (effects.located)
    add("locate", {
      who: "rules",
      what: `Located your house from ${effects.located.by} · ${effects.located.label ?? effects.located.buildingId} → zone ${effects.located.zoneId}`,
      to: `/v/zone/${effects.located.zoneId}`,
    });
  if (effects.shelterRoute) {
    const route = effects.shelterRoute;
    add("shelter-route", {
      who: "physics",
      what: `Walk to ${route.name}: deepest ~${route.deepestM} m ${route.by === "streets" ? "along the streets" : "on a direct line (no street route)"}`,
    });
  }
  if (turn.status?.wantsOut && household?.cannotWalk)
    add("ride", { who: "rules", what: "ครอบครัวต้องการออก เดินไม่ได้ · Family wants to leave; can't walk → teams see 'needs a ride'", to });
  if (turn.status?.urgent && (afterTeamVisit || turn.status.outcome?.kind === "nobodyThere" || previous?.outcome?.kind === "nobodyThere") && turn.status.status === "open")
    add("reopened", { who: "rules", what: "ยังมีคนอยู่ในบ้าน เปิดเคสด่วนอีกครั้ง · Team visit: someone still inside → case reopened, urgent", to });
  if (household?.urgent)
    add("triage", {
      who: "rules",
      what: `${household.id} flagged urgent from reported needs · volunteer attention required`,
      to,
    });
  if (effects.depthHere) {
    const [depth, low, high] = effects.depthHere;
    const model = effects.simHere;
    add("depth", {
      who: "physics",
      what: `${model == null ? "Model depth unavailable" : `Model ${model.toFixed(1)} m`} → model + reports ${depth.toFixed(1)} m · likely ${low.toFixed(1)}–${high.toFixed(1)} m`,
    });
  }
  if (turn.reply)
    add("asking", {
      who: readerLabel(effects.reader) === "Gemini" ? "gemini" : "rules",
      what: "Agent reply / next question",
      quote: displayText(turn.reply),
      gloss: replyGloss(turn),
    });
  if (effects.neighbour?.sure)
    add("neighbour", {
      who: "action",
      what: `${effects.neighbour.householdId} · ${effects.neighbour.known ? "already known; not counted twice" : "confirmed as a separate neighbour household"}`,
      to: `/v/case/${effects.neighbour.householdId}`,
    });
  return lines;
}

function replyGloss(turn: TurnResult): string {
  // an English reply that only quotes a Thai place name is its own gloss
  const thai = (turn.reply.match(/[\u0e00-\u0e7f]/g) ?? []).length;
  const latin = (turn.reply.match(/[a-z]/gi) ?? []).length;
  if (thai < latin)
    return turn.reply;
  if (turn.effects.nbConfirm)
    return "Please confirm the neighbour’s house in the satellite picture.";
  if (turn.session.pending === "nb_confirm")
    return "Is this the neighbour’s house?";
  if (/กี่คน|กี่ท่าน/.test(turn.reply))
    return "How many people are with you?";
  if (/ข้าง|เพื่อนบ้าน|ใกล้/.test(turn.reply))
    return "The agent is asking about nearby households.";
  if (/น้ำ/.test(turn.reply))
    return "The agent is discussing the reported water level and asking for details.";
  if (/ที่อยู่|บ้านเลขที่|ซอย/.test(turn.reply))
    return "The agent is asking for location details.";
  return "Thai agent reply; the extracted facts above provide the English evidence summary.";
}

/** Only describe effects actually returned for this simulation. */
export function buildFollowUpTrace(result: SimResult, index: number, at: string, atH: number): TraceEntry[] {
  const what: Record<SimResult["event"], string> = {
    rain: "แจ้งเตือนฝนครอบครัวนี้ · Warned this family: more rain",
    river: "แจ้งเตือนน้ำแม่น้ำครอบครัวนี้ · Warned this family: river rising",
    teamPlan: "แจ้งแผนทีมให้ครอบครัว · Team plan told to this family",
    teamVisit: "ขอยืนยันผลการเยี่ยม · Team visit: asked this family to confirm",
    checkin: "ถามไถ่ความปลอดภัยต่อ · Sent this family a safety check-in",
  };
  if (!result.message && !result.inbox) return [];
  return [{ id: `followup-${index}`, who: "action", at, atH, turn: index, what: what[result.event] }];
}
