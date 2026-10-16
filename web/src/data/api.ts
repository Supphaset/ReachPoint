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
  if (res.status === 422) throw new ApiError("INVALID", "Some details weren't accepted. Check the form and try again.", 422);
  if (!res.ok) throw new ApiError(json.code ?? `HTTP_${res.status}`, json.message ?? res.statusText, res.status);
  return json as T;
}

export const get = <T>(path: string, token?: string) => call<T>("GET", path, undefined, token);
export const post = <T>(path: string, body: object, token?: string) => call<T>("POST", path, body, token);

/** POST with SSE; decode across network/UTF-8 boundaries and require a final snapshot. */
export async function streamPost<T>(path: string, body: object, onDelta: (text: string) => void): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      method: "POST", headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError("OFFLINE", "Can't reach the server. Check your connection and try again");
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(error.code ?? `HTTP_${response.status}`, error.message ?? error.detail ?? response.statusText, response.status);
  }
  if (!response.body || !response.headers.get("content-type")?.includes("text/event-stream")) {
    throw new ApiError("STREAM", "Chat couldn't start. Please try again.");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      let boundary: RegExpExecArray | null;
      while ((boundary = /\r?\n\r?\n/.exec(buffer))) {
        const frame = buffer.slice(0, boundary.index);
        buffer = buffer.slice(boundary.index + boundary[0].length);
        const lines = frame.split(/\r?\n/);
        const event = lines.find((line) => line.startsWith("event:"))?.slice(6).trim();
        const data = lines.filter((line) => line.startsWith("data:")).map((line) => line.slice(5).trimStart()).join("\n");
        if (!data) continue;
        const payload = JSON.parse(data);
        if (event === "error") throw new ApiError("TURN", payload.message, payload.status);
        if (event === "delta") onDelta(payload.text);
        if (event === "snapshot") return payload as T;
      }
      if (done) throw new ApiError("STREAM", "Chat was interrupted. Please try again.");
    }
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
