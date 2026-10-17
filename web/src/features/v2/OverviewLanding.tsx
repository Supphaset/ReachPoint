import { useUiLang } from "./ui/lang";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { BoardMap } from "./BoardMap";
import { v2, vol, type BoardState, type Feed, type GeoView, type Overview, type Timeline } from "./api";
import { HonestyLabel, Panel, StepHeader, TraceLine, type ClockAction } from "./ui/Shared";
import { buildTraceLines } from "./ui/trace";
import { latestRequest, playFlood } from "./ui/replay";
import { useTween } from "./ui/useTween";
import "./v2.css";
let visited = false;
export function OverviewLanding() {
  const { lang } = useUiLang();
  const navigate = useNavigate();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [board, setBoard] = useState<BoardState | null>(null);
  const [feed, setFeed] = useState<Feed | null>(null);
  const [geo, setGeo] = useState<GeoView | null>(null);
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [hour, setHour] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);
  const [replayed, setReplayed] = useState(visited);
  const [error, setError] = useState("");
  const cancel = useRef<(() => void) | null>(null);
  const replayLoader = useRef(latestRequest<BoardState>(setBoard, failure => setError(String(failure))));
  const historicalView = useRef(false);
  const currentBoard = useRef<BoardState | null>(null);
  // Keep a current snapshot ready so Skip and completion do not wait for the API.
  const refresh = useCallback(async () => {
    try {
      const [overviewData, snapshot, recentFeed] = await Promise.all([vol.overview(), v2.state(), vol.feed(undefined, undefined, 20)]);
      currentBoard.current = snapshot;
      setOverview(overviewData);
      setFeed(recentFeed);
      if (!historicalView.current)
        setBoard(snapshot);
      setError("");
    }
    catch (failure) {
      setError(String(failure));
    }
  }, []);
  useEffect(() => {
    void refresh();
    v2.geo().then(setGeo, failure => setError(String(failure)));
    v2.timeline().then(setTimeline, failure => setError(String(failure)));
    const timer = window.setInterval(refresh, 5000);
    return () => {
      window.clearInterval(timer);
      cancel.current?.();
      replayLoader.current.invalidate();
    };
  }, [refresh]);
  const finish = useCallback(() => {
    cancel.current?.();
    historicalView.current = false;
    setPlaying(false);
    setHour(null);
    if (currentBoard.current) setBoard(currentBoard.current);
    replayLoader.current.invalidate();
    void refresh();
  }, [refresh]);
  const start = useCallback(() => {
    if (!overview || !timeline)
      return;
    visited = true;
    setReplayed(true);
    cancel.current?.();
    historicalView.current = true;
    setPlaying(true);
    replayLoader.current.invalidate();
    // Fixed wall-time steps launch independent reads; only the latest response is accepted.
    cancel.current = playFlood(0, overview.atH, 20000, targetHour => {
      setHour(targetHour);
      replayLoader.current.load(() => v2.state(Math.floor(targetHour)));
    }, finish);
  }, [overview, timeline, finish]);
  const startRef = useRef(start);
  startRef.current = start;
  useEffect(() => {
    if (!overview || !timeline || visited || window.matchMedia('(prefers-reduced-motion: reduce)').matches)
      return;
    const timer = window.setTimeout(() => startRef.current(), 1500);
    return () => window.clearTimeout(timer);
  }, [!!overview, !!timeline]);
  async function action(clockAction: ClockAction) {
    finish();
    await v2.clock(clockAction);
    await refresh();
  }
  const overall = overview?.overall;
  const at = hour ?? overview?.atH ?? 0;
  const sample = timeline?.series.reduce((previous, point) => point.atH <= at ? point : previous, timeline.series[0]);
  const messages = useTween(hour === null ? overall?.messages : sample?.messages);
  const families = useTween(hour === null ? overall?.households : sample?.households);
  const gaps = overview?.zones.filter(zone => zone.open > 0 && !zone.plans).sort((first, second) => second.score - first.score) ?? [];
  const urgent = useTween(hour === null ? overview?.points.filter(point => point.urgent).length : board?.households.filter(point => point.urgent).length);
  const lines = buildTraceLines(feed?.items ?? [], board?.activity ?? [], at).slice(0, 6);
  return <div className="rp-app">
    <StepHeader at={board?.at ?? overview?.at} onAction={action} />
    <main className="rp-main">
      {lang === "th" && <p className="rp-language-hint">Prefer English? Tap EN (top right)</p>}
      <section className="rp-hero">
        <div>
          <HonestyLabel />
          <h1>In the Hat Yai flood, {fmt(messages)} messages came in. Gemini turned them into {fmt(families)} families on a map.</h1>
          <p>So volunteers can see where help is missing. Every fact keeps the sender’s own words.</p>
        </div>
        <div className="rp-hero-actions">
          <Doors />
          <button onClick={playing ? finish : start} disabled={!timeline || !overview}>{playing ? "Skip to the picture →" : replayed ? "↻ Replay again" : "▶ Play the flood week · 20 s"}</button>
        </div>
      </section>
      {error && <p role="alert" className="rp-warning">Couldn't reach the server:
        {error}
        <button onClick={refresh}>Retry</button>
      </p>}
      <div className="rp-overview-grid">
        <div>
          <OverviewFunnel messages={messages} families={families} urgent={urgent} overview={overview} board={board} hour={hour} gaps={gaps} />
          <div className="rp-map-hero">
            <BoardMap showPlans={false} geo={geo} state={board} selected={null} onSelect={zone => navigate(`/v/zone/${zone}`)} houses={[]} focus={null} lang="en" simHour={at} simMode="corrected" />
            <div className="rp-scrub">
              <time>{board?.at ?? "21 Nov 06:00"}</time>
              <input type="range" min="0" max={overview?.atH ?? 96} step="1" value={at} aria-label="Flood replay time" onChange={event => {
                cancel.current?.();
                historicalView.current = true;
                setPlaying(false);
                visited = true;
                setReplayed(true);
                const targetHour = Number(event.target.value);
                setHour(targetHour);
                replayLoader.current.load(() => v2.state(Math.floor(targetHour)));
              }} />
              <button onClick={playing ? finish : hour !== null ? finish : start}>{playing ? "Skip" : hour !== null ? "Back to demo time" : "Replay"}</button>
            </div>
          </div>
          <div className="rp-map-caption">Water: flood model (terrain, rain and river gauge), corrected by reports ·
            {board?.at}
            <br />● urgent · ● waiting · □ candidate shelter · dashed zones: families, no team. Depth: 0 → &gt;2 m. Unknown is not dry.
          </div>
          <CoverageGaps gaps={gaps} />
        </div>
        <aside className="rp-stack">
          <Panel title={<>
            <span>What the AI is doing</span>
            <Link to="/v/feed">Every decision →</Link>
          </>}>
            <div className="rp-trace-list">
              {lines.length ? lines.map(line => <TraceLine key={line.id} {...line} />) : <p className="rp-pad">Waiting for recorded evidence at this replay time.</p>}
            </div>
            <p className="rp-map-caption">Recent reads and model activity · refreshed every 5 s</p>
          </Panel>

        </aside>
      </div>
    </main>
  </div>;
}

function Doors() {
  return <div className="rp-doors">
    <Link className="rp-door rp-primary" to="/report">
      <b>Report as a family →</b>
      <small>English or Thai · no microphone needed</small>
    </Link>
    <Link className="rp-door" to="/v">
      <b>See where help is missing →</b>
      <small>Where first, with evidence</small>
    </Link>
  </div>;
}

interface FunnelProps {
  messages: number | undefined;
  families: number | undefined;
  urgent: number | undefined;
  overview: Overview | null;
  board: BoardState | null;
  hour: number | null;
  gaps: Overview["zones"];
}

function OverviewFunnel({ messages, families, urgent, overview, board, hour, gaps }: FunnelProps) {
  const overall = overview?.overall;
  return <div className="rp-funnel">
    <div title="overall.messages">
      <b>{fmt(messages)}</b>
      <span>messages read</span>
      <small>{overall ? Object.keys(overall.channels).length : "…"} channels</small>
    </div>
    <div title="overall.households">
      <b>{fmt(families)}</b>
      <span>families</span>
      <small>{fmt(overall?.duplicatesMerged)} duplicates merged</small>
    </div>
    <div className="rp-urgent" title="points.filter(urgent).length">
      <b>{fmt(urgent)}</b>
      <span>urgent</span>
      <small>reported in this replay</small>
    </div>
    <div title="zones with open > 0 and plans == 0">
      <b>
        {hour === null ? gaps.length : Object.values(board?.zones ?? {}).filter(zone => zone.status.open + zone.status.lostContact > 0 && !zone.plans.length).length}
        <small> / {overview?.zones.length ?? "…"}</small>
      </b>
      <span>zones with families, no team</span>
    </div>
  </div>;
}

function CoverageGaps({ gaps }: {
  gaps: Overview["zones"];
}) {
  return <Panel title="Where help is missing">
    {gaps.slice(0, 3).map((zone, index) => <Link className="rp-gap" key={zone.id} to={`/v/zone/${zone.id}`}>
      <span className="rp-rank">0{index + 1}</span>
      <div>
        <strong>
          {zone.id}
          {zone.label ? ` · ${zone.label}` : ""}
          <span className="rp-gloss">Zone with uncovered needs</span>
        </strong>
        <p>{zone.open} families waiting · {zone.urgent} urgent · no team planned</p>
        {zone.cannotWalk > 0 && <small>{zone.cannotWalk} cannot walk</small>}
      </div>
      <span>→</span>
    </Link>)}
  </Panel>;
}

function fmt(value: number | undefined) {
  return value === undefined ? "…" : value.toLocaleString("en-US");
}
