import { get, post, submissionId } from "./api";

export type MapMode = "water" | "needs" | "response";
export type MapSource = "operations" | "replay";
export interface WaterEstimate {
  siteId: string; status: "available" | "conflicting" | "qualitative_only" | "insufficient_evidence" | "stale";
  rangeM: [number, number] | null; centralM: number | null; latestAt: string | null;
  observationCount: number; sourceReferences: number; independence: "unknown"; bands: string[];
  trends: string[]; reasons: string[]; evidenceIds: string[]; method: string;
}
export interface WaterEvidence {
  observationId: string; reportId: string; observedAt: string | null; receivedAt: string;
  reference: string; source: string; band: string | null; depthM: number | null;
  uncertaintyM: number | null; trend: string; review: string;
}
export interface FloodSegment {
  segmentId: string; zoneId: string; areaId: string; label: string; at: [number, number]; noSatelliteDataShare: number;
  needs: { reportedPeople: number; verifiedTransportUnassigned: number; urgentReports: number; urgentReviewedGroups: number; supplyReports: number; checkOnReports: number };
  coverage: { activeJobs: number; heldJobs: number; state: string };
  estimates: WaterEstimate[]; observations: WaterEvidence[];
}
export interface FloodView {
  source: MapSource; asOf: string; processingMode: string; note: string;
  replay: { version: string; cursor: number; revision: number; total: number; at: string; mode: string } | null;
  counters: { received: number; organized: number; exceptions: number; urgentReports: number; observations: number;
    numericEstimates: number; conflicts: number; verifiedTransportUnassigned: number };
  segments: FloodSegment[];
  exceptions: { reportId: string; segmentId: string | null; urgent: boolean; reasons: string[] }[];
  exceptionsTotal: number;
  teams: { teamId: string; status: string; at: [number, number]; areas: string[]; capabilities: string[];
    resourceId: string; resourceStatus: string; statusSetAt: string; freeSeats: number }[];
}
export const loadFlood = (source: MapSource) => get<FloodView>(`/api/views/floodMap?source=${source}`);
export const stepReplay = (cursor: number, revision: number, count: number, id = submissionId()) =>
  post<{ ok: true; cursor: number; total: number }>("/api/demo/flood-replay/step", { expectedCursor: cursor, expectedRevision: revision, count, submissionId: id });
export const resetReplay = (cursor: number, revision: number, id = submissionId()) =>
  post("/api/demo/flood-replay/reset", { expectedCursor: cursor, expectedRevision: revision, submissionId: id });
