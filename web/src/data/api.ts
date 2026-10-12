/**
 * Typed API client (C10). Every write goes through the friend's FastAPI on Cloud Run (D2): the app never
 * writes Firestore directly. Each call carries `expectedVersion` and a `submissionId` so a retry is safe.
 * Endpoints are added as the contract freezes; until the API URL is set, calls fail with a clear error.
 */
const BASE = import.meta.env.VITE_API_URL as string | undefined;

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

export function submissionId(): string {
  return `SUB-${crypto.randomUUID()}`;
}

export async function post<T>(path: string, body: object, token?: string): Promise<T> {
  if (!BASE) throw new ApiError("NO_API", "The server isn't connected yet");
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify(body),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(json.code ?? `HTTP_${res.status}`, json.message ?? res.statusText);
  return json as T;
}
