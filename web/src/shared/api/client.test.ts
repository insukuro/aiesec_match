// web/src/shared/api/client.test.ts
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  request, ApiError, setAccessToken, getAccessToken, setUnauthorizedHandler,
} from "./client";

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  setAccessToken(null);
  setUnauthorizedHandler(null);
});

afterEach(() => vi.unstubAllGlobals());

describe("request", () => {
  it("200 JSON", async () => {
    fetchMock.mockResolvedValueOnce(Response.json({ ok: true }));
    expect(await request<{ ok: boolean }>("/x")).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledExactlyOnceWith("/api/v1/x", expect.any(Object));
  });

  it("204 → undefined", async () => {
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }));
    expect(await request("/x", { method: "DELETE" })).toBeUndefined();
    expect(fetchMock).toHaveBeenCalledExactlyOnceWith(
      "/api/v1/x",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("ставит Authorization если токен есть", async () => {
    setAccessToken("tok");
    fetchMock.mockResolvedValueOnce(Response.json({}));
    await request("/x");
    expect(new Headers(fetchMock.mock.calls[0][1]?.headers).get("authorization")).toBe("Bearer tok");
  });

  it("skipAuth — не ставит Authorization", async () => {
    setAccessToken("tok");
    fetchMock.mockResolvedValueOnce(Response.json({}));
    await request("/x", { method: "POST", body: {}, skipAuth: true });
    expect(fetchMock).toHaveBeenCalledExactlyOnceWith(
      "/api/v1/x",
      expect.objectContaining({ method: "POST", body: "{}" }),
    );
    expect(new Headers(fetchMock.mock.calls[0][1]?.headers).has("authorization")).toBe(false);
  });

  it("ставит If-Match и Idempotency-Key", async () => {
    fetchMock.mockResolvedValueOnce(Response.json({}));
    await request("/x", { method: "POST", body: {}, ifMatch: '"3"', idempotencyKey: "k1" });
    expect(fetchMock).toHaveBeenCalledExactlyOnceWith(
      "/api/v1/x",
      expect.objectContaining({ method: "POST" }),
    );
    const headers = new Headers(fetchMock.mock.calls[0][1]?.headers);
    expect(headers.get("if-match")).toBe('"3"');
    expect(headers.get("idempotency-key")).toBe("k1");
  });

  it("401 — сбрасывает токен и зовёт onUnauthorized", async () => {
    setAccessToken("tok");
    const onUnauth = vi.fn();
    setUnauthorizedHandler(onUnauth);
    fetchMock.mockResolvedValueOnce(
      Response.json({ type: "/problems/unauthorized", title: "U", status: 401 }, { status: 401 }),
    );
    await expect(request("/x")).rejects.toMatchObject({ status: 401 });
    expect(getAccessToken()).toBeNull();
    expect(onUnauth).toHaveBeenCalledOnce();
  });

  it("401 + skipAuth — НЕ зовёт onUnauthorized", async () => {
    const onUnauth = vi.fn();
    setUnauthorizedHandler(onUnauth);
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 401 }));
    const result = request("/x", { method: "POST", skipAuth: true });
    await expect(result).rejects.toBeInstanceOf(ApiError);
    await expect(result).rejects.toMatchObject({ status: 401 });
    expect(onUnauth).not.toHaveBeenCalled();
  });

  it("4xx — ApiError с problem", async () => {
    fetchMock.mockResolvedValueOnce(
      Response.json({ type: "/problems/validation", title: "V", status: 422, errors: [] }, { status: 422 }),
    );
    await expect(request("/x")).rejects.toMatchObject({
      status: 422,
      problem: { type: "/problems/validation" },
    });
  });

  it("не-JSON тело ошибки — fallback problem", async () => {
    fetchMock.mockResolvedValueOnce(new Response("oops", { status: 500 }));
    await expect(request("/x")).rejects.toMatchObject({ status: 500 });
  });

  it("сетевой сбой → ApiError(0, /problems/network)", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    await expect(request("/x")).rejects.toMatchObject({
      status: 0,
      problem: { type: "/problems/network" },
    });
  });

  it("200 с пустым телом → undefined", async () => {
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 200 }));
    expect(await request("/x")).toBeUndefined();
  });
});
