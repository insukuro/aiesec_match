import { describe, it, expect } from "vitest";
import { getPath, setPath, stripEmpty } from "./get";

describe("getPath", () => {
  const obj = { a: { b: { c: 1 } }, x: 2 };
  it("вложенный", () => expect(getPath(obj, "a.b.c")).toBe(1));
  it("верхний", () => expect(getPath(obj, "x")).toBe(2));
  it("отсутствует — undefined", () => {
    expect(getPath(obj, "a.b.z")).toBeUndefined();
    expect(getPath(null, "a")).toBeUndefined();
    expect(getPath(obj, "a.b.c.d")).toBeUndefined();
  });
});

describe("setPath", () => {
  it("создаёт промежуточные объекты", () => {
    const out = setPath({}, "a.b.c", 42);
    expect(out).toEqual({ a: { b: { c: 42 } } });
  });
  it("не мутирует исходный", () => {
    const src = { a: { x: 1 } };
    const out = setPath(src, "a.y", 2);
    expect(src).toEqual({ a: { x: 1 } });
    expect(out).toEqual({ a: { x: 1, y: 2 } });
  });
});

describe("stripEmpty", () => {
  it("убирает undefined, '', []", () => {
    expect(stripEmpty({ a: undefined, b: "", c: [], d: 0, e: false, f: [1] }))
      .toEqual({ d: 0, e: false, f: [1] });
  });
});