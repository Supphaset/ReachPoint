/**
 * Typed API client (C10). Every write goes through the FastAPI server (D2): the app never writes Firestore
 * directly. Each write carries a `submissionId` so a retry is safe, and the revision it saw where it matters.
 * Routes: contract/api.md. Rule failures come back as HTTP 409 with `{ code, message, detail }`.
 */
const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "";

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status = 0,
  ) {
    super(message);
  }
}

export function submissionId(): string {
  return `SUB-${crypto.randomUUID()}`;
}

async function call<T>(method: "GET" | "POST", path: string, body?: object, token?: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers: { ...(body ? { "Content-Type": "application/json" } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("OFFLINE", "Can't reach the server. Check your connection and try again");
  }
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(json.code ?? `HTTP_${res.status}`, json.message ?? res.statusText, res.status);
  return json as T;
}

export const get = <T>(path: string, token?: string) => call<T>("GET", path, undefined, token);
export const post = <T>(path: string, body: object, token?: string) => call<T>("POST", path, body, token);
