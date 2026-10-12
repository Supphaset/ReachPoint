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
  state: "ready" | "unavailable";
  text: string | null;
  reason?: string;
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
  people: number;
  party: Party;
  seatUnits: number;
  state: "open" | "taken";
  takenBy?: string;
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
  resource: { resourceId: string; kind: string; seatUnits: number; seatUnitsLeft: number; basis: string };
}

export type JobState = "taken" | "on_the_way" | "on_scene" | "closed";
export type Outcome = "done" | "already_left" | "not_found" | "needs_more_help";

/** The team's own job. Only here does the exact pickup point appear, after taking it (D25, C16). */
export interface Job {
  allocationId: string;
  listingId: string;
  caseId: string;
  colour: Priority;
  landmarkLabel: string;
  groups: Group[];
  seatUnits: number;
  state: JobState;
  outcome?: Outcome;
  window: { start: string; end: string; setAt: string } | null;
  acceptedAt: string;
  closedAt?: string;
  pickup: { landmarkLabel: string; at: [number, number]; precision: "rooftop" | "building" | "landmark"; source: string };
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
}

export type ClaimCode =
  | "ALREADY_TAKEN"
  | "NOT_ENOUGH_CAPACITY"
  | "NEED_CHANGED"
  | "ALLOCATION_CLOSED"
  | "VERSION_CONFLICT"
  | "NOT_AVAILABLE";

export type Result<T = undefined> = { ok: true; value: T } | { ok: false; code: ClaimCode; message: string };
