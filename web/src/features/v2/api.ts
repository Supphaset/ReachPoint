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
  labels?: { consistent: number; unchecked: number; doubtful: number };
  lastH: number | null;
  flooded?: boolean;
  reconstructed?: boolean;
}

export interface Plan {
  order?: string[];
  checkStreets?: string[];
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

/** Both forms stay on the wire; UI selection never changes source quotes. */
export interface PlaceNames {
  name?: string | null;
  nameEn?: string | null;
  labelEn?: string | null;
  districtEn?: string | null;
  sectorNameEn?: string | null;
}

export interface UnheardStreet {
  name: string; nameEn: string; floodedBuildings: number; depthM: number; lon: number; lat: number;
}
export interface Unheard {
  floodedBuildings?: number;
  estimatedHouseholds: Range | null; heardFrom: number; notHeard: Range | null;
  quiet: boolean; streets: UnheardStreet[]; atH: number; basis: string;
}

export interface ZoneView extends PlaceNames {
  unheard?: Unheard;
  sector?: string | null;
  sectorName?: string | null;
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
    status: { open: number; safe: number; evacuated: number; lostContact: number; atShelter?: number; toShelter?: number };
    estimatedHouseholdsAffected: number;
  };
  zones: Record<string, ZoneView>;
  households: HouseholdView[];
  plans: Plan[];
  activity: Activity[];
  outbound: { total: number; byKind: Record<string, number> };
  bulletin: { atH: number; text: string; gaugeM: number; rateMh: number } | null;
  shelters?: Shelter[];
}

export interface Shelter {
  id: string;
  name: string;
  nameEn: string | null;
  kind: string;
  lon: number;
  lat: number;
  capacity: number;
  households: number;
  people: number;
  coming: number;
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

export interface Incoming { kind: "safetyCheck" | "lostContact"; at: string; reason: string }

export interface Session {
  incoming?: Incoming | null;
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

export interface LocationPin {
  lon: number;
  lat: number;
  method: "gps" | "map";
  accuracyM?: number;
}

export interface ShelterRoute {
  shelterId: string;
  name: string;
  nameEn?: string | null;
  kind: string;
  lon: number;
  lat: number;
  km: number;
  minutes: number;
  deepestM: number;
  walkable: boolean;
  by: "streets" | "direct line";
  path: [number, number][];
  samples: [number, number, number][];
  deepestAt: [number, number];
  from: [number, number];
  googleMaps: string;
}

export interface Choice { label: string; send: string }
export interface FamilyStatus {
  incoming?: Incoming | null;
  householdId: string | null;
  zoneId: string | null;
  status: string;
  urgent: boolean;
  wantsOut: boolean;
  people: number | null;
  water: { nowM: number; loM: number; hiM: number; in6hM: number; trend: "rising" | "falling" | "steady"; reports: number } | null;
  team: { team: string; vehicle: string; seats: number; eta: string; at: string } | null;
  outcome: { kind: string; team: string; at: string } | null;
  shelter: { name: string; nameEn?: string | null; km: number; deepestM: number; walkable: boolean; minutes: number } | null;
  nextCheck: string;
  now: string;
  /** The family already asked for a team; a second ask gets "we already have your request". */
  rideRequested?: boolean;
  /** Ticked get-ready items (indexes), kept on the server. */
  ready?: number[];
  readyTotal?: number;
}
export type SimEvent = "rain" | "river" | "teamPlan" | "teamVisit" | "checkin" | "safetyCall";
export interface SimResult {
  event: SimEvent;
  incoming?: Incoming;
  message?: { text: string; kind: string; choices: [string, string][] };
  inbox?: boolean;
  status: FamilyStatus;
}

export interface TurnResult {
  session: Session;
  reply: string;
  status?: FamilyStatus;
  effects: {
    choices?: { kind: string; options: Choice[] };
    checklist?: [string, string][];
    facts?: Fact[];
    reader?: string;
    located?: { by: string; label?: string; labelEn?: string; zoneId: string; buildingId: string; lon?: number; lat?: number; precision?: string };
    askLocation?: boolean;
    /** The pin missed: "noHouse" (inside our zones, no building under it) or "outside" (beyond what we cover). */
    pinOutside?: { reason: "noHouse" | "outside" } | boolean;
    shelterRoute?: ShelterRoute;
    neighbour?: { side: string; known: boolean; householdId: string; buildingId: string; sure: boolean } | null;
    nbConfirm?: NbConfirm;
    shelter?: { name: string; km: number; deepestM: number; walkable: boolean; going: boolean; minutes: number };
    household?: HouseholdView | null;
    depthHere?: [number, number, number] | null;
    simHere?: number | null;
  };
  zone: ZoneView | null;
}

export interface NbConfirm {
  side: string;
  quote: string;
  candidate: { id: string; outline: [number, number][]; lon: number; lat: number };
  me: { id: string; outline: [number, number][]; lon: number; lat: number } | null;
  n: number;
  of: number;
}

export interface Inbox {
  incoming?: Incoming | null;
  inbox: { atH: number; at: string; kind: string; text: string; choices?: Choice[] }[];
  now: { atH: number; at: string };
}

export interface GeoView {
  zones: GeoJSON.FeatureCollection;
  sectors?: GeoJSON.FeatureCollection;
  center: [number, number];
}

export const v2 = {
  geo: () => get<GeoView>("/api/v2/geo"),
  timeline: () => get<Timeline>("/api/v2/timeline"),
  state: (at?: number) => get<BoardState>(`/api/v2/state${at === undefined ? "" : `?at=${at}`}`),
  clock: (action: "advance" | "morning" | "rain" | "river" | "flood" | "reset") => post<{ now: { atH: number } }>("/api/v2/clock", { action }),
  newChat: (lang: "th" | "en") => post<Session>(`/api/v2/chat/sessions?lang=${lang}`, {}),
  turn: (id: string, text: string, channel: "chat" | "voice", pin?: LocationPin, replyTo?: string) => post<TurnResult>(`/api/v2/chat/sessions/${id}/turn`, { text, channel, ...(pin ? { pin } : {}), ...(replyTo ? { replyTo } : {}) }),
  incoming: (id: string, action: "answer" | "decline") => post<{ incoming: null; kind: Incoming["kind"] }>(`/api/v2/chat/sessions/${id}/incoming`, { action }),
  status: (id: string) => get<FamilyStatus>(`/api/v2/chat/sessions/${id}/status`),
  simulate: (id: string, event: SimEvent) => post<SimResult>(`/api/v2/chat/sessions/${id}/simulate`, { event }),
  ready: (id: string, done: number[]) => post<FamilyStatus>(`/api/v2/chat/sessions/${id}/ready`, { done }),
  me: (token: string) => get<Inbox>(`/api/v2/me/${token}`),
  plan: (text: string, team?: string, options?: { zone: string; order?: string[]; checkStreets?: string[] }) => post<{ plan: Plan; reader: string }>("/api/v2/plans", { text, ...(team ? { team } : {}), ...options }),
  buildings: (lon: number, lat: number, r = 45) =>
    get<{ buildings: { id: string; outline: [number, number][]; groundM: number | null }[] }>(`/api/v2/buildings?lon=${lon}&lat=${lat}&r=${r}`),
};

// --- volunteer pages (docs/product/v2-volunteer-pages.md) ---
const q = (team?: string | null) => (team ? `team=${encodeURIComponent(team)}` : "");

export interface CaseRow {
  id: string;
  zoneId: string | null;
  lon: number | null;
  lat: number | null;
  people: number | null;
  elderly: number;
  children: number;
  cannotWalk: number;
  urgent: boolean;
  status: "open" | "safe" | "evacuated" | "lostContact" | "nobodyThere" | "atShelter" | "toShelter";
  shelterId?: string | null;
  needs: string[];
  depth: { m: number; lo: number; hi: number; reports: number } | null;
  boat: boolean;
  priority: number;
  messages: number;
  lastHeard: string;
  hoursSilent: number;
  firstHand: boolean;
  possibleDuplicateOf: string | null;
  outcome: { kind: "pickedUp" | "nobodyThere"; team: string; at: string } | null;
  reportedBy: string;
}

export type UrgentCase = CaseRow & { markedFirst: { team: string; at: string } | null };
export interface UrgentZone extends PlaceNames {
  id: string;
  label: string | null;
  sector: string | null;
  plans: number;
  depthM: number | null;
  score: number;
  cases: UrgentCase[];
}
export interface UrgentView { atH: number; at: string; total: number; zones: UrgentZone[] }

export interface OverviewZone extends PlaceNames {
  id: string;
  label: string | null;
  sector: string | null;
  sectorName: string | null;
  district: string | null;
  score: number;
  open: number;
  urgent: number;
  lostContact: number;
  cannotWalk: number;
  elderly: number;
  boat: number;
  depthM: number | null;
  likelyFlooded: Range | null;
  heard: number;
  plans: number;
  nextPlan: Plan | null;
  gap: string | null;
  quiet: boolean;
  predicted: boolean;
  closed: number;
  /** The model's change at the zone's houses: last 3 hours and next 6 (null outside the model). */
  water: WaterTrend | null;
}

export interface WaterTrend { past3hM: number | null; next6hM: number; trend: "rising" | "falling" | "steady" }

/** Basin rain: last 6 h observed; next 6 h is, in the replay, the rain that really fell next (no archived forecast). */
export interface RainOutlook { past6hMm: number | null; next6hMm: number | null; heavy: boolean; source: string; kind: string }

export interface Overview {
  atH: number;
  at: string;
  overall: BoardState["overall"];
  zones: OverviewZone[];
  points: CaseRow[];
  shelters: Shelter[];
  hotspots: SubArea[];
  sectors: { id: string; name: string | null; nameEn?: string | null; zones: number; open: number; urgent: number; noTeam: number; boat: number }[];
  rain?: RainOutlook | null;
}

export interface SubArea extends PlaceNames {
  id: string;
  zoneId: string;
  name: string | null;
  access: "walk" | "truck" | "boat" | "unknown";
  geometry?: GeoJSON.Polygon | GeoJSON.MultiPolygon;
  open: number;
  people: number;
  urgent: number;
  lostContact: number;
  cannotWalk: number;
  boat: number;
  depthM: number | null;
  need: number;
  households: string[];
}

export interface ShelterOption { nameEn?: string | null; shelterId: string; name: string; kind: string; lon: number; lat: number; km: number; deepestM: number; walkable: boolean; minutes: number }

export interface FactView { field: string; value: unknown; quote: string }

export interface FeedItem {
  id: string;
  atH: number;
  at: string;
  channel: string;
  source: string;
  text: string;
  householdId: string;
  zoneId: string | null;
  how: string;
  tags: string[];
  facts: FactView[];
  label: string | null;
  reader: string | null;
}

export interface Feed { atH: number; items: FeedItem[]; total: number; counts: Record<string, number> }

export interface StoryItem {
  id: string;
  atH: number;
  at: string;
  channel: string;
  source: string;
  how: string | null;
  text: string;
  facts: FactView[];
  reader: string | null;
  depth: { lo: number; hi: number; model: number; label: string; weight: number } | null;
}

export interface CaseView {
  household: CaseRow;
  shelterOptions: ShelterOption[];
  shelter: { id: string; name: string; nameEn?: string } | null;
  unlocked: boolean;
  address: string | null;
  building: { id: string; outline: [number, number][]; groundM: number | null } | null;
  story: StoryItem[];
  depth: { m: number; lo: number; hi: number; reports: number; model: number } | null;
  depthSeries: [number, number][];
  depthReports: [number, number, number, string][];
  doubtfulWhy: string | null;
  neighbours: { from: string; to: string; side: string; sure: boolean; quote: string; known: boolean; at?: string; atH: number }[];
  possibleDuplicates: string[];
  contact: { sent: { atH: number; at: string; kind: string; text: string; en?: string }[]; replies: number; unanswered: number; lastHeard: string };
  zone: { id: string; district: string | null; level: Level | null; gap: string | null } | null;
  plans: Plan[];
  now: { atH: number; at: string };
}

export interface RouteLeg {
  from: string; to: string; path: [number, number][]; samples: [number, number, number][];
  km: number; minutes: number; deepestM: number; warnings: string[]; warningAt: [number, number];
}
export interface MissionRoute {
  vehicle: string; seats: number; start: { lon: number; lat: number; label: string };
  runs: { run: number; stops: string[]; start: MissionRoute["start"]; shelter: { id: string; name: string; nameEn: string | null; lon: number; lat: number } | null;
    legs: RouteLeg[]; totals: { km: number; minutes: number } }[];
  totals: { km: number; minutes: number }; perRun?: { runs: number; km: number; minutes: number }; deepestM: number; warnings: string[];
  unreachable: { id: string; reason: string; reasonTh: string }[]; now: { at: string; atH: number };
}
export interface ZonePage {
  route?: MissionRoute;
  plan?: Plan | null;
  /** Some zone responses may supply shelter choices; absence leaves the outcome unlinked. */
  shelterOptions?: ShelterOption[];
  zone: ZoneView;
  households: CaseRow[];
  outlook: { inH: number; wetShare: number; surfaceM: number | null }[];
  briefing: string;
  unlocked: boolean;
  subareas: SubArea[];
  blocks: SubArea[];
  totals: { open: number; people: number; urgent?: number; boat: number; closed: number };
  now: { atH: number; at: string };
}

export interface Trip {
  zones: { id: string; district: string | null; depthM: number | null; families: CaseRow[]; count: number; people: number; cannotWalk: number;
    elderly: number; children: number; boat: number; urgent: number; otherTeams: Plan[]; gap: string | null }[];
  people: number;
  boatNeeded: boolean;
  now: { atH: number; at: string };
}

export interface DepthSeries {
  start: string;
  nowH: number;
  now: string;
  model: number[];
  corrected: { m: number; lo: number; hi: number; reports: number; model: number };
  groundM: number | null;
  buildingId: string | null;
}

export const depthAt = (lon: number, lat: number) => get<DepthSeries>(`/api/v2/depth-series?lon=${lon}&lat=${lat}`);

export const blocksNow = () => get<{ blocks: SubArea[]; thresholds: { walkM: number; truckM: number } }>("/api/v2/v/blocks");

export interface ZoneSuggestion {
  reader: string;
  context: { waiting: number; people: number; otherTeams: number; floodedBuildings: number; householdEstimate: Range | null };
  order: { householdId: string; run: number; reason: string; quote: string }[];
  spareSeats: number; bring: string[]; checkStreets: { name: string; why: string }[]; warnings: string[]; summary: string;
}

export const vol = {
  route: (id: string, vehicle: string, seats: number, team?: string) => get<MissionRoute>(`/api/v2/v/mission/${encodeURIComponent(id)}/route?vehicle=${encodeURIComponent(vehicle)}&seats=${seats}&${q(team)}`),
  suggest: (zone: string, input: { team: string; vehicle: "boat" | "truck" | "foot"; seats: number; eta: string; lang: "th" | "en" }) => post<ZoneSuggestion>(`/api/v2/v/zones/${encodeURIComponent(zone)}/suggest`, input),
  urgent: () => get<UrgentView>("/api/v2/v/urgent"),
  first: (id: string, team: string, first: boolean) =>
    post<UrgentView>(`/api/v2/v/cases/${encodeURIComponent(id)}/first`, { team, first }),
  overview: () => get<Overview>("/api/v2/v/overview"),
  feed: (kind?: string, team?: string | null, limit?: number) => get<Feed>(`/api/v2/v/feed?${[kind ? `kind=${encodeURIComponent(kind)}` : "", q(team), limit ? `limit=${limit}` : ""].filter(Boolean).join("&")}`),
  zone: (id: string, team?: string | null) => get<ZonePage>(`/api/v2/v/zones/${encodeURIComponent(id)}?${q(team)}`),
  case: (id: string, team?: string | null) => get<CaseView>(`/api/v2/v/cases/${encodeURIComponent(id)}?${q(team)}`),
  outcome: (id: string, outcome: "pickedUp" | "nobodyThere" | "atShelter", team: string, shelterId?: string) =>
    post<CaseView>(`/api/v2/v/cases/${encodeURIComponent(id)}/outcome`, { outcome, team, shelterId }),
  trip: (zones: string[], team?: string | null) => get<Trip>(`/api/v2/v/trip?zones=${encodeURIComponent(zones.join(","))}&${q(team)}`),
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
