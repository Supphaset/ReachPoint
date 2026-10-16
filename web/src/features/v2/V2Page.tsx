/**
 * ReachPoint v2 judge page: report as a victim on the left, watch the information system react on the right.
 * The board is the volunteer's view of Hat Yai city during the real 21–28 Nov 2025 flood (synthetic people).
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { apiMode } from "../../data/mode";
import { BoardMap, type HouseMark, type SimMode } from "./BoardMap";
import { ActivityList, PlanBox, TimeBar, ZoneCard } from "./Panels";
import { Phone } from "./Phone";
import { v2, type BoardState, type GeoView, type Timeline, type TurnResult } from "./api";
import "./v2.css";

export function V2Page() {
  const [geo, setGeo] = useState<GeoView | null>(null);
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [state, setState] = useState<BoardState | null>(null);
  const [viewH, setViewH] = useState<number | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [houses, setHouses] = useState<HouseMark[]>([]);
  const [focus, setFocus] = useState<{ lon: number; lat: number } | null>(null);
  const [playing, setPlaying] = useState(false);
  const [tab, setTab] = useState<"zone" | "activity">("zone");
  const [lang, setLang] = useState<"th" | "en">("th");
  const [chatVersion, setChatVersion] = useState(0);
  const [simMode, setSimMode] = useState<SimMode>("corrected");
  const [simHour, setSimHour] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const live = useRef(true);
  const nowH = state?.now.atH ?? 96;

  const load = useCallback((at?: number) => {
    return v2.state(at).then((s) => {
      setState(s);
      setSelected((sel) => sel ?? pickDeepest(s));
      return s;
    }, (e) => setError(String(e.message ?? e)));
  }, []);

  useEffect(() => {
    if (!apiMode()) return;
    v2.geo().then(setGeo, (e) => setError(String(e.message ?? e)));
    v2.timeline().then(setTimeline, () => undefined);
    load();
  }, [load]);

  // live: refresh every 6 s when looking at "now"
  useEffect(() => {
    const t = window.setInterval(() => {
      if (live.current && !playing) load();
    }, 6000);
    return () => window.clearInterval(t);
  }, [load, playing]);

  // the time-lapse
  useEffect(() => {
    if (!playing) return;
    let h = viewH !== null && viewH < nowH - 1 ? viewH : 0;
    live.current = false;
    const t = window.setInterval(() => {
      h = Math.min(nowH, h + 1);
      setSimHour(h);
      if (h % 3 === 0 || h >= nowH) {
        setViewH(h);
        load(h);
      }
      if (h >= nowH) {
        setPlaying(false);
        live.current = true;
        setViewH(null);
        setSimHour(null);
      }
    }, 260);
    return () => window.clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing]);

  const scrub = (h: number) => {
    setPlaying(false);
    setSimHour(h >= nowH - 0.5 ? null : h);
    if (h >= nowH - 0.5) {
      live.current = true;
      setViewH(null);
      load();
    } else {
      live.current = false;
      setViewH(h);
      load(h);
    }
  };

  const onTurn = async (r: TurnResult) => {
    live.current = true;
    setViewH(null);
    const s = await load();
    const hh = r.effects.household;
    if (hh?.zoneId) {
      setSelected(hh.zoneId);
      setTab("zone");
    }
    if (hh?.lon && hh.lat && (r.effects.located || r.effects.neighbour)) {
      setFocus({ lon: hh.lon, lat: hh.lat });
      const near = await v2.buildings(hh.lon, hh.lat, 60);
      const marks: HouseMark[] = [];
      const me = near.buildings.find((b) => b.id === hh.buildingId);
      if (me) marks.push({ outline: me.outline, kind: "me" });
      for (const n of r.session.neighbours) {
        const b = near.buildings.find((x) => x.id === n.buildingId);
        if (b) marks.push({ outline: b.outline, kind: n.result === "known" ? "known" : "new" });
      }
      setHouses(marks);
    }
    void s;
  };

  const act = async (a: "advance" | "morning" | "rain" | "river" | "flood" | "reset") => {
    await v2.clock(a);
    if (a === "reset") {
      setHouses([]);
      setFocus(null);
      setChatVersion((v) => v + 1);
    }
    live.current = true;
    setViewH(null);
    load();
  };

  if (!apiMode())
    return (
      <main className="v2-page">
        <p className="v2-card">This page needs the ReachPoint server. Open it with <code>?data=api</code> or use the deployed site.</p>
      </main>
    );

  const zone = selected && state ? state.zones[selected] : null;
  const o = state?.overall;
  const viewing = viewH ?? nowH;

  return (
    <main className="v2-page">
      <header className="v2-header">
        <div className="v2-brand">
          <b>ReachPoint</b>
          <span>Hat Yai flood, 21–28 Nov 2025 · real water data, synthetic people</span>
        </div>
        <div className="v2-clock">
          <span className="v2-clock-time">{state?.at ?? "…"}</span>
          {viewH !== null ? <span className="v2-chip is-amber">time-lapse</span> : <span className="v2-chip is-live">live</span>}
        </div>
        <nav className="v2-actions" aria-label="Demo clock">
          <button type="button" onClick={() => act("advance")}>+30 min</button>
          <button type="button" onClick={() => act("morning")}>Next 07:00</button>
          <button type="button" onClick={() => act("rain")}>Rain alert</button>
          <button type="button" onClick={() => act("river")}>River rising</button>
          <button type="button" onClick={() => act("flood")}>Flood the system</button>
          <button type="button" onClick={() => act("reset")}>Reset</button>
          <Link to="/v" className="v2-volunteer-link">Volunteer pages →</Link>
        </nav>
      </header>
      {error ? <p className="v2-error">Couldn't reach the server: {error}</p> : null}
      <div className="v2-layout">
        <Phone onTurn={onTurn} version={chatVersion} lang={lang} setLang={setLang} />
        <section className="v2-board" aria-label="Volunteer information board">
          {o ? (
            <div className="v2-stats">
              <div><b>{o.messages.toLocaleString()}</b><span>messages in · {Object.keys(o.channels).length} channels</span></div>
              <div><b>{o.households.toLocaleString()}</b><span>households · {o.duplicatesMerged} duplicates merged</span></div>
              <div><b>{o.people.toLocaleString()}</b><span>people reported · ≈ {(o.likelyFlooded / 1000).toFixed(0)}k likely flooded (estimate)</span></div>
              <div><b>{(o.certainty * 100).toFixed(0)}%</b><span>map certainty</span></div>
              <div><b>{o.status.lostContact}</b><span>lost contact · {o.status.safe + o.status.evacuated} safe or evacuated</span></div>
            </div>
          ) : null}
          <div className="v2-mapwrap">
            <BoardMap
              geo={geo}
              state={state}
              selected={selected}
              onSelect={(z) => { setSelected(z); setTab("zone"); }}
              houses={houses}
              focus={focus}
              lang={lang}
              simHour={simHour ?? viewing}
              simMode={simMode}
            />
            <div className="v2-simswitch" role="radiogroup" aria-label="Water layer">
              {([["corrected", "Simulation + reports"], ["physics", "Physics only"], ["off", "Zones"]] as [SimMode, string][]).map(([m, label]) => (
                <button key={m} type="button" role="radio" aria-checked={simMode === m} onClick={() => setSimMode(m)}>{label}</button>
              ))}
            </div>
            <div className="v2-map-legend" aria-hidden="true">
              <span><i className="is-unknown" />unknown</span>
              <span><i className="is-1" />&lt; 0.5 m</span>
              <span><i className="is-2" />0.5–1 m</span>
              <span><i className="is-3" />1–2 m</span>
              <span><i className="is-4" />&gt; 2 m</span>
              <span><i className="is-dot" />household</span>
            </div>
          </div>
          <TimeBar timeline={timeline} viewH={viewing} nowH={nowH} onChange={scrub} playing={playing} onPlay={() => setPlaying((p) => !p)} />
          <div className="v2-tabs" role="tablist">
            <button role="tab" aria-selected={tab === "zone"} onClick={() => setTab("zone")}>Zone {selected ?? ""}</button>
            <button role="tab" aria-selected={tab === "activity"} onClick={() => setTab("activity")}>AI activity</button>
          </div>
          {tab === "zone" ? <ZoneCard zone={zone} state={state} /> : <ActivityList items={state?.activity ?? []} />}
          {tab === "zone" && zone ? <p className="v2-more"><Link to={`/v/zone/${zone.id}`}>Open zone {zone.id}: every family, by priority →</Link></p> : null}
          <PlanBox onPosted={() => load()} />
        </section>
      </div>
    </main>
  );
}

function pickDeepest(s: BoardState): string | null {
  let best: [number, string] | null = null;
  for (const z of Object.values(s.zones)) {
    const d = z.level?.depthM ?? -1;
    if (!best || d > best[0]) best = [d, z.id];
  }
  return best?.[1] ?? null;
}
