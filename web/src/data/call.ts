/** ReachPoint conversation API. The server owns facts, location choices and report submission. */

import { get, post, submissionId } from "./api";

export interface CallCase {
  reporter_name: string | null;
  reporter_age: number | null;
  people_count: number | null;
  people_details: string | null;
  children_count: number | null;
  elderly_count: number | null;
  mobility_needs: string | null;
  location: string | null;
  landmark: string | null;
  coordinates: string | null;
  water_level: string | null;
  water_trend: string | null;
  current_shelter: string | null;
  injuries: string | null;
  urgent_needs: string | null;
  immediate_danger: boolean | null;
  danger_details: string | null;
  callback_contact: string | null;
  unavailable_fields: string[];
  contradictions: string[];
}

export interface CallSession {
  sessionId: string;
  messages: { role: "user" | "assistant"; text: string }[];
  case: CallCase;
  locationLookup: {
    status: string;
    query?: string;
    candidates?: { id: string; label: string }[];
    label?: string;
  };
  canConfirm: boolean;
  summary: string | null;
  sent: { reportId: string; statusToken: string; statusUrl: string; aiSource: string } | null;
}

export interface CallConfig { chat: boolean; voice: boolean }

export const callConfig = () => get<CallConfig>("/api/call/config");
export const startCall = () => post<CallSession>("/api/call/sessions", {});
export const readCall = (id: string) => get<CallSession>(`/api/call/sessions/${id}`);
export const sendCallTurn = (id: string, text: string, turnId = submissionId()) =>
  post<CallSession>(`/api/call/sessions/${id}/turn`, { text, turnId });
export const chooseCallLocation = (id: string, query: string, action: "select" | "reject", locationId?: string) =>
  post<CallSession>(`/api/call/sessions/${id}/location`, { query, action, locationId });
export const confirmCall = (id: string, idempotencyKey = submissionId()) =>
  post<CallSession>(`/api/call/sessions/${id}/confirm`, { submissionId: idempotencyKey });
