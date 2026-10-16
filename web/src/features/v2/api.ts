/** v2 API (docs/product/v2-spec.md §8). Every call carries the demo room, so judges never see each other's reports. */
import { get, post } from "../../data/api";

export type Range = [number, number];

export interface Level {
  wseM: number;
  loM: number;
  hiM: number;
  depthM: number;
  depthLoM: number;
  depthHiM: number;
  trendCmH: number | null;
  n: number;
  doubtful: number;
  certainty: number;
}

export interface Source {
  kind: "victims" | "posts" | "satellite" | "gauge" | "terrain" | "simulation";
  text: string;
  labels?: { confirmed: number; unconfirmed: number; doubtful: number };
  lastH: number | null;
  flooded?: boolean;
  reconstructed?: boolean;
}

export interface Plan {
  id: string;
  team: string | null;
  vehicle: string | null;
  seats: number | null;
  eta: string | null;
  offers: string | null;
  at: string;
  told?: number;
  zones?: string[];
  text?: string;
}

export interface ZoneView {
  id: string;
  label: string;
  district: string | null;
  level: Level | null;
  people: {
    everyone: Range;
    likelyFlooded: Range | null;
    reported: Range;
    households: number;
    elderly: number;
    children: number;
    cannotWalk: number;
    urgent: number;
  };
  status: { open: number; safe: number; evacuated: number; lostContact: number };
  sources: Source[];
  plans: Plan[];
  gap: string | null;
  quiet: boolean;
  predicted: boolean;
  disagree: string | null;
  summary: string;
  simulation?: { wetShare: number; surfaceM: number | null; correctionM: number | null };
}

export interface HouseholdView {
  id: string;
  buildingId: string | null;
  zoneId: string | null;
  lon: number;
  lat: number;
  precision: string;
  people: number | null;
  elderly: number;
  children: number;
  cannotWalk: number;
  urgent: boolean;
  status: "open" | "safe" | "evacuated" | "lostContact";
  firstHand: boolean;
  reportedByOthersOnly: boolean;
  messages: number;
}

export interface Activity {
  atH: number;
  at: string;
  agent: string;
  text: string;
  tool: string;
  key?: string;
}

export interface BoardState {
  atH: number;
  at: string;
  now: { atH: number; at: string };
  overall: {
    messages: number;
    channels: Record<string, number>;
    households: number;
    duplicatesMerged: number;
    people: number;
    likelyFlooded: number;
    certainty: number;
    status: { open: number; safe: number; evacuated: number; lostContact: number };
    estimatedHouseholdsAffected: number;
  };
  zones: Record<string, ZoneView>;
  households: HouseholdView[];
  plans: Plan[];
  activity: Activity[];
  outbound: { total: number; byKind: Record<string, number> };
  bulletin: { atH: number; text: string; gaugeM: number; rateMh: number } | null;
}

export interface Timeline {
  start: string;
  hours: number;
  stops: { atH: number; at: string; caption: string }[];
  series: { atH: number; at: string; messages: number; households: number; people: number; certainty: number; gaugeM: number | null }[];
}

export interface Fact {
  field: string;
  value: unknown;
  quote: string;
}

export interface Session {
  id: string;
  token: string;
  lang: "th" | "en";
  householdId: string | null;
  pin: { lon: number; lat: number } | null;
  buildingId: string | null;
  zoneId: string | null;
  transcript: { role: "agent" | "person"; text: string; channel?: string }[];
  neighbours: { side: string; result: string; buildingId?: string }[];
  pending: string | null;
  finished: boolean;
}

export interface TurnResult {
  session: Session;
  reply: string;
  effects: {
    facts?: Fact[];
    reader?: string;
    located?: { by: string; label?: string; zoneId: string; buildingId: string };
    neighbour?: { side: string; known: boolean; householdId: string; buildingId: string; sure: boolean } | null;
    household?: HouseholdView | null;
    depthHere?: [number, number, number] | null;
    simHere?: number | null;
  };
  zone: ZoneView | null;
}

export interface Inbox {
  inbox: { atH: number; at: string; kind: string; text: string }[];
  now: { atH: number; at: string };
}

export interface GeoView {
  zones: GeoJSON.FeatureCollection;
  center: [number, number];
}

export const v2 = {
  geo: () => get<GeoView>("/api/v2/geo"),
  timeline: () => get<Timeline>("/api/v2/timeline"),
  state: (at?: number) => get<BoardState>(`/api/v2/state${at === undefined ? "" : `?at=${at}`}`),
  clock: (action: "advance" | "morning" | "rain" | "river" | "flood" | "reset") => post<{ now: { atH: number } }>("/api/v2/clock", { action }),
  newChat: (lang: "th" | "en") => post<Session>(`/api/v2/chat/sessions?lang=${lang}`, {}),
  turn: (id: string, text: string, channel: "chat" | "voice") => post<TurnResult>(`/api/v2/chat/sessions/${id}/turn`, { text, channel }),
  me: (token: string) => get<Inbox>(`/api/v2/me/${token}`),
  plan: (text: string) => post<{ plan: Plan; reader: string }>("/api/v2/plans", { text }),
  buildings: (lon: number, lat: number, r = 45) =>
    get<{ buildings: { id: string; outline: [number, number][]; groundM: number | null }[] }>(`/api/v2/buildings?lon=${lon}&lat=${lat}&r=${r}`),
};

export function depthBand(d: number | null | undefined): "unknown" | "0" | "1" | "2" | "3" | "4" {
  if (d === null || d === undefined) return "unknown";
  if (d < 0.1) return "0";
  if (d < 0.5) return "1";
  if (d < 1.0) return "2";
  if (d < 2.0) return "3";
  return "4";
}

export function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}
