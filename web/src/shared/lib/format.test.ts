import { describe, it, expect } from "vitest";
import { pluralRu, formatMoney, formatPercent } from "./format";

describe("pluralRu", () => {
  const forms: [string, string, string] = ["заявка", "заявки", "заявок"];
  it.each([
    [1, "заявка"], [2, "заявки"], [4, "заявки"], [5, "заявок"],
    [11, "заявок"], [21, "заявка"], [22, "заявки"], [25, "заявок"],
    [101, "заявка"], [111, "заявок"],
  ])("%i → %s", (n, expected) => {
    expect(pluralRu(n, forms)).toBe(expected);
  });
});

describe("formatMoney", () => {
  it("EUR", () => {
    expect(formatMoney(300, "EUR")).toMatch(/300/);
  });
  it("невалидный код — fallback", () => {
    expect(formatMoney(100, "INVALID")).toBe("100 INVALID");
  });
});

describe("formatPercent", () => {
  it("округляет", () => {
    expect(formatPercent(0.756)).toBe("76%");
    expect(formatPercent(0.5, 1)).toBe("50.0%");
  });
});