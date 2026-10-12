/** Intake and desk review calls (contract/api.md). These need the server: in fixture mode they say so. */
import { ApiError, post, submissionId } from "./api";
import type { AssistanceType, WaterBand } from "./contract";
import { apiMode } from "./mode";

export type Sent = { ok: true; reportId: string; statusUrl: string; aiSource: string } | { ok: false; message: string };
export type Done = { ok: true; value?: { caseId: string; listingIds: string[] } } | { ok: false; message: string };

const NEEDS_SERVER = "This needs the server. Open the app with ?data=api (see contract/api.md).";

async function send<T>(path: string, body: object): Promise<{ ok: true; value: T } | { ok: false; message: string }> {
  if (!apiMode()) return { ok: false, message: NEEDS_SERVER };
  try {
    const r = await post<{ value: T }>(path, { ...body, submissionId: submissionId() });
    return { ok: true, value: r.value };
  } catch (e) {
    return { ok: false, message: e instanceof ApiError ? e.message : "Something went wrong; nothing was saved. Try again." };
  }
}

export async function sendRequest(text: string): Promise<Sent> {
  const r = await send<{ reportId: string; statusUrl: string; aiSource: string }>("/api/intake/text", { text, channel: "text" });
  return r.ok ? { ok: true, ...r.value } : r;
}

export interface Approval {
  segmentId: string;
  people: { adults: number; children: number; infants: number; stretcher: number };
  needs: AssistanceType[];
  waterBand: WaterBand | null;
  urgentReason: string | null;
  deskNote: string | null;
}

export const approveReport = (reportId: string, a: Approval): Promise<Done> => send(`/api/reports/${reportId}/approve`, a);
export const rejectReport = (reportId: string, reason: string): Promise<Done> => send(`/api/reports/${reportId}/reject`, { reason });
export { NEEDS_SERVER };

export const publishMission = (zoneId: string, reasons: string[]): Promise<Done> => send("/api/zone-missions", { zoneId, reasons });
export const dismissCheck = (zoneId: string, reason: string): Promise<Done> => send(`/api/suggested-checks/${zoneId}/dismiss`, { reason });
export const linkReport = (reportId: string, caseId: string): Promise<Done> => send(`/api/reports/${reportId}/link`, { caseId });
export const notSame = (reportId: string, caseId: string): Promise<Done> => send(`/api/reports/${reportId}/not-same`, { caseId });
