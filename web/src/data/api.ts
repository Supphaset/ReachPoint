/** Shared v2 HTTP client with room isolation and readable validation/rate-limit errors. */
import { demoRoom } from "./room";

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status = 0,
    public retryAfter = 0,
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
    res = await fetch(path, {
      method,
      headers: {
        "X-Demo-Room": demoRoom(),
        ...(body ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("OFFLINE", "Can't reach the server. Check your connection and try again");
  }
  const json = await res.json().catch(() => ({}));
  if (res.status === 429) {
    const seconds = Math.max(1, Math.ceil(Number(res.headers.get("Retry-After") ?? json.retryAfter) || 60));
    throw new ApiError("rate_limited", `Too many messages at once — wait ${seconds} seconds / ส่งข้อความถี่เกินไป กรุณารอ ${seconds} วินาที`, 429, seconds);
  }
  if (res.status === 422) throw new ApiError("INVALID", "Some details weren't accepted. Check the form and try again.", 422);
  if (!res.ok) throw new ApiError(json.code ?? `HTTP_${res.status}`, json.message ?? res.statusText, res.status);
  return json as T;
}

export const get = <T>(path: string, token?: string) => call<T>("GET", path, undefined, token);
export const post = <T>(path: string, body: object, token?: string) => call<T>("POST", path, body, token);
