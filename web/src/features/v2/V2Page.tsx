/** The reporting loop: the family's phone, evidence from each turn, and the water at her house. */
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { BoardMap, type HouseMark, type SimMode } from "./BoardMap";
import { Phone } from "./Phone";
import { v2, type BoardState, type GeoView, type HouseholdView, type TurnResult, type SimResult, type FamilyStatus } from "./api";
import { DepthRange, HonestyLabel, Panel, StepHeader, type ClockAction, TraceLine } from "./ui/Shared";
import { buildFollowUpTrace, buildReportTrace } from "./ui/reportTrace";
import type { TraceEntry } from "./ui/trace";
import "./v2.css";

export function V2Page() {
  const [geo, setGeo] = useState<GeoView | null>(null);
  const [board, setBoard] = useState<BoardState | null>(null);
  const [household, setHousehold] = useState<HouseholdView | null>(null);
  const [houses, setHouses] = useState<HouseMark[]>([]);
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
    const added = buildReportTrace(turn, ++turnIndex.current, at, atH, previousStatus.current, pendingVisit.current);
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

  const focus = household ? { lon: household.lon, lat: household.lat } : null;
  return (
    <div className="rp-app">
      <StepHeader at={board?.at} onAction={act} />
      <main className="rp-main">
        <div className="rp-section-head">
          <div>
            <h1>One message. A family on the map.</h1>
            <p>Be a synthetic family. Follow her words through the AI’s decisions.</p>
          </div>
          <HonestyLabel />
        </div>
        {error && <p role="alert" className="rp-warning">{error}</p>}
        <div className="rp-report-layout">
          <Phone onSimulation={onSimulation} onTurn={onTurn} version={chatVersion} lang={lang} setLang={setLang} />
          <Panel title="What the AI is doing for this family">
            <div aria-live="polite">
              {trace.length ? trace.map(line => <TraceLine key={line.id} {...line} />) : (
                <div className="rp-pad rp-stack">
                  <h3>Her words become evidence.</h3>
                  <p>Send the message to watch Gemini read, rules locate, and physics correct the map.</p>
                </div>
              )}
            </div>
          </Panel>
          <aside className="rp-stack">
            <div className="rp-report-map">
              <BoardMap geo={geo} state={board} selected={household?.zoneId ?? null} onSelect={() => undefined}
                houses={houses} focus={focus} focusedHousehold={household} lang="en"
                simHour={board?.atH ?? 96} simMode={simMode} />
            </div>
            <div className="rp-toggle" role="group" aria-label="Water layer">
              <button aria-pressed={simMode === "physics"} onClick={() => setSimMode("physics")}>Model only</button>
              <button aria-pressed={simMode === "corrected"} onClick={() => setSimMode("corrected")}>Model + reports</button>
            </div>
            <Panel title={household ? `Her house · ${household.id}` : "Her house · awaiting location"}>
              <div className="rp-pad rp-stack">
                <DepthRange value={modelDepth} source="model only · before correction" at={depthUpdatedAt} />
                <span>↓ Reports correct the estimate</span>
                <DepthRange value={correctedDepth?.[0] ?? null} lo={correctedDepth?.[1]} hi={correctedDepth?.[2]}
                  source="model + reports" at={depthUpdatedAt} />
                <p>Switch between the model and the model with reports. Depth is an estimate; unknown is not dry.</p>
              </div>
            </Panel>
            {confirmed && household?.zoneId && <Link className="rp-button rp-primary" to={`/v/zone/${household.zoneId}`}>See her on the volunteer page →</Link>}
          </aside>
        </div>
      </main>
    </div>
  );
}
