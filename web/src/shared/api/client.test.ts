// web/src/shared/api/client.test.ts
import { describe, it, expect, beforeEach, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../../test/msw/server";
import {
  request, ApiError, setAccessToken, getAccessToken, setUnauthorizedHandler,
} from "./client";

beforeEach(() => {
  setAccessToken(null);
  setUnauthorizedHandler(null);
  localStorage.clear();
});

describe("request", () => {
  it("200 JSON", async () => {
    server.use(http.get("/api/v1/x", () => HttpResponse.json({ ok: true })));
    expect(await request<{ ok: boolean }>("/x")).toEqual({ ok: true });
  });

  it("204 → undefined", async () => {
    server.use(http.delete("/api/v1/x", () => new HttpResponse(null, { status: 204 })));
    expect(await request("/x", { method: "DELETE" })).toBeUndefined();
  });

  it("ставит Authorization если токен есть", async () => {
    setAccessToken("tok");
    let header = "";
    server.use(http.get("/api/v1/x", ({ request }) => {
      header = request.headers.get("authorization") ?? "";
      return HttpResponse.json({});
    }));
    await request("/x");
    expect(header).toBe("Bearer tok");
  });

  it("skipAuth — не ставит Authorization", async () => {
    setAccessToken("tok");
    let header: string | null = "sentinel";
    server.use(http.post("/api/v1/x", ({ request }) => {
      header = request.headers.get("authorization");
      return HttpResponse.json({});
    }));
    await request("/x", { method: "POST", body: {}, skipAuth: true });
    expect(header).toBeNull();
  });

  it("ставит If-Match и Idempotency-Key", async () => {
    let ifMatch: string | null = null, idem: string | null = null;
    server.use(http.post("/api/v1/x", ({ request }) => {
      ifMatch = request.headers.get("if-match");
      idem = request.headers.get("idempotency-key");
      return HttpResponse.json({});
    }));
    await request("/x", { method: "POST", body: {}, ifMatch: '"3"', idempotencyKey: "k1" });
    expect(ifMatch).toBe('"3"');
    expect(idem).toBe("k1");
  });

  it("401 — сбрасывает токен и зовёт onUnauthorized", async () => {
    setAccessToken("tok");
    const onUnauth = vi.fn();
    setUnauthorizedHandler(onUnauth);
    server.use(http.get("/api/v1/x", () =>
      HttpResponse.json({ type: "/problems/unauthorized", title: "U", status: 401 }, { status: 401 })));
    await expect(request("/x")).rejects.toMatchObject({ status: 401 });
    expect(getAccessToken()).toBeNull();
    expect(onUnauth).toHaveBeenCalledOnce();
  });

  it("401 + skipAuth — НЕ зовёт onUnauthorized", async () => {
    const onUnauth = vi.fn();
    setUnauthorizedHandler(onUnauth);
    server.use(http.post("/api/v1/x", () => new HttpResponse(null, { status: 401 })));
    await expect(request("/x", { method: "POST", skipAuth: true })).rejects.toBeInstanceOf(ApiError);
    expect(onUnauth).not.toHaveBeenCalled();
  });

  it("4xx — ApiError с problem", async () => {
    server.use(http.get("/api/v1/x", () =>
      HttpResponse.json({ type: "/problems/validation", title: "V", status: 422, errors: [] }, { status: 422 })));
    await expect(request("/x")).rejects.toMatchObject({
      status: 422,
      problem: { type: "/problems/validation" },
    });
  });

  it("не-JSON тело ошибки — fallback problem", async () => {
    server.use(http.get("/api/v1/x", () => new HttpResponse("oops", { status: 500 })));
    await expect(request("/x")).rejects.toMatchObject({ status: 500 });
  });

  it("сетевой сбой → ApiError(0, /problems/network)", async () => {
    server.use(http.get("/api/v1/x", () => HttpResponse.error()));
    await expect(request("/x")).rejects.toMatchObject({
      status: 0,
      problem: { type: "/problems/network" },
    });
  });

  it("200 с пустым телом → undefined", async () => {
    server.use(http.get("/api/v1/x", () => new HttpResponse(null, { status: 200 })));
    expect(await request("/x")).toBeUndefined();
  });
});