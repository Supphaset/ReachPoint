/**
 * Shapes of the views the app reads. DRAFT, hand-written from the fixtures in `contract/fixtures/`
 * (C1 geography, C2 area briefing). When contract v1.0 is frozen, these are replaced by the types
 * generated from the Pydantic models in `api/contract/` (T2, T12); keep field names in step until then.
 *
 * Convention (pack §3): an unknown value is `null` with a `valueReason`, never 0.
 */

export type Range = [number, number];

export type Priority = "red" | "yellow" | "green";

export type AssistanceType = "evacuation_transport" | "medical" | "supplies";

export type AllocationState = "open" | "taken" | "on_the_way" | "held" | "done" | "closed";

export type SegmentCheckState = "not_checked" | "partly_checked" | "checked" | "could_not_reach";

export type LayerState = "available" | "unavailable";

export interface Fact {
  key: string;
  label: string;
  value: number | null;
  valueReason?: string;
  unit: string;
  basis?: string;
  of?: number;
}

export interface UnknownItem {
  key: string;
  text: string;
  ref?: string;
}

export interface Assistance {
  type: AssistanceType;
  priority: Priority;
  review: "reported" | "validated" | "needs_clarification";
  allocation: AllocationState;
  teamId?: string;
  note?: string;
}

/** A reviewed case as a team leader sees it: landmark-level location only (D25). */
export interface CaseRow {
  caseId: string;
  segmentId: string;
  people: number;
  lastConfirmedAt: string;
  assistance: Assistance[];
}

export interface SegmentCheck {
  state: SegmentCheckState;
  at?: string;
  teamId?: string;
  householdsFound?: number;
  pickupsNeeded?: number;
  reason?: string;
}

export interface Estimate {
  everyone: Range;
  inSatelliteExtent: Range;
  modelledFlooded: Range | null;
  basis: "satellite" | "model" | "callers";
}

export interface SegmentDepth {
  /** Bare-earth ground height, 10th/50th/90th percentile (m). */
  groundM: [number, number, number];
  /** Modelled depth band (m), city segments only; capped at the deepest report. */
  modelledM: Range | null;
}

export interface SegmentView {
  segmentId: string;
  label: string;
  check: SegmentCheck;
  estimate: Estimate;
  depth: SegmentDepth;
  noSatelliteDataShare: number;
  cases: number;
}

export interface Briefing {
  /** writing: the server is asking Gemini; the facts are complete without it (C8). */
  state: "ready" | "writing" | "unavailable";
  text: string | null;
  reason?: string | null;
  source?: string;
}

/** Water reported by callers (D26, D32): reviewed requests only, at the segment's landmark (D25). */
export interface CallerWater {
  segmentId: string;
  landmarkLabel: string;
  at: [number, number];
  band: "knee" | "waist" | "chest" | "over_head" | "second_floor";
  bandLabel: string;
  approxM: number;
  callers: number;
  latestAt: string;
  stale: boolean;
}

export interface ZoneBriefingView {
  zoneId: string;
  areaId: string;
  district: string | null;
  badge: { urgent: number; unreviewed: number };
  status: "no_reports" | "has_reports";
  facts: Fact[];
  unknown: UnknownItem[];
  estimate: Estimate & { notYetChecked: Range };
  depth: { modelledM: Range; source: "model"; label: string } | null;
  cases: CaseRow[];
  segments: SegmentView[];
  callerWater: CallerWater[];
  briefing: Briefing;
}

export interface Layer {
  state: LayerState;
  id?: string | null;
  label: string;
}

export interface AreaBriefingView {
  areaId: string;
  label: string;
  need: "support_in_place" | "evacuation" | "no_recent_assessment";
  description: string;
  dataMode: "synthetic";
  package: string;
  generatedAt: string;
  inputVersions: Record<string, number>;
  dataLabel: string;
  badge: { urgent: number; unreviewed: number };
  facts: Fact[];
  estimate: { label: string; modelLabel: string; everyone: Range; notYetChecked: Range };
  layers: { floodExtent: Layer; noSatelliteData: Layer; reportedFlooding: Layer };
  callerWater: CallerWater[];
  callerWaterLabel: string;
  zones: ZoneBriefingView[];
}

/* ---- Team view (C5) and claim results (C6): draft, from contract/fixtures/teamMissions.T-S.json ---- */

export interface Party {
  adults: number;
  children: number;
  infants: number;
  stretcher: number;
}

export interface Group {
  groupId: string;
  label: string; // "Family 1"
  labelTh?: string; // "ครอบครัว 1"
  people: number;
  party: Party;
  seatUnits: number;
  state: "open" | "taken";
  takenBy?: string;
}

/** Why a case is red/yellow/green and what to bring: reviewed operational facts only (pack §4.1). */
export interface Urgency {
  title: string;
  summary: string;
  facts: { kind: "medical" | "medical_category" | "flag" | "people" | "mobility" | "water"; text: string; th?: string; basis: string; at?: string; callers?: number; stale?: boolean }[];
  kit: string[];
  withheld: string | null;
  /** The same lines in Thai, written by the server (api/views/thai.py). */
  th?: { title: string; summary: string; kit: string[]; withheld: string | null };
}

export interface Destination {
  id: string; // D1 shelter, H1 hospital (synthetic)
  label: string;
  reason: string;
  th?: { label: string; reason: string | null };
}

/** Medical notes for the team that took the job only (D38): functional first, then the condition, with the legal basis. */
export interface MedicalNotes {
  consent: "given" | "cannot_consent";
  basis: string;
  functional: string[];
  condition: string;
}

/** One open listing (case × help type) as a team sees it: landmark-level only, no exact point (D25). */
export interface OpenListing {
  listingId: string;
  caseId: string;
  assistanceType: AssistanceType;
  colour: Priority;
  tier: "1a" | "1b" | "2";
  needRevision: number;
  zoneId: string;
  segmentId: string;
  landmarkLabel: string;
  distanceM: number | null;
  distanceBasis: string;
  waitingSince: string;
  lastConfirmedAt: string;
  reconfirmRequestedAt?: string;
  reasons: string[];
  urgency: Urgency;
  destination: Destination;
  people: number;
  groups: Group[];
}

export type TeamStatus = "available" | "busy" | "off_duty";

export interface TeamState {
  status: TeamStatus;
  statusSetAt: string;
  reason: string | null;
  backAbout: string | null;
  capabilities: AssistanceType[];
  location: { landmarkId: string; label: string; at: [number, number] };
  resource: { resourceId: string; kind: string; seatUnits: number; seatUnitsLeft: number; basis: string; status?: "unavailable" };
}

export type JobState = "taken" | "on_the_way" | "on_scene" | "held" | "closed";
export type Outcome = "done" | "already_left" | "not_found" | "needs_more_help";

/** The team's own job. Only here does the exact pickup point appear, after taking it (D25, C16). */
export interface Job {
  allocationId: string;
  listingId: string;
  caseId: string;
  colour: Priority;
  landmarkLabel: string;
  urgency: Urgency;
  destination: Destination;
  /** Present while the job is open; removed from the team's view when it closes (D38). */
  medical: MedicalNotes | null;
  medicalRemovedAt?: string;
  groups: Group[];
  seatUnits: number;
  state: JobState;
  outcome?: Outcome;
  window: { start: string; end: string; setAt: string } | null;
  withdrawnWindow?: { start: string; end: string; setAt: string; state: "withdrawn"; withdrawnAt: string; withdrawnBy: string };
  owner?: "coordinator";
  holdReason?: string;
  nextStatusUpdate?: { at: string; by: string };
  briefRevision?: number;
  acceptedAt: string;
  closedAt?: string;
  pickup: { landmarkLabel: string; at: [number, number]; precision: "rooftop" | "building" | "landmark"; source: string };
}

/** Zone missions and segments (D17b, D20): on the team view once the desk has published a mission. */
export type SegmentMark =
  | { state: "checked" | "partly_checked"; at: string; teamId: string; householdsFound: number; pickupsNeeded: number }
  | { state: "could_not_reach"; at: string; teamId: string; reason: string };
export interface SegmentRow {
  segmentId: string;
  label: string;
  state: "open" | "taken" | SegmentCheckState;
  takenBy: string | null;
  claimId: string | null;
  mark: SegmentMark | null;
  registerCount: number;
  estimate: { everyone: Range; label: string };
  families: { caseId: string; people: number; listingIds: string[] }[];
}
export interface ZoneMissionView {
  missionId: string;
  zoneId: string;
  publishedAt: string;
  by: string;
  reasons: string[];
  segments: SegmentRow[];
}
export interface SegmentJob extends Omit<SegmentRow, "state" | "claimId" | "takenBy"> {
  claimId: string;
  state: "taken" | "marked";
  takenAt: string;
}

export interface TeamMissionsView {
  teamId: string;
  label: string;
  dataMode: "synthetic";
  generatedAt: string;
  dataLabel: string;
  team: TeamState;
  seatUnits: Record<keyof Party, number> & { label: string };
  open: OpenListing[];
  jobs: Job[];
  zoneMissions?: ZoneMissionView[];
  segmentJobs?: SegmentJob[];
  asks?: { askId: string; askedAt: string; listingIds: string[]; groups: { listingId: string; groupId: string; expectedRevision: number }[] }[];
}

export type ClaimCode =
  | "ALREADY_TAKEN"
  | "NOT_ENOUGH_CAPACITY"
  | "NEED_CHANGED"
  | "ALLOCATION_CLOSED"
  | "VERSION_CONFLICT"
  | "NOT_AVAILABLE"
  | "INVALID" // e.g. an urgent flag without a reason
  | "OFFLINE"; // API mode: the server couldn't be reached; nothing was changed

export type Result<T = undefined> = { ok: true; value: T } | { ok: false; code: ClaimCode; message: string };

/* ---- Split panel (C4 view) and asks (C7): draft, from contract/fixtures/splitPanel.cp3.json ---- */

export interface SplitRow {
  listingId: string;
  caseId: string | null;
  assistanceType: AssistanceType;
  areaId: string;
  tier: "1a" | "1b" | "2";
  colour: Priority;
  unit: "people" | "packs";
  units: number;
  part: Party | null;
  split: boolean;
  needsCoordinatorApproval: boolean;
}

export interface SplitAssignment extends SplitRow {
  resourceId: string;
  teamId: string;
  seatUnits: number | null;
  accepted: boolean;
}

export interface SplitUnassigned extends SplitRow {
  reason: "capacity_exhausted" | "no_capable_team";
  capableResources: string[];
  returnedFrom: string | null;
}

export interface Suggestion {
  suggestionId: string;
  inputVersions: Record<string, number>;
  snapshotAt: string;
  simulation: boolean;
  solver: { name: string; optimal: boolean; levels: Record<string, number> };
  weights: Record<string, number>;
  assignments: SplitAssignment[];
  unassigned: SplitUnassigned[];
  resources: { resourceId: string; teamId: string; capacity: Record<string, number>; used: Record<string, number>; simulated: boolean }[];
  explanations: { listingId: string; facts: string[] }[];
}

export interface SplitPanelView {
  dataMode: "synthetic";
  generatedAt: string;
  label: string;
  whatIfLabel: string;
  weights: Record<string, number | string>;
  needs: Record<string, { caseId: string; areaId: string; assistanceType: AssistanceType; label: string; units: number; unit: string; party: Party | null; note: string }>;
  resources: Record<string, { teamId: string; kind: string; basis: string }>;
  suggestion: Suggestion;
  scenarios: { id: string; label: string; options: Record<string, unknown>; diff: { peopleCoveredDelta: number; moreCovered: string[]; lessCovered: string[] }; suggestion: Suggestion }[];
}

export type AskResult =
  | { ok: true; askedAt: string; asks: { askId: string; teamId: string; listingIds: string[] }[]; note: string }
  | { ok: false; code: "VERSION_CONFLICT"; message: string; detail: { why: string; current: Suggestion } };

/** D41: satellite rain replayed on the demo clock. Never water depth; never changes counts or order. */
export interface RainPrompt {
  promptId: string;
  state: "proposed";
  title: string;
  reasons: string[];
  recheck: { segmentId: string; zoneId: string; checkedAt: string; groundM: number | null; reason: string }[];
  note: string;
}

export interface RainStatus {
  areaId: string;
  asOf: string;
  label: string;
  source: string;
  last1h: number | null;
  last3h: number | null;
  last24h: number | null;
  complete: boolean;
  class24h: string | null;
  line: string;
  prompt: RainPrompt | null;
}

/** D42: water rising, who to re-confirm first. A prompt for the desk; it never changes a colour by itself. */
export interface ReconfirmRow {
  rank: number;
  listingId: string;
  caseId: string;
  label: string;
  people: string;
  points: number;
  reasons: string[];
  lastConfirmedAt: string;
  ifItRises: { text: string; rangeM: [number, number] | null; mayBeOverHead: boolean | null } | null;
  actions: ("call_back" | "flag_urgent" | "dismiss")[];
}

export interface RisingWaterView {
  areaId: string;
  asOf: string;
  gaugeLine: string | null;
  forecastLines: string[];
  prompt: null | {
    promptId: string;
    state: "proposed";
    title: string;
    signals: { kind: "gauge_forecast" | "gauge_reading" | "heavy_rain"; since: string; text: string }[];
    rise: { atGaugeM: [number, number]; text: string } | null;
    reconfirm: ReconfirmRow[];
    more: number;
    note: string;
  };
}

/* ---- Intake, desk review, family status (T3, D6): from the starter server (contract/api.md) ---- */
export type WaterBand = "knee" | "waist" | "chest" | "over_head" | "second_floor";
export interface Quoted { quote: string }
export interface ProposedFacts {
  kind: "my_household" | "check_on" | "neighbour_report";
  kindQuote: string | null;
  people: ({ adults: number; children: number; infants: number; stretcher: number } & Quoted) | null;
  needs: ({ type: AssistanceType } & Quoted)[];
  water: ({ band: WaterBand } & Quoted) | null;
  place: ({ text: string } & Quoted) | null;
  dangerSigns: ({ text: string } & Quoted)[];
  cantWalk: Quoted | null;
  summary: string;
}
export interface ReviewRow {
  reportId: string;
  receivedAt: string;
  text: string;
  channel: string;
  proposal: { source: string; note: string | null; facts: ProposedFacts; dropped: string[] };
  suggestedSegment: { segmentId: string | null; zoneId?: string; label: string; why: string } | null;
  prompts: { kind: "urgent_flag" | "stretcher" | "neighbour" | "field"; text: string }[];
  /** The ADK triage agent's proposals (D29): possible duplicates and a rank reason. A person decides. */
  triage: null | {
    source: string;
    at: string;
    links: { caseId: string; place: string; people: number; reason: string; quote: string; newHazard: boolean }[];
    rank: { reason: string; quote: string; danger: string[] } | null;
  };
  fromTeam?: string;
}
export interface ReviewQueueView {
  generatedAt: string;
  label: string;
  triage: { source: string | null; at: string | null; note?: string | null } | null;
  reports: ReviewRow[];
  landmarks: { segmentId: string; label: string }[];
}
export interface ReceiptResponse { answer: "yes" | "no"; at: string }

export interface ResidentStatusView {
  receipt?: ReceiptResponse | null;
  completedAt?: (string | null)[];
  reportId: string;
  caseId?: string;
  generatedAt: string;
  label: string;
  state: string;
  lastConfirmedAt?: string;
  lines: { family?: string; familyTh?: string; state: string; text: string; th?: string }[];
}
