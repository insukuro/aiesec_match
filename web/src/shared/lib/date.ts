export function formatDate(iso: string | null | undefined, locale = "ru-RU"): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString(locale, { year: "numeric", month: "short", day: "numeric" });
}

export function formatDateTime(iso: string | null | undefined, locale = "ru-RU"): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString(locale, {
    year: "numeric", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export function daysAgo(n: number): Date {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d;
}

export function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}