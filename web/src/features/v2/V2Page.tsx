/** The reporting loop: the family's phone, evidence from each turn, and the water at her house. */
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { BoardMap, type HouseMark, type SimMode } from "./BoardMap";
import { Phone } from "./Phone";
import { v2, type BoardState, type GeoView, type HouseholdView, type TurnResult, type SimResult, type FamilyStatus } from "./api";
import { HonestyLabel, Panel, StepHeader, type ClockAction } from "./ui/Shared";
import { DepthBars } from "./ui/DepthBars";
import { TraceTimeline } from "./ui/TraceTimeline";
import { buildFollowUpTrace, buildReportTrace } from "./ui/reportTrace";
import { displayText } from "./ui/trace";
import type { TraceEntry } from "./ui/trace";
import "./v2.css";

export function V2Page() {
  const [tab, setTab] = useState("chat");
  const [toast, setToast] = useState<TraceEntry | null>(null);
  const [geo, setGeo] = useState<GeoView | null>(null);
  const [board, setBoard] = useState<BoardState | null>(null);
  const [household, setHousehold] = useState<HouseholdView | null>(null);
  const [houses, setHouses] = useState<HouseMark[]>([]);
  const [activeTurn, setActiveTurn] = useState<number | null>(null);
  const [trace, setTrace] = useState<TraceEntry[]>([]);
  const [lang, setLang] = useState<"th" | "en">("th");
  const [chatVersion, setChatVersion] = useState(0);
  const [simMode, setSimMode] = useState<SimMode>("corrected");
  const [modelDepth, setModelDepth] = useState<number | null>(null);
  const [correctedDepth, setCorrectedDepth] = useState<[number, number, number] | null>(null);
  const [depthUpdatedAt, setDepthUpdatedAt] = useState<string | undefined>();
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  const generation = useRef(0);
  const turnIndex = useRef(0);
  const pendingVisit = useRef(false);
  const previousStatus = useRef<FamilyStatus | null>(null);

  const refresh = useCallback(async () => {
    const version = generation.current;
    try {
      const snapshot = await v2.state();
      if (version === generation.current) {
        setBoard(snapshot);
        setError("");
      }
    } catch (failure) {
      if (version === generation.current) setError(String(failure));
    }
  }, []);

  useEffect(() => {
    v2.geo().then(setGeo, failure => setError(String(failure)));
    void refresh();
    const timer = window.setInterval(refresh, 6000);
    return () => {
      window.clearInterval(timer);
      generation.current++;
    };
  }, [refresh]);

  function onTurn(turn: TurnResult) {
    const at = board?.at ?? "Demo time";
    const atH = board?.atH ?? 0;
    const index = ++turnIndex.current;
    const added = buildReportTrace(turn, index, at, atH, previousStatus.current, pendingVisit.current);
    pendingVisit.current = false;
    setTrace(lines => [...lines, ...added]);
    previousStatus.current = turn.status ?? null;
    const reportedHousehold = turn.effects.household;
    if (reportedHousehold) setHousehold(reportedHousehold);
    if (turn.effects.simHere != null) setModelDepth(turn.effects.simHere);
    if (turn.effects.depthHere) setCorrectedDepth(turn.effects.depthHere);
    if (turn.effects.depthHere || turn.effects.simHere != null) setDepthUpdatedAt(at);
    if (turn.effects.neighbour?.sure) setConfirmed(true);
    void refresh();

    // Keep the satellite confirmation in the phone; outline these buildings on the map too.
    if (reportedHousehold && (turn.effects.located || turn.effects.neighbour)) {
      const version = generation.current;
      v2.buildings(reportedHousehold.lon, reportedHousehold.lat, 60).then(nearby => {
        if (version !== generation.current) return;
        const marks: HouseMark[] = [];
        const ownBuilding = nearby.buildings.find(building => building.id === reportedHousehold.buildingId);
        if (ownBuilding) marks.push({ outline: ownBuilding.outline, kind: "me" });
        for (const neighbour of turn.session.neighbours) {
          const building = nearby.buildings.find(candidate => candidate.id === neighbour.buildingId);
          if (building) marks.push({ outline: building.outline, kind: neighbour.result === "known" ? "known" : "new" });
        }
        setHouses(marks);
      }, failure => setError(String(failure)));
    }
    return index;
  }

  function onSimulation(result: SimResult) {
    previousStatus.current = result.status;
    if (result.event === "teamVisit") pendingVisit.current = true;
    const added = buildFollowUpTrace(result, ++turnIndex.current, board?.at ?? "Demo time", board?.atH ?? 0);
    setTrace(lines => [...lines, ...added]);
    void refresh();
  }

  async function act(action: ClockAction) {
    await v2.clock(action);
    generation.current++;
    if (action === "reset") {
      previousStatus.current = null;
      pendingVisit.current = false;
      setHousehold(null);
      setHouses([]);
      setTrace([]);
      setModelDepth(null);
      setCorrectedDepth(null);
      setDepthUpdatedAt(undefined);
      setConfirmed(false);
      setChatVersion(version => version + 1);
    }
    await refresh();
  }

  const latest = trace[trace.length - 1];
  useEffect(() => {
    setToast(latest ?? null);
    if (!latest) return;
    const timer = window.setTimeout(() => setToast(null), 6000);
    return () => window.clearTimeout(timer);
  }, [latest]);

  const focus = household ? { lon: household.lon, lat: household.lat } : null;
  return (
    <div className="rp-app rp-report-app">
      <StepHeader at={board?.at} showDemo={false} />
      <main className="rp-main">
        <div className="rp-section-head">
          <div>
            <h1>ข้อความเดียว ครอบครัวปรากฏบนแผนที่</h1>
            <p>One message. A family on the map. · Synthetic demo family</p>
          </div>
          <HonestyLabel />
        </div>
        {error && <p role="alert" className="rp-warning">{error}</p>}
        <ReportTabs tab={tab} onChange={setTab} />
        {toast && <button className="rp-ai-toast" onClick={() => setTab("ai")}><b>{toast.who === "gemini" ? "Gemini" : toast.who === "physics" ? "แบบจำลอง · Physics" : "กติกา · Rules"}</b> · {displayText(toast.what)}</button>}
        <div className="rp-report-layout" data-tab={tab}>
          <section className="rp-report-phone">
            <h2 className="rp-column-heading"><span>①</span> แชทครอบครัว <small>Her phone</small></h2>
            <div className="rp-phone-stage">
              <Phone at={board?.at} onClock={act} activeTurn={activeTurn} onActiveTurn={setActiveTurn}
                onSimulation={onSimulation} onTurn={onTurn} version={chatVersion} lang={lang} setLang={setLang} />
            </div>
          </section>
          <section className="rp-report-trace">
            <h2 className="rp-column-heading"><span>②</span> การทำงานของ AI <small>For this family</small></h2>
            <Panel title="หลักฐานและการตัดสินใจ · Evidence & decisions">
              <TraceTimeline lines={trace} activeTurn={activeTurn} onActiveTurn={setActiveTurn} />
            </Panel>
          </section>
          <aside className="rp-stack rp-report-aside">
            <h2 className="rp-column-heading"><span>③</span> แผนที่เรียนรู้ <small>Her house</small></h2>
            <div className="card rp-map-card">
            <div className="rp-report-map">
              <BoardMap geo={geo} state={board} selected={household?.zoneId ?? null} onSelect={() => undefined}
                houses={houses} focus={focus} focusZoom={16} maxZoom={18} focusedHousehold={household} lang="en"
                simHour={board?.atH ?? 96} simMode={simMode} />
            </div>
            <div className="seg" role="group" aria-label="Water layer">
              <button aria-pressed={simMode === "physics"} onClick={() => setSimMode("physics")}>แบบจำลอง<small>Model only</small></button>
              <button aria-pressed={simMode === "corrected"} onClick={() => setSimMode("corrected")}>+ รายงาน<small>Model + reports</small></button>
            </div>
            <DepthBars model={modelDepth} corrected={correctedDepth} at={depthUpdatedAt} />
            </div>
            {confirmed && household?.zoneId && <Link className="rp-button rp-primary" to={`/v/zone/${household.zoneId}`}>ดูครอบครัวในหน้าอาสา · See her on the volunteer page →</Link>}
          </aside>
        </div>
      </main>
    </div>
  );
}


export function ReportTabs({ tab, onChange }: { tab: string; onChange: (tab: string) => void }) {
  return <nav className="rp-phone-tabs seg" aria-label="มุมมอง · Report view">
    {[["chat", "แชท", "Chat"], ["ai", "AI", "Decisions"], ["map", "แผนที่", "Map"]].map(([id, th, en]) =>
      <button key={id} aria-pressed={tab === id} onClick={() => onChange(id)}>{th}<small>{en}</small></button>)}
  </nav>;
}
