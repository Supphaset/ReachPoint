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
