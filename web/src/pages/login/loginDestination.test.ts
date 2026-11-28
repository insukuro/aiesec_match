import { describe, expect, it } from "vitest";
import { loginDestination } from "./loginDestination";

describe("loginDestination", () => {
  it.each([
    ["/profile/favorites", "/profile/favorites"],
    ["/SETTINGS/", "/settings"],
    ["/opportunities", "/results"],
    ["/profile/statistics/settings", "/app"],
    ["/opportunity/42", "/opportunity/42"],
    ["/onboarding/2", "/onboarding/2"],
  ])("возвращает на внутренний маршрут %s", (next, expected) => {
    expect(loginDestination(next, true)).toBe(expected);
  });

  it.each([
    null,
    "https://example.invalid",
    "//example.invalid",
    "/\\example.invalid",
    "/\texample.invalid",
    "/%2Fexample.invalid",
    "/login",
    "/opportunity/9007199254740992",
  ])("выбирает страницу по умолчанию для %s", (next) => {
    expect(loginDestination(next, true)).toBe("/app");
    expect(loginDestination(next, false)).toBe("/onboarding/0");
  });
});
