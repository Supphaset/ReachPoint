import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { loadFlood, resetReplay, stepReplay, type FloodSegment, type FloodView, type MapMode, type MapSource } from "../../data/flood";
import { apiMode } from "../../data/mode";
import { fmtTime } from "../../data/format";
import { Banner } from "../../ui/components";
import { FloodMap, estimateLabel, markerLabel } from "./FloodMap";
import "./flood.css";

export function Evidence({ segment }: { segment: FloodSegment }) {
  return <section className="flood-evidence" aria-label="Selected segment evidence">
    <p className="eyebrow">Evidence at the reported landmark</p><h2>{segment.label}</h2>
    {segment.estimates.map((e) => <div key={e.siteId} className={`flood-estimate flood-estimate-${e.status}`}>
      <h3>{estimateLabel(e)}</h3>
      <p>{e.latestAt ? `Latest observation ${fmtTime(e.latestAt)}` : "Observation time unknown"} · {e.observationCount} records · {e.sourceReferences} numeric source references</p>
      <p>{e.trends.length ? `Reported trend: ${e.trends.join(" / ")}` : "Trend unknown"} · Independent observers unknown</p>
      <ul>{e.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
    </div>)}
    {!segment.estimates.length && <p>No water observations. Conditions remain unknown; consider a field check.</p>}
    <p>{segment.needs.reportedPeople} people in assistance reports (not unique households). {segment.needs.verifiedTransportUnassigned} verified people seeking transport.</p>
    {segment.noSatelliteDataShare > 0 && <p>Part of this segment has no satellite data. Review evidence and consider a field check.</p>}
    <a href="/desk?data=api">Review coordinator checks</a>
    <details><summary>Observation history ({segment.observations.length})</summary>
      <ul className="flood-history">{segment.observations.slice(-40).reverse().map((o) => <li key={o.observationId}>
        <strong>{o.depthM !== null ? `${o.depthM.toFixed(2)} m reported` : (o.band ?? "unknown").replaceAll("_", " ")}</strong>
        <span>{o.review.replaceAll("_", " ")} · {o.source.replaceAll("_", " ")} · {o.reference.replaceAll("_", " ")}</span>
        <span>Observed {o.observedAt ? fmtTime(o.observedAt) : "time unknown"}; received {fmtTime(o.receivedAt)}</span>
        <span>Evidence {o.observationId}</span>
      </li>)}</ul><p>Last 40 observations shown. Original transcripts and household locations are withheld.</p>
    </details>
  </section>;
}
export function FloodPage() {
  const [source, setSource] = useState<MapSource>("replay");
  const [mode, setMode] = useState<MapMode>("water");
  const [view, setView] = useState<FloodView | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [zone, setZone] = useState("all");
  const [playing, setPlaying] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const generation = useRef(0);
  const refresh = useCallback(async () => {
    const g = generation.current;
    try { const v = await loadFlood(source); if (g === generation.current) { setView(v); setError(null); } }
    catch (e) { if (g === generation.current) setError(e instanceof Error ? e.message : String(e)); }
  }, [source]);
  useEffect(() => { generation.current++; setView(null); setPlaying(false); void refresh(); }, [refresh]);
  const step = useCallback(async (count: number) => {
    if (!view?.replay || busy) return;
    setBusy(true);
    try { await stepReplay(view.replay.cursor, view.replay.revision, count); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); setPlaying(false); }
    finally { setBusy(false); }
  }, [view, busy, refresh]);
  useEffect(() => {
    if (!playing || busy || !view?.replay) return;
    if (view.replay.cursor >= view.replay.total) { setPlaying(false); return; }
    const timer = setTimeout(() => void step(20), 1000);
    return () => clearTimeout(timer);
  }, [playing, busy, view, step]);
  // Operations change in other screens; refresh while the replay remains manually controlled.
  useEffect(() => {
    if (source !== "operations") return;
    const timer = setInterval(() => void refresh(), 5000);
    return () => clearInterval(timer);
  }, [source, refresh]);
  const reset = async () => {
    if (!view?.replay || busy) return;
    setPlaying(false); setBusy(true);
    try { await resetReplay(view.replay.cursor, view.replay.revision); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };
  const segments = view?.segments.filter((s) => zone === "all" || s.zoneId === zone) ?? [];
  const focused = segments.find((s) => s.segmentId === selected);
  const planningArea = focused?.areaId ?? (zone === "all" ? null : segments[0]?.areaId);
  return <div className="page flood-page">
    <header className="flood-header"><div><p className="eyebrow">Hat Yai · Flood response workspace</p><h1>From reports to response</h1><p>Water evidence, outstanding needs and team coverage in one place.</p></div>
      <label>Dataset<select value={source} onChange={(e) => { setSource(e.target.value as MapSource); setSelected(null); }} disabled={busy}>
        <option value="replay">1,200-report simulation</option><option value="operations">Operational demo jobs</option></select></label>
    </header>
    {!apiMode() && <Banner kind="info">This workspace needs the API server. Open with ?data=api. No fixture is presented as live data.</Banner>}
    {error && <Banner kind="error">{error} <button onClick={() => void refresh()}>Refresh</button></Banner>}
    {view && <>
      <p className="flood-disclosure">{view.processingMode} · As of {fmtTime(view.asOf)}. Synthetic operational records.</p>
      {view.replay && <section className="replay-controls" aria-label="Replay controls">
        <button onClick={() => setPlaying(!playing)} disabled={busy || view.replay.cursor === view.replay.total}>{playing ? "Pause" : "Play reports"}</button>
        <button onClick={() => void step(20)} disabled={busy || playing || view.replay.cursor === view.replay.total}>Next 20</button>
        <button onClick={() => void step(200)} disabled={busy || playing || view.replay.cursor === view.replay.total}>Next 200</button>
        <button onClick={() => void reset()} disabled={busy}>Reset simulation</button>
        <progress max={view.replay.total} value={view.replay.cursor} aria-label="Reports replayed" /><span>{view.replay.cursor} / {view.replay.total}</span>
        <p>Replay only. Team commitments and resident status are untouched. Phone inputs here are simulated transcripts; live voice is a separate integration.</p>
      </section>}
      <dl className="flood-counts"><div><dt>Reports received</dt><dd>{view.counters.received}</dd></div><div><dt>Organized by simulator</dt><dd>{view.counters.organized}</dd></div>
        <div><dt>Exceptions</dt><dd>{view.counters.exceptions}</dd></div><div><dt>Urgent reports</dt><dd>{view.counters.urgentReports}</dd></div>
        <div><dt>Water observations</dt><dd>{view.counters.observations}</dd></div><div><dt>Local estimates</dt><dd>{view.counters.numericEstimates}</dd></div><div><dt>Conflicting sites</dt><dd>{view.counters.conflicts}</dd></div></dl>
      <div className="flood-toolbar"><div role="group" aria-label="Map mode">{(["water", "needs", "response"] as MapMode[]).map((m) =>
        <button key={m} aria-pressed={mode === m} onClick={() => setMode(m)}>{m[0].toUpperCase() + m.slice(1)}</button>)}</div>
        <label>Focus zone<select value={zone} onChange={(e) => { setZone(e.target.value); setSelected(null); }}><option value="all">All zones</option>
          {[...new Set(view.segments.map((s) => s.zoneId))].map((z) => <option key={z}>{z}</option>)}</select></label>
      </div>
      <div className="flood-workspace"><div><FloodMap segments={segments} mode={mode} selected={selected} onSelect={setSelected} zone={zone} teams={view.teams} onZone={(z) => { setZone(z); setSelected(null); }} />
        <section className="flood-planning"><h2>Plan the response</h2>
          {source === "replay" ? <p>These reports are an isolated simulation and do not become operational jobs. Switch to Operational demo jobs to compare demo resources and send team asks.</p> : <>
            <p>{view.counters.verifiedTransportUnassigned} verified people still seeking transport. Estimates suggest checks; they do not prove route safety.</p>
            <Link className="flood-plan-link" to={`/desk/split?data=api${planningArea ? `&area=${planningArea}` : ""}`}>Compare whole-family transport plans{planningArea ? ` in ${planningArea}` : ""}</Link>
            <ul>{view.teams.map((t) => <li key={t.teamId}><strong>{t.teamId} · {t.resourceId}</strong> — {t.resourceStatus === "unavailable" ? "Unavailable" : t.status}, {t.freeSeats} free demo seats · updated {fmtTime(t.statusSetAt)}</li>)}</ul>
          </>}
        </section>
      </div><aside>{focused ? <Evidence segment={focused} /> : <section className="flood-evidence"><h2>Inspect a segment</h2><p>Select a marker or a row below to see evidence, uncertainty and outstanding needs.</p></section>}
        <section className="flood-segment-list" aria-label="Segment list"><h2>{segments.length} segments</h2>{segments.map((s) => <button key={s.segmentId} aria-pressed={selected === s.segmentId} onClick={() => setSelected(s.segmentId)}>
          <strong>{s.label}</strong><span>{markerLabel(s, mode)}</span></button>)}</section></aside></div>
      {view.exceptionsTotal > 0 && <details className="flood-exceptions"><summary>Attention queue · {view.exceptionsTotal} exceptions (latest 100)</summary>
        <ul>{view.exceptions.map((r) => <li key={r.reportId}><strong>{r.urgent ? "Urgent · " : ""}{r.reportId}</strong> · {r.segmentId ?? "Location unknown"} — {r.reasons.join("; ")}</li>)}</ul>
      </details>}
      <p className="fine-print">{view.note}</p>
    </>}
    {!view && !error && <p>Loading map evidence…</p>}
  </div>;
}
