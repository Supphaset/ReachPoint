import type { Activity, FeedItem, FactView } from "../api";
export type Who = "gemini" | "rules" | "physics" | "action" | "doubt";
export interface TraceEntry {
  id: string;
  who: Who;
  at: string;
  atH: number;
  what: string;
  quote?: string;
  gloss?: string;
  to?: string;
}

export function readerLabel(reader: string | null | undefined) {
  return reader?.startsWith("gemini") ? "Gemini" : "Rules";
}

export function displayText(text: string): string {
  return text
    .replace(/claude[\w:.-]*/gi, "Rules")
    .replace(/\s*\(?stand-in\)?/gi, "")
    .replace(/safetyReply/g, "Reply to a check");
}

export function factGloss(fact: FactView): string {
  const value = Array.isArray(fact.value) ? fact.value.join("–") : String(fact.value);
  const labels: Record<string, string> = {
    people: "people",
    children: "children",
    elderly: "elderly people",
    cannotWalk: "unable to walk",
    urgent: "urgent help reported",
    depthRange: "reported depth range (m)",
    safe: "reported safe",
    trend: "water trend",
    forwarded: "forwarded report",
    neighbour: "neighbour report",
    about: "person described",
  };
  return `${labels[fact.field] ?? fact.field}: ${value}`;
}

export function buildTraceLines(items: FeedItem[], activity: Activity[], atH = Infinity): TraceEntry[] {
  const evidence = items.filter(item => item.atH <= atH).flatMap(feedTrace);
  const modelActivity = activity.flatMap((entry, index) => entry.atH <= atH ? activityTrace(entry, index) : []);
  return [...evidence, ...modelActivity].sort((first, second) => second.atH - first.atH);
}

function feedTrace(item: FeedItem): TraceEntry[] {
  const lines: TraceEntry[] = [];
  const facts = item.facts.filter(fact => fact.quote);
  const to = `/v/case/${item.householdId}`;
  if (facts.length) {
    lines.push({
      id: `${item.id}-read`,
      who: readerLabel(item.reader) === "Gemini" ? "gemini" : "rules",
      at: item.at,
      atH: item.atH,
      what: `Read · ${item.householdId} · ${item.zoneId ?? "zone unknown"}`,
      quote: facts.map(fact => displayText(fact.quote)).join(" · "),
      gloss: facts.map(factGloss).join(" · "),
      to,
    });
  }
  if (item.how) {
    lines.push({
      id: `${item.id}-rules`,
      who: "rules",
      at: item.at,
      atH: item.atH,
      what: displayText(item.how),
      to,
    });
  }
  return lines;
}

function activityTrace(entry: Activity, index: number): TraceEntry[] {
  const agent = entry.agent.toLowerCase();
  if (!/planner|physics|water|model/.test(agent)) return [];
  return [{
    id: `activity-${entry.atH}-${index}`,
    who: agent.includes("planner") ? "action" : "physics",
    at: entry.at,
    atH: entry.atH,
    what: displayText(entry.text),
  }];
}
