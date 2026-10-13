import { useEffect, useRef, useState } from "react";
import type { LocationInput, Location, AssistanceType, ReviewQueueView, ReviewRow, WaterBand } from "../../data/contract";
import { approveReport, linkReport, notSame, rejectReport, type Approval } from "../../data/intake";
import { apiMode } from "../../data/mode";
import { useView } from "../../data/useView";
import { Banner, BigButton, ProposalCard, Skeleton } from "../../ui/components";
import { Icon } from "../../ui/Icon";
import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { DeskLocation } from "../location/DeskLocation";
import "../intake/intake.css";

const NEED_LABEL = { evacuation_transport: true, medical: true, supplies: true };
const BAND_LABEL = { knee: true, waist: true, chest: true, over_head: true, second_floor: true };

/** Preserve the server's triage order; only fall back when the selection leaves the queue. */
export function selectedReport(reports: ReviewRow[], selected: string | null) {
  return reports.find(r => r.reportId === selected) ?? reports[0];
}

export function ReviewQueue({ onCount }: { onCount?: (n: number) => void }) {
  const { t } = useLang();
  const [n, setN] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [completed, setCompleted] = useState<string[]>([]);
  const [message, setMessage] = useState<string>();
  const list = useRef<HTMLElement>(null);
  const focusNext = useRef(false);
  const v = useView<ReviewQueueView>(apiMode() ? `views/reviewQueue?r=${n}` : null);
  useEffect(() => { if (v.status === "ready") onCount?.(v.data.reports.filter(r => !completed.includes(r.reportId)).length); }, [v, completed, onCount]);
  useEffect(() => {
    if (v.status !== "ready" || !focusNext.current) return;
    focusNext.current = false;
    requestAnimationFrame(() => {
      const target = document.getElementById("desk-detail") ?? list.current;
      target?.focus({ preventScroll: true });
      target?.scrollIntoView({ block: "nearest" });
    });
  }, [v]);
  if (!apiMode()) return <Banner kind="info">{t(S.desk.queueOffline)}</Banner>;
  if (v.status === "loading") return <Skeleton lines={3} />;
  if (v.status !== "ready") return <Banner kind="error">{t(S.desk.queueError)}</Banner>;
  const q = v.data;
  const reports = q.reports.filter(r => !completed.includes(r.reportId));
  const current = selectedReport(reports, selected);
  const select = (id: string) => {
    setSelected(id);
    requestAnimationFrame(() => document.getElementById("desk-detail")?.focus({ preventScroll: true }));
    requestAnimationFrame(() => document.getElementById("desk-detail")?.scrollIntoView({ block: "nearest" }));
  };
  return <>
    {message && <Banner kind="info">{message}</Banner>}
    <section className="desk-inbox" aria-label={t(S.desk.queue)}>
      <aside className="desk-list" ref={list} tabIndex={-1}>
        <header><h2>{t(S.desk.queue)} ({reports.length})</h2>{q.triage && <p className="fine-print">{t(S.desk.sorted)} {q.triage.note}</p>}</header>
        {!current && <div className="desk-empty"><Icon name="check" /><h3>{t(S.desk.empty)}</h3><p className="muted">{t(S.desk.emptyBody)}</p></div>}
        <ol>{reports.map((r, index) => <li key={r.reportId}>
          <button className="desk-request" aria-pressed={r.reportId === current?.reportId} onClick={() => select(r.reportId)} onKeyDown={e => {
            if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
            e.preventDefault();
            const next = reports[Math.max(0, Math.min(reports.length - 1, index + (e.key === "ArrowDown" ? 1 : -1)))];
            setSelected(next.reportId);
            (e.currentTarget.closest("ol")?.querySelectorAll("button")[reports.indexOf(next)] as HTMLButtonElement)?.focus();
          }}>
            <span className="rising-row-top"><strong>{r.reportId}</strong><time dateTime={r.receivedAt}>{new Date(r.receivedAt).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Bangkok" })}</time></span>
            <span className="desk-preview">{r.text.split("\n")[0]}</span>
            <span className="desk-chips">
              {(r.proposal.facts.dangerSigns.length > 0 || (r.triage?.rank?.danger.length ?? 0) > 0) && <span className="chip chip-held chip-sm"><Icon name="triangle" />{t(S.desk.danger)}</span>}
              {!!r.triage?.links.length && <span className="chip chip-unknown chip-sm"><Icon name="question" />{t(S.desk.duplicate)}</span>}
              <span className="desk-ai chip chip-sm"><Icon name="sparkle" />{t(S.desk.aiRead)}</span>
            </span>
          </button>
        </li>)}</ol>
      </aside>
      {current && <div className="desk-reading">
        <button className="desk-back" onClick={() => { list.current?.focus(); list.current?.scrollIntoView({ block: "start" }); }}><Icon name="back" />{t(S.desk.back)}</button>
        <Row key={current.reportId} r={current} landmarks={q.landmarks} onDone={(msg, remove = true) => {
          setMessage(msg);
          focusNext.current = true;
          if (remove) { setCompleted(ids => [...ids, current.reportId]); setSelected(null); }
          setN(x => x + 1);
        }} />
      </div>}
    </section>
  </>;
}

function Row({ r, landmarks, onDone }: { r: ReviewRow; landmarks: ReviewQueueView["landmarks"]; onDone: (message?: string, remove?: boolean) => void }) {
  const { t } = useLang();
  const f = r.proposal.facts;
  const [segmentId, setSegment] = useState((r.location?.status === "located" ? r.location.segmentId : undefined) ?? r.suggestedSegment?.segmentId ?? "");
  const [location, setLocation] = useState<LocationInput>();
  const [resolvedLocation, setResolvedLocation] = useState<Location | undefined>(r.location);
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
    const a: Approval = { segmentId, people, needs, waterBand: band || null, urgentReason: urgent.trim() || null, deskNote: null, ...(location ? { location } : {}) };
    const res = await approveReport(r.reportId, a);
    setBusy(false);
    if (!res.ok) return setMsg(res.message);
    onDone(res.value ? t(S.desk.created(res.value.caseId)) + (urgent.trim() ? " · RED" : "") : undefined);
  };
  const act = async (p: Promise<{ ok: boolean; message?: string }>, remove = true) => {
    setBusy(true);
    const res = await p;
    setBusy(false);
    if (!res.ok) return setMsg(res.message ?? t(S.desk.error));
    onDone(undefined, remove);
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
    <article className="review-row desk-detail" tabIndex={-1} id="desk-detail">
      <div className="rising-row-top">
        <strong className="num">{r.reportId}</strong>
        <span className="muted">{new Date(r.receivedAt).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Bangkok" })}</span>
        <span className="muted">· {r.channel === "text" ? t(S.desk.textChannel) : r.channel === "voice" ? t(S.desk.voiceChannel) : r.channel}</span>
      </div>
      <blockquote className="review-text">{r.text}</blockquote>
      <DeskLocation location={resolvedLocation} disabled={busy} onApply={(input, resolved) => {
        setLocation(input); setResolvedLocation(resolved); setSegment(resolved.segmentId ?? "");
      }} />
      <ProposalCard title={f.summary || t(S.desk.facts)} label={t(S.desk.proposal)}>
        <table className="desk-facts"><thead><tr><th>{t(S.desk.fact)}</th><th>{t(S.desk.value)}</th><th>{t(S.desk.quote)}</th></tr></thead>
          <tbody>
            <tr><th>{t(S.desk.kind)}</th><td>{t(S.desk[f.kind])}</td><td>{f.kindQuote && <q>{f.kindQuote}</q>}</td></tr>
            {f.people && <tr><th>{t(S.desk.people)}</th><td>{(["adults", "children", "infants", "stretcher"] as const).map(k => `${t(S.desk[k])}: ${f.people![k]}`).join(" · ")}</td><td><q>{f.people.quote}</q></td></tr>}
            {f.needs.map(x => <tr key={x.type}><th>{t(S.desk.help)}</th><td>{t(S.desk[x.type])}</td><td><q>{x.quote}</q></td></tr>)}
            {f.water && <tr><th>{t(S.desk.water)}</th><td>{t(S.desk[f.water.band])}</td><td><q>{f.water.quote}</q></td></tr>}
            {f.place && <tr><th>{t(S.desk.place)}</th><td>{f.place.text}</td><td><q>{f.place.quote}</q></td></tr>}
            {f.dangerSigns.map(d => <tr key={d.quote}><th>{t(S.desk.danger)}</th><td>{d.text}{d.by && <span className="fine-print"> · {t(S.desk.keywordCheck)}</span>}</td><td><q>{d.quote}</q></td></tr>)}
            {f.cantWalk && <tr><th>{t(S.desk.stretcher)}</th><td>{t(S.desk.stretcher)}</td><td><q>{f.cantWalk.quote}</q></td></tr>}
          </tbody>
        </table>
        <p className="fine-print">{t(S.desk.readBy)} {r.proposal.source.replace("gemini:", "Gemini ")}{r.proposal.note ? ` · ${r.proposal.note}` : ""}{r.proposal.dropped.length ? ` · ${t(S.desk.dropped(r.proposal.dropped.length))}` : ""}</p>
      </ProposalCard>
      {r.triage && (r.triage.links.length > 0 || r.triage.rank || r.triage.question) && (
        <ProposalCard title={t(S.desk.triage)} label={t(S.desk.proposal)}>
          {r.triage.rank && <p className="fine-print">{r.triage.rank.reason}</p>}
          {r.triage.question && (
            <div className="triage-link">
              <p>{t(S.desk.askCaller(r.triage.question.caseId))} <q>{r.triage.question.text}</q></p>
            </div>
          )}
          {r.triage.links.map((l) => (
            <div key={l.caseId} className="triage-link">
              <p>
                {l.newHazard ? t(S.desk.samePlace) : t(S.desk.possibleSame)} <strong className="num">{l.caseId}</strong> ({l.place}, {l.people}{" "}
                {t(S.desk.people)}): {l.reason}
                {l.quote && <> · <q>{l.quote}</q></>}
              </p>
              {l.newHazard ? (
                <p className="review-prompts">{t(S.desk.newDanger)}</p>
              ) : (
                <div className="review-actions">
                  <BigButton size="md" variant="secondary" disabled={busy} onClick={() => act(linkReport(r.reportId, l.caseId))}>
                    {t(S.desk.linked(l.caseId))}
                  </BigButton>
                  <BigButton size="md" variant="quiet" disabled={busy} onClick={() => act(notSame(r.reportId, l.caseId), false)}>
                    {t(S.desk.notSame)}
                  </BigButton>
                </div>
              )}
            </div>
          ))}
          {!!r.triage.steps?.length && (
            <p className="fine-print">
              {t(S.desk.agentSteps)} ({r.triage.source.replace("agent:", "Gemini ")}): {r.triage.steps.map((s) => (S.desk.tools[s] ? t(S.desk.tools[s]) : s)).join(" → ")}
            </p>
          )}
        </ProposalCard>
      )}
      {r.prompts.length > 0 && (
        <ul className="review-prompts">
          {r.prompts.map((p) => <li key={p.kind}>{p.kind === "urgent_flag" ? <>{f.dangerSigns.map(d => d.text).join("; ")} · {t(S.desk.dangerPrompt)}</> : p.kind === "stretcher" ? t(S.desk.stretcherPrompt) : p.kind === "neighbour" ? t(S.desk.neighbourPrompt) : r.fromTeam ? t(S.desk.fieldPrompt(r.fromTeam)) : p.text}</li>)}
        </ul>
      )}
      <div className="review-form desk-form">
        <h3>1 · {t(S.desk.place)}</h3>
        <label htmlFor={id("seg")}>
          {t(S.desk.landmark)} {r.suggestedSegment && <span className="muted">({t(S.desk.suggested)}: {r.suggestedSegment.why})</span>}
          <select id={id("seg")} value={segmentId} onChange={(e) => setSegment(e.target.value)}>
            <option value="">{t(S.desk.pickLandmark)}</option>
            {landmarks.map((l) => <option key={l.segmentId} value={l.segmentId}>{l.label}</option>)}
          </select>
        </label>
        <fieldset className="desk-people">
          <legend>2 · {t(S.desk.approvedCount)}</legend>
          {(["adults", "children", "infants", "stretcher"] as const).map((k) => (
            <label key={k} htmlFor={id(k)}>
              {t(S.desk[k])}
              <span className="desk-stepper">
                <button type="button" aria-label={`${t(S.desk.decrease)} ${t(S.desk[k])}`} disabled={busy || people[k] <= 0} onClick={() => setPeople(p => ({ ...p, [k]: p[k] - 1 }))}>−</button>
                <input id={id(k)} type="number" min={0} max={60} step={1} value={people[k]} onChange={e => setPeople(p => ({ ...p, [k]: Math.min(60, Math.max(0, Math.floor(Number(e.target.value) || 0))) }))} />
                <button type="button" aria-label={`${t(S.desk.increase)} ${t(S.desk[k])}`} disabled={busy || people[k] >= 60} onClick={() => setPeople(p => ({ ...p, [k]: p[k] + 1 }))}>+</button>
              </span>
            </label>
          ))}
        </fieldset>
        <fieldset>
          <legend>3 · {t(S.desk.needs)}</legend>
          {(Object.keys(NEED_LABEL) as AssistanceType[]).map((need) => (
            <label key={need} className="inline" htmlFor={id(need)}>
              <input id={id(need)} type="checkbox" checked={needs.includes(need)} onChange={(e) => setNeeds(e.target.checked ? [...needs, need] : needs.filter((x) => x !== need))} />
              {t(S.desk[need])}
            </label>
          ))}
        </fieldset>
        <label htmlFor={id("band")}>
          {t(S.desk.water)}
          <select id={id("band")} value={band} onChange={(e) => setBand(e.target.value as WaterBand | "")}>
            <option value="">{t(S.desk.notSaid)}</option>
            {(Object.keys(BAND_LABEL) as WaterBand[]).map((b) => <option key={b} value={b}>{t(S.desk[b])}</option>)}
          </select>
        </label>
        <h3>4 · {t(S.desk.urgentStep)}</h3>
        <label htmlFor={id("urgent")}>
          {t(S.desk.urgent)}
          <input id={id("urgent")} value={urgent} onChange={(e) => setUrgent(e.target.value)} placeholder={t(S.desk.urgentExample)} />
        </label>
        {msg && <Banner kind="error">{msg}</Banner>}
        <footer className="desk-footer">
        {rejecting ? (
          <div className="review-flag">
            <label htmlFor={id("reason")}>
              {t(S.desk.rejectReason)}
              <input id={id("reason")} value={reason} onChange={(e) => setReason(e.target.value)} placeholder={t(S.desk.rejectExample)} />
            </label>
            <div className="review-actions">
              <BigButton size="md" onClick={reject} disabled={busy || !reason.trim()}>{t(S.desk.rejectRequest)}</BigButton>
              <BigButton size="md" variant="secondary" disabled={busy} onClick={() => setRejecting(false)}>{t(S.desk.cancel)}</BigButton>
            </div>
          </div>
        ) : (
          <div className="review-actions">
            <BigButton size="md" onClick={approve} disabled={busy || !segmentId || total === 0 || needs.length === 0}>
              {t(S.desk.approve(total))}
            </BigButton>
            <BigButton size="md" variant="secondary" disabled={busy} onClick={() => setRejecting(true)}>{t(S.desk.reject)}</BigButton>
          </div>
        )}
        </footer>
      </div>
    </article>
  );
}
