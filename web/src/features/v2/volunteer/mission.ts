import { useEffect, useState } from "react";
import type { CaseRow } from "../api";

export const MISSION_KEY = "rp.v2.mission";
export interface Mission {
  zoneId: string;
  team: string;
  vehicle: string;
  seats: number;
  eta: string;
  told: number | null;
  at: string;
}

/** A blocked storage API still lets the team continue in this tab. */
let current: Mission | null = null;
let memoryOnly = false;
export function saveMission(mission: Mission): void {
  current = mission;
  try { localStorage.setItem(MISSION_KEY, JSON.stringify(mission)); memoryOnly = false; } catch { memoryOnly = true; }
  window.dispatchEvent(new Event("reachpoint-mission"));
}
export function loadMission(): Mission | null {
  if (memoryOnly) return current;
  let raw: string | null;
  try { raw = localStorage.getItem(MISSION_KEY); } catch { return current; }
  if (!raw) return null;
  try {
    const value = JSON.parse(raw) as Partial<Mission> | null;
    if (!value || ![value.zoneId, value.team, value.vehicle, value.eta, value.at].every(v => typeof v === "string")
      || !value.zoneId || typeof value.seats !== "number" || !Number.isFinite(value.seats) || value.seats < 0
      || !(value.told === null || typeof value.told === "number" && Number.isFinite(value.told) && value.told >= 0)) return null;
    return value as Mission;
  } catch { return null; }
}
export function useMission(): Mission | null {
  const [mission, setMission] = useState(loadMission);
  useEffect(() => {
    const sync = () => setMission(loadMission());
    window.addEventListener("reachpoint-mission", sync);
    window.addEventListener("storage", sync);
    return () => { window.removeEventListener("reachpoint-mission", sync); window.removeEventListener("storage", sync); };
  }, []);
  return mission;
}
export function isDone(row: CaseRow): boolean {
  return ["safe", "evacuated", "nobodyThere", "atShelter"].includes(row.status);
}
/** Server priority is the attention ranking; urgency and mobility break ties. Never mutates the live view. */
export function visitingOrder(rows: CaseRow[]): CaseRow[] {
  return [...rows].sort((a, b) => Number(isDone(a)) - Number(isDone(b)) || b.priority - a.priority
    || Number(b.urgent) - Number(a.urgent) || b.cannotWalk - a.cannotWalk || a.id.localeCompare(b.id));
}
export function directionsUrl(lat: number | null, lon: number | null): string | null {
  if (lat === null || lon === null || !Number.isFinite(lat) || !Number.isFinite(lon)
    || Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
  return `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}&travelmode=driving`;
}
