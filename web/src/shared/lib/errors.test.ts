import { describe, it, expect } from "vitest";
import { ApiError } from "../api/client";
import { errorMessage, asProblem } from "./errors";

const err = (type: string, status = 400, detail = "", title = "") =>
  new ApiError(status, { type, title, status, detail });

describe("asProblem", () => {
  it("ApiError → problem", () => {
    expect(asProblem(err("/problems/x"))?.type).toBe("/problems/x");
  });
  it("обычный Error → about:blank", () => {
    expect(asProblem(new Error("boom"))?.status).toBe(0);
  });
  it("null", () => expect(asProblem(null)).toBeNull());
});

describe("errorMessage", () => {
  it.each([
    ["/problems/validation", "Проверьте поля формы"],
    ["/problems/unauthorized", "Нужно войти заново"],
    ["/problems/forbidden-guest", "Доступно только в аккаунте"],
    ["/problems/email-taken", "Этот email уже зарегистрирован"],
    ["/problems/bad-credentials", "Неверный email или пароль"],
    ["/problems/consent-required", "Требуется согласие на обработку данных"],
    ["/problems/profile-incomplete", "Профиль заполнен не полностью"],
    ["/problems/version-conflict", "Профиль изменён в другом месте"],
    ["/problems/rate-limited", "Слишком много запросов"],
    ["/problems/matcher-unavailable", "Сервис подбора временно недоступен"],
    ["/problems/matcher-timeout", "Сервис подбора временно недоступен"],
  ])("%s", (type, expected) => {
    expect(errorMessage(err(type))).toBe(expected);
  });
  it("неизвестный — detail", () => {
    expect(errorMessage(err("/problems/unknown", 400, "деталь"))).toBe("деталь");
  });
  it("совсем неизвестный — title", () => {
    expect(errorMessage(err("/problems/unknown", 400, "", "Заголовок"))).toBe("Заголовок");
  });
  it("null — 'Неизвестная ошибка'", () => {
    expect(errorMessage(null)).toBe("Неизвестная ошибка");
  });
});