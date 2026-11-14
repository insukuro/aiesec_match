import { describe, it, expect } from "vitest";
import { evaluate } from "./condition";

const values = { a: 1, b: "x", list: [1, 2], empty: [], obj: {} };

describe("evaluate", () => {
  it("undefined — true", () => expect(evaluate(undefined, values)).toBe(true));
  it("any", () => {
    expect(evaluate({ any: [{ field: "a", op: "eq", value: 1 }, { field: "b", op: "eq", value: "no" }] }, values)).toBe(true);
  });
  it("all", () => {
    expect(evaluate({ all: [{ field: "a", op: "eq", value: 1 }, { field: "b", op: "eq", value: "no" }] }, values)).toBe(false);
  });
  it("eq", () => {
    expect(evaluate({ field: "a", op: "eq", value: 1 }, values)).toBe(true);
    expect(evaluate({ field: "a", op: "eq", value: 2 }, values)).toBe(false);
  });
  it("in", () => {
    expect(evaluate({ field: "a", op: "in", value: [1, 3] }, values)).toBe(true);
    expect(evaluate({ field: "a", op: "in", value: [3, 4] }, values)).toBe(false);
  });
  it("empty / not_empty", () => {
    expect(evaluate({ field: "empty", op: "empty" }, values)).toBe(true);
    expect(evaluate({ field: "obj", op: "empty" }, values)).toBe(false);
    expect(evaluate({ field: "list", op: "not_empty" }, values)).toBe(true);
    expect(evaluate({ field: "missing", op: "empty" }, values)).toBe(true);
  });
});