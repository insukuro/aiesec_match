import type { Condition } from "../api/types";

export function evaluate(cond: Condition | undefined, values: Record<string, unknown>): boolean {
  if (!cond) return true;
  if ("any" in cond) return cond.any.some((c) => evaluate(c, values));
  if ("all" in cond) return cond.all.every((c) => evaluate(c, values));
  const v = values[cond.field];
  switch (cond.op) {
    case "eq": return v === cond.value;
    case "in": return Array.isArray(cond.value) && (cond.value as unknown[]).includes(v);
    case "not_in": return Array.isArray(cond.value) && !(cond.value as unknown[]).includes(v);
    case "empty": return v == null || v === "" || (Array.isArray(v) && v.length === 0);
    case "not_empty": return !(v == null || v === "" || (Array.isArray(v) && v.length === 0));
  }
}