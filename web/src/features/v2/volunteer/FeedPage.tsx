import { readerLabel, displayText } from "../ui/trace";
/** Live feed: every message as it arrives, and what the AI agents did with it. */
import { useState } from "react";
import { Link } from "react-router-dom";
import { vol } from "../api";
import { VShell, fmtTags, useLive, useTeam } from "./shared";

const FILTERS: [string | undefined, string][] = [
  [undefined, "Everything"], ["urgent", "Urgent"], ["new", "New families"], ["merged", "Merged"], ["doubtful", "Doubtful"],
  ["possibleDuplicate", "Possible duplicates"], ["neighbour", "Neighbours"], ["lostContact", "Not answering"], ["team", "Team visits"],
];

const FIELD: Record<string, string> = {
  depthRange: "Water", people: "People", elderly: "Elderly", children: "Children", cannotWalk: "Can't walk", urgent: "Urgent",
  safe: "Safe", trend: "Trend", forwarded: "Forwarded", about: "About", neighbour: "Neighbour",
};

export function factValue(field: string, v: unknown): string {
  if (field === "depthRange" && Array.isArray(v)) return `${v[0]}–${v[1]} m`;
  if (field === "neighbour" && v && typeof v === "object") {
    const n = v as { side?: string; people?: number };
    return `${n.side === "unknown" ? "direction not given" : `to the ${n.side}`}${n.people ? `, ${n.people} people` : ""}`;
  }
  if (v === true) return "yes";
  return String(v);
}

export function FactChips({ facts }: { facts: { field: string; value: unknown; quote: string }[] }) {
  return (
    <ul className="v-facts">
      {facts.filter((f) => FIELD[f.field]).map((f, i) => (
        <li key={i} title={`From the words: “${f.quote}”`}>
          <b>{FIELD[f.field]}</b> {factValue(f.field, f.value)} <q>{f.quote}</q>
        </li>
      ))}
    </ul>
  );
}

export function FeedPage() {
  const [kind, setKind] = useState<string | undefined>(undefined);
  const [team] = useTeam();
  const { data, error } = useLive(() => vol.feed(kind, team), [kind, team]);
  return (
    <VShell title="Decision feed" sub="Each message as it came in, what the AI read from it (with the person's own words) and what it did." at={data ? undefined : undefined}>
      {error ? <p className="v2-error">Couldn't reach the server: {error}</p> : null}
      <div className="v-filters" role="tablist" aria-label="Filter">
        {FILTERS.map(([k, label]) => (
          <button key={label} role="tab" aria-selected={kind === k} onClick={() => setKind(k)}>
            {label}{k && data?.counts[k] !== undefined && kind === undefined ? <span>{data.counts[k]}</span> : null}
          </button>
        ))}
      </div>
      <p className="v-muted v-small">{data ? `${data.total.toLocaleString()} messages${kind ? " match" : ""}. Showing the latest ${data.items.length}.` : "Loading…"}</p>
      <ol className="v-feed">
        {(data?.items ?? []).map((it) => (
          <li key={it.id} className={it.tags.includes("urgent") ? "is-urgent" : ""}>
            <div className="v-feed-head">
              <time>{it.at}</time>
              <span className="v-feed-src">{it.source} · {it.channel}</span>
              {fmtTags(it.tags).map((t) => <span key={t.key} className={`v2-chip ${t.tone}`}>{t.label}</span>)}
              <Link to={`/v/case/${it.householdId}`} className="v-feed-hh">{it.householdId} · {it.zoneId} →</Link>
            </div>
            <p className="v-feed-text">{it.text}</p>
            <FactChips facts={it.facts} />
            <p className="v-feed-did"><b>AI:</b> {displayText(describe(it.how, it.householdId))}{it.label === "doubtful" ? " Marked doubtful: the model and nearby reports disagree." : ""}
              {it.reader ? <span className="v-muted"> · read by {readerLabel(it.reader)}</span> : null}</p>
          </li>
        ))}
      </ol>
    </VShell>
  );
}

function describe(how: string, hid: string): string {
  if (how.startsWith("new household")) return `Started a new household ${hid}${how.includes("possibly") ? `; it may be the same family as ${how.match(/HH\d+/)?.[0]}, so it counts as a range` : ""}.`;
  if (how === "team visit") return `Recorded a team visit for ${hid} and told the family.`;
  return `Added to ${hid}: ${how}. Count unchanged.`;
}
