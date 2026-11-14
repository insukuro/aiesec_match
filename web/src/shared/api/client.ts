import type { Problem } from "./types";

const API_BASE = "/api/v1";
const TOKEN_KEY = "access_token";

let accessToken: string | null = localStorage.getItem(TOKEN_KEY);
let onUnauthorized: (() => void) | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function setUnauthorizedHandler(fn: (() => void) | null): void {
  onUnauthorized = fn;
}

export class ApiError extends Error {
  readonly status: number;
  readonly problem: Problem;

  constructor(status: number, problem: Problem) {
    super(problem.title || `HTTP ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.problem = problem;
  }
}

export interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  ifMatch?: string;
  idempotencyKey?: string;
  skipAuth?: boolean;
}

function buildHeaders(opts: RequestOptions): Headers {
  const h = new Headers(opts.headers);
  h.set("Accept", "application/json");
  if (opts.body !== undefined) h.set("Content-Type", "application/json");
  h.set("X-Request-ID", crypto.randomUUID());
  if (!opts.skipAuth && accessToken) h.set("Authorization", `Bearer ${accessToken}`);
  if (opts.ifMatch) h.set("If-Match", opts.ifMatch);
  if (opts.idempotencyKey) h.set("Idempotency-Key", opts.idempotencyKey);
  return h;
}

async function parseProblem(res: Response): Promise<Problem> {
  try {
    const body = (await res.json()) as Partial<Problem>;
    return {
      type: body.type ?? "about:blank",
      title: body.title ?? res.statusText,
      status: body.status ?? res.status,
      detail: body.detail,
      instance: body.instance,
      request_id: body.request_id,
      errors: body.errors,
    };
  } catch {
    return { type: "about:blank", title: res.statusText || "error", status: res.status };
  }
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { body, ifMatch: _if, idempotencyKey: _id, skipAuth, ...rest } = opts;
  const init: RequestInit = {
    ...rest,
    headers: buildHeaders(opts),
    body: body === undefined ? undefined : JSON.stringify(body),
  };

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, init);
  } catch (e) {
    throw new ApiError(0, {
      type: "/problems/network",
      title: "Сеть недоступна",
      status: 0,
      detail: e instanceof Error ? e.message : "network error",
    });
  }

  if (res.status === 401 && !skipAuth) {
    setAccessToken(null);
    if (onUnauthorized) onUnauthorized();
    throw new ApiError(401, await parseProblem(res));
  }
  if (!res.ok) throw new ApiError(res.status, await parseProblem(res));
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}