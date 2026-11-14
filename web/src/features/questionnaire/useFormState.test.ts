// web/src/features/questionnaire/useFormState.test.ts
import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useFormState } from "./useFormState";
import type { FormStep } from "../../shared/api/types";

const step: FormStep = {
  id: "s",
  title: "S",
  fields: [
    { id: "f_req", kind: "text", label: "R", required: true },
    { id: "f_max", kind: "text", label: "M", validation: { max_length: 3 } },
    { id: "f_num", kind: "number", label: "N", validation: { min: 1, max: 10 } },
    { id: "f_bd", kind: "date", label: "BD", maps_to: "birth_date" },
    { id: "f_dur", kind: "multi", label: "D", maps_to: "duration" },
  ],
};

describe("useFormState", () => {
  it("validate: required, max_length, min/max", () => {
    const { result } = renderHook(() => useFormState(step, {}));
    act(() => result.current.update("f_req", undefined, ""));
    act(() => result.current.update("f_max", undefined, "abcd"));
    act(() => result.current.update("f_num", undefined, 0));
    let ok = false;
    act(() => { ok = result.current.validate(); });
    expect(ok).toBe(false);
    expect(result.current.errors.f_req).toBe("Обязательное поле");
    expect(result.current.errors.f_max).toMatch(/Не более 3/);
    expect(result.current.errors.f_num).toMatch(/Минимум 1/);
  });

  it("validate: age для birth_date", () => {
    const { result } = renderHook(() => useFormState(step, {}));
    act(() => result.current.update("f_req", undefined, "x"));
    act(() => result.current.update("f_bd", "birth_date", "2999-01-01"));
    let ok = false;
    act(() => { ok = result.current.validate(); });
    expect(ok).toBe(false);
    expect(result.current.errors.f_bd).toMatch(/в будущем/);
  });

  it("duration: массив → {min_weeks, max_weeks}", () => {
    const { result } = renderHook(() => useFormState(step, {}));
    act(() => result.current.update("f_dur", "duration", ["8", "6", "12"]));
    expect(result.current.sanitized.duration).toEqual({ min_weeks: 6, max_weeks: 12 });
  });

  it("stripEmpty: пустые значения выпадают", () => {
    const { result } = renderHook(() => useFormState(step, {}));
    act(() => result.current.update("f_req", undefined, "x"));
    expect(result.current.sanitized.f_req).toBe("x");
    expect(result.current.sanitized.f_max).toBeUndefined();
  });

  it("visibleFields: show_if", () => {
    const s: FormStep = {
      id: "s", title: "S",
      fields: [
        { id: "a", kind: "boolean", label: "A", maps_to: "a" },
        { id: "b", kind: "text", label: "B", show_if: { field: "a", op: "eq", value: true } },
      ],
    };
    const { result } = renderHook(() => useFormState(s, {}));
    expect(result.current.visibleFields.map((f) => f.id)).toEqual(["a"]);
    act(() => result.current.update("a", "a", true));
    expect(result.current.visibleFields.map((f) => f.id)).toEqual(["a", "b"]);
  });
});