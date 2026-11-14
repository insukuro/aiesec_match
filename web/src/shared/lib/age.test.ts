import { describe, it, expect } from "vitest";
import { MIN_AGE, MAX_AGE, yearsBetween, maxBirthDate, minBirthDate, validateAge, parseIsoDate } from "./age";

const d = (iso: string) => new Date(iso + "T00:00:00");

describe("yearsBetween", () => {
  it("считает полные годы", () => {
    expect(yearsBetween(d("2000-01-01"), d("2025-01-01"))).toBe(25);
  });
  it("не наступил день рождения — на год меньше", () => {
    expect(yearsBetween(d("2000-06-15"), d("2025-06-14"))).toBe(24);
    expect(yearsBetween(d("2000-06-15"), d("2025-06-15"))).toBe(25);
  });
  it("високосный год", () => {
    expect(yearsBetween(d("2000-02-29"), d("2025-02-28"))).toBe(24);
    expect(yearsBetween(d("2000-02-29"), d("2025-03-01"))).toBe(25);
  });
});

describe("parseIsoDate", () => {
  it("валидная строка", () => {
    const d = parseIsoDate("2020-01-15")!;
    expect(d.getFullYear()).toBe(2020);
    expect(d.getMonth()).toBe(0);       // 0-based
    expect(d.getDate()).toBe(15);
  });
  it("пустая и мусор — null", () => {
    expect(parseIsoDate("")).toBeNull();
    expect(parseIsoDate("not-a-date")).toBeNull();
  });
});

describe("maxBirthDate / minBirthDate", () => {
  const today = d("2025-06-15");
  it("maxBirthDate = сегодня − MIN_AGE", () => {
    expect(maxBirthDate(today)).toBe("2009-06-15");
  });
  it("minBirthDate = сегодня − (MAX_AGE+1) + 1 день", () => {
    expect(minBirthDate(today)).toBe("1990-06-16");
  });
  it("не зависит от UTC-сдвига (регрессия)", () => {
    const lateNight = new Date("2025-06-15T00:30:00+05:00");
    const expected = new Date(lateNight);
    expected.setFullYear(expected.getFullYear() - MIN_AGE);
    const iso = `${expected.getFullYear()}-${String(expected.getMonth() + 1).padStart(2, "0")}-${String(expected.getDate()).padStart(2, "0")}`;
    expect(maxBirthDate(lateNight)).toBe(iso);
  });
});

describe("validateAge", () => {
  it("ok", () => {
    expect(validateAge("2000-01-01")).toBeNull();
  });
  it("будущее", () => {
    expect(validateAge("2999-01-01")).toMatch(/в будущем/i);
  });
  it("слишком юн", () => {
    const iso = maxBirthDate();
    const dPlus = new Date(iso); dPlus.setDate(dPlus.getDate() + 1);
    expect(validateAge(dPlus.toISOString().slice(0, 10))).toMatch(/Минимальный возраст/);
  });
  it("слишком стар", () => {
    const iso = minBirthDate();
    const dMinus = new Date(iso); dMinus.setDate(dMinus.getDate() - 1);
    expect(validateAge(dMinus.toISOString().slice(0, 10))).toMatch(/Максимальный возраст/);
  });
  it("null и пустая строка — null", () => {
    expect(validateAge(null)).toBeNull();
    expect(validateAge(undefined)).toBeNull();
    expect(validateAge("")).toBeNull();
  });
  it("мусор — некорректная дата", () => {
    expect(validateAge("abc")).toMatch(/Некорректная/);
  });
  it("MIN_AGE/MAX_AGE — 16/34", () => {
    expect(MIN_AGE).toBe(16);
    expect(MAX_AGE).toBe(34);
  });
});