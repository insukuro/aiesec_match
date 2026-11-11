export interface Reason { code: string; polarity: "positive" | "negative"; weight: number; text: string }

export function ReasonList({ reasons }: { reasons: Reason[] }) {
  const positive = reasons.filter((r) => r.polarity === "positive").slice(0, 3);
  const negative = reasons.find((r) => r.polarity === "negative");
  if (positive.length === 0 && !negative) return null;
  return (
    <ul className="stack" style={{ padding: 0, listStyle: "none", margin: "var(--space-2) 0" }}>
      {positive.map((r, i) => (
        <li key={`p-${i}`} style={{ color: "var(--c-success)", fontSize: "var(--fs-caption)" }}>+ {r.text}</li>
      ))}
      {negative && (
        <li style={{ color: "var(--c-warning)", fontSize: "var(--fs-caption)" }}>− {negative.text}</li>
      )}
    </ul>
  );
}