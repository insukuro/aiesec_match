export function getPath(obj: Record<string, unknown> | null | undefined, path: string): unknown {
  if (!obj) return undefined;
  let cur: unknown = obj;
  for (const p of path.split(".")) {
    if (cur && typeof cur === "object" && p in (cur as object)) {
      cur = (cur as Record<string, unknown>)[p];
    } else {
      return undefined;
    }
  }
  return cur;
}

export function setPath(obj: Record<string, unknown>, path: string, value: unknown): Record<string, unknown> {
  const parts = path.split(".");
  const out: Record<string, unknown> = { ...obj };
  let cur: Record<string, unknown> = out;
  for (let i = 0; i < parts.length - 1; i++) {
    const k = parts[i]!;
    cur[k] = { ...((cur[k] as Record<string, unknown>) ?? {}) };
    cur = cur[k] as Record<string, unknown>;
  }
  cur[parts[parts.length - 1]!] = value;
  return out;
}

export function stripEmpty<T extends Record<string, unknown>>(obj: T): T {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(obj)) {
    if (v === undefined || v === "") continue;
    if (Array.isArray(v) && v.length === 0) continue;
    out[k] = v;
  }
  return out as T;
}