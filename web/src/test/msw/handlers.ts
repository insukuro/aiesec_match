import { http, HttpResponse } from "msw";

const API = "/api/v1";

export const handlers = [
  http.get(`${API}/health`, () => HttpResponse.json({ status: "ok" })),
  // по умолчанию — «не залогинен»
  http.get(`${API}/me`, () =>
    HttpResponse.json({ type: "/problems/unauthorized", title: "Unauthorized", status: 401 },
      { status: 401 }),
  ),
];