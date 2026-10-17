import { useMemo } from "react";
import { Link } from "react-router-dom";
import { BoardMap, type TripOverlay } from "../BoardMap";
import { v2, type CaseRow, type CopilotPlan, type GeoView, type Shelter } from "../api";
import { useLive } from "../volunteer/shared";
import { DepthRange, Panel } from "./Shared";
interface TripMapProps {
  plan: CopilotPlan;
  households: CaseRow[];
  shelters: Shelter[];
  geo: GeoView | null;
  atH: number;
}

type Point = {
  lon: number;
  lat: number;
};
export function TripMap({ plan, households, shelters, geo, atH }: TripMapProps) {
  const { data: board } = useLive(() => v2.state(), []);
  const stops = useMemo(() => plan.families.flatMap((family, index) => {
    const household = households.find(candidate => candidate.id === family.id);
    return household?.lon != null && household.lat != null
      ? [{ id: family.id, lon: household.lon, lat: household.lat, label: String(index + 1) }]
      : [];
  }), [plan, households]);
  const center = stops.length ? {
    lon: stops.reduce((total, stop) => total + stop.lon, 0) / stops.length,
    lat: stops.reduce((total, stop) => total + stop.lat, 0) / stops.length,
  } : null;
  const shelter = center ? [...shelters].sort((first, second) => distance(first, center) - distance(second, center))[0] : undefined;
  const launch = useMemo(() => shelter && geo ? nearestBoundaryPoint(geo, plan.zone, shelter) : null, [geo, plan.zone, shelter]);
  const overlay = useMemo<TripOverlay>(() => ({
    stops: [
      ...stops,
      ...(shelter ? [{ ...shelter, label: "□ Drop-off" }] : []),
      ...(launch ? [{ ...launch, id: "launch", label: "Launch · illustrative" }] : []),
    ],
    runs: plan.runs.map((run, index) => ({
      run: run.run,
      points: [
        ...(index === 0 ? (launch ? [launch] : []) : (shelter ? [shelter] : [])),
        ...run.households.flatMap(id => stops.filter(stop => stop.id === id)),
        ...(shelter ? [shelter] : []),
      ],
    })),
  }), [stops, plan.runs, shelter, launch]);
  const depths = plan.families.flatMap(family => family.depthM == null ? [] : [family.depthM]);
  return (<Panel title={<>
    {plan.zone} · เส้นทางช่วยเหลือ
    <span className="rp-gloss">Trip on the map</span>
  </>} className="rp-trip-map">
    {stops.length ? (<div className="rp-trip-satellite">
      <BoardMap geo={geo} state={board} selected={plan.zone} onSelect={() => undefined} houses={[]} focus={null} lang="en" simHour={atH} simMode="physics" showPlans tripOverlay={overlay} />
    </div>) : <p className="rp-pad">Household positions have not been provided. No route is drawn.</p>}
    <div className="rp-pad rp-stack">
      <DepthRange value={plan.depthM} lo={depths.length ? Math.min(...depths) : undefined} hi={depths.length ? Math.max(...depths) : undefined} source="depth at planned households" />
      <p>Run 1 solid · later runs dashed · numbered stops · □ candidate shelter</p>
      {shelter ? <p>
        <b>{shelter.nameEn ?? "Candidate shelter"}</b>
        <br />Nearest to these stops by straight-line distance. Confirm shelter and access before departure.
      </p>
        : <p>No shelter provided. Confirm drop-off before departure.</p>}
      <p>{launch ? "Launch · illustrative: nearest point on this zone’s boundary to the shelter." : "Launch unknown: boundary or shelter unavailable."} Access unverified.</p>
      {plan.runs.map(run => <SeatRun key={run.run} run={run} seats={plan.seats} />)}
      {stops.length < plan.families.length && <p className="rp-warning">Some household positions are unavailable; their stops cannot be drawn.</p>}
      <p className="rp-honesty">Illustrative connections, not navigable directions. Water: recorded physics model at demo time; household depths are reported separately.</p>
      {plan.families.map((family, index) => <Link key={family.id} to={`/v/case/${family.id}`}>{index + 1}. {family.id} · {family.people} people →</Link>)}
    </div>
  </Panel>);
}

function SeatRun({ run, seats }: {
  run: CopilotPlan["runs"][number];
  seats: number;
}) {
  return (<div>
    <b>Run {run.run} · {run.people} of {seats} seats</b>
    <div className="rp-seats" aria-label={`${run.people} passengers, ${seats} seats`}>
      {Array.from({ length: Math.min(100, Math.max(0, seats)) }, (_, index) => <span key={index} className={index < run.people ? "rp-filled" : ""}>●</span>)}
    </div>
    {run.people > seats && <p className="rp-warning">Over capacity. Revise before posting.</p>}
  </div>);
}

function distance(first: Point, second: Point) {
  return ((first.lon - second.lon) * Math.cos(second.lat * Math.PI / 180)) ** 2 + (first.lat - second.lat) ** 2;
}
/** Project onto every boundary segment, rather than picking a corner of the map. */
export function nearestBoundaryPoint(geo: GeoView, zoneId: string, shelter: Point): Point | null {
  const feature = geo.zones.features.find(candidate => candidate.properties?.id === zoneId);
  if (!feature || !["Polygon", "MultiPolygon"].includes(feature.geometry.type))
    return null;
  const geometry = feature.geometry as GeoJSON.Polygon | GeoJSON.MultiPolygon;
  const rings = geometry.type === "Polygon" ? geometry.coordinates : geometry.coordinates.flat();
  const longitudeScale = Math.cos(shelter.lat * Math.PI / 180);
  let nearest: Point | null = null;
  let nearestDistance = Infinity;
  for (const ring of rings) {
    for (let index = 0;index < ring.length - 1;index++) {
      const start = ring[index];
      const end = ring[index + 1];
      const deltaX = (end[0] - start[0]) * longitudeScale;
      const deltaY = end[1] - start[1];
      const lengthSquared = deltaX ** 2 + deltaY ** 2;
      const fraction = lengthSquared === 0 ? 0 : Math.max(0, Math.min(1, ((shelter.lon - start[0]) * longitudeScale * deltaX + (shelter.lat - start[1]) * deltaY) / lengthSquared));
      const candidate = { lon: start[0] + (end[0] - start[0]) * fraction, lat: start[1] + deltaY * fraction };
      const candidateDistance = distance(candidate, shelter);
      if (candidateDistance < nearestDistance) {
        nearestDistance = candidateDistance;
        nearest = candidate;
      }
    }
  }
  return nearest;
}
