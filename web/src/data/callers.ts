/** Caller-page API client. Uses the same intake contract as the call page. */
import { get, post, streamPost, submissionId } from "./api";
import type { CallConfig, CallSession, HelpRequestDetails } from "./call";
export { EMPTY_REQUEST_DETAILS, REQUEST_DETAIL_FIELDS } from "./call";
export type { CallConfig, CallSession, HelpRequestDetails } from "./call";

export const callConfig = () => get<CallConfig>("/api/callers/config");
export const startCall = () => post<CallSession>("/api/callers/sessions", {});
export const readCall = (id: string) => get<CallSession>(`/api/callers/sessions/${id}`);
export const sendCallTurn = (id: string, text: string, turnId = submissionId()) =>
  post<CallSession>(`/api/callers/sessions/${id}/turn`, { text, turnId });
export const streamCallTurn = (id: string, text: string, onDelta: (text: string) => void, turnId = submissionId()) =>
  streamPost<CallSession>(`/api/callers/sessions/${id}/turn`, { text, turnId }, onDelta);
export const chooseCallLocation = (id: string, query: string, action: "select" | "reject", locationId?: string) =>
  post<CallSession>(`/api/callers/sessions/${id}/location`, { query, action, locationId });
export const confirmCall = (id: string, expectedRevision: number, idempotencyKey = submissionId()) =>
  post<CallSession>(`/api/callers/sessions/${id}/confirm`, { submissionId: idempotencyKey, expectedRevision });

export const submitCallerForm = (id: string, details: HelpRequestDetails, expectedRevision: number, idempotencyKey = submissionId()) =>
  post<CallSession>(`/api/callers/sessions/${id}/form`, { ...details, expectedRevision, submissionId: idempotencyKey });
