export const MIN_AGE = 16;
export const MAX_AGE = 34; // «< 35»

export function yearsBetween(birth: Date, today = new Date()): number {
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age;
}

export function parseIsoDate(iso: string): Date | null {
  if (!iso) return null;
  const d = new Date(iso + "T00:00:00");
  return Number.isNaN(d.getTime()) ? null : d;
}

export function toIso(d: Date): string {
  return d.toISOString().slice(0, 10);
}

/** Последняя допустимая дата рождения: чтобы сегодня было ≥ 16 лет. */
export function maxBirthDate(today = new Date()): string {
  const d = new Date(today);
  d.setFullYear(d.getFullYear() - MIN_AGE);
  return toIso(d);
}

/** Первая допустимая дата рождения: чтобы сегодня было ≤ 34 лет (строго < 35). */
export function minBirthDate(today = new Date()): string {
  const d = new Date(today);
  d.setFullYear(d.getFullYear() - (MAX_AGE + 1));
  d.setDate(d.getDate() + 1);
  return toIso(d);
}

export function validateAge(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = parseIsoDate(iso);
  if (!d) return "Некорректная дата";
  const today = new Date();
  if (d > today) return "Дата не может быть в будущем";
  const age = yearsBetween(d, today);
  if (age < MIN_AGE) return `Минимальный возраст — ${MIN_AGE} лет`;
  if (age > MAX_AGE) return `Максимальный возраст — ${MAX_AGE} лет (до 35)`;
  return null;
}