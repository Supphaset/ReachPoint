import { useState } from "react";
import type { AssistanceType, ReviewQueueView, ReviewRow, WaterBand } from "../../data/contract";
import { approveReport, rejectReport, type Approval } from "../../data/intake";
import { apiMode } from "../../data/mode";
import { useView } from "../../data/useView";
import { Banner, BigButton, ProposalCard, Skeleton } from "../../ui/components";
import "../intake/intake.css";

const NEED_LABEL: Record<AssistanceType, string> = { evacuation_transport: "Evacuation", medical: "Medical", supplies: "Supplies" };
const BAND_LABEL: Record<WaterBand, string> = { knee: "Knee deep", waist: "Waist deep", chest: "Chest deep", over_head: "Over head height", second_floor: "Up to the 2nd floor" };
function peopleText(p: { adults: number; children: number; infants: number; stretcher: number }) {
  const n = (k: number, one: string, many: string) => (k ? `${k} ${k === 1 ? one : many}` : null);
  return [n(p.adults, "adult", "adults"), n(p.children, "child", "children"), n(p.infants, "baby", "babies"), n(p.stretcher, "person who can't walk", "people who can't walk")]
    .filter(Boolean)
    .join(", ");
}

const KIND_LABEL = { my_household: "Their own household", check_on: "Asking for someone else", neighbour_report: "What a neighbour can see" };

/**
 * Desk review (T3): each request in the caller's words, the AI's reading as a proposal with quotes, and the facts the
 * coordinator approves. Only the approved values become a case; the AI never decides counts, place or urgency.
 */
export function ReviewQueue() {
  const [n, setN] = useState(0);
  const v = useView<ReviewQueueView>(apiMode() ? `views/reviewQueue?r=${n}` : null);
  if (!apiMode()) return <Banner kind="info">Review queue: open the app with ?data=api to see requests sent from Ask for help.</Banner>;
  if (v.status === "loading") return <Skeleton lines={3} />;
  if (v.status !== "ready") return <Banner kind="error">Review queue unavailable.</Banner>;
  const q = v.data;
  return (
    <section className="review" aria-label="Requests to review">
      <h2>Requests to review ({q.reports.length})</h2>
      {q.reports.length === 0 && <p className="muted">No requests waiting. New ones appear here within 15 seconds.</p>}
      {q.reports.map((r) => (
        <Row key={r.reportId} r={r} landmarks={q.landmarks} onDone={() => setN((x) => x + 1)} />
      ))}
    </section>
  );
}

function Row({ r, landmarks, onDone }: { r: ReviewRow; landmarks: ReviewQueueView["landmarks"]; onDone: () => void }) {
  const f = r.proposal.facts;
  const [segmentId, setSegment] = useState(r.suggestedSegment?.segmentId ?? "");
  const [people, setPeople] = useState(() => {
    const p = f.people;
    return { adults: p?.adults ?? 0, children: p?.children ?? 0, infants: p?.infants ?? 0, stretcher: p?.stretcher ?? 0 };
  });
  const [needs, setNeeds] = useState<AssistanceType[]>(f.needs.length ? f.needs.map((x) => x.type) : ["evacuation_transport"]);
  const [band, setBand] = useState<WaterBand | "">(f.water?.band ?? "");
  const [urgent, setUrgent] = useState("");
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const total = people.adults + people.children + people.infants + people.stretcher;

  const approve = async () => {
    setBusy(true);
    const a: Approval = { segmentId, people, needs, waterBand: band || null, urgentReason: urgent.trim() || null, deskNote: null };
    const res = await approveReport(r.reportId, a);
    setBusy(false);
    if (!res.ok) return setMsg(res.message);
    onDone();
  };
  const reject = async () => {
    setBusy(true);
    const res = await rejectReport(r.reportId, reason);
    setBusy(false);
    if (!res.ok) return setMsg(res.message);
    onDone();
  };
  const id = (s: string) => `${r.reportId}-${s}`;

  return (
    <article className="review-row">
      <div className="rising-row-top">
        <strong className="num">{r.reportId}</strong>
        <span className="muted">{new Date(r.receivedAt).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Bangkok" })}</span>
        <span className="muted">· {r.channel}</span>
      </div>
      <blockquote className="review-text">{r.text}</blockquote>
      <ProposalCard title={f.summary || "Proposed facts"}>
        <ul className="review-facts">
          <li>{KIND_LABEL[f.kind]}{f.kindQuote && <> · <q>{f.kindQuote}</q></>}</li>
          {f.people && <li>{peopleText(f.people)} · <q>{f.people.quote}</q></li>}
          {f.needs.map((x) => <li key={x.type}>{NEED_LABEL[x.type]} · <q>{x.quote}</q></li>)}
          {f.water && <li>{BAND_LABEL[f.water.band]} · <q>{f.water.quote}</q></li>}
          {f.place && <li>Place: {f.place.text} · <q>{f.place.quote}</q></li>}
          {f.dangerSigns.map((d) => <li key={d.quote}>Danger sign: {d.text} · <q>{d.quote}</q></li>)}
          {f.cantWalk && <li>Someone can't walk · <q>{f.cantWalk.quote}</q></li>}
        </ul>
        <p className="fine-print">
          Read by {r.proposal.source.replace("gemini:", "Gemini ")}{r.proposal.note ? ` · ${r.proposal.note}` : ""}
          {r.proposal.dropped.length ? ` · ${r.proposal.dropped.length} unquoted item(s) dropped` : ""}
        </p>
      </ProposalCard>
      {r.prompts.length > 0 && (
        <ul className="review-prompts">
          {r.prompts.map((p) => <li key={p.kind}>{p.text}</li>)}
        </ul>
      )}
      <div className="review-form">
        <label htmlFor={id("seg")}>
          Nearest landmark {r.suggestedSegment && <span className="muted">(suggested: {r.suggestedSegment.why})</span>}
          <select id={id("seg")} value={segmentId} onChange={(e) => setSegment(e.target.value)}>
            <option value="">Pick a landmark…</option>
            {landmarks.map((l) => <option key={l.segmentId} value={l.segmentId}>{l.label}</option>)}
          </select>
        </label>
        <fieldset>
          <legend>Who is there (approved count)</legend>
          {(["adults", "children", "infants", "stretcher"] as const).map((k) => (
            <label key={k} htmlFor={id(k)}>
              {{ adults: "Adults", children: "Children under 12", infants: "Babies", stretcher: "Can't walk" }[k]}
              <input id={id(k)} type="number" min={0} max={60} value={people[k]} onChange={(e) => setPeople({ ...people, [k]: Math.max(0, Number(e.target.value) || 0) })} />
            </label>
          ))}
        </fieldset>
        <fieldset>
          <legend>Help needed</legend>
          {(Object.keys(NEED_LABEL) as AssistanceType[]).map((t) => (
            <label key={t} className="inline" htmlFor={id(t)}>
              <input id={id(t)} type="checkbox" checked={needs.includes(t)} onChange={(e) => setNeeds(e.target.checked ? [...needs, t] : needs.filter((x) => x !== t))} />
              {NEED_LABEL[t]}
            </label>
          ))}
        </fieldset>
        <label htmlFor={id("band")}>
          Water at their place
          <select id={id("band")} value={band} onChange={(e) => setBand(e.target.value as WaterBand | "")}>
            <option value="">Not said</option>
            {(Object.keys(BAND_LABEL) as WaterBand[]).map((b) => <option key={b} value={b}>{BAND_LABEL[b]}</option>)}
          </select>
        </label>
        <label htmlFor={id("urgent")}>
          Flag urgent (optional): your reason makes it RED on every team list
          <input id={id("urgent")} value={urgent} onChange={(e) => setUrgent(e.target.value)} placeholder="e.g. Bedridden, can't self-evacuate" />
        </label>
        {msg && <Banner kind="error">{msg}</Banner>}
        {rejecting ? (
          <div className="review-flag">
            <label htmlFor={id("reason")}>
              Why reject? The family's status link shows it.
              <input id={id("reason")} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. Duplicate of C-03" />
            </label>
            <div className="review-actions">
              <BigButton size="md" onClick={reject} disabled={busy || !reason.trim()}>Reject request</BigButton>
              <BigButton size="md" variant="secondary" onClick={() => setRejecting(false)}>Cancel</BigButton>
            </div>
          </div>
        ) : (
          <div className="review-actions">
            <BigButton size="md" onClick={approve} disabled={busy || !segmentId || total === 0 || needs.length === 0}>
              Approve: {total} {total === 1 ? "person" : "people"}
            </BigButton>
            <BigButton size="md" variant="secondary" onClick={() => setRejecting(true)}>Reject</BigButton>
          </div>
        )}
      </div>
    </article>
  );
}
