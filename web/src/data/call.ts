/** ReachPoint conversation API. The server owns facts, location choices and report submission. */

import { get, post, submissionId } from "./api";

export interface HelpRequestDetails {
  phone_number: string | null;
  type: "food" | "evacuation" | null;
  people_details: string | null;
  n_children: number | null;
  n_elders: number | null;
  n_pets: number | null;
  location: string | null;
  coordinates: string | null;
  location_details: string | null;
  water_level: string | null;
  situation_details: string | null;
  emergency_detail: string | null;
  other_details: string | null;
}

export interface HelpRequest extends HelpRequestDetails {
  phone_number: string;
  type: "food" | "evacuation";
  report_id: string;
  channel: "chat" | "voice" | "form";
}

export const REQUEST_DETAIL_FIELDS = [
  "phone_number", "type",
  "people_details", "n_children", "n_elders", "n_pets", "location", "coordinates",
  "location_details", "water_level", "situation_details", "emergency_detail", "other_details",
] as const satisfies readonly (keyof HelpRequestDetails)[];

export const EMPTY_REQUEST_DETAILS: HelpRequestDetails = {
  phone_number: null, type: null,
  people_details: null, n_children: null, n_elders: null, n_pets: null, location: null,
  coordinates: null, location_details: null, water_level: null, situation_details: null,
  emergency_detail: null, other_details: null,
};

export interface CallCase extends HelpRequestDetails {
  immediate_danger: boolean | null;
  unavailable_fields: string[];
  contradictions: string[];
}

export interface CallSession {
  sessionId: string;
  revision: number;
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
export const confirmCall = (id: string, expectedRevision: number, idempotencyKey = submissionId()) =>
  post<CallSession>(`/api/call/sessions/${id}/confirm`, { submissionId: idempotencyKey, expectedRevision });
